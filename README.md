# RBAC管理系统 + AI聊天功能

这是一个基于Django + Vue3的RBAC权限管理系统，集成了AI聊天功能。

## 特点

- RBAC基础权限管理
- 用户管理和角色控制
- 集成OpenAI API的流式聊天功能
- 用户聊天功能使用频率限制

## 聊天功能说明

该系统集成了与GPT的流式对话功能，具有以下特点：

1. 真实流式响应：使用Server-Sent Events实现实时流式聊天效果
2. 用户权限区分：
   - 普通用户：每日限制发送5条消息
   - 管理员和超级管理员：无聊天次数限制
3. 历史消息记录：自动保存并展示历史对话

## 环境要求

- Python 3.10+
- Node.js 16+
- Django 5.1+
- Vue 3
- OpenAI API密钥

## 安装与配置

### 后端配置

1. 安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 创建`.env`文件并配置OpenAI密钥：
```
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# 聊天配置
CHAT_DAILY_LIMIT=5  # 普通用户每日消息限制
```

3. 运行数据库迁移：
```bash
python manage.py makemigrations
python manage.py migrate
```

4. 启动后端服务：
```bash 
python manage.py runserver
```

### 前端配置

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器：
```bash
npm run serve
```

## 使用说明

1. 注册并登录系统
2. 在左侧菜单找到"AI聊天助手"
3. 开始与AI进行对话
4. 普通用户每天最多发送5条消息，管理员和超级管理员无限制

## 技术实现

- 后端：Django + Django REST Framework + OpenAI API
- 前端：Vue 3 + Element Plus + Axios
- 实时通讯：Server-Sent Events (SSE)
