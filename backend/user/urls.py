# -*- coding: utf-8 -*-
from django.urls import path

from user import views

urlpatterns = [
    path('login', views.LoginView.as_view(), name="login"),  # 登录
    path('save', views.SaveView.as_view(), name="save"),  # 用户添加或修改
    path('updateUserPwd ', views.PwdView.as_view(), name="updateUserPwd"),  # 修改密码
    path('uploadImage ', views.ImageView.as_view(), name="uploadImage"),  # 头像上传
    path('updateAvatar', views.AvatarView.as_view(), name="updateAvatar"),  # 头像更新
    path('action', views.ActionView.as_view(), name='action'),  # 用户信息操作
    path('check', views.CheckView.as_view(), name='check'),  # 用户名查重
    path('search', views.SearchView.as_view(), name="search"),  # 用户信息分页查询
    path('resetPassword', views.PasswordView.as_view(), name='resetPassword'),  # 重置密码
    path('status', views.StatusView.as_view(), name='status'),  # 状态修改
    path('grantRole', views.GrantRole.as_view(), name='grant'),  # 角色授权
    path('test', views.TestView.as_view(), name="test"),  # 测试
    path('jwt_test', views.JwtTestView.as_view(), name="jwt_test"),  # jwt测试
]
