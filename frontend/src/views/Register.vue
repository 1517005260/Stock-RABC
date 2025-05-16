<template>
  <div class="register">
    <el-form ref="registerRef" :model="registerForm" :rules="registerRules" class="register-form">
      <h3 class="title">用户注册</h3>

      <el-form-item prop="username">
        <el-input
            v-model="registerForm.username"
            type="text"
            size="large"
            auto-complete="off"
            placeholder="请输入用户名"
        >
          <template #prefix><svg-icon icon="user" /></template>
        </el-input>
      </el-form-item>

      <el-form-item prop="password">
        <el-input
            v-model="registerForm.password"
            type="password"
            size="large"
            auto-complete="off"
            placeholder="请输入密码"
        >
          <template #prefix><svg-icon icon="password" /></template>
        </el-input>
      </el-form-item>

      <el-form-item prop="confirmPassword">
        <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            size="large"
            auto-complete="off"
            placeholder="请确认密码"
        >
          <template #prefix><svg-icon icon="password" /></template>
        </el-input>
      </el-form-item>

      <el-form-item prop="email">
        <el-input
            v-model="registerForm.email"
            type="text"
            size="large"
            auto-complete="off"
            placeholder="请输入邮箱（选填）"
        >
          <template #prefix><svg-icon icon="email" /></template>
        </el-input>
      </el-form-item>

      <el-form-item style="width:100%;">
        <el-button
            size="large"
            type="primary"
            style="width:100%;"
            @click.prevent="handleRegister"
            :loading="loading"
        >
          <span>注 册</span>
        </el-button>
      </el-form-item>

      <div class="login-link">
        已有账号？<router-link to="/login">立即登录</router-link>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import requestUtil from '@/util/request'
import { ElMessage } from "element-plus"
import router from "@/router"
import store from "@/store"

const registerForm = ref({
  username: '',
  password: '',
  confirmPassword: '',
  email: ''
})

const loading = ref(false)
const registerRef = ref(null)

const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请输入密码'))
  } else {
    if (registerForm.value.confirmPassword !== '') {
      registerRef.value?.validateField('confirmPassword')
    }
    callback()
  }
}

const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.value.password) {
    callback(new Error('两次输入密码不一致!'))
  } else {
    callback()
  }
}

const registerRules = {
  username: [
    { required: true, trigger: "blur", message: "请输入用户名" },
    { min: 3, max: 20, message: "用户名长度必须在3-20个字符之间", trigger: "blur" }
  ],
  password: [
    { required: true, validator: validatePass, trigger: "blur" },
    { min: 6, message: "密码长度不能小于6个字符", trigger: "blur" }
  ],
  confirmPassword: [
    { required: true, validator: validatePass2, trigger: "blur" }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const handleRegister = () => {
  if (loading.value) return
  
  registerRef.value?.validate(async (valid) => {
    if (valid) {
      try {
        loading.value = true
        let result = await requestUtil.post("user/register", registerForm.value)
        let data = result.data
        if (data.code == 200) {
          ElMessage.success(data.info || "注册成功")
          
          // 使用Vuex存储登录状态
          store.commit('SET_TOKEN', data.token)
          store.commit('SET_CURRENT_USER', data.user)
          
          // 存储权限信息
          if (data.permissions) {
            store.commit('SET_PERMISSIONS', data.permissions)
          }
          
          // 也存在sessionStorage中，兼容旧代码
          window.sessionStorage.setItem("token", data.token)
          window.sessionStorage.setItem("currentUser", JSON.stringify(data.user))
          
          // 重置标签页
          store.commit('RESET_TABS')
          
          // 跳转首页
          router.replace('/')
        } else {
          ElMessage.error(data.info || "注册失败")
        }
      } catch (error) {
        console.error('注册失败:', error)
        ElMessage.error("注册失败，请稍后重试")
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.register {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-image: url("../assets/images/login-background.jpg");
  background-size: cover;
}

.register-form {
  border-radius: 6px;
  background: #ffffff;
  width: 400px;
  padding: 25px 25px 5px 25px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.title {
  margin: 0px auto 30px auto;
  text-align: center;
  color: #707070;
}

.login-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}

.login-link a {
  color: #409EFF;
  text-decoration: none;
}

.login-link a:hover {
  text-decoration: underline;
}
</style> 