// 引入axios
import axios from 'axios';
import { ElMessage } from 'element-plus'
import router from '@/router'

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
    const token = window.sessionStorage.getItem('token')
    if (token) {
        config.headers.AUTHORIZATION = token
    }
    return config;
}, function (error) {
    // 对请求错误做些什么
    ElMessage.error('请求发送失败')
    return Promise.reject(error);
});

// 添加响应拦截器
httpService.interceptors.response.use(function (response) {
    // 对响应数据做点什么
    // 检查业务逻辑错误
    if (response.data && response.data.code !== 200) {
      // 可以根据不同的错误码做不同处理
      if (response.data.code === 401) {
        ElMessage.error('登录已过期，请重新登录')
        sessionStorage.clear()
        router.replace('/login')
      } else {
        ElMessage.error(response.data.msg || response.data.info || '操作失败')
      }
    }
    return response;
}, function (error) {
    // 对响应错误做点什么
    if (error.response) {
      // 处理不同状态码
      switch (error.response.status) {
        case 401:
          ElMessage.error('您的登录已过期，请重新登录')
          sessionStorage.clear()
          router.replace('/login')
          break
        case 403:
          ElMessage.error('您没有权限进行此操作')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器错误，请联系管理员')
          break
        default:
          ElMessage.error(`请求失败(${error.response.status})`)
      }
    } else if (error.request) {
      ElMessage.error('服务器无响应，请检查网络连接')
    } else {
      ElMessage.error('请求发送失败')
    }
    return Promise.reject(error);
});

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
    del,
    fileUpload,
    getServerUrl
}