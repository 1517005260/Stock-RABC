# Django RBAC + 股票交易模拟系统

基于 Django 实现的 RBAC（基于角色的访问控制）后台管理系统，集成了完整的股票交易模拟功能。系统提供了用户、角色、权限管理、AI 聊天功能以及全面的股票交易模拟系统，支持实时行情数据、K 线图、技术分析、新闻资讯等功能。本系统使用 JWT 进行身份验证，支持跨域请求和 WebSocket 实时推送。

## 项目亮点

- 完整的股票交易系统：实现了模拟股票交易的所有核心功能
- 真实数据支持：基于 TuShare Pro API 获取真实股票行情数据
- 企业级数据服务：整合量化数据服务和企业级金融数据服务
- 兼容性设计：兼容新旧版本 tushare API，确保数据稳定性
- 权限管理完善：支持普通用户、管理员、超级管理员三级权限
- API 测试完备：提供完整的 API 功能测试脚本
- 技术指标齐全：支持 MACD、RSI、BOLL、KDJ 等主流技术分析指标

## 技术栈

### 核心框架

- **Python**: 3.10+
- **Django**: 5.1.1
- **Django REST Framework**: 3.14.0
- **JWT 认证**: djangorestframework-jwt 1.11.0
- **数据库**: SQLite（可扩展至 PostgreSQL 等）
- **跨域支持**: django-cors-headers 4.7.0

### 实时通信

- **WebSocket**: channels 4.3.1
- **异步支持**: asgiref 3.9.1

### 定时任务

- **定时任务**: django-crontab 0.7.1

### 股票数据与分析

- **多源数据整合**: tushare 1.2.89
- **量化数据服务**: 专业的金融市场数据获取与分析平台
- **企业级金融数据**: 基于 TuShare Pro 的专业金融数据获取平台
- **数据分析**: pandas 1.5.0+, numpy 1.21.0+
- **数学计算**: scipy 1.9.0+
- **API 兼容性**: 兼容新旧版本 tushare，确保数据稳定性
- **智能缓存**: 实现数据缓存和 API 限流机制
- **实时推送**: 支持 5 秒刷新的实时股票数据推送

### 网络请求与解析

- **HTTP 客户端**: httpx 0.27.2, requests 2.31.0+
- **网页解析**: beautifulsoup4 4.13.0+

### AI 功能

- **OpenAI API**: openai 1.55.3+

### 环境配置

- **环境变量**: python-dotenv 1.0.0

## 主要功能特性

### 1. RBAC 权限管理系统

- 用户、角色、权限三层管理
- JWT 身份验证
- 灵活的菜单权限控制
- 多级角色体系（普通用户、管理员、超级管理员）

### 2. 股票交易模拟系统

- **实时股票行情**: 支持股票价格实时推送（每 5 秒刷新）
- **K 线图数据**: 日 K、周 K、月 K 线数据，支持多种技术指标
- **技术分析**: MACD、RSI、BOLL、KDJ、MA、EMA 等技术指标
- **分时图**: 模拟分时数据，支持交易时间检测
- **模拟交易**: 股票买入/卖出、持仓管理、交易记录
- **市场概况**: 涨跌统计、主要指数、交易状态
- **股票搜索**: 支持股票代码、名称搜索
- **行业分类**: 股票行业筛选功能

### 3. 新闻资讯系统

- **财经新闻**: 自动爬取并展示财经新闻
- **新闻分类**: 支持新闻分类管理
- **实时推送**: WebSocket 推送最新新闻到客户端
- **新闻管理**: 管理员可创建和管理新闻内容

### 4. WebSocket 实时通信

- **实时数据推送**: 股票价格、市场数据实时推送
- **订阅机制**: 支持订阅特定股票的实时数据
- **交易时间检测**: 智能检测交易时间，仅在交易时间推送数据
- **用户通知**: 支持个人消息通知推送

### 5. 定时任务系统

- **数据同步**: 每个交易日收盘后自动同步股票数据
- **新闻爬取**: 定时爬取财经新闻
- **数据清理**: 自动清理过期的历史数据

### 6. AI 聊天助手

- **流式聊天**: 基于 OpenAI API 的智能对话
- **聊天限制**: 普通用户每日聊天次数限制
- **历史记录**: 完整的聊天历史记录

## 安装与启动

### 前提条件

- Python 3.10 或更高版本
- pip 包管理工具
- 虚拟环境工具(推荐使用 venv 或 conda)
- Tushare Pro API Token (用于获取股票数据)

### 步骤 1: 克隆仓库

```bash
git clone 本项目
cd Mini-RABC/backend
```

### 步骤 2: 创建并激活虚拟环境

```bash
# 使用conda创建虚拟环境
conda create -n rabc python==3.10
conda activate rabc

# 或使用venv
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 步骤 3: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 4: 配置环境变量

创建`.env`文件并配置以下参数：

```env
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# 聊天配置
CHAT_DAILY_LIMIT=5  # 普通用户每日消息限制

# Tushare Pro API配置 (必需)
TUSHARE_TOKEN=your_tushare_pro_api_token_here
```

### 步骤 5: 初始化数据库

```bash
# 执行数据库迁移
python manage.py makemigrations
python manage.py migrate

# 初始化系统数据（包括用户、角色、股票数据）
python init_system.py
```

### 步骤 6: 配置定时任务（可选）

```bash
# 添加定时任务到系统crontab
python manage.py crontab add

# 查看已添加的定时任务
python manage.py crontab show

# 移除定时任务
python manage.py crontab remove
```

### 步骤 7: 启动服务器

#### 开发环境

```bash
# 启动HTTP服务器
python manage.py runserver

# 如需WebSocket功能，使用ASGI服务器，注意与上条命令互斥，启动一个即可
daphne -p 8000 app.asgi:application
```

#### 生产环境

```bash
# 使用Gunicorn + Uvicorn
pip install gunicorn uvicorn
gunicorn app.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

服务器将在 `http://localhost:8000/` 运行。

## 项目架构

```
backend/
├── app/                  # 主应用配置
│   ├── settings.py       # Django设置
│   ├── urls.py           # 主URL配置
│   ├── wsgi.py           # WSGI配置
│   └── asgi.py           # ASGI配置 (支持WebSocket)
├── chat/                 # AI聊天模块
├── role/                 # 角色管理模块
├── user/                 # 用户管理模块
├── stock/                # 股票交易模块
│   ├── models.py         # 股票相关模型
│   ├── views.py          # 股票API视图
│   ├── services.py       # 股票业务逻辑
│   ├── consumers.py      # WebSocket消费者
│   ├── routing.py        # WebSocket路由
│   └── tasks.py          # 定时任务
├── trading/              # 交易功能模块
│   ├── models.py         # 交易相关模型
│   └── views.py          # 交易API视图
├── utils/                # 工具类
│   ├── permissions.py    # 权限装饰器
│   └── jwt_helper.py     # JWT工具类
├── manage.py             # Django管理脚本
├── requirements.txt      # 项目依赖
├── init_system.py        # 系统初始化脚本
└── README.md             # 项目文档
```

## API 接口文档

### 用户认证接口

#### 用户登录

```http
POST /user/login
Content-Type: application/json

{
    "username": "python222",
    "password": "123456"
}

# 响应
{
    "code": 200,
    "info": "登录成功",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "python222",
        "roles": "超级管理员"
    },
    "permissions": ["system:user:list", "system:user:edit", ...]
}
```

### 股票行情接口

#### 获取股票列表

```http
GET /stock/list/?page=1&pageSize=20&keyword=&industry=&market=
Authorization: Bearer <token>

# 响应
{
    "code": 200,
    "msg": "获取成功",
    "data": {
        "list": [
            {
                "ts_code": "000001.SZ",
                "symbol": "000001",
                "name": "平安银行",
                "industry": "银行",
                "current_price": 10.59,
                "change": 0.094,
                "pct_chg": 0.899,
                "volume": 846318,
                "amount": 113013.67
            }
        ],
        "total": 4000,
        "page": 1,
        "pageSize": 20,
        "totalPages": 200
    }
}
```

#### 获取股票详情

```http
GET /stock/detail/<ts_code>/
Authorization: Bearer <token>

# 响应
{
    "code": 200,
    "msg": "获取成功",
    "data": {
        "ts_code": "000001.SZ",
        "name": "平安银行",
        "current_price": 10.59,
        "history_data": [...],  # 最近30天历史数据
        "company_info": {...}   # 公司基本信息
    }
}
```

#### 获取实时股票价格

```http
GET /stock/realtime/price/<ts_code>/
Authorization: Bearer <token>

# 响应
{
    "code": 200,
    "msg": "获取成功",
    "data": {
        "ts_code": "000001.SZ",
        "current_price": 10.59,
        "change": 0.094,
        "pct_chg": 0.899,
        "volume": 846318,
        "timestamp": "2025-09-09T19:28:38.729799",
        "is_real_time": true
    }
}
```

#### 获取 K 线数据

```http
GET /stock/kline/<ts_code>/?period=daily&limit=100&adjust=qfq
Authorization: Bearer <token>

# 参数说明:
# period: daily(日K), weekly(周K), monthly(月K)
# limit: 数据条数，最大500
# adjust: qfq(前复权), hfq(后复权), none(不复权)

# 响应
{
    "code": 200,
    "msg": "获取成功",
    "data": {
        "ts_code": "000001.SZ",
        "name": "平安银行",
        "period": "daily",
        "count": 100,
        "kline_data": [
            {
                "date": "2025-09-09",
                "open": 10.5,
                "high": 10.77,
                "low": 10.31,
                "close": 10.59,
                "volume": 846318,
                "amount": 113013.67
            }
        ],
        "technical_indicators": {
            "ma5": [10.2, 10.3, ...],
            "ma10": [10.1, 10.2, ...],
            "macd": {
                "dif": [0.1, 0.2, ...],
                "dea": [0.05, 0.15, ...],
                "macd": [0.1, 0.1, ...]
            },
            "rsi": [45.2, 48.5, ...],
            "boll": {
                "upper": [11.2, 11.3, ...],
                "middle": [10.5, 10.6, ...],
                "lower": [9.8, 9.9, ...]
            }
        }
    }
}
```

#### 获取分时图数据

```http
GET /stock/realtime/chart/<ts_code>/
Authorization: Bearer <token>

# 响应
{
    "code": 200,
    "msg": "获取成功",
    "data": {
        "ts_code": "000001.SZ",
        "intraday_data": [
            {
                "time": "09:30",
                "price": 10.6,
                "volume": 784,
                "avg_price": 10.55,
                "change": 0.1,
                "pct_change": 0.95
            }
        ],
        "base_info": {
            "current_price": 10.59,
            "pre_close": 10.5,
            "high": 10.77,
            "low": 10.31
        }
    }
}
```

#### 获取市场概况

```http
GET /stock/market/overview/
Authorization: Bearer <token>

# 响应
{
    "code": 200,
    "msg": "获取成功",
    "data": {
        "indices": [
            {
                "ts_code": "000001.SH",
                "name": "上证指数",
                "current_price": 3200.5,
                "change": 15.2,
                "pct_chg": 0.48
            }
        ],
        "market_stats": {
            "trade_date": "2025-09-09",
            "total_stocks": 4000,
            "up_count": 2100,
            "down_count": 1800,
            "equal_count": 100,
            "up_ratio": 52.5
        },
        "trading_status": {
            "is_trading_time": false,
            "time_period": "after_market",
            "timestamp": "2025-09-09T19:27:06.032772"
        }
    }
}
```

### 交易功能接口

#### 获取用户账户信息

```http
GET /trading/account/
Authorization: Bearer <token>
```

#### 股票买入

```http
POST /trading/buy/
Authorization: Bearer <token>
Content-Type: application/json

{
    "ts_code": "000001.SZ",
    "price": 10.50,
    "shares": 1000
}
```

#### 股票卖出

```http
POST /trading/sell/
Authorization: Bearer <token>
Content-Type: application/json

{
    "ts_code": "000001.SZ",
    "price": 10.60,
    "shares": 500
}
```

#### 获取用户持仓

```http
GET /trading/positions/
Authorization: Bearer <token>
```

#### 获取交易记录

```http
GET /trading/records/?page=1&pageSize=20
Authorization: Bearer <token>
```

### 新闻资讯接口

#### 获取最新新闻

```http
GET /stock/news/latest/?limit=10&category=市场动态
Authorization: Bearer <token>

# 响应
{
    "code": 200,
    "msg": "获取成功",
    "data": [
        {
            "id": 1,
            "title": "A股市场今日震荡上涨，科技股表现强势",
            "source": "财经新闻",
            "category": "市场动态",
            "publish_time": "2025-09-09 10:10:35",
            "summary": "今日A股三大指数集体上涨，创业板指涨幅超过2%...",
            "related_stocks": []
        }
    ]
}
```

#### 创建新闻（管理员权限）

```http
POST /stock/news/create/
Authorization: Bearer <token>
Content-Type: application/json

{
    "title": "新闻标题",
    "content": "新闻内容",
    "source": "新闻来源",
    "category": "新闻分类",
    "related_stocks": ["000001.SZ", "000002.SZ"]
}
```

### WebSocket 实时推送

#### 连接 WebSocket

```javascript
// 连接股票实时数据推送
const ws = new WebSocket(
  "ws://localhost:8000/ws/stock/realtime/general/?token=<jwt_token>"
);

// 监听消息
ws.onmessage = function (event) {
  const data = JSON.parse(event.data);
  console.log("推送数据:", data);

  switch (data.type) {
    case "market_data":
      // 市场数据：热门股票、市场概况、最新新闻
      updateMarketData(data.data);
      break;
    case "realtime_data":
      // 订阅股票实时数据
      updateStockPrices(data.data);
      break;
    case "connection_established":
      console.log("WebSocket连接成功");
      break;
  }
};

// 订阅特定股票
ws.send(
  JSON.stringify({
    type: "subscribe",
    ts_codes: ["000001.SZ", "000002.SZ"],
  })
);
```

### 数据同步接口（超级管理员权限）

#### 手动同步股票数据

```http
POST /stock/sync/
Authorization: Bearer <token>
Content-Type: application/json

{
    "type": "basic"  # basic(基本信息), daily(日线数据), company(公司信息)
}
```

## 错误处理

API 返回的错误响应格式统一如下：

```json
{
  "code": 400,
  "msg": "错误描述信息",
  "data": null
}
```

常见错误码：

- `200`: 成功
- `400`: 请求参数错误
- `401`: 未认证或 Token 无效
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

## 注意事项

1. **生产环境部署**时请修改`SECRET_KEY`并关闭`DEBUG`模式
2. **默认管理员账号**：`python222`，密码：`123456`
3. **Tushare API**：需要在 https://tushare.pro/ 注册并获取 API Token 才能获取真实股票数据
4. **WebSocket 支持**：需要 ASGI 服务器支持，推荐使用 Daphne 或 Uvicorn
5. **定时任务**：Linux 环境下可使用 crontab，Windows 环境下可使用计划任务
6. **数据库扩展**：支持 PostgreSQL、MySQL 等数据库，需安装相应驱动
