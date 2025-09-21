# 股票交易模拟系统

基于 Python 的股票交易模拟系统，采用 Django + Vue3 技术栈开发。系统实现了完整的股票实时交易模拟、权限管理和数据分析功能，符合金融软件项目管理实践课程要求。

本系统基于[Mini-RABC 权限管理系统](https://github.com/1517005260/Stock-RABC/tree/b28cf383880f164473a17d2ab80a85b175a662ec)扩展开发，在保留完整 RBAC 权限管理功能的基础上，新增了股票交易模拟的核心业务功能。

## 项目概述

- **前端技术栈**：Vue 3 + Element Plus + Vuex + Vue Router + Axios + ECharts
- **后端技术栈**：Django + Django REST Framework + JWT + SQLite + Redis
- **数据接口**：东方财富 API、akshare
- **核心功能**：股票实时交易模拟、K 线图表展示、权限管理、AI 聊天

## 系统功能

### 业务子系统

1. **股票实时交易过程模拟功能**

   - 实时股价展示和走势图（K 线图、分时图）
   - 大盘指数监控（上证指数、深证成指、创业板指等）
   - 技术指标分析（MA、MACD、RSI 等）
   - 涨跌分布统计

2. **股票交易（买卖）**

   - 模拟买入/卖出操作
   - 资金账户管理
   - 持仓管理
   - 交易记录查询

3. **公司基本信息**
   - 股票基本面数据
   - 公司财务信息
   - 行业分类信息
   - 市场新闻资讯

### 用户权限子系统

- **角色管理**：支持多角色定义和权限分配
- **功能管理**：基于菜单的细粒度权限控制
- **角色分配管理**：用户-角色关联管理
- **权限分配管理**：角色-权限关联管理

## 软件架构设计

### 系统架构图

```
+---------------+        +---------------+        +---------------+
|               |        |               |        |               |
|    前端       |<------>|    后端API    |<------>|  数据接口     |
|  (Vue 3)      |  HTTP  |  (Django)     |  HTTP  |  (东方财富)   |
|               |        |               |        |               |
+---------------+        +---------------+        +---------------+
                                |
                                |
                         +---------------+
                         |               |
                         |   Redis缓存   |
                         |   数据库      |
                         |  (SQLite)     |
                         +---------------+
```

### ER 图 (实体关系图)

```
用户权限模块：
+---------------+      +----------------+      +---------------+
|    User       |      |    UserRole    |      |    Role       |
+---------------+      +----------------+      +---------------+
| id            |<---->| user_id        |<---->| id            |
| username      |      | role_id        |      | name          |
| password      |      +----------------+      | status        |
| status        |                              | sort          |
| email         |                              | remark        |
| create_time   |                              +---------------+
+---------------+                                      |
                                                       |
                                               +----------------+      +---------------+
                                               |   RoleMenu     |      |    Menu       |
                                               +----------------+      +---------------+
                                               | role_id        |<---->| id            |
                                               | menu_id        |      | name          |
                                               +----------------+      | path          |
                                                                      | parent_id     |
                                                                      | component     |
                                                                      | perms         |
                                                                      +---------------+

股票交易模块：
+------------------+      +------------------+      +------------------+
| UserStockAccount |      |   UserPosition   |      |  TradeRecord     |
+------------------+      +------------------+      +------------------+
| user_id          |<---->| user_id          |<---->| user_id          |
| account_balance  |      | ts_code          |      | ts_code          |
| frozen_balance   |      | stock_name       |      | trade_type       |
| total_assets     |      | position_shares  |      | trade_shares     |
| total_profit     |      | cost_price       |      | trade_price      |
+------------------+      | current_price    |      | trade_amount     |
                          | profit_loss      |      | create_time      |
                          +------------------+      +------------------+
```

### UML 类图

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

- **frontend/**: Vue 3 前端项目
- **backend/**: Django 后端项目

每个部分都有自己的 README 文件，详细说明了安装、配置和实现思路。

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

#### 2. 启动 Redis 服务器

**Windows 系统**：

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

**Linux/macOS 系统**：

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

**Windows 系统完整启动流程**：

**第一步：启动 Redis 服务器**

```bash
# Redis应该已经作为Windows服务运行，检查状态：
redis-cli ping
# 应该返回：PONG

# 如果Redis未运行，手动启动：
redis-server
```

**第二步：启动 Django 后端服务器**

```bash
cd backend

# 启动HTTP服务器
python manage.py runserver

# 如果启用websocket
daphne -p 8000 app.asgi:application

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

**第四步：启动市场数据自动更新器（Windows 专用）**

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
- 后端 API：http://localhost:8000
- Redis 缓存状态：http://localhost:8000/stock/market/cache/status/

**快速验证系统是否正常运行**：

1. 访问前端页面，检查市场指数显示是否正常
2. 查看涨跌分布数据是否实时更新
3. 检查资金流向数据是否非零
4. 后端日志应显示市场数据更新信息

### 测试账号

系统初始化后提供以下测试账号：

- **超级管理员**: `python222` / `123456`
- **管理员**: `admin001` / `123456`
- **普通用户 1**: `trader001` / `123456`
- **普通用户 2**: `trader002` / `123456`

### 市场数据缓存说明

系统使用 Redis 缓存市场数据以提升性能：

- **首次访问**：系统自动从东方财富 API 获取完整 A 股数据（约 5470 只股票）并缓存
- **后续访问**：从 Redis 缓存毫秒级响应
- **自动更新**：定时任务每 30 分钟自动刷新缓存
- **手动刷新**：可通过 API `/stock/market/cache/refresh/` 手动刷新

### 故障排除

**Redis 连接失败**：

- 确保 Redis 服务器正在运行：`redis-cli ping`
- 检查 Redis 端口（默认 6379）是否被占用
- 查看 Redis 服务状态和错误日志

**市场数据获取失败**：

- 检查网络连接
- 确认东方财富 API 可访问
- 查看后端控制台错误信息

详细的前端和后端配置请参考各自目录中的 README 文件。
