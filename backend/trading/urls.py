# -*- coding: utf-8 -*-

from django.urls import path
from . import views

app_name = 'trading'

urlpatterns = [
    # 交易相关
    path('buy/', views.buy_stock, name='buy_stock'),                      # POST 买入股票
    path('sell/', views.sell_stock, name='sell_stock'),                   # POST 卖出股票
    path('cancel/', views.cancel_trade, name='cancel_trade'),             # POST 撤销交易
    
    # 账户相关
    path('account/', views.get_account_info, name='get_account_info'),     # GET 获取账户信息
    path('positions/', views.get_positions, name='get_positions'),         # GET 获取持仓信息
    path('records/', views.get_trade_records, name='get_trade_records'),   # GET 获取交易记录
    path('statistics/', views.trading_statistics, name='trading_statistics'), # GET 获取交易统计
    
    # 自选股相关
    path('watchlist/', views.get_watchlist, name='get_watchlist'),         # GET 获取自选股
    path('watchlist/add/', views.add_to_watchlist, name='add_to_watchlist'), # POST 添加自选股
    path('watchlist/remove/<str:ts_code>/', views.remove_from_watchlist, name='remove_from_watchlist'), # DELETE 移除自选股
    
    # 新闻相关
    path('news/', views.get_news_list, name='get_news_list'),              # GET 获取新闻列表
    path('news/<int:news_id>/', views.get_news_detail, name='get_news_detail'), # GET 获取新闻详情
    
    # 管理员功能 - 用户管理
    path('admin/accounts/', views.admin_user_accounts, name='admin_user_accounts'), # GET 管理员查看用户账户
    path('admin/records/', views.admin_user_records, name='admin_user_records'),     # GET 管理员查看用户交易记录
    path('admin/assets/adjust/', views.admin_adjust_assets, name='admin_adjust_assets'), # POST 管理员调整用户资产
    path('admin/freeze-user/', views.admin_freeze_user, name='admin_freeze_user'),   # POST 管理员冻结用户
    
    # 管理员功能 - 新闻管理
    path('admin/news/', views.admin_news_list, name='admin_news_list'),             # GET 管理员获取新闻列表
    path('admin/news/create/', views.admin_create_news, name='admin_create_news'),  # POST 管理员创建新闻
    path('admin/news/<int:news_id>/update/', views.admin_update_news, name='admin_update_news'), # PUT 管理员更新新闻
    path('admin/news/<int:news_id>/delete/', views.admin_delete_news, name='admin_delete_news'), # DELETE 管理员删除新闻
    
    # 管理员功能 - 系统管理
    path('admin/logs/', views.admin_operation_logs, name='admin_operation_logs'),   # GET 管理员操作日志
    path('admin/statistics/', views.admin_statistics, name='admin_statistics'),     # GET 管理员统计信息
]