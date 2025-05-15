<template>
  <div class="not-found">
    <div class="container">
      <h1>404</h1>
      <h2>页面不存在</h2>
      <p>您访问的页面不存在或已被删除</p>
      <el-button type="primary" @click="goHome">返回首页</el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<style scoped>
.not-found {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f5f5;
}

.container {
  text-align: center;
  padding: 40px;
  border-radius: 8px;
  background-color: white;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
}

h1 {
  font-size: 80px;
  margin: 0;
  color: #409eff;
}

h2 {
  font-size: 32px;
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
}

p {
  font-size: 18px;
  color: #666;
  margin-bottom: 30px;
}
</style>