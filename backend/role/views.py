import json
from datetime import datetime

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView

from menu.models import SysRoleMenu
from role.models import SysRole, SysRoleSerializer, SysUserRole


# 查询所有角色信息

class ListAllView(APIView):

    def get(self, request):
        obj_roleList = SysRole.objects.all().values()  # 转成字典
        roleList = list(obj_roleList)  # 把外层的容器转为List
        return JsonResponse({'code': 200, 'roleList': roleList})


class SearchView(APIView):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        pageNum = data['pageNum']  # 当前页
        pageSize = data['pageSize']  # 每页大小
        query = data['query']  # 查询参数
        print(pageNum, pageSize)
        roleListPage = Paginator(SysRole.objects.filter(name__icontains=query), pageSize).page(pageNum)
        obj_roles = roleListPage.object_list.values()  # 转成字典
        roles = list(obj_roles)  # 把外层的容器转为List
        total = SysRole.objects.filter(name__icontains=query).count()
        return JsonResponse({'code': 200, 'roleList': roles, 'total': total})


class SaveView(APIView):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        if data['id'] == -1:  # 添加
            obj_sysRole = SysRole(name=data['name'], code=data['code'], remark=data['remark'])
            obj_sysRole.create_time = datetime.now().date()
            obj_sysRole.save()
        else:  # 修改
            obj_sysRole = SysRole(id=data['id'], name=data['name'], code=data['code'],
                                  remark=data['remark'], create_time=data['create_time'],
                                  update_time=data['update_time'])
            obj_sysRole.update_time = datetime.now().date()
            obj_sysRole.save()
        return JsonResponse({'code': 200})


class ActionView(APIView):

    def get(self, request):
        """
        根据id获取角色信息
        :param request:
        :return:
        """
        id = request.GET.get('id')
        role_object = SysRole.objects.get(id=id)
        return JsonResponse({'code': 200, 'role': SysRoleSerializer(role_object).data})

    def delete(self, request):
        """
        删除操作
        :param request:
        :return:
        """
        idList = json.loads(request.body.decode('utf-8'))
        SysUserRole.objects.filter(role_id__in=idList).delete()
        SysRoleMenu.objects.filter(role_id__in=idList).delete()
        SysRole.objects.filter(id__in=idList).delete()
        return JsonResponse({'code': 200})


# 根据角色查询菜单权限
class MenusView(APIView):
    def get(self, request):
        id = request.GET.get("id")
        menuList = SysRoleMenu.objects.filter(role_id=id).values("menu_id")
        menuIdList = [m['menu_id'] for m in menuList]
        print("menuIdList=", menuIdList)
        return JsonResponse({'code': 200, 'menuIdList': menuIdList})


class GrantMenu(APIView):
    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        role_id = data['id']
        menuIdList = data['menuIds']
        print(role_id, menuIdList)
        SysRoleMenu.objects.filter(role_id=role_id).delete()  # 删除角色菜单关联表中的指定角色数据
        for menuId in menuIdList:
            roleMenu = SysRoleMenu(role_id=role_id, menu_id=menuId)
            roleMenu.save()
        return JsonResponse({'code': 200})
