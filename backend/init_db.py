import os
import sys
import django

# 设置 Django 环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

# 创建空数据库文件
for db_name in ['db.sqlite3', 'db_user.sqlite3']:
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)
    if not os.path.exists(db_path):
        open(db_path, 'a').close()
        print(f"创建数据库文件: {db_path}")

# 分别为每个数据库应用迁移
from django.core.management import call_command

# 为主数据库应用迁移
print("为主数据库应用迁移...")
call_command('migrate', '--database=default')

# 为用户数据库应用迁移
print("为用户数据库应用迁移...")
call_command('migrate', 'user', '--database=db_user')
call_command('migrate', 'role', '--database=db_user')
call_command('migrate', 'menu', '--database=db_user')

print("数据库迁移完成！")