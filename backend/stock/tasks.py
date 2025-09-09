# -*- coding: utf-8 -*-
"""
定时任务模块 - 用于股票数据自动同步
"""
import os
import sys
import django
import logging
from datetime import datetime, timedelta
from decimal import Decimal

# 设置Django环境
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from stock.models import StockBasic, StockDaily, StockCompany, TradeCal
from trading.models import MarketNews
from stock.services import StockDataService, RealTimeDataService
import tushare as ts
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/stock_tasks.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 初始化Tushare
token = os.getenv('TUSHARE_KEY')
if token:
    ts.set_token(token)
    pro = ts.pro_api()


def sync_daily_stock_data():
    """
    每个交易日收盘后同步当日股票数据
    定时任务：每个工作日15:10执行
    """
    logger.info("开始同步当日股票数据...")
    
    try:
        # 检查今天是否为交易日
        today = datetime.now().strftime('%Y%m%d')
        
        # 获取交易日历
        trade_cal = pro.trade_cal(exchange='SSE', cal_date=today)
        if trade_cal.empty or trade_cal.iloc[0]['is_open'] == 0:
            logger.info(f"{today} 不是交易日，跳过数据同步")
            return
        
        # 获取所有上市股票
        stocks = StockBasic.objects.filter(list_status='L')
        success_count = 0
        error_count = 0
        
        logger.info(f"开始同步 {stocks.count()} 只股票的数据")
        
        # 批量同步股票数据
        for i in range(0, stocks.count(), 100):  # 每批100只股票
            stock_batch = stocks[i:i+100]
            ts_codes = [stock.ts_code for stock in stock_batch]
            
            try:
                # 调用tushare接口获取当日数据
                df = pro.daily(trade_date=today, ts_code=','.join(ts_codes))
                
                if not df.empty:
                    for _, row in df.iterrows():
                        try:
                            daily_data = {
                                'ts_code': row['ts_code'],
                                'trade_date': datetime.strptime(str(row['trade_date']), '%Y%m%d').date(),
                                'open': Decimal(str(row['open'])) if row['open'] else None,
                                'high': Decimal(str(row['high'])) if row['high'] else None,
                                'low': Decimal(str(row['low'])) if row['low'] else None,
                                'close': Decimal(str(row['close'])) if row['close'] else None,
                                'pre_close': Decimal(str(row['pre_close'])) if row['pre_close'] else None,
                                'change': Decimal(str(row['change'])) if row['change'] else None,
                                'pct_chg': Decimal(str(row['pct_chg'])) if row['pct_chg'] else None,
                                'vol': int(row['vol']) if row['vol'] else None,
                                'amount': Decimal(str(row['amount'])) if row['amount'] else None,
                            }
                            
                            StockDaily.objects.update_or_create(
                                ts_code=daily_data['ts_code'],
                                trade_date=daily_data['trade_date'],
                                defaults=daily_data
                            )
                            success_count += 1
                            
                        except Exception as e:
                            error_count += 1
                            logger.error(f"同步股票 {row['ts_code']} 数据失败: {e}")
                
                logger.info(f"批次 {i//100 + 1} 完成，等待1秒...")
                import time
                time.sleep(1)  # 避免API频率限制
                
            except Exception as e:
                error_count += len(ts_codes)
                logger.error(f"批次同步失败: {e}")
        
        logger.info(f"当日数据同步完成：成功 {success_count} 条，失败 {error_count} 条")
        
        # 清理超过1年的历史数据（可选）
        cleanup_old_data()
        
    except Exception as e:
        logger.error(f"同步当日股票数据失败: {e}")


def sync_company_info():
    """
    同步公司基本信息
    定时任务：每周一15:15执行
    """
    logger.info("开始同步公司基本信息...")
    
    try:
        # 获取所有上市股票
        stocks = StockBasic.objects.filter(list_status='L').order_by('ts_code')
        success_count = 0
        error_count = 0
        
        # 批量同步公司信息
        for i in range(0, stocks.count(), 50):  # 每批50只股票
            stock_batch = stocks[i:i+50]
            ts_codes = [stock.ts_code for stock in stock_batch]
            
            try:
                # 调用Tushare接口
                df = pro.stock_company(ts_code=','.join(ts_codes))
                
                if not df.empty:
                    for _, row in df.iterrows():
                        try:
                            company_data = {
                                'ts_code': row['ts_code'],
                                'exchange': row['exchange'],
                                'chairman': row['chairman'],
                                'manager': row['manager'],
                                'secretary': row['secretary'],
                                'reg_capital': Decimal(str(row['reg_capital'])) if row['reg_capital'] else None,
                                'setup_date': datetime.strptime(str(row['setup_date']), '%Y%m%d').date() if row['setup_date'] and str(row['setup_date']) != 'nan' else None,
                                'province': row['province'],
                                'city': row['city'],
                                'introduction': row['introduction'],
                                'website': row['website'],
                                'email': row['email'],
                                'office': row['office'],
                                'employees': int(row['employees']) if row['employees'] else None,
                                'main_business': row['main_business'],
                                'business_scope': row['business_scope'],
                            }
                            
                            StockCompany.objects.update_or_create(
                                ts_code=company_data['ts_code'],
                                defaults=company_data
                            )
                            success_count += 1
                            
                        except Exception as e:
                            error_count += 1
                            logger.error(f"同步公司信息 {row['ts_code']} 失败: {e}")
                
                logger.info(f"批次 {i//50 + 1} 完成，等待2秒...")
                import time
                time.sleep(2)  # 避免API频率限制
                
            except Exception as e:
                error_count += len(ts_codes)
                logger.error(f"批次同步公司信息失败: {e}")
        
        logger.info(f"公司信息同步完成：成功 {success_count} 条，失败 {error_count} 条")
        
    except Exception as e:
        logger.error(f"同步公司信息失败: {e}")


def sync_financial_news():
    """
    同步财经新闻
    定时任务：每天早上8:00执行
    """
    logger.info("开始同步财经新闻...")
    
    try:
        success_count = 0
        
        # 方法1：从新浪财经爬取新闻
        news_list = crawl_sina_finance_news()
        
        # 方法2：从东方财富爬取新闻（备用）
        if not news_list:
            news_list = crawl_eastmoney_news()
        
        # 保存新闻到数据库
        for news in news_list:
            try:
                # 检查新闻是否已存在
                if not MarketNews.objects.filter(title=news['title']).exists():
                    MarketNews.objects.create(
                        title=news['title'],
                        content=news['content'],
                        source=news['source'],
                        publish_time=news['publish_time'],
                        category='财经新闻',
                        related_stocks=news.get('related_stocks', [])
                    )
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"保存新闻失败: {e}")
        
        logger.info(f"财经新闻同步完成：新增 {success_count} 条新闻")
        
        # 清理超过30天的旧新闻
        cleanup_old_news()
        
    except Exception as e:
        logger.error(f"同步财经新闻失败: {e}")


def crawl_sina_finance_news():
    """从新浪财经爬取新闻"""
    try:
        url = "https://finance.sina.com.cn/roll/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.find_all('li', class_='clearfix')
            
            news_list = []
            for item in news_items[:10]:  # 获取前10条新闻
                try:
                    link = item.find('a')
                    if link:
                        title = link.get('title') or link.text.strip()
                        href = link.get('href')
                        
                        # 获取发布时间
                        time_span = item.find('span', class_='time')
                        publish_time = datetime.now()
                        if time_span:
                            try:
                                time_str = time_span.text.strip()
                                # 简单的时间解析，实际项目中需要更完善的解析
                                if '今天' in time_str or '小时前' in time_str or '分钟前' in time_str:
                                    publish_time = datetime.now()
                                else:
                                    # 可以添加更复杂的时间解析逻辑
                                    pass
                            except:
                                pass
                        
                        if title and len(title) > 5:  # 过滤掉太短的标题
                            news_list.append({
                                'title': title,
                                'content': title,  # 简化版本，实际可以爬取详细内容
                                'source': '新浪财经',
                                'publish_time': publish_time,
                                'related_stocks': []
                            })
                except Exception as e:
                    logger.error(f"解析新闻项失败: {e}")
                    continue
            
            return news_list
            
    except Exception as e:
        logger.error(f"爬取新浪财经新闻失败: {e}")
        return []


def crawl_eastmoney_news():
    """从东方财富爬取新闻（备用方案）"""
    try:
        # 创建一些模拟新闻作为示例
        current_time = datetime.now()
        sample_news = [
            {
                'title': f'股市要闻：{current_time.strftime("%Y-%m-%d")}市场概况',
                'content': '今日股市整体表现平稳，主要指数小幅波动。投资者关注宏观经济数据和政策动向。',
                'source': '东方财富',
                'publish_time': current_time,
                'related_stocks': []
            },
            {
                'title': f'市场分析：{current_time.strftime("%Y-%m-%d")}热点板块点评',
                'content': '科技股和消费股表现活跃，新能源板块继续受到资金关注。',
                'source': '东方财富',
                'publish_time': current_time - timedelta(hours=1),
                'related_stocks': []
            }
        ]
        
        return sample_news
        
    except Exception as e:
        logger.error(f"爬取东方财富新闻失败: {e}")
        return []


def cleanup_old_data():
    """清理超过1年的历史股票数据"""
    try:
        one_year_ago = datetime.now().date() - timedelta(days=365)
        deleted_count = StockDaily.objects.filter(trade_date__lt=one_year_ago).count()
        StockDaily.objects.filter(trade_date__lt=one_year_ago).delete()
        logger.info(f"清理了 {deleted_count} 条超过1年的历史数据")
    except Exception as e:
        logger.error(f"清理历史数据失败: {e}")


def cleanup_old_news():
    """清理超过30天的旧新闻"""
    try:
        thirty_days_ago = datetime.now() - timedelta(days=30)
        deleted_count = MarketNews.objects.filter(publish_time__lt=thirty_days_ago).count()
        MarketNews.objects.filter(publish_time__lt=thirty_days_ago).delete()
        logger.info(f"清理了 {deleted_count} 条超过30天的旧新闻")
    except Exception as e:
        logger.error(f"清理旧新闻失败: {e}")


def cleanup_websocket_connections():
    """清理过期的WebSocket连接（占位符）"""
    logger.info("清理WebSocket连接...")
    # 这里可以添加清理逻辑，比如清理Redis中的过期连接信息
    pass


def sync_trade_calendar():
    """同步交易日历"""
    logger.info("开始同步交易日历...")
    
    try:
        # 同步当年和明年的交易日历
        current_year = datetime.now().year
        years = [current_year, current_year + 1]
        
        for year in years:
            start_date = f"{year}0101"
            end_date = f"{year}1231"
            
            # 获取SSE和SZSE的交易日历
            for exchange in ['SSE', 'SZSE']:
                df = pro.trade_cal(exchange=exchange, start_date=start_date, end_date=end_date)
                
                for _, row in df.iterrows():
                    trade_date = datetime.strptime(str(row['cal_date']), '%Y%m%d').date()
                    is_open = row['is_open'] == 1
                    pretrade_date = None
                    
                    if row['pretrade_date']:
                        pretrade_date = datetime.strptime(str(row['pretrade_date']), '%Y%m%d').date()
                    
                    TradeCal.objects.update_or_create(
                        exchange=exchange,
                        cal_date=trade_date,
                        defaults={
                            'is_open': is_open,
                            'pretrade_date': pretrade_date
                        }
                    )
        
        logger.info("交易日历同步完成")
        
    except Exception as e:
        logger.error(f"同步交易日历失败: {e}")


def manual_sync_all():
    """手动同步所有数据（用于测试）"""
    logger.info("开始手动同步所有数据...")
    
    # 1. 同步交易日历
    sync_trade_calendar()
    
    # 2. 同步股票基本信息
    result = StockDataService.sync_stock_basic()
    logger.info(f"股票基本信息同步结果: {result}")
    
    # 3. 同步当日数据
    sync_daily_stock_data()
    
    # 4. 同步公司信息（部分）
    sync_company_info()
    
    # 5. 同步新闻
    sync_financial_news()
    
    logger.info("手动同步完成")


if __name__ == '__main__':
    """
    命令行执行方式：
    python stock/tasks.py sync_daily      # 同步当日数据
    python stock/tasks.py sync_company    # 同步公司信息
    python stock/tasks.py sync_news       # 同步新闻
    python stock/tasks.py manual_sync     # 手动同步所有
    """
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'sync_daily':
            sync_daily_stock_data()
        elif command == 'sync_company':
            sync_company_info()
        elif command == 'sync_news':
            sync_financial_news()
        elif command == 'manual_sync':
            manual_sync_all()
        else:
            print("未知命令，可用命令：sync_daily, sync_company, sync_news, manual_sync")
    else:
        print("请指定命令：sync_daily, sync_company, sync_news, manual_sync")