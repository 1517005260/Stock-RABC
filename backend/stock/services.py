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
        """获取热门牛股 - 基于涨跌幅排序"""
        try:
            # 获取最新交易日的股票数据，按涨跌幅排序
            latest_date = StockDaily.objects.values('trade_date').order_by('-trade_date').first()
            if not latest_date:
                return []
            
            top_stocks = StockDaily.objects.filter(
                trade_date=latest_date['trade_date'],
                pct_chg__isnull=False
            ).select_related().order_by('-pct_chg')[:limit]
            
            result = []
            for stock_daily in top_stocks:
                try:
                    stock_basic = StockBasic.objects.get(ts_code=stock_daily.ts_code)
                    result.append({
                        'ts_code': stock_daily.ts_code,
                        'name': stock_basic.name,
                        'close': stock_daily.close,
                        'change': stock_daily.change,
                        'pct_chg': stock_daily.pct_chg,
                        'vol': stock_daily.vol,
                        'amount': stock_daily.amount,
                    })
                except StockBasic.DoesNotExist:
                    continue
            
            return result
        
        except Exception as e:
            return []


class TradingService:
    """交易服务"""
    
    @staticmethod
    def get_or_create_account(user):
        """获取或创建用户股票账户"""
        try:
            account = UserStockAccount.objects.get(user=user)
        except UserStockAccount.DoesNotExist:
            # 根据用户角色设置初始资金
            user_roles = SysUserRole.objects.filter(user=user)
            initial_balance = Decimal('100000.00')  # 默认普通用户
            
            for user_role in user_roles:
                if user_role.role.code == 'admin':
                    initial_balance = Decimal('500000.00')
                    break
                elif user_role.role.code == 'superadmin':
                    initial_balance = Decimal('1000000.00')
                    break
            
            account = UserStockAccount.objects.create(
                user=user,
                account_balance=initial_balance,
                total_assets=initial_balance
            )
        
        return account
    
    @staticmethod
    def buy_stock(user, ts_code, price, shares):
        """买入股票"""
        try:
            with transaction.atomic():
                # 检查股票是否存在
                try:
                    stock = StockBasic.objects.get(ts_code=ts_code)
                except StockBasic.DoesNotExist:
                    return {'success': False, 'message': '股票代码不存在'}
                
                # 获取用户账户
                account = TradingService.get_or_create_account(user)
                
                # 计算交易金额和手续费
                price = Decimal(str(price))
                trade_amount = price * shares
                commission = Decimal('5.00')  # 固定手续费
                total_cost = trade_amount + commission
                
                # 检查账户余额
                if account.account_balance < total_cost:
                    return {'success': False, 'message': '账户余额不足'}
                
                # 检查用户状态
                if user.status == 1:  # 停用状态
                    return {'success': False, 'message': '账户已被冻结，无法交易'}
                
                # 扣减账户余额
                account.account_balance -= total_cost
                account.save()
                
                # 更新持仓
                position, created = UserPosition.objects.get_or_create(
                    user=user,
                    ts_code=ts_code,
                    defaults={
                        'stock_name': stock.name,
                        'position_shares': 0,
                        'available_shares': 0,
                        'cost_price': price,
                        'current_price': price,
                    }
                )
                
                if created:
                    position.position_shares = shares
                    position.available_shares = shares
                    position.cost_price = price
                else:
                    # 计算新的成本价（加权平均）
                    total_cost_old = position.cost_price * position.position_shares
                    total_cost_new = price * shares
                    new_total_shares = position.position_shares + shares
                    
                    position.cost_price = (total_cost_old + total_cost_new) / new_total_shares
                    position.position_shares = new_total_shares
                    position.available_shares += shares
                
                position.current_price = price
                position.save()
                
                # 记录交易
                TradeRecord.objects.create(
                    user=user,
                    ts_code=ts_code,
                    stock_name=stock.name,
                    trade_type='BUY',
                    trade_price=price,
                    trade_shares=shares,
                    trade_amount=trade_amount,
                    commission=commission,
                    status='COMPLETED',
                    remark=f'买入{stock.name} {shares}股'
                )
                
                return {
                    'success': True,
                    'message': f'成功买入{stock.name} {shares}股',
                    'remaining_balance': account.account_balance
                }
        
        except Exception as e:
            return {'success': False, 'message': f'买入失败: {str(e)}'}
    
    @staticmethod
    def sell_stock(user, ts_code, price, shares):
        """卖出股票"""
        try:
            with transaction.atomic():
                # 检查持仓
                try:
                    position = UserPosition.objects.get(user=user, ts_code=ts_code)
                except UserPosition.DoesNotExist:
                    return {'success': False, 'message': '未持有该股票'}
                
                # 检查可卖数量
                if position.available_shares < shares:
                    return {'success': False, 'message': f'可卖数量不足，当前可卖: {position.available_shares}股'}
                
                # 获取股票信息
                stock = StockBasic.objects.get(ts_code=ts_code)
                
                # 获取用户账户
                account = TradingService.get_or_create_account(user)
                
                # 计算交易金额和手续费
                price = Decimal(str(price))
                trade_amount = price * shares
                commission = Decimal('5.00')
                net_amount = trade_amount - commission
                
                # 增加账户余额
                account.account_balance += net_amount
                account.save()
                
                # 更新持仓
                position.position_shares -= shares
                position.available_shares -= shares
                position.current_price = price
                
                # 如果持仓为0，删除持仓记录
                if position.position_shares <= 0:
                    position.delete()
                else:
                    position.save()
                
                # 记录交易
                TradeRecord.objects.create(
                    user=user,
                    ts_code=ts_code,
                    stock_name=stock.name,
                    trade_type='SELL',
                    trade_price=price,
                    trade_shares=shares,
                    trade_amount=trade_amount,
                    commission=commission,
                    status='COMPLETED',
                    remark=f'卖出{stock.name} {shares}股'
                )
                
                return {
                    'success': True,
                    'message': f'成功卖出{stock.name} {shares}股',
                    'net_amount': net_amount,
                    'remaining_balance': account.account_balance
                }
        
        except Exception as e:
            return {'success': False, 'message': f'卖出失败: {str(e)}'}
    
    @staticmethod
    def get_user_positions(user):
        """获取用户持仓"""
        positions = UserPosition.objects.filter(user=user).order_by('-update_time')
        result = []
        
        for position in positions:
            # 计算盈亏
            profit_loss = (position.current_price - position.cost_price) * position.position_shares
            profit_loss_ratio = ((position.current_price - position.cost_price) / position.cost_price * 100) if position.cost_price > 0 else 0
            
            result.append({
                'ts_code': position.ts_code,
                'stock_name': position.stock_name,
                'position_shares': position.position_shares,
                'available_shares': position.available_shares,
                'cost_price': float(position.cost_price),
                'current_price': float(position.current_price),
                'profit_loss': float(profit_loss),
                'profit_loss_ratio': float(profit_loss_ratio),
                'market_value': float(position.current_price * position.position_shares),
            })
        
        return result
    
    @staticmethod
    def get_user_trades(user, limit=20):
        """获取用户交易记录"""
        trades = TradeRecord.objects.filter(user=user).order_by('-trade_time')[:limit]
        return [
            {
                'id': trade.id,
                'ts_code': trade.ts_code,
                'stock_name': trade.stock_name,
                'trade_type': trade.trade_type,
                'trade_type_display': trade.get_trade_type_display(),
                'trade_price': trade.trade_price,
                'trade_shares': trade.trade_shares,
                'trade_amount': trade.trade_amount,
                'commission': trade.commission,
                'trade_time': trade.trade_time,
                'status': trade.status,
                'remark': trade.remark,
            }
            for trade in trades
        ]


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
        return UserPermissionService.has_permission(user, ['admin', 'superadmin'])
    
    @staticmethod
    def is_superadmin(user):
        """检查是否为超级管理员"""
        return UserPermissionService.has_permission(user, ['superadmin'])
    
    @staticmethod
    def get_admin_users():
        """获取所有管理员用户"""
        admin_roles = SysRole.objects.filter(code__in=['admin', 'superadmin'])
        admin_user_roles = SysUserRole.objects.filter(role__in=admin_roles)
        return [ur.user for ur in admin_user_roles]


class NewsService:
    """新闻服务"""
    
    @staticmethod
    def get_latest_news(limit=10):
        """获取最新市场新闻"""
        return MarketNews.objects.order_by('-publish_time')[:limit]
    
    @staticmethod
    def create_news(title, content, source=None, category=None, related_stocks=None):
        """创建新闻"""
        return MarketNews.objects.create(
            title=title,
            content=content,
            source=source or '系统',
            publish_time=datetime.now(),
            category=category,
            related_stocks=related_stocks
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
    
    @staticmethod
    def get_intraday_chart_data(ts_code):
        """获取分时图数据 - 使用智能缓存和限流策略"""
        try:
            # 1. 检查缓存
            cache_key = f"intraday_chart_{ts_code}"
            cached_data = DataCache.get(cache_key, expiry_seconds=30)  # 30秒缓存
            if cached_data:
                cached_data['data']['message'] = f'使用缓存数据 (30秒内有效)'
                cached_data['data']['data_source'] = 'cache'
                return cached_data
            
            # 2. 检查限流
            api_name = "stk_mins"
            if not RateLimiter.can_call(api_name, max_calls=2, time_window=60):
                wait_time = RateLimiter.get_wait_time(api_name, max_calls=2, time_window=60)
                
                # 超出限流，返回数据库中的最新数据
                latest_daily = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date').first()
                if not latest_daily:
                    return {
                        'success': False,
                        'message': f'API限流中，需等待{int(wait_time)}秒，且未找到股票数据'
                    }
                
                return {
                    'success': True,
                    'data': {
                        'ts_code': ts_code,
                        'intraday_data': [],  # 限流期间不提供分时数据
                        'base_info': {
                            'current_price': float(latest_daily.close) if latest_daily.close else 0,
                            'pre_close': float(latest_daily.pre_close) if latest_daily.pre_close else 0,
                            'high': float(latest_daily.high) if latest_daily.high else 0,
                            'low': float(latest_daily.low) if latest_daily.low else 0,
                            'change': float(latest_daily.change) if latest_daily.change else 0,
                            'pct_chg': float(latest_daily.pct_chg) if latest_daily.pct_chg else 0,
                            'volume': latest_daily.vol if latest_daily.vol else 0,
                            'amount': float(latest_daily.amount) if latest_daily.amount else 0,
                            'trade_date': latest_daily.trade_date.strftime('%Y-%m-%d')
                        },
                        'timestamp': datetime.now().isoformat(),
                        'data_source': 'database_daily_rate_limited',
                        'message': f'API限流中，需等待{int(wait_time)}秒。显示最新日线数据'
                    }
                }
            
            # 3. 获取基础数据
            latest_daily = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date').first()
            if not latest_daily:
                return {
                    'success': False,
                    'message': '未找到股票数据'
                }
            
            # 4. 尝试获取真实的分时数据
            intraday_data = []
            data_source = 'database_daily'
            message = '当前非交易时间或无分时数据权限，显示最新日线数据'
            
            try:
                if pro and RealTimeDataService.is_trading_time():
                    # 记录API调用
                    RateLimiter.record_call(api_name)
                    
                    # 使用Tushare获取分时数据
                    today = datetime.now().strftime('%Y%m%d')
                    df = pro.stk_mins(ts_code=ts_code, freq='1min', trade_date=today)
                    
                    if not df.empty:
                        for _, row in df.iterrows():
                            intraday_data.append({
                                'time': datetime.strptime(str(row['trade_time']), '%Y%m%d %H%M%S').strftime('%H:%M'),
                                'price': float(row['close']) if row['close'] else 0,
                                'volume': int(row['vol']) if row['vol'] else 0,
                                'amount': float(row['amount']) if row['amount'] else 0,
                                'change': float(row['close'] - latest_daily.pre_close) if row['close'] and latest_daily.pre_close else 0,
                                'pct_change': float((row['close'] - latest_daily.pre_close) / latest_daily.pre_close * 100) if row['close'] and latest_daily.pre_close else 0
                            })
                        
                        data_source = 'tushare_realtime'
                        message = f'获取到{len(intraday_data)}个分时数据点'
                
            except Exception as e:
                print(f"获取Tushare分时数据失败: {e}")
                # 如果API调用失败，返回空分时数据但保留基础信息
                data_source = 'database_daily_api_failed'
                message = f'Tushare API调用失败: {str(e)}，显示最新日线数据'
            
            # 5. 构建返回数据
            result = {
                'success': True,
                'data': {
                    'ts_code': ts_code,
                    'intraday_data': intraday_data,
                    'base_info': {
                        'current_price': float(latest_daily.close) if latest_daily.close else 0,
                        'pre_close': float(latest_daily.pre_close) if latest_daily.pre_close else 0,
                        'high': float(latest_daily.high) if latest_daily.high else 0,
                        'low': float(latest_daily.low) if latest_daily.low else 0,
                        'change': float(latest_daily.change) if latest_daily.change else 0,
                        'pct_chg': float(latest_daily.pct_chg) if latest_daily.pct_chg else 0,
                        'volume': latest_daily.vol if latest_daily.vol else 0,
                        'amount': float(latest_daily.amount) if latest_daily.amount else 0,
                        'trade_date': latest_daily.trade_date.strftime('%Y-%m-%d')
                    },
                    'timestamp': datetime.now().isoformat(),
                    'data_source': data_source,
                    'message': message
                }
            }
            
            # 6. 缓存结果
            DataCache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'message': f'获取分时图数据失败: {str(e)}'
            }
    
    @staticmethod
    def get_realtime_tick_data(ts_code):
        """获取实时逐笔数据 - 使用Tushare真实数据"""
        try:
            # 获取最新股票数据作为基础信息
            latest_daily = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date').first()
            if not latest_daily:
                return {
                    'success': False,
                    'message': '未找到股票数据'
                }
            
            # 尝试获取真实逐笔数据
            tick_data = []
            try:
                if pro and RealTimeDataService.is_trading_time():
                    # 使用Tushare获取逐笔数据（需要高级权限）
                    today = datetime.now().strftime('%Y%m%d')
                    
                    # 注意：逐笔数据接口需要很高的权限等级，大部分用户无法访问
                    # 这里尝试调用，如果失败则回退到基础信息
                    df = pro.stk_ticks(ts_code=ts_code, trade_date=today)
                    
                    if not df.empty:
                        # 取最新的20条逐笔数据
                        recent_ticks = df.head(20)
                        for _, row in recent_ticks.iterrows():
                            tick_data.append({
                                'time': datetime.strptime(str(row['trade_time']), '%Y%m%d %H%M%S').strftime('%H:%M:%S'),
                                'price': float(row['price']) if row['price'] else 0,
                                'volume': int(row['vol']) if row['vol'] else 0,
                                'amount': float(row['amount']) if row['amount'] else 0,
                                'bs_flag': row['bs_flag'] if 'bs_flag' in row else 'N',  # 买卖标识
                                'change': float(row['change']) if 'change' in row and row['change'] else 0
                            })
                
            except Exception as e:
                print(f"获取Tushare逐笔数据失败: {e}")
                # 逐笔数据获取失败是正常的，因为需要很高权限
            
            base_price = float(latest_daily.close) if latest_daily.close else 0
            
            return {
                'success': True,
                'data': {
                    'ts_code': ts_code,
                    'tick_data': tick_data,  # 如果获取失败则为空列表
                    'base_info': {
                        'current_price': base_price,
                        'latest_trade_date': latest_daily.trade_date.strftime('%Y-%m-%d'),
                        'volume': latest_daily.vol if latest_daily.vol else 0,
                        'amount': float(latest_daily.amount) if latest_daily.amount else 0,
                        'change': float(latest_daily.change) if latest_daily.change else 0,
                        'pct_chg': float(latest_daily.pct_chg) if latest_daily.pct_chg else 0
                    },
                    'timestamp': datetime.now().isoformat(),
                    'data_source': 'tushare_ticks' if tick_data else 'database_daily',
                    'message': f'逐笔数据条数: {len(tick_data)}' if tick_data else '当前非交易时间或无逐笔数据权限，显示基础股票信息'
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'获取逐笔数据失败: {str(e)}'
            }
