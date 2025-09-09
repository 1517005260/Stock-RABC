# -*- coding: utf-8 -*-

from django.urls import path
from . import views

app_name = 'trading'

urlpatterns = [
    # 交易相关
    path('buy/', views.buy_stock, name='buy_stock'),                      # POST 买入股票
    path('sell/', views.sell_stock, name='sell_stock'),                   # POST 卖出股票
    
    # 账户相关
    path('account/', views.get_account_info, name='get_account_info'),     # GET 获取账户信息
    path('positions/', views.get_positions, name='get_positions'),         # GET 获取持仓信息
    path('records/', views.get_trade_records, name='get_trade_records'),   # GET 获取交易记录
    
    # 自选股相关
    path('watchlist/', views.get_watchlist, name='get_watchlist'),         # GET 获取自选股
    path('watchlist/add/', views.add_to_watchlist, name='add_to_watchlist'), # POST 添加自选股
    path('watchlist/remove/<str:ts_code>/', views.remove_from_watchlist, name='remove_from_watchlist'), # DELETE 移除自选股
]