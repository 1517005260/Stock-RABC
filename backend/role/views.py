import json
from datetime import datetime

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from django.db import connections

# from menu.models import SysRoleMenu
from role.models import SysRole, SysRoleSerializer, SysUserRole, ROLE_SUPERADMIN, ROLE_ADMIN


# 查询所有角色信息

class ListAllView(APIView):

    def get(self, request):
        obj_roleList = SysRole.objects.all().values()  # 转成字典
        roleList = list(obj_roleList)  # 把外层的容器转为List
        return JsonResponse({'code': 200, 'roleList': roleList})


class SearchView(APIView):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        pageNum = int(data['pageNum'])  # 当前页
        pageSize = int(data['pageSize'])  # 每页大小
        query = data['query']  # 查询参数
        
        # Use db_user connection explicitly
        with connections['db_user'].cursor() as cursor:
            # Count total matches
            cursor.execute(
                "SELECT COUNT(*) FROM sys_role WHERE name LIKE %s",
                ['%' + query + '%']
            )
            total = cursor.fetchone()[0]
            
            # Get paginated results - note: create_time and update_time are DateField (not DateTimeField)
            offset = (pageNum - 1) * pageSize
            cursor.execute(
                """SELECT id, name, code, remark, 
                   CASE WHEN create_time IS NOT NULL THEN date(create_time) ELSE NULL END as create_time,
                   CASE WHEN update_time IS NOT NULL THEN date(update_time) ELSE NULL END as update_time
                   FROM sys_role 
                   WHERE name LIKE %s 
                   ORDER BY id
                   LIMIT %s OFFSET %s""",
                ['%' + query + '%', pageSize, offset]
            )
            columns = [col[0] for col in cursor.description]
            roles = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        return JsonResponse({'code': 200, 'roleList': roles, 'total': total})


class SaveView(APIView):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        # 获取当前登录用户信息
        user_id = getattr(request, 'user_id', None)
        
        # 检查用户权限
        if user_id:
            # 查询用户角色
            user_roles = SysRole.objects.raw(
                "SELECT id, code, name FROM sys_role WHERE id IN "
                "(SELECT role_id FROM sys_user_role WHERE user_id=%s)", 
                [user_id]
            )
            
            # 检查用户角色
            is_superadmin = False
            is_admin = False
            
            for role in user_roles:
                if role.code == ROLE_SUPERADMIN or role.name == '超级管理员':
                    is_superadmin = True
                    break
                if role.code == ROLE_ADMIN or role.name == '管理员':
                    is_admin = True
                    
            # 只有超级管理员可以管理角色
            if not is_superadmin:
                return JsonResponse({
                    'code': 403, 
                    'message': '权限不足，只有超级管理员可以管理角色'
                }, status=403)
                
            # 只有超级管理员可以创建或修改超级管理员角色
            if not is_superadmin and data.get('code') == ROLE_SUPERADMIN:
                return JsonResponse({
                    'code': 403,
                    'message': '权限不足，只有超级管理员可以管理超级管理员角色'
                }, status=403)
                
        if data['id'] == -1:  # 添加
            obj_sysRole = SysRole(name=data['name'], code=data['code'], remark=data['remark'])
            obj_sysRole.create_time = datetime.now().date()  # Store as date, not datetime
            obj_sysRole.save()
        else:  # 修改
            obj_sysRole = SysRole(id=data['id'], name=data['name'], code=data['code'],
                                  remark=data['remark'], create_time=data['create_time'],
                                  update_time=data['update_time'])
            obj_sysRole.update_time = datetime.now().date()  # Store as date, not datetime
            obj_sysRole.save()
        return JsonResponse({'code': 200})


class ActionView(APIView):

    def get(self, request):
        """
        获取角色信息
        :param request:
        :return:
        """
        # 获取当前登录用户信息
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            return JsonResponse({'code': 401, 'message': '未授权'}, status=401)
            
        # 查询用户角色
        user_roles = SysRole.objects.raw(
            "SELECT id, code, name FROM sys_role WHERE id IN "
            "(SELECT role_id FROM sys_user_role WHERE user_id=%s)", 
            [user_id]
        )
        
        # 检查是否为超级管理员
        is_superadmin = False
        for role in user_roles:
            if role.code == ROLE_SUPERADMIN or role.name == '超级管理员':
                is_superadmin = True
                break
                
        # 非超级管理员只能查看角色列表
        if not is_superadmin:
            return JsonResponse({'code': 403, 'message': '权限不足，只有超级管理员可以查看角色详情'}, status=403)
            
        id = request.GET.get("id")
        role_object = SysRole.objects.get(id=id)
        return JsonResponse({'code': 200, 'role': SysRoleSerializer(role_object).data})

    def delete(self, request):
        """
        删除操作
        :param request:
        :return:
        """
        # 获取当前登录用户信息
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            return JsonResponse({'code': 401, 'message': '未授权'}, status=401)
            
        # 查询用户角色
        user_roles = SysRole.objects.raw(
            "SELECT id, code, name FROM sys_role WHERE id IN "
            "(SELECT role_id FROM sys_user_role WHERE user_id=%s)", 
            [user_id]
        )
        
        # 检查是否为超级管理员
        is_superadmin = False
        for role in user_roles:
            if role.code == ROLE_SUPERADMIN or role.name == '超级管理员':
                is_superadmin = True
                break
                
        # 只有超级管理员可以删除角色
        if not is_superadmin:
            return JsonResponse({'code': 403, 'message': '权限不足，只有超级管理员可以删除角色'}, status=403)
            
        idList = json.loads(request.body.decode("utf-8"))
        SysUserRole.objects.filter(role_id__in=idList).delete()
        SysRole.objects.filter(id__in=idList).delete()
        return JsonResponse({'code': 200})
