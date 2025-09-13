# -*- coding: utf-8 -*-

import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q

from stock.models import StockBasic, StockDaily, StockCompany, StockBasicSerializer, StockDailySerializer, StockCompanySerializer
from stock.services import StockDataService, UserPermissionService, RealTimeDataService, IntradayDataService
from trading.services import TradingService
from stock.tushare_service import EnterpriseFinanceDataService
enterprise_finance_service = EnterpriseFinanceDataService()
from utils.permissions import require_role, require_login, admin_required, superadmin_required
from user.models import SysUser

# 导入Tushare
import os
import tushare as ts
from dotenv import load_dotenv

# 加载环境变量并初始化Tushare
load_dotenv()
token = os.getenv('TUSHARE_TOKEN')
if token:
    ts.set_token(token)
    pro = ts.pro_api()
else:
    pro = None


@require_login
def stock_list(request):
    """股票列表 - 所有用户可访问，自动同步真实数据"""
    try:
        from stock.services import StockDataService
        
        # 检查是否有股票数据，如果没有则自动同步
        if not StockBasic.objects.exists():
            sync_result = StockDataService.sync_stock_basic()
            if not sync_result['success']:
                return JsonResponse({
                    'code': 500,
                    'msg': f'同步股票基本信息失败: {sync_result["message"]}'
                })
        
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
    """股票详情 - 点击时自动获取最新数据，参考sample项目策略"""
    try:
        # 获取股票基本信息，如果不存在则尝试同步
        try:
            stock = StockBasic.objects.get(ts_code=ts_code)
        except StockBasic.DoesNotExist:
            # 股票不存在，尝试同步股票基本信息
            sync_result = StockDataService.sync_stock_basic()
            if sync_result['success']:
                try:
                    stock = StockBasic.objects.get(ts_code=ts_code)
                except StockBasic.DoesNotExist:
                    return JsonResponse({
                        'code': 404,
                        'msg': f'股票代码 {ts_code} 不存在'
                    })
            else:
                return JsonResponse({
                    'code': 404,
                    'msg': '股票不存在且同步失败'
                })

        # 参考sample项目：点击时自动获取/更新最新数据
        try:
            # 检查是否有日线数据，没有则同步
            latest_daily = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date').first()

            # 如果没有数据或数据过旧（超过3天），则同步最新数据
            should_sync = False
            if not latest_daily:
                should_sync = True
                print(f"股票 {ts_code} 无历史数据，开始同步...")
            else:
                from datetime import datetime, timedelta
                # 检查数据是否过旧
                days_old = (datetime.now().date() - latest_daily.trade_date).days
                if days_old > 3:
                    should_sync = True
                    print(f"股票 {ts_code} 数据过旧({days_old}天)，开始更新...")

            # 同步最新数据
            if should_sync:
                sync_result = StockDataService.sync_stock_daily(ts_code, days=90)  # 同步3个月数据
                if sync_result['success']:
                    print(f"成功同步 {ts_code} 的 {sync_result['count']} 条数据")
                    latest_daily = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date').first()
                else:
                    print(f"同步 {ts_code} 数据失败: {sync_result['message']}")

        except Exception as sync_error:
            print(f"数据同步过程出错: {sync_error}")

        # 获取历史行情数据（最近250天，足够画K线图）
        history_data = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date')[:250]
        history_list = []
        for daily in reversed(history_data):  # 按时间正序，符合前端K线图需求
            history_list.append({
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

        # 尝试获取公司信息（如果没有则尝试同步）
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
            # 尝试同步公司信息（不影响主流程）
            try:
                sync_result = StockDataService.sync_company_info([ts_code])
                if sync_result['success']:
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
            except:
                pass  # 公司信息获取失败不影响主要功能

        # 构建返回数据
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
            'current_price': float(latest_daily.close) if latest_daily and latest_daily.close else 0,
            'open_price': float(latest_daily.open) if latest_daily and latest_daily.open else 0,
            'high_price': float(latest_daily.high) if latest_daily and latest_daily.high else 0,
            'low_price': float(latest_daily.low) if latest_daily and latest_daily.low else 0,
            'pre_close': float(latest_daily.pre_close) if latest_daily and latest_daily.pre_close else 0,
            'change': float(latest_daily.change) if latest_daily and latest_daily.change else 0,
            'pct_chg': float(latest_daily.pct_chg) if latest_daily and latest_daily.pct_chg else 0,
            'volume': latest_daily.vol if latest_daily else 0,
            'amount': float(latest_daily.amount) if latest_daily and latest_daily.amount else 0,
            'trade_date': latest_daily.trade_date.strftime('%Y-%m-%d') if latest_daily else None,
            'history_data': history_list,
            'company_info': company_info,
            'data_count': len(history_list),  # 返回数据条数
            'last_update': datetime.now().isoformat()  # 最后更新时间
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
    """热门牛股/涨幅榜 - 动态显示涨幅最大的前N只股票"""
    try:
        limit = int(request.GET.get('limit', 10))  # 默认10只，支持用户自定义
        limit = min(limit, 50)  # 最大50只，防止性能问题

        print(f"获取涨幅榜前{limit}只股票")

        # 参考sample项目策略：优先从TuShare API实时获取涨幅榜
        use_realtime_api = True
        hot_stocks = []

        if use_realtime_api and pro:
            try:
                print("尝试从TuShare API获取实时涨幅榜...")

                # 使用sample项目中的get_top_gainers方法
                from stock.tushare_service import enterprise_finance_service

                gainers = enterprise_finance_service.get_top_gainers(limit * 2)  # 获取2倍数量，筛选后返回

                if gainers and len(gainers) > 0:
                    print(f"从TuShare API获取到 {len(gainers)} 只涨幅股票")

                    # 转换为标准格式
                    for gainer in gainers:
                        try:
                            # 获取股票基本信息
                            try:
                                stock_basic = StockBasic.objects.get(ts_code=gainer['ts_code'])
                                stock_name = stock_basic.name
                                industry = stock_basic.industry if stock_basic.industry else '未分类'
                            except StockBasic.DoesNotExist:
                                stock_name = gainer.get('ts_code', '未知')
                                industry = '未分类'

                            hot_stocks.append({
                                'ts_code': gainer['ts_code'],
                                'name': stock_name,
                                'close': float(gainer['close']) if gainer.get('close') else 0,
                                'open': float(gainer['open']) if gainer.get('open') else 0,
                                'high': float(gainer['high']) if gainer.get('high') else 0,
                                'low': float(gainer['low']) if gainer.get('low') else 0,
                                'change': float(gainer['change']) if gainer.get('change') else 0,
                                'pct_chg': float(gainer['pct_chg']) if gainer.get('pct_chg') else 0,
                                'vol': int(gainer['vol']) if gainer.get('vol') else 0,
                                'amount': float(gainer['amount']) if gainer.get('amount') else 0,
                                'trade_date': gainer.get('trade_date', datetime.now().strftime('%Y%m%d')),
                                'industry': industry,
                                'data_source': 'tushare_api_realtime'
                            })

                            # 已经获得足够数量就停止
                            if len(hot_stocks) >= limit:
                                break

                        except Exception as item_error:
                            print(f"处理涨幅股票数据失败: {item_error}")
                            continue

                    # 确保按涨跌幅排序
                    hot_stocks.sort(key=lambda x: x['pct_chg'], reverse=True)
                    hot_stocks = hot_stocks[:limit]

                else:
                    print("TuShare API返回空涨幅榜，回退到本地数据")
                    use_realtime_api = False

            except Exception as api_error:
                print(f"TuShare API获取涨幅榜失败: {api_error}，回退到本地数据")
                use_realtime_api = False

        # 如果实时API失败，回退到本地数据
        if not use_realtime_api or not hot_stocks:
            print("从本地数据库获取涨幅榜...")

            try:
                hot_stocks = StockDataService.get_top_stocks(limit)

                # 添加数据源标识
                for stock in hot_stocks:
                    stock['data_source'] = 'local_database'

                print(f"从本地数据库获取到 {len(hot_stocks)} 只热门股票")

            except Exception as local_error:
                print(f"本地数据获取也失败: {local_error}")

                # 最后的回退：使用固定的热门股票列表
                fallback_stocks = ['000001.SZ', '000002.SZ', '000858.SZ', '600000.SH', '600036.SH',
                                 '600519.SH', '002594.SZ', '300750.SZ', '002415.SZ', '000776.SZ']

                hot_stocks = []
                for ts_code in fallback_stocks[:limit]:
                    try:
                        stock = StockBasic.objects.get(ts_code=ts_code)
                        latest_daily = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date').first()

                        if latest_daily:
                            hot_stocks.append({
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

        # 如果还是没有数据，返回错误
        if not hot_stocks:
            return JsonResponse({
                'code': 404,
                'msg': '暂时无法获取涨幅榜数据，请稍后重试'
            })

        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'list': hot_stocks,
                'count': len(hot_stocks),
                'limit': limit,
                'data_source': hot_stocks[0].get('data_source', 'unknown') if hot_stocks else 'unknown',
                'last_update': datetime.now().isoformat()
            }
        })

    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取涨幅榜失败: {str(e)}'
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
    """获取股票分时图数据 - 使用多数据源策略，只返回真实数据"""
    try:
        result = IntradayDataService.get_stock_intraday_multi_source(ts_code)
        
        if result['success']:
            return JsonResponse({
                'code': 200,
                'msg': f'获取成功 (数据源: {result.get("source", "unknown")})',
                'data': result['data']
            })
        else:
            return JsonResponse({
                'code': 404,
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
    """获取K线图数据 - 参考sample项目，实时获取最新数据，确保ECharts兼容性"""
    try:
        from datetime import datetime, timedelta
        from chinese_calendar import is_workday, is_holiday

        # 获取参数
        period = request.GET.get('period', 'daily')  # 周期：daily, weekly, monthly
        limit = int(request.GET.get('limit', 100))    # 数据条数
        adjust = request.GET.get('adjust', 'qfq')     # 复权类型：qfq前复权, hfq后复权, none不复权

        # 限制数据条数
        limit = min(limit, 500)  # 增加到500条，更适合K线图展示

        print(f"获取K线数据: {ts_code}, 周期: {period}, 条数: {limit}")

        # 安全数值转换函数
        def safe_float(value, default=0.0):
            try:
                if value is None or value == '':
                    return default
                return float(value)
            except (ValueError, TypeError):
                return default

        def safe_int(value, default=0):
            try:
                if value is None or value == '':
                    return default
                return int(float(value))
            except (ValueError, TypeError):
                return default

        # 检查是否为指数代码（上证指数、深证指数等）
        is_index = ts_code in ['000001.SH', '399001.SZ', '399006.SZ', '000300.SH', '000905.SH']

        if is_index:
            # 指数数据直接从Tushare获取 - 参考sample项目做法
            if not pro:
                return JsonResponse({
                    'code': 500,
                    'msg': 'Tushare API未配置，无法获取指数数据'
                })

            # 参考sample项目：直接从API获取最新数据
            try:
                # 计算日期范围 - 确保获取足够的数据
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=limit * 3)).strftime('%Y%m%d')

                print(f"获取指数数据: {ts_code}, 日期范围: {start_date} - {end_date}")

                # 获取指数日线数据
                df = pro.index_daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
                )

                if df.empty:
                    return JsonResponse({
                        'code': 404,
                        'msg': f'无法获取指数 {ts_code} 的K线数据'
                    })

                # 转换为前端需要的格式 - 使用安全转换
                kline_data = []
                for _, row in df.iterrows():
                    try:
                        kline_data.append({
                            'date': datetime.strptime(str(row['trade_date']), '%Y%m%d').strftime('%Y-%m-%d'),
                            'open': safe_float(row['open']),
                            'high': safe_float(row['high']),
                            'low': safe_float(row['low']),
                            'close': safe_float(row['close']),
                            'volume': safe_int(row['vol']),
                            'amount': safe_float(row['amount']),
                            'change': safe_float(row['change']),
                            'pct_chg': safe_float(row['pct_chg']),
                            'pre_close': safe_float(row['pre_close'])
                        })
                    except (ValueError, TypeError) as e:
                        continue

                # 按日期正序排列，符合K线图要求
                kline_data.sort(key=lambda x: x['date'])

                # 限制返回数量
                result_data = kline_data[-limit:] if limit and len(kline_data) > limit else kline_data

                # 获取指数名称
                index_names = {
                    '000001.SH': '上证指数',
                    '399001.SZ': '深证成指',
                    '399006.SZ': '创业板指',
                    '000300.SH': '沪深300',
                    '000905.SH': '中证500'
                }
                stock_name = index_names.get(ts_code, ts_code)

                # 创建ECharts安全格式
                echarts_data = {
                    'dates': [item['date'] for item in result_data],
                    'values': [[
                        item['open'],
                        item['close'],
                        item['low'],
                        item['high']
                    ] for item in result_data],
                    'volumes': [item['volume'] for item in result_data]
                }

                chart_data = [[
                    item['date'],
                    item['open'],
                    item['close'],
                    item['low'],
                    item['high'],
                    item['volume']
                ] for item in result_data]

                return JsonResponse({
                    'code': 200,
                    'msg': '获取成功',
                    'data': {
                        'ts_code': ts_code,
                        'name': stock_name,
                        'period': period,
                        'adjust': adjust,
                        'count': len(result_data),
                        'kline_data': result_data,
                        'latest_info': result_data[-1] if result_data else None,
                        'data_source': 'tushare_index_realtime',
                        'last_update': datetime.now().isoformat(),
                        # ECharts专用格式 - 确保数据安全
                        'echarts_data': echarts_data,
                        # 二维数组格式（ECharts标准格式）
                        'chart_data': chart_data
                    }
                })

            except Exception as e:
                return JsonResponse({
                    'code': 500,
                    'msg': f'获取指数数据失败: {str(e)}'
                })
        else:
            # 股票数据 - 参考sample项目策略：优先使用实时API，回退到本地数据
            stock_name = ts_code
            kline_data = []

            # 获取股票基本信息
            try:
                stock = StockBasic.objects.get(ts_code=ts_code)
                stock_name = stock.name
            except StockBasic.DoesNotExist:
                # 股票不存在，尝试同步
                sync_result = StockDataService.sync_stock_basic()
                if sync_result['success']:
                    try:
                        stock = StockBasic.objects.get(ts_code=ts_code)
                        stock_name = stock.name
                    except StockBasic.DoesNotExist:
                        return JsonResponse({
                            'code': 404,
                            'msg': f'股票代码 {ts_code} 不存在'
                        })
                else:
                    return JsonResponse({
                        'code': 500,
                        'msg': f'股票不存在且同步失败: {sync_result["message"]}'
                    })

            # 参考sample项目：优先从TuShare API实时获取数据
            use_realtime_api = True
            if use_realtime_api and pro:
                try:
                    print(f"尝试从TuShare API实时获取股票数据: {ts_code}")

                    # 计算获取的日期范围
                    end_date = datetime.now().strftime('%Y%m%d')
                    start_date = (datetime.now() - timedelta(days=max(limit * 2, 365))).strftime('%Y%m%d')  # 至少获取1年数据

                    # 直接从TuShare获取最新数据
                    df = pro.daily(
                        ts_code=ts_code,
                        start_date=start_date,
                        end_date=end_date,
                        fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
                    )

                    if not df.empty:
                        print(f"从TuShare API获取到 {len(df)} 条实时数据")

                        # 转换为标准格式 - 使用安全转换
                        for _, row in df.iterrows():
                            try:
                                kline_data.append({
                                    'date': datetime.strptime(str(row['trade_date']), '%Y%m%d').strftime('%Y-%m-%d'),
                                    'open': safe_float(row['open']),
                                    'high': safe_float(row['high']),
                                    'low': safe_float(row['low']),
                                    'close': safe_float(row['close']),
                                    'volume': safe_int(row['vol']),
                                    'amount': safe_float(row['amount']),
                                    'change': safe_float(row['change']),
                                    'pct_chg': safe_float(row['pct_chg']),
                                    'pre_close': safe_float(row['pre_close'])
                                })
                            except (ValueError, TypeError):
                                continue

                        # 按日期正序排列
                        kline_data.sort(key=lambda x: x['date'])

                        # 限制数量
                        if len(kline_data) > limit:
                            kline_data = kline_data[-limit:]

                        # 异步更新本地数据库（不影响返回速度）
                        try:
                            # 只更新最近30天的数据到本地数据库
                            recent_data = kline_data[-30:] if len(kline_data) > 30 else kline_data
                            for data_point in recent_data:
                                try:
                                    trade_date = datetime.strptime(data_point['date'], '%Y-%m-%d').date()
                                    daily_data = {
                                        'ts_code': ts_code,
                                        'trade_date': trade_date,
                                        'open': data_point['open'],
                                        'high': data_point['high'],
                                        'low': data_point['low'],
                                        'close': data_point['close'],
                                        'pre_close': data_point['pre_close'],
                                        'change': data_point['change'],
                                        'pct_chg': data_point['pct_chg'],
                                        'vol': data_point['volume'],
                                        'amount': data_point['amount']
                                    }
                                    StockDaily.objects.update_or_create(
                                        ts_code=ts_code,
                                        trade_date=trade_date,
                                        defaults=daily_data
                                    )
                                except:
                                    continue
                            print(f"已更新 {ts_code} 最近30天数据到本地数据库")
                        except Exception as update_error:
                            print(f"更新本地数据库失败: {update_error}")

                        data_source = 'tushare_api_realtime'

                    else:
                        print(f"TuShare API返回空数据，回退到本地数据库")
                        use_realtime_api = False

                except Exception as api_error:
                    print(f"TuShare API调用失败: {api_error}，回退到本地数据库")
                    use_realtime_api = False

            # 如果实时API失败，回退到本地数据库
            if not use_realtime_api or not kline_data:
                print(f"从本地数据库获取K线数据: {ts_code}")

                # 检查本地是否有数据，没有则同步
                daily_data = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date')
                if not daily_data.exists():
                    print(f"本地无数据，开始同步 {ts_code}")
                    sync_result = StockDataService.sync_stock_daily(ts_code, days=max(limit * 2, 180))
                    if sync_result['success']:
                        daily_data = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date')
                        print(f"同步成功，获得 {daily_data.count()} 条数据")
                    else:
                        return JsonResponse({
                            'code': 500,
                            'msg': f'本地无数据且同步失败: {sync_result["message"]}'
                        })

                # 从数据库获取K线数据 - 使用安全转换
                if period == 'daily':
                    daily_data = daily_data[:limit]
                    kline_data = []

                    for daily in reversed(daily_data):  # 按时间正序
                        kline_data.append({
                            'date': daily.trade_date.strftime('%Y-%m-%d'),
                            'open': safe_float(daily.open),
                            'high': safe_float(daily.high),
                            'low': safe_float(daily.low),
                            'close': safe_float(daily.close),
                            'volume': safe_int(daily.vol),
                            'amount': safe_float(daily.amount),
                            'change': safe_float(daily.change),
                            'pct_chg': safe_float(daily.pct_chg),
                            'pre_close': safe_float(daily.pre_close)
                        })

                elif period == 'weekly':
                    # 周K线数据（基于日K线聚合）
                    kline_data = generate_weekly_kline(ts_code, limit)

                elif period == 'monthly':
                    # 月K线数据（基于日K线聚合）
                    kline_data = generate_monthly_kline(ts_code, limit)

                data_source = 'local_database'

        # 检查是否有数据
        if not kline_data:
            return JsonResponse({
                'code': 404,
                'msg': f'未找到 {ts_code} 的K线数据'
            })

        # 数据验证 - 确保价格逻辑正确
        validated_data = []
        for item in kline_data:
            # 基本数据完整性检查
            if (item['open'] >= 0 and item['high'] >= 0 and
                item['low'] >= 0 and item['close'] >= 0 and
                item['high'] >= item['low']):
                validated_data.append(item)

        if not validated_data:
            return JsonResponse({
                'code': 404,
                'msg': f'{ts_code} 的K线数据验证失败，无有效数据'
            })

        kline_data = validated_data

        # 计算技术指标（可选）
        technical_indicators = {}
        if len(kline_data) >= 20:  # 需要足够数据才计算技术指标
            try:
                technical_indicators = calculate_technical_indicators(kline_data)
            except Exception as tech_error:
                print(f"计算技术指标失败: {tech_error}")
                technical_indicators = {}

        # 创建ECharts安全格式
        echarts_data = {
            'dates': [item['date'] for item in kline_data],
            'values': [[
                item['open'],
                item['close'],
                item['low'],
                item['high']
            ] for item in kline_data],
            'volumes': [item['volume'] for item in kline_data]
        }

        chart_data = [[
            item['date'],
            item['open'],
            item['close'],
            item['low'],
            item['high'],
            item['volume']
        ] for item in kline_data]

        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'ts_code': ts_code,
                'name': stock_name,
                'period': period,
                'adjust': adjust,
                'count': len(kline_data),
                'kline_data': kline_data,
                'technical_indicators': technical_indicators,
                'latest_info': kline_data[-1] if kline_data else None,
                'data_source': data_source if 'data_source' in locals() else 'unknown',
                'last_update': datetime.now().isoformat(),
                # ECharts专用格式 - 确保数据安全
                'echarts_data': echarts_data,
                # 二维数组格式（ECharts标准格式）
                'chart_data': chart_data
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
        daily_data = StockDaily.objects.filter(ts_code=ts_code).order_by('-trade_date')[:500]
        
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


@require_login
def get_kline_data(request, ts_code):
    """
    获取K线数据
    支持日线、周线、月线数据
    """
    try:
        period = request.GET.get('period', 'daily')  # daily, weekly, monthly
        start_date = request.GET.get('start_date', '20200101')
        end_date = request.GET.get('end_date', None)
        
        # 获取日线数据
        daily_data = enterprise_finance_service.get_daily_data(ts_code, start_date, end_date)
        
        if not daily_data:
            return JsonResponse({
                'code': 404,
                'msg': '暂无K线数据'
            })
        
        # 转换为前端ECharts所需的格式
        # 数据格式：[date, open, close, low, high]
        kline_data = []
        for item in reversed(daily_data):  # 按时间正序
            if len(item) >= 5:
                date_str = item[0]
                open_price = float(item[1])
                high_price = float(item[2])
                low_price = float(item[3])
                close_price = float(item[4])
                
                # ECharts K线图数据格式：[open, close, low, high]
                kline_data.append([open_price, close_price, low_price, high_price])
        
        # 计算移动平均线
        def calculate_ma(data, days):
            ma_data = []
            for i in range(len(data)):
                if i < days - 1:
                    ma_data.append(None)
                else:
                    avg = sum([data[j][1] for j in range(i - days + 1, i + 1)]) / days  # 使用收盘价
                    ma_data.append(round(avg, 2))
            return ma_data
        
        ma5 = calculate_ma(kline_data, 5)
        ma10 = calculate_ma(kline_data, 10)
        ma20 = calculate_ma(kline_data, 20)
        ma30 = calculate_ma(kline_data, 30)
        
        # 日期数据
        dates = [item[0] for item in reversed(daily_data)]
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'dates': dates,
                'kline': kline_data,
                'ma5': ma5,
                'ma10': ma10,
                'ma20': ma20,
                'ma30': ma30
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取K线数据失败: {str(e)}'
        })


@require_login
def get_realtime_data(request, ts_code):
    """
    获取股票实时数据
    """
    try:
        realtime_data = enterprise_finance_service.get_realtime_data(ts_code)
        
        if not realtime_data:
            return JsonResponse({
                'code': 404,
                'msg': '暂无实时数据'
            })
        
        # 计算涨跌额和涨跌幅
        current_price = realtime_data['price']
        pre_close = realtime_data['pre_close']
        change = current_price - pre_close
        pct_change = (change / pre_close) * 100 if pre_close > 0 else 0
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'ts_code': ts_code,
                'current_price': current_price,
                'open': realtime_data['open'],
                'high': realtime_data['high'],
                'low': realtime_data['low'],
                'pre_close': pre_close,
                'change': round(change, 2),
                'pct_change': round(pct_change, 2),
                'volume': realtime_data['volume'],
                'amount': realtime_data['amount'],
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取实时数据失败: {str(e)}'
        })


@require_login
def get_intraday_chart(request, ts_code):
    """
    获取分时图数据 - 使用多数据源策略，只返回真实数据
    """
    try:
        result = IntradayDataService.get_stock_intraday_multi_source(ts_code)
        
        if result['success']:
            return JsonResponse({
                'code': 200,
                'msg': f'获取成功 (数据源: {result.get("source", "unknown")})',
                'data': result['data']
            })
        else:
            return JsonResponse({
                'code': 404,
                'msg': result['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取分时数据失败: {str(e)}'
        })


@require_login
def get_stock_holders(request, ts_code):
    """
    获取股票持股信息
    """
    try:
        holders_data = enterprise_finance_service.get_stock_holders(ts_code)
        
        if not holders_data:
            return JsonResponse({
                'code': 404,
                'msg': '暂无持股数据'
            })
        
        # 转换为饼图数据格式
        pie_data = []
        total_hold = sum([item[1] for item in holders_data])
        
        for holder_name, hold_vol in holders_data:
            percentage = (hold_vol / total_hold) * 100 if total_hold > 0 else 0
            pie_data.append({
                'name': holder_name,
                'value': hold_vol,
                'percentage': round(percentage, 2)
            })
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': pie_data
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取持股数据失败: {str(e)}'
        })


@require_login
def get_hot_stocks(request):
    """
    获取热门股票 - 真正的每日涨幅榜
    """
    try:
        limit = int(request.GET.get('limit', 10))
        
        # 尝试从数据库获取最新交易日数据
        latest_date = StockDaily.objects.values('trade_date').order_by('-trade_date').first()
        
        if not latest_date:
            # 如果数据库中没有数据，尝试从Tushare获取今日数据
            try:
                if not pro:  # 如果没有配置Tushare
                    return JsonResponse({
                        'code': 500,
                        'msg': 'Tushare API未配置，请联系管理员配置TUSHARE_TOKEN'
                    })
                
                # 获取今日股票数据
                today = datetime.now().strftime('%Y%m%d')
                df = pro.daily(
                    trade_date=today,
                    fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
                )
                
                if df.empty:
                    # 尝试前一交易日
                    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
                    df = pro.daily(
                        trade_date=yesterday,
                        fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
                    )
                
                if df.empty:
                    return JsonResponse({
                        'code': 404,
                        'msg': '暂无最新交易数据'
                    })
                
                # 筛选涨幅榜 - 真正的每日涨幅最大股票
                filtered_df = df[
                    (df['pct_chg'].notna()) & 
                    (df['pct_chg'] > 0) &  # 只要上涨的
                    (df['vol'] > 0) &  # 有成交量
                    (~df['ts_code'].str.contains('ST', na=False))  # 排除ST股票
                ].sort_values('pct_chg', ascending=False).head(limit)
                
                if filtered_df.empty:
                    # 如果没有上涨股票，返回涨跌幅最大的
                    filtered_df = df[
                        (df['pct_chg'].notna()) & 
                        (df['vol'] > 0)
                    ].sort_values('pct_chg', ascending=False).head(limit)
                
                # 获取股票名称
                ts_codes = ','.join(filtered_df['ts_code'].tolist())
                stock_basic = pro.stock_basic(
                    ts_code=ts_codes,
                    fields='ts_code,name,industry'
                )
                
                # 构建返回数据
                hot_stocks = []
                for _, row in filtered_df.iterrows():
                    basic_info = stock_basic[stock_basic['ts_code'] == row['ts_code']]
                    if not basic_info.empty:
                        basic = basic_info.iloc[0]
                        hot_stocks.append({
                            'ts_code': row['ts_code'],
                            'name': basic['name'],
                            'industry': basic['industry'] if basic['industry'] else '未分类',
                            'close': float(row['close']),
                            'change': float(row['change']),
                            'pct_chg': float(row['pct_chg']),
                            'vol': int(row['vol']),
                            'amount': float(row['amount']),
                            'trade_date': datetime.strptime(str(row['trade_date']), '%Y%m%d').strftime('%Y-%m-%d')
                        })
                
                return JsonResponse({
                    'code': 200,
                    'msg': '获取成功',
                    'data': hot_stocks
                })
                
            except Exception as api_error:
                return JsonResponse({
                    'code': 500,
                    'msg': f'获取实时热门股票失败: {str(api_error)}'
                })
        
        # 使用数据库数据获取热门股票
        try:
            hot_stocks = StockDataService.get_top_stocks(limit)
            
            return JsonResponse({
                'code': 200,
                'msg': '获取成功',
                'data': hot_stocks
            })
        except Exception as service_error:
            return JsonResponse({
                'code': 500,
                'msg': f'获取数据库热门股票失败: {str(service_error)}'
            })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取热门股票失败: {str(e)}'
        })


@require_login
def get_market_overview(request):
    """
    获取市场概览数据
    """
    try:
        # 获取主要指数数据
        indices = ['000001.SH', '399001.SZ', '399006.SZ']  # 上证指数、深证成指、创业板指
        index_data = []
        
        for index_code in indices:
            realtime = enterprise_finance_service.get_realtime_data(index_code)
            if realtime:
                change = realtime['price'] - realtime['pre_close']
                pct_change = (change / realtime['pre_close']) * 100 if realtime['pre_close'] > 0 else 0
                
                index_name = {
                    '000001.SH': '上证指数',
                    '399001.SZ': '深证成指', 
                    '399006.SZ': '创业板指'
                }.get(index_code, index_code)
                
                index_data.append({
                    'code': index_code,
                    'name': index_name,
                    'current': realtime['price'],
                    'change': round(change, 2),
                    'pct_change': round(pct_change, 2)
                })
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'indices': index_data,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取市场概览失败: {str(e)}'
        })
