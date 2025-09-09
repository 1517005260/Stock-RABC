# -*- coding: utf-8 -*-

import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q

from trading.models import (UserStockAccount, UserPosition, TradeRecord, UserWatchList, MarketNews,
                          UserStockAccountSerializer, UserPositionSerializer, TradeRecordSerializer, 
                          UserWatchListSerializer, MarketNewsSerializer)
from stock.services import TradingService, UserPermissionService
from stock.models import StockBasic, StockDaily
from utils.permissions import require_login, admin_required, data_permission_filter
from user.models import SysUser


@require_login
@csrf_exempt
@require_http_methods(["POST"])
def buy_stock(request):
    """买入股票 - 所有用户可访问"""
    try:
        # 获取当前用户
        user = SysUser.objects.get(id=request.user_id)
        
        # 解析请求数据
        data = json.loads(request.body)
        ts_code = data.get('ts_code')
        price = data.get('price')
        shares = data.get('shares')
        
        # 参数验证
        if not all([ts_code, price, shares]):
            return JsonResponse({
                'code': 400,
                'msg': '参数不完整，请提供股票代码、价格和数量'
            })
        
        try:
            price = float(price)
            shares = int(shares)
        except (ValueError, TypeError):
            return JsonResponse({
                'code': 400,
                'msg': '价格和数量格式错误'
            })
        
        if price <= 0 or shares <= 0:
            return JsonResponse({
                'code': 400,
                'msg': '价格和数量必须大于0'
            })
        
        # 调用交易服务
        result = TradingService.buy_stock(user, ts_code, price, shares)
        
        if result['success']:
            return JsonResponse({
                'code': 200,
                'msg': result['message'],
                'data': {
                    'remaining_balance': float(result['remaining_balance'])
                }
            })
        else:
            return JsonResponse({
                'code': 400,
                'msg': result['message']
            })
        
    except SysUser.DoesNotExist:
        return JsonResponse({
            'code': 404,
            'msg': '用户不存在'
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'买入失败: {str(e)}'
        })


@require_login
@csrf_exempt
@require_http_methods(["POST"])
def sell_stock(request):
    """卖出股票 - 所有用户可访问"""
    try:
        # 获取当前用户
        user = SysUser.objects.get(id=request.user_id)
        
        # 解析请求数据
        data = json.loads(request.body)
        ts_code = data.get('ts_code')
        price = data.get('price')
        shares = data.get('shares')
        
        # 参数验证
        if not all([ts_code, price, shares]):
            return JsonResponse({
                'code': 400,
                'msg': '参数不完整，请提供股票代码、价格和数量'
            })
        
        try:
            price = float(price)
            shares = int(shares)
        except (ValueError, TypeError):
            return JsonResponse({
                'code': 400,
                'msg': '价格和数量格式错误'
            })
        
        if price <= 0 or shares <= 0:
            return JsonResponse({
                'code': 400,
                'msg': '价格和数量必须大于0'
            })
        
        # 调用交易服务
        result = TradingService.sell_stock(user, ts_code, price, shares)
        
        if result['success']:
            return JsonResponse({
                'code': 200,
                'msg': result['message'],
                'data': {
                    'net_amount': float(result['net_amount']),
                    'remaining_balance': float(result['remaining_balance'])
                }
            })
        else:
            return JsonResponse({
                'code': 400,
                'msg': result['message']
            })
        
    except SysUser.DoesNotExist:
        return JsonResponse({
            'code': 404,
            'msg': '用户不存在'
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'卖出失败: {str(e)}'
        })


@require_login
def get_account_info(request):
    """获取账户信息 - 所有用户可访问"""
    try:
        user = SysUser.objects.get(id=request.user_id)
        account = TradingService.get_or_create_account(user)
        
        # 计算总市值
        positions = TradingService.get_user_positions(user)
        total_market_value = sum(pos['market_value'] for pos in positions)
        
        account_info = {
            'account_balance': float(account.account_balance),
            'frozen_balance': float(account.frozen_balance),
            'total_assets': float(account.total_assets),
            'total_profit': float(account.total_profit),
            'market_value': total_market_value,
            'total_value': float(account.account_balance) + total_market_value,
            'position_count': len(positions),
        }
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': account_info
        })
        
    except SysUser.DoesNotExist:
        return JsonResponse({
            'code': 404,
            'msg': '用户不存在'
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取账户信息失败: {str(e)}'
        })


@require_login
@data_permission_filter
def get_positions(request):
    """获取持仓信息 - 根据权限显示数据"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        
        # 根据数据权限过滤
        if request.data_scope == 'self':
            # 普通用户只能看自己的
            user = SysUser.objects.get(id=request.user_id)
            positions = TradingService.get_user_positions(user)
        elif request.data_scope == 'users':
            # 管理员可以看所有普通用户的
            user_id = request.GET.get('user_id')
            if user_id:
                user = SysUser.objects.get(id=user_id)
                positions = TradingService.get_user_positions(user)
            else:
                # 获取所有用户持仓（简化版本）
                all_positions = UserPosition.objects.all()[:100]  # 限制数量
                positions = []
                for pos in all_positions:
                    positions.append({
                        'user_id': pos.user.id,
                        'username': pos.user.username,
                        'ts_code': pos.ts_code,
                        'stock_name': pos.stock_name,
                        'position_shares': pos.position_shares,
                        'cost_price': float(pos.cost_price),
                        'current_price': float(pos.current_price),
                        'market_value': float(pos.current_price * pos.position_shares),
                    })
        else:
            # 超级管理员可以看所有数据
            user_id = request.GET.get('user_id')
            if user_id:
                user = SysUser.objects.get(id=user_id)
                positions = TradingService.get_user_positions(user)
            else:
                all_positions = UserPosition.objects.all()[:100]
                positions = []
                for pos in all_positions:
                    positions.append({
                        'user_id': pos.user.id,
                        'username': pos.user.username,
                        'ts_code': pos.ts_code,
                        'stock_name': pos.stock_name,
                        'position_shares': pos.position_shares,
                        'cost_price': float(pos.cost_price),
                        'current_price': float(pos.current_price),
                        'market_value': float(pos.current_price * pos.position_shares),
                    })
        
        # 简单分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_positions = positions[start:end]
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'list': paginated_positions,
                'total': len(positions),
                'page': page,
                'pageSize': page_size,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取持仓信息失败: {str(e)}'
        })


@require_login
@data_permission_filter
def get_trade_records(request):
    """获取交易记录 - 根据权限显示数据"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        
        # 根据数据权限过滤
        if request.data_scope == 'self':
            # 普通用户只能看自己的
            user = SysUser.objects.get(id=request.user_id)
            queryset = TradeRecord.objects.filter(user=user)
        elif request.data_scope == 'users':
            # 管理员可以看所有普通用户的
            user_id = request.GET.get('user_id')
            if user_id:
                queryset = TradeRecord.objects.filter(user_id=user_id)
            else:
                # 排除管理员的交易记录
                admin_users = UserPermissionService.get_admin_users()
                admin_ids = [user.id for user in admin_users]
                queryset = TradeRecord.objects.exclude(user_id__in=admin_ids)
        else:
            # 超级管理员可以看所有数据
            user_id = request.GET.get('user_id')
            if user_id:
                queryset = TradeRecord.objects.filter(user_id=user_id)
            else:
                queryset = TradeRecord.objects.all()
        
        # 分页
        paginator = Paginator(queryset.order_by('-trade_time'), page_size)
        trades = paginator.get_page(page)
        
        # 序列化数据
        trade_list = []
        for trade in trades:
            trade_data = {
                'id': trade.id,
                'user_id': trade.user.id,
                'username': trade.user.username,
                'ts_code': trade.ts_code,
                'stock_name': trade.stock_name,
                'trade_type': trade.trade_type,
                'trade_type_display': trade.get_trade_type_display(),
                'trade_price': float(trade.trade_price),
                'trade_shares': trade.trade_shares,
                'trade_amount': float(trade.trade_amount),
                'commission': float(trade.commission),
                'trade_time': trade.trade_time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': trade.status,
                'status_display': trade.get_status_display(),
                'remark': trade.remark,
            }
            trade_list.append(trade_data)
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'list': trade_list,
                'total': paginator.count,
                'page': page,
                'pageSize': page_size,
                'totalPages': paginator.num_pages,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取交易记录失败: {str(e)}'
        })


@require_login
@csrf_exempt
@require_http_methods(["POST"])
def add_to_watchlist(request):
    """添加自选股 - 所有用户可访问"""
    try:
        user = SysUser.objects.get(id=request.user_id)
        data = json.loads(request.body)
        ts_code = data.get('ts_code')
        
        if not ts_code:
            return JsonResponse({
                'code': 400,
                'msg': '请提供股票代码'
            })
        
        # 检查股票是否存在
        try:
            stock = StockBasic.objects.get(ts_code=ts_code)
        except StockBasic.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'msg': '股票不存在'
            })
        
        # 检查是否已添加
        if UserWatchList.objects.filter(user=user, ts_code=ts_code).exists():
            return JsonResponse({
                'code': 400,
                'msg': '该股票已在自选股中'
            })
        
        # 添加自选股
        UserWatchList.objects.create(
            user=user,
            ts_code=ts_code,
            stock_name=stock.name
        )
        
        return JsonResponse({
            'code': 200,
            'msg': '添加成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'添加自选股失败: {str(e)}'
        })


@require_login
def get_watchlist(request):
    """获取自选股列表 - 所有用户可访问"""
    try:
        user = SysUser.objects.get(id=request.user_id)
        watchlist = UserWatchList.objects.filter(user=user).order_by('-add_time')
        
        result = []
        for item in watchlist:
            # 获取最新行情
            latest_daily = StockDaily.objects.filter(ts_code=item.ts_code).order_by('-trade_date').first()
            
            watch_data = {
                'ts_code': item.ts_code,
                'stock_name': item.stock_name,
                'add_time': item.add_time.strftime('%Y-%m-%d %H:%M:%S'),
                'current_price': float(latest_daily.close) if latest_daily and latest_daily.close else None,
                'change': float(latest_daily.change) if latest_daily and latest_daily.change else None,
                'pct_chg': float(latest_daily.pct_chg) if latest_daily and latest_daily.pct_chg else None,
            }
            result.append(watch_data)
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': result
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取自选股失败: {str(e)}'
        })


@require_login
@csrf_exempt
@require_http_methods(["DELETE"])
def remove_from_watchlist(request, ts_code):
    """移除自选股 - 所有用户可访问"""
    try:
        user = SysUser.objects.get(id=request.user_id)
        
        try:
            watch_item = UserWatchList.objects.get(user=user, ts_code=ts_code)
            watch_item.delete()
            
            return JsonResponse({
                'code': 200,
                'msg': '移除成功'
            })
        except UserWatchList.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'msg': '该股票不在自选股中'
            })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'移除自选股失败: {str(e)}'
        })
