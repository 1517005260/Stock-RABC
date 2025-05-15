# Django Vue3 Admin 前端项目

## 项目简介

这是一个基于 Vue 3 的前端项目，配合 Django 后端实现的权限管理系统。项目使用 Element Plus 作为 UI 组件库，Vue Router 进行路由管理，Vuex 进行状态管理，Axios 进行 HTTP 请求。

## 技术栈

- Vue 3
- Element Plus
- Vue Router 4
- Vuex 4
- Axios
- SVG Icon
- JS-Cookie

## 功能特性

- 用户登录/注销
- 权限管理
- 角色管理
- 菜单管理
- 用户管理
- 个人中心
- 可折叠侧边栏
- 标签页导航

## 环境要求

- Node.js (14.x 或更高版本)
- npm (6.x 或更高版本)

## 项目启动

### 克隆项目

```bash
git clone https://github.com/1517005260/Mini-RABC.git
cd Mini-RABC/frontend
```

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run serve
```

启动成功后，访问 http://localhost:8080 (默认端口)

### 构建生产环境

```bash
npm run build
```

构建完成后，生成的文件将位于`dist`目录中，可以部署到任何静态文件服务器。

## 项目结构

```
frontend/
├── public/                  # 静态资源
├── src/
│   ├── assets/              # 项目资源文件
│   ├── components/          # 通用组件
│   ├── icons/               # SVG图标
│   ├── layout/              # 布局组件
│   ├── router/              # 路由配置
│   ├── store/               # Vuex状态管理
│   ├── util/                # 工具函数
│   ├── views/               # 页面视图
│   ├── App.vue              # 根组件
│   └── main.js              # 入口文件
├── .gitignore               # Git忽略文件
├── babel.config.js          # Babel配置
├── jsconfig.json            # JavaScript配置
├── package.json             # 依赖配置
└── vue.config.js            # Vue配置文件
```

## 后端配置

默认情况下，前端项目会连接到`http://localhost:8000/`作为后端 API 地址。如需修改，请在`src/util/request.js`文件中修改`baseUrl`变量。

```javascript
let baseUrl = "http://localhost:8000/";
```

## 登录信息

- 默认用户名：根据后端设置
- 默认密码：123456 (新用户注册时的默认密码)

## 实现大致思路

### 1. 用户认证流程

- 用户登录时，前端将用户名和密码发送到后端
- 后端验证成功后返回 JWT token 和用户信息
- 前端将 token 存储在 sessionStorage 中
- 后续请求都在 header 中附带 token 进行身份验证

### 2. 权限控制流程

- 用户登录成功后，后端会返回该用户对应的角色和权限菜单
- 前端根据返回的菜单数据动态生成路由和侧边栏
- 每个用户只能看到自己有权限的菜单项和功能按钮

### 3. 界面布局结构

- 采用经典的后台管理布局（顶部导航+侧边栏+内容区）
- 使用标签页形式管理多页面切换
- 布局组件分离，方便维护和扩展

### 4. 数据交互模式

- 统一封装 Axios 请求，处理请求拦截和响应拦截
- 使用 Promise 处理异步请求
- 全局错误处理和消息提示

### 5. 组件化设计

- 每个功能模块独立成组件
- 公共组件抽离复用
- 组件间通信主要通过 props 和事件

## 核心代码

# Django Vue3 Admin 前端项目

## 项目简介

基于 Vue 3 和 Element Plus 的前端管理系统，配合 Django 后端实现 RBAC 权限管理。

## 环境启动

1. 安装依赖

   ```bash
   npm install
   ```

2. 开发环境运行

   ```bash
   npm run serve
   ```

3. 生产环境构建
   ```bash
   npm run build
   ```

## 核心代码实现说明

### 1. 用户认证与权限控制

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

```javascript
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
```

#### 路由配置 (`src/router/index.js`)

```javascript
const routes = [
  {
    path: "/",
    name: "主页",
    component: () => import("../layout/index.vue"),
    redirect: "/index",
    children: [
      // 子路由配置
      {
        path: "/index",
        name: "首页",
        component: () => import("../views/index/index.vue"),
      },
      // 系统管理路由
      {
        path: "/sys/user",
        name: "用户管理",
        component: () => import("../views/sys/user/index.vue"),
      },
      // ...其他路由
    ],
  },
  {
    path: "/login",
    name: "login",
    component: () => import("../views/Login.vue"),
  },
];
```

### 2. 菜单与权限动态加载

#### 动态菜单实现 (`src/layout/menu/index.vue`)

```javascript
<template>
  <el-menu
      active-text-color="#ffd04b"
      background-color="#2d3a4b"
      class="el-menu-vertical-demo"
      text-color="#fff"
      router
      :default-active="'/index'"
  >
    <el-menu-item index="/index" @click="openTab({name:'首页', path:'/index'})">
      <el-icon><home-filled/></el-icon>
      <span>首页</span>
    </el-menu-item>
    <el-sub-menu :index="menu.path" v-for="menu in menuList">
      <template #title>
        <el-icon><svg-icon :icon="menu.icon"/></el-icon>
        <span>{{menu.name}}</span>
      </template>
      <el-menu-item :index="item.path" v-for="item in menu.children" @click="openTab(item)">
        <el-icon><svg-icon :icon="item.icon"/></el-icon>
        <span>{{item.name}}</span>
      </el-menu-item>
    </el-sub-menu>
  </el-menu>
</template>

<script setup>
// 从sessionStorage获取后端返回的菜单数据
const menuList = JSON.parse(sessionStorage.getItem("menuList"))

// 点击菜单时添加标签页
const openTab = (item) => {
  store.commit('ADD_TABS', item)
}
</script>
```

### 3. 标签页导航功能

#### 标签页管理 (`src/store/index.js`)

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
      if (state.editableTabs.findIndex((e) => e.name === tab.path) === -1) {
        state.editableTabs.push({
          title: tab.name,
          name: tab.path,
        });
      }
      state.editableTabsValue = tab.path;
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
// 从Vuex获取标签页数据
const editableTabsValue = ref(store.state.editableTabsValue)
const editableTabs = ref(store.state.editableTabs)

// 关闭标签页
const removeTab = (targetName) => {
  const tabs = editableTabs.value
  let activeName = editableTabsValue.value
  if (activeName === targetName) {
    // 当关闭的是当前激活的标签页时，选择相邻标签页
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
  editableTabs.value = tabs.filter((tab) => tab.name !== targetName)

  // 更新Vuex中的数据
  store.state.editableTabsValue = editableTabsValue.value
  store.state.editableTabs = editableTabs.value

  // 路由跳转
  router.push({path:activeName})
}

// 点击标签页
const clickTab = (target) => {
  router.push({name: target.props.label})
}
</script>
```

### 4. 用户管理功能

#### 用户列表与操作 (`src/views/sys/user/index.vue`)

```javascript
<template>
  <div class="app-container">
    <!-- 搜索和操作按钮 -->
    <el-row :gutter="20" class="header">
      <el-col :span="7">
        <el-input placeholder="请输入用户名..." v-model="queryForm.query" clearable></el-input>
      </el-col>
      <el-button type="primary" :icon="Search" @click="initUserList">搜索</el-button>
      <el-button type="success" :icon="DocumentAdd" @click="handleDialogValue()">新增</el-button>
      <!-- 批量删除 -->
      <el-popconfirm title="您确定批量删除这些记录吗？" @confirm="handleDelete(null)">
        <template #reference>
          <el-button type="danger" :disabled="delBtnStatus" :icon="Delete">批量删除</el-button>
        </template>
      </el-popconfirm>
    </el-row>

    <!-- 用户数据表格 -->
    <el-table :data="tableData" stripe @selection-change="handleSelectionChange">
      <!-- 表格列配置 -->
    </el-table>

    <!-- 分页控件 -->
    <el-pagination
        v-model:currentPage="queryForm.pageNum"
        v-model:page-size="queryForm.pageSize"
        :page-sizes="[10, 20, 30, 40]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
    />

    <!-- 用户编辑对话框 -->
    <Dialog v-model="dialogVisible" :dialogVisible="dialogVisible" :id="id" :dialogTitle="dialogTitle"
            @initUserList="initUserList"></Dialog>

    <!-- 角色分配对话框 -->
    <RoleDialog v-model="roleDialogVisible" :sysRoleList="sysRoleList" :roleDialogVisible="roleDialogVisible" :id="id"
                @initUserList="initUserList"></RoleDialog>
  </div>
</template>

<script setup>
// 查询用户列表
const initUserList = async () => {
  const res = await requestUtil.post("user/search", queryForm.value)
  tableData.value = res.data.userList
  total.value = res.data.total
}

// 删除用户
const handleDelete = async (id) => {
  var ids = []
  if (id) {
    ids.push(id)
  } else {
    multipleSelection.value.forEach(row => {
      ids.push(row.id)
    })
  }
  const res = await requestUtil.del("user/action", ids)
  if (res.data.code == 200) {
    ElMessage.success('执行成功!')
    initUserList();
  }
}

// 重置密码
const handleResetPassword = async (id) => {
  const res = await requestUtil.get("user/resetPassword?id=" + id)
  if (res.data.code == 200) {
    ElMessage.success('执行成功!')
    initUserList();
  }
}
</script>
```

### 5. 角色权限管理功能

#### 角色管理 (`src/views/sys/role/index.vue`)

```javascript
<template>
  <div class="app-container">
    <!-- 表格和搜索区域 -->

    <!-- 角色编辑对话框 -->
    <Dialog v-model="dialogVisible" :dialogVisible="dialogVisible" :id="id" :dialogTitle="dialogTitle"
            @initRoleList="initRoleList"></Dialog>

    <!-- 权限分配对话框 -->
    <MenuDialog v-model="menuDialogVisible" :menuDialogVisible="menuDialogVisible" :id="id"
              @initRoleList="initRoleList"></MenuDialog>
  </div>
</template>

<script setup>
// 查询角色列表
const initRoleList = async () => {
  const res = await requestUtil.post("role/search", queryForm.value)
  tableData.value = res.data.roleList;
  total.value = res.data.total;
}

// 打开权限分配对话框
const handleMenuDialogValue = (roleId) => {
  if (roleId) {
    id.value = roleId;
  }
  menuDialogVisible.value = true
}
</script>
```

#### 权限分配 (`src/views/sys/role/components/menuDialog.vue`)

```javascript
<template>
  <el-dialog
      model-value="menuDialogVisible"
      title="分配权限"
      width="30%"
      @close="handleClose"
  >
    <el-form>
      <!-- 权限树组件 -->
      <el-tree
          ref="treeRef"
          :data="treeData"
          :props="defaultProps"
          show-checkbox
          :default-expand-all="true"
          node-key="id"
          :check-strictly="true"
      />
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button type="primary" @click="handleConfirm">确认</el-button>
        <el-button @click="handleClose">取消</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
// 初始化菜单树和已分配权限
const initFormData = async (id) => {
  // 获取所有菜单树
  const res = await requestUtil.get("menu/treeList");
  treeData.value = res.data.treeList;
  form.value.id = id;

  // 获取角色已分配的菜单ID
  const res2 = await requestUtil.get("role/menus?id=" + id);
  treeRef.value.setCheckedKeys(res2.data.menuIdList);
}

// 保存权限分配
const handleConfirm = async () => {
  // 获取选中的菜单ID
  var menuIds = treeRef.value.getCheckedKeys();

  // 保存分配
  let result = await requestUtil.post("role/grant", {"id": form.value.id, "menuIds": menuIds});
  if (result.data.code == 200) {
    ElMessage.success("执行成功！")
    emits("initRoleList")
    handleClose();
  }
}
</script>
```

### 6. 菜单管理功能

#### 菜单树表 (`src/views/sys/menu/index.vue`)

```javascript
<template>
  <div class="app-container">
    <!-- 新增按钮 -->
    <el-row class="header">
      <el-button type="success" :icon="DocumentAdd" @click="handleDialogValue()">新增</el-button>
    </el-row>

    <!-- 菜单树表 -->
    <el-table
        :data="tableData"
        row-key="id"
        border
        stripe
        default-expand-all
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
    >
      <!-- 表格列配置 -->
    </el-table>
  </div>

  <!-- 菜单编辑对话框 -->
  <Dialog v-model="dialogVisible" :tableData="tableData" :dialogVisible="dialogVisible" :id="id"
          :dialogTitle="dialogTitle" @initMenuList="initMenuList"></Dialog>
</template>

<script setup>
// 获取菜单树形列表
const initMenuList = async () => {
  const res = await requestUtil.get("menu/treeList");
  tableData.value = res.data.treeList;
}

// 删除菜单
const handleDelete = async (id) => {
  const res = await requestUtil.del("menu/action", id)
  if (res.data.code == 200) {
    ElMessage.success('执行成功!')
    initMenuList();
  }
}
</script>
```

### 7. 个人中心功能

#### 个人信息展示与编辑 (`src/views/userCenter/index.vue`)

```javascript
<template>
  <div class="app-container">
    <el-row :gutter="20">
      <!-- 左侧基本信息 -->
      <el-col :span="6">
        <el-card class="box-card">
          <!-- 头像和个人信息 -->
          <div>
            <div class="text-center">
              <avatar :user="currentUser"/>
            </div>
            <ul class="list-group list-group-striped">
              <li class="list-group-item">
                用户名称
                <div class="pull-right">{{ currentUser.username }}</div>
              </li>
              <!-- 其他信息项 -->
            </ul>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧编辑区域 -->
      <el-col :span="18">
        <el-card>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="基本资料" name="userinfo">
              <userInfo :user="currentUser"/>
            </el-tab-pane>
            <el-tab-pane label="修改密码" name="resetPwd">
              <resetPwd :user="currentUser"/>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
// 从sessionStorage获取当前用户信息
const currentUser = JSON.parse(sessionStorage.getItem("currentUser"))
</script>
```

#### 头像上传 (`src/views/userCenter/components/avatar.vue`)

```javascript
<template>
  <el-form style="text-align: center;padding-bottom:10px">
    <el-upload
        name="avatar"
        :headers="headers"
        class="avatar-uploader"
        :action="getServerUrl()+'user/uploadImage'"
        :show-file-list="false"
        :on-success="handleAvatarSuccess"
        :before-upload="beforeAvatarUpload"
    >
      <img v-if="imageUrl" :src="imageUrl" class="avatar"/>
      <el-icon v-else class="avatar-uploader-icon">
        <Plus/>
      </el-icon>
    </el-upload>

    <el-button @click="handleConfirm">确认更换</el-button>
  </el-form>
</template>

<script setup>
// 处理头像上传成功
const handleAvatarSuccess = (res) => {
  imageUrl.value = getServerUrl() + 'media/userAvatar/' + res.title
  form.value.avatar = res.title;
}

// 提交头像更新
const handleConfirm = async () => {
  let result = await requestUtil.post("user/updateAvatar", form.value);
  if (result.data.code == 200) {
    ElMessage.success("执行成功！")
  }
}
</script>
```

### 8. 网络请求封装 (`src/util/request.js`)

```javascript
// 创建axios实例
const httpService = axios.create({
  baseURL: baseUrl,
  timeout: 3000,
});

// 请求拦截器
httpService.interceptors.request.use(
  function (config) {
    config.headers.AUTHORIZATION = window.sessionStorage.getItem("token");
    return config;
  },
  function (error) {
    return Promise.reject(error);
  }
);

// 响应拦截器
httpService.interceptors.response.use(
  function (response) {
    return response;
  },
  function (error) {
    return Promise.reject(error);
  }
);

// GET请求封装
export function get(url, params = {}) {
  return new Promise((resolve, reject) => {
    httpService({
      url: url,
      method: "get",
      params: params,
    })
      .then((response) => {
        resolve(response);
      })
      .catch((error) => {
        reject(error);
      });
  });
}

// POST请求封装
export function post(url, params = {}) {
  return new Promise((resolve, reject) => {
    httpService({
      url: url,
      method: "post",
      data: params,
    })
      .then((response) => {
        console.log(response);
        resolve(response);
      })
      .catch((error) => {
        console.log(error);
        reject(error);
      });
  });
}

// DELETE请求封装
export function del(url, params = {}) {
  return new Promise((resolve, reject) => {
    httpService({
      url: url,
      method: "delete",
      data: params,
    })
      .then((response) => {
        resolve(response);
      })
      .catch((error) => {
        reject(error);
      });
  });
}

// 文件上传封装
export function fileUpload(url, params = {}) {
  return new Promise((resolve, reject) => {
    httpService({
      url: url,
      method: "post",
      data: params,
      headers: { "Content-Type": "multipart/form-data" },
    })
      .then((response) => {
        resolve(response);
      })
      .catch((error) => {
        reject(error);
      });
  });
}
```

### 9. SVG 图标组件实现 (`src/icons/index.js` & `src/components/Svglcon/index.vue`)

```javascript
// icons/index.js
import SvgIcon from '@/components/Svglcon'

const svgRequired = require.context('./svg', false, /\.svg$/)
svgRequired.keys().forEach((item) => svgRequired(item))

export default (app) => {
    app.component('svg-icon', SvgIcon)
}

// components/Svglcon/index.vue
<template>
  <svg class="svg-icon" aria-hidden="true">
    <use :xlink:href="iconName"></use>
  </svg>
</template>

<script setup>
import { defineProps, computed } from 'vue'

const props = defineProps({
  icon: {
    type: String, required: true
  }
})

const iconName = computed(() => {
  return `#icon-${props.icon}`
})
</script>
```

### 10. 密码加密处理 (`src/util/jsencrypt.js`)

```javascript
import JSEncrypt from "jsencrypt/bin/jsencrypt.min";

// 公钥与私钥
const publicKey = "..."; // 实际公钥字符串
const privateKey = "..."; // 实际私钥字符串

// 加密
export function encrypt(txt) {
  const encryptor = new JSEncrypt();
  encryptor.setPublicKey(publicKey);
  return encryptor.encrypt(txt);
}

// 解密
export function decrypt(txt) {
  const encryptor = new JSEncrypt();
  encryptor.setPrivateKey(privateKey);
  return encryptor.decrypt(txt);
}
```
