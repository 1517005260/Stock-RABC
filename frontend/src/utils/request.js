import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const request = axios.create({
  baseURL: process.env.VUE_APP_BASE_API || 'http://localhost:8000',
  timeout: 15000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 在发送请求之前做些什么
    const token = sessionStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    // 对请求错误做些什么
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    // 对响应数据做点什么
    return response
  },
  error => {
    // 对响应错误做点什么
    let message = '请求失败'
    
    if (error.response) {
      // 请求已发出，服务器以状态码响应
      const { status, data } = error.response
      
      switch (status) {
        case 400:
          message = data.msg || '请求参数错误'
          break
        case 401:
          message = '认证失败，请重新登录'
          // 清除token
          sessionStorage.removeItem('token')
          sessionStorage.removeItem('currentUser')
          // 跳转到登录页
          window.location.href = '#/login'
          break
        case 403:
          message = '权限不足'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 500:
          message = '服务器内部错误'
          break
        default:
          message = data.msg || `请求失败 (${status})`
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      message = '网络连接失败，请检查网络'
    } else {
      // 在设置请求时发生了一些事情，触发了错误
      message = error.message || '请求配置错误'
    }
    
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default request