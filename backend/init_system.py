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


def create_test_stocks():
    """创建测试股票数据"""
    print("\n=== 创建测试股票数据 ===")
    
    # 使用非标准格式避免与真实股票混淆
    stocks = [
        {
            'ts_code': 'TEST001.SZ',
            'symbol': 'TEST001',
            'name': '测试银行',
            'fullname': '测试银行股份有限公司',
            'industry': '银行',
            'area': '深圳',
            'market': '主板',
            'exchange': 'SZSE',
            'list_status': 'L',
            'list_date': date(2020, 1, 1)
        },
        {
            'ts_code': 'TEST002.SZ',
            'symbol': 'TEST002',
            'name': '测试地产',
            'fullname': '测试地产开发有限公司',
            'industry': '房地产开发',
            'area': '深圳',
            'market': '主板',
            'exchange': 'SZSE',
            'list_status': 'L',
            'list_date': date(2020, 2, 1)
        },
        {
            'ts_code': 'TEST003.SH',
            'symbol': 'TEST003',
            'name': '测试科技',
            'fullname': '测试科技股份有限公司',
            'industry': '软件开发',
            'area': '上海',
            'market': '主板',
            'exchange': 'SSE',
            'list_status': 'L',
            'list_date': date(2020, 3, 1)
        },
        {
            'ts_code': 'TEST004.SH',
            'symbol': 'TEST004',
            'name': '测试制造',
            'fullname': '测试制造工业集团',
            'industry': '机械设备',
            'area': '上海',
            'market': '主板',
            'exchange': 'SSE',
            'list_status': 'L',
            'list_date': date(2020, 4, 1)
        },
        {
            'ts_code': 'TEST005.SZ',
            'symbol': 'TEST005',
            'name': '测试医药',
            'fullname': '测试医药生物科技有限公司',
            'industry': '生物医药',
            'area': '北京',
            'market': '创业板',
            'exchange': 'SZSE',
            'list_status': 'L',
            'list_date': date(2020, 5, 1)
        },
        {
            'ts_code': 'TEST006.SZ',
            'symbol': 'TEST006',
            'name': '测试新能源',
            'fullname': '测试新能源汽车股份公司',
            'industry': '汽车制造',
            'area': '广东',
            'market': '主板',
            'exchange': 'SZSE',
            'list_status': 'L',
            'list_date': date(2020, 6, 1)
        }
    ]
    
    for stock_data in stocks:
        stock, created = StockBasic.objects.get_or_create(
            ts_code=stock_data['ts_code'],
            defaults=stock_data
        )
        if created:
            print(f"  创建股票: {stock.name} ({stock.ts_code})")
        else:
            print(f"  股票已存在: {stock.name}")


def create_stock_daily_data():
    """创建股票行情数据"""
    print("\n=== 创建股票行情数据 ===")
    
    # 为最近3天创建行情数据
    today = date.today()
    
    stocks_prices = {
        'TEST001.SZ': {'base_price': 10.50, 'name': '测试银行'},
        'TEST002.SZ': {'base_price': 8.80, 'name': '测试地产'},  
        'TEST003.SH': {'base_price': 45.20, 'name': '测试科技'},
        'TEST004.SH': {'base_price': 23.10, 'name': '测试制造'},
        'TEST005.SZ': {'base_price': 86.50, 'name': '测试医药'},
        'TEST006.SZ': {'base_price': 128.90, 'name': '测试新能源'}
    }
    
    import random
    
    for i in range(3):  # 最近3天
        trade_date = today - timedelta(days=2-i)
        
        for ts_code, stock_info in stocks_prices.items():
            base_price = stock_info['base_price']
            
            # 模拟价格波动
            price_change = random.uniform(-0.05, 0.05)  # 5%内波动
            close_price = base_price * (1 + price_change)
            open_price = close_price * random.uniform(0.99, 1.01)
            high_price = max(open_price, close_price) * random.uniform(1.00, 1.02)
            low_price = min(open_price, close_price) * random.uniform(0.98, 1.00)
            pre_close = base_price
            
            # 计算涨跌额和涨跌幅
            change = Decimal(str(close_price)) - Decimal(str(pre_close))
            pct_chg = (change / Decimal(str(pre_close))) * 100
            
            daily, created = StockDaily.objects.get_or_create(
                ts_code=ts_code,
                trade_date=trade_date,
                defaults={
                    'open': Decimal(str(round(open_price, 2))),
                    'high': Decimal(str(round(high_price, 2))),
                    'low': Decimal(str(round(low_price, 2))),
                    'close': Decimal(str(round(close_price, 2))),
                    'pre_close': Decimal(str(round(pre_close, 2))),
                    'change': change,
                    'pct_chg': pct_chg,
                    'vol': random.randint(500000, 2000000),
                    'amount': Decimal(str(round(random.uniform(50000, 200000), 2)))
                }
            )
            
            if created:
                print(f"  创建行情: {ts_code} {trade_date}")


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
            
            # 7. 创建测试股票
            create_test_stocks()
            
            # 8. 创建股票行情数据
            create_stock_daily_data()
            
            # 9. 创建示例新闻
            create_sample_news()
        
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