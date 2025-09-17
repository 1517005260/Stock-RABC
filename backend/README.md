# 股票交易模拟系统 - 后端

基于 Django + Django REST Framework 的股票交易模拟系统后端 API，提供完整的股票数据获取、交易模拟和权限管理功能。

## 技术栈

- **框架**: Django 4.x + Django REST Framework
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **缓存**: Redis
- **认证**: JWT (JSON Web Token)
- **任务队列**: Django-crontab (定时任务)
- **数据源**: 东方财富 API、akshare
- **部署**: Gunicorn + Nginx

## 项目结构

```
backend/
├── app/                 # Django项目配置
│   ├── settings.py     # 项目设置
│   ├── urls.py         # 主路由配置
│   └── wsgi.py         # WSGI配置
├── user/               # 用户管理模块
│   ├── models.py       # 用户模型
│   ├── views.py        # 用户API视图
│   └── serializers.py  # 序列化器
├── role/               # 角色权限模块
│   ├── models.py       # 角色权限模型
│   └── views.py        # 权限API视图
├── stock/              # 股票数据模块
│   ├── models.py       # 股票模型
│   ├── views.py        # 股票API视图
│   ├── services.py     # 股票数据服务
│   ├── redis_cache.py  # Redis缓存管理
│   └── tasks.py        # 定时任务
├── trading/            # 交易模拟模块
│   ├── models.py       # 交易模型
│   ├── views.py        # 交易API视图
│   └── services.py     # 交易业务逻辑
├── utils/              # 工具模块
│   ├── permissions.py  # 权限验证
│   ├── response.py     # 统一响应格式
│   └── exceptions.py   # 异常处理
├── init_system.py      # 系统初始化脚本
├── market_data_cron.py # 市场数据定时更新
├── requirements.txt    # 依赖包列表
└── manage.py          # Django管理脚本
```

## 核心功能模块

### 1. 用户管理模块 (`user/`)

**数据模型**:

- `SysUser`: 用户基本信息
- `SysUserRole`: 用户-角色关联

**主要功能**:

- 用户注册、登录、注销
- JWT Token 认证
- 用户信息 CRUD
- 密码加密存储

**API 接口**:

```
POST /user/login/          # 用户登录
POST /user/register/       # 用户注册
GET  /user/info/          # 获取用户信息
PUT  /user/info/          # 更新用户信息
POST /user/logout/        # 用户注销
```

### 2. 角色权限模块 (`role/`)

**数据模型**:

- `SysRole`: 角色信息
- `SysMenu`: 菜单权限
- `SysRoleMenu`: 角色-菜单关联

**主要功能**:

- RBAC 权限控制
- 角色管理
- 菜单权限管理
- 动态权限验证

**API 接口**:

```
GET  /role/list/          # 角色列表
POST /role/create/        # 创建角色
PUT  /role/update/{id}/   # 更新角色
GET  /role/menus/{id}/    # 角色菜单权限
```

### 3. 股票数据模块 (`stock/`)

**数据模型**:

- `StockInfo`: 股票基本信息
- `StockDaily`: 日行情数据
- `MarketIndex`: 市场指数

**主要功能**:

- 股票基础数据获取
- 实时行情数据
- K 线数据计算
- 技术指标分析
- Redis 缓存管理

**核心服务**:

- `QuantitativeDataService`: 量化数据服务
- `RedisCache`: 缓存管理服务
- `TushareService`: Tushare 数据接口

**API 接口**:

```
GET  /stock/list/                    # 股票列表
GET  /stock/detail/{code}/           # 股票详情
GET  /stock/kline/{code}/            # K线数据
GET  /stock/market/indices/          # 市场指数
GET  /stock/market/cache/status/     # 缓存状态
POST /stock/market/cache/refresh/    # 刷新缓存
```

### 4. 交易模拟模块 (`trading/`)

**数据模型**:

- `UserStockAccount`: 用户股票账户
- `UserPosition`: 用户持仓
- `TradeRecord`: 交易记录
- `MarketNews`: 市场资讯

**主要功能**:

- 模拟买入/卖出
- 账户资金管理
- 持仓管理
- 盈亏计算
- 交易记录查询

**业务逻辑**:

- 交易风控检查
- 资金冻结/解冻
- 持仓成本计算
- 盈亏实时更新

**API 接口**:

```
GET  /trading/account/           # 账户信息
POST /trading/buy/               # 买入股票
POST /trading/sell/              # 卖出股票
GET  /trading/positions/         # 持仓查询
GET  /trading/records/           # 交易记录
GET  /trading/news/              # 市场资讯
```

## 设计思路

### 1. 分层架构设计

```
API层 (views.py)           # 接口路由，参数验证
 ↓
业务逻辑层 (services.py)   # 核心业务逻辑
 ↓
数据访问层 (models.py)     # 数据模型，数据库操作
 ↓
数据存储层 (Database)      # SQLite/PostgreSQL + Redis
```

### 2. 数据获取策略

- **实时数据**: 通过东方财富 API 获取
- **历史数据**: 使用 akshare 库补充
- **缓存机制**: Redis 缓存热点数据，减少 API 调用
- **定时更新**: 每 30 分钟更新一次市场数据

### 3. 权限控制设计

- **JWT 认证**: 无状态认证机制
- **RBAC 模型**: 基于角色的权限控制
- **装饰器权限**: 使用@permission_required 装饰器
- **细粒度控制**: 支持菜单级和功能级权限

### 4. 交易业务设计

- **账户模型**: 模拟真实证券账户
- **交易规则**: T+1 交易，涨跌停限制
- **风控机制**: 资金充足性检查，持仓限制
- **数据一致性**: 事务保证数据完整性

## 安装和启动

### 环境要求

- Python 3.10+
- Redis 服务器
- pip 包管理工具

### 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 环境配置

复制环境配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要参数：

```
# 数据库配置
DATABASE_URL=sqlite:///db.sqlite3

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=your-secret-key
DEBUG=True

# 股票数据API
TUSHARE_TOKEN=your-tushare-token
```

### 数据库初始化

```bash
# 创建数据库表
python manage.py migrate

# 或使用一键初始化脚本
python init_system.py
```

### 启动服务

**开发环境**:

```bash
python manage.py runserver
```

**生产环境**:

```bash
gunicorn app.wsgi:application
```

### 启动市场数据更新器

```bash
# Windows系统
python windows_market_updater.py

# Linux系统 (使用crontab)
python manage.py crontab add
```

## 核心 API 说明

### 1. 用户认证 API

**用户登录**

```
POST /user/login/
Content-Type: application/json

{
    "username": "trader001",
    "password": "123456"
}

Response:
{
    "code": 200,
    "msg": "登录成功",
    "data": {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
            "id": 1,
            "username": "trader001",
            "email": "trader001@example.com"
        },
        "roles": ["普通用户"],
        "menus": [...]
    }
}
```

### 2. 股票数据 API

**获取股票列表**

```
GET /stock/list/?page=1&size=20&search=腾讯

Response:
{
    "code": 200,
    "data": {
        "count": 5470,
        "results": [
            {
                "ts_code": "000001.SZ",
                "name": "平安银行",
                "close": 12.34,
                "pct_chg": 2.15,
                "volume": 123456789
            }
        ]
    }
}
```

**获取 K 线数据**

```
GET /stock/kline/000001.SZ/?period=daily&limit=100

Response:
{
    "code": 200,
    "data": {
        "kline": [
            {
                "trade_date": "2024-01-15",
                "open": 12.00,
                "high": 12.50,
                "low": 11.80,
                "close": 12.34,
                "volume": 123456789
            }
        ],
        "indicators": {
            "ma5": [12.10, 12.15, 12.20],
            "ma10": [12.00, 12.05, 12.10]
        }
    }
}
```

### 3. 交易模拟 API

**买入股票**

```
POST /trading/buy/
Content-Type: application/json

{
    "ts_code": "000001.SZ",
    "shares": 100,
    "price": 12.34
}

Response:
{
    "code": 200,
    "msg": "买入成功",
    "data": {
        "trade_id": "T20240115001",
        "amount": 1234.00,
        "fee": 1.23
    }
}
```

## 数据缓存策略

### Redis 缓存结构

```
stock:basic:{ts_code}           # 股票基本信息 (24小时)
stock:daily:{ts_code}           # 日行情数据 (4小时)
market:indices                  # 市场指数 (1小时)
market:hot_stocks              # 热门股票 (30分钟)
user:positions:{user_id}       # 用户持仓 (实时)
```

### 缓存更新机制

1. **定时更新**: 每 30 分钟全量更新市场数据
2. **实时更新**: 交易操作后立即更新相关缓存
3. **懒加载**: 首次访问时从 API 获取并缓存
4. **缓存预热**: 系统启动时预加载热点数据

## 定时任务

### 市场数据更新任务

```python
# market_data_cron.py
@cron_job(minute='*/30')  # 每30分钟执行
def update_market_data():
    """更新市场数据到缓存"""
    cache_service = RedisCache()
    data_service = QuantitativeDataService()

    # 更新基础数据
    cache_service.refresh_all_cache()

    # 更新指数数据
    data_service.update_market_indices()
```

### Windows 定时更新器

```bash
# 启动后台更新服务
python windows_market_updater.py

# 立即更新一次
python windows_market_updater.py --once

# 自定义更新间隔(分钟)
python windows_market_updater.py --interval 15
```
