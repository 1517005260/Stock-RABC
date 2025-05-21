# Vue 3 RBAC 前端系统

这是一个基于 Vue 3 和 Element Plus 的前端系统，配合 Django 后端实现的 RBAC 权限管理和 AI 聊天功能。项目采用组件化设计，使用 Vue Router 进行路由管理，Vuex 进行状态管理。

## 技术栈

- **Vue 3**: 核心框架
- **Element Plus**: UI 组件库
- **Vue Router 4**: 路由管理
- **Vuex 4**: 状态管理
- **Axios**: HTTP 请求
- **SVG Icon**: 图标管理
- **JS-Cookie**: Cookie 管理

## 功能特性

- 用户登录/注销
- 权限管理
- 角色管理
- 菜单管理
- 用户管理
- AI 聊天助手
- 可折叠侧边栏
- 标签页导航

## 环境要求

- **Node.js**: 14.x 或更高版本
- **npm**: 6.x 或更高版本

## 安装与启动

### 克隆项目

```bash
git clone https://github.com/1517005260/Mini-RABC.git
cd Mini-RABC/frontend
```

### 安装依赖

```bash
npm install
```

如果遇到依赖问题，可以尝试：

```bash
# 安装核心依赖
npm install @vue/cli-service
```

### 开发环境启动

```bash
npm run serve
```

启动成功后，访问 http://localhost:8080

### 生产环境构建

```bash
npm run build
```

构建完成后，生成的文件将位于 `dist` 目录中，可以部署到任何静态文件服务器。

## 项目结构

```
frontend/
├── public/              # 静态资源
├── src/
│   ├── assets/          # 资源文件
│   ├── components/      # 公共组件
│   ├── icons/           # SVG图标
│   ├── layout/          # 布局组件
│   ├── router/          # 路由配置
│   ├── store/           # Vuex状态管理
│   ├── util/            # 工具函数
│   ├── views/           # 页面视图
│   ├── App.vue          # 根组件
│   └── main.js          # 入口文件
├── babel.config.js      # Babel配置
├── package.json         # 依赖配置
└── vue.config.js        # Vue配置
```

## 实现思路与核心代码

### 1. 用户认证与权限控制

用户认证采用基于 JWT 的无状态认证方式，确保系统安全和可扩展性。

#### 登录实现 (`src/views/Login.vue`)

```javascript
const handleLogin = () => {
  loginRef.value.validate(async (valid) => {
    if (valid) {
      let result = await requestUtil.post(
        "user/login?" + qs.stringify(loginForm.value)
      );
      let data = result.data;
      if (data.code == 200) {
        // 登录成功，存储token和用户信息
        window.sessionStorage.setItem("token", data.token);
        const currentUser = data.user;
        currentUser.roles = data.roles;
        window.sessionStorage.setItem(
          "currentUser",
          JSON.stringify(currentUser)
        );
        window.sessionStorage.setItem(
          "menuList",
          JSON.stringify(data.menuList)
        );

        // 记住密码功能
        if (loginForm.value.rememberMe) {
          Cookies.set("username", loginForm.value.username, { expires: 30 });
          Cookies.set("password", encrypt(loginForm.value.password), {
            expires: 30,
          });
          Cookies.set("rememberMe", loginForm.value.rememberMe, {
            expires: 30,
          });
        }
        router.replace("/");
      }
    }
  });
};
```

#### 请求拦截器 (`src/util/request.js`)

确保每次请求自动附加 JWT Token 到请求头：

```javascript
let baseUrl = "http://localhost:8000/";

// 创建axios实例
const httpService = axios.create({
  baseURL: baseUrl,
  timeout: 30000,
});

// 添加请求拦截器，自动添加token
httpService.interceptors.request.use(
  function (config) {
    config.headers.AUTHORIZATION = window.sessionStorage.getItem("token");
    return config;
  },
  function (error) {
    return Promise.reject(error);
  }
);

// 添加响应拦截器
httpService.interceptors.response.use(
  function (response) {
    // 当返回的状态码为401时，表示token已过期，需要重新登录
    if (response.data.code === 401) {
      window.sessionStorage.clear();
      router.replace("/login");
    }
    return response;
  },
  function (error) {
    ElMessage.error("请求失败");
    return Promise.reject(error);
  }
);
```

### 2. 动态菜单与路由

系统基于用户角色动态生成菜单和路由，确保用户只能访问有权限的功能。

#### 动态菜单实现 (`src/layout/menu/index.vue`)

```javascript
<template>
  <el-menu
      active-text-color="#ffd04b"
      background-color="#2d3a4b"
      class="el-menu-vertical-demo"
      text-color="#fff"
      router
      :default-active="activePath"
  >
    <el-menu-item index="/index" @click="openTab({name:'首页', path:'/index'})">
      <el-icon><home-filled/></el-icon>
      <span>首页</span>
    </el-menu-item>
    <el-sub-menu :index="menu.path" v-for="menu in menuList" :key="menu.id">
      <template #title>
        <el-icon><svg-icon :icon="menu.icon"/></el-icon>
        <span>{{menu.name}}</span>
      </template>
      <el-menu-item 
        :index="item.path" 
        v-for="item in menu.children" 
        :key="item.id"
        @click="openTab(item)"
      >
        <el-icon><svg-icon :icon="item.icon"/></el-icon>
        <span>{{item.name}}</span>
      </el-menu-item>
    </el-sub-menu>
  </el-menu>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useRoute } from 'vue-router'

const store = useStore()
const route = useRoute()

// 从sessionStorage获取后端返回的菜单数据
const menuList = JSON.parse(sessionStorage.getItem("menuList") || "[]")

// 激活的菜单项
const activePath = computed(() => route.path)

// 点击菜单时添加标签页
const openTab = (item) => {
  store.commit('ADD_TABS', {
    title: item.name,
    name: item.path
  })
}
</script>
```

### 3. 标签页导航

使用标签页形式管理多页面切换，提升用户体验和工作效率。

#### Vuex 状态管理 (`src/store/index.js`)

```javascript
export default createStore({
  state: {
    editableTabsValue: "/index",
    editableTabs: [
      {
        title: "首页",
        name: "/index",
      },
    ],
  },
  mutations: {
    // 添加标签页
    ADD_TABS: (state, tab) => {
      if (state.editableTabs.findIndex((e) => e.name === tab.name) === -1) {
        state.editableTabs.push({
          title: tab.title,
          name: tab.name,
        });
      }
      state.editableTabsValue = tab.name;
    },
    // 重置标签页
    RESET_TABS: (state) => {
      state.editableTabsValue = "/index";
      state.editableTabs = [
        {
          title: "首页",
          name: "/index",
        },
      ];
    },
  },
});
```

#### 标签页组件 (`src/layout/tabs/index.vue`)

```javascript
<template>
  <el-tabs
      v-model="editableTabsValue"
      type="card"
      class="demo-tabs"
      closable
      @tab-remove="removeTab"
      @tab-click="clickTab"
  >
    <el-tab-pane
        v-for="item in editableTabs"
        :key="item.name"
        :label="item.title"
        :name="item.name"
    />
  </el-tabs>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'

const store = useStore()
const router = useRouter()
const route = useRoute()

// 使用计算属性从Vuex获取标签页数据
const editableTabsValue = computed({
  get: () => store.state.editableTabsValue,
  set: (val) => store.state.editableTabsValue = val
})
const editableTabs = computed(() => store.state.editableTabs)

// 监听路由变化，添加标签页
watch(() => route.path, (newPath) => {
  if (newPath !== '/login') {
    store.commit('ADD_TABS', {
      title: route.meta.title || route.name,
      name: newPath
    })
  }
}, { immediate: true })

// 关闭标签页
const removeTab = (targetName) => {
  const tabs = [...editableTabs.value]
  let activeName = editableTabsValue.value
  if (activeName === targetName) {
    tabs.forEach((tab, index) => {
      if (tab.name === targetName) {
        const nextTab = tabs[index + 1] || tabs[index - 1]
        if (nextTab) {
          activeName = nextTab.name
        }
      }
    })
  }
  
  editableTabsValue.value = activeName
  store.state.editableTabs = tabs.filter(tab => tab.name !== targetName)
  
  // 路由跳转
  router.push(activeName)
}

// 点击标签页
const clickTab = (tab) => {
  router.push(tab.props.name)
}
</script>
```

### 4. RBAC 管理模块

系统实现了完整的 RBAC 权限管理功能，包括用户、角色、菜单的管理和权限分配。

#### 用户管理 (`src/views/sys/user/index.vue`)

```javascript
<template>
  <div>
    <!-- 搜索栏 -->
    <el-form :inline="true" :model="searchForm" class="demo-form-inline">
      <el-form-item label="用户名">
        <el-input v-model="searchForm.username" placeholder="用户名" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button type="success" @click="handleAdd">添加</el-button>
      </el-form-item>
    </el-form>
    
    <!-- 用户列表 -->
    <el-table :data="tableData" stripe style="width: 100%">
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="realname" label="姓名" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column label="状态">
        <template #default="scope">
          <el-switch
            v-model="scope.row.is_enabled"
            @change="handleStatusChange(scope.row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="320">
        <template #default="scope">
          <el-button type="primary" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button type="danger" @click="handleDelete(scope.row)">删除</el-button>
          <el-button type="warning" @click="handleResetPwd(scope.row)">重置密码</el-button>
          <el-button type="success" @click="handleGrant(scope.row)">授权</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <el-pagination
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
      :current-page="searchForm.pageNum"
      :page-sizes="[10, 20, 50, 100]"
      :page-size="searchForm.pageSize"
      layout="total, sizes, prev, pager, next, jumper"
      :total="total"
    />
    
    <!-- 用户表单对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="40%">
      <el-form :model="form" label-width="80px" :rules="rules" ref="formRef">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" autocomplete="off" />
        </el-form-item>
        <el-form-item label="姓名" prop="realname">
          <el-input v-model="form.realname" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSave">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 角色授权对话框 -->
    <el-dialog v-model="grantDialogVisible" title="角色授权" width="30%">
      <el-checkbox-group v-model="selectedRoles">
        <el-checkbox v-for="role in rolesList" :key="role.id" :label="role.id">
          {{ role.name }}
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="grantDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleGrantSave">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>
```

### 5. AI 聊天功能

实现了与 OpenAI 的流式对话功能，提供自然的聊天体验。

#### 聊天组件 (`src/views/chat/index.vue`)

```javascript
<template>
  <div class="chat-container">
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
        <div class="avatar">
          <img :src="msg.role === 'user' ? userAvatar : botAvatar" alt="avatar">
        </div>
        <div class="content">
          <div class="name">{{ msg.role === 'user' ? '你' : 'AI助手' }}</div>
          <div class="text" v-html="formatMessage(msg.content)"></div>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="2"
        placeholder="输入消息..."
        @keyup.enter.native="sendMessage"
      />
      <el-button type="primary" @click="sendMessage" :loading="loading">发送</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue';
import { ElMessage } from 'element-plus';
import marked from 'marked';
import DOMPurify from 'dompurify';
import requestUtil from '@/util/request';

// 用户头像
const userAvatar = computed(() => {
  const user = JSON.parse(sessionStorage.getItem('currentUser') || '{}');
  return user.avatar || require('@/assets/user-avatar.png');
});
const botAvatar = require('@/assets/bot-avatar.png');

// 消息列表
const messages = ref([]);
const inputMessage = ref('');
const loading = ref(false);
const messagesContainer = ref(null);

// 获取聊天历史
const getChatHistory = async () => {
  try {
    const res = await requestUtil.get('chat/history');
    if (res.data.code === 200) {
      const history = res.data.data;
      history.forEach(item => {
        messages.value.push({
          role: 'user',
          content: item.content
        });
        
        if (item.response) {
          messages.value.push({
            role: 'assistant',
            content: item.response
          });
        }
      });
      
      // 滚动到底部
      nextTick(() => {
        scrollToBottom();
      });
    }
  } catch (error) {
    ElMessage.error('获取聊天历史失败');
  }
};

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim()) return;
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: inputMessage.value.trim()
  });
  
  // 清空输入框
  const userMessage = inputMessage.value.trim();
  inputMessage.value = '';
  
  // 滚动到底部
  nextTick(() => {
    scrollToBottom();
  });
  
  // 正在加载状态
  loading.value = true;
  
  // 添加AI消息占位
  const aiMessageIndex = messages.value.length;
  messages.value.push({
    role: 'assistant',
    content: ''
  });
  
  try {
    // 创建EventSource连接
    const eventSource = new EventSource(`http://localhost:8000/chat/stream?message=${encodeURIComponent(userMessage)}`);
    
    eventSource.addEventListener('start', () => {
      console.log('Chat stream started');
    });
    
    eventSource.addEventListener('message', (event) => {
      const data = JSON.parse(event.data);
      if (data.content) {
        // 追加内容
        messages.value[aiMessageIndex].content += data.content;
        
        // 滚动到底部
        nextTick(() => {
          scrollToBottom();
        });
      }
    });
    
    eventSource.addEventListener('end', () => {
      eventSource.close();
      loading.value = false;
    });
    
    eventSource.addEventListener('error', (event) => {
      const data = event.data ? JSON.parse(event.data) : { error: '连接错误' };
      ElMessage.error(data.error || '聊天请求失败');
      eventSource.close();
      loading.value = false;
      
      // 如果消息为空，移除AI消息
      if (!messages.value[aiMessageIndex].content) {
        messages.value.splice(aiMessageIndex, 1);
      }
    });
  } catch (error) {
    ElMessage.error('发送消息失败');
    loading.value = false;
    
    // 如果消息为空，移除AI消息
    if (!messages.value[aiMessageIndex].content) {
      messages.value.splice(aiMessageIndex, 1);
    }
  }
};

// 格式化消息，支持Markdown
const formatMessage = (content) => {
  return DOMPurify.sanitize(marked(content));
};

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

onMounted(() => {
  getChatHistory();
});
</script>
```

## 配置后端连接

默认情况下，前端项目会连接到 `http://localhost:8000/` 作为后端 API 地址。如需修改，请在 `src/util/request.js` 文件中更新 `baseUrl` 变量：

```javascript
let baseUrl = "http://your-backend-url/";
```
