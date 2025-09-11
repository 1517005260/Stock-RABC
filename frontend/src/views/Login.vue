<template>
  <div class="login">
    <el-form ref="loginRef" :model="loginForm" :rules="loginRules" class="login-form">
      <h3 class="title">Django后台管理系统</h3>

      <el-form-item prop="username">
        <el-input
            v-model="loginForm.username"
            type="text"
            size="large"
            auto-complete="off"
            placeholder="账号"
        >
          <template #prefix><svg-icon icon="user" /></template>
        </el-input>
      </el-form-item>
      <el-form-item prop="password">
        <el-input
            v-model="loginForm.password"
            type="password"
            size="large"
            auto-complete="off"
            placeholder="密码"
            @keyup.enter="handleLogin"
        >
          <template #prefix><svg-icon icon="password" /></template>
        </el-input>
      </el-form-item>
      <el-checkbox v-model="loginForm.rememberMe" style="margin:0px 0px 25px 0px;">记住密码</el-checkbox>
      <el-form-item style="width:100%;">
        <el-button
            size="large"
            type="primary"
            style="width:100%;"
            @click.prevent="handleLogin"
            :loading="loading"
        >
          <span>登 录</span>
        </el-button>
      </el-form-item>
      <div class="register-link">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import requestUtil from '@/util/request'
import {ElMessage} from "element-plus";
import Cookies from "js-cookie";
import {encrypt, decrypt} from "@/util/jsencrypt";
import router from "@/router";
import store from "@/store";

const loginForm = ref({
  username: '',
  password: '',
  rememberMe: false
})

const loading = ref(false)
const loginRef = ref(null)

const loginRules = {
  username: [{required: true, trigger: "blur", message: "请输入您的账号"}],
  password: [{required: true, trigger: "blur", message: "请输入您的密码"}],
};

const handleLogin = () => {
  if (loading.value) return
  
  loginRef.value?.validate(async (valid) => {
    if (valid) {
      try {
        loading.value = true
        let result = await requestUtil.post("user/login", loginForm.value)
        let data = result.data
        if (data.code == 200) {
          ElMessage.success(data.info || "登录成功")
          
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
          
          // 勾选了需要记住密码设置在cookie中设置记住用户名和密码
          if (loginForm.value.rememberMe) {
            Cookies.set("username", loginForm.value.username, {expires: 30});
            Cookies.set("password", encrypt(loginForm.value.password), {expires: 30});
            Cookies.set("rememberMe", loginForm.value.rememberMe, {expires: 30});
          } else {
            // 否则移除
            Cookies.remove("username");
            Cookies.remove("password");
            Cookies.remove("rememberMe");
          }
          
          // 重置标签页
          store.commit('RESET_TABS')
          
          // 跳转首页
          router.replace('/')
        } else {
          ElMessage.error(data.info || "登录失败")
        }
      } catch (error) {
        ElMessage.error("登录请求失败，请检查网络连接")
        console.error("登录失败:", error)
      } finally {
        loading.value = false
      }
    } else {
      ElMessage.warning("请正确填写登录信息")
    }
  })
}

// 从Cookie获取记住的登录信息
const getCookie = () => {
  try {
    const username = Cookies.get("username");
    const password = Cookies.get("password");
    const rememberMe = Cookies.get("rememberMe");
    
    if (username) {
      loginForm.value.username = username
    }
    
    if (password) {
      try {
        loginForm.value.password = decrypt(password)
      } catch (e) {
        console.error("密码解密失败:", e)
      }
    }
    
    if (rememberMe) {
      loginForm.value.rememberMe = rememberMe === "true" || rememberMe === true
    }
  } catch (error) {
    console.error("读取Cookie失败:", error)
  }
}

onMounted(() => {
  getCookie();
})
</script>

<style lang="scss" scoped>
a {
  color: white
}

.login {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-image: url("../assets/images/login-background.jpg");
  background-size: cover;
}

.title {
  margin: 0px auto 30px auto;
  text-align: center;
  color: #707070;
}

.login-form {
  border-radius: 6px;
  background: #ffffff;
  width: 400px;
  padding: 25px 25px 5px 25px;

  .el-input {
    height: 40px;

    input {
      display: inline-block;
      height: 40px;
    }
  }

  .input-icon {
    height: 39px;
    width: 14px;
    margin-left: 0px;
  }
}

.login-tip {
  font-size: 13px;
  text-align: center;
  color: #bfbfbf;
}

.login-code {
  width: 33%;
  height: 40px;
  float: right;

  img {
    cursor: pointer;
    vertical-align: middle;
  }
}

.el-login-footer {
  height: 40px;
  line-height: 40px;
  position: fixed;
  bottom: 0;
  width: 100%;
  text-align: center;
  color: #fff;
  font-family: Arial;
  font-size: 12px;
  letter-spacing: 1px;
}

.login-code-img {
  height: 40px;
  padding-left: 12px;
}

.register-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}

.register-link a {
  color: #409EFF;
  text-decoration: none;
}

.register-link a:hover {
  text-decoration: underline;
}
</style>