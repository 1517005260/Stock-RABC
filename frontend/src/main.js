import { createApp } from 'vue'
import App from './App.vue'
import SvgIcon from '@/icons'
import router from './router'
import store from './store'
import ElementPlus from 'element-plus'
import { ElMessage } from 'element-plus'
// 国际化中文
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import '@/assets/styles/border.css'
import '@/assets/styles/reset.css'
// 权限指令
import permissionDirectives from '@/util/permission'

const app = createApp(App)

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue错误：', err)
  console.info('错误组件：', vm)
  console.info('错误信息：', info)
  
  // 如果是权限相关错误，显示更友好的消息
  if (err.message && err.message.includes('permission')) {
    ElMessage.error('权限不足，无法执行该操作')
  } else {
    ElMessage.error('操作出错，请重试或联系管理员')
  }
}

window.addEventListener('error', (event) => {
  console.error('全局错误：', event.error)
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('未处理的Promise拒绝：', event.reason)
  
  // 处理API请求被拒绝的情况
  if (event.reason && event.reason.response) {
    const response = event.reason.response
    if (response.status === 403) {
      ElMessage.error('权限不足，无法执行该操作')
    } else if (response.status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      router.push('/login')
    }
  }
})

SvgIcon(app);

app.use(store)
app.use(router)
app.use(ElementPlus, {
    locale: zhCn,
})
app.use(permissionDirectives)
app.mount('#app')