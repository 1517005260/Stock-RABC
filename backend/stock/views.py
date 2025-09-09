# -*- coding: utf-8 -*-

import json
from decimal import Decimal
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q

from stock.models import StockBasic, StockDaily, StockCompany, StockBasicSerializer, StockDailySerializer, StockCompanySerializer
from stock.services import StockDataService, TradingService, UserPermissionService, RealTimeDataService
from utils.permissions import require_role, require_login, admin_required, superadmin_required
from user.models import SysUser


@require_login
def stock_list(request):
    """股票列表 - 所有用户可访问"""
    try:
        # 获取查询参数
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        keyword = request.GET.get('keyword', '').strip()
        industry = request.GET.get('industry', '').strip()
        market = request.GET.get('market', '').strip()
        
        # 构建查询条件
        queryset = StockBasic.objects.filter(list_status='L')  # 只显示上市股票
        
        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword) | 
                Q(ts_code__icontains=keyword) |
                Q(symbol__icontains=keyword)
            )
        
        if industry:
            queryset = queryset.filter(industry=industry)
        
        if market:
            queryset = queryset.filter(market=market)
        
        # 分页
        paginator = Paginator(queryset.order_by('ts_code'), page_size)
        stocks = paginator.get_page(page)
        
        # 序列化数据
        stock_list = []
        for stock in stocks:
            # 获取最新行情数据
            latest_daily = StockDaily.objects.filter(ts_code=stock.ts_code).order_by('-trade_date').first()
            
            stock_data = {
                'ts_code': stock.ts_code,
                'symbol': stock.symbol,
                'name': stock.name,
                'industry': stock.industry,
                'market': stock.market,
                'area': stock.area,
                'list_date': stock.list_date.strftime('%Y-%m-%d') if stock.list_date else None,
                'current_price': float(latest_daily.close) if latest_daily and latest_daily.close else None,
                'change': float(latest_daily.change) if latest_daily and latest_daily.change else None,
                'pct_chg': float(latest_daily.pct_chg) if latest_daily and latest_daily.pct_chg else None,
                'volume': latest_daily.vol if latest_daily else None,
                'amount': float(latest_daily.amount) if latest_daily and latest_daily.amount else None,
                'trade_date': latest_daily.trade_date.strftime('%Y-%m-%d') if latest_daily else None,
            }
            stock_list.append(stock_data)
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'list': stock_list,
                'total': paginator.count,
                'page': page,
                'pageSize': page_size,
                'totalPages': paginator.num_pages,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取股票列表失败: {str(e)}'
        })


@require_login
def stock_detail(request, ts_code):
    """股票详情 - 所有用户可访问"""
    try:
        # 获取股票基本信息
        try:
            stock = StockBasic.objects.get(ts_code=ts_code)
        except StockBasic.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'msg': '股票不存在'
            })
        
        # 获取最新行情
        latest_daily = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date').first()
        
        # 获取历史行情数据（最近30天）
        history_data = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date')[:30]
        history_list = []
        for daily in reversed(history_data):  # 按时间正序
            history_list.append({
                'date': daily.trade_date.strftime('%Y-%m-%d'),
                'open': float(daily.open) if daily.open else None,
                'high': float(daily.high) if daily.high else None,
                'low': float(daily.low) if daily.low else None,
                'close': float(daily.close) if daily.close else None,
                'volume': daily.vol,
                'amount': float(daily.amount) if daily.amount else None,
            })
        
        # 获取公司信息
        company_info = None
        try:
            company = StockCompany.objects.get(ts_code=ts_code)
            company_info = {
                'chairman': company.chairman,
                'manager': company.manager,
                'secretary': company.secretary,
                'reg_capital': float(company.reg_capital) if company.reg_capital else None,
                'setup_date': company.setup_date.strftime('%Y-%m-%d') if company.setup_date else None,
                'province': company.province,
                'city': company.city,
                'introduction': company.introduction,
                'website': company.website,
                'employees': company.employees,
                'main_business': company.main_business,
            }
        except StockCompany.DoesNotExist:
            pass
        
        stock_detail = {
            'ts_code': stock.ts_code,
            'symbol': stock.symbol,
            'name': stock.name,
            'fullname': stock.fullname,
            'industry': stock.industry,
            'market': stock.market,
            'area': stock.area,
            'exchange': stock.exchange,
            'list_date': stock.list_date.strftime('%Y-%m-%d') if stock.list_date else None,
            'current_price': float(latest_daily.close) if latest_daily and latest_daily.close else None,
            'open_price': float(latest_daily.open) if latest_daily and latest_daily.open else None,
            'high_price': float(latest_daily.high) if latest_daily and latest_daily.high else None,
            'low_price': float(latest_daily.low) if latest_daily and latest_daily.low else None,
            'pre_close': float(latest_daily.pre_close) if latest_daily and latest_daily.pre_close else None,
            'change': float(latest_daily.change) if latest_daily and latest_daily.change else None,
            'pct_chg': float(latest_daily.pct_chg) if latest_daily and latest_daily.pct_chg else None,
            'volume': latest_daily.vol if latest_daily else None,
            'amount': float(latest_daily.amount) if latest_daily and latest_daily.amount else None,
            'trade_date': latest_daily.trade_date.strftime('%Y-%m-%d') if latest_daily else None,
            'history_data': history_list,
            'company_info': company_info,
        }
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': stock_detail
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取股票详情失败: {str(e)}'
        })


@require_login
def stock_hot_list(request):
    """热门牛股 - 所有用户可访问"""
    try:
        limit = int(request.GET.get('limit', 10))
        hot_stocks = StockDataService.get_top_stocks(limit)
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': hot_stocks
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取热门股票失败: {str(e)}'
        })


@superadmin_required
@require_http_methods(["POST"])
@csrf_exempt
def sync_stock_data(request):
    """同步股票数据 - 仅超级管理员可访问"""
    try:
        data = json.loads(request.body)
        data_type = data.get('type', 'basic')  # basic, daily, company
        
        if data_type == 'basic':
            # 同步股票基本信息
            result = StockDataService.sync_stock_basic()
        elif data_type == 'daily':
            # 同步日线数据
            ts_code = data.get('ts_code')
            days = data.get('days', 30)
            if not ts_code:
                return JsonResponse({
                    'code': 400,
                    'msg': '请提供股票代码'
                })
            result = StockDataService.sync_stock_daily(ts_code, days)
        elif data_type == 'company':
            # 同步公司信息
            ts_codes = data.get('ts_codes', [])
            if not ts_codes:
                return JsonResponse({
                    'code': 400,
                    'msg': '请提供股票代码列表'
                })
            result = StockDataService.sync_company_info(ts_codes)
        else:
            return JsonResponse({
                'code': 400,
                'msg': '不支持的数据类型'
            })
        
        if result['success']:
            return JsonResponse({
                'code': 200,
                'msg': result['message'],
                'data': {'count': result.get('count', 0)}
            })
        else:
            return JsonResponse({
                'code': 500,
                'msg': result['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'同步数据失败: {str(e)}'
        })


@require_login
def stock_search(request):
    """股票搜索 - 所有用户可访问"""
    try:
        keyword = request.GET.get('keyword', '').strip()
        limit = int(request.GET.get('limit', 10))
        
        if not keyword:
            return JsonResponse({
                'code': 400,
                'msg': '请输入搜索关键词'
            })
        
        # 搜索股票
        stocks = StockBasic.objects.filter(
            Q(name__icontains=keyword) | 
            Q(ts_code__icontains=keyword) |
            Q(symbol__icontains=keyword),
            list_status='L'
        )[:limit]
        
        result = []
        for stock in stocks:
            result.append({
                'ts_code': stock.ts_code,
                'symbol': stock.symbol,
                'name': stock.name,
                'industry': stock.industry,
                'market': stock.market,
            })
        
        return JsonResponse({
            'code': 200,
            'msg': '搜索成功',
            'data': result
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'搜索失败: {str(e)}'
        })


@require_login
def stock_industries(request):
    """获取股票行业列表 - 所有用户可访问"""
    try:
        industries = StockBasic.objects.values_list('industry', flat=True).distinct().exclude(industry__isnull=True).exclude(industry='')
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': list(industries)
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取行业列表失败: {str(e)}'
        })


@require_login
def stock_realtime_data(request, ts_code):
    """获取股票实时分时数据 - 所有用户可访问"""
    try:
        result = RealTimeDataService.get_realtime_tick_data(ts_code)
        
        if result['success']:
            return JsonResponse({
                'code': 200,
                'msg': '获取成功',
                'data': result['data']
            })
        else:
            return JsonResponse({
                'code': 500,
                'msg': result['message']
            })
            
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取实时数据失败: {str(e)}'
        })


@require_login
def stock_intraday_chart(request, ts_code):
    """获取股票分时图数据 - 所有用户可访问，支持5秒刷新"""
    try:
        result = RealTimeDataService.get_intraday_chart_data(ts_code)
        
        if result['success']:
            return JsonResponse({
                'code': 200,
                'msg': '获取成功',
                'data': result['data']
            })
        else:
            return JsonResponse({
                'code': 500,
                'msg': result['message']
            })
            
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取分时图数据失败: {str(e)}'
        })


@require_login
def stock_realtime_price(request, ts_code):
    """获取股票实时价格 - 所有用户可访问"""
    try:
        result = RealTimeDataService.get_stock_realtime_price(ts_code)
        
        if result['success']:
            return JsonResponse({
                'code': 200,
                'msg': '获取成功',
                'data': result['data']
            })
        else:
            return JsonResponse({
                'code': 500,
                'msg': result['message']
            })
            
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取实时价格失败: {str(e)}'
        })


@require_login
def market_overview(request):
    """获取市场概况 - 所有用户可访问"""
    try:
        result = RealTimeDataService.get_market_overview()
        
        if result['success']:
            return JsonResponse({
                'code': 200,
                'msg': '获取成功',
                'data': result['data']
            })
        else:
            return JsonResponse({
                'code': 500,
                'msg': result['message']
            })
            
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取市场概况失败: {str(e)}'
        })


@require_login
def stock_kline_data(request, ts_code):
    """获取K线图数据 - 所有用户可访问"""
    try:
        # 获取参数
        period = request.GET.get('period', 'daily')  # 周期：daily, weekly, monthly
        limit = int(request.GET.get('limit', 100))    # 数据条数
        adjust = request.GET.get('adjust', 'qfq')     # 复权类型：qfq前复权, hfq后复权, none不复权
        
        # 限制数据条数
        limit = min(limit, 500)
        
        # 获取股票基本信息
        try:
            stock = StockBasic.objects.get(ts_code=ts_code)
        except StockBasic.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'msg': '股票不存在'
            })
        
        # 获取K线数据
        if period == 'daily':
            # 日K线数据
            daily_data = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date')[:limit]
            kline_data = []
            
            for daily in reversed(daily_data):  # 按时间正序
                kline_data.append({
                    'date': daily.trade_date.strftime('%Y-%m-%d'),
                    'open': float(daily.open) if daily.open else 0,
                    'high': float(daily.high) if daily.high else 0,
                    'low': float(daily.low) if daily.low else 0,
                    'close': float(daily.close) if daily.close else 0,
                    'volume': daily.vol if daily.vol else 0,
                    'amount': float(daily.amount) if daily.amount else 0,
                    'change': float(daily.change) if daily.change else 0,
                    'pct_chg': float(daily.pct_chg) if daily.pct_chg else 0,
                    'pre_close': float(daily.pre_close) if daily.pre_close else 0
                })
        
        elif period == 'weekly':
            # 周K线数据（基于日K线聚合）
            kline_data = generate_weekly_kline(ts_code, limit)
            
        elif period == 'monthly':
            # 月K线数据（基于日K线聚合）
            kline_data = generate_monthly_kline(ts_code, limit)
            
        else:
            return JsonResponse({
                'code': 400,
                'msg': '不支持的周期类型'
            })
        
        # 计算技术指标
        technical_indicators = calculate_technical_indicators(kline_data)
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'ts_code': ts_code,
                'name': stock.name,
                'period': period,
                'adjust': adjust,
                'count': len(kline_data),
                'kline_data': kline_data,
                'technical_indicators': technical_indicators,
                'latest_info': kline_data[-1] if kline_data else None
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取K线数据失败: {str(e)}'
        })


def generate_weekly_kline(ts_code, limit=100):
    """生成周K线数据"""
    try:
        from datetime import datetime, timedelta
        import pandas as pd
        
        # 获取足够的日K线数据用于聚合
        daily_data = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date')[:limit*7]
        
        if not daily_data:
            return []
        
        # 转换为DataFrame便于处理
        df_data = []
        for daily in daily_data:
            df_data.append({
                'trade_date': daily.trade_date,
                'open': float(daily.open) if daily.open else 0,
                'high': float(daily.high) if daily.high else 0,
                'low': float(daily.low) if daily.low else 0,
                'close': float(daily.close) if daily.close else 0,
                'volume': daily.vol if daily.vol else 0,
                'amount': float(daily.amount) if daily.amount else 0,
            })
        
        df = pd.DataFrame(df_data)
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df.set_index('trade_date', inplace=True)
        df.sort_index(inplace=True)
        
        # 按周聚合
        weekly_data = df.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'amount': 'sum'
        }).dropna()
        
        # 转换回列表格式
        weekly_kline = []
        for date, row in weekly_data.iterrows():
            weekly_kline.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(row['open'], 2),
                'high': round(row['high'], 2),
                'low': round(row['low'], 2),
                'close': round(row['close'], 2),
                'volume': int(row['volume']),
                'amount': round(row['amount'], 2),
                'change': round(row['close'] - row['open'], 2),
                'pct_chg': round((row['close'] - row['open']) / row['open'] * 100, 2) if row['open'] > 0 else 0,
                'pre_close': 0  # 简化处理
            })
        
        return weekly_kline[-limit:]  # 返回最近的limit条记录
        
    except Exception as e:
        return []


def generate_monthly_kline(ts_code, limit=100):
    """生成月K线数据"""
    try:
        from datetime import datetime, timedelta
        import pandas as pd
        
        # 获取足够的日K线数据用于聚合
        daily_data = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date')[:limit*30]
        
        if not daily_data:
            return []
        
        # 转换为DataFrame便于处理
        df_data = []
        for daily in daily_data:
            df_data.append({
                'trade_date': daily.trade_date,
                'open': float(daily.open) if daily.open else 0,
                'high': float(daily.high) if daily.high else 0,
                'low': float(daily.low) if daily.low else 0,
                'close': float(daily.close) if daily.close else 0,
                'volume': daily.vol if daily.vol else 0,
                'amount': float(daily.amount) if daily.amount else 0,
            })
        
        df = pd.DataFrame(df_data)
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df.set_index('trade_date', inplace=True)
        df.sort_index(inplace=True)
        
        # 按月聚合
        monthly_data = df.resample('M').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'amount': 'sum'
        }).dropna()
        
        # 转换回列表格式
        monthly_kline = []
        for date, row in monthly_data.iterrows():
            monthly_kline.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(row['open'], 2),
                'high': round(row['high'], 2),
                'low': round(row['low'], 2),
                'close': round(row['close'], 2),
                'volume': int(row['volume']),
                'amount': round(row['amount'], 2),
                'change': round(row['close'] - row['open'], 2),
                'pct_chg': round((row['close'] - row['open']) / row['open'] * 100, 2) if row['open'] > 0 else 0,
                'pre_close': 0  # 简化处理
            })
        
        return monthly_kline[-limit:]  # 返回最近的limit条记录
        
    except Exception as e:
        return []


def calculate_technical_indicators(kline_data):
    """计算技术指标"""
    try:
        if len(kline_data) < 20:  # 数据不足
            return {}
        
        import pandas as pd
        import numpy as np
        
        # 转换为DataFrame
        df = pd.DataFrame(kline_data)
        df['close'] = pd.to_numeric(df['close'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['volume'] = pd.to_numeric(df['volume'])
        
        indicators = {}
        
        # 移动平均线 (MA)
        indicators['ma5'] = df['close'].rolling(window=5).mean().round(2).fillna(0).tolist()
        indicators['ma10'] = df['close'].rolling(window=10).mean().round(2).fillna(0).tolist()
        indicators['ma20'] = df['close'].rolling(window=20).mean().round(2).fillna(0).tolist()
        indicators['ma60'] = df['close'].rolling(window=60).mean().round(2).fillna(0).tolist() if len(kline_data) >= 60 else []
        
        # 指数移动平均线 (EMA)
        indicators['ema12'] = df['close'].ewm(span=12).mean().round(2).fillna(0).tolist()
        indicators['ema26'] = df['close'].ewm(span=26).mean().round(2).fillna(0).tolist()
        
        # MACD
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9).mean()
        macd = (dif - dea) * 2
        
        indicators['macd'] = {
            'dif': dif.round(2).fillna(0).tolist(),
            'dea': dea.round(2).fillna(0).tolist(),
            'macd': macd.round(2).fillna(0).tolist()
        }
        
        # RSI 相对强弱指标
        if len(kline_data) >= 14:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            indicators['rsi'] = rsi.round(2).fillna(50).tolist()
        
        # 布林带 (BOLL)
        if len(kline_data) >= 20:
            ma20 = df['close'].rolling(window=20).mean()
            std20 = df['close'].rolling(window=20).std()
            upper = ma20 + (std20 * 2)
            lower = ma20 - (std20 * 2)
            
            indicators['boll'] = {
                'upper': upper.round(2).fillna(0).tolist(),
                'middle': ma20.round(2).fillna(0).tolist(),
                'lower': lower.round(2).fillna(0).tolist()
            }
        
        # KDJ 随机指标
        if len(kline_data) >= 9:
            low_min = df['low'].rolling(window=9).min()
            high_max = df['high'].rolling(window=9).max()
            rsv = (df['close'] - low_min) / (high_max - low_min) * 100
            k = rsv.ewm(com=2).mean()
            d = k.ewm(com=2).mean()
            j = 3 * k - 2 * d
            
            indicators['kdj'] = {
                'k': k.round(2).fillna(50).tolist(),
                'd': d.round(2).fillna(50).tolist(),
                'j': j.round(2).fillna(50).tolist()
            }
        
        # 成交量移动平均
        indicators['vol_ma5'] = df['volume'].rolling(window=5).mean().round(0).fillna(0).tolist()
        indicators['vol_ma10'] = df['volume'].rolling(window=10).mean().round(0).fillna(0).tolist()
        
        return indicators
        
    except Exception as e:
        return {}


@require_login
def stock_technical_analysis(request, ts_code):
    """获取股票技术分析数据 - 所有用户可访问"""
    try:
        # 获取最近100天的数据用于技术分析
        daily_data = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date')[:100]
        
        if not daily_data:
            return JsonResponse({
                'code': 404,
                'msg': '未找到股票数据'
            })
        
        # 转换数据格式
        kline_data = []
        for daily in reversed(daily_data):
            kline_data.append({
                'date': daily.trade_date.strftime('%Y-%m-%d'),
                'close': float(daily.close) if daily.close else 0,
                'high': float(daily.high) if daily.high else 0,
                'low': float(daily.low) if daily.low else 0,
                'volume': daily.vol if daily.vol else 0,
            })
        
        # 计算技术指标
        indicators = calculate_technical_indicators(kline_data)
        
        # 获取最新技术指标值
        latest_indicators = {}
        for key, value in indicators.items():
            if isinstance(value, list) and value:
                latest_indicators[key] = value[-1]
            elif isinstance(value, dict):
                latest_indicators[key] = {}
                for k, v in value.items():
                    if isinstance(v, list) and v:
                        latest_indicators[key][k] = v[-1]
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'ts_code': ts_code,
                'latest_indicators': latest_indicators,
                'full_indicators': indicators,
                'data_count': len(kline_data)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取技术分析数据失败: {str(e)}'
        })


@require_login
def market_news_list(request):
    """获取市场新闻列表 - 所有用户可访问"""
    try:
        from trading.models import MarketNews
        
        # 获取查询参数
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        category = request.GET.get('category', '').strip()
        keyword = request.GET.get('keyword', '').strip()
        
        # 构建查询条件
        queryset = MarketNews.objects.all()
        
        if category:
            queryset = queryset.filter(category=category)
        
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) | 
                Q(content__icontains=keyword)
            )
        
        # 分页
        paginator = Paginator(queryset.order_by('-publish_time'), page_size)
        news_page = paginator.get_page(page)
        
        # 序列化数据
        news_list = []
        for news in news_page:
            news_list.append({
                'id': news.id,
                'title': news.title,
                'content': news.content[:200] + '...' if len(news.content) > 200 else news.content,
                'source': news.source,
                'category': news.category,
                'publish_time': news.publish_time.strftime('%Y-%m-%d %H:%M:%S'),
                'related_stocks': news.related_stocks if news.related_stocks else [],
                'summary': news.content[:100] + '...' if len(news.content) > 100 else news.content,
            })
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'list': news_list,
                'total': paginator.count,
                'page': page,
                'pageSize': page_size,
                'totalPages': paginator.num_pages,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取新闻列表失败: {str(e)}'
        })


@require_login
def market_news_detail(request, news_id):
    """获取新闻详情 - 所有用户可访问"""
    try:
        from trading.models import MarketNews
        
        try:
            news = MarketNews.objects.get(id=news_id)
        except MarketNews.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'msg': '新闻不存在'
            })
        
        news_detail = {
            'id': news.id,
            'title': news.title,
            'content': news.content,
            'source': news.source,
            'category': news.category,
            'publish_time': news.publish_time.strftime('%Y-%m-%d %H:%M:%S'),
            'related_stocks': news.related_stocks if news.related_stocks else [],
            'create_time': news.create_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': news_detail
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取新闻详情失败: {str(e)}'
        })


@require_login
def latest_market_news(request):
    """获取最新市场新闻 - 所有用户可访问"""
    try:
        from trading.models import MarketNews
        
        limit = int(request.GET.get('limit', 10))
        category = request.GET.get('category', '').strip()
        
        queryset = MarketNews.objects.all()
        if category:
            queryset = queryset.filter(category=category)
        
        latest_news = queryset.order_by('-publish_time')[:limit]
        
        news_list = []
        for news in latest_news:
            news_list.append({
                'id': news.id,
                'title': news.title,
                'source': news.source,
                'category': news.category,
                'publish_time': news.publish_time.strftime('%Y-%m-%d %H:%M:%S'),
                'summary': news.content[:100] + '...' if len(news.content) > 100 else news.content,
                'related_stocks': news.related_stocks if news.related_stocks else [],
            })
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': news_list
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取最新新闻失败: {str(e)}'
        })


@require_login
def news_categories(request):
    """获取新闻分类列表 - 所有用户可访问"""
    try:
        from trading.models import MarketNews
        
        categories = MarketNews.objects.values_list('category', flat=True).distinct().exclude(category__isnull=True).exclude(category='')
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': list(categories)
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取新闻分类失败: {str(e)}'
        })


@admin_required
@require_http_methods(["POST"])
@csrf_exempt
def create_market_news(request):
    """创建市场新闻 - 管理员可访问"""
    try:
        from trading.models import MarketNews
        
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        source = data.get('source', '系统').strip()
        category = data.get('category', '财经新闻').strip()
        related_stocks = data.get('related_stocks', [])
        
        if not title:
            return JsonResponse({
                'code': 400,
                'msg': '标题不能为空'
            })
        
        if not content:
            return JsonResponse({
                'code': 400,
                'msg': '内容不能为空'
            })
        
        news = MarketNews.objects.create(
            title=title,
            content=content,
            source=source,
            category=category,
            related_stocks=related_stocks,
            publish_time=datetime.now()
        )
        
        return JsonResponse({
            'code': 200,
            'msg': '新闻创建成功',
            'data': {
                'id': news.id,
                'title': news.title,
                'category': news.category,
                'source': news.source,
                'publish_time': news.publish_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'创建新闻失败: {str(e)}'
        })


@superadmin_required
@require_http_methods(["POST"])
@csrf_exempt  
def sync_news_manual(request):
    """手动同步新闻数据 - 超级管理员可访问"""
    try:
        from stock.tasks import sync_financial_news
        
        # 在后台异步执行同步任务
        import threading
        thread = threading.Thread(target=sync_financial_news)
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'code': 200,
            'msg': '新闻同步任务已启动，请稍后查看结果'
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'启动新闻同步失败: {str(e)}'
        })
