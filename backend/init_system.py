#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一系统初始化脚本 - 一键初始化数据库和测试数据
支持：
1. 数据库迁移
2. 创建用户、角色数据
3. 创建股票测试数据
4. 创建交易账户
5. 创建示例新闻和自选股
"""

import os
import sys
import django
from pathlib import Path

# 设置 Django 环境
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.core.management import call_command
from django.db import transaction
from datetime import datetime, date, timedelta
from decimal import Decimal
import hashlib

# 导入模型
from user.models import SysUser
from role.models import SysRole, SysUserRole
from stock.models import StockBasic, StockDaily, StockCompany
from trading.models import UserStockAccount, UserPosition, TradeRecord, UserWatchList, MarketNews


def reset_database():
    """重置数据库文件"""
    print("=== 重置数据库 ===")
    
    # 删除现有数据库文件
    db_files = ['db.sqlite3']
    for db_file in db_files:
        db_path = BASE_DIR / db_file
        if db_path.exists():
            db_path.unlink()
            print(f"删除数据库文件: {db_file}")
    
    print("数据库文件清理完成")


def create_database_tables():
    """创建数据库表结构"""
    print("\n=== 创建数据库表结构 ===")
    
    try:
        # 应用所有迁移到统一数据库
        call_command('migrate', verbosity=0)
        print("数据库表结构创建完成")
        return True
    except Exception as e:
        print(f"数据库迁移失败: {e}")
        return False


def create_roles():
    """创建系统角色"""
    print("\n=== 创建系统角色 ===")
    
    roles_data = [
        {
            'name': '普通用户',
            'code': 'user',
            'remark': '基础交易功能权限'
        },
        {
            'name': '管理员',
            'code': 'admin', 
            'remark': '用户管理和数据查看权限'
        },
        {
            'name': '超级管理员',
            'code': 'superadmin',
            'remark': '系统管理和所有权限'
        }
    ]
    
    for role_data in roles_data:
        role, created = SysRole.objects.get_or_create(
            code=role_data['code'],
            defaults={
                'name': role_data['name'],
                'remark': role_data['remark'],
                'create_time': datetime.now(),
                'update_time': datetime.now()
            }
        )
        if created:
            print(f"  创建角色: {role.name}")
        else:
            print(f"  角色已存在: {role.name}")


def create_users():
    """创建测试用户"""
    print("\n=== 创建测试用户 ===")
    
    # MD5加密123456的结果
    password_hash = hashlib.md5('123456'.encode()).hexdigest()
    
    users_data = [
        {
            'username': 'python222',
            'email': 'admin@example.com',
            'remark': '系统超级管理员',
            'role_code': 'superadmin'
        },
        {
            'username': 'admin001',
            'email': 'admin001@example.com', 
            'remark': '测试管理员',
            'role_code': 'admin'
        },
        {
            'username': 'trader001',
            'email': 'trader001@example.com',
            'remark': '测试普通用户',
            'role_code': 'user'
        },
        {
            'username': 'trader002',
            'email': 'trader002@example.com',
            'remark': '测试普通用户',
            'role_code': 'user'
        }
    ]
    
    created_users = []
    
    for user_data in users_data:
        user, created = SysUser.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'password': password_hash,
                'email': user_data['email'],
                'status': 0,  # 0=正常，1=停用
                'remark': user_data['remark'],
                'create_time': datetime.now(),
                'update_time': datetime.now()
            }
        )
        
        if created:
            print(f"  创建用户: {user.username} ({user_data['role_code']})")
        else:
            print(f"  用户已存在: {user.username}")
            
        created_users.append((user, user_data['role_code']))
    
    return created_users


def assign_roles(users_with_roles):
    """分配用户角色"""
    print("\n=== 分配用户角色 ===")
    
    for user, role_code in users_with_roles:
        try:
            role = SysRole.objects.get(code=role_code)
            user_role, created = SysUserRole.objects.get_or_create(
                user=user,
                role=role
            )
            if created:
                print(f"  为用户 {user.username} 分配角色 {role.name}")
            else:
                print(f"  用户 {user.username} 已有角色 {role.name}")
        except SysRole.DoesNotExist:
            print(f"  角色 {role_code} 不存在")


def create_stock_accounts(users_with_roles):
    """创建股票账户"""
    print("\n=== 创建股票账户 ===")
    
    for user, role_code in users_with_roles:
        # 根据角色设置初始资金
        if role_code == 'superadmin':
            initial_balance = 1000000.00
        elif role_code == 'admin':
            initial_balance = 500000.00
        else:
            initial_balance = 100000.00
        
        account, created = UserStockAccount.objects.get_or_create(
            user=user,
            defaults={
                'account_balance': initial_balance,
                'frozen_balance': 0.00,
                'total_assets': initial_balance,
                'total_profit': 0.00,
            }
        )
        
        if created:
            print(f"  为用户 {user.username} 创建股票账户，初始资金: {initial_balance}")
        else:
            print(f"  用户 {user.username} 股票账户已存在")


def sync_real_stock_data():
    """同步真实股票数据 - 使用智能限流策略"""
    print("\n=== 同步真实股票数据 ===")
    
    try:
        from stock.services import StockDataService, RateLimiter
        import time
        
        # 1. 同步股票基本信息 (优先级最高)
        print("  正在同步股票基本信息...")
        if RateLimiter.can_call("stock_basic", max_calls=1, time_window=300):  # 5分钟1次
            RateLimiter.record_call("stock_basic")
            sync_result = StockDataService.sync_stock_basic()
            if sync_result['success']:
                print(f"  {sync_result['message']}")
            else:
                print(f"  同步股票基本信息失败: {sync_result['message']}")
                return False
        else:
            wait_time = RateLimiter.get_wait_time("stock_basic", max_calls=1, time_window=300)
            print(f"  股票基本信息同步限流中，需等待{int(wait_time)}秒")
            return False
        
        # 2. 分批同步热门股票的日线数据
        popular_stocks = [
            '000001.SZ',  # 平安银行
            '000002.SZ',  # 万科A
            '600036.SH',  # 招商银行
            '600519.SH',  # 贵州茅台
            '000858.SZ',  # 五粮液
        ]
        
        print("  正在分批同步热门股票日线数据...")
        api_name = "daily"
        success_count = 0
        
        for i, ts_code in enumerate(popular_stocks):
            try:
                # 检查限流 - 每分钟最多2次调用
                if not RateLimiter.can_call(api_name, max_calls=2, time_window=60):
                    wait_time = RateLimiter.get_wait_time(api_name, max_calls=2, time_window=60)
                    print(f"    API限流，等待{int(wait_time)}秒后继续...")
                    time.sleep(wait_time + 1)  # 多等1秒确保安全
                
                # 记录API调用并同步数据
                RateLimiter.record_call(api_name)
                sync_result = StockDataService.sync_stock_daily(ts_code, days=30)
                
                if sync_result['success']:
                    print(f"    {sync_result['message']}")
                    success_count += 1
                else:
                    print(f"    同步{ts_code}失败: {sync_result['message']}")
                
                # 如果不是最后一个，等待间隔以避免过于频繁的调用
                if i < len(popular_stocks) - 1:
                    print(f"    等待5秒后继续下一个股票...")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"    同步{ts_code}出现异常: {e}")
                continue
        
        print(f"  成功同步{success_count}/{len(popular_stocks)}只股票的日线数据")
        
        if success_count > 0:
            print("  股票数据同步完成！")
            return True
        else:
            print("  警告：所有股票数据同步失败，可能是API限流或网络问题")
            return False
        
    except Exception as e:
        print(f"  同步真实股票数据失败: {e}")
        print("  提示：如果是限流错误，请稍后再试")
        return False


def create_sample_news():
    """创建示例新闻"""
    print("\n=== 创建示例新闻 ===")
    
    news_data = [
        {
            'title': 'A股市场今日震荡上涨，科技股表现强势',
            'content': '今日A股三大指数集体上涨，创业板指涨幅超过2%...',
            'source': '财经新闻'
        },
        {
            'title': '央行货币政策保持稳健，流动性合理充裕',
            'content': '人民银行今日发布公告称，将继续实施稳健的货币政策...',
            'source': '央行公告'
        },
        {
            'title': '新能源汽车板块活跃，多只个股涨停',
            'content': '受政策利好影响，新能源汽车概念股今日表现活跃...',
            'source': '行业资讯'
        }
    ]
    
    for news in news_data:
        market_news, created = MarketNews.objects.get_or_create(
            title=news['title'],
            defaults={
                'content': news['content'],
                'source': news['source'],
                'publish_time': datetime.now(),
                'category': '市场动态'
            }
        )
        if created:
            print(f"  创建新闻: {news['title'][:20]}...")


def main():
    """主函数"""
    print("Mini-RABC 统一系统初始化")
    print("=" * 50)
    
    try:
        # 1. 重置数据库（放在事务外）
        reset_database()
        
        # 2. 创建数据库表结构
        if not create_database_tables():
            return
            
        with transaction.atomic():
            # 3. 创建角色
            create_roles()
            
            # 4. 创建用户
            users_with_roles = create_users()
            
            # 5. 分配角色
            assign_roles(users_with_roles)
            
            # 6. 创建股票账户
            create_stock_accounts(users_with_roles)
            
            # 7. 创建示例新闻
            create_sample_news()
        
        # 8. 同步真实股票数据（放在事务外，因为可能耗时较长）
        sync_real_stock_data()
        
        print("\n" + "=" * 50)
        print("系统初始化完成！")
        print("\n测试账号信息:")
        print("  超级管理员: python222 / 123456")
        print("  管理员: admin001 / 123456")
        print("  普通用户1: trader001 / 123456")
        print("  普通用户2: trader002 / 123456")
        
        print(f"\n数据统计:")
        print(f"  用户数量: {SysUser.objects.count()}")
        print(f"  角色数量: {SysRole.objects.count()}")
        print(f"  股票数量: {StockBasic.objects.count()}")
        print(f"  行情记录: {StockDaily.objects.count()}")
        print(f"  股票账户: {UserStockAccount.objects.count()}")
        print(f"  市场新闻: {MarketNews.objects.count()}")
        
        print(f"\n启动服务器: python manage.py runserver")
        print(f"现在可以开始测试系统功能了！")
        
    except Exception as e:
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()