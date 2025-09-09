#!/usr/bin/env python
"""
初始化测试数据脚本
创建测试用户和角色数据
"""

import os
import sys
import hashlib
from datetime import datetime

# 添加Django项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

import django
django.setup()

from user.models import SysUser
from role.models import SysRole, SysUserRole
from trading.models import UserStockAccount


def create_roles():
    """创建角色数据"""
    print("创建角色数据...")
    
    roles = [
        {'name': '普通用户', 'code': 'user', 'remark': '基础交易功能权限'},
        {'name': '管理员', 'code': 'admin', 'remark': '用户管理和数据查看权限'},
        {'name': '超级管理员', 'code': 'superadmin', 'remark': '系统管理和所有权限'},
    ]
    
    created_roles = []
    for role_data in roles:
        role, created = SysRole.objects.get_or_create(
            code=role_data['code'],
            defaults={
                'name': role_data['name'],
                'remark': role_data['remark'],
                'create_time': datetime.now(),
                'update_time': datetime.now(),
            }
        )
        created_roles.append(role)
        if created:
            print(f"  创建角色: {role.name}")
        else:
            print(f"  角色已存在: {role.name}")
    
    return created_roles


def create_users():
    """创建测试用户"""
    print("\n创建测试用户...")
    
    users = [
        {
            'username': 'python222',
            'password': '123456',
            'email': 'admin@example.com',
            'role': 'superadmin',
            'remark': '系统超级管理员'
        },
        {
            'username': 'admin001', 
            'password': '123456',
            'email': 'admin001@example.com',
            'role': 'admin',
            'remark': '测试管理员'
        },
        {
            'username': 'trader001',
            'password': '123456',
            'email': 'trader001@example.com', 
            'role': 'user',
            'remark': '测试普通用户'
        },
        {
            'username': 'trader002',
            'password': '123456',
            'email': 'trader002@example.com',
            'role': 'user', 
            'remark': '测试普通用户2'
        }
    ]
    
    created_users = []
    for user_data in users:
        # 密码MD5加密
        password_md5 = hashlib.md5(user_data['password'].encode()).hexdigest()
        
        user, created = SysUser.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'password': password_md5,
                'email': user_data['email'],
                'status': 0,  # 正常状态
                'create_time': datetime.now(),
                'update_time': datetime.now(),
                'remark': user_data['remark']
            }
        )
        
        created_users.append((user, user_data['role']))
        if created:
            print(f"  创建用户: {user.username} ({user_data['role']})")
        else:
            print(f"  用户已存在: {user.username}")
    
    return created_users


def assign_roles(users_with_roles):
    """分配用户角色"""
    print("\n分配用户角色...")
    
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
            print(f"  角色 {role_code} 不存在，跳过用户 {user.username}")


def create_stock_accounts(users_with_roles):
    """为用户创建股票账户"""
    print("\n创建股票账户...")
    
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


def main():
    """主函数"""
    print("=== 初始化测试数据 ===")
    
    try:
        # 创建角色
        roles = create_roles()
        
        # 创建用户
        users_with_roles = create_users()
        
        # 分配角色
        assign_roles(users_with_roles)
        
        # 创建股票账户
        create_stock_accounts(users_with_roles)
        
        print("\n=== 初始化完成 ===")
        print("测试账号信息:")
        print("  超级管理员: python222 / 123456")
        print("  管理员: admin001 / 123456") 
        print("  普通用户: trader001 / 123456")
        print("  普通用户: trader002 / 123456")
        
    except Exception as e:
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()