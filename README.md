# RBAC权限管理系统

这是一个基于Django + Vue3的RBAC (Role-Based Access Control) 权限管理系统，集成了AI聊天功能。系统采用前后端分离架构，提供完善的用户、角色、权限管理功能。

## 项目概述

- **前端技术栈**：Vue 3 + Element Plus + Vuex + Vue Router + Axios
- **后端技术栈**：Django + Django REST Framework + JWT + SQLite
- **AI聊天功能**：集成OpenAI API的流式对话功能

## RBAC基本原理

RBAC（Role-Based Access Control，基于角色的访问控制）是一种通过角色关联用户和权限的访问控制模型。其核心原理如下：

1. **用户（User）**: 系统的使用者，可以是个人、组织或自动化系统等。
2. **角色（Role）**: 用户在组织中的职责或工作岗位，一个用户可以拥有多个角色。
3. **权限（Permission）**: 对特定资源执行特定操作的能力，在本系统中通过菜单和功能点体现。
4. **会话（Session）**: 用户登录系统时创建，包含用户所有激活角色的权限集合。

RBAC的主要优势：
- **简化权限管理**: 通过分配角色而非直接分配权限，大幅降低权限管理的复杂度。
- **职责分离**: 可以基于职责来设计角色，符合最小权限原则。
- **易于审计**: 通过角色关系可以方便地查看和审计谁拥有什么权限。
- **可扩展性**: 在用户和权限数量增加时，仍然可以保持管理的简洁性。

本系统实现了RBAC模型的核心功能，包括用户-角色分配、角色-权限分配，以及基于这些关联关系的权限验证流程。

## 系统功能

- 用户管理：用户CRUD、密码管理、状态管理
- 角色管理：角色CRUD、角色授权
- 菜单管理：菜单CRUD、树状结构
- 权限控制：基于RBAC模型的访问控制
- AI聊天：与GPT模型的流式对话功能

## 软件架构设计

### 系统架构图

```
+---------------+        +---------------+        +---------------+
|               |        |               |        |               |
|    前端       |<------>|    后端API    |<------>|  OpenAI API   |
|  (Vue 3)      |  HTTP  |  (Django)     |  HTTP  |               |
|               |        |               |        |               |
+---------------+        +---------------+        +---------------+
                                |
                                |
                         +---------------+
                         |               |
                         |   数据库      |
                         |  (SQLite)     |
                         |               |
                         +---------------+
```

### ER图 (实体关系图)

```
+---------------+      +----------------+      +---------------+
|    User       |      |    UserRole    |      |    Role       |
+---------------+      +----------------+      +---------------+
| id            |<---->| user_id        |<---->| id            |
| username      |      | role_id        |      | name          |
| password      |      +----------------+      | status        |
| status        |                              | sort          |
| avatar        |                              | remark        |
| email         |                              | create_time   |
| create_time   |                              | update_time   |
+---------------+                              +---------------+
                                                      |
                                                      |
                                              +----------------+      +---------------+
                                              |   RoleMenu     |      |    Menu       |
                                              +----------------+      +---------------+
                                              | role_id        |<---->| id            |
                                              | menu_id        |      | name          |
                                              +----------------+      | path          |
                                                                     | parent_id     |
                                                                     | type          |
                                                                     | icon          |
                                                                     | component     |
                                                                     | perms         |
                                                                     | sort          |
                                                                     | visible       |
                                                                     +---------------+
+---------------+      
|  ChatMessage  |      
+---------------+      
| id            |      
| user_id       |<----+ (关联到User)
| content       |      
| response      |      
| create_time   |      
+---------------+      
```

### UML类图

```
+------------------+        +------------------+        +------------------+
|     SysUser      |        |     SysRole      |        |     SysMenu      |
+------------------+        +------------------+        +------------------+
| -id: Integer     |        | -id: Integer     |        | -id: Integer     |
| -username: String|        | -name: String    |        | -name: String    |
| -password: String|        | -status: Boolean |        | -path: String    |
| -status: Boolean |        | -sort: Integer   |        | -parent_id: Int  |
| -avatar: String  |        | -remark: String  |        | -type: String    |
| -email: String   |        | -create_time     |        | -icon: String    |
| -create_time     |        | -update_time     |        | -component: Str  |
+------------------+        +------------------+        | -perms: String   |
      ^ |                          ^ |                  | -sort: Integer   |
      | |                          | |                  | -visible: Bool   |
      | |                          | |                  +------------------+
      | |                          | |                          ^ |
      | |                          | |                          | |
      | v                          | v                          | v
+------------------+        +------------------+        
| SysUserRole     |        | SysRoleMenu      |        
+------------------+        +------------------+        
| -user_id: FK     |        | -role_id: FK     |        
| -role_id: FK     |        | -menu_id: FK     |        
+------------------+        +------------------+        
```

### 流程图：用户权限验证流程

```
+-------------+     +-------------+     +----------------+     +--------------+
|  用户登录   |---->| 后端验证    |---->| 生成JWT Token  |---->| 返回用户信息  |
+-------------+     +-------------+     +----------------+     +--------------+
                                                                      |
                                                                      v
+-------------+     +-------------+     +----------------+     +--------------+
| 前端保存    |<----| 保存Token   |<----| 保存菜单权限   |<----| 保存用户角色  |
| 状态        |     | 到Storage   |     | 到Storage      |     | 到Storage     |
+-------------+     +-------------+     +----------------+     +--------------+
       |
       v
+-------------+     +-------------+     +----------------+     +--------------+
| 用户请求    |---->| 前端拦截    |---->| 附加Token到    |---->| 发送请求      |
| 资源        |     | 请求        |     | 请求头         |     |               |
+-------------+     +-------------+     +----------------+     +--------------+
                                                                      |
                                                                      v
+-------------+     +-------------+     +----------------+     +--------------+
| 允许访问    |<----| 验证通过    |<----| 后端验证Token  |<----| 后端接收请求  |
| 资源        |     |             |     | 和权限         |     |               |
+-------------+     +-------------+     +----------------+     +--------------+
```

## 目录结构

项目分为前端和后端两部分：

- **frontend/**: Vue 3前端项目
- **backend/**: Django后端项目

每个部分都有自己的README文件，详细说明了安装、配置和实现思路。

## 如何开始

### 前置要求

1. Python 3.10+
2. Node.js 16+
3. Redis 服务器

### 快速启动指南

#### 1. 克隆仓库并安装依赖
```bash
git clone <repository-url>
cd Mini-RABC

# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install
```

#### 2. 启动Redis服务器

**Windows系统**：
```bash
# 下载并安装Redis for Windows
# https://github.com/microsoftarchive/redis/releases
# 或使用Chocolatey安装：
choco install redis-64

# 启动Redis服务
redis-server

# 验证Redis是否正常运行
redis-cli ping
# 应该返回：PONG
```

**Linux/macOS系统**：
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# macOS (使用Homebrew)
brew install redis
brew services start redis

# 验证Redis是否正常运行
redis-cli ping
# 应该返回：PONG
```

#### 3. 初始化后端系统
```bash
cd backend

# 一键初始化数据库、用户数据和市场数据缓存
python init_system.py
```

#### 4. 配置定时任务（可选 - 用于自动更新市场数据）

```bash
# 添加定时任务到系统crontab
python manage.py crontab add

# 查看已添加的定时任务
python manage.py crontab show

# 移除定时任务（如需要）
python manage.py crontab remove
```

#### 5. 启动完整系统（四个服务）

**Windows系统完整启动流程**：

**第一步：启动Redis服务器**
```bash
# Redis应该已经作为Windows服务运行，检查状态：
redis-cli ping
# 应该返回：PONG

# 如果Redis未运行，手动启动：
redis-server
```

**第二步：启动Django后端服务器**
```bash
cd backend

# 启动HTTP服务器
python manage.py runserver

# 后端将在 http://localhost:8000 运行
```

**第三步：启动前端开发服务器**
```bash
# 打开新的终端窗口
cd frontend

# 启动前端开发服务器
npm run serve

# 前端将在 http://localhost:8080 运行
```

**第四步：启动市场数据自动更新器（Windows专用）**
```bash
# 打开新的终端窗口
cd backend

# 方式1：使用批处理脚本（推荐）
start_market_updater.bat

# 方式2：直接运行Python脚本
# 30分钟自动更新（推荐）
python windows_market_updater.py

# 立即更新一次
python windows_market_updater.py --once

# 自定义15分钟更新间隔
python windows_market_updater.py --interval 15
```

**系统架构概览**：
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  前端服务器     │    │  后端API服务器  │    │  Redis缓存服务  │
│  :8080          │◄──►│  :8000          │◄──►│  :6379          │
│  npm run serve  │    │  python manage  │    │  redis-server   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              ▲
                              │
                    ┌─────────────────┐
                    │  市场数据更新器 │
                    │  每30分钟更新   │
                    │  windows_market │
                    │  _updater.py    │
                    └─────────────────┘
```

#### 6. 访问系统

- 前端页面：http://localhost:8080
- 后端API：http://localhost:8000
- Redis缓存状态：http://localhost:8000/stock/market/cache/status/

**快速验证系统是否正常运行**：
1. 访问前端页面，检查市场指数显示是否正常
2. 查看涨跌分布数据是否实时更新
3. 检查资金流向数据是否非零
4. 后端日志应显示市场数据更新信息

### 测试账号

系统初始化后提供以下测试账号：

- **超级管理员**: `python222` / `123456`
- **管理员**: `admin001` / `123456`
- **普通用户1**: `trader001` / `123456`
- **普通用户2**: `trader002` / `123456`

### 市场数据缓存说明

系统使用Redis缓存市场数据以提升性能：

- **首次访问**：系统自动从东方财富API获取完整A股数据（约5470只股票）并缓存
- **后续访问**：从Redis缓存毫秒级响应
- **自动更新**：定时任务每30分钟自动刷新缓存
- **手动刷新**：可通过API `/stock/market/cache/refresh/` 手动刷新

### 故障排除

**Redis连接失败**：
- 确保Redis服务器正在运行：`redis-cli ping`
- 检查Redis端口（默认6379）是否被占用
- 查看Redis服务状态和错误日志

**市场数据获取失败**：
- 检查网络连接
- 确认东方财富API可访问
- 查看后端控制台错误信息

详细的前端和后端配置请参考各自目录中的README文件。
