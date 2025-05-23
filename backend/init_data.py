import os
import sys
import django
from django.utils import timezone

# 设置 Django 环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from user.models import SysUser
from role.models import SysRole, SysUserRole
# from menu.models import SysMenu, SysRoleMenu

# 检查是否已有数据
if SysUser.objects.count() > 0:
    print("数据库已经初始化，跳过...")
    sys.exit(0)

# 创建用户数据
print("创建用户数据...")
current_time = timezone.now()
user_data = [
    {'id': 1, 'username': 'superroot', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'admin@example.com', 'phonenumber': '18862857104', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '超级管理员'},
    {'id': 2, 'username': 'admin', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'manager@example.com', 'phonenumber': '18862857104', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '管理员'},
    {'id': 3, 'username': 'user', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'user@example.com', 'phonenumber': '15586521012', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '普通用户'},
    {'id': 4, 'username': 'zhangsan', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'zhangsan@example.com', 'phonenumber': '13512345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '销售部门'},
    {'id': 5, 'username': 'lisi', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'lisi@example.com', 'phonenumber': '13612345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '市场部门'},
    {'id': 6, 'username': 'wangwu', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'wangwu@example.com', 'phonenumber': '13712345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '技术部门'},
    {'id': 7, 'username': 'zhaoliu', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'zhaoliu@example.com', 'phonenumber': '13812345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '财务部门'},
    {'id': 8, 'username': 'sunqi', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'sunqi@example.com', 'phonenumber': '13912345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '人事部门'},
    {'id': 9, 'username': 'zhouba', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'zhouba@example.com', 'phonenumber': '15012345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '运营部门'},
    {'id': 10, 'username': 'wujiu', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'wujiu@example.com', 'phonenumber': '15112345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '客服部门'},
    {'id': 11, 'username': 'zhengshi', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'zhengshi@example.com', 'phonenumber': '15212345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '销售经理'},
    {'id': 12, 'username': 'wangshiyi', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'wangshiyi@example.com', 'phonenumber': '15312345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '技术总监'},
    {'id': 13, 'username': 'lishier', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'lishier@example.com', 'phonenumber': '15412345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '产品经理'},
    {'id': 14, 'username': 'zhaoshisan', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'zhaoshisan@example.com', 'phonenumber': '15512345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': 'UI设计师'},
    {'id': 15, 'username': 'qianshisi', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'qianshisi@example.com', 'phonenumber': '15612345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '前端工程师'},
    {'id': 16, 'username': 'sunshiwu', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'sunshiwu@example.com', 'phonenumber': '15712345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '后端工程师'},
    {'id': 17, 'username': 'zhoushiliu', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'zhoushiliu@example.com', 'phonenumber': '15812345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '测试工程师'},
    {'id': 18, 'username': 'wushiqi', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'wushiqi@example.com', 'phonenumber': '15912345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '运维工程师'},
    {'id': 19, 'username': 'zhengshiba', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'zhengshiba@example.com', 'phonenumber': '16012345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '数据分析师'},
    {'id': 20, 'username': 'wangshijiu', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'wangshijiu@example.com', 'phonenumber': '16112345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '市场专员'},
    {'id': 21, 'username': 'liershiyi', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'liershiyi@example.com', 'phonenumber': '16212345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '人力资源'},
    {'id': 22, 'username': 'zhaoershier', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'zhaoershier@example.com', 'phonenumber': '16312345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '财务专员'},
    {'id': 23, 'username': 'qianershisan', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'qianershisan@example.com', 'phonenumber': '16412345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '行政助理'},
    {'id': 24, 'username': 'sunershisi', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'sunershisi@example.com', 'phonenumber': '16512345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '销售助理'},
    {'id': 25, 'username': 'zhouershiwu', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'zhouershiwu@example.com', 'phonenumber': '16612345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '技术助理'},
    {'id': 26, 'username': 'wuershiliu', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'wuershiliu@example.com', 'phonenumber': '16712345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '实习生'},
    {'id': 27, 'username': 'zhengershiqi', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'zhengershiqi@example.com', 'phonenumber': '16812345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '客户经理'},
    {'id': 28, 'username': 'wangershiba', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'wangershiba@example.com', 'phonenumber': '16912345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '项目经理'},
    {'id': 29, 'username': 'liershijiu', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'liershijiu@example.com', 'phonenumber': '17012345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '产品助理'},
    {'id': 30, 'username': 'zhaosanshi', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'zhaosanshi@example.com', 'phonenumber': '17112345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '研发工程师'},
    {'id': 31, 'username': 'qiansanshiyi', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'qiansanshiyi@example.com', 'phonenumber': '17212345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '算法工程师'},
    {'id': 32, 'username': 'sunsanshier', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'sunsanshier@example.com', 'phonenumber': '17312345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '全栈工程师'},
    {'id': 33, 'username': 'zhousanshisan', 'password': '123456', 'avatar': 'default.jpg', 
     'email': 'zhousanshisan@example.com', 'phonenumber': '17412345678', 'login_date': current_time, 
     'status': 1, 'create_time': current_time, 'update_time': current_time, 'remark': '安全工程师'}
]

for user_info in user_data:
    try:
        user = SysUser(**user_info)
        user.save()
        print(f"用户 {user.username} 创建成功")
    except Exception as e:
        print(f"创建用户 {user_info['username']} 失败: {e}")

# 创建角色数据
print("\n创建角色数据...")
role_data = [
    {'id': 1, 'name': '超级管理员', 'code': 'superadmin', 'create_time': current_time, 
     'update_time': current_time, 'remark': '拥有系统最高权限，能分配角色并管理用户'},
    {'id': 2, 'name': '管理员', 'code': 'admin', 'create_time': current_time, 
     'update_time': current_time, 'remark': '可以增删改查用户'},
    {'id': 3, 'name': '普通用户', 'code': 'user', 'create_time': current_time, 
     'update_time': current_time, 'remark': '只能查看自己的信息和权限'}
]

for role_info in role_data:
    try:
        role = SysRole(**role_info)
        role.save()
        print(f"角色 {role.name} 创建成功")
    except Exception as e:
        print(f"创建角色 {role_info['name']} 失败: {e}")

# 创建用户-角色关联
print("\n创建用户-角色关联数据...")
user_role_data = [
    {'id': 1, 'role_id': 1, 'user_id': 1},  # superroot是超级管理员
    {'id': 2, 'role_id': 2, 'user_id': 2},  # admin是管理员
    {'id': 3, 'role_id': 3, 'user_id': 3},  # user是普通用户
    {'id': 4, 'role_id': 3, 'user_id': 4},  # zhangsan是普通用户
    {'id': 5, 'role_id': 3, 'user_id': 5},  # lisi是普通用户
    {'id': 6, 'role_id': 3, 'user_id': 6},  # wangwu是普通用户
    {'id': 7, 'role_id': 3, 'user_id': 7},  # zhaoliu是普通用户
    {'id': 8, 'role_id': 3, 'user_id': 8},  # sunqi是普通用户
    {'id': 9, 'role_id': 3, 'user_id': 9},  # zhouba是普通用户
    {'id': 10, 'role_id': 3, 'user_id': 10},  # wujiu是普通用户
    {'id': 11, 'role_id': 2, 'user_id': 11},  # zhengshi是管理员 (销售经理)
    {'id': 12, 'role_id': 2, 'user_id': 12},  # wangshiyi是管理员 (技术总监)
    {'id': 13, 'role_id': 2, 'user_id': 13},  # lishier是管理员 (产品经理)
    {'id': 14, 'role_id': 3, 'user_id': 14},  # zhaoshisan是普通用户
    {'id': 15, 'role_id': 3, 'user_id': 15},  # qianshisi是普通用户
    {'id': 16, 'role_id': 3, 'user_id': 16},  # sunshiwu是普通用户
    {'id': 17, 'role_id': 3, 'user_id': 17},  # zhoushiliu是普通用户
    {'id': 18, 'role_id': 3, 'user_id': 18},  # wushiqi是普通用户
    {'id': 19, 'role_id': 3, 'user_id': 19},  # zhengshiba是普通用户
    {'id': 20, 'role_id': 3, 'user_id': 20},  # wangshijiu是普通用户
    {'id': 21, 'role_id': 2, 'user_id': 21},  # liershiyi是管理员 (人力资源)
    {'id': 22, 'role_id': 2, 'user_id': 22},  # zhaoershier是管理员 (财务专员)
    {'id': 23, 'role_id': 3, 'user_id': 23},  # qianershisan是普通用户
    {'id': 24, 'role_id': 3, 'user_id': 24},  # sunershisi是普通用户
    {'id': 25, 'role_id': 3, 'user_id': 25},  # zhouershiwu是普通用户
    {'id': 26, 'role_id': 3, 'user_id': 26},  # wuershiliu是普通用户
    {'id': 27, 'role_id': 2, 'user_id': 27},  # zhengershiqi是管理员 (客户经理)
    {'id': 28, 'role_id': 2, 'user_id': 28},  # wangershiba是管理员 (项目经理)
    {'id': 29, 'role_id': 3, 'user_id': 29},  # liershijiu是普通用户
    {'id': 30, 'role_id': 3, 'user_id': 30},  # zhaosanshi是普通用户
    {'id': 31, 'role_id': 3, 'user_id': 31},  # qiansanshiyi是普通用户
    {'id': 32, 'role_id': 3, 'user_id': 32},  # sunsanshier是普通用户
    {'id': 33, 'role_id': 3, 'user_id': 33}   # zhousanshisan是普通用户
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