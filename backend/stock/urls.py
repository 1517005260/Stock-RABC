# -*- coding: utf-8 -*-

from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    # 股票信息相关
    path('list/', views.stock_list, name='stock_list'),                    # GET 股票列表
    path('detail/<str:ts_code>/', views.stock_detail, name='stock_detail'), # GET 股票详情
    path('hot/', views.get_hot_stocks, name='get_hot_stocks'),             # GET 热门股票
    path('search/', views.stock_search, name='stock_search'),              # GET 股票搜索
    path('industries/', views.stock_industries, name='stock_industries'),   # GET 行业列表
    
    # 实时数据相关
    path('realtime/data/<str:ts_code>/', views.get_realtime_data, name='get_realtime_data'),    # GET 实时数据
    path('realtime/chart/<str:ts_code>/', views.get_intraday_chart, name='get_intraday_chart'), # GET 分时图数据
    path('realtime/price/<str:ts_code>/', views.stock_realtime_price, name='stock_realtime_price'), # GET 实时价格
    path('market/overview/', views.market_overview, name='market_overview'),              # GET 市场概况
    
    # K线图和技术分析相关
    path('kline/<str:ts_code>/', views.stock_kline_data, name='stock_kline_data'),                   # GET K线数据
    path('technical/<str:ts_code>/', views.stock_technical_analysis, name='stock_technical_analysis'), # GET 技术分析
    path('holders/<str:ts_code>/', views.get_stock_holders, name='get_stock_holders'),          # GET 股票持股信息
    
    # 新闻相关
    path('news/', views.market_news_list, name='market_news_list'),                                # GET 新闻列表
    path('news/<int:news_id>/', views.market_news_detail, name='market_news_detail'),             # GET 新闻详情
    path('news/latest/', views.latest_market_news, name='latest_market_news'),                     # GET 最新新闻
    path('news/categories/', views.news_categories, name='news_categories'),                       # GET 新闻分类
    path('news/create/', views.create_market_news, name='create_market_news'),                     # POST 创建新闻（管理员）
    path('news/sync/', views.sync_news_manual, name='sync_news_manual'),                           # POST 手动同步新闻（超级管理员）
    
    # 数据同步相关（仅超级管理员）
    path('sync/', views.sync_stock_data, name='sync_stock_data'),          # POST 同步股票数据
]