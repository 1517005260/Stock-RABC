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

const app = createApp(App)

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue错误：', err)
  console.info('错误组件：', vm)
  console.info('错误信息：', info)
}

window.addEventListener('error', (event) => {
  console.error('全局错误：', event.error)
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('未处理的Promise拒绝：', event.reason)
})

SvgIcon(app);

app.use(store)
app.use(router)
app.use(ElementPlus, {
    locale: zhCn,
})
app.mount('#app')