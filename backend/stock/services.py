# -*- coding: utf-8 -*-

import os
import tushare as ts
from datetime import datetime, timedelta
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from dotenv import load_dotenv

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
        """获取热门牛股 - 基于涨跌幅排序，返回每日涨幅最大的股票"""
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
            print(f"获取热门股票失败: {str(e)}")
            raise  # 直接抛出异常，不返回空数组
    
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
        """获取股票实时价格 - 用于5秒刷新"""
        try:
            # 在交易时间，尝试获取实时数据
            if RealTimeDataService.is_trading_time() and pro:
                try:
                    # 获取实时行情（限制调用频率）
                    df = pro.daily(ts_code=ts_code, trade_date='', limit=1)
                    if not df.empty:
                        row = df.iloc[0]
                        return {
                            'success': True,
                            'data': {
                                'ts_code': ts_code,
                                'current_price': float(row['close']),
                                'open_price': float(row['open']),
                                'high_price': float(row['high']),
                                'low_price': float(row['low']),
                                'change': float(row['change']),
                                'pct_chg': float(row['pct_chg']),
                                'volume': int(row['vol']),
                                'amount': float(row['amount']),
                                'timestamp': datetime.now().isoformat(),
                                'is_real_time': True
                            }
                        }
                except Exception as e:
                    print(f"实时数据获取失败: {e}")
            
            # 回退到数据库最新数据
            latest_daily = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date').first()
            if latest_daily:
                return {
                    'success': True,
                    'data': {
                        'ts_code': ts_code,
                        'current_price': float(latest_daily.close) if latest_daily.close else 0,
                        'open_price': float(latest_daily.open) if latest_daily.open else 0,
                        'high_price': float(latest_daily.high) if latest_daily.high else 0,
                        'low_price': float(latest_daily.low) if latest_daily.low else 0,
                        'change': float(latest_daily.change) if latest_daily.change else 0,
                        'pct_chg': float(latest_daily.pct_chg) if latest_daily.pct_chg else 0,
                        'volume': latest_daily.vol if latest_daily.vol else 0,
                        'amount': float(latest_daily.amount) if latest_daily.amount else 0,
                        'timestamp': datetime.now().isoformat(),
                        'is_real_time': False
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
        """获取市场概况"""
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
            
            # 获取市场统计数据
            latest_date = StockDaily.objects.values('trade_date').order_by('-trade_date').first()
            market_stats = {}
            
            if latest_date:
                daily_data = StockDaily.objects.filter(trade_date=latest_date['trade_date'])
                
                # 统计涨跌家数
                up_count = daily_data.filter(pct_chg__gt=0).count()
                down_count = daily_data.filter(pct_chg__lt=0).count()
                equal_count = daily_data.filter(pct_chg=0).count()
                
                market_stats = {
                    'trade_date': latest_date['trade_date'].strftime('%Y-%m-%d'),
                    'total_stocks': daily_data.count(),
                    'up_count': up_count,
                    'down_count': down_count,
                    'equal_count': equal_count,
                    'up_ratio': round(up_count / daily_data.count() * 100, 2) if daily_data.count() > 0 else 0
                }
            
            return {
                'success': True,
                'data': {
                    'indices': indices_data,
                    'market_stats': market_stats,
                    'trading_status': {
                        'is_trading_time': RealTimeDataService.is_trading_time(),
                        'time_period': RealTimeDataService.get_time_period(),
                        'timestamp': datetime.now().isoformat()
                    }
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
