# Django RBAC 后台系统

这是一个基于 Django 实现的 RBAC（基于角色的访问控制）后台管理系统，提供了用户、角色、菜单权限管理等核心功能。本系统使用 JWT 进行身份验证，支持跨域请求，适合作为前后端分离架构下的权限管理系统。

## 技术栈

- **Python**: 3.10+
- **Django**: 5.1.1
- **Django REST Framework**: 3.14.0
- **JWT 认证**: djangorestframework-jwt 1.11.0
- **数据库**: SQLite（可扩展至 PostgreSQL 等）
- **跨域支持**: django-cors-headers 4.7.0

## 安装与启动

### 前提条件

- Python 3.10 或更高版本
- pip 包管理工具
- 虚拟环境工具(推荐使用 venv 或 conda)

### 步骤 1: 克隆仓库

```bash
git clone https://github.com/1517005260/Mini-RABC.git
cd Mini-RABC/backend
```

### 步骤 2: 创建并激活虚拟环境

```bash
conda create -n rabc python==3.10
```

### 步骤 3: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 4: 初始化数据库

```bash
# 执行数据库迁移
python init_db.py

# 初始化数据库数据
python init_data.py
```

### 步骤 5: 启动服务器

```bash
python manage.py runserver
```

此时，服务器将在 `http://localhost:8000/` 运行。

## 项目架构

```
backend/
├── app/                  # 主应用配置
├── menu/                 # 菜单管理模块
├── role/                 # 角色管理模块
├── user/                 # 用户管理模块
├── utils/                # 工具类
├── manage.py             # Django管理脚本
├── requirements.txt      # 项目依赖
└── sqlite_init.py        # 数据库初始化脚本
```

## 核心功能实现

### 1. 用户管理 (user)

用户模块实现了用户的基本管理功能，包括：

- **用户认证**: 基于 JWT 的登录认证
- **用户 CRUD**: 创建、查询、更新、删除用户
- **密码管理**: 重置密码、修改密码
- **用户状态管理**: 启用/禁用用户
- **角色分配**: 给用户分配角色

#### 实现思路

- 使用 Django 的内置用户模型进行扩展
- JWT 认证流程：用户登录 → 生成 token → 请求时带上 token 进行身份验证
- 自定义中间件`JwtAuthenticationMiddleware`拦截请求，验证 JWT token

### 2. 角色管理 (role)

角色模块实现了角色权限的管理，包括：

- **角色 CRUD**: 创建、查询、更新、删除角色
- **角色权限管理**: 给角色分配菜单权限
- **用户角色关联**: 与用户进行多对多关联

#### 实现思路

- 角色与用户通过`SysUserRole`中间表实现多对多关系
- 角色与菜单通过`SysRoleMenu`中间表实现多对多关系
- 提供角色列表、搜索、授权等 API 接口

### 3. 菜单管理 (menu)

菜单模块实现了系统菜单及权限的管理，包括：

- **菜单 CRUD**: 创建、查询、更新、删除菜单
- **树状结构**: 构建菜单树状结构
- **权限标识**: 设置菜单对应的权限标识

#### 实现思路

- 使用 parent_id 实现菜单的树状结构
- 菜单类型区分为：目录(M)、菜单(C)、按钮(F)
- 通过`buildTreeMenu`方法递归构建菜单树
- Django 序列化器`SysMenuSerializer`处理嵌套菜单数据

### 4. 数据库路由 (utils.router)

实现了多数据库的路由机制：

- **数据库路由**: 将不同应用的模型映射到不同的数据库
- **分库设计**: 用户相关表放在单独的数据库中

#### 实现思路

- 通过自定义的`DatabaseAppsRouter`类，实现对不同应用的数据库路由
- 在`settings.py`中配置数据库映射关系
- 重写`db_for_read`、`db_for_write`等方法控制数据库的读写行为

## API 接口概览

### 用户相关接口

- `POST /user/login`: 用户登录
- `POST /user/save`: 添加/修改用户
- `POST /user/updateUserPwd`: 修改密码
- `POST /user/uploadImage`: 上传头像
- `POST /user/updateAvatar`: 更新头像
- `GET /user/action`: 获取用户信息
- `DELETE /user/action`: 删除用户
- `POST /user/search`: 用户分页查询
- `GET /user/resetPassword`: 重置密码
- `POST /user/status`: 修改用户状态
- `POST /user/grantRole`: 角色授权

### 角色相关接口

- `GET /role/listAll`: 获取所有角色
- `POST /role/search`: 角色分页查询
- `POST /role/save`: 添加/修改角色
- `GET /role/action`: 获取角色信息
- `DELETE /role/action`: 删除角色
- `GET /role/menus`: 获取角色菜单
- `POST /role/grant`: 角色菜单授权

### 菜单相关接口

- `GET /menu/treeList`: 获取菜单树
- `POST /menu/save`: 添加/修改菜单
- `GET /menu/action`: 获取菜单信息
- `DELETE /menu/action`: 删除菜单

## 安全实现

1. **JWT 认证**: 使用 JWT 进行无状态身份验证
2. **路由拦截**: 自定义中间件拦截非白名单请求进行 token 验证
3. **CORS 配置**: 使用 django-cors-headers 处理跨域请求
4. **角色权限**: 基于角色的访问控制机制

## 数据初始化

使用`sqlite_init.py`脚本初始化系统数据，包括：

- 预设用户数据（管理员、测试用户等）
- 基础菜单数据（系统管理、用户管理、角色管理等）
- 角色数据（超级管理员、普通角色等）
- 角色-菜单、用户-角色关联数据

## 注意事项

1. 生产环境部署时请修改`SECRET_KEY`并关闭`DEBUG`模式
2. 默认超级管理员账号：`python222`，密码：`123456`
3. 如需连接 PostgreSQL 等数据库，请安装相应的数据库驱动并修改 settings.py 中的数据库配置
4. 项目默认使用 SQLite 数据库，支持多库配置
