# -*- coding: utf-8 -*-

import os
import tushare as ts
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from django.db import transaction
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from dotenv import load_dotenv
import requests
import re

from stock.models import StockBasic, StockDaily, StockCompany, TradeCal, IndexDaily
from trading.models import UserStockAccount, UserPosition, TradeRecord, UserWatchList, MarketNews
from user.models import SysUser
from role.models import SysUserRole, SysRole

# 加载环境变量
load_dotenv()

# 初始化Tushare
token = os.getenv('TUSHARE_TOKEN')  # 修正环境变量名
if token:
    ts.set_token(token)
    pro = ts.pro_api()
else:
    pro = None  # 避免pro未定义的错误


class StockDataService:
    """股票数据服务 - 负责从Tushare获取和同步数据"""
    
    @staticmethod
    def sync_stock_basic():
        """同步股票基本信息"""
        try:
            if not pro:
                return {
                    'success': False,
                    'message': 'TuShare API未配置或token无效',
                    'count': 0
                }
                
            # 获取所有上市股票基本信息
            df = pro.stock_basic(exchange='', list_status='L', 
                               fields='ts_code,symbol,name,area,industry,fullname,enname,cnspell,market,exchange,curr_type,list_status,list_date,delist_date,is_hs,act_name,act_ent_type')
            
            success_count = 0
            for _, row in df.iterrows():
                stock_data = {
                    'ts_code': row['ts_code'],
                    'symbol': row['symbol'],
                    'name': row['name'],
                    'area': row['area'],
                    'industry': row['industry'],
                    'fullname': row['fullname'],
                    'enname': row['enname'],
                    'cnspell': row['cnspell'],
                    'market': row['market'],
                    'exchange': row['exchange'],
                    'curr_type': row['curr_type'],
                    'list_status': row['list_status'],
                    'list_date': row['list_date'] if row['list_date'] and str(row['list_date']) != 'nan' else None,
                    'delist_date': row['delist_date'] if row['delist_date'] and str(row['delist_date']) != 'nan' else None,
                    'is_hs': row['is_hs'],
                    'act_name': row['act_name'],
                    'act_ent_type': row['act_ent_type'],
                }
                
                # 处理日期格式
                if stock_data['list_date']:
                    try:
                        stock_data['list_date'] = datetime.strptime(str(stock_data['list_date']), '%Y%m%d').date()
                    except:
                        stock_data['list_date'] = None
                
                if stock_data['delist_date']:
                    try:
                        stock_data['delist_date'] = datetime.strptime(str(stock_data['delist_date']), '%Y%m%d').date()
                    except:
                        stock_data['delist_date'] = None
                
                # 使用update_or_create避免重复
                StockBasic.objects.update_or_create(
                    ts_code=stock_data['ts_code'],
                    defaults=stock_data
                )
                success_count += 1
            
            return {'success': True, 'count': success_count, 'message': f'成功同步{success_count}只股票基本信息'}
        
        except Exception as e:
            return {'success': False, 'message': f'同步股票基本信息失败: {str(e)}'}
    
    @staticmethod
    def sync_stock_daily(ts_code, days=30):
        """同步单只股票日线数据"""
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            success_count = 0
            for _, row in df.iterrows():
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
            
            return {'success': True, 'count': success_count, 'message': f'成功同步{ts_code} {success_count}条日线数据'}
        
        except Exception as e:
            return {'success': False, 'message': f'同步{ts_code}日线数据失败: {str(e)}'}
    
    @staticmethod
    def sync_company_info(ts_codes):
        """同步公司基本信息"""
        try:
            if isinstance(ts_codes, str):
                ts_codes = [ts_codes]
            
            # Tushare接口一次最多查询多只股票
            ts_codes_str = ','.join(ts_codes[:50])  # 限制数量
            df = pro.stock_company(ts_code=ts_codes_str)
            
            success_count = 0
            for _, row in df.iterrows():
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
            
            return {'success': True, 'count': success_count, 'message': f'成功同步{len(ts_codes)}只股票的公司信息'}
        
        except Exception as e:
            return {'success': False, 'message': f'同步公司信息失败: {str(e)}'}
    
    @staticmethod
    def get_top_stocks(limit=10):
        """获取热门牛股 - 直接从TuShare API获取今日涨幅榜"""
        try:
            if not pro:
                raise Exception('TuShare API未配置，无法获取涨幅榜')

            # 获取今日交易数据
            today = datetime.now().strftime('%Y%m%d')

            try:
                # 获取今日全市场股票数据
                df = pro.daily(
                    trade_date=today,
                    fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
                )

                # 如果今日没有数据，尝试获取最近交易日数据
                if df.empty:
                    for i in range(1, 6):
                        date_str = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
                        df = pro.daily(
                            trade_date=date_str,
                            fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
                        )
                        if not df.empty:
                            break

                if df.empty:
                    raise Exception("无法获取股票交易数据")

                # 筛选出涨幅榜：排除ST股票、停牌股票，筛选涨幅最大的股票
                filtered_df = df[
                    (df['pct_chg'].notna()) &
                    (df['pct_chg'] > 0) &  # 只要上涨的股票
                    (df['vol'] > 0) &  # 有成交量
                    (df['close'] > 0) &  # 正常价格
                    (~df['ts_code'].str.contains('ST', na=False)) &  # 排除ST股票
                    (~df['ts_code'].str.contains('退', na=False))  # 排除退市股票
                ].sort_values('pct_chg', ascending=False).head(limit * 2)  # 获取更多数据以便筛选

                # 如果没有上涨股票，获取涨跌幅最大的股票
                if filtered_df.empty:
                    filtered_df = df[
                        (df['pct_chg'].notna()) &
                        (df['vol'] > 0) &
                        (df['close'] > 0) &
                        (~df['ts_code'].str.contains('ST', na=False))
                    ].sort_values('pct_chg', ascending=False).head(limit * 2)

                if filtered_df.empty:
                    raise Exception("没有找到有效的股票数据")

                # 获取股票基本信息（名称、行业等）
                ts_codes = filtered_df['ts_code'].tolist()

                # 分批获取股票基本信息（TuShare单次查询限制）
                stock_basic_data = {}
                batch_size = 100
                for i in range(0, len(ts_codes), batch_size):
                    batch_codes = ts_codes[i:i+batch_size]
                    try:
                        basic_df = pro.stock_basic(
                            ts_code=','.join(batch_codes),
                            fields='ts_code,name,industry'
                        )
                        for _, row in basic_df.iterrows():
                            stock_basic_data[row['ts_code']] = {
                                'name': row['name'],
                                'industry': row['industry'] if row['industry'] else '未分类'
                            }
                    except Exception as e:
                        print(f"获取基本信息批次失败: {e}")

                # 构建热门股票列表
                result = []
                for _, row in filtered_df.iterrows():
                    ts_code = row['ts_code']
                    basic_info = stock_basic_data.get(ts_code, {'name': ts_code, 'industry': '未分类'})

                    result.append({
                        'ts_code': ts_code,
                        'name': basic_info['name'],
                        'close': float(row['close']) if row['close'] else 0,
                        'open': float(row['open']) if row['open'] else 0,
                        'high': float(row['high']) if row['high'] else 0,
                        'low': float(row['low']) if row['low'] else 0,
                        'change': float(row['change']) if row['change'] else 0,
                        'pct_chg': float(row['pct_chg']) if row['pct_chg'] else 0,
                        'vol': int(row['vol']) if row['vol'] else 0,
                        'amount': float(row['amount']) if row['amount'] else 0,
                        'trade_date': datetime.strptime(str(row['trade_date']), '%Y%m%d').strftime('%Y-%m-%d'),
                        'industry': basic_info['industry'],
                        'data_source': 'tushare_api_realtime'
                    })

                    # 限制返回数量
                    if len(result) >= limit:
                        break

                if not result:
                    raise Exception("处理股票数据后无有效结果")

                print(f"成功从TuShare API获取 {len(result)} 只涨幅榜股票")
                return result

            except Exception as api_error:
                print(f"TuShare API调用失败: {api_error}")
                # 回退到本地数据库
                return StockDataService.get_top_stocks_from_db(limit)

        except Exception as e:
            print(f"获取热门股票失败: {str(e)}")
            # 最终回退：返回固定的热门股票
            return StockDataService.get_fallback_stocks(limit)

    @staticmethod
    def get_top_stocks_from_db(limit=10):
        """从本地数据库获取热门股票（回退方案）"""
        try:
            # 获取最新交易日的股票数据，按涨跌幅排序
            latest_date = StockDaily.objects.values('trade_date').order_by('-trade_date').first()
            if not latest_date:
                raise Exception('数据库中没有股票交易数据')
            
            # 获取涨跌幅大于0且有效的股票，按涨跌幅排序
            top_stocks = StockDaily.objects.filter(
                trade_date=latest_date['trade_date'],
                pct_chg__isnull=False,
                pct_chg__gt=0,  # 只获取上涨的股票
                close__isnull=False,
                vol__gt=0  # 确保有成交量
            ).order_by('-pct_chg')[:limit]
            
            result = []
            for stock_daily in top_stocks:
                try:
                    stock_basic = StockBasic.objects.get(ts_code=stock_daily.ts_code)
                    result.append({
                        'ts_code': stock_daily.ts_code,
                        'name': stock_basic.name,
                        'close': float(stock_daily.close) if stock_daily.close else 0,
                        'change': float(stock_daily.change) if stock_daily.change else 0,
                        'pct_chg': float(stock_daily.pct_chg) if stock_daily.pct_chg else 0,
                        'vol': stock_daily.vol if stock_daily.vol else 0,
                        'amount': float(stock_daily.amount) if stock_daily.amount else 0,
                        'trade_date': stock_daily.trade_date.strftime('%Y-%m-%d'),
                        'industry': stock_basic.industry if stock_basic.industry else '未分类'
                    })
                except StockBasic.DoesNotExist:
                    continue
            
            # 如果没有上涨的股票，则返回涨跌幅最大的股票（包括下跌）
            if not result:
                top_stocks = StockDaily.objects.filter(
                    trade_date=latest_date['trade_date'],
                    pct_chg__isnull=False,
                    close__isnull=False,
                    vol__gt=0
                ).order_by('-pct_chg')[:limit]
                
                for stock_daily in top_stocks:
                    try:
                        stock_basic = StockBasic.objects.get(ts_code=stock_daily.ts_code)
                        result.append({
                            'ts_code': stock_daily.ts_code,
                            'name': stock_basic.name,
                            'close': float(stock_daily.close) if stock_daily.close else 0,
                            'change': float(stock_daily.change) if stock_daily.change else 0,
                            'pct_chg': float(stock_daily.pct_chg) if stock_daily.pct_chg else 0,
                            'vol': stock_daily.vol if stock_daily.vol else 0,
                            'amount': float(stock_daily.amount) if stock_daily.amount else 0,
                            'trade_date': stock_daily.trade_date.strftime('%Y-%m-%d'),
                            'industry': stock_basic.industry if stock_basic.industry else '未分类'
                        })
                    except StockBasic.DoesNotExist:
                        continue
            
            if not result:
                raise Exception(f'在{latest_date["trade_date"]}没有找到有效的股票交易数据')
            
            return result

        except Exception as e:
            print(f"从本地数据库获取热门股票失败: {str(e)}")
            return []

    @staticmethod
    def get_fallback_stocks(limit=10):
        """固定的热门股票列表（最终回退方案）"""
        fallback_stocks = [
            '000001.SZ', '000002.SZ', '000858.SZ', '600000.SH', '600036.SH',
            '600519.SH', '002594.SZ', '300750.SZ', '002415.SZ', '000776.SZ',
            '002230.SZ', '000858.SZ', '600276.SH', '000725.SZ', '002142.SZ'
        ]

        result = []
        for ts_code in fallback_stocks[:limit]:
            try:
                stock = StockBasic.objects.get(ts_code=ts_code)
                latest_daily = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date').first()

                if latest_daily:
                    result.append({
                        'ts_code': ts_code,
                        'name': stock.name,
                        'close': float(latest_daily.close) if latest_daily.close else 0,
                        'change': float(latest_daily.change) if latest_daily.change else 0,
                        'pct_chg': float(latest_daily.pct_chg) if latest_daily.pct_chg else 0,
                        'vol': latest_daily.vol if latest_daily.vol else 0,
                        'amount': float(latest_daily.amount) if latest_daily.amount else 0,
                        'trade_date': latest_daily.trade_date.strftime('%Y-%m-%d'),
                        'industry': stock.industry if stock.industry else '未分类',
                        'data_source': 'local_fallback'
                    })
            except:
                continue

        return result
    
    @staticmethod
    def get_hot_stocks(limit=10):
        """获取热门股票 - get_top_stocks的别名"""
        return StockDataService.get_top_stocks(limit)
    
    @staticmethod
    def get_index_daily_from_tushare(ts_code, period='daily', limit=100):
        """从Tushare API直接获取指数K线数据"""
        try:
            if not pro:
                print("Tushare pro API未初始化")
                return []
            
            # 放宽限流策略，改为每分钟最多5次调用
            if not RateLimiter.can_call("index_daily", max_calls=5, time_window=60):
                print(f"指数数据API限流中，等待1分钟后重试")
                return []
            
            # 记录API调用
            RateLimiter.record_call("index_daily")
            
            # 计算日期范围 - 确保获取足够的数据
            end_date = datetime.now().strftime('%Y%m%d')
            if period == 'daily':
                # 增加日期范围，确保获取到足够的交易日数据
                start_date = (datetime.now() - timedelta(days=limit * 3)).strftime('%Y%m%d')
            elif period == 'weekly':
                start_date = (datetime.now() - timedelta(days=limit * 14)).strftime('%Y%m%d')
            elif period == 'monthly':
                start_date = (datetime.now() - timedelta(days=limit * 60)).strftime('%Y%m%d')
            else:
                start_date = (datetime.now() - timedelta(days=300)).strftime('%Y%m%d')
            
            print(f"获取指数数据: {ts_code}, 日期范围: {start_date} - {end_date}")
            
            # 获取指数日线数据
            import pandas as pd
            df = pro.index_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
            )
            
            if df.empty:
                print(f"指数 {ts_code} 在日期范围 {start_date}-{end_date} 内无数据")
                return []
            
            print(f"成功获取指数数据 {len(df)} 条")
            
            # 转换为所需格式
            kline_data = []
            for _, row in df.iterrows():
                try:
                    kline_data.append({
                        'date': pd.to_datetime(row['trade_date']).strftime('%Y-%m-%d'),
                        'open': float(row['open']) if pd.notna(row['open']) else 0,
                        'high': float(row['high']) if pd.notna(row['high']) else 0,
                        'low': float(row['low']) if pd.notna(row['low']) else 0,
                        'close': float(row['close']) if pd.notna(row['close']) else 0,
                        'volume': int(row['vol']) if pd.notna(row['vol']) else 0,
                        'amount': float(row['amount']) if pd.notna(row['amount']) else 0,
                        'change': float(row['change']) if pd.notna(row['change']) else 0,
                        'pct_chg': float(row['pct_chg']) if pd.notna(row['pct_chg']) else 0,
                        'pre_close': float(row['pre_close']) if pd.notna(row['pre_close']) else 0
                    })
                except (ValueError, TypeError) as e:
                    print(f"数据转换错误: {e}")
                    continue
            
            # 按日期正序排列
            kline_data.sort(key=lambda x: x['date'])
            
            # 限制返回数量
            result = kline_data[-limit:] if limit and len(kline_data) > limit else kline_data
            print(f"返回指数数据 {len(result)} 条")
            return result
            
        except Exception as e:
            print(f"获取指数数据失败: {e}")
            return []


class UserPermissionService:
    """用户权限服务"""
    
    @staticmethod
    def get_user_roles(user):
        """获取用户角色"""
        user_roles = SysUserRole.objects.filter(user=user).select_related('role')
        return [user_role.role for user_role in user_roles]
    
    @staticmethod
    def has_permission(user, required_roles):
        """检查用户是否有指定权限"""
        if isinstance(required_roles, str):
            required_roles = [required_roles]
        
        user_roles = UserPermissionService.get_user_roles(user)
        user_role_codes = [role.code for role in user_roles]
        
        return any(role_code in required_roles for role_code in user_role_codes)
    
    @staticmethod
    def is_admin(user):
        """检查是否为管理员"""
        return user.is_admin or UserPermissionService.has_permission(user, ['admin', 'superadmin'])
    
    @staticmethod
    def is_superadmin(user):
        """检查是否为超级管理员"""
        return UserPermissionService.has_permission(user, ['superadmin'])
    
    @staticmethod
    def get_admin_users():
        """获取所有管理员用户"""
        admin_roles = SysRole.objects.filter(code__in=['admin', 'superadmin'])
        admin_user_roles = SysUserRole.objects.filter(role__in=admin_roles)
        admin_users_from_roles = [ur.user for ur in admin_user_roles]
        
        # 同时包括直接标记为管理员的用户
        admin_users_direct = list(SysUser.objects.filter(is_admin=True))
        
        # 合并去重
        all_admin_users = list(set(admin_users_from_roles + admin_users_direct))
        return all_admin_users


class NewsService:
    """新闻服务"""

    @staticmethod
    def get_latest_news(limit=10):
        """获取最新市场新闻"""
        return MarketNews.objects.filter(is_published=True).order_by('-publish_time')[:limit]

    @staticmethod
    def create_news(title, content, source=None, category=None, related_stocks=None):
        """创建新闻"""
        return MarketNews.objects.create(
            title=title,
            content=content,
            source=source or '系统',
            publish_time=datetime.now(),
            category=category,
            related_stocks=related_stocks,
            is_published=True
        )

    @staticmethod
    def create_news(title: str, content: str, source: str = None,
                   category: str = None, source_url: str = None):
        """创建新闻（系统自动创建）"""
        try:
            from django.utils import timezone
            from trading.models import MarketNews

            news = MarketNews.objects.create(
                title=title,
                content=content,
                source=source or '系统',
                source_url=source_url,
                category=category or '综合新闻',
                publish_time=timezone.now(),
                is_published=True
            )
            return news

        except Exception as e:
            print(f"创建新闻失败: {e}")
            return None

    @staticmethod
    def fetch_real_news_from_api(limit=20):
        """Fetch real financial news from verified working sources"""
        import requests
        from bs4 import BeautifulSoup
        from datetime import datetime

        news_list = []

        # Source 1: Yicai (第一财经) - tested and working
        try:
            yicai_news = NewsService._fetch_from_yicai(limit)
            if yicai_news:
                news_list.extend(yicai_news)
                print(f"Fetched {len(yicai_news)} news from Yicai")
        except Exception as e:
            print(f"Yicai source failed: {e}")

        # Source 2: Sina Finance (with encoding fix)
        if len(news_list) < limit:
            try:
                sina_news = NewsService._fetch_from_sina_fixed(limit - len(news_list))
                if sina_news:
                    news_list.extend(sina_news)
                    print(f"Fetched {len(sina_news)} news from Sina Finance")
            except Exception as e:
                print(f"Sina Finance source failed: {e}")

        # Source 3: NetEase Money (backup)
        if len(news_list) < limit:
            try:
                netease_news = NewsService._fetch_from_netease(limit - len(news_list))
                if netease_news:
                    news_list.extend(netease_news)
                    print(f"Fetched {len(netease_news)} news from NetEase")
            except Exception as e:
                print(f"NetEase source failed: {e}")

        if not news_list:
            print("All news sources failed - no news available")
            return []

        print(f"Successfully fetched {len(news_list)} real news items from working sources")
        return news_list[:limit]

    @staticmethod
    def _fetch_from_yicai(limit=10):
        """Fetch from Yicai (第一财经) - verified working source"""
        import requests
        from bs4 import BeautifulSoup

        try:
            url = "https://www.yicai.com/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []

            # Look for article titles in headlines
            titles = soup.find_all(['h1', 'h2', 'h3'])

            for title in titles:
                text = title.get_text(strip=True)
                if text and len(text) > 10 and len(text) < 80:
                    # Find parent or child link
                    link = title.find('a') or title.find_parent('a')
                    url = link['href'] if link and link.get('href') else ''

                    if url and not url.startswith('http'):
                        url = 'https://www.yicai.com' + url

                    news_item = {
                        'title': text,
                        'content': f"来源：第一财经\n\n{text}\n\n详细内容请访问原文链接。",
                        'source': '第一财经',
                        'url': url,
                        'category': '财经资讯'
                    }
                    news_items.append(news_item)

                    if len(news_items) >= limit:
                        break

            return news_items

        except Exception as e:
            print(f"Yicai fetch error: {e}")
            return []

    @staticmethod
    def _fetch_from_sina_fixed(limit=10):
        """Fetch from Sina Finance with proper encoding handling"""
        import requests
        from bs4 import BeautifulSoup

        try:
            url = "https://finance.sina.com.cn/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []

            # Look for finance news links
            all_links = soup.find_all('a', href=True)

            for link in all_links:
                href = link.get('href', '')
                title = link.get_text(strip=True)

                # Filter for finance-related links with meaningful titles
                if ('finance.sina.com.cn' in href or 'money.sina.com.cn' in href) and title and len(title) > 8 and len(title) < 100:
                    full_url = href if href.startswith('http') else 'https:' + href

                    news_item = {
                        'title': title,
                        'content': f"来源：新浪财经\n\n{title}\n\n详细内容请访问原文链接。",
                        'source': '新浪财经',
                        'url': full_url,
                        'category': '财经资讯'
                    }
                    news_items.append(news_item)

                    if len(news_items) >= limit:
                        break

            return news_items

        except Exception as e:
            print(f"Sina Finance fetch error: {e}")
            return []

    @staticmethod
    def _fetch_from_netease(limit=10):
        """Fetch from NetEase Money as backup source"""
        import requests
        from bs4 import BeautifulSoup

        try:
            url = "https://money.163.com/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []

            # Look for money.163.com links
            links = soup.find_all('a', href=True)
            netease_links = [link for link in links if 'money.163.com' in str(link.get('href', ''))]

            for link in netease_links:
                title = link.get_text(strip=True)
                if title and len(title) > 10 and len(title) < 80:
                    url = link['href']
                    if not url.startswith('http'):
                        url = 'https://money.163.com' + url

                    news_item = {
                        'title': title,
                        'content': f"来源：网易财经\n\n{title}\n\n详细内容请访问原文链接。",
                        'source': '网易财经',
                        'url': url,
                        'category': '财经资讯'
                    }
                    news_items.append(news_item)

                    if len(news_items) >= limit:
                        break

            return news_items

        except Exception as e:
            print(f"NetEase fetch error: {e}")
            return []

    @staticmethod
    def update_news_data(limit=20):
        """更新新闻数据到数据库"""
        try:
            # 获取新闻数据
            news_list = NewsService.fetch_real_news_from_api(limit)

            if not news_list:
                print("未获取到有效新闻")
                return 0

            saved_count = 0
            for news_item in news_list:
                try:
                    # 检查是否已存在相同标题的新闻
                    if not MarketNews.objects.filter(title=news_item['title']).exists():
                        NewsService.create_news(
                            title=news_item['title'],
                            content=news_item['content'],
                            source=news_item.get('source', '系统'),
                            category=news_item.get('category', '综合新闻'),
                            source_url=news_item.get('url', '')  # 添加原文链接
                        )
                        saved_count += 1
                        print(f"保存新闻: {news_item['title'][:30]}...")

                except Exception as e:
                    print(f"保存新闻失败: {e}")
                    continue

            print(f"成功更新 {saved_count} 条新闻到数据库")
            return saved_count

        except Exception as e:
            print(f"更新新闻数据失败: {e}")
            return 0

    @staticmethod
    def clean_old_news(days=7):
        """清理N天前的旧新闻"""
        try:
            from django.utils import timezone
            cutoff_date = timezone.now() - timedelta(days=days)
            old_news_count = MarketNews.objects.filter(publish_time__lt=cutoff_date).count()

            if old_news_count > 0:
                MarketNews.objects.filter(publish_time__lt=cutoff_date).delete()
                print(f"清理了 {old_news_count} 条{days}天前的旧新闻")
                return old_news_count

            return 0

        except Exception as e:
            print(f"清理旧新闻失败: {e}")
            return 0


class DataCache:
    """数据缓存管理"""
    _cache = {}
    _cache_time = {}
    
    @classmethod
    def get(cls, key, expiry_seconds=300):
        """获取缓存数据，默认5分钟过期"""
        if key in cls._cache:
            if datetime.now().timestamp() - cls._cache_time[key] < expiry_seconds:
                return cls._cache[key]
            else:
                # 清理过期缓存
                del cls._cache[key]
                del cls._cache_time[key]
        return None
    
    @classmethod
    def set(cls, key, value):
        """设置缓存数据"""
        cls._cache[key] = value
        cls._cache_time[key] = datetime.now().timestamp()
    
    @classmethod
    def clear_expired(cls, expiry_seconds=300):
        """清理过期缓存"""
        current_time = datetime.now().timestamp()
        expired_keys = [
            key for key, cache_time in cls._cache_time.items()
            if current_time - cache_time >= expiry_seconds
        ]
        for key in expired_keys:
            if key in cls._cache:
                del cls._cache[key]
            if key in cls._cache_time:
                del cls._cache_time[key]


class RateLimiter:
    """接口限流管理"""
    _call_records = {}
    
    @classmethod
    def can_call(cls, api_name, max_calls=2, time_window=60):
        """检查是否可以调用API"""
        current_time = datetime.now().timestamp()
        
        if api_name not in cls._call_records:
            cls._call_records[api_name] = []
        
        # 清理过期记录
        cls._call_records[api_name] = [
            call_time for call_time in cls._call_records[api_name]
            if current_time - call_time < time_window
        ]
        
        # 检查是否超过限制
        if len(cls._call_records[api_name]) >= max_calls:
            return False
        
        return True
    
    @classmethod
    def record_call(cls, api_name):
        """记录API调用"""
        current_time = datetime.now().timestamp()
        if api_name not in cls._call_records:
            cls._call_records[api_name] = []
        cls._call_records[api_name].append(current_time)
    
    @classmethod
    def get_wait_time(cls, api_name, max_calls=2, time_window=60):
        """获取需要等待的时间"""
        if cls.can_call(api_name, max_calls, time_window):
            return 0
        
        if api_name not in cls._call_records or not cls._call_records[api_name]:
            return 0
        
        oldest_call = min(cls._call_records[api_name])
        current_time = datetime.now().timestamp()
        return max(0, time_window - (current_time - oldest_call))


class IntradayDataService:
    """分时数据服务 - 参考sample项目方式，支持多数据源策略"""

    @staticmethod
    def get_stock_intraday_from_tushare(ts_code):
        """从Tushare获取分时数据 - 参考sample项目使用get_today_ticks"""
        try:
            import tushare as ts

            # 检查是否为工作日
            from datetime import date, datetime
            from chinese_calendar import is_workday, is_holiday

            today = date.today()
            if not is_workday(today) or is_holiday(today):
                return {'success': False, 'message': '非交易日', 'data': None}

            # 转换股票代码格式：000007.SZ -> 000007
            stock_code = ts_code.split('.')[0]

            # 使用sample项目的方式获取今日分时数据
            df = ts.get_today_ticks(stock_code)

            if df is not None and not df.empty:
                # 转换为标准格式
                times = []
                prices = []

                for _, row in df.iterrows():
                    time_str = str(row['time'])  # 091505格式
                    price = float(row['price'])

                    # 转换时间格式：091505 -> 09:15
                    if len(time_str) == 6:
                        formatted_time = f"{time_str[:2]}:{time_str[2:4]}"
                        times.append(formatted_time)
                        prices.append(price)

                return {
                    'success': True,
                    'data': {'time': times, 'price': prices},
                    'source': 'tushare',
                    'count': len(times)
                }
            else:
                return {'success': False, 'message': 'Tushare无分时数据', 'data': None}

        except Exception as e:
            return {'success': False, 'message': f'Tushare分时数据获取失败: {str(e)}', 'data': None}

    @staticmethod
    def get_stock_intraday_from_eastmoney(ts_code):
        """从东方财富API获取分时数据"""
        try:
            import requests

            # 转换股票代码格式
            if ts_code.endswith('.SZ'):
                secid = f"0.{ts_code.split('.')[0]}"
            elif ts_code.endswith('.SH'):
                secid = f"1.{ts_code.split('.')[0]}"
            else:
                return {'success': False, 'message': '不支持的股票代码格式', 'data': None}

            # 东方财富分时数据接口
            url = "http://push2his.eastmoney.com/api/qt/stock/trends2/get"
            params = {
                'secid': secid,
                'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',
                'iscr': '0'
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data'] and 'trends' in data['data']:
                    trends = data['data']['trends']
                    if trends:
                        times = []
                        prices = []

                        for trend in trends:
                            parts = trend.split(',')
                            if len(parts) >= 2:
                                time_str = parts[0]  # 2025-09-12 09:30 格式
                                price = float(parts[1])

                                # 提取时间部分：2025-09-12 09:30 -> 09:30
                                if ' ' in time_str:
                                    time_only = time_str.split(' ')[1]
                                    times.append(time_only)
                                    prices.append(price)

                        return {
                            'success': True,
                            'data': {'time': times, 'price': prices},
                            'source': 'eastmoney',
                            'count': len(times)
                        }

            return {'success': False, 'message': '东方财富无分时数据', 'data': None}

        except Exception as e:
            return {'success': False, 'message': f'东方财富分时数据获取失败: {str(e)}', 'data': None}

    @staticmethod
    def get_stock_intraday_from_tencent(ts_code):
        """从腾讯财经API获取分时数据"""
        try:
            import requests

            # 转换股票代码格式
            if ts_code.endswith('.SZ'):
                stock_code = f"sz{ts_code.split('.')[0]}"
            elif ts_code.endswith('.SH'):
                stock_code = f"sh{ts_code.split('.')[0]}"
            else:
                return {'success': False, 'message': '不支持的股票代码格式', 'data': None}

            # 腾讯分时数据接口
            market = stock_code[:2]  # sz or sh
            code = stock_code[2:]    # 6位数字

            url = f"http://data.gtimg.cn/flashdata/hushen/minute/{market}{code}.js"
            response = requests.get(url, timeout=10)

            if response.status_code == 200 and response.text:
                lines = response.text.strip().split('\n')
                valid_lines = [line for line in lines if ' ' in line and ':' in line]

                if valid_lines:
                    times = []
                    prices = []

                    for line in valid_lines:
                        parts = line.split(' ')
                        if len(parts) >= 2:
                            time_str = parts[0]  # 09:30 格式
                            price = float(parts[1])
                            times.append(time_str)
                            prices.append(price)

                    return {
                        'success': True,
                        'data': {'time': times, 'price': prices},
                        'source': 'tencent',
                        'count': len(times)
                    }

            return {'success': False, 'message': '腾讯无分时数据', 'data': None}

        except Exception as e:
            return {'success': False, 'message': f'腾讯分时数据获取失败: {str(e)}', 'data': None}
    
    
    @staticmethod
    def get_stock_intraday_multi_source(ts_code):
        """多数据源策略获取分时数据"""
        # 优先级: 东方财富 > 腾讯 > Tushare
        data_sources = [
            ('eastmoney', IntradayDataService.get_stock_intraday_from_eastmoney),
            ('tencent', IntradayDataService.get_stock_intraday_from_tencent),
            ('tushare', IntradayDataService.get_stock_intraday_from_tushare)
        ]

        for source_name, source_func in data_sources:
            try:
                # 检查缓存
                cache_key = f"intraday_{ts_code}_{source_name}"
                cached_data = DataCache.get(cache_key, expiry_seconds=30)  # 30秒缓存
                if cached_data:
                    return cached_data

                # 获取数据
                result = source_func(ts_code)

                if result['success']:
                    # 缓存成功结果
                    DataCache.set(cache_key, result)
                    return result

            except Exception as e:
                print(f"数据源 {source_name} 获取失败: {e}")
                continue

        return {
            'success': False,
            'message': '所有数据源都无法获取分时数据，请稍后重试',
            'data': None
        }



class RealTimeDataService:
    """实时股票数据服务 - 支持5秒刷新功能，智能缓存和限流"""
    
    @staticmethod
    def is_trading_time():
        """判断是否为交易时间"""
        from datetime import datetime, time as dt_time
        
        now = datetime.now()
        current_time = now.time()
        weekday = now.weekday()
        
        # 周末不交易
        if weekday >= 5:  # 5=Saturday, 6=Sunday
            return False
        
        # 交易时间：9:30-11:30, 13:00-15:00
        morning_start = dt_time(9, 30)
        morning_end = dt_time(11, 30)
        afternoon_start = dt_time(13, 0)
        afternoon_end = dt_time(15, 0)
        
        return (morning_start <= current_time <= morning_end) or \
               (afternoon_start <= current_time <= afternoon_end)

    @staticmethod
    def get_complete_market_stats_eastmoney():
        """从东方财富分页获取完整A股市场统计数据"""
        try:
            import time

            url = "http://push2.eastmoney.com/api/qt/clist/get"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'http://quote.eastmoney.com/'
            }

            # 基础参数 - 获取包含资金流向f62字段的完整数据
            base_params = {
                'po': '1',
                'np': '1',
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': '2',
                'invt': '2',
                'fid': 'f12',
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',  # A股
                'fields': 'f2,f3,f12,f14,f62'  # 价格、涨跌幅、代码、名称、净资金流向
            }

            all_stocks = []
            page = 1
            page_size = 100

            print(f"开始获取完整A股市场数据...")

            # 分页获取全部股票数据
            while True:
                params = base_params.copy()
                params['pn'] = str(page)
                params['pz'] = str(page_size)

                response = requests.get(url, params=params, headers=headers, timeout=10)

                if response.status_code != 200:
                    print(f"第{page}页请求失败: {response.status_code}")
                    break

                data = response.json()

                if 'data' not in data or not data['data']:
                    print(f"第{page}页无数据")
                    break

                page_stocks = data['data'].get('diff', [])
                if not page_stocks:
                    print(f"第{page}页股票列表为空")
                    break

                all_stocks.extend(page_stocks)
                print(f"第{page}页: {len(page_stocks)}只股票, 累计: {len(all_stocks)}只")

                # 如果这页数据少于页面大小，说明是最后一页
                if len(page_stocks) < page_size:
                    print(f"第{page}页为最后一页")
                    break

                page += 1
                time.sleep(0.05)  # 短暂延时避免限流

            print(f"数据获取完成: 共{len(all_stocks)}只股票")

            # 统计涨跌分布和真实资金流向
            up_count = 0
            down_count = 0
            flat_count = 0
            limit_up_count = 0
            limit_down_count = 0
            valid_count = 0

            # 资金流向统计
            total_net_flow = 0.0  # 净流向（元）
            stocks_with_flow_data = 0
            positive_flow = 0.0  # 流入
            negative_flow = 0.0  # 流出

            for stock in all_stocks:
                change_pct = stock.get('f3')
                price = stock.get('f2')
                net_flow = stock.get('f62')  # 净资金流向（元）

                # 跳过停牌股票
                if change_pct is None or price is None or price == 0:
                    continue

                valid_count += 1

                try:
                    change_pct = float(change_pct)

                    # 处理真实资金流向数据
                    if net_flow and isinstance(net_flow, (int, float)):
                        flow_value = float(net_flow)
                        total_net_flow += flow_value
                        stocks_with_flow_data += 1

                        if flow_value > 0:
                            positive_flow += flow_value
                        else:
                            negative_flow += abs(flow_value)

                except (ValueError, TypeError):
                    continue

                # 统计涨跌分布
                if change_pct > 9.8:  # 涨停
                    limit_up_count += 1
                    up_count += 1
                elif change_pct > 0:
                    up_count += 1
                elif change_pct < -9.8:  # 跌停
                    limit_down_count += 1
                    down_count += 1
                elif change_pct < 0:
                    down_count += 1
                else:
                    flat_count += 1

            # 转换为亿元
            net_inflow_billion = total_net_flow / 100000000
            positive_flow_billion = positive_flow / 100000000
            negative_flow_billion = negative_flow / 100000000

            print(f"市场统计完成: 上涨{up_count}, 下跌{down_count}, 平盘{flat_count}")
            print(f"资金流向: 净流向{net_inflow_billion:.2f}亿元 (流入{positive_flow_billion:.2f}亿, 流出{negative_flow_billion:.2f}亿)")

            return {
                'up_count': up_count,
                'down_count': down_count,
                'flat_count': flat_count,
                'limit_up_count': limit_up_count,
                'limit_down_count': limit_down_count,
                'total_count': valid_count,
                'sample_size': len(all_stocks),
                'net_inflow_billion': round(net_inflow_billion, 2),
                'total_inflow_billion': round(positive_flow_billion, 2),
                'total_outflow_billion': round(negative_flow_billion, 2),
                'stocks_with_flow_data': stocks_with_flow_data
            }

        except Exception as e:
            print(f"获取东方财富完整市场统计失败: {e}")
            return None

    @staticmethod
    def get_time_period():
        """获取当前时间段"""
        from datetime import datetime, time as dt_time
        
        now = datetime.now()
        current_time = now.time()
        weekday = now.weekday()
        
        if weekday >= 5:
            return 'weekend'
        
        # 盘前：8:00-9:30
        if dt_time(8, 0) <= current_time < dt_time(9, 30):
            return 'pre_market'
        
        # 交易时间：9:30-11:30, 13:00-15:00
        elif (dt_time(9, 30) <= current_time <= dt_time(11, 30)) or \
             (dt_time(13, 0) <= current_time <= dt_time(15, 0)):
            return 'trading_time'
        
        # 中午休息：11:30-13:00
        elif dt_time(11, 30) < current_time < dt_time(13, 0):
            return 'lunch_break'
        
        # 盘后：15:00-22:00
        elif dt_time(15, 0) < current_time <= dt_time(22, 0):
            return 'after_market'
        
        else:
            return 'closed'
    
    @staticmethod
    def get_stock_realtime_price(ts_code):
        """获取股票实时价格 - 使用轻量级腾讯API"""
        try:
            # 使用腾讯API获取实时数据 - 测试证明最快
            stock_code = ts_code.replace('.SH', '').replace('.SZ', '')
            if ts_code.endswith('.SH'):
                tencent_code = f'sh{stock_code}'
            else:
                tencent_code = f'sz{stock_code}'

            url = f"http://qt.gtimg.cn/q={tencent_code}"
            response = requests.get(url, timeout=3)
            response.encoding = 'gbk'

            if response.status_code == 200 and response.text:
                # 解析腾讯数据格式
                data_match = re.search(r'"([^"]+)"', response.text)
                if data_match:
                    data_str = data_match.group(1)
                    data_parts = data_str.split('~')

                    if len(data_parts) >= 50:  # 腾讯API返回50+字段
                        current_price = float(data_parts[3])

                        # 根据成交价格计算买卖价差（模拟真实市场）
                        spread_rate = 0.0002  # 0.02%的价差
                        spread = current_price * spread_rate

                        bid_price = current_price - spread / 2  # 买一价
                        ask_price = current_price + spread / 2  # 卖一价

                        return {
                            'success': True,
                            'data': {
                                'ts_code': ts_code,
                                'current_price': current_price,
                                'bid_price': round(bid_price, 2),
                                'ask_price': round(ask_price, 2),
                                'open_price': float(data_parts[5]),
                                'high_price': float(data_parts[33]),
                                'low_price': float(data_parts[34]),
                                'change': float(data_parts[31]),
                                'pct_chg': float(data_parts[32]),
                                'volume': int(float(data_parts[36])) if data_parts[36] else 0,
                                'amount': float(data_parts[37]) if data_parts[37] else 0,
                                'timestamp': datetime.now().isoformat(),
                                'is_real_time': True,
                                'spread': round(spread, 4),
                                'data_source': 'tencent_api'
                            }
                        }

            # 回退到数据库最新数据
            latest_daily = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date').first()
            if latest_daily:
                current_price = float(latest_daily.close) if latest_daily.close else 0

                # 非交易时间使用固定价差
                spread_rate = 0.0003  # 0.03%的价差
                spread = current_price * spread_rate
                bid_price = current_price - spread / 2
                ask_price = current_price + spread / 2

                return {
                    'success': True,
                    'data': {
                        'ts_code': ts_code,
                        'current_price': current_price,
                        'bid_price': round(bid_price, 2),
                        'ask_price': round(ask_price, 2),
                        'open_price': float(latest_daily.open) if latest_daily.open else 0,
                        'high_price': float(latest_daily.high) if latest_daily.high else 0,
                        'low_price': float(latest_daily.low) if latest_daily.low else 0,
                        'change': float(latest_daily.change) if latest_daily.change else 0,
                        'pct_chg': float(latest_daily.pct_chg) if latest_daily.pct_chg else 0,
                        'volume': latest_daily.vol if latest_daily.vol else 0,
                        'amount': float(latest_daily.amount) if latest_daily.amount else 0,
                        'timestamp': datetime.now().isoformat(),
                        'is_real_time': False,
                        'spread': round(spread, 4),
                        'data_source': 'database'
                    }
                }

            return {
                'success': False,
                'message': '未找到股票数据',
                'data': None
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'获取实时价格失败: {str(e)}',
                'data': None
            }
    
    @staticmethod
    def get_stock_batch_prices(ts_codes, limit=20):
        """批量获取股票实时价格"""
        try:
            # 限制批量查询数量
            ts_codes = ts_codes[:limit]
            results = []
            
            for ts_code in ts_codes:
                price_data = RealTimeDataService.get_stock_realtime_price(ts_code)
                if price_data['success']:
                    results.append(price_data['data'])
            
            return {
                'success': True,
                'data': results,
                'count': len(results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'批量获取价格失败: {str(e)}',
                'data': []
            }
    
    @staticmethod
    def get_market_overview():
        """获取市场概况 - 使用东方财富API获取精确实时数据"""
        try:
            # 使用东方财富API获取完整市场统计
            market_stats = RealTimeDataService.get_complete_market_stats_eastmoney()

            # 获取主要指数数据（使用腾讯API）
            indices_data = RealTimeDataService.get_indices_from_tencent()

            if market_stats:
                # 计算资金流向（使用真实的东方财富数据）
                up_ratio = market_stats['up_count'] / market_stats['total_count'] if market_stats['total_count'] > 0 else 0
                down_ratio = market_stats['down_count'] / market_stats['total_count'] if market_stats['total_count'] > 0 else 0

                # 使用真实的净资金流向数据
                net_inflow = market_stats.get('net_inflow_billion', 0)
                total_inflow = market_stats.get('total_inflow_billion', 0)
                total_outflow = market_stats.get('total_outflow_billion', 0)

                formatted_stats = {
                    'up_count': market_stats['up_count'],
                    'down_count': market_stats['down_count'],
                    'flat_count': market_stats['flat_count'],
                    'limit_up_count': market_stats['limit_up_count'],
                    'limit_down_count': market_stats['limit_down_count'],
                    'total_count': market_stats['total_count'],
                    'net_inflow': round(net_inflow, 2),
                    'total_inflow': round(total_inflow, 2),
                    'total_outflow': round(total_outflow, 2),
                    'up_ratio': round(up_ratio * 100, 2),
                    'down_ratio': round(down_ratio * 100, 2),
                    'stocks_with_flow_data': market_stats.get('stocks_with_flow_data', 0)
                }

                return {
                    'success': True,
                    'data': {
                        'market_stats': formatted_stats,
                        'indices': indices_data,
                        'timestamp': datetime.now().isoformat(),
                        'data_source': '东方财富完整数据',
                        'sample_size': market_stats['sample_size']
                    },
                    'message': f'成功获取{market_stats["sample_size"]}只股票的完整市场数据'
                }
            else:
                # 如果API失败，回退到本地数据库
                print("东方财富API获取失败, 使用回退方案")
                return RealTimeDataService.get_market_overview_from_db()

        except Exception as e:
            print(f"市场概况获取错误: {e}")
            # 完全失败时的回退方案
            return RealTimeDataService.get_market_overview_from_db()

    @staticmethod
    def get_indices_from_tencent():
        """从腾讯API获取指数数据"""
        try:
            codes = "sh000001,sz399001,sz399006"
            url = f"http://qt.gtimg.cn/q={codes}"

            response = requests.get(url, timeout=5)
            response.encoding = 'gbk'

            indices_data = []

            if response.status_code == 200:
                lines = response.text.strip().split('\n')

                for line in lines:
                    if 'v_' in line and '=' in line:
                        code_match = re.search(r'v_([^=]+)', line)
                        data_match = re.search(r'"([^"]+)"', line)

                        if code_match and data_match:
                            code = code_match.group(1)
                            data_str = data_match.group(1)
                            data_parts = data_str.split('~')

                            if len(data_parts) >= 6:
                                try:
                                    name = data_parts[1]
                                    current = float(data_parts[3])      # 现价
                                    prev_close = float(data_parts[4])   # 昨收价

                                    # 计算涨跌额和涨跌幅
                                    change = current - prev_close
                                    pct_chg = (change / prev_close * 100) if prev_close > 0 else 0

                                    indices_data.append({
                                        'code': code,
                                        'name': name,
                                        'current': current,
                                        'change': round(change, 2),
                                        'pct_chg': round(pct_chg, 2)
                                    })

                                except (ValueError, IndexError):
                                    continue

            return indices_data

        except Exception as e:
            print(f"获取指数失败: {e}")
            return []

    @staticmethod
    def get_market_overview_from_db():
        """从本地数据库获取市场概况（回退方案）"""
        try:
            # 获取主要指数数据
            major_indices = ['000001.SH', '399001.SZ', '399006.SZ']  # 上证指数、深成指、创业板指
            indices_data = []

            for index_code in major_indices:
                try:
                    # 从IndexDaily表获取数据
                    latest_index = IndexDaily.objects.filter(ts_code=index_code).order_by('-trade_date').first()
                    if latest_index:
                        indices_data.append({
                            'ts_code': index_code,
                            'name': RealTimeDataService.get_index_name(index_code),
                            'current_price': float(latest_index.close) if latest_index.close else 0,
                            'change': float(latest_index.change) if latest_index.change else 0,
                            'pct_chg': float(latest_index.pct_chg) if latest_index.pct_chg else 0,
                            'volume': latest_index.vol if latest_index.vol else 0,
                            'amount': float(latest_index.amount) if latest_index.amount else 0,
                        })
                except Exception as e:
                    continue

            # 获取市场统计数据 - 涨跌分布
            latest_date = StockDaily.objects.values('trade_date').order_by('-trade_date').first()
            market_stats = {
                'up_count': 0,
                'down_count': 0,
                'flat_count': 0,
                'total_count': 0,
                'net_inflow': 0,  # 本地数据库没有资金流向数据，设为0
                'total_inflow': 0,
                'total_outflow': 0
            }

            if latest_date:
                daily_data = StockDaily.objects.filter(trade_date=latest_date['trade_date'])

                # 统计涨跌分布
                total_count = daily_data.count()
                up_count = daily_data.filter(pct_chg__gt=0).count()
                down_count = daily_data.filter(pct_chg__lt=0).count()
                flat_count = daily_data.filter(pct_chg=0).count()

                market_stats = {
                    'up_count': up_count,
                    'down_count': down_count,
                    'flat_count': flat_count,
                    'total_count': total_count,
                    'net_inflow': 0,  # 本地数据库没有资金流向数据
                    'total_inflow': 0,
                    'total_outflow': 0,
                    'trade_date': latest_date['trade_date'].strftime('%Y-%m-%d')
                }

            return {
                'success': True,
                'data': {
                    'indices': indices_data,
                    'market_stats': market_stats,
                    'timestamp': timezone.now().isoformat(),
                    'data_source': '本地数据库（无资金流向数据）'
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'获取市场概况失败: {str(e)}',
                'data': None
            }

    @staticmethod
    def get_index_name(ts_code):
        """获取指数名称"""
        index_names = {
            '000001.SH': '上证指数',
            '399001.SZ': '深证成指',
            '399006.SZ': '创业板指',
            '000300.SH': '沪深300',
            '000905.SH': '中证500'
        }
        return index_names.get(ts_code, ts_code)
