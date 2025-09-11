# 股票交易模拟系统 - 前端项目

基于 Vue3 + Element Plus 构建的股票交易模拟系统前端，集成 RBAC 权限管理、实时行情、K 线图表、模拟交易等功能。

## 技术栈

- **Vue 3.2+**: 渐进式 JavaScript 框架
- **Element Plus 2.2+**: Vue3 UI 组件库
- **Vue Router 4.0+**: 官方路由管理器
- **Vuex 4.0+**: 状态管理模式
- **ECharts 5.4+**: 专业数据可视化库
- **Vue-ECharts 6.6+**: ECharts 的 Vue 封装
- **Axios 1.7+**: HTTP 请求库
- **Sass**: CSS 预处理器
- **Moment.js**: 时间处理库
- **Lodash**: JavaScript 实用工具库

## 功能特性

### 📈 股票交易模块

- **股票首页**: 市场概览、热门股票、实时新闻、自选股管理
- **股票列表**: 支持搜索、筛选、分页的股票列表，实时涨跌显示
- **股票详情**: K 线图、技术指标、分时图、公司基本信息
- **模拟交易**: 买入卖出操作、五档盘口、交易记录

### 🔐 权限管理

- **登录认证**: JWT token 身份验证，支持记住密码
- **路由守卫**: 基于权限的路由访问控制
- **角色管理**: 超级管理员、管理员、普通用户三级权限
- **权限验证**: 页面级和功能级权限控制

### 📊 数据可视化

- **K 线图表**: 日 K/周 K/月 K，支持缩放和多种技术指标
- **分时图**: 实时价格走势，5 秒自动刷新
- **成交量图**: 柱状图显示成交量变化
- **技术指标**: MA、MACD、RSI、KDJ、BOLL 等专业分析工具
- **市场概览**: 大盘指数、涨跌统计、资金流向

### 🎯 用户体验

- **响应式设计**: 适配 PC、平板、手机等多种设备
- **标签页导航**: 多页面标签切换，提升工作效率
- **实时数据**: WebSocket 推送，股票价格实时更新
- **错误处理**: 完善的错误边界和友好提示

## 项目结构

```
src/
├── api/                    # API接口管理
│   └── stock.js           # 股票相关接口
├── assets/                 # 静态资源
│   ├── images/            # 图片资源
│   └── styles/            # 全局样式
├── components/            # 公共组件
│   ├── HelloWorld.vue
│   └── SvgIcon/           # SVG图标组件
├── icons/                 # SVG图标集
├── layout/                # 布局组件
│   ├── header/            # 顶部导航
│   ├── menu/              # 侧边菜单
│   └── footer/            # 底部信息
├── router/                # 路由配置
│   └── index.js           # 路由定义和守卫
├── store/                 # Vuex状态管理
├── utils/                 # 工具函数
│   └── request.js         # HTTP请求配置
├── views/                 # 页面组件
│   ├── index/             # 系统首页
│   ├── stock/             # 股票模块
│   │   ├── dashboard/     # 股票仪表板
│   │   ├── list/          # 股票列表
│   │   ├── detail/        # 股票详情
│   │   └── trade/         # 股票交易
│   ├── sys/               # 系统管理
│   │   ├── user/          # 用户管理
│   │   └── role/          # 角色管理
│   ├── userCenter/        # 个人中心
│   ├── chat/              # AI聊天
│   ├── Login.vue          # 登录页
│   └── Register.vue       # 注册页
├── App.vue                # 根组件
└── main.js                # 入口文件
```

## 安装运行

### 环境要求

- Node.js 16+
- NPM 8+ 或 Yarn 1.22+

### 安装依赖

```bash
npm install
# 或
yarn install
```

### 开发环境

```bash
npm run serve
# 或
yarn serve
```

访问: http://localhost:8080

### 生产构建

```bash
npm run build
# 或
yarn build
```

## 主要页面

### 1. 股票首页 (`/stock/dashboard`)

- 市场指数概览（上证、深证、创业板、科创板）
- 热门股票排行榜，支持实时刷新
- 最新市场新闻，点击查看详情
- 我的自选股列表
- 大盘走势图，支持不同周期切换
- 涨跌分布统计和资金流向分析
- 快捷操作入口

### 2. 股票列表 (`/stock/list`)

- 分页显示所有上市股票
- 支持按股票名称、代码搜索
- 按行业和市场类型筛选
- 实时显示股价、涨跌幅、成交量
- 红绿配色显示涨跌状态
- 点击跳转详情页或交易页

### 3. 股票详情 (`/stock/detail/:tsCode`)

- 股票基本信息和实时价格
- 专业 K 线图表，支持日 K/周 K/月 K 切换
- 技术指标计算和展示
- 实时分时图，每 5 秒更新
- 上市公司详细信息
- 快速跳转交易页面

### 4. 股票交易 (`/stock/trade/:tsCode`)

- 买入卖出操作界面
- 实时五档买卖盘口数据
- 分时走势图
- 今日交易记录查询
- 模拟资金和持仓管理
- 快速下单和撤单功能

## API 配置

后端 API 地址配置在 `src/utils/request.js`：

```javascript
const request = axios.create({
  baseURL: process.env.VUE_APP_BASE_API || "http://localhost:8000/api",
  timeout: 15000,
});
```

环境变量配置（.env 文件）：

```
VUE_APP_BASE_API=http://localhost:8000/api
```

## 核心功能实现

### 权限控制

- JWT token 自动附加到请求头
- 路由守卫验证用户权限
- 基于角色的菜单动态生成
- 页面权限和功能权限双重验证

### 实时数据

- WebSocket 连接推送实时股价
- 定时器实现数据自动刷新
- 错误重连机制保证数据连续性

### 图表组件

- ECharts 按需加载，减少打包体积
- 专业股票图表配置
- 响应式图表尺寸自适应
- 丰富的交互功能支持

### 性能优化

- 路由懒加载减少初始加载时间
- 组件按需引入
- 图表数据缓存机制
- 防抖节流优化用户操作
- 虚拟滚动支持大数据量

## 样式规范

### 股票涨跌颜色

```scss
$price-up: #f56c6c; // 上涨红色
$price-down: #67c23a; // 下跌绿色
$price-flat: #909399; // 平盘灰色
```

### 主题色彩

```scss
$primary: #409eff; // 主色调
$success: #67c23a; // 成功色
$warning: #e6a23c; // 警告色
$danger: #f56c6c; // 危险色
```

## 浏览器支持

| Browser | Version |
| ------- | ------- |
| Chrome  | 88+     |
| Firefox | 85+     |
| Safari  | 14+     |
| Edge    | 88+     |

## 开发指南

### 添加新页面

1. 在 `src/views` 目录创建页面组件
2. 在 `src/router/index.js` 添加路由配置
3. 配置页面权限和菜单项
4. 添加 API 接口到 `src/api` 目录

### 添加新图表

1. 在 `main.js` 注册所需 ECharts 组件
2. 创建图表配置对象
3. 使用 `v-chart` 组件渲染
4. 配置响应式和交互功能

### 权限配置

1. 在路由 meta 中配置所需权限
2. 使用路由守卫验证权限
3. 在组件中使用 v-if 控制显示
4. API 请求自动验证权限
