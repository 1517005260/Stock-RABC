# -*- coding: utf-8 -*-

import json
from decimal import Decimal
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from user.models import SysUser, SysUserSerializer
from role.models import SysRole, SysUserRole
from utils.permissions import require_login, admin_required, superadmin_required
from trading.models import UserStockAccount, TradeRecord
from app import settings

# 角色常量
ROLE_SUPERADMIN = 'superadmin'
ROLE_ADMIN = 'admin'
ROLE_USER = 'user'


class AuthenticationView(APIView):
    """统一的认证相关视图"""
    
    def post(self, request):
        """登录"""
        try:
            data = json.loads(request.body.decode("utf-8"))
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return JsonResponse({'code': 400, 'msg': '用户名和密码不能为空'})
            
            # 查找用户
            try:
                user = SysUser.objects.get(username=username)
            except SysUser.DoesNotExist:
                return JsonResponse({'code': 401, 'msg': '用户名或密码错误'})
            
            # 验证密码和用户状态
            # 先进行MD5加密比较
            import hashlib
            password_md5 = hashlib.md5(password.encode()).hexdigest()
            
            if user.password != password_md5:
                return JsonResponse({'code': 401, 'msg': '用户名或密码错误'})
            
            if user.status != 0:  # 0正常，1停用
                return JsonResponse({'code': 403, 'msg': '账户已被禁用'})
            
            # 生成token
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            
            # 获取用户角色
            roles = self._get_user_roles(user.id)
            
            # 序列化用户数据并添加金融信息
            user_data = SysUserSerializer(user).data
            user_data.update(self._get_user_financial_info(user))
            user_data['roles'] = roles
            
            return JsonResponse({
                'code': 200,
                'msg': '登录成功',
                'token': token,
                'user': user_data
            })
            
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'登录失败: {str(e)}'})
    
    def put(self, request):
        """注册"""
        try:
            data = json.loads(request.body.decode("utf-8"))
            username = data.get('username')
            password = data.get('password')
            confirm_password = data.get('confirmPassword')
            email = data.get('email', '')
            
            # 验证数据
            if not username or not password:
                return JsonResponse({'code': 400, 'msg': '用户名和密码不能为空'})
            
            if password != confirm_password:
                return JsonResponse({'code': 400, 'msg': '两次输入的密码不一致'})
            
            if SysUser.objects.filter(username=username).exists():
                return JsonResponse({'code': 400, 'msg': '用户名已存在'})
            
            # 创建用户
            user = SysUser.objects.create(
                username=username,
                password=password,
                email=email,
                status=1,
                create_time=timezone.now(),
                update_time=timezone.now(),
                avatar='default.jpg'
            )
            
            # 分配普通用户角色
            role = SysRole.objects.get(code=ROLE_USER)
            SysUserRole.objects.create(user=user, role=role)
            
            # 创建股票账户
            UserStockAccount.objects.create(
                user=user,
                account_balance=Decimal('100000.00'),  # 默认10万初始资金
                frozen_balance=Decimal('0.00'),
                total_assets=Decimal('100000.00'),
                total_profit=Decimal('0.00')
            )
            
            return JsonResponse({'code': 200, 'msg': '注册成功'})
            
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'注册失败: {str(e)}'})
    
    def _get_user_roles(self, user_id):
        """获取用户角色"""
        roles = SysRole.objects.raw(
            "SELECT id, name, code FROM sys_role WHERE id IN "
            "(SELECT role_id FROM sys_user_role WHERE user_id=%s)", 
            [user_id]
        )
        return ",".join([role.name for role in roles])
    
    def _get_user_financial_info(self, user):
        """获取用户金融信息"""
        try:
            # 获取账户信息
            account = UserStockAccount.objects.filter(user=user).first()
            
            # 获取交易统计
            buy_count = TradeRecord.objects.filter(user=user, trade_type='BUY').count()
            sell_count = TradeRecord.objects.filter(user=user, trade_type='SELL').count()
            
            return {
                'account_balance': float(account.account_balance) if account else 0.0,
                'buy_count': buy_count,
                'sell_count': sell_count,
            }
        except Exception:
            return {
                'account_balance': 0.0,
                'buy_count': 0,
                'sell_count': 0,
            }


class UserManagementView(APIView):
    """统一的用户管理视图"""
    
    @method_decorator(require_login)
    def get(self, request):
        """获取用户信息或用户列表"""
        action = request.GET.get('action', 'current')
        
        if action == 'current':
            return self._get_current_user(request)
        elif action == 'list':
            return self._get_user_list(request)
        elif action == 'detail':
            return self._get_user_detail(request)
        else:
            return JsonResponse({'code': 400, 'msg': '无效的操作'})
    
    @method_decorator(require_login)
    def post(self, request):
        """用户操作：保存、修改密码、重置密码等"""
        try:
            data = json.loads(request.body.decode("utf-8"))
            action = data.get('action', 'save')
            
            if action == 'save':
                return self._save_user(request, data)
            elif action == 'change_password':
                return self._change_password(request, data)
            elif action == 'reset_password':
                return self._reset_password(request, data)
            elif action == 'update_status':
                return self._update_status(request, data)
            elif action == 'grant_role':
                return self._grant_role(request, data)
            else:
                return JsonResponse({'code': 400, 'msg': '无效的操作'})
                
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'操作失败: {str(e)}'})
    
    @method_decorator(require_login)
    def delete(self, request):
        """删除用户"""
        try:
            data = json.loads(request.body.decode("utf-8"))
            user_ids = data if isinstance(data, list) else [data]
            
            # 检查权限：只有超级管理员可以删除用户
            current_user_id = getattr(request, 'user_id', None)
            if not self._is_superadmin(current_user_id):
                return JsonResponse({'code': 403, 'msg': '权限不足'})
            
            # 删除用户和相关数据
            SysUserRole.objects.filter(user_id__in=user_ids).delete()
            SysUser.objects.filter(id__in=user_ids).delete()
            
            return JsonResponse({'code': 200, 'msg': '删除成功'})
            
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'删除失败: {str(e)}'})
    
    def _get_current_user(self, request):
        """获取当前用户信息"""
        try:
            # 从请求中获取用户ID（由中间件设置）
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return JsonResponse({'code': 401, 'msg': '未授权'})
            
            user = SysUser.objects.get(id=user_id)
            user_data = SysUserSerializer(user).data
            
            # 添加角色和金融信息
            roles = self._get_user_roles(user_id)
            financial_info = self._get_user_financial_info(user)
            
            user_data.update(financial_info)
            user_data['roles'] = roles
            
            return JsonResponse({
                'code': 200,
                'user': user_data
            })
            
        except SysUser.DoesNotExist:
            return JsonResponse({'code': 404, 'msg': '用户不存在'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'获取用户信息失败: {str(e)}'})
    
    def _get_user_list(self, request):
        """获取用户列表（需要管理员权限）"""
        try:
            current_user_id = getattr(request, 'user_id', None)
            if not self._is_admin_or_above(current_user_id):
                return JsonResponse({'code': 403, 'msg': '权限不足'})
            
            # 分页参数
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('pageSize', 10))
            
            # 查询用户
            users = SysUser.objects.all()
            total = users.count()
            
            start = (page - 1) * page_size
            end = start + page_size
            user_list = list(users[start:end].values())
            
            return JsonResponse({
                'code': 200,
                'data': {
                    'list': user_list,
                    'total': total,
                    'page': page,
                    'pageSize': page_size
                }
            })
            
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'获取用户列表失败: {str(e)}'})
    
    def _get_user_detail(self, request):
        """获取用户详情"""
        try:
            user_id = request.GET.get("id")
            user = SysUser.objects.get(id=user_id)
            return JsonResponse({'code': 200, 'user': SysUserSerializer(user).data})
        except SysUser.DoesNotExist:
            return JsonResponse({'code': 404, 'msg': '用户不存在'})
    
    def _save_user(self, request, data):
        """保存或更新用户"""
        user_id = data.get('id', -1)
        current_user_id = getattr(request, 'user_id', None)
        
        # 权限检查
        is_self_operation = current_user_id and int(data.get('id', -1)) == int(current_user_id)
        if not is_self_operation and not self._is_superadmin(current_user_id):
            return JsonResponse({'code': 403, 'msg': '权限不足'})
        
        try:
            if int(user_id) == -1:  # 新增用户
                if not self._is_superadmin(current_user_id):
                    return JsonResponse({'code': 403, 'msg': '只有超级管理员可以添加用户'})
                
                user = SysUser.objects.create(
                    username=data['username'],
                    password=data.get('password', '123456'),
                    email=data.get('email', ''),
                    phonenumber=data.get('phonenumber', ''),
                    status=data.get('status', 1),
                    create_time=timezone.now(),
                    update_time=timezone.now(),
                    avatar=data.get('avatar', 'default.jpg')
                )
                
                # 创建股票账户
                UserStockAccount.objects.create(
                    user=user,
                    account_balance=Decimal('100000.00'),
                    frozen_balance=Decimal('0.00'),
                    total_assets=Decimal('100000.00'),
                    total_profit=Decimal('0.00')
                )
                
            else:  # 更新用户
                user = SysUser.objects.get(id=user_id)
                user.username = data.get('username', user.username)
                user.email = data.get('email', user.email)
                user.phonenumber = data.get('phonenumber', user.phonenumber)
                if not is_self_operation:  # 只有管理员可以修改状态
                    user.status = data.get('status', user.status)
                user.update_time = timezone.now()
                user.save()
            
            return JsonResponse({'code': 200, 'msg': '保存成功'})
            
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'保存失败: {str(e)}'})
    
    def _change_password(self, request, data):
        """修改密码"""
        try:
            user_id = data['id']
            old_password = data['oldPassword']
            new_password = data['newPassword']
            
            user = SysUser.objects.get(id=user_id)
            if user.password != old_password:
                return JsonResponse({'code': 400, 'msg': '原密码错误'})
            
            user.password = new_password
            user.update_time = timezone.now()
            user.save()
            
            return JsonResponse({'code': 200, 'msg': '密码修改成功'})
            
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'修改密码失败: {str(e)}'})
    
    def _reset_password(self, request, data):
        """重置密码（管理员功能）"""
        try:
            current_user_id = getattr(request, 'user_id', None)
            if not self._is_admin_or_above(current_user_id):
                return JsonResponse({'code': 403, 'msg': '权限不足'})
            
            user_id = data.get("id")
            user = SysUser.objects.get(id=user_id)
            user.password = "123456"
            user.update_time = timezone.now()
            user.save()
            
            return JsonResponse({'code': 200, 'msg': '密码重置成功'})
            
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'重置密码失败: {str(e)}'})
    
    def _update_status(self, request, data):
        """更新用户状态"""
        try:
            current_user_id = getattr(request, 'user_id', None)
            if not self._is_admin_or_above(current_user_id):
                return JsonResponse({'code': 403, 'msg': '权限不足'})
            
            user_id = data['id']
            status = data['status']
            
            user = SysUser.objects.get(id=user_id)
            user.status = status
            user.update_time = timezone.now()
            user.save()
            
            return JsonResponse({'code': 200, 'msg': '状态更新成功'})
            
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'状态更新失败: {str(e)}'})
    
    def _grant_role(self, request, data):
        """角色授权"""
        try:
            current_user_id = getattr(request, 'user_id', None)
            if not self._is_superadmin(current_user_id):
                return JsonResponse({'code': 403, 'msg': '权限不足'})
            
            user_id = data['id']
            role_ids = data['roleIds']
            
            # 删除原有角色
            SysUserRole.objects.filter(user_id=user_id).delete()
            
            # 添加新角色
            for role_id in role_ids:
                SysUserRole.objects.create(user_id=user_id, role_id=role_id)
            
            return JsonResponse({'code': 200, 'msg': '角色授权成功'})
            
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'角色授权失败: {str(e)}'})
    
    def _get_user_roles(self, user_id):
        """获取用户角色"""
        roles = SysRole.objects.raw(
            "SELECT id, name, code FROM sys_role WHERE id IN "
            "(SELECT role_id FROM sys_user_role WHERE user_id=%s)", 
            [user_id]
        )
        return ",".join([role.name for role in roles])
    
    def _get_user_financial_info(self, user):
        """获取用户金融信息"""
        try:
            account = UserStockAccount.objects.filter(user=user).first()
            buy_count = TradeRecord.objects.filter(user=user, trade_type='BUY').count()
            sell_count = TradeRecord.objects.filter(user=user, trade_type='SELL').count()
            
            return {
                'account_balance': float(account.account_balance) if account else 0.0,
                'buy_count': buy_count,
                'sell_count': sell_count,
            }
        except Exception:
            return {
                'account_balance': 0.0,
                'buy_count': 0,
                'sell_count': 0,
            }
    
    def _is_superadmin(self, user_id):
        """检查是否为超级管理员"""
        if not user_id:
            return False
        roles = SysRole.objects.raw(
            "SELECT id, code FROM sys_role WHERE id IN "
            "(SELECT role_id FROM sys_user_role WHERE user_id=%s)", 
            [user_id]
        )
        return any(role.code == ROLE_SUPERADMIN for role in roles)
    
    def _is_admin_or_above(self, user_id):
        """检查是否为管理员或以上级别"""
        if not user_id:
            return False
        roles = SysRole.objects.raw(
            "SELECT id, code FROM sys_role WHERE id IN "
            "(SELECT role_id FROM sys_user_role WHERE user_id=%s)", 
            [user_id]
        )
        role_codes = [role.code for role in roles]
        return ROLE_SUPERADMIN in role_codes or ROLE_ADMIN in role_codes


class UtilityView(APIView):
    """工具类视图：头像上传、用户名检查等"""
    
    @method_decorator(require_login)
    def post(self, request):
        """处理各种工具类操作"""
        action = request.POST.get('action') or request.GET.get('action', 'check')
        
        if action == 'upload_avatar':
            return self._upload_avatar(request)
        elif action == 'check_username':
            return self._check_username(request)
        else:
            return JsonResponse({'code': 400, 'msg': '无效的操作'})
    
    def _upload_avatar(self, request):
        """上传头像"""
        try:
            if 'file' not in request.FILES:
                return JsonResponse({'code': 400, 'msg': '没有上传文件'})
            
            file = request.FILES['file']
            if file.size > 2 * 1024 * 1024:  # 2MB限制
                return JsonResponse({'code': 400, 'msg': '文件大小不能超过2MB'})
            
            # 生成文件名
            import uuid
            file_extension = file.name.split('.')[-1]
            filename = f"avatar_{uuid.uuid4()}.{file_extension}"
            
            # 保存文件
            file_path = default_storage.save(f"avatars/{filename}", ContentFile(file.read()))
            
            return JsonResponse({
                'code': 200,
                'msg': '上传成功',
                'url': f'/media/{file_path}'
            })
            
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'上传失败: {str(e)}'})
    
    def _check_username(self, request):
        """检查用户名是否可用"""
        try:
            data = json.loads(request.body.decode("utf-8"))
            username = data['username']
            
            if SysUser.objects.filter(username=username).exists():
                return JsonResponse({'code': 400, 'msg': '用户名已存在'})
            else:
                return JsonResponse({'code': 200, 'msg': '用户名可用'})
                
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'检查失败: {str(e)}'})


# 为了兼容现有的URL配置，保留一些简化的视图类
class LoginView(AuthenticationView):
    """登录视图 - 兼容性"""
    def post(self, request):
        return super().post(request)


class RegisterView(AuthenticationView):
    """注册视图 - 兼容性"""
    def post(self, request):
        return super().put(request)


class CurrentUserView(UserManagementView):
    """当前用户视图 - 兼容性"""
    def get(self, request):
        return self._get_current_user(request)


class SaveView(UserManagementView):
    """保存用户视图 - 兼容性"""
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        return self._save_user(request, data)


# 其他必要的简化视图...
class CheckView(UtilityView):
    """用户名检查视图 - 兼容性"""
    def post(self, request):
        return self._check_username(request)


class ImageView(UtilityView):
    """图片上传视图 - 兼容性"""
    def post(self, request):
        return self._upload_avatar(request)


class AvatarView(UtilityView):
    """头像更新视图 - 兼容性"""
    def post(self, request):
        return self._upload_avatar(request)


class PwdView(UserManagementView):
    """密码修改视图 - 兼容性"""
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        data['action'] = 'change_password'
        return super().post(request)


class PasswordView(UserManagementView):
    """密码重置视图 - 兼容性"""
    def get(self, request):
        data = {'id': request.GET.get("id"), 'action': 'reset_password'}
        return self._reset_password(request, data)


class StatusView(UserManagementView):
    """状态修改视图 - 兼容性"""
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        data['action'] = 'update_status'
        return super().post(request)


class GrantRole(UserManagementView):
    """角色授权视图 - 兼容性"""
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        data['action'] = 'grant_role'
        return super().post(request)


class SearchView(UserManagementView):
    """用户搜索视图 - 兼容性"""
    def get(self, request):
        request.GET = request.GET.copy()
        request.GET['action'] = 'list'
        return super().get(request)


class ActionView(UserManagementView):
    """用户操作视图 - 兼容性"""
    def get(self, request):
        request.GET = request.GET.copy()
        request.GET['action'] = 'detail'
        return super().get(request)
    
    def delete(self, request):
        return super().delete(request)


class AccessibleUrlsView(APIView):
    """获取可访问URL列表"""
    
    @method_decorator(require_login)
    def get(self, request):
        try:
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return JsonResponse({'code': 401, 'msg': '未授权'})
            
            # 获取用户角色
            roles = SysRole.objects.raw(
                "SELECT id, name, code FROM sys_role WHERE id IN "
                "(SELECT role_id FROM sys_user_role WHERE user_id=%s)", 
                [user_id]
            )
            
            role_codes = [role.code for role in roles]
            role_names = [role.name for role in roles]
            
            # 确定用户角色类型
            is_superadmin = ROLE_SUPERADMIN in role_codes or '超级管理员' in role_names
            is_admin = ROLE_ADMIN in role_codes or '管理员' in role_names
            
            # 所有可能的路由和对应的权限
            all_routes = [
                {"path": "/index", "name": "首页", "requires_auth": True},
                {"path": "/chat", "name": "AI聊天助手", "requires_auth": True, "permission": "system:chat:use"},
                {"path": "/sys/user", "name": "用户管理", "requires_auth": True, "permission": "system:user:list"},
                {"path": "/sys/role", "name": "角色管理", "requires_auth": True, "permission": "system:role:list"},
                {"path": "/userCenter", "name": "个人中心", "requires_auth": True, "permission": "system:user:profile"},
                {"path": "/stock", "name": "股票交易系统", "requires_auth": True},
                {"path": "/accessibleUrls", "name": "我的可访问URL", "requires_auth": True}
            ]
            
            # 根据用户角色过滤可访问的路由
            accessible_routes = []
            
            if is_superadmin:
                accessible_routes = all_routes
            elif is_admin:
                accessible_routes = [route for route in all_routes if route["path"] != "/sys/role"]
            else:
                accessible_routes = [route for route in all_routes if route["path"] in [
                    "/index", "/userCenter", "/chat", "/stock", "/accessibleUrls"
                ]]
            
            return JsonResponse({
                'code': 200,
                'accessibleUrls': accessible_routes
            })
            
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'获取可访问URL失败: {str(e)}'})


# 调试相关视图
class DebugLoginView(APIView):
    """调试登录视图"""
    def post(self, request):
        # 简单的调试登录，生产环境应该禁用
        if not settings.DEBUG:
            return JsonResponse({'code': 403, 'msg': '调试功能已禁用'})
        
        try:
            user = SysUser.objects.first()  # 使用第一个用户进行调试登录
            if not user:
                return JsonResponse({'code': 404, 'msg': '没有可用的用户进行调试'})
            
            # 生成token
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            
            return JsonResponse({
                'code': 200,
                'msg': '调试登录成功',
                'token': token,
                'user': SysUserSerializer(user).data
            })
            
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'调试登录失败: {str(e)}'})


class TestView(APIView):
    """测试视图"""
    def get(self, request):
        if settings.DEBUG:
            return JsonResponse({'code': 200, 'msg': '测试成功', 'data': 'Debug mode enabled'})
        else:
            return JsonResponse({'code': 403, 'msg': '测试功能已禁用'})


class JwtTestView(APIView):
    """JWT测试视图"""
    def get(self, request):
        if not settings.DEBUG:
            return JsonResponse({'code': 403, 'msg': '测试功能已禁用'})
        
        try:
            user = SysUser.objects.first()
            if not user:
                return JsonResponse({'code': 404, 'msg': '没有可用的用户'})
            
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            
            return JsonResponse({'code': 200, 'token': token})
            
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': f'JWT测试失败: {str(e)}'})