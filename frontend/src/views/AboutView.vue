<template>

    <el-button type="primary" @click="handleLogin">测试登录</el-button>
    <el-button type="success" @click="handleUserList">测试获取用户信息列表</el-button>

</template>

<script setup>
import requestUtil from '@/util/request'

const handleLogin=async()=>{
  let result=await requestUtil.get("user/jwt_test");
  let data = result.data;
  if(data.code==200){
    const token=data.token;
    console.log("登录成功：token="+ token);
    window.sessionStorage.setItem("token",token)
  }else{
    console.log("登录出错！")
  }
}

const handleUserList=async()=>{
  let result=await requestUtil.get("user/test");
  let data=result.data
  if(data.code==200){
    const userList=data.data;
    console.log("用户列表信息：userList="+userList);
  }else{
    console.log("出错！")
  }
}
</script>
