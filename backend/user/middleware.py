# -*- coding: utf-8 -*-
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError
from rest_framework_jwt.settings import api_settings
import json

from role.models import SysRole
from user.models import SysUser


class JwtAuthenticationMiddleware(MiddlewareMixin):

    def process_request(self, request):
        white_list = ["/user/login"]  # 请求白名单
        path = request.path
        if path not in white_list and not path.startswith("/media"):
            print('要进行token验证')
            # Check both header formats (Authorization header or direct token)
            token = request.META.get('HTTP_AUTHORIZATION')
            if not token and 'HTTP_X_TOKEN' in request.META:
                token = request.META.get('HTTP_X_TOKEN')
                
            # Handle the case when token is passed directly in the body
            if not token and request.body:
                try:
                    body_data = json.loads(request.body)
                    if 'token' in body_data:
                        token = body_data['token']
                except Exception:
                    pass
                
            print("token:", token)
            
            if not token:
                return JsonResponse({'code': 401, 'message': '未提供Token'}, status=401)
                
            # Strip 'Bearer ' prefix if present
            if token.startswith('Bearer '):
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
            "/user/current",
            "/user/updateUserPwd",
            "/user/uploadImage",
            "/user/updateAvatar",
        ]
        path = request.path
        
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
            
            # 查询用户角色
            user_roles = SysRole.objects.raw(
                "SELECT id, code, name FROM sys_role WHERE id IN "
                "(SELECT role_id FROM sys_user_role WHERE user_id=%s)", 
                [user_id]
            )
            
            # 如果用户是管理员，无需进一步校验权限
            for role in user_roles:
                if role.code == 'admin' or role.name == '管理员':
                    return None
            
            # 获取用户权限
            user_permissions = []
            for role in user_roles:
                # 这里应该获取该角色下的所有权限
                # 为了简化，可以暂时允许所有操作或添加具体的权限检查逻辑
                # 由于目前权限验证不完整，临时允许用户列表和角色列表的访问
                if path.startswith('/user/search') or path.startswith('/role/search') or path.startswith('/role/listAll'):
                    return None
            
            # 获取当前请求对应的权限标识
            required_permission = self.get_required_permission(path, request.method)
            
            if required_permission and required_permission not in user_permissions:
                # 记录日志
                print(f"权限校验失败: 用户ID={user_id}, URL={path}, 方法={request.method}, 缺少权限={required_permission}")
                return JsonResponse({
                    'code': 403, 
                    'message': '权限不足，无法访问该资源'
                }, status=403)
                
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
        
        # 菜单管理相关权限
        # if path.startswith('/menu/'):
        #     if 'save' in path:
        #         return 'system:menu:edit'
        #     if 'search' in path:
        #         return 'system:menu:list'
        #     if 'action' in path and method == 'DELETE':
        #         return 'system:menu:remove'
            
        # 如果没有找到匹配的权限，返回None表示不需要特殊权限
        return None
