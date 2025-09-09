# -*- coding: utf-8 -*-

import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q

from stock.models import StockBasic, StockDaily, StockCompany, StockBasicSerializer, StockDailySerializer, StockCompanySerializer
from stock.services import StockDataService, TradingService, UserPermissionService
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
