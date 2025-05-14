# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from django.urls import path

from role import views

urlpatterns = [
    # path('index/', views.index, name="index "),
    path('listAll', views.ListAllView.as_view(), name='listAll'),  # 查询所有角色信息
    path('search', views.SearchView.as_view(), name='search'),  # 角色信息查询
    path('save', views.SaveView.as_view(), name='save'),  # 角色信息查询
    path('action', views.ActionView.as_view(), name='action'),  # 角色信息查询
    path('menus', views.MenusView.as_view(), name='menus'),  # 根据角色查询菜单权限
    path('grant', views.GrantMenu.as_view(), name='grant'),  # 角色权限授权
]
