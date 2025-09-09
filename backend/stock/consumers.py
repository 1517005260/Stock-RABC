# -*- coding: utf-8 -*-
"""
WebSocket消费者，用于实时推送股票数据
"""
import json
import asyncio
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist

from stock.models import StockBasic, StockDaily
from stock.services import RealTimeDataService
from user.models import SysUser
from utils.jwt_helper import decode_jwt_token


class StockRealTimeConsumer(AsyncWebsocketConsumer):
    """股票实时数据WebSocket消费者"""
    
    async def connect(self):
        """WebSocket连接"""
        # 获取URL参数
        self.room_name = self.scope['url_route']['kwargs'].get('room_name', 'general')
        self.room_group_name = f'stock_realtime_{self.room_name}'
        
        # 验证用户身份（可选）
        self.user = await self.get_user_from_token()
        
        # 加入房间组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # 发送连接成功消息
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected to {self.room_name} room',
            'timestamp': datetime.now().isoformat()
        }))
        
        # 如果连接成功，开始定时推送数据
        if RealTimeDataService.is_trading_time():
            await self.start_realtime_push()

    async def disconnect(self, close_code):
        """WebSocket断开连接"""
        # 离开房间组
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # 停止定时任务
        if hasattr(self, 'push_task') and self.push_task:
            self.push_task.cancel()

    async def receive(self, text_data):
        """接收客户端消息"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'subscribe':
                # 订阅特定股票
                ts_codes = text_data_json.get('ts_codes', [])
                await self.handle_subscribe(ts_codes)
                
            elif message_type == 'unsubscribe':
                # 取消订阅
                ts_codes = text_data_json.get('ts_codes', [])
                await self.handle_unsubscribe(ts_codes)
                
            elif message_type == 'get_price':
                # 获取实时价格
                ts_code = text_data_json.get('ts_code')
                if ts_code:
                    await self.send_stock_price(ts_code)
                    
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    async def handle_subscribe(self, ts_codes):
        """处理订阅请求"""
        if not hasattr(self, 'subscribed_stocks'):
            self.subscribed_stocks = set()
        
        for ts_code in ts_codes:
            self.subscribed_stocks.add(ts_code)
        
        await self.send(text_data=json.dumps({
            'type': 'subscription_success',
            'subscribed_stocks': list(self.subscribed_stocks),
            'message': f'Subscribed to {len(ts_codes)} stocks'
        }))

    async def handle_unsubscribe(self, ts_codes):
        """处理取消订阅"""
        if hasattr(self, 'subscribed_stocks'):
            for ts_code in ts_codes:
                self.subscribed_stocks.discard(ts_code)
        
        await self.send(text_data=json.dumps({
            'type': 'unsubscription_success',
            'message': f'Unsubscribed from {len(ts_codes)} stocks'
        }))

    async def send_stock_price(self, ts_code):
        """发送单只股票价格"""
        try:
            price_data = await database_sync_to_async(
                RealTimeDataService.get_stock_realtime_price
            )(ts_code)
            
            if price_data['success']:
                await self.send(text_data=json.dumps({
                    'type': 'stock_price',
                    'data': price_data['data']
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Failed to get price for {ts_code}'
                }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error getting price: {str(e)}'
            }))

    async def start_realtime_push(self):
        """开始实时推送数据"""
        try:
            # 创建定时任务，每5秒推送一次数据
            self.push_task = asyncio.create_task(self.realtime_push_loop())
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Failed to start realtime push: {str(e)}'
            }))

    async def realtime_push_loop(self):
        """实时推送循环"""
        while True:
            try:
                # 检查是否在交易时间
                is_trading = await database_sync_to_async(
                    RealTimeDataService.is_trading_time
                )()
                
                if is_trading:
                    # 推送订阅的股票数据
                    if hasattr(self, 'subscribed_stocks') and self.subscribed_stocks:
                        await self.push_subscribed_stocks()
                    else:
                        # 推送热门股票数据
                        await self.push_hot_stocks()
                
                # 等待5秒
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Push loop error: {str(e)}'
                }))
                await asyncio.sleep(5)  # 出错后等待5秒再继续

    async def push_subscribed_stocks(self):
        """推送订阅的股票数据"""
        stock_data_list = []
        
        for ts_code in list(self.subscribed_stocks)[:10]:  # 限制最多10只股票
            try:
                price_data = await database_sync_to_async(
                    RealTimeDataService.get_stock_realtime_price
                )(ts_code)
                
                if price_data['success']:
                    stock_data_list.append(price_data['data'])
            except Exception as e:
                continue  # 忽略单只股票的错误
        
        if stock_data_list:
            await self.send(text_data=json.dumps({
                'type': 'realtime_data',
                'data': stock_data_list,
                'timestamp': datetime.now().isoformat()
            }))

    async def push_hot_stocks(self):
        """推送热门股票数据"""
        try:
            # 获取热门股票数据
            from stock.services import StockDataService
            hot_stocks = await database_sync_to_async(StockDataService.get_top_stocks)(10)
            
            # 获取市场概况
            market_overview_result = await database_sync_to_async(RealTimeDataService.get_market_overview)()
            market_data = market_overview_result.get('data') if market_overview_result.get('success') else None
            
            # 获取最新财经新闻
            latest_news = await self.get_latest_news(5)
            
            message = {
                'type': 'market_data',
                'data': {
                    'hot_stocks': hot_stocks,
                    'market_overview': market_data,
                    'latest_news': latest_news,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            await self.send(text_data=json.dumps(message))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'数据推送失败: {str(e)}'
            }))

    def get_hot_stocks(self):
        """获取热门股票数据（同步方法）"""
        try:
            # 获取最新交易日的前5只涨幅最大的股票
            latest_date = StockDaily.objects.values('trade_date').order_by('-trade_date').first()
            if not latest_date:
                return []
            
            hot_stocks = StockDaily.objects.filter(
                trade_date=latest_date['trade_date'],
                pct_chg__isnull=False
            ).order_by('-pct_chg')[:5]
            
            result = []
            for stock_daily in hot_stocks:
                try:
                    stock_basic = StockBasic.objects.get(ts_code=stock_daily.ts_code)
                    result.append({
                        'ts_code': stock_daily.ts_code,
                        'name': stock_basic.name,
                        'current_price': float(stock_daily.close) if stock_daily.close else 0,
                        'change': float(stock_daily.change) if stock_daily.change else 0,
                        'pct_chg': float(stock_daily.pct_chg) if stock_daily.pct_chg else 0,
                        'volume': stock_daily.vol if stock_daily.vol else 0,
                        'amount': float(stock_daily.amount) if stock_daily.amount else 0,
                    })
                except StockBasic.DoesNotExist:
                    continue
            
            return result
        except Exception as e:
            return []

    async def get_latest_news(self, limit=5):
        """获取最新财经新闻（异步方法）"""
        try:
            from trading.models import MarketNews
            
            latest_news_data = await database_sync_to_async(self._get_latest_news_sync)(limit)
            return latest_news_data
        except Exception as e:
            return []

    def _get_latest_news_sync(self, limit):
        """获取最新新闻的同步方法"""
        try:
            from trading.models import MarketNews
            
            latest_news = MarketNews.objects.order_by('-publish_time')[:limit]
            news_list = []
            
            for news in latest_news:
                news_list.append({
                    'id': news.id,
                    'title': news.title,
                    'source': news.source,
                    'category': news.category,
                    'publish_time': news.publish_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'summary': news.content[:100] + '...' if len(news.content) > 100 else news.content,
                })
            
            return news_list
        except Exception as e:
            return []

    @database_sync_to_async
    def get_user_from_token(self):
        """从JWT token获取用户（可选功能）"""
        try:
            # 从查询参数或头部获取token
            query_params = dict(self.scope.get('query_string', b'').decode().split('&'))
            token = query_params.get('token')
            
            if token:
                payload = decode_jwt_token(token)
                if payload:
                    user = SysUser.objects.get(id=payload['user_id'])
                    return user
        except:
            pass
        return None

    # WebSocket消息处理方法
    async def stock_price_update(self, event):
        """处理股票价格更新消息"""
        await self.send(text_data=json.dumps({
            'type': 'stock_price_update',
            'data': event['data']
        }))

    async def market_status_update(self, event):
        """处理市场状态更新消息"""
        await self.send(text_data=json.dumps({
            'type': 'market_status',
            'data': event['data']
        }))


class UserNotificationConsumer(AsyncWebsocketConsumer):
    """用户通知WebSocket消费者"""
    
    async def connect(self):
        """连接处理"""
        self.user_id = self.scope['url_route']['kwargs'].get('user_id')
        if not self.user_id:
            await self.close()
            return
        
        self.room_group_name = f'user_notifications_{self.user_id}'
        
        # 验证用户身份
        user = await self.get_user(self.user_id)
        if not user:
            await self.close()
            return
        
        # 加入个人通知组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        """断开连接"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """接收消息"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
        except:
            pass

    @database_sync_to_async
    def get_user(self, user_id):
        """获取用户"""
        try:
            return SysUser.objects.get(id=user_id)
        except SysUser.DoesNotExist:
            return None

    # 通知处理方法
    async def trade_notification(self, event):
        """交易通知"""
        await self.send(text_data=json.dumps({
            'type': 'trade_notification',
            'data': event['data']
        }))

    async def system_notification(self, event):
        """系统通知"""
        await self.send(text_data=json.dumps({
            'type': 'system_notification',
            'data': event['data']
        }))