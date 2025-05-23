// 引入axios
import axios from 'axios';
import { ElMessage } from 'element-plus'
import router from '@/router'
import store from '@/store'

let baseUrl="http://localhost:8000/";
// 创建axios实例
const httpService = axios.create({
    // url前缀
    baseURL: baseUrl,
    // 请求超时时间
    timeout: 10000 // 增加超时时间
});

//添加请求和响应拦截器
// 添加请求拦截器
httpService.interceptors.request.use(function (config) {
    // 在发送请求之前做些什么
    // 优先从Vuex store获取token，确保获取最新token
    const token = store.getters.getToken
    
    if (token) {
        // 确保请求头中带有token
        config.headers.Authorization = `Bearer ${token}`
        // 也添加X-Token头，以兼容某些后端实现
        config.headers['X-Token'] = token
    }
    
    // 打印请求信息，便于调试
    console.log('请求配置:', {
        url: config.url,
        method: config.method,
        headers: config.headers
    })
    
    return config;
}, function (error) {
    // 对请求错误做些什么
    ElMessage.error('请求发送失败')
    return Promise.reject(error);
});

// 添加响应拦截器
httpService.interceptors.response.use(
    response => {
        // 检查是否需要重定向到403页面
        if (response.status === 403 && response.headers['x-error-page'] === '/403') {
            router.push('/403')
            return Promise.reject(new Error(response.data.message || '权限不足'))
        }
        return response
    },
    error => {
        if (error.response) {
            // 检查是否需要重定向到403页面
            if (error.response.status === 403 && error.response.headers['x-error-page'] === '/403') {
                router.push('/403')
                return Promise.reject(new Error(error.response.data.message || '权限不足'))
            }
            
            // 处理其他错误
            if (error.response.status === 401) {
                // token过期或无效
                sessionStorage.removeItem('token')
                sessionStorage.removeItem('currentUser')
                router.push('/login')
            }
            return Promise.reject(error)
        }
        return Promise.reject(error)
    }
)

/*网络请求部分*/

/*
 *  get请求
 *  url:请求地址
 *  params:参数
 * */
export function get(url, params = {}) {
    return new Promise((resolve, reject) => {
        httpService({
            url: url,
            method: 'get',
            params: params
        }).then(response => {
            resolve(response);
        }).catch(error => {
            reject(error);
        });
    });
}

/*
 *  post请求
 *  url:请求地址
 *  params:参数
 * */
export function post(url, params = {}) {
    return new Promise((resolve, reject) => {
        httpService({
            url: url,
            method: 'post',
            data: params
        }).then(response => {
            resolve(response);
        }).catch(error => {
            reject(error);
        });
    });
}

/*
 *  delete请求
 *  url:请求地址
 *  params:参数
 * */
export function del(url, params = {}) {
    return new Promise((resolve, reject) => {
        httpService({
            url: url,
            method: 'delete',
            data: params
        }).then(response => {
            resolve(response);
        }).catch(error => {
            reject(error);
        });
    });
}

/*
 *  put请求
 *  url:请求地址
 *  params:参数
 * */
export function put(url, params = {}) {
    return new Promise((resolve, reject) => {
        httpService({
            url: url,
            method: 'put',
            data: params
        }).then(response => {
            resolve(response);
        }).catch(error => {
            reject(error);
        });
    });
}

/*
 *  文件上传
 *  url:请求地址
 *  params:参数
 * */
export function fileUpload(url, params = {}) {
    return new Promise((resolve, reject) => {
        httpService({
            url: url,
            method: 'post',
            data: params,
            headers: { 'Content-Type': 'multipart/form-data' }
        }).then(response => {
            resolve(response);
        }).catch(error => {
            reject(error);
        });
    });
}

export function getServerUrl(){
    return baseUrl;
}

export default {
    get,
    post,
    put,
    del,
    fileUpload,
    getServerUrl
}