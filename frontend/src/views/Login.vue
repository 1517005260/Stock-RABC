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
        >
          <span>登 录</span>

        </el-button>
      </el-form-item>
    </el-form>
    <!-- 底部 -->

  </div>
</template>

<script setup>
import {ref} from 'vue'
import requestUtil from '@/util/request'
import qs from 'qs'
import {ElMessage} from "element-plus";
import Cookies from "js-cookie";
import {encrypt, decrypt} from "@/util/jsencrypt";
import router from "@/router";

const loginForm = ref({
  username: '',
  password: '',
  rememberMe: false
})

const loginRef = ref(null)

const loginRules = {
  username: [{required: true, trigger: "blur", message: "请输入您的账号"}],
  password: [{required: true, trigger: "blur", message: "请输入您的密码"}],
};


const handleLogin = () => {
  loginRef.value.validate(async (valid) => {
    if (valid) {
      let result = await requestUtil.post("user/login?" + qs.stringify(loginForm.value))
      console.log(result)
      let data = result.data
      if (data.code == 200) {
        ElMessage.success(data.info)
        window.sessionStorage.setItem("token", data.token)
        const currentUser = data.user
        currentUser.roles=data.roles
        window.sessionStorage.setItem("currentUser", JSON.stringify(currentUser))
        window.sessionStorage.setItem("menuList", JSON.stringify(data.menuList))
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
        router.replace('/')
      } else {
        ElMessage.error(data.info)
      }
    } else {
      console.log("验证失败")
    }
  })
}

function getCookie() {
  const username = Cookies.get("username");
  const password = Cookies.get("password");
  const rememberMe = Cookies.get("rememberMe");
  loginForm.value = {
    username: username === undefined ? loginForm.value.username : username,
    password: password === undefined ? loginForm.value.password : decrypt(password),
    rememberMe: rememberMe === undefined ? false : Boolean(rememberMe),
  }
}

getCookie();

</script>

<style lang="scss" scoped>
a {
  color: white
}

.login {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
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
</style>