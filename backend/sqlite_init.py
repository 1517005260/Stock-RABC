import os
import sqlite3
import django
import sys

# 设置 Django 环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.db import connections

# 创建数据库目录（如果不存在）
for db_name in ['db.sqlite3', 'db_user.sqlite3']:
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)
    if not os.path.exists(db_path):
        # Create empty file
        open(db_path, 'a').close()
        print(f"Created empty database file: {db_path}")

# 应用所有迁移
print("Applying migrations...")
os.system('python manage.py migrate')

# 连接到 SQLite 数据库
conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db_user.sqlite3'))
cursor = conn.cursor()

# 创建表结构（这些应该由 Django migrate 命令创建）
print("Populating user data...")

# 插入 sys_user 表数据
user_data = [
    (1, 'python222', '123456', '20240906202303.jpg', 'caofeng2014@126.com', '18862857104', '2024-08-08', 1, '2024-08-08', '2024-08-08', '超级管理员'),
    (3, '1', '123456', '20240808230603.jpg', 'caofeng2014@126.com', '18862857104', '2024-08-08', 0, '2024-08-08', '2024-08-14', '测试用户'),
    (6, '4', '123456', '20240808230603.jpg', None, None, None, 1, None, None, None),
    (7, '5', '123456', '20240808230603.jpg', None, None, None, 1, None, None, None),
    (8, '6', '123456', '20240808230603.jpg', None, None, None, 0, None, None, None),
    (11, '9', '123456', '20240808230603.jpg', None, None, None, 1, None, None, None),
    (14, '666', '123456', 'default.jpg', 'caofeng2014@126.com', '18862857104', None, 1, '2024-08-13', None, '33'),
    (15, 'jack', '123456', 'default.jpg', 'caofeng2014@126.com', '18862857104', None, 1, '2024-08-13', '2024-09-06', '禁用用户测试4'),
    (16, '12323232', '123456', 'default.jpg', '1@126.com', '18862857104', None, 1, '2024-08-18', '2024-08-18', '115'),
    (17, 'marry', '123456', 'default.jpg', '111@qq.com', '15586521012', None, 1, '2024-09-05', None, '555')
]

for user in user_data:
    try:
        cursor.execute("""
        INSERT INTO sys_user (id, username, password, avatar, email, phonenumber, login_date, status, create_time, update_time, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, user)
    except sqlite3.IntegrityError as e:
        print(f"Error inserting user {user[1]}: {e}")

# 插入 sys_menu 表数据
menu_data = [
    (1, '系统管理', 'system', 0, 1, '/sys', '', 'M', '', '2024-07-04', '2024-07-04', '系统管理目录'),
    (2, '业务管理', 'monitor', 0, 2, '/bsns', '', 'M', '', '2024-07-04', '2024-07-04', '业务管理目录'),
    (3, '用户管理', 'user', 1, 1, '/sys/user', 'sys/user/index', 'C', 'system:user:list', '2024-07-04', '2024-07-04', '用户管理菜单'),
    (4, '角色管理', 'peoples', 1, 2, '/sys/role', 'sys/role/index', 'C', 'system:role:list', '2024-07-04', '2024-07-04', '角色管理菜单'),
    (5, '菜单管理', 'tree-table', 1, 3, '/sys/menu', 'sys/menu/index', 'C', 'system:menu:list', '2024-07-04', '2024-07-04', '菜单管理菜单'),
    (6, '部门管理', 'tree', 2, 1, '/bsns/department', 'bsns/Department', 'C', '', '2024-07-04', '2024-07-04', '部门管理菜单'),
    (7, '岗位管理', 'post', 2, 2, '/bsns/post', 'bsns/Post', 'C', '', '2024-07-04', '2024-07-04', '岗位管理菜单')
]

print("Populating menu data...")
for menu in menu_data:
    try:
        cursor.execute("""
        INSERT INTO sys_menu (id, name, icon, parent_id, order_num, path, component, menu_type, perms, create_time, update_time, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, menu)
    except sqlite3.IntegrityError as e:
        print(f"Error inserting menu {menu[1]}: {e}")

# 插入 sys_role 表数据
role_data = [
    (1, '超级管理员', 'admin', '2024-07-04', '2024-07-04', '拥有系统最高权限'),
    (2, '普通角色', 'common', '2024-07-04', '2024-07-04', '普通角色'),
    (3, '测试角色', 'test', '2024-07-04', '2024-07-04', '测试角色'),
    (4, '是', None, '2024-07-04', '2024-07-04', None),
    (5, '3', None, '2024-07-04', '2024-07-04', None),
    (6, '4', None, '2024-07-04', '2024-07-04', None),
    (19, '测2', 'cc2', '2024-07-04', '2024-07-04', 'eewew2'),
    (20, 'ccc测试', 'test2', '2024-07-04', '2024-07-04', 'xxx'),
    (21, '今天测试角色', 'todytest', '2024-07-04', '2024-07-04', 'ccc'),
    (22, '12', '123', '2024-07-04', '2024-08-29', '12')
]

print("Populating role data...")
for role in role_data:
    try:
        cursor.execute("""
        INSERT INTO sys_role (id, name, code, create_time, update_time, remark)
        VALUES (?, ?, ?, ?, ?, ?)
        """, role)
    except sqlite3.IntegrityError as e:
        print(f"Error inserting role {role[1]}: {e}")

# 插入 sys_role_menu 表数据
role_menu_data = [
    (102, 2, 2),
    (103, 6, 2),
    (104, 7, 2),
    (106, 1, 1),
    (107, 3, 1),
    (108, 4, 1),
    (109, 5, 1),
    (110, 2, 1),
    (111, 6, 1),
    (112, 7, 1),
    (114, 1, 6),
    (115, 5, 6),
    (116, 2, 6),
    (117, 6, 6),
    (118, 7, 6)
]

print("Populating role-menu relationship data...")
for role_menu in role_menu_data:
    try:
        cursor.execute("""
        INSERT INTO sys_role_menu (id, menu_id, role_id)
        VALUES (?, ?, ?)
        """, role_menu)
    except sqlite3.IntegrityError as e:
        print(f"Error inserting role_menu {role_menu}: {e}")

# 插入 sys_user_role 表数据
user_role_data = [
    (1, 1, 1),
    (2, 2, 1),
    (13, 5, 6),
    (17, 2, 6),
    (18, 3, 6),
    (19, 20, 6),
    (20, 2, 8),
    (21, 20, 8),
    (22, 5, 8),
    (23, 2, 17),
    (24, 2, 3),
    (25, 3, 3),
    (26, 4, 3),
    (27, 2, 15)
]

print("Populating user-role relationship data...")
for user_role in user_role_data:
    try:
        cursor.execute("""
        INSERT INTO sys_user_role (id, role_id, user_id)
        VALUES (?, ?, ?)
        """, user_role)
    except sqlite3.IntegrityError as e:
        print(f"Error inserting user_role {user_role}: {e}")

# 提交事务
conn.commit()
conn.close()

print("Database initialization completed!") 