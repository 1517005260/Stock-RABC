# Django RBAC + 股票交易模拟系统

**注意：**curl 测试时，登录需要 md5 密码+token 登录

这是一个基于 Django 实现的 RBAC（基于角色的访问控制）后台管理系统，集成了股票交易模拟功能。系统提供了用户、角色、权限管理、AI 聊天功能以及完整的股票交易模拟系统，支持实时行情数据、K 线图、技术分析、新闻资讯等功能。本系统使用 JWT 进行身份验证，支持跨域请求和 WebSocket 实时推送，适合作为金融类应用的后端系统。

## 技术栈

### 核心框架

- **Python**: 3.10+
- **Django**: 5.1.1
- **Django REST Framework**: 3.14.0
- **JWT 认证**: djangorestframework-jwt 1.11.0
- **数据库**: SQLite（可扩展至 PostgreSQL 等）
- **跨域支持**: django-cors-headers 4.7.0

### 实时通信

- **WebSocket**: channels 4.3.1 (实现实时股票数据推送)
- **异步支持**: asgiref 3.9.1

### 定时任务

- **定时任务**: django-crontab 0.7.1 (收盘后数据同步)

### 股票数据与分析

- **股票数据源**: tushare 1.2.89 (获取真实股票数据)
- **数据分析**: pandas 1.5.0+, numpy 1.21.0+
- **数学计算**: scipy 1.9.0+

### 网络请求与解析

- **HTTP 客户端**: httpx 0.27.2, requests 2.31.0+
- **网页解析**: beautifulsoup4 4.13.0+ (新闻爬取)

### AI 功能

- **OpenAI API**: openai 1.55.3+ (AI 聊天助手)

### 环境配置

- **环境变量**: python-dotenv 1.0.0

## 主要功能特性

### 1. RBAC 权限管理系统

- ✅ 用户、角色、权限三层管理
- ✅ JWT 身份验证
- ✅ 灵活的菜单权限控制
- ✅ 多级角色体系（普通用户、管理员、超级管理员）

### 2. 股票交易模拟系统

- ✅ **实时股票行情**: 支持股票价格实时推送（每 5 秒刷新）
- ✅ **K 线图数据**: 日 K、周 K、月 K 线数据，支持多种技术指标
- ✅ **技术分析**: MACD、RSI、BOLL、KDJ、MA、EMA 等技术指标
- ✅ **分时图**: 模拟分时数据，支持交易时间检测
- ✅ **模拟交易**: 股票买入/卖出、持仓管理、交易记录
- ✅ **市场概况**: 涨跌统计、主要指数、交易状态
- ✅ **股票搜索**: 支持股票代码、名称搜索
- ✅ **行业分类**: 股票行业筛选功能

### 3. 新闻资讯系统

- ✅ **财经新闻**: 自动爬取并展示财经新闻
- ✅ **新闻分类**: 支持新闻分类管理
- ✅ **实时推送**: WebSocket 推送最新新闻到客户端
- ✅ **新闻管理**: 管理员可创建和管理新闻内容

### 4. WebSocket 实时通信

- ✅ **实时数据推送**: 股票价格、市场数据实时推送
- ✅ **订阅机制**: 支持订阅特定股票的实时数据
- ✅ **交易时间检测**: 智能检测交易时间，仅在交易时间推送数据
- ✅ **用户通知**: 支持个人消息通知推送

### 5. 定时任务系统

- ✅ **数据同步**: 每个交易日收盘后自动同步股票数据
- ✅ **新闻爬取**: 定时爬取财经新闻
- ✅ **数据清理**: 自动清理过期的历史数据

### 6. AI 聊天助手

- ✅ **流式聊天**: 基于 OpenAI API 的智能对话
- ✅ **聊天限制**: 普通用户每日聊天次数限制
- ✅ **历史记录**: 完整的聊天历史记录

## 安装与启动

### 前提条件

- Python 3.10 或更高版本
- pip 包管理工具
- 虚拟环境工具(推荐使用 venv 或 conda)
- Tushare Pro API Token (用于获取股票数据)

### 步骤 1: 克隆仓库

```bash
git clone https://github.com/1517005260/Mini-RABC.git
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
TUSHARE_KEY=your_tushare_pro_api_token_here
```

**重要**: 需要在 [Tushare Pro](https://tushare.pro/) 注册账号并获取 API Token 才能获取股票数据。

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

# 如需WebSocket功能，使用ASGI服务器
daphne -p 8000 app.asgi:application
```

#### 生产环境

```bash
# 使用Gunicorn + Uvicorn
pip install gunicorn uvicorn
gunicorn app.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

此时，服务器将在 `http://localhost:8000/` 运行。

### 项目架构

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
├── stock/                # 股票交易模块 ⭐ 新增
│   ├── models.py         # 股票相关模型
│   ├── views.py          # 股票API视图
│   ├── services.py       # 股票业务逻辑
│   ├── consumers.py      # WebSocket消费者
│   ├── routing.py        # WebSocket路由
│   └── tasks.py          # 定时任务
├── trading/              # 交易功能模块 ⭐ 新增
│   ├── models.py         # 交易相关模型
│   └── views.py          # 交易API视图
├── utils/                # 工具类
│   ├── permissions.py    # 权限装饰器
│   └── jwt_helper.py     # JWT工具类 ⭐ 新增
├── manage.py             # Django管理脚本
├── requirements.txt      # 项目依赖
├── init_system.py        # 系统初始化脚本 ⭐ 更新
└── README.md             # 项目文档
```

### 股票交易系统数据库设计

#### 股票基础数据模型

```python
# stock/models.py
class StockBasic(models.Model):
    """股票基本信息"""
    ts_code = models.CharField(max_length=20, unique=True)  # 股票代码
    symbol = models.CharField(max_length=20)               # 股票简称
    name = models.CharField(max_length=100)                # 股票名称
    area = models.CharField(max_length=50)                 # 地区
    industry = models.CharField(max_length=50)             # 行业
    market = models.CharField(max_length=20)               # 市场类型
    list_date = models.DateField()                         # 上市日期

class StockDaily(models.Model):
    """股票日线数据"""
    ts_code = models.CharField(max_length=20)
    trade_date = models.DateField()                        # 交易日期
    open = models.DecimalField(max_digits=10, decimal_places=2)    # 开盘价
    high = models.DecimalField(max_digits=10, decimal_places=2)    # 最高价
    low = models.DecimalField(max_digits=10, decimal_places=2)     # 最低价
    close = models.DecimalField(max_digits=10, decimal_places=2)   # 收盘价
    vol = models.BigIntegerField()                         # 成交量
    amount = models.DecimalField(max_digits=20, decimal_places=2)  # 成交额
```

#### 交易系统数据模型

```python
# trading/models.py
class UserStockAccount(models.Model):
    """用户股票账户"""
    user = models.OneToOneField(SysUser, on_delete=models.CASCADE)
    account_balance = models.DecimalField(max_digits=15, decimal_places=2)  # 账户余额
    total_assets = models.DecimalField(max_digits=15, decimal_places=2)     # 总资产

class UserPosition(models.Model):
    """用户持仓"""
    user = models.ForeignKey(SysUser, on_delete=models.CASCADE)
    ts_code = models.CharField(max_length=20)              # 股票代码
    stock_name = models.CharField(max_length=100)          # 股票名称
    position_shares = models.IntegerField()                # 持仓数量
    available_shares = models.IntegerField()               # 可卖数量
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)  # 成本价
    current_price = models.DecimalField(max_digits=10, decimal_places=2)  # 现价

class TradeRecord(models.Model):
    """交易记录"""
    user = models.ForeignKey(SysUser, on_delete=models.CASCADE)
    ts_code = models.CharField(max_length=20)
    trade_type = models.CharField(max_length=10)           # BUY/SELL
    trade_price = models.DecimalField(max_digits=10, decimal_places=2)
    trade_shares = models.IntegerField()
    trade_amount = models.DecimalField(max_digits=15, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2)
    trade_time = models.DateTimeField(auto_now_add=True)
```

## 🚀 快速开始与API测试

### 启动服务器

```bash
# 启动HTTP服务器
python manage.py runserver

# 或启动支持WebSocket的ASGI服务器
pip install daphne
daphne -p 8000 app.asgi:application
```

服务器启动后，访问 `http://localhost:8000/` 即可使用API。

### API测试工具

我们提供了多种测试工具来验证API功能：

#### 1. Python自动化测试脚本 (推荐)

```bash
# 完整测试所有API接口
python test_api.py

# 测试特定功能模块
python test_api.py login      # 仅测试登录
python test_api.py stock      # 测试股票相关接口
python test_api.py trading    # 测试交易功能
python test_api.py realtime   # 测试实时数据
python test_api.py performance # 性能压力测试
```

#### 2. 股票走势5s异步刷新测试页面

打开浏览器访问 `test_realtime.html` 文件，可以：
- 实时查看股票数据（每5秒自动刷新）
- 监控API响应性能
- 观察数据变化动画效果
- 支持手动刷新和停止功能

#### 3. Shell脚本测试 (Linux/Mac)

```bash
chmod +x test_api.sh
./test_api.sh                # 完整测试
./test_api.sh login          # 测试特定功能
```

#### 4. Windows批处理测试

```cmd
test_api.bat                 # 完整测试
test_api.bat login          # 测试特定功能
```

## 📋 完整API接口文档

### 🔐 用户认证接口

所有接口都需要先通过用户登录获取JWT Token，然后在请求头中携带认证信息。

#### 用户登录
**用途**: 用户身份验证，获取访问令牌

```http
POST /user/login
Content-Type: application/json

{
    "username": "python222",
    "password": "123456"
}
```

**响应示例**:
```json
{
    "code": 200,
    "info": "登录成功",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "python222",
        "roles": "超级管理员"
    },
    "permissions": ["system:user:list", "system:user:edit"]
}
```

### 📈 股票行情接口

#### 获取股票列表
**用途**: 获取股票列表，支持分页、搜索、筛选

```http
GET /stock/list/?page=1&pageSize=20&keyword=&industry=&market=
Authorization: Bearer <token>
```

**参数说明**:
- `page`: 页码 (默认: 1)
- `pageSize`: 每页数量 (默认: 20, 最大: 100)
- `keyword`: 搜索关键词 (股票名称或代码)
- `industry`: 行业筛选
- `market`: 市场筛选 (主板/创业板等)

**响应示例**:
```json
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
                "current_price": 11.75,
                "change": 0.05,
                "pct_chg": 0.427,
                "volume": 860539,
                "amount": 1009279.73,
                "trade_date": "2025-09-09"
            }
        ],
        "total": 5435,
        "page": 1,
        "pageSize": 20,
        "totalPages": 272
    }
}
```

#### 获取股票详情
**用途**: 获取单只股票的详细信息，包括历史数据和公司信息

```http
GET /stock/detail/{ts_code}/
Authorization: Bearer <token>
```

**路径参数**:
- `ts_code`: 股票代码 (如: 000001.SZ)

#### 股票搜索
**用途**: 根据关键词搜索股票

```http
GET /stock/search/?keyword={keyword}&limit=10
Authorization: Bearer <token>
```

#### 获取行业列表
**用途**: 获取所有可用的股票行业分类

```http
GET /stock/industries/
Authorization: Bearer <token>
```

### ⚡ 实时数据接口 (支持5s异步刷新)

#### 获取实时股票价格
**用途**: 获取股票实时价格信息，支持高频调用

```http
GET /stock/realtime/price/{ts_code}/
Authorization: Bearer <token>
```

**响应示例**:
```json
{
    "code": 200,
    "msg": "获取成功",
    "data": {
        "ts_code": "000001.SZ",
        "current_price": 11.75,
        "change": 0.05,
        "pct_chg": 0.427,
        "volume": 860539,
        "timestamp": "2025-09-10T12:23:40.521440",
        "is_real_time": true
    }
}
```

#### 获取分时图数据
**用途**: 获取股票分时走势图数据

```http
GET /stock/realtime/chart/{ts_code}/
Authorization: Bearer <token>
```

#### 获取市场概况
**用途**: 获取整体市场状况，包括指数、涨跌统计等

```http
GET /stock/market/overview/
Authorization: Bearer <token>
```

### 💰 交易功能接口

#### 获取用户账户信息
**用途**: 查看用户的股票账户资金状况

```http
GET /trading/account/
Authorization: Bearer <token>
```

**响应示例**:
```json
{
    "code": 200,
    "msg": "获取成功",
    "data": {
        "account_balance": 989495.0,
        "frozen_balance": 0.0,
        "total_assets": 1000000.0,
        "total_profit": 10505.0,
        "market_value": 11750,
        "position_count": 1
    }
}
```

#### 股票买入
**用途**: 购买股票

```http
POST /trading/buy/
Authorization: Bearer <token>
Content-Type: application/json

{
    "ts_code": "000001.SZ",
    "price": 11.50,
    "shares": 100
}
```

#### 股票卖出
**用途**: 出售持有的股票

```http
POST /trading/sell/
Authorization: Bearer <token>
Content-Type: application/json

{
    "ts_code": "000001.SZ",
    "price": 11.60,
    "shares": 50
}
```

#### 查看持仓
**用途**: 查看用户当前持有的所有股票

```http
GET /trading/positions/
Authorization: Bearer <token>
```

#### 查看交易记录
**用途**: 查看历史交易记录

```http
GET /trading/records/?page=1&pageSize=20
Authorization: Bearer <token>
```

### 📊 K线图和技术分析接口

#### 获取K线数据
**用途**: 获取股票K线图数据，支持日K、周K、月K

```http
GET /stock/kline/{ts_code}/?period=daily&limit=100&adjust=qfq
Authorization: Bearer <token>
```

**参数说明**:
- `period`: 周期类型 (daily/weekly/monthly)
- `limit`: 数据条数 (最大500)
- `adjust`: 复权类型 (qfq前复权/hfq后复权/none不复权)

#### 获取技术分析指标
**用途**: 获取技术分析指标数据 (MACD、RSI、BOLL等)

```http
GET /stock/technical/{ts_code}/
Authorization: Bearer <token>
```

### 📰 新闻资讯接口

#### 获取最新新闻
**用途**: 获取最新的财经新闻

```http
GET /stock/news/latest/?limit=10&category=市场动态
Authorization: Bearer <token>
```

#### 创建新闻 (管理员权限)
**用途**: 发布新的财经新闻

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

### 🔄 数据同步接口 (超级管理员权限)

#### 同步股票基本信息
**用途**: 从Tushare同步最新的股票基本信息

```http
POST /stock/sync/
Authorization: Bearer <token>
Content-Type: application/json

{
    "type": "basic"
}
```

#### 同步股票日线数据
**用途**: 同步指定股票的历史交易数据

```http
POST /stock/sync/
Authorization: Bearer <token>
Content-Type: application/json

{
    "type": "daily",
    "ts_code": "000001.SZ",
    "days": 30
}
```

#### 同步公司信息
**用途**: 同步上市公司基本信息

```http
POST /stock/sync/
Authorization: Bearer <token>
Content-Type: application/json

{
    "type": "company",
    "ts_codes": ["000001.SZ", "000002.SZ"]
}
```

## 🧪 API使用示例

### 1. 基础工作流程

```bash
# 1. 登录获取Token
curl -X POST "http://localhost:8000/user/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "python222", "password": "123456"}'

# 2. 使用Token访问股票列表
curl -X GET "http://localhost:8000/stock/list/?pageSize=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. 查看股票详情
curl -X GET "http://localhost:8000/stock/detail/000001.SZ/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. 买入股票
curl -X POST "http://localhost:8000/trading/buy/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ts_code": "000001.SZ", "price": 11.50, "shares": 100}'
```

### 2. 实时数据刷新示例

```javascript
// 每5秒获取最新股票数据
setInterval(async () => {
    const response = await fetch('http://localhost:8000/stock/list/?pageSize=8', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    const data = await response.json();
    console.log('最新股票数据:', data);
}, 5000);
```

### 3. WebSocket实时推送

```javascript
// 连接WebSocket获取实时数据推送
const ws = new WebSocket(`ws://localhost:8000/ws/stock/realtime/general/?token=${token}`);

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    switch(data.type) {
        case 'market_data':
            console.log('市场数据:', data.data);
            break;
        case 'realtime_data':
            console.log('实时股价:', data.data);
            break;
    }
};

// 订阅特定股票
ws.send(JSON.stringify({
    type: 'subscribe',
    ts_codes: ['000001.SZ', '000002.SZ']
}));
```

## 🔍 错误处理

API返回的错误响应格式统一如下：

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
- `401`: 未认证或Token无效
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

## ⚙️ API 配置说明

### 认证方式
- 使用JWT Bearer Token认证
- Token有效期: 30天
- 需要在请求头中携带: `Authorization: Bearer <token>`

### 请求限制
- 单个API请求超时时间: 30秒
- 批量查询限制: 最多100条记录
- 数据同步接口仅超级管理员可用

### 数据更新频率
- 股票基本信息: 每日更新
- 股票价格数据: 实时更新 (交易时间内)
- 新闻数据: 每小时更新
- 技术指标: 随价格数据实时计算

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

#### 获取技术分析数据

```http
GET /stock/technical/<ts_code>/
Authorization: Bearer <token>

# 响应
{
    "code": 200,
    "msg": "获取成功",
    "data": {
        "ts_code": "000001.SZ",
        "latest_indicators": {
            "ma5": 10.45,
            "ma20": 10.32,
            "rsi": 52.3,
            "macd": {
                "dif": 0.15,
                "dea": 0.12,
                "macd": 0.06
            }
        },
        "full_indicators": {...},  # 完整历史技术指标
        "data_count": 100
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
        "indices": [  # 主要指数数据
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

#### 获取新闻列表（分页）

```http
GET /stock/news/?page=1&pageSize=20&category=&keyword=
Authorization: Bearer <token>
```

#### 获取新闻详情

```http
GET /stock/news/<news_id>/
Authorization: Bearer <token>
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

### 交易相关接口

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

// 取消订阅
ws.send(
  JSON.stringify({
    type: "unsubscribe",
    ts_codes: ["000001.SZ"],
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

#### 手动同步新闻数据

```http
POST /stock/news/sync/
Authorization: Bearer <token>
```

## 部署说明

```bash
# 启动开发服务器（支持WebSocket）
python manage.py runserver

# 或使用ASGI服务器
pip install daphne
daphne -p 8000 app.asgi:application
```

## 注意事项

1. **生产环境部署**时请修改`SECRET_KEY`并关闭`DEBUG`模式
2. **默认管理员账号**：`python222`，密码：`123456`
3. **Tushare API**：需要注册并获取 API Token 才能获取真实股票数据
4. **WebSocket 支持**：需要 ASGI 服务器支持，推荐使用 Daphne 或 Uvicorn
5. **定时任务**：Linux 环境下可使用 crontab，Windows 环境下可使用计划任务
6. **数据库扩展**：支持 PostgreSQL、MySQL 等数据库，需安装相应驱动
7. **Redis 缓存**：生产环境建议配置 Redis 用于 WebSocket 通道层
