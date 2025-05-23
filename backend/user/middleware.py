# -*- coding: utf-8 -*-
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError
from rest_framework_jwt.settings import api_settings
import json

from role.models import SysRole, ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_USER
from user.models import SysUser


class JwtAuthenticationMiddleware(MiddlewareMixin):

    def process_request(self, request):
        white_list = ["/user/login", "/user/register"]  # 请求白名单
        path = request.path
        if path not in white_list and not path.startswith("/media"):
            print('要进行token验证')
            # 检查多种获取token的方式
            token = None
            
            # 1. 从Authorization或X-Token头中获取
            if 'HTTP_AUTHORIZATION' in request.META:
                token = request.META.get('HTTP_AUTHORIZATION')
            elif 'HTTP_X_TOKEN' in request.META:
                token = request.META.get('HTTP_X_TOKEN')
            
            # 2. 从URL参数中获取token（用于SSE连接）
            if not token and 'token' in request.GET:
                token = request.GET.get('token')
                
            # 3. 从请求体中获取token
            if not token and request.body:
                try:
                    body_data = json.loads(request.body)
                    if 'token' in body_data:
                        token = body_data['token']
                except Exception:
                    pass
                
            print("token:", token)
            
            if not token:
                print(f"Unauthorized: {path}")
                return JsonResponse({'code': 401, 'message': '未提供Token'}, status=401)
                
            # 如果token以Bearer开头，移除前缀
            if isinstance(token, str) and token.startswith('Bearer '):
                token = token[7:]

            try:
                # 解析 JWT token
                jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
                payload = jwt_decode_handler(token)
                
                # 从 payload 中获取用户 ID
                user_id = payload.get('user_id')
                
                if user_id:
                    # 将用户 ID 存储在请求对象中，供后续中间件和视图使用
                    request.user_id = user_id
                else:
                    return JsonResponse({'code': 401, 'message': 'Token 无效，未包含用户ID'}, status=401)
                    
            except ExpiredSignatureError:
                return JsonResponse({'code': 401, 'message': 'Token 已过期'}, status=401)
            except (InvalidTokenError, PyJWTError) as e:
                print(f"Token 验证失败: {e}")
                return JsonResponse({'code': 401, 'message': 'Token 无效'}, status=401)
        else:
            print('token验证')
            return None


class PermissionMiddleware(MiddlewareMixin):
    """
    权限校验中间件
    在通过JWT身份验证后，进一步判断用户是否有权限访问请求的URL
    """
    
    def process_request(self, request):
        # 白名单，无需权限校验的路径
        white_list = [
            "/user/login", 
            "/user/register",  # 注册接口
            "/user/current",
            "/user/updateUserPwd",  # 修改自己的密码
            "/user/updateAvatar",   # 修改自己的头像
            "/user/uploadImage",    # 上传图片
            "/user/save",          # 修改个人信息
            "/user/accessibleUrls", # 获取可访问URL列表
            "/chat/",              # 聊天API，允许所有用户访问
            "/chat/stream/",        # 聊天流式API
        ]
        path = request.path
        
        # 确保流式响应的路径匹配
        if path.startswith("/chat/stream/"):
            return None
            
        # 跳过白名单中的路径和媒体文件
        if path in white_list or path.startswith("/media"):
            return None
            
        # 如果没有完成JWT验证，直接返回（让JWT中间件处理）
        if not hasattr(request, 'user_id'):
            return None
            
        user_id = request.user_id
        
        try:
            # 获取用户信息
            user = SysUser.objects.get(id=user_id)
            
            # 查询用户角色 - 始终从数据库获取最新角色，确保权限实时更新
            user_roles = SysRole.objects.raw(
                "SELECT id, code, name FROM sys_role WHERE id IN "
                "(SELECT role_id FROM sys_user_role WHERE user_id=%s)", 
                [user_id]
            )
            
            # 角色名称列表和角色代码列表
            role_names = [role.name for role in user_roles]
            role_codes = [role.code for role in user_roles]
            
            # 缓存当前用户角色到请求对象，方便在视图中使用
            request.user_role_names = role_names
            request.user_role_codes = role_codes
            
            # 根据角色确定用户的权限
            user_permissions = []
            
            # 检查用户角色类型
            is_superadmin = ROLE_SUPERADMIN in role_codes or '超级管理员' in role_names
            is_admin = ROLE_ADMIN in role_codes or '管理员' in role_names
            
            # 1. 超级管理员拥有所有权限
            if is_superadmin:
                # 超级管理员拥有所有权限
                return None
                
            # 2. 管理员有角色管理权限
            # 用户管理权限 - 仅超级管理员可访问（由前面的条件判断）
            user_management_urls = [
                '/user/status',
                '/user/resetPassword',
                '/user/action',  # DELETE操作
                '/user/grantRole',
            ]
            
            # 角色管理权限 - 超级管理员可访问
            role_management_urls = [
                '/role/save',
                '/role/action',  # DELETE操作
            ]
            
            # 3. 如果是普通用户，只能获取列表和修改自己的信息
            # 普通用户只能访问：
            # - 用户列表 (仅查看): /user/search
            # - 角色列表 (仅查看): /role/search, /role/listAll
            # - 个人信息修改: /user/updateUserPwd, /user/updateAvatar, /user/save
            
            # 检查是用户自己的操作
            is_self_operation = False
            if path.startswith('/user/'):
                if 'updateUserPwd' in path or 'updateAvatar' in path or 'save' in path:
                    is_self_operation = True
                    
            # 如果是普通用户，限制访问权限
            if not is_superadmin and not is_admin:
                # 只允许访问白名单中的路径
                allowed_paths = [
                    '/user/search',  # 用户列表
                    '/role/search',  # 角色列表
                    '/role/listAll', # 所有角色列表
                    '/user/updateUserPwd',  # 修改自己的密码
                    '/user/updateAvatar',   # 修改自己的头像
                    '/user/uploadImage',    # 上传图片
                    '/user/save',          # 修改个人信息
                ]
                
                if path not in allowed_paths:
                    response = JsonResponse({
                        'code': 403,
                        'message': '权限不足，无法访问该资源'
                    }, status=403)
                    response['X-Error-Page'] = '/403'  # 添加自定义头，用于前端识别需要重定向
                    return response
                    
            # 如果是管理员，限制访问权限
            elif is_admin and not is_superadmin:
                # 管理员不能访问角色管理相关操作
                if path.startswith('/role/') and path not in ['/role/search', '/role/listAll']:
                    response = JsonResponse({
                        'code': 403,
                        'message': '权限不足，只有超级管理员可以管理角色'
                    }, status=403)
                    response['X-Error-Page'] = '/403'
                    return response
            
            # 访问权限检查 - 用户管理
            if any(path.startswith(url) for url in user_management_urls):
                # 超级管理员和管理员可以进行用户管理
                if not (is_admin or is_self_operation):
                    response = JsonResponse({
                        'code': 403, 
                        'message': '权限不足，只有管理员或超级管理员可以进行用户管理'
                    }, status=403)
                    response['X-Error-Page'] = '/403'
                    return response
                    
                # 对于用户删除操作，只有超级管理员可以执行
                if path.startswith('/user/action') and request.method == 'DELETE' and not is_superadmin:
                    response = JsonResponse({
                        'code': 403, 
                        'message': '权限不足，只有超级管理员可以删除用户'
                    }, status=403)
                    response['X-Error-Page'] = '/403'
                    return response
            
            # 访问权限检查 - 角色管理
            if any(path.startswith(url) for url in role_management_urls):
                if not is_superadmin:
                    response = JsonResponse({
                        'code': 403, 
                        'message': '权限不足，只有超级管理员可以进行角色管理'
                    }, status=403)
                    response['X-Error-Page'] = '/403'
                    return response
            
            # 允许所有用户查看列表
            if path.startswith('/user/search') or path.startswith('/role/search') or path.startswith('/role/listAll'):
                return None
                
            # 如果所有检查都通过，允许访问
            return None
            
        except Exception as e:
            print(f"权限校验发生异常: {e}")
            return JsonResponse({
                'code': 500, 
                'message': '系统权限校验异常'
            }, status=500)
    
    def get_required_permission(self, path, method):
        """
        根据URL路径和HTTP方法获取所需的权限标识
        需要根据系统的权限设计完善此映射关系
        """
        # 用户管理相关权限
        if path.startswith('/user/'):
            if 'save' in path:
                return 'system:user:edit'
            if 'status' in path:
                return 'system:user:edit'
            if 'resetPassword' in path:
                return 'system:user:reset'
            if 'search' in path:
                return 'system:user:list'
            if 'action' in path and method == 'DELETE':
                return 'system:user:remove'
            if 'grantRole' in path:
                return 'system:user:edit'
        
        # 角色管理相关权限
        if path.startswith('/role/'):
            if 'save' in path:
                return 'system:role:edit'
            if 'search' in path:
                return 'system:role:list'
            if 'action' in path and method == 'DELETE':
                return 'system:role:remove'
            if 'grantMenu' in path:
                return 'system:role:edit'
        
        if path.startswith('/chat/'):
            # 通用聊天权限
            return 'system:chat:use'
            
        # 如果没有找到匹配的权限，返回None表示不需要特殊权限
        return None
