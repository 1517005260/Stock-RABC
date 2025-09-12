# -*- coding: utf-8 -*-

from datetime import datetime, date
from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.utils import timezone
from typing import Dict, List, Optional, Tuple

from trading.models import (
    UserStockAccount, UserPosition, TradeRecord, UserWatchList, 
    MarketNews, AdminOperationLog
)
from stock.models import StockBasic, StockDaily
from user.models import SysUser


class TradingService:
    """交易服务类"""
    
    @staticmethod
    def get_user_account(user: SysUser) -> Optional[UserStockAccount]:
        """获取用户股票账户"""
        try:
            return UserStockAccount.objects.get(user=user)
        except UserStockAccount.DoesNotExist:
            return None
    
    @staticmethod
    def create_user_account(user: SysUser, initial_balance: Decimal = Decimal('100000.00')) -> UserStockAccount:
        """创建用户股票账户"""
        return UserStockAccount.objects.create(
            user=user,
            account_balance=initial_balance,
            total_assets=initial_balance
        )
    
    @staticmethod
    def get_or_create_account(user: SysUser) -> UserStockAccount:
        """获取或创建用户股票账户"""
        account, created = UserStockAccount.objects.get_or_create(
            user=user,
            defaults={
                'account_balance': Decimal('100000.00'),
                'frozen_balance': Decimal('0.00'),
                'total_assets': Decimal('100000.00'),
                'total_profit': Decimal('0.00')
            }
        )
        return account
    
    @staticmethod
    def get_user_positions(user: SysUser) -> List[Dict]:
        """获取用户持仓信息"""
        positions = UserPosition.objects.filter(user=user)
        result = []
        
        for position in positions:
            # 获取最新价格
            try:
                latest_daily = StockDaily.objects.filter(ts_code=position.ts_code).order_by('-trade_date').first()
                current_price = float(latest_daily.close) if latest_daily and latest_daily.close else float(position.current_price)
            except:
                current_price = float(position.current_price)
            
            market_value = position.position_shares * Decimal(str(current_price))
            profit_loss = market_value - (position.position_shares * position.cost_price)
            
            result.append({
                'ts_code': position.ts_code,
                'stock_name': position.stock_name,
                'position_shares': position.position_shares,
                'available_shares': position.available_shares,
                'cost_price': float(position.cost_price),
                'current_price': current_price,
                'market_value': float(market_value),
                'profit_loss': float(profit_loss),
                'profit_loss_ratio': float(profit_loss / (position.position_shares * position.cost_price) * 100) if position.cost_price > 0 else 0
            })
        
        return result
    
    @staticmethod
    def update_user_assets(user: SysUser) -> bool:
        """更新用户总资产"""
        try:
            account = TradingService.get_or_create_account(user)
            if not account:
                return False
                
            positions = UserPosition.objects.filter(user=user)
            position_value = sum(
                position.position_shares * position.current_price
                for position in positions
            )
            
            account.total_assets = account.account_balance + account.frozen_balance + position_value
            account.save()
            return True
        except Exception:
            return False
    
    @staticmethod
    @transaction.atomic
    def buy_stock(user: SysUser, ts_code: str, shares: int, price: Decimal) -> Tuple[bool, str]:
        """买入股票"""
        try:
            # 获取股票信息
            try:
                stock = StockBasic.objects.get(ts_code=ts_code)
            except StockBasic.DoesNotExist:
                return False, "股票不存在"
            
            # 获取用户账户
            account = TradingService.get_or_create_account(user)
            if not account:
                return False, "用户账户不存在"
            
            # 计算交易金额
            trade_amount = shares * price
            commission = Decimal('5.00')  # 手续费
            total_cost = trade_amount + commission
            
            # 检查资金是否充足
            if account.account_balance < total_cost:
                return False, "资金不足"
            
            # 更新账户余额
            account.account_balance -= total_cost
            account.save()
            
            # 更新或创建持仓
            position, created = UserPosition.objects.get_or_create(
                user=user,
                ts_code=ts_code,
                defaults={
                    'stock_name': stock.name,
                    'position_shares': shares,
                    'available_shares': shares,
                    'cost_price': price,
                    'current_price': price
                }
            )
            
            if not created:
                # 计算新的成本价
                total_shares = position.position_shares + shares
                total_cost_old = position.position_shares * position.cost_price
                new_cost_price = (total_cost_old + trade_amount) / total_shares
                
                position.position_shares = total_shares
                position.available_shares += shares
                position.cost_price = new_cost_price
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
                status='COMPLETED'
            )
            
            # 更新总资产
            TradingService.update_user_assets(user)
            
            return True, "买入成功"
            
        except Exception as e:
            return False, f"买入失败: {str(e)}"
    
    @staticmethod
    @transaction.atomic
    def sell_stock(user: SysUser, ts_code: str, price: float, shares: int) -> Dict:
        """卖出股票 - 返回字典格式以兼容视图层"""
        try:
            # 获取股票信息
            try:
                stock = StockBasic.objects.get(ts_code=ts_code)
            except StockBasic.DoesNotExist:
                return {'success': False, 'message': "股票不存在"}
            
            # 获取用户账户和持仓
            account = TradingService.get_or_create_account(user)
            if not account:
                return {'success': False, 'message': "用户账户不存在"}
            
            try:
                position = UserPosition.objects.get(user=user, ts_code=ts_code)
            except UserPosition.DoesNotExist:
                return {'success': False, 'message': "无此股票持仓"}
            
            # 检查可用股数
            if position.available_shares < shares:
                return {'success': False, 'message': "可用股数不足"}
            
            # 计算交易金额
            price_decimal = Decimal(str(price))
            trade_amount = shares * price_decimal
            commission = Decimal('5.00')  # 手续费
            net_amount = trade_amount - commission
            
            # 更新账户余额
            account.account_balance += net_amount
            account.save()
            
            # 更新持仓
            position.position_shares -= shares
            position.available_shares -= shares
            
            if position.position_shares == 0:
                position.delete()
            else:
                position.save()
            
            # 记录交易
            TradeRecord.objects.create(
                user=user,
                ts_code=ts_code,
                stock_name=stock.name,
                trade_type='SELL',
                trade_price=price_decimal,
                trade_shares=shares,
                trade_amount=trade_amount,
                commission=commission,
                status='COMPLETED'
            )
            
            # 更新总资产
            TradingService.update_user_assets(user)
            
            return {
                'success': True, 
                'message': "卖出成功",
                'net_amount': net_amount,
                'remaining_balance': account.account_balance
            }
            
        except Exception as e:
            return {'success': False, 'message': f"卖出失败: {str(e)}"}
    

class AdminService:
    """管理员服务类"""
    
    @staticmethod
    def log_operation(admin_user: SysUser, operation_type: str, operation_desc: str, 
                     target_object: str = None, is_success: bool = True, 
                     error_message: str = None, ip_address: str = None, 
                     user_agent: str = None) -> AdminOperationLog:
        """记录管理员操作日志"""
        return AdminOperationLog.objects.create(
            admin_user=admin_user,
            operation_type=operation_type,
            operation_desc=operation_desc,
            target_object=target_object,
            is_success=is_success,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def get_user_list(page: int = 1, page_size: int = 20) -> Dict:
        """获取用户列表"""
        users = SysUser.objects.all().order_by('-create_time')
        total = users.count()
        start = (page - 1) * page_size
        end = start + page_size
        user_list = users[start:end]
        
        # 获取每个用户的股票账户信息
        result = []
        for user in user_list:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phonenumber': user.phonenumber,
                'status': user.status,
                'create_time': user.create_time,
                'account_balance': 0,
                'total_assets': 0
            }
            
            # 获取股票账户信息
            try:
                account = UserStockAccount.objects.get(user=user)
                user_data['account_balance'] = account.account_balance
                user_data['total_assets'] = account.total_assets
            except UserStockAccount.DoesNotExist:
                pass
                
            result.append(user_data)
        
        return {
            'total': total,
            'users': result,
            'page': page,
            'page_size': page_size
        }
    
    @staticmethod
    def get_trading_records(page: int = 1, page_size: int = 20, 
                           user_id: int = None, ts_code: str = None) -> Dict:
        """获取交易记录"""
        trades = TradeRecord.objects.all().order_by('-trade_time')
        
        # 筛选条件
        if user_id:
            trades = trades.filter(user_id=user_id)
        if ts_code:
            trades = trades.filter(ts_code=ts_code)
        
        total = trades.count()
        start = (page - 1) * page_size
        end = start + page_size
        trade_list = trades[start:end]
        
        # 构建返回数据
        result = []
        for trade in trade_list:
            result.append({
                'id': trade.id,
                'username': trade.user.username,
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
                'status_display': trade.get_status_display()
            })
        
        return {
            'total': total,
            'trades': result,
            'page': page,
            'page_size': page_size
        }
    
    @staticmethod
    def get_news_list(page: int = 1, page_size: int = 20, 
                     category: str = None, is_published: bool = None) -> Dict:
        """获取新闻列表"""
        news = MarketNews.objects.all().order_by('-publish_time')
        
        # 筛选条件
        if category:
            news = news.filter(category=category)
        if is_published is not None:
            news = news.filter(is_published=is_published)
        
        total = news.count()
        start = (page - 1) * page_size
        end = start + page_size
        news_list = news[start:end]
        
        return {
            'total': total,
            'news': list(news_list.values()),
            'page': page,
            'page_size': page_size
        }
    
    @staticmethod
    @transaction.atomic
    def create_news(admin_user: SysUser, title: str, content: str, 
                   source: str = None, category: str = None, 
                   related_stocks: List[str] = None) -> Tuple[bool, str, MarketNews]:
        """创建新闻"""
        try:
            news = MarketNews.objects.create(
                title=title,
                content=content,
                source=source,
                category=category,
                related_stocks=related_stocks,
                publish_time=timezone.now(),
                created_by=admin_user,
                is_published=True
            )
            
            # 记录操作日志
            AdminService.log_operation(
                admin_user=admin_user,
                operation_type='NEWS_CREATE',
                operation_desc=f"创建新闻: {title}",
                target_object=f"news_id:{news.id}"
            )
            
            return True, "新闻创建成功", news
            
        except Exception as e:
            return False, f"新闻创建失败: {str(e)}", None
    
    @staticmethod
    @transaction.atomic
    def update_news(admin_user: SysUser, news_id: int, **kwargs) -> Tuple[bool, str]:
        """更新新闻"""
        try:
            news = MarketNews.objects.get(id=news_id)
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(news, key):
                    setattr(news, key, value)
            
            news.save()
            
            # 记录操作日志
            AdminService.log_operation(
                admin_user=admin_user,
                operation_type='NEWS_UPDATE',
                operation_desc=f"更新新闻: {news.title}",
                target_object=f"news_id:{news_id}"
            )
            
            return True, "新闻更新成功"
            
        except MarketNews.DoesNotExist:
            return False, "新闻不存在"
        except Exception as e:
            return False, f"新闻更新失败: {str(e)}"
    
    @staticmethod
    @transaction.atomic
    def delete_news(admin_user: SysUser, news_id: int) -> Tuple[bool, str]:
        """删除新闻"""
        try:
            news = MarketNews.objects.get(id=news_id)
            title = news.title
            news.delete()
            
            # 记录操作日志
            AdminService.log_operation(
                admin_user=admin_user,
                operation_type='NEWS_DELETE',
                operation_desc=f"删除新闻: {title}",
                target_object=f"news_id:{news_id}"
            )
            
            return True, "新闻删除成功"
            
        except MarketNews.DoesNotExist:
            return False, "新闻不存在"
        except Exception as e:
            return False, f"新闻删除失败: {str(e)}"
    
    @staticmethod
    def get_operation_logs(page: int = 1, page_size: int = 20, 
                          admin_user_id: int = None, operation_type: str = None) -> Dict:
        """获取操作日志"""
        logs = AdminOperationLog.objects.all().order_by('-operation_time')
        
        # 筛选条件
        if admin_user_id:
            logs = logs.filter(admin_user_id=admin_user_id)
        if operation_type:
            logs = logs.filter(operation_type=operation_type)
        
        total = logs.count()
        start = (page - 1) * page_size
        end = start + page_size
        log_list = logs[start:end]
        
        # 构建返回数据
        result = []
        for log in log_list:
            result.append({
                'id': log.id,
                'admin_username': log.admin_user.username,
                'operation_type': log.operation_type,
                'operation_type_display': dict(AdminOperationLog.OPERATION_TYPES).get(log.operation_type),
                'operation_desc': log.operation_desc,
                'target_object': log.target_object,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'operation_time': log.operation_time,
                'is_success': log.is_success,
                'error_message': log.error_message
            })
        
        return {
            'total': total,
            'logs': result,
            'page': page,
            'page_size': page_size
        }
    
    @staticmethod
    def get_statistics() -> Dict:
        """获取统计信息"""
        # 用户统计
        total_users = SysUser.objects.count()
        active_users = SysUser.objects.filter(status=0).count()
        
        # 交易统计
        total_trades = TradeRecord.objects.count()
        today_trades = TradeRecord.objects.filter(
            trade_time__date=date.today()
        ).count()
        
        # 新闻统计
        total_news = MarketNews.objects.count()
        published_news = MarketNews.objects.filter(is_published=True).count()
        
        # 资产统计
        total_assets = UserStockAccount.objects.aggregate(
            total=Sum('total_assets')
        )['total'] or 0
        
        return {
            'user_stats': {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': total_users - active_users
            },
            'trade_stats': {
                'total_trades': total_trades,
                'today_trades': today_trades
            },
            'news_stats': {
                'total_news': total_news,
                'published_news': published_news,
                'draft_news': total_news - published_news
            },
            'asset_stats': {
                'total_assets': total_assets
            }
        }


class WatchListService:
    """自选股服务类"""
    
    @staticmethod
    def add_to_watchlist(user: SysUser, ts_code: str) -> Tuple[bool, str]:
        """添加到自选股"""
        try:
            # 检查股票是否存在
            try:
                stock = StockBasic.objects.get(ts_code=ts_code)
            except StockBasic.DoesNotExist:
                return False, "股票不存在"
            
            # 检查是否已经在自选股中
            if UserWatchList.objects.filter(user=user, ts_code=ts_code).exists():
                return False, "股票已在自选股中"
            
            # 添加到自选股
            UserWatchList.objects.create(
                user=user,
                ts_code=ts_code,
                stock_name=stock.name
            )
            
            return True, "添加成功"
            
        except Exception as e:
            return False, f"添加失败: {str(e)}"
    
    @staticmethod
    def remove_from_watchlist(user: SysUser, ts_code: str) -> Tuple[bool, str]:
        """从自选股中移除"""
        try:
            watchlist_item = UserWatchList.objects.get(user=user, ts_code=ts_code)
            watchlist_item.delete()
            return True, "移除成功"
        except UserWatchList.DoesNotExist:
            return False, "股票不在自选股中"
        except Exception as e:
            return False, f"移除失败: {str(e)}"
    
    @staticmethod
    def get_user_watchlist(user: SysUser) -> List[Dict]:
        """获取用户自选股列表"""
        watchlist = UserWatchList.objects.filter(user=user).order_by('-add_time')
        
        result = []
        for item in watchlist:
            # 获取最新价格信息
            try:
                latest_data = StockDaily.objects.filter(
                    ts_code=item.ts_code
                ).order_by('-trade_date').first()
                
                current_price = latest_data.close if latest_data else 0
                change = latest_data.change if latest_data else 0
                pct_chg = latest_data.pct_chg if latest_data else 0
            except:
                current_price = change = pct_chg = 0
            
            result.append({
                'ts_code': item.ts_code,
                'stock_name': item.stock_name,
                'add_time': item.add_time,
                'current_price': current_price,
                'change': change,
                'pct_chg': pct_chg
            })
        
        return result