# -*- coding: utf-8 -*-

from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    # 股票信息相关
    path('list/', views.stock_list, name='stock_list'),                    # GET 股票列表
    path('detail/<str:ts_code>/', views.stock_detail, name='stock_detail'), # GET 股票详情
    path('hot/', views.stock_hot_list, name='stock_hot_list'),             # GET 热门股票
    path('search/', views.stock_search, name='stock_search'),              # GET 股票搜索
    path('industries/', views.stock_industries, name='stock_industries'),   # GET 行业列表
    
    # 数据同步相关（仅超级管理员）
    path('sync/', views.sync_stock_data, name='sync_stock_data'),          # POST 同步股票数据
]