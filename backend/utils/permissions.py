# -*- coding: utf-8 -*-

from functools import wraps
from django.http import JsonResponse
from user.models import SysUser
from role.models import SysUserRole


def get_user_roles(user_id):
    """获取用户角色列表"""
    try:
        user = SysUser.objects.get(id=user_id)
        user_roles = SysUserRole.objects.filter(user=user).select_related('role')
        return [user_role.role for user_role in user_roles]
    except SysUser.DoesNotExist:
        return []


def require_role(allowed_roles):
    """权限控制装饰器
    
    Args:
        allowed_roles: 允许的角色列表，如 ['user', 'admin', 'superadmin']
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # 检查用户是否登录
            if not hasattr(request, 'user_id') or not request.user_id:
                return JsonResponse({
                    'code': 401,
                    'msg': '未登录或登录已过期'
                })
            
            # 获取用户角色
            user_roles = get_user_roles(request.user_id)
            user_role_codes = [role.code for role in user_roles]
            
            # 检查权限
            if not any(role_code in allowed_roles for role_code in user_role_codes):
                return JsonResponse({
                    'code': 403,
                    'msg': '权限不足，无法访问该功能'
                })
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_login(func):
    """登录检查装饰器"""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user_id') or not request.user_id:
            return JsonResponse({
                'code': 401,
                'msg': '未登录或登录已过期'
            })
        return func(request, *args, **kwargs)
    return wrapper


def admin_required(func):
    """管理员权限装饰器"""
    return require_role(['admin', 'superadmin'])(func)


def superadmin_required(func):
    """超级管理员权限装饰器"""
    return require_role(['superadmin'])(func)


class PermissionMixin:
    """权限检查混合类"""
    
    def has_permission(self, request, required_roles):
        """检查用户权限"""
        if not hasattr(request, 'user_id') or not request.user_id:
            return False
        
        if isinstance(required_roles, str):
            required_roles = [required_roles]
        
        user_roles = get_user_roles(request.user_id)
        user_role_codes = [role.code for role in user_roles]
        
        return any(role_code in required_roles for role_code in user_role_codes)
    
    def get_current_user(self, request):
        """获取当前用户"""
        if not hasattr(request, 'user_id') or not request.user_id:
            return None
        
        try:
            return SysUser.objects.get(id=request.user_id)
        except SysUser.DoesNotExist:
            return None
    
    def is_owner_or_admin(self, request, resource_user_id):
        """检查是否为资源所有者或管理员"""
        current_user = self.get_current_user(request)
        if not current_user:
            return False
        
        # 检查是否为资源所有者
        if current_user.id == resource_user_id:
            return True
        
        # 检查是否为管理员
        return self.has_permission(request, ['admin', 'superadmin'])


def data_permission_filter(func):
    """数据权限过滤装饰器
    
    根据用户角色过滤数据：
    - 普通用户：只能看到自己的数据
    - 管理员：可以看到所有普通用户的数据
    - 超级管理员：可以看到所有数据
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        # 获取用户角色
        user_roles = get_user_roles(request.user_id) if hasattr(request, 'user_id') else []
        user_role_codes = [role.code for role in user_roles]
        
        # 设置数据权限标识
        if 'superadmin' in user_role_codes:
            request.data_scope = 'all'  # 查看所有数据
        elif 'admin' in user_role_codes:
            request.data_scope = 'users'  # 查看普通用户数据
        else:
            request.data_scope = 'self'  # 只查看自己的数据
        
        return func(request, *args, **kwargs)
    return wrapper