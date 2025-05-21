# Django RBAC 后台系统

这是一个基于 Django 实现的 RBAC（基于角色的访问控制）后台管理系统，提供了用户、角色、菜单权限管理等核心功能和AI聊天功能。本系统使用 JWT 进行身份验证，支持跨域请求，适合作为前后端分离架构下的权限管理系统。

## 技术栈

- **Python**: 3.10+
- **Django**: 5.1.1
- **Django REST Framework**: 3.14.0
- **JWT 认证**: djangorestframework-jwt 1.11.0
- **数据库**: SQLite（可扩展至 PostgreSQL 等）
- **跨域支持**: django-cors-headers 4.7.0
- **OpenAI API**: openai 客户端库

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

### 步骤 4: 配置OpenAI API

创建`.env`文件并配置OpenAI密钥：

```
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# 聊天配置
CHAT_DAILY_LIMIT=5  # 普通用户每日消息限制
```

### 步骤 5: 初始化数据库

```bash
# 执行数据库初始化
python init_db.py

# 初始化数据
python init_data.py
```

### 步骤 6: 启动服务器

```bash
python manage.py runserver
```

此时，服务器将在 `http://localhost:8000/` 运行。

## 项目架构与实现思路

### 项目架构

```
backend/
├── app/                  # 主应用配置
├── chat/                 # AI聊天模块
├── menu/                 # 菜单管理模块
├── role/                 # 角色管理模块
├── user/                 # 用户管理模块
├── utils/                # 工具类
├── manage.py             # Django管理脚本
├── requirements.txt      # 项目依赖
├── init_db.py            # 数据库初始化脚本
└── init_data.py          # 初始数据脚本
```

### 实现思路详解

#### 1. RBAC 权限模型设计

RBAC（Role-Based Access Control）是一种基于角色的访问控制模型，其核心思想是将权限与角色关联，再将角色分配给用户。

**核心实体关系**:
- 用户 (User) ←→ 角色 (Role) ←→ 菜单/权限 (Menu)

**数据库模型**:
1. `SysUser`: 用户信息表
2. `SysRole`: 角色表
3. `SysMenu`: 菜单/权限表
4. `SysUserRole`: 用户-角色关联表
5. `SysRoleMenu`: 角色-菜单关联表

```python
# user/models.py
class SysUser(models.Model):
    """用户表"""
    username = models.CharField(max_length=100, unique=True, verbose_name='用户名')
    password = models.CharField(max_length=100, verbose_name='密码')
    realname = models.CharField(max_length=100, null=True, blank=True, verbose_name='姓名')
    email = models.CharField(max_length=100, null=True, blank=True, verbose_name='邮箱')
    avatar = models.CharField(max_length=200, null=True, blank=True, verbose_name='头像')
    is_enabled = models.BooleanField(default=True, verbose_name='是否启用')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

# role/models.py
class SysRole(models.Model):
    """角色表"""
    name = models.CharField(max_length=100, verbose_name='角色名称')
    code = models.CharField(max_length=100, unique=True, verbose_name='角色编码')
    status = models.BooleanField(default=True, verbose_name='状态')
    sort = models.IntegerField(default=0, verbose_name='排序')
    remark = models.CharField(max_length=500, null=True, blank=True, verbose_name='备注')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

class SysUserRole(models.Model):
    """用户角色关联表"""
    user_id = models.IntegerField(verbose_name='用户ID')
    role_id = models.IntegerField(verbose_name='角色ID')

class SysRoleMenu(models.Model):
    """角色菜单关联表"""
    role_id = models.IntegerField(verbose_name='角色ID')
    menu_id = models.IntegerField(verbose_name='菜单ID')
```

#### 2. JWT认证实现

使用JWT进行用户身份验证，避免使用传统的session管理。

**核心代码实现**:

```python
# user/middleware.py
class JwtAuthenticationMiddleware:
    """JWT认证中间件"""
    def __init__(self, get_response):
        self.get_response = get_response
        # 白名单路径，这些路径不需要验证token
        self.white_list = [
            '/user/login',
            '/favicon.ico',
        ]

    def __call__(self, request):
        # 如果请求路径在白名单中，直接放行
        for path in self.white_list:
            if request.path.startswith(path):
                return self.get_response(request)

        # 获取JWT Token
        token = request.META.get('HTTP_AUTHORIZATION')
        if not token:
            return JsonResponse({
                'code': 401,
                'msg': '未登录或登录已过期'
            })

        try:
            # 解析JWT Token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            # 将用户ID保存到request中，方便后续使用
            request.user_id = payload['user_id']
        except Exception as e:
            return JsonResponse({
                'code': 401,
                'msg': '未登录或登录已过期'
            })

        return self.get_response(request)
```

**登录实现**:

```python
# user/views.py
def login(request):
    """用户登录"""
    try:
        # 获取用户名和密码
        username = request.GET.get('username')
        password = request.GET.get('password')
        
        # 查询用户
        user = SysUser.objects.filter(username=username).first()
        if not user:
            return JsonResponse({'code': 500, 'msg': '用户名或密码错误'})
        
        # 验证密码
        if hashlib.md5(password.encode()).hexdigest() != user.password:
            return JsonResponse({'code': 500, 'msg': '用户名或密码错误'})
        
        # 生成JWT Token
        payload = {
            'user_id': user.id,
            'exp': datetime.datetime.now() + datetime.timedelta(days=1)  # 过期时间1天
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        
        # 获取用户角色
        roles = []
        userRoles = SysUserRole.objects.filter(user_id=user.id)
        for userRole in userRoles:
            role = SysRole.objects.filter(id=userRole.role_id).first()
            if role:
                roles.append({
                    'id': role.id,
                    'name': role.name
                })
        
        # 获取用户菜单权限
        menuList = get_menu_tree_by_user_id(user.id)
        
        # 返回用户信息、Token和菜单权限
        return JsonResponse({
            'code': 200,
            'msg': '登录成功',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'avatar': user.avatar
            },
            'roles': roles,
            'menuList': menuList
        })
    except Exception as e:
        return JsonResponse({'code': 500, 'msg': str(e)})
```

#### 3. 菜单与权限管理

菜单系统支持多级树状结构，每个菜单项可以是目录、菜单或按钮。

**菜单模型**:

```python
# 在role/models.py或单独的menu/models.py中
class SysMenu(models.Model):
    """菜单表"""
    name = models.CharField(max_length=100, verbose_name='菜单名称')
    parent_id = models.IntegerField(default=0, verbose_name='父菜单ID')
    path = models.CharField(max_length=200, null=True, blank=True, verbose_name='路由地址')
    component = models.CharField(max_length=200, null=True, blank=True, verbose_name='组件路径')
    perms = models.CharField(max_length=100, null=True, blank=True, verbose_name='权限标识')
    icon = models.CharField(max_length=100, null=True, blank=True, verbose_name='图标')
    type = models.CharField(max_length=1, choices=(
        ('M', '目录'),
        ('C', '菜单'),
        ('F', '按钮')
    ), verbose_name='菜单类型')
    sort = models.IntegerField(default=0, verbose_name='排序')
    visible = models.BooleanField(default=True, verbose_name='是否可见')
    status = models.BooleanField(default=True, verbose_name='状态')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
```

**构建树状菜单**:

```python
def get_menu_tree_by_user_id(user_id):
    """根据用户ID获取菜单树"""
    # 获取用户角色
    userRoles = SysUserRole.objects.filter(user_id=user_id)
    roleIds = [userRole.role_id for userRole in userRoles]
    
    # 获取角色菜单
    roleMenus = SysRoleMenu.objects.filter(role_id__in=roleIds)
    menuIds = [roleMenu.menu_id for roleMenu in roleMenus]
    
    # 获取菜单
    menus = SysMenu.objects.filter(id__in=menuIds, status=True).order_by('sort')
    
    # 构建树状结构
    return build_tree_menu(menus)

def build_tree_menu(menus, parent_id=0):
    """构建树状菜单"""
    tree = []
    for menu in menus:
        if menu.parent_id == parent_id:
            node = {
                'id': menu.id,
                'name': menu.name,
                'path': menu.path,
                'component': menu.component,
                'icon': menu.icon,
                'type': menu.type,
                'visible': menu.visible,
                'children': build_tree_menu(menus, menu.id)
            }
            tree.append(node)
    return tree
```

#### 4. AI聊天功能实现

集成OpenAI API实现流式聊天功能，使用Server-Sent Events (SSE) 向前端推送数据。

**聊天记录模型**:

```python
# chat/models.py
class ChatMessage(models.Model):
    """聊天消息记录"""
    user_id = models.IntegerField(verbose_name='用户ID')
    content = models.TextField(verbose_name='用户消息')
    response = models.TextField(null=True, blank=True, verbose_name='AI回复')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        ordering = ['-create_time']
```

**实现流式聊天**:

```python
# chat/views.py
@require_http_methods(["POST"])
def chat_stream(request):
    """流式聊天"""
    try:
        # 获取用户ID
        user_id = request.user_id
        
        # 获取当前用户
        user = SysUser.objects.filter(id=user_id).first()
        if not user:
            return HttpResponse(
                f"event: error\ndata: {json.dumps({'error': '用户不存在'})}\n\n",
                content_type="text/event-stream"
            )
        
        # 获取用户角色
        user_roles = SysUserRole.objects.filter(user_id=user_id)
        is_admin = any(
            SysRole.objects.filter(id=role.role_id, code__in=['admin', 'superadmin']).exists()
            for role in user_roles
        )
        
        # 普通用户检查每日聊天限制
        if not is_admin:
            # 获取今日消息数量
            today = datetime.datetime.now().date()
            today_messages_count = ChatMessage.objects.filter(
                user_id=user_id,
                create_time__date=today
            ).count()
            
            # 超过限制返回错误
            daily_limit = int(os.getenv('CHAT_DAILY_LIMIT', 5))
            if today_messages_count >= daily_limit:
                return HttpResponse(
                    f"event: error\ndata: {json.dumps({'error': f'您今日的消息已达上限({daily_limit}条)'})}\n\n",
                    content_type="text/event-stream"
                )
        
        # 解析聊天消息
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        
        if not message:
            return HttpResponse(
                f"event: error\ndata: {json.dumps({'error': '消息不能为空'})}\n\n",
                content_type="text/event-stream"
            )
        
        # 创建消息记录
        chat_record = ChatMessage.objects.create(
            user_id=user_id,
            content=message
        )
        
        # 创建一个流式响应
        response = StreamingHttpResponse(
            stream_openai_response(message, chat_record),
            content_type="text/event-stream"
        )
        response['Cache-Control'] = 'no-cache'
        return response
        
    except Exception as e:
        return HttpResponse(
            f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n",
            content_type="text/event-stream"
        )

def stream_openai_response(message, chat_record):
    """生成OpenAI流式响应"""
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        full_response = ""
        
        # 调用OpenAI API
        stream = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o'),
            messages=[{"role": "user", "content": message}],
            stream=True,
            max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', 2000)),
            temperature=float(os.getenv('OPENAI_TEMPERATURE', 0.7))
        )
        
        # 发送初始消息
        yield f"event: start\ndata: {{}}\n\n"
        
        # 流式发送消息
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                yield f"event: message\ndata: {json.dumps({'content': content})}\n\n"
        
        # 保存完整响应
        chat_record.response = full_response
        chat_record.save()
        
        # 发送结束消息
        yield f"event: end\ndata: {{}}\n\n"
        
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
```

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

### 聊天相关接口

- `POST /chat/stream`: 流式聊天
- `GET /chat/history`: 获取聊天历史

## 注意事项

1. 生产环境部署时请修改`SECRET_KEY`并关闭`DEBUG`模式
2. 默认超级管理员账号：`python222`，密码：`123456`
3. 如需连接 PostgreSQL 等数据库，请安装相应的数据库驱动并修改 settings.py 中的数据库配置
4. 项目默认使用 SQLite 数据库，支持多库配置
