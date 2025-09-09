#!/usr/bin/env python
"""
股票交易系统API测试脚本
测试股票和交易相关的所有功能
"""

import requests
import json
import sys

BASE_URL = 'http://localhost:8000'
session = requests.Session()

def test_user_login():
    """测试用户登录"""
    print("=== 测试用户登录 ===")
    
    # 使用系统默认的超级管理员账号
    login_data = {
        'username': 'python222',
        'password': '123456'
    }
    
    response = session.post(f'{BASE_URL}/user/login', data=login_data)
    print(f"登录响应状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"登录结果: {result}")
        
        if result.get('code') == 200:
            token = result.get('token')
            if token:
                # 设置Authorization header
                session.headers.update({'Authorization': token})
                print(f"登录成功，Token: {token[:50]}...")
                return True
    
    print("登录失败")
    print(f"响应内容: {response.text}")
    return False


def test_stock_sync():
    """测试股票数据同步（仅超级管理员）"""
    print("\n=== 测试股票数据同步 ===")
    
    # 同步少量股票基本信息
    sync_data = {
        'type': 'basic'
    }
    
    response = session.post(
        f'{BASE_URL}/stock/sync/', 
        data=json.dumps(sync_data),
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"同步响应状态: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"同步结果: {result}")
        return result.get('code') == 200
    else:
        print(f"同步失败: {response.text}")
        return False


def test_stock_list():
    """测试股票列表"""
    print("\n=== 测试股票列表 ===")
    
    response = session.get(f'{BASE_URL}/stock/list/', params={'pageSize': 5})
    print(f"响应状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"获取到 {len(result.get('data', {}).get('list', []))} 只股票")
        
        # 打印前几只股票信息
        stocks = result.get('data', {}).get('list', [])
        for stock in stocks[:3]:
            print(f"  - {stock['ts_code']} {stock['name']} 价格: {stock.get('current_price', 'N/A')}")
        
        return len(stocks) > 0
    else:
        print(f"获取失败: {response.text}")
        return False


def test_stock_detail():
    """测试股票详情"""
    print("\n=== 测试股票详情 ===")
    
    # 测试平安银行
    ts_code = '000001.SZ'
    response = session.get(f'{BASE_URL}/stock/detail/{ts_code}/')
    print(f"响应状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        stock_detail = result.get('data', {})
        print(f"股票详情: {stock_detail.get('name')} ({stock_detail.get('ts_code')})")
        print(f"当前价: {stock_detail.get('current_price')}")
        print(f"涨跌幅: {stock_detail.get('pct_chg')}%")
        return True
    else:
        print(f"获取详情失败: {response.text}")
        return False


def test_account_info():
    """测试账户信息"""
    print("\n=== 测试账户信息 ===")
    
    response = session.get(f'{BASE_URL}/trading/account/')
    print(f"响应状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        account = result.get('data', {})
        print(f"账户余额: {account.get('account_balance')}")
        print(f"总资产: {account.get('total_assets')}")
        print(f"持仓数量: {account.get('position_count')}")
        return True
    else:
        print(f"获取账户信息失败: {response.text}")
        return False


def test_buy_stock():
    """测试买入股票"""
    print("\n=== 测试买入股票 ===")
    
    buy_data = {
        'ts_code': '000001.SZ',
        'price': 11.50,
        'shares': 100
    }
    
    response = session.post(
        f'{BASE_URL}/trading/buy/',
        data=json.dumps(buy_data),
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"响应状态: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"买入结果: {result.get('msg')}")
        if result.get('code') == 200:
            print(f"剩余余额: {result.get('data', {}).get('remaining_balance')}")
            return True
    else:
        print(f"买入失败: {response.text}")
    
    return False


def test_positions():
    """测试持仓查询"""
    print("\n=== 测试持仓查询 ===")
    
    response = session.get(f'{BASE_URL}/trading/positions/')
    print(f"响应状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        positions = result.get('data', {}).get('list', [])
        print(f"持仓数量: {len(positions)}")
        
        for pos in positions:
            print(f"  - {pos.get('ts_code')} {pos.get('stock_name')}")
            print(f"    持仓: {pos.get('position_shares')} 股")
            print(f"    成本价: {pos.get('cost_price')}")
            print(f"    市值: {pos.get('market_value')}")
        
        return True
    else:
        print(f"获取持仓失败: {response.text}")
        return False


def test_trade_records():
    """测试交易记录"""
    print("\n=== 测试交易记录 ===")
    
    response = session.get(f'{BASE_URL}/trading/records/')
    print(f"响应状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        records = result.get('data', {}).get('list', [])
        print(f"交易记录数量: {len(records)}")
        
        for record in records[:3]:  # 显示前3条
            print(f"  - {record.get('trade_time')} {record.get('trade_type_display')}")
            print(f"    {record.get('ts_code')} {record.get('stock_name')}")
            print(f"    价格: {record.get('trade_price')} 数量: {record.get('trade_shares')}")
        
        return True
    else:
        print(f"获取交易记录失败: {response.text}")
        return False


def test_watchlist():
    """测试自选股功能"""
    print("\n=== 测试自选股功能 ===")
    
    # 添加自选股
    add_data = {'ts_code': '000002.SZ'}
    response = session.post(
        f'{BASE_URL}/trading/watchlist/add/',
        data=json.dumps(add_data),
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"添加自选股响应: {response.status_code}")
    if response.status_code == 200:
        print("添加自选股成功")
    
    # 查看自选股列表
    response = session.get(f'{BASE_URL}/trading/watchlist/')
    print(f"查看自选股响应: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        watchlist = result.get('data', [])
        print(f"自选股数量: {len(watchlist)}")
        
        for item in watchlist:
            print(f"  - {item.get('ts_code')} {item.get('stock_name')}")
            print(f"    当前价: {item.get('current_price')} 涨跌幅: {item.get('pct_chg')}%")
        
        return True
    else:
        print(f"获取自选股失败: {response.text}")
        return False


def run_tests():
    """运行所有测试"""
    print("开始股票交易系统API测试")
    print("=" * 50)
    
    test_results = []
    
    # 登录测试
    if not test_user_login():
        print("登录失败，终止测试")
        return
    
    # 运行各项测试
    tests = [
        ("股票数据同步", test_stock_sync),
        ("股票列表", test_stock_list),
        ("股票详情", test_stock_detail),
        ("账户信息", test_account_info),
        ("买入股票", test_buy_stock),
        ("持仓查询", test_positions),
        ("交易记录", test_trade_records),
        ("自选股功能", test_watchlist),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"{test_name} 测试异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试总结
    print("\n" + "=" * 50)
    print("测试总结:")
    success_count = 0
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n总计: {success_count}/{len(test_results)} 项测试通过")
    
    if success_count == len(test_results):
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败，请检查")


if __name__ == '__main__':
    run_tests()