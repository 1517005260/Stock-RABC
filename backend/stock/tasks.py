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
import json

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
log_file = os.path.join(BASE_DIR, 'logs', 'stock_tasks.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
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
        
        # 方法2：从东方财富爬取新闻（如果新浪失败）
        if not news_list:
            news_list = crawl_eastmoney_news()
        
        # 方法3：使用Bing搜索作为最后备用方案
        if not news_list:
            news_list = crawl_bing_finance_news()
        
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
    """从新浪财经爬取真实新闻"""
    try:
        url = "https://feed.mix.sina.com.cn/api/roll/get"
        params = {
            'pageid': '153',  # 财经新闻频道
            'lid': '1686',    # 股市新闻
            'num': '10',      # 获取10条
            'versionNumber': '1.2.4',
            'page': '1'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://finance.sina.com.cn/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('result', {}).get('status', {}).get('code') == 0:
                    news_list = []
                    articles = data.get('result', {}).get('data', [])
                    
                    for article in articles[:10]:  # 取前10条
                        try:
                            title = article.get('title', '').strip()
                            url_link = article.get('url', '')
                            create_date = article.get('create_date', '')
                            
                            # 解析时间
                            publish_time = datetime.now()
                            if create_date:
                                try:
                                    publish_time = datetime.strptime(create_date, '%Y-%m-%d %H:%M:%S')
                                except:
                                    pass
                            
                            if title and len(title) > 5:  # 过滤太短的标题
                                news_list.append({
                                    'title': title,
                                    'content': title,  # 简化版本，可以进一步获取正文
                                    'source': '新浪财经',
                                    'publish_time': publish_time,
                                    'url': url_link,
                                    'related_stocks': []
                                })
                        except Exception as e:
                            logger.error(f"解析新闻项失败: {e}")
                            continue
                    
                    return news_list
                else:
                    logger.error(f"新浪财经API返回错误: {data}")
            except json.JSONDecodeError:
                logger.error("新浪财经返回数据不是有效JSON")
        else:
            logger.error(f"访问新浪财经失败: HTTP {response.status_code}")
            
    except Exception as e:
        logger.error(f"爬取新浪财经新闻失败: {e}")
    
    return []


def crawl_eastmoney_news():
    """从东方财富easyfinance爬取真实新闻数据"""
    try:
        # 使用东方财富的easyfinance新闻接口
        url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
        params = {
            'sr': -1,
            'page': 1,
            'pagesize': 10,
            'ann_type': 'A',
            'client': 'web'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://data.eastmoney.com/',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                news_list = []
                
                # 尝试不同的数据结构
                announcements = data.get('data', []) or data.get('result', []) or []
                
                if announcements:
                    for ann in announcements[:10]:
                        try:
                            title = ann.get('title', '').strip()
                            code = ann.get('code', '') or ann.get('secucode', '')
                            name = ann.get('name', '') or ann.get('secuname', '')
                            notice_date = ann.get('notice_date', '') or ann.get('ann_date', '')
                            
                            # 构建完整标题
                            if name and code:
                                full_title = f"{name}({code}): {title}"
                            else:
                                full_title = title
                            
                            # 解析时间
                            publish_time = datetime.now()
                            if notice_date:
                                try:
                                    if ' ' in notice_date:
                                        publish_time = datetime.strptime(notice_date.split(' ')[0], '%Y-%m-%d')
                                    else:
                                        publish_time = datetime.strptime(notice_date, '%Y-%m-%d')
                                except:
                                    pass
                            
                            if full_title and len(full_title) > 5:
                                news_list.append({
                                    'title': full_title,
                                    'content': full_title,
                                    'source': '东方财富',
                                    'publish_time': publish_time,
                                    'related_stocks': [code] if code else []
                                })
                        except Exception as e:
                            logger.error(f"解析东方财富公告失败: {e}")
                            continue
                else:
                    logger.warning("东方财富API返回数据为空")
                
                return news_list
                
            except json.JSONDecodeError:
                logger.error("东方财富返回数据不是有效JSON")
        else:
            logger.error(f"访问东方财富失败: HTTP {response.status_code}")
            logger.error(f"响应内容: {response.text[:200]}")
        
        return []
        
    except Exception as e:
        logger.error(f"爬取东方财富新闻失败: {e}")
        return []


def crawl_bing_finance_news():
    """使用Bing搜索获取财经新闻作为备用方案"""
    try:
        # 使用Bing搜索最新财经新闻
        search_query = "A股市场 股票 财经新闻"
        url = "https://www.bing.com/search"
        params = {
            'q': search_query,
            'count': 10,
            'offset': 0,
            'mkt': 'zh-CN'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            news_list = []
            
            # 解析Bing搜索结果
            search_results = soup.find_all('div', class_='b_algo')
            
            for result in search_results[:10]:
                try:
                    title_element = result.find('h2')
                    if title_element:
                        title_link = title_element.find('a')
                        if title_link:
                            title = title_link.get_text().strip()
                            url_link = title_link.get('href', '')
                            
                            # 过滤非财经相关的结果
                            if any(keyword in title for keyword in ['股票', '股市', 'A股', '财经', '证券', '投资', '市场']):
                                if title and len(title) > 5:
                                    news_list.append({
                                        'title': title,
                                        'content': title,
                                        'source': 'Bing搜索',
                                        'publish_time': datetime.now(),
                                        'url': url_link,
                                        'related_stocks': []
                                    })
                except Exception as e:
                    logger.error(f"解析Bing搜索结果失败: {e}")
                    continue
            
            return news_list
            
        else:
            logger.error(f"Bing搜索失败: HTTP {response.status_code}")
            
    except Exception as e:
        logger.error(f"Bing搜索新闻失败: {e}")
    
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