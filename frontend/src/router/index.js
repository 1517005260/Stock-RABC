import {createRouter, createWebHashHistory} from 'vue-router'
import store from '@/store'
import { ElMessage } from 'element-plus'

const routes = [
  {
    path: '/',
    name: '主页',
    component: () => import('../layout/index.vue'),
    redirect:'/index',
    children:[
      {
        path: '/index',
        name: '首页',
        component: () => import('../views/index/index.vue'),
        meta: { title: '首页', requiresAuth: true }
      },
      {
        path: '/sys/user',
        name: '用户管理',
        component: () => import('../views/sys/user/index.vue'),
        meta: { 
          title: '用户管理', 
          requiresAuth: true,
          permissions: ['system:user:list']
        }
      },
      {
        path: '/sys/role',
        name: '角色管理',
        component: () => import('../views/sys/role/index.vue'),
        meta: { 
          title: '角色管理', 
          requiresAuth: true,
          permissions: ['system:role:list']
        }
      },
      {
        path: '/userCenter',
        name: '个人中心',
        component: () => import('../views/userCenter/index.vue'),
        meta: { title: '个人中心', requiresAuth: true }
      }
    ]
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/403',
    name: '403',
    component: () => import('../views/403.vue'),
    meta: { title: '权限不足', requiresAuth: false }
  },
  {
    path: '/:pathMatch(.*)*',
    name: '404',
    component: () => import('../views/404.vue'),
    meta: { title: '页面不存在', requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 添加路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = to.meta.title + ' - 管理系统'
  }
  
  const token = sessionStorage.getItem('token')
  const currentUser = JSON.parse(sessionStorage.getItem('currentUser') || '{}')
  const userRoles = currentUser.roles || ''
  
  // 如果是前往登录页面
  if (to.path === '/login') {
    if (token) {
      // 已登录，跳转到首页
      next('/')
    } else {
      // 未登录，允许访问登录页
      next()
    }
    return
  }
  
  // 如果是前往其他页面，检查是否已登录
  if (!token) {
    // 未登录，跳转到登录页
    next('/login')
    return
  }
  
  // 检查系统管理相关路由的权限
  if (to.path.startsWith('/sys')) {
    // 检查是否为管理员或超级管理员
    const isAdmin = userRoles.includes('超级管理员') || userRoles.includes('管理员')
    if (!isAdmin) {
      ElMessage.error('权限不足，无法访问')
      next('/403')
      return
    }
    
    // 检查角色管理页面的权限
    if (to.path === '/sys/role' && !userRoles.includes('超级管理员')) {
      ElMessage.error('权限不足，只有超级管理员可以访问角色管理')
      next('/403')
      return
    }
  }
  
  // 检查路由是否需要特定权限
  if (to.meta.permissions && to.meta.permissions.length > 0) {
    const hasPermission = to.meta.permissions.some(permission => 
      store.getters.hasPermission(permission)
    )
    
    if (!hasPermission) {
      ElMessage.error('权限不足，无法访问')
      next('/403')
      return
    }
  }
  
  // 通过所有检查，允许访问
  next()
})

export default router