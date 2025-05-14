# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from django.urls import path

from menu import views

urlpatterns = [
    # path('index/', views.index, name="index "),
    path('treeList', views.TreeListView.as_view(), name='treeList'),  # 查询权限菜单树信息
    path('save', views.SaveView.as_view(), name='save'), # 添加或者修改权限信息
    path('action', views.ActionView.as_view(), name='action'), # 权限信息操作
]
