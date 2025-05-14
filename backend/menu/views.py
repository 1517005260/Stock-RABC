import json
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView

from menu.models import SysMenu, SysMenuSerializer, SysRoleMenu


class TreeListView(APIView):
    # 构造菜单树
    def buildTreeMenu(self, sysMenuList):
        resultMenuList: list[SysMenu] = list()
        for menu in sysMenuList:
            # 寻找子节点
            for e in sysMenuList:
                if e.parent_id == menu.id:
                    if not hasattr(menu, "children"):
                        menu.children = list()
                    menu.children.append(e)
            # 判断父节点，添加到集合
            if menu.parent_id == 0:
                resultMenuList.append(menu)
        return resultMenuList

    def get(self, request):
        menuQuerySet = SysMenu.objects.order_by("order_num")
        # 构造菜单树
        sysMenuList: list[SysMenu] = self.buildTreeMenu(menuQuerySet)
        serializerMenuList: list[SysMenuSerializer] = list()
        for sysMenu in sysMenuList:
            serializerMenuList.append(SysMenuSerializer(sysMenu).data)
        return JsonResponse({'code': 200, 'treeList': serializerMenuList})


class SaveView(APIView):
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))

        if data['id'] == -1:  # 添加
            obj_sysMenu = SysMenu(name=data['name'], icon=data['icon'], parent_id=data['parent_id'],
                                  order_num=data['order_num'], path=data['path'], component=data['component'],
                                  menu_type=data['menu_type'], perms=data['perms'], remark=data['remark'])
            obj_sysMenu.create_time = datetime.now().date()
            obj_sysMenu.save()
        else:  # 修改
            obj_sysMenu = SysMenu(id=data['id'], name=data['name'], icon=data['icon'], parent_id=data['parent_id'],
                                  order_num=data['order_num'], path=data['path'], component=data['component'],
                                  menu_type=data['menu_type'], perms=data['perms'], remark=data['remark'],
                                  create_time=data['create_time'], update_time=data['update_time'])
            obj_sysMenu.update_time = datetime.now().date()
            obj_sysMenu.save()
        return JsonResponse({'code': 200})


# 菜单基本操作
class ActionView(APIView):
    def get(self, request):
        """
        根据id获取权限信息
        :param request:
        :return:
        """
        id = request.GET.get("id")
        menu_object = SysMenu.objects.get(id=id)
        return JsonResponse({'code': 200, 'menu': SysMenuSerializer(menu_object).data})

    def delete(self, request):
        """
        删除操作
        :param request:
        :return:
        """
        id = json.loads(request.body.decode("utf-8"))
        if SysMenu.objects.filter(parent_id=id).count() > 0:
            return JsonResponse({'code': 500, 'msg': '请先删除子菜单！'})
        else:
            SysRoleMenu.objects.filter(menu_id=id).delete()
            SysMenu.objects.get(id=id).delete()
            return JsonResponse({'code': 200})
