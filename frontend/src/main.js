import { createApp } from 'vue'
import App from './App.vue'
import SvgIcon from '@/icons'
import router from './router'
import store from './store'
import ElementPlus from 'element-plus'
// 国际化中文
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import '@/assets/styles/border.css'
import '@/assets/styles/reset.css'

// createApp(App).use(store).use(router).use(ElementPlus).mount('#app')



const app=createApp(App)
SvgIcon(app);

app.use(store)

app.use(router)

app.use(ElementPlus, {
    locale: zhCn,
})
app.mount('#app')