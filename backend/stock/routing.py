# -*- coding: utf-8 -*-
"""
WebSocket路由配置
"""
from django.urls import re_path
from stock.consumers import StockRealTimeConsumer, UserNotificationConsumer

websocket_urlpatterns = [
    # 股票实时数据WebSocket
    re_path(r'ws/stock/realtime/(?P<room_name>\w+)/$', StockRealTimeConsumer.as_asgi()),
    
    # 用户通知WebSocket
    re_path(r'ws/user/notifications/(?P<user_id>\d+)/$', UserNotificationConsumer.as_asgi()),
    
    # 通用股票数据WebSocket
    re_path(r'ws/stock/general/$', StockRealTimeConsumer.as_asgi(), {'room_name': 'general'}),
]