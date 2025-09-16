# -*- coding: utf-8 -*-

import json
import time
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
from stock.services import RealTimeDataService


class MarketDataCache:
    """市场数据Redis缓存管理"""

    CACHE_KEY = settings.MARKET_DATA_CACHE['CACHE_KEY']
    EXPIRE_TIME = settings.MARKET_DATA_CACHE['EXPIRE_TIME']
    UPDATE_INTERVAL = settings.MARKET_DATA_CACHE['UPDATE_INTERVAL']

    @classmethod
    def get_market_data(cls):
        """获取市场数据（优先从缓存获取）"""
        try:
            # 1. 尝试从Redis缓存获取
            cached_data = cache.get(cls.CACHE_KEY)

            if cached_data:
                print(f"从Redis缓存获取市场数据成功")
                return {
                    'success': True,
                    'data': cached_data['data'],
                    'message': f'缓存数据 (更新时间: {cached_data["update_time"]})',
                    'is_cached': True,
                    'cache_time': cached_data['update_time']
                }

            # 2. 缓存未命中，获取实时数据并缓存
            print(f"Redis缓存未命中，获取实时市场数据...")
            return cls.refresh_market_data()

        except Exception as e:
            print(f"Redis缓存获取失败: {e}")
            # 缓存失败时直接获取实时数据
            return RealTimeDataService.get_market_overview()

    @classmethod
    def refresh_market_data(cls):
        """刷新市场数据到缓存"""
        try:
            print("开始获取完整市场数据...")
            start_time = time.time()

            # 获取实时市场数据
            result = RealTimeDataService.get_market_overview()

            end_time = time.time()
            fetch_duration = round(end_time - start_time, 2)

            if result and result.get('success'):
                # 准备缓存数据
                cache_data = {
                    'data': result['data'],
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'fetch_duration': fetch_duration,
                    'data_source': result['data'].get('data_source', '东方财富完整数据'),
                    'sample_size': result['data'].get('sample_size', 0)
                }

                # 存储到Redis缓存
                cache.set(cls.CACHE_KEY, cache_data, cls.EXPIRE_TIME)
                print(f"市场数据已缓存到Redis，耗时{fetch_duration}秒，{cls.EXPIRE_TIME/60}分钟后过期")

                return {
                    'success': True,
                    'data': result['data'],
                    'message': f'实时数据 (耗时{fetch_duration}秒)',
                    'is_cached': False,
                    'fetch_duration': fetch_duration,
                    'cache_time': cache_data['update_time']
                }
            else:
                error_msg = result.get('message', '获取市场数据失败') if result else '市场数据服务不可用'
                print(f"获取实时市场数据失败: {error_msg}")
                return {
                    'success': False,
                    'message': error_msg,
                    'data': cls._get_default_data()
                }

        except Exception as e:
            print(f"刷新市场数据失败: {e}")
            return {
                'success': False,
                'message': f'刷新市场数据异常: {str(e)}',
                'data': cls._get_default_data()
            }

    @classmethod
    def force_refresh(cls):
        """强制刷新缓存（忽略过期时间）"""
        print("强制刷新市场数据缓存...")
        # 先清除旧缓存
        cache.delete(cls.CACHE_KEY)
        # 获取新数据
        return cls.refresh_market_data()

    @classmethod
    def get_cache_info(cls):
        """获取缓存信息"""
        try:
            cached_data = cache.get(cls.CACHE_KEY)
            if cached_data:
                return {
                    'cached': True,
                    'update_time': cached_data['update_time'],
                    'fetch_duration': cached_data.get('fetch_duration', 0),
                    'data_source': cached_data.get('data_source', '未知'),
                    'sample_size': cached_data.get('sample_size', 0),
                    'expire_time': cls.EXPIRE_TIME
                }
            else:
                return {
                    'cached': False,
                    'message': '缓存为空'
                }
        except Exception as e:
            return {
                'cached': False,
                'error': str(e)
            }

    @classmethod
    def clear_cache(cls):
        """清除市场数据缓存"""
        try:
            cache.delete(cls.CACHE_KEY)
            print("市场数据缓存已清除")
            return True
        except Exception as e:
            print(f"清除缓存失败: {e}")
            return False

    @classmethod
    def _get_default_data(cls):
        """获取默认数据结构"""
        return {
            'market_stats': {
                'up_count': 0,
                'down_count': 0,
                'flat_count': 0,
                'limit_up_count': 0,
                'limit_down_count': 0,
                'total_count': 0,
                'net_inflow': 0,
                'total_inflow': 0,
                'total_outflow': 0,
                'stocks_with_flow_data': 0
            },
            'indices': [],
            'timestamp': datetime.now().isoformat(),
            'data_source': '默认数据',
            'sample_size': 0
        }


def update_market_data_task():
    """定时任务：更新市场数据到缓存"""
    try:
        print(f"[定时任务] 开始更新市场数据缓存 - {datetime.now()}")
        result = MarketDataCache.refresh_market_data()

        if result['success']:
            print(f"[定时任务] 市场数据更新成功 - 耗时{result.get('fetch_duration', 0)}秒")
        else:
            print(f"[定时任务] 市场数据更新失败 - {result['message']}")

    except Exception as e:
        print(f"[定时任务] 更新市场数据异常: {e}")


if __name__ == "__main__":
    # 测试缓存功能
    import os
    import sys
    import django

    # 设置Django环境
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
    django.setup()

    print("测试市场数据缓存...")

    # 获取缓存信息
    cache_info = MarketDataCache.get_cache_info()
    print(f"缓存信息: {cache_info}")

    # 获取市场数据
    result = MarketDataCache.get_market_data()
    print(f"获取结果: 成功={result['success']}, 消息={result['message']}")

    if result['success']:
        market_stats = result['data']['market_stats']
        print(f"市场统计: 上涨{market_stats['up_count']}, 下跌{market_stats['down_count']}, 净流入{market_stats['net_inflow']}亿")