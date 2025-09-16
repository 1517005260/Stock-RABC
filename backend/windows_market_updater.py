#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Windows 市场数据自动更新器
自动更新Redis缓存的大盘数据，替代Linux下的cron任务

功能：
1. 30分钟自动更新一次市场数据
2. 自动重试机制
3. 日志记录
4. Windows服务友好
"""

import os
import sys
import time
import datetime
import threading
import signal
import logging
from pathlib import Path

# 设置Django环境
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

import django
django.setup()

from stock.redis_cache import MarketDataCache

# 配置日志
log_dir = BASE_DIR / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'market_updater_{datetime.date.today()}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class WindowsMarketUpdater:
    """Windows市场数据更新器"""

    def __init__(self, update_interval=30*60):  # 默认30分钟
        self.update_interval = update_interval
        self.running = False
        self.thread = None

    def start(self):
        """启动更新器"""
        if self.running:
            logger.warning("更新器已在运行中")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"市场数据更新器已启动，更新间隔: {self.update_interval//60}分钟")

    def stop(self):
        """停止更新器"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        logger.info("市场数据更新器已停止")

    def _run_loop(self):
        """主循环"""
        # 启动后立即执行一次更新
        self._update_market_data()

        while self.running:
            try:
                # 等待指定时间间隔
                for _ in range(self.update_interval):
                    if not self.running:
                        break
                    time.sleep(1)

                if self.running:
                    self._update_market_data()

            except Exception as e:
                logger.error(f"更新循环异常: {e}")
                time.sleep(60)  # 出错后等待1分钟再重试

    def _update_market_data(self):
        """更新市场数据"""
        try:
            logger.info("开始更新市场数据缓存...")
            start_time = time.time()

            # 强制刷新缓存
            result = MarketDataCache.force_refresh()

            duration = time.time() - start_time

            if result['success']:
                market_stats = result['data']['market_stats']
                logger.info(f"✅ 市场数据更新成功! 耗时: {duration:.2f}秒")
                logger.info(f"   - 股票数量: {market_stats.get('total_count', 0)}只")
                logger.info(f"   - 上涨: {market_stats.get('up_count', 0)}只 "
                           f"({market_stats.get('up_count', 0) / market_stats.get('total_count', 1) * 100:.1f}%)")
                logger.info(f"   - 下跌: {market_stats.get('down_count', 0)}只 "
                           f"({market_stats.get('down_count', 0) / market_stats.get('total_count', 1) * 100:.1f}%)")
                logger.info(f"   - 净流入: {market_stats.get('net_inflow', 0)}亿元")
                logger.info(f"   - 数据源: {result['data'].get('data_source', '未知')}")

                # 记录成功统计
                self._log_success_stats(market_stats)

            else:
                logger.error(f"❌ 市场数据更新失败: {result['message']}")

        except Exception as e:
            logger.error(f"❌ 市场数据更新异常: {e}")

    def _log_success_stats(self, stats):
        """记录成功统计到独立文件"""
        stats_file = BASE_DIR / 'logs' / 'market_stats.log'
        try:
            with open(stats_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"{timestamp},{stats.get('total_count', 0)},{stats.get('up_count', 0)},"
                       f"{stats.get('down_count', 0)},{stats.get('net_inflow', 0)}\n")
        except Exception as e:
            logger.warning(f"统计日志写入失败: {e}")

    def update_once(self):
        """手动执行一次更新"""
        logger.info("执行手动更新...")
        self._update_market_data()


def signal_handler(sig, frame):
    """信号处理器"""
    logger.info("收到退出信号，正在关闭...")
    global updater
    if updater:
        updater.stop()
    sys.exit(0)


def main():
    """主函数"""
    global updater

    # 检查Redis连接
    try:
        from django.core.cache import cache
        cache.get('test_connection')
        logger.info("✅ Redis连接正常")
    except Exception as e:
        logger.error(f"❌ Redis连接失败: {e}")
        logger.error("请确保Redis服务正在运行: redis-server")
        return

    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 解析命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            # 只执行一次更新
            updater = WindowsMarketUpdater()
            updater.update_once()
            return
        elif sys.argv[1] == '--interval':
            # 自定义更新间隔（分钟）
            try:
                interval_minutes = int(sys.argv[2])
                update_interval = interval_minutes * 60
                logger.info(f"使用自定义更新间隔: {interval_minutes}分钟")
            except (IndexError, ValueError):
                logger.error("使用方法: python windows_market_updater.py --interval <分钟数>")
                return
        else:
            update_interval = 30 * 60  # 默认30分钟
    else:
        update_interval = 30 * 60  # 默认30分钟

    # 创建并启动更新器
    updater = WindowsMarketUpdater(update_interval)
    updater.start()

    logger.info("=" * 60)
    logger.info("Windows 市场数据自动更新器")
    logger.info("=" * 60)
    logger.info("使用方法:")
    logger.info("  python windows_market_updater.py              # 30分钟自动更新")
    logger.info("  python windows_market_updater.py --once       # 只执行一次更新")
    logger.info("  python windows_market_updater.py --interval 15 # 15分钟自动更新")
    logger.info("")
    logger.info("按 Ctrl+C 停止程序")
    logger.info("=" * 60)

    try:
        # 保持主线程运行
        while updater.running:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    finally:
        updater.stop()


if __name__ == "__main__":
    main()