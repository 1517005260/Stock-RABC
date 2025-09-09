# 股票交易系统角色权限设计

## 角色权限体系

### 1. 普通用户 (user)
**权限范围**: 基础交易功能
- 查看股票列表和基本信息
- 查看股票实时行情和K线图
- 查看自己的持仓和交易记录
- 进行股票买入/卖出操作
- 管理自选股
- 查看市场新闻
- 查看公司基本信息
- 修改个人信息
- 初始资金: 100,000元

### 2. 管理员 (admin)  
**权限范围**: 普通用户权限 + 用户管理
- 拥有普通用户所有权限
- 查看所有用户列表
- 查看用户交易记录和持仓
- 冻结/解冻用户账户
- 重置用户密码
- 管理市场新闻
- 查看系统统计数据
- 初始资金: 500,000元

### 3. 超级管理员 (superadmin)
**权限范围**: 管理员权限 + 系统管理
- 拥有管理员所有权限  
- 管理股票基础数据
- 更新股票行情数据
- 系统配置管理
- 角色权限管理
- 数据导入/导出
- 系统监控和日志
- 无资金限制

## 权限控制实现

### 装饰器权限控制
```python
def require_role(allowed_roles):
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            user_roles = get_user_roles(request.user_id)
            if not any(role.code in allowed_roles for role in user_roles):
                return JsonResponse({'code': 403, 'msg': '权限不足'})
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@require_role(['user', 'admin', 'superadmin'])  # 所有用户可访问
def stock_list(request):
    pass

@require_role(['admin', 'superadmin'])  # 仅管理员可访问  
def user_management(request):
    pass

@require_role(['superadmin'])  # 仅超级管理员可访问
def system_config(request):
    pass
```

### API权限矩阵

| 功能模块 | API接口 | 普通用户 | 管理员 | 超级管理员 |
|---------|--------|---------|--------|-----------|
| 股票信息 | GET /stock/list | ✓ | ✓ | ✓ |
| 股票信息 | GET /stock/detail/{code} | ✓ | ✓ | ✓ |
| 股票交易 | POST /trading/buy | ✓ | ✓ | ✓ |
| 股票交易 | POST /trading/sell | ✓ | ✓ | ✓ |
| 持仓管理 | GET /trading/positions | ✓ | ✓ | ✓ |
| 交易记录 | GET /trading/records | ✓ | ✓ | ✓ |
| 用户管理 | GET /admin/users | ✗ | ✓ | ✓ |
| 用户管理 | POST /admin/user/freeze | ✗ | ✓ | ✓ |
| 数据管理 | POST /admin/data/update | ✗ | ✗ | ✓ |
| 系统配置 | GET /admin/system/config | ✗ | ✗ | ✓ |

### 数据权限控制

#### 普通用户
- 只能查看和操作自己的数据
- 交易记录、持仓信息按user_id过滤

#### 管理员  
- 可以查看所有用户的交易数据
- 可以管理普通用户账户
- 不能操作其他管理员账户

#### 超级管理员
- 可以查看和操作所有数据
- 可以管理所有角色的用户
- 拥有系统级别的操作权限

## 初始化数据

### 默认角色数据
```sql
INSERT INTO sys_role (name, code, create_time, remark) VALUES
('普通用户', 'user', NOW(), '基础交易功能权限'),
('管理员', 'admin', NOW(), '用户管理和数据查看权限'),  
('超级管理员', 'superadmin', NOW(), '系统管理和所有权限');
```

### 默认用户账户
```sql
-- 测试用普通用户
INSERT INTO sys_user (username, password, status, create_time) VALUES
('trader001', MD5('123456'), 0, NOW()),
('trader002', MD5('123456'), 0, NOW());

-- 测试用管理员
INSERT INTO sys_user (username, password, status, create_time) VALUES  
('admin001', MD5('123456'), 0, NOW());

-- 超级管理员 (保持原有)
-- username: python222, password: 123456
```

这个权限设计既保持了原有RBAC系统的完整性，又满足了股票交易系统的业务需求。