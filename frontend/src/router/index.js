import {createRouter, createWebHashHistory} from 'vue-router'

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
        component: () => import('../views/index/index.vue')
      },
      {
        path: '/sys/user',
        name: '用户管理',
        component: () => import('../views/sys/user/index.vue')
      },
      {
        path: '/sys/role',
        name: '角色管理',
        component: () => import('../views/sys/role/index.vue')
      },
      {
        path: '/sys/menu',
        name: '菜单管理',
        component: () => import('../views/sys/menu/index.vue')
      },
      {
        path: '/bsns/department',
        name: '部门管理',
        component: () => import('../views/bsns/Department.vue')
      },
      {
        path: '/bsns/post',
        name: '岗位管理',
        component: () => import('../views/bsns/Post.vue')
      },
      {
        path: '/userCenter',
        name: '个人中心',
        component: () => import('../views/userCenter/index.vue')
      }
    ]
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/:pathMatch(.*)*',
    name: '404',
    component: () => import('../views/404.vue')
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 添加路由守卫
router.beforeEach((to, from, next) => {
  const token = sessionStorage.getItem('token')
  
  if (to.path === '/login') {
    if (token) {
      next('/')
    } else {
      next()
    }
  } else {
    if (!token) {
      next('/login')
    } else {
      next()
    }
  }
})

export default router