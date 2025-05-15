import os
import sys
import django
from datetime import datetime

# 设置 Django 环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from user.models import SysUser
from role.models import SysRole, SysUserRole
from menu.models import SysMenu, SysRoleMenu

# 检查是否已有数据
if SysUser.objects.count() > 0:
    print("数据库已经初始化，跳过...")
    sys.exit(0)

# 创建用户数据
print("创建用户数据...")
user_data = [
    {'id': 1, 'username': 'superroot', 'password': '123456', 'avatar': '20240906202303.jpg', 
     'email': 'caofeng2014@126.com', 'phonenumber': '18862857104', 'login_date': datetime.now(), 
     'status': 1, 'create_time': datetime.now(), 'update_time': datetime.now(), 'remark': '超级管理员'},
    {'id': 3, 'username': '1', 'password': '123456', 'avatar': '20240808230603.jpg', 
     'email': 'caofeng2014@126.com', 'phonenumber': '18862857104', 'login_date': datetime.now(), 
     'status': 0, 'create_time': datetime.now(), 'update_time': datetime.now(), 'remark': '测试用户'},
    {'id': 6, 'username': '4', 'password': '123456', 'avatar': '20240808230603.jpg', 
     'status': 1},
    {'id': 7, 'username': '5', 'password': '123456', 'avatar': '20240808230603.jpg', 
     'status': 1},
    {'id': 8, 'username': '6', 'password': '123456', 'avatar': '20240808230603.jpg', 
     'status': 0},
    {'id': 11, 'username': '9', 'password': '123456', 'avatar': '20240808230603.jpg', 
     'status': 1},
    {'id': 14, 'username': '666', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'caofeng2014@126.com', 'phonenumber': '18862857104', 'status': 1, 
     'create_time': datetime.now(), 'remark': '33'},
    {'id': 15, 'username': 'jack', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'caofeng2014@126.com', 'phonenumber': '18862857104', 'status': 1, 
     'create_time': datetime.now(), 'update_time': datetime.now(), 'remark': '禁用用户测试4'},
    {'id': 16, 'username': '12323232', 'password': '123456', 'avatar': 'default.jpg', 
     'email': '1@126.com', 'phonenumber': '18862857104', 'status': 1, 
     'create_time': datetime.now(), 'update_time': datetime.now(), 'remark': '115'},
    {'id': 17, 'username': 'marry', 'password': '123456', 'avatar': 'default.jpg', 
     'email': '111@qq.com', 'phonenumber': '15586521012', 'status': 1, 
     'create_time': datetime.now(), 'remark': '555'}
]

for user_info in user_data:
    try:
        user = SysUser(**user_info)
        user.save()
        print(f"用户 {user.username} 创建成功")
    except Exception as e:
        print(f"创建用户 {user_info['username']} 失败: {e}")

# 创建菜单数据
print("\n创建菜单数据...")
menu_data = [
    {'id': 1, 'name': '系统管理', 'icon': 'system', 'parent_id': 0, 'order_num': 1, 
     'path': '/sys', 'component': '', 'menu_type': 'M', 'perms': '', 
     'create_time': datetime.now(), 'update_time': datetime.now(), 'remark': '系统管理目录'},
    {'id': 2, 'name': '业务管理', 'icon': 'monitor', 'parent_id': 0, 'order_num': 2, 
     'path': '/bsns', 'component': '', 'menu_type': 'M', 'perms': '', 
     'create_time': datetime.now(), 'update_time': datetime.now(), 'remark': '业务管理目录'},
    {'id': 3, 'name': '用户管理', 'icon': 'user', 'parent_id': 1, 'order_num': 1, 
     'path': '/sys/user', 'component': 'sys/user/index', 'menu_type': 'C', 
     'perms': 'system:user:list', 'create_time': datetime.now(), 'update_time': datetime.now(), 
     'remark': '用户管理菜单'},
    {'id': 4, 'name': '角色管理', 'icon': 'peoples', 'parent_id': 1, 'order_num': 2, 
     'path': '/sys/role', 'component': 'sys/role/index', 'menu_type': 'C', 
     'perms': 'system:role:list', 'create_time': datetime.now(), 'update_time': datetime.now(), 
     'remark': '角色管理菜单'},
    {'id': 5, 'name': '菜单管理', 'icon': 'tree-table', 'parent_id': 1, 'order_num': 3, 
     'path': '/sys/menu', 'component': 'sys/menu/index', 'menu_type': 'C', 
     'perms': 'system:menu:list', 'create_time': datetime.now(), 'update_time': datetime.now(), 
     'remark': '菜单管理菜单'},
    {'id': 6, 'name': '部门管理', 'icon': 'tree', 'parent_id': 2, 'order_num': 1, 
     'path': '/bsns/department', 'component': 'bsns/Department', 'menu_type': 'C', 
     'perms': '', 'create_time': datetime.now(), 'update_time': datetime.now(), 
     'remark': '部门管理菜单'},
    {'id': 7, 'name': '岗位管理', 'icon': 'post', 'parent_id': 2, 'order_num': 2, 
     'path': '/bsns/post', 'component': 'bsns/Post', 'menu_type': 'C', 'perms': '', 
     'create_time': datetime.now(), 'update_time': datetime.now(), 'remark': '岗位管理菜单'}
]

for menu_info in menu_data:
    try:
        menu = SysMenu(**menu_info)
        menu.save()
        print(f"菜单 {menu.name} 创建成功")
    except Exception as e:
        print(f"创建菜单 {menu_info['name']} 失败: {e}")

# 创建角色数据
print("\n创建角色数据...")
role_data = [
    {'id': 1, 'name': '超级管理员', 'code': 'admin', 'create_time': datetime.now(), 
     'update_time': datetime.now(), 'remark': '拥有系统最高权限'},
    {'id': 2, 'name': '普通角色', 'code': 'common', 'create_time': datetime.now(), 
     'update_time': datetime.now(), 'remark': '普通角色'},
    {'id': 3, 'name': '测试角色', 'code': 'test', 'create_time': datetime.now(), 
     'update_time': datetime.now(), 'remark': '测试角色'},
    {'id': 4, 'name': '是', 'create_time': datetime.now(), 'update_time': datetime.now()},
    {'id': 5, 'name': '3', 'create_time': datetime.now(), 'update_time': datetime.now()},
    {'id': 6, 'name': '4', 'create_time': datetime.now(), 'update_time': datetime.now()},
    {'id': 19, 'name': '测2', 'code': 'cc2', 'create_time': datetime.now(), 
     'update_time': datetime.now(), 'remark': 'eewew2'},
    {'id': 20, 'name': 'ccc测试', 'code': 'test2', 'create_time': datetime.now(), 
     'update_time': datetime.now(), 'remark': 'xxx'},
    {'id': 21, 'name': '今天测试角色', 'code': 'todytest', 'create_time': datetime.now(), 
     'update_time': datetime.now(), 'remark': 'ccc'},
    {'id': 22, 'name': '12', 'code': '123', 'create_time': datetime.now(), 
     'update_time': datetime.now(), 'remark': '12'}
]

for role_info in role_data:
    try:
        role = SysRole(**role_info)
        role.save()
        print(f"角色 {role.name} 创建成功")
    except Exception as e:
        print(f"创建角色 {role_info['name']} 失败: {e}")

# 创建角色-菜单关联
print("\n创建角色-菜单关联数据...")
role_menu_data = [
    {'id': 102, 'menu_id': 2, 'role_id': 2},
    {'id': 103, 'menu_id': 6, 'role_id': 2},
    {'id': 104, 'menu_id': 7, 'role_id': 2},
    {'id': 106, 'menu_id': 1, 'role_id': 1},
    {'id': 107, 'menu_id': 3, 'role_id': 1},
    {'id': 108, 'menu_id': 4, 'role_id': 1},
    {'id': 109, 'menu_id': 5, 'role_id': 1},
    {'id': 110, 'menu_id': 2, 'role_id': 1},
    {'id': 111, 'menu_id': 6, 'role_id': 1},
    {'id': 112, 'menu_id': 7, 'role_id': 1},
    {'id': 114, 'menu_id': 1, 'role_id': 6},
    {'id': 115, 'menu_id': 5, 'role_id': 6},
    {'id': 116, 'menu_id': 2, 'role_id': 6},
    {'id': 117, 'menu_id': 6, 'role_id': 6},
    {'id': 118, 'menu_id': 7, 'role_id': 6}
]

for role_menu_info in role_menu_data:
    try:
        menu = SysMenu.objects.get(id=role_menu_info['menu_id'])
        role = SysRole.objects.get(id=role_menu_info['role_id'])
        role_menu = SysRoleMenu(id=role_menu_info['id'], menu=menu, role=role)
        role_menu.save()
        print(f"角色菜单关联 {role_menu.id} 创建成功")
    except Exception as e:
        print(f"创建角色菜单关联 {role_menu_info['id']} 失败: {e}")

# 创建用户-角色关联
print("\n创建用户-角色关联数据...")
user_role_data = [
    {'id': 1, 'role_id': 1, 'user_id': 1},
    {'id': 2, 'role_id': 2, 'user_id': 1},
    {'id': 13, 'role_id': 5, 'user_id': 6},
    {'id': 17, 'role_id': 2, 'user_id': 6},
    {'id': 18, 'role_id': 3, 'user_id': 6},
    {'id': 19, 'role_id': 20, 'user_id': 6},
    {'id': 20, 'role_id': 2, 'user_id': 8},
    {'id': 21, 'role_id': 20, 'user_id': 8},
    {'id': 22, 'role_id': 5, 'user_id': 8},
    {'id': 23, 'role_id': 2, 'user_id': 17},
    {'id': 24, 'role_id': 2, 'user_id': 3},
    {'id': 25, 'role_id': 3, 'user_id': 3},
    {'id': 26, 'role_id': 4, 'user_id': 3},
    {'id': 27, 'role_id': 2, 'user_id': 15}
]

for user_role_info in user_role_data:
    try:
        user = SysUser.objects.get(id=user_role_info['user_id'])
        role = SysRole.objects.get(id=user_role_info['role_id'])
        user_role = SysUserRole(id=user_role_info['id'], user=user, role=role)
        user_role.save()
        print(f"用户角色关联 {user_role.id} 创建成功")
    except Exception as e:
        print(f"创建用户角色关联 {user_role_info['id']} 失败: {e}")

print("\n数据库初始化完成!")