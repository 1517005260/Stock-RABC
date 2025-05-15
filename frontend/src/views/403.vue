<template>
  <div class="unauthorized-container">
    <div class="unauthorized-content">
      <el-result
        icon="warning"
        title="403"
        sub-title="抱歉，您没有访问该页面的权限"
      >
        <template #extra>
          <div class="actions">
            <el-button type="primary" @click="goBack">返回上一页</el-button>
            <el-button @click="goHome">返回首页</el-button>
          </div>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goBack = () => {
  router.go(-1)
}

const goHome = () => {
  router.push('/')
}
</script>

<style scoped lang="scss">
.unauthorized-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.unauthorized-content {
  text-align: center;
  padding: 40px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  max-width: 600px;
  width: 100%;
}

.actions {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 20px;
}
</style> 