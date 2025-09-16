# -*- coding: utf-8 -*-

"""
市场数据定时更新任务
使用django-crontab实现30分钟自动更新市场数据缓存
"""

import os
import sys
import django
from pathlib import Path

# 设置Django环境
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from datetime import datetime
from stock.redis_cache import MarketDataCache


def update_market_cache():
    """定时任务：更新市场数据缓存"""
    try:
        print(f"\n[定时任务] 开始更新市场数据缓存 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 强制刷新缓存
        result = MarketDataCache.force_refresh()

        if result['success']:
            market_stats = result['data']['market_stats']
            print(f"✅ [定时任务] 市场数据更新成功!")
            print(f"   - 股票数量: {market_stats.get('total_count', 0)}只")
            print(f"   - 上涨: {market_stats.get('up_count', 0)}只 ({market_stats.get('up_count', 0) / market_stats.get('total_count', 1) * 100:.1f}%)")
            print(f"   - 下跌: {market_stats.get('down_count', 0)}只 ({market_stats.get('down_count', 0) / market_stats.get('total_count', 1) * 100:.1f}%)")
            print(f"   - 净流入: {market_stats.get('net_inflow', 0)}亿元")
            print(f"   - 获取耗时: {result.get('fetch_duration', 0)}秒")
            print(f"   - 数据源: {result['data'].get('data_source', '未知')}")
            print(f"   - 下次更新时间: 30分钟后")
        else:
            print(f"❌ [定时任务] 市场数据更新失败: {result['message']}")

    except Exception as e:
        print(f"❌ [定时任务] 市场数据更新异常: {e}")


def check_market_cache_status():
    """检查市场数据缓存状态"""
    try:
        print(f"\n[状态检查] 市场数据缓存状态 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        cache_info = MarketDataCache.get_cache_info()

        if cache_info['cached']:
            print(f"✅ 缓存状态: 正常")
            print(f"   - 更新时间: {cache_info['update_time']}")
            print(f"   - 数据源: {cache_info['data_source']}")
            print(f"   - 样本数量: {cache_info['sample_size']}只股票")
            print(f"   - 获取耗时: {cache_info['fetch_duration']}秒")
        else:
            print(f"⚠️ 缓存状态: 无缓存数据")
            if 'error' in cache_info:
                print(f"   - 错误: {cache_info['error']}")

    except Exception as e:
        print(f"❌ [状态检查] 缓存状态检查异常: {e}")


if __name__ == "__main__":
    # 可以直接运行此脚本进行测试
    print("市场数据定时任务测试")
    print("=" * 40)

    # 检查当前缓存状态
    check_market_cache_status()

    # 更新缓存
    update_market_cache()

    # 再次检查状态
    check_market_cache_status()