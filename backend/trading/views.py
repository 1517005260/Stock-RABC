# -*- coding: utf-8 -*-

import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from trading.models import (UserStockAccount, UserPosition, TradeRecord, UserWatchList, MarketNews, AdminOperationLog,
                          UserStockAccountSerializer, UserPositionSerializer, TradeRecordSerializer, 
                          UserWatchListSerializer, MarketNewsSerializer)
from trading.services import TradingService, AdminService, WatchListService
from stock.services import UserPermissionService
from stock.models import StockBasic, StockDaily
from utils.permissions import require_login, admin_required, data_permission_filter
from user.models import SysUser
from datetime import datetime
import time


def _is_trading_time():
    """检查是否为交易时间"""
    from datetime import datetime, time as dt_time

    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()

    # 周末不交易 (5=Saturday, 6=Sunday)
    if weekday >= 5:
        return False

    # 交易时间：9:30-11:30, 13:00-15:00
    morning_start = dt_time(9, 30)
    morning_end = dt_time(11, 30)
    afternoon_start = dt_time(13, 0)
    afternoon_end = dt_time(15, 0)

    return (morning_start <= current_time <= morning_end) or \
           (afternoon_start <= current_time <= afternoon_end)


@require_login
@csrf_exempt
@require_http_methods(["POST"])
def buy_stock(request):
    """
    买入股票
    支持AJAX请求，返回JSON响应
    """
    try:
        # 交易时间检查
        if not _is_trading_time():
            return JsonResponse({
                'flag': 0,
                'money': 1,
                'msg': '当前非交易时间！交易时间：工作日 9:30-11:30, 13:00-15:00'
            })

        # 获取当前用户
        user = SysUser.objects.get(id=request.user_id)
        
        # 解析请求数据 - 支持AJAX GET和POST
        if request.method == 'GET':
            price = float(request.GET.get("price"))
            shares = int(request.GET.get("shares"))
            ts_code = request.GET.get("ts_code")
        else:
            data = json.loads(request.body)
            price = float(data.get('price'))
            shares = int(data.get('shares'))
            ts_code = data.get('ts_code')
        
        # 参数验证
        if not all([ts_code, price, shares]):
            return JsonResponse({
                'code': 400,
                'msg': '参数不完整，请提供股票代码、价格和数量'
            })
        
        if price <= 0 or shares <= 0:
            return JsonResponse({
                'code': 400,
                'msg': '价格和数量必须大于0'
            })
        
        # 计算交易金额
        trade_amount = price * shares
        
        # 获取或创建用户股票账户
        account, created = UserStockAccount.objects.get_or_create(
            user=user,
            defaults={
                'account_balance': Decimal('100000.00'),  # 默认10万初始资金
                'frozen_balance': Decimal('0.00'),
                'total_assets': Decimal('100000.00'),
                'total_profit': Decimal('0.00')
            }
        )
        
        # 获取股票信息
        try:
            stock = StockBasic.objects.get(ts_code=ts_code)
        except StockBasic.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'msg': '股票不存在'
            })
        
        # 检查资金是否充足和账户状态
        if (account.account_balance >= Decimal(str(trade_amount)) and 
            not getattr(user, 'freeze', False) and 
            getattr(user, 'account_opened', True)):
            
            # 资金充足，执行买入
            # 扣除资金
            account.account_balance -= Decimal(str(trade_amount))
            account.save()
            
            # 更新持仓
            position, created = UserPosition.objects.get_or_create(
                user=user,
                ts_code=ts_code,
                defaults={
                    'stock_name': stock.name,
                    'position_shares': 0,
                    'available_shares': 0,
                    'cost_price': Decimal(str(price)),
                    'current_price': Decimal(str(price))
                }
            )
            
            if not created:
                # 计算新的成本价（加权平均）
                total_cost = (position.position_shares * position.cost_price + 
                             shares * Decimal(str(price)))
                total_shares = position.position_shares + shares
                position.cost_price = total_cost / total_shares
            
            position.position_shares += shares
            position.available_shares += shares
            position.current_price = Decimal(str(price))
            position.save()
            
            # 记录交易历史
            TradeRecord.objects.create(
                user=user,
                ts_code=ts_code,
                stock_name=stock.name,
                trade_type='BUY',
                trade_price=Decimal(str(price)),
                trade_shares=shares,
                trade_amount=Decimal(str(trade_amount)),
                commission=Decimal('5.00'),  # 固定手续费
                status='COMPLETED',  # 直接成交，无委托状态
                trade_time=timezone.now()  # 使用Django的timezone来确保时区正确
            )
            
            return JsonResponse({
                "flag": 1,
                "money": 1,  # 资金充足标识
                "msg": "买入成功",
                "remaining_balance": float(account.account_balance)
            })
        else:
            # 资金不足或账户问题
            money_flag = 1 if account.account_balance >= Decimal(str(trade_amount)) else 0
            
            return JsonResponse({
                "flag": 0,
                "money": money_flag,
                "msg": "买入失败：资金不足或账户被冻结" if money_flag else "买入失败：资金不足"
            })
        
    except (ValueError, TypeError) as e:
        return JsonResponse({
            'code': 400,
            'msg': f'参数格式错误: {str(e)}'
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
        # 交易时间检查
        if not _is_trading_time():
            return JsonResponse({
                'flag': 0,
                'money': 1,
                'msg': '当前非交易时间！交易时间：工作日 9:30-11:30, 13:00-15:00'
            })

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
                'flag': 0,
                'money': 0,
                'msg': '参数不完整，请提供股票代码、价格和数量'
            })

        try:
            price = float(price)
            shares = int(shares)
        except (ValueError, TypeError):
            return JsonResponse({
                'flag': 0,
                'money': 0,
                'msg': '价格和数量格式错误'
            })

        if price <= 0 or shares <= 0:
            return JsonResponse({
                'flag': 0,
                'money': 0,
                'msg': '价格和数量必须大于0'
            })
        
        # 调用交易服务
        result = TradingService.sell_stock(user, ts_code, price, shares)
        
        if result['success']:
            return JsonResponse({
                'flag': 1,
                'money': 1,
                'msg': result['message'],
                'data': {
                    'net_amount': float(result['net_amount']),
                    'remaining_balance': float(result['remaining_balance'])
                }
            })
        else:
            return JsonResponse({
                'flag': 0,
                'money': 0,
                'msg': result['message']
            })
        
    except SysUser.DoesNotExist:
        return JsonResponse({
            'flag': 0,
            'money': 0,
            'msg': '用户不存在'
        })
    except Exception as e:
        return JsonResponse({
            'flag': 0,
            'money': 0,
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
        total_market_value = sum(float(pos['market_value']) for pos in positions)
        
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
        ts_code = request.GET.get('ts_code', '').strip()  # 按股票代码筛选

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

        # 按股票代码筛选
        if ts_code:
            queryset = queryset.filter(ts_code=ts_code)

        # 分页
        paginator = Paginator(queryset.order_by('-trade_time'), page_size)
        trades = paginator.get_page(page)

        # 序列化数据
        trade_list = []
        for trade in trades:
            # 确保时间格式化使用本地时区
            local_time = timezone.localtime(trade.trade_time)
            trade_data = {
                'id': trade.id,
                'user_id': trade.user.id,
                'username': trade.user.username,
                'ts_code': trade.ts_code,
                'stock_name': trade.stock_name,
                'trade_type': trade.trade_type,
                'trade_price': float(trade.trade_price),
                'trade_shares': trade.trade_shares,
                'trade_amount': float(trade.trade_amount),
                'commission': float(trade.commission),
                'status': trade.status,
                'trade_time': local_time.strftime('%Y-%m-%d %H:%M:%S'),
                # 前端显示用字段
                'time': local_time.strftime('%H:%M:%S'),
                'type': trade.trade_type.lower(),
                'price': float(trade.trade_price),
                'quantity': trade.trade_shares // 100,  # 转换为手数
                'amount': float(trade.trade_amount),
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

            # 获取股票基础信息，用于计算市值等指标
            try:
                stock_basic = StockBasic.objects.get(ts_code=item.ts_code)
            except StockBasic.DoesNotExist:
                stock_basic = None

            watch_data = {
                'ts_code': item.ts_code,
                'stock_name': item.stock_name,
                'name': item.stock_name,  # 前端兼容字段
                'add_time': item.add_time.strftime('%Y-%m-%d %H:%M:%S'),
                'current_price': float(latest_daily.close) if latest_daily and latest_daily.close else None,
                'change': float(latest_daily.change) if latest_daily and latest_daily.change else None,
                'pct_chg': float(latest_daily.pct_chg) if latest_daily and latest_daily.pct_chg else None,
                # 只返回真实存在的字段
                'volume': latest_daily.vol if latest_daily else None,
                'amount': float(latest_daily.amount) if latest_daily and latest_daily.amount else None,
                'turnover_rate': None,
                'pe_ratio': None,
                'market_cap': None,
                'trade_date': latest_daily.trade_date.strftime('%Y-%m-%d') if latest_daily else None,
                'open': float(latest_daily.open) if latest_daily and latest_daily.open else None,
                'high': float(latest_daily.high) if latest_daily and latest_daily.high else None,
                'low': float(latest_daily.low) if latest_daily and latest_daily.low else None,
                'pre_close': float(latest_daily.pre_close) if latest_daily and latest_daily.pre_close else None,
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


@admin_required
def admin_user_accounts(request):
    """管理员查看用户账户 - 仅管理员可访问"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        
        # 使用AdminService获取用户列表
        result = AdminService.get_user_list(page, page_size)
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'list': result['users'],
                'total': result['total'],
                'page': result['page'],
                'pageSize': result['page_size'],
                'totalPages': (result['total'] + page_size - 1) // page_size,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取用户账户失败: {str(e)}'
        })


@admin_required
@csrf_exempt
@require_http_methods(["POST"])
def admin_freeze_user(request):
    """管理员冻结用户账户 - 仅管理员可访问"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        freeze = data.get('freeze', True)  # True冻结，False解冻
        
        if not user_id:
            return JsonResponse({
                'code': 400,
                'msg': '请提供用户ID'
            })
        
        try:
            user = SysUser.objects.get(id=user_id)
            user.status = 1 if freeze else 0  # 1停用，0启用
            user.save()
            
            action = '冻结' if freeze else '解冻'
            return JsonResponse({
                'code': 200,
                'msg': f'{action}用户成功'
            })
            
        except SysUser.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'msg': '用户不存在'
            })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'操作失败: {str(e)}'
        })


@require_login
@csrf_exempt
@require_http_methods(["POST"])
def cancel_trade(request):
    """撤销交易 - 所有用户可访问（仅能撤销自己的待成交订单）"""
    try:
        user = SysUser.objects.get(id=request.user_id)
        data = json.loads(request.body)
        trade_id = data.get('trade_id')
        
        if not trade_id:
            return JsonResponse({
                'code': 400,
                'msg': '请提供交易记录ID'
            })
        
        try:
            trade = TradeRecord.objects.get(id=trade_id, user=user, status='PENDING')
            
            # 如果是买入订单，需要解冻资金
            if trade.trade_type == 'BUY':
                account = TradingService.get_or_create_account(user)
                total_cost = trade.trade_amount + trade.commission
                account.account_balance += total_cost
                account.frozen_balance -= total_cost
                account.save()
            
            # 如果是卖出订单，需要解冻股票
            elif trade.trade_type == 'SELL':
                try:
                    position = UserPosition.objects.get(user=user, ts_code=trade.ts_code)
                    position.available_shares += trade.trade_shares
                    position.save()
                except UserPosition.DoesNotExist:
                    pass
            
            # 更新交易状态
            trade.status = 'CANCELLED'
            trade.remark = (trade.remark or '') + ' [用户撤销]'
            trade.save()
            
            return JsonResponse({
                'code': 200,
                'msg': '撤销成功'
            })
            
        except TradeRecord.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'msg': '交易记录不存在或无法撤销'
            })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'撤销失败: {str(e)}'
        })


@require_login
def trading_statistics(request):
    """获取交易统计 - 所有用户可访问"""
    try:
        user = SysUser.objects.get(id=request.user_id)
        
        # 获取交易统计
        buy_trades = TradeRecord.objects.filter(user=user, trade_type='BUY', status='COMPLETED')
        sell_trades = TradeRecord.objects.filter(user=user, trade_type='SELL', status='COMPLETED')
        
        buy_count = buy_trades.count()
        sell_count = sell_trades.count()
        buy_amount = sum(float(trade.trade_amount) for trade in buy_trades)
        sell_amount = sum(float(trade.trade_amount) for trade in sell_trades)
        total_commission = sum(float(trade.commission) for trade in TradeRecord.objects.filter(user=user, status='COMPLETED'))
        
        # 持仓统计
        positions = TradingService.get_user_positions(user)
        total_market_value = sum(float(pos['market_value']) for pos in positions)
        total_profit_loss = sum(float(pos['profit_loss']) for pos in positions)
        
        # 账户信息
        account = TradingService.get_or_create_account(user)
        
        statistics = {
            'account_balance': float(account.account_balance),
            'total_assets': float(account.total_assets),
            'market_value': total_market_value,
            'total_profit_loss': total_profit_loss,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'buy_amount': buy_amount,
            'sell_amount': sell_amount,
            'total_commission': total_commission,
            'position_count': len(positions),
            'total_trades': buy_count + sell_count,
        }
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': statistics
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取统计数据失败: {str(e)}'
        })


@admin_required
def admin_user_records(request):
    """管理员查看用户交易记录 - 仅管理员可访问"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        user_id = request.GET.get('user_id')
        ts_code = request.GET.get('ts_code')
        
        # 使用AdminService获取交易记录
        result = AdminService.get_trading_records(
            page=page, 
            page_size=page_size, 
            user_id=int(user_id) if user_id else None,
            ts_code=ts_code
        )
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'list': result['trades'],
                'total': result['total'],
                'page': result['page'],
                'pageSize': result['page_size'],
                'totalPages': (result['total'] + page_size - 1) // page_size,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取用户交易记录失败: {str(e)}'
        })


@admin_required
@csrf_exempt
@require_http_methods(["POST"])
def admin_adjust_assets(request):
    """管理员调整用户资产 - 仅管理员可访问"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        adjust_amount = data.get('adjust_amount')
        reason = data.get('reason', '管理员调整')
        
        if not user_id or adjust_amount is None:
            return JsonResponse({
                'code': 400,
                'msg': '请提供用户ID和调整金额'
            })
        
        try:
            adjust_amount = Decimal(str(adjust_amount))
        except (ValueError, TypeError):
            return JsonResponse({
                'code': 400,
                'msg': '调整金额格式错误'
            })
        
        try:
            user = SysUser.objects.get(id=user_id)
            account = TradingService.get_or_create_account(user)
            
            # 记录调整前的资产
            old_balance = account.account_balance
            
            # 调整资产
            account.account_balance += adjust_amount
            
            # 检查资产不能为负
            if account.account_balance < 0:
                return JsonResponse({
                    'code': 400,
                    'msg': '调整后资产不能为负数'
                })
            
            account.save()
            
            # 记录调整日志
            TradeRecord.objects.create(
                user=user,
                ts_code='ADMIN_ADJUST',
                stock_name='资产调整',
                trade_type='ADJUST',
                trade_price=Decimal('0.00'),
                trade_shares=0,
                trade_amount=adjust_amount,
                commission=Decimal('0.00'),
                status='COMPLETED',
                remark=f'{reason}，调整前: {old_balance}，调整后: {account.account_balance}'
            )
            
            return JsonResponse({
                'code': 200,
                'msg': '资产调整成功',
                'data': {
                    'old_balance': float(old_balance),
                    'new_balance': float(account.account_balance),
                    'adjust_amount': float(adjust_amount)
                }
            })
            
        except SysUser.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'msg': '用户不存在'
            })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'资产调整失败: {str(e)}'
        })


# ====================新闻管理功能====================

@admin_required
def admin_news_list(request):
    """管理员获取新闻列表 - 仅管理员可访问"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        category = request.GET.get('category')
        is_published = request.GET.get('is_published')
        
        # 转换is_published参数
        if is_published is not None:
            is_published = is_published.lower() == 'true'
        
        # 使用AdminService获取新闻列表
        result = AdminService.get_news_list(
            page=page, 
            page_size=page_size, 
            category=category,
            is_published=is_published
        )
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'list': result['news'],
                'total': result['total'],
                'page': result['page'],
                'pageSize': result['page_size'],
                'totalPages': (result['total'] + page_size - 1) // page_size,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取新闻列表失败: {str(e)}'
        })


@admin_required
@csrf_exempt
@require_http_methods(["POST"])
def admin_create_news(request):
    """管理员创建新闻 - 仅管理员可访问"""
    try:
        admin_user = SysUser.objects.get(id=request.user_id)
        data = json.loads(request.body)
        
        title = data.get('title')
        content = data.get('content')
        source = data.get('source')
        category = data.get('category')
        related_stocks = data.get('related_stocks', [])
        
        if not title or not content:
            return JsonResponse({
                'code': 400,
                'msg': '标题和内容不能为空'
            })
        
        # 使用AdminService创建新闻
        success, message, news = AdminService.create_news(
            admin_user=admin_user,
            title=title,
            content=content,
            source=source,
            category=category,
            related_stocks=related_stocks
        )
        
        if success:
            return JsonResponse({
                'code': 200,
                'msg': message,
                'data': {
                    'id': news.id,
                    'title': news.title
                }
            })
        else:
            return JsonResponse({
                'code': 400,
                'msg': message
            })
        
    except SysUser.DoesNotExist:
        return JsonResponse({
            'code': 404,
            'msg': '管理员用户不存在'
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'创建新闻失败: {str(e)}'
        })


@admin_required
@csrf_exempt
@require_http_methods(["PUT"])
def admin_update_news(request, news_id):
    """管理员更新新闻 - 仅管理员可访问"""
    try:
        admin_user = SysUser.objects.get(id=request.user_id)
        data = json.loads(request.body)
        
        # 使用AdminService更新新闻
        success, message = AdminService.update_news(
            admin_user=admin_user,
            news_id=news_id,
            **data
        )
        
        if success:
            return JsonResponse({
                'code': 200,
                'msg': message
            })
        else:
            return JsonResponse({
                'code': 400,
                'msg': message
            })
        
    except SysUser.DoesNotExist:
        return JsonResponse({
            'code': 404,
            'msg': '管理员用户不存在'
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'更新新闻失败: {str(e)}'
        })


@admin_required
@csrf_exempt
@require_http_methods(["DELETE"])
def admin_delete_news(request, news_id):
    """管理员删除新闻 - 仅管理员可访问"""
    try:
        admin_user = SysUser.objects.get(id=request.user_id)
        
        # 使用AdminService删除新闻
        success, message = AdminService.delete_news(
            admin_user=admin_user,
            news_id=news_id
        )
        
        if success:
            return JsonResponse({
                'code': 200,
                'msg': message
            })
        else:
            return JsonResponse({
                'code': 400,
                'msg': message
            })
        
    except SysUser.DoesNotExist:
        return JsonResponse({
            'code': 404,
            'msg': '管理员用户不存在'
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'删除新闻失败: {str(e)}'
        })


@admin_required
def admin_operation_logs(request):
    """管理员获取操作日志 - 仅管理员可访问"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        admin_user_id = request.GET.get('admin_user_id')
        operation_type = request.GET.get('operation_type')
        
        # 使用AdminService获取操作日志
        result = AdminService.get_operation_logs(
            page=page,
            page_size=page_size,
            admin_user_id=int(admin_user_id) if admin_user_id else None,
            operation_type=operation_type
        )
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'list': result['logs'],
                'total': result['total'],
                'page': result['page'],
                'pageSize': result['page_size'],
                'totalPages': (result['total'] + page_size - 1) // page_size,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取操作日志失败: {str(e)}'
        })


@admin_required
def admin_statistics(request):
    """管理员获取统计信息 - 仅管理员可访问"""
    try:
        from utils.auth_utils import get_client_ip, get_user_agent
        
        # 记录操作日志
        admin_user = SysUser.objects.get(id=request.user_id)
        AdminService.log_operation(
            admin_user=admin_user,
            operation_type='ADMIN_VIEW',
            operation_desc='查看系统统计信息',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        # 获取统计信息
        stats = AdminService.get_statistics()
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': stats
        })
        
    except SysUser.DoesNotExist:
        return JsonResponse({
            'code': 404,
            'msg': '管理员用户不存在'
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取统计信息失败: {str(e)}'
        })


@require_login
def get_news_list(request):
    """获取新闻列表 - 所有用户可访问"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        category = request.GET.get('category')
        
        # 只显示已发布的新闻
        result = AdminService.get_news_list(
            page=page,
            page_size=page_size,
            category=category,
            is_published=True
        )
        
        return JsonResponse({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'list': result['news'],
                'total': result['total'],
                'page': result['page'],
                'pageSize': result['page_size'],
                'totalPages': (result['total'] + page_size - 1) // page_size,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取新闻列表失败: {str(e)}'
        })


@require_login
def get_news_detail(request, news_id):
    """获取新闻详情 - 所有用户可访问"""
    try:
        try:
            news = MarketNews.objects.get(id=news_id, is_published=True)
            
            # 增加阅读次数
            news.read_count += 1
            news.save()
            
            news_data = {
                'id': news.id,
                'title': news.title,
                'content': news.content,
                'source': news.source,
                'source_url': getattr(news, 'source_url', ''),
                'category': news.category,
                'related_stocks': news.related_stocks,
                'publish_time': news.publish_time.strftime('%Y-%m-%d %H:%M:%S'),
                'read_count': news.read_count,
            }
            
            return JsonResponse({
                'code': 200,
                'msg': '获取成功',
                'data': news_data
            })
            
        except MarketNews.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'msg': '新闻不存在或未发布'
            })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'获取新闻详情失败: {str(e)}'
        })


@admin_required
@csrf_exempt
@require_http_methods(["POST"])
def admin_fetch_news(request):
    """管理员爬取最新新闻 - 仅管理员可访问"""
    try:
        from stock.services import NewsService

        admin_user = SysUser.objects.get(id=request.user_id)
        data = json.loads(request.body) if request.body else {}
        limit = data.get('limit', 20)

        # 记录操作日志
        AdminService.log_operation(
            admin_user=admin_user,
            operation_type='NEWS_FETCH',
            operation_desc=f"爬取最新新闻，限制数量：{limit}"
        )

        # 爬取新闻
        saved_count = NewsService.update_news_data(limit=limit)

        if saved_count > 0:
            return JsonResponse({
                'code': 200,
                'msg': f'成功爬取并保存了 {saved_count} 条新闻',
                'data': {'saved_count': saved_count}
            })
        else:
            return JsonResponse({
                'code': 200,
                'msg': '未发现新的新闻或爬取失败',
                'data': {'saved_count': 0}
            })

    except Exception as e:
        return JsonResponse({
            'code': 500,
            'msg': f'爬取新闻失败: {str(e)}'
        })
