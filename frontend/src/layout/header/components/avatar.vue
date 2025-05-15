<template>
  <el-dropdown>
    <span class="el-dropdown-link">
      <el-avatar 
        shape="square" 
        :size="40" 
        :src="avatarUrl"
        @error="handleAvatarError"
      />
      &nbsp;&nbsp;{{ getUserName() }}
      <el-icon class="el-icon--right">
        <arrow-down/>
      </el-icon>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item>
          <router-link :to="{name:'个人中心'}">个人中心</router-link>
        </el-dropdown-item>
        <el-dropdown-item @click="logout">安全退出</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'
import requestUtil, {getServerUrl} from '@/util/request'
import router from '@/router'
import store from '@/store'
import { ElMessage } from 'element-plus'

// 默认头像
const defaultAvatar = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAABmJLR0QA/wD/AP+gvaeTAAAFZUlEQVRoge2ZW2wUVRjHf2dm2+1uW7q7pS29UCgexKgYI2g08YKGmHiJxkR9MJjgm5HwRB+Mho0mPJgYiU88PagJpgYfTDQRTAgKRhKREEFEsNyKICBIy7Ld0u7OnPl8aKe0dHfmdBco8f+0+53v8p3fnpk5M2eglVZaaaWVVlpJxJzmUB91E0U9OAQxWYlwFR5zMT6Pnp/WInZDOEg5SJnlmLRGzUeALUA34OILhpCXtDVqTfzzKMZvBl7QFPnYhruAbeamDTaMxgQJ7QFusQnqx2y4wYbNhN8B99rQBeA7YG1SU0xhAC4D4iTdYA2cXyBvgkzQnUljsAHYC6zWlHUDP9rymfJlMaBWoOy03Gi+QOkm2EwYAO7RlAVUzgJ2fGa1DVdYcN9sA5M9j5l4LgBM9OWm4ZJM8yR/lNNAHn+qLYszPx1CpPaGzCID+3Pp6OhKZ4Mnd2KxXXQvzFQqZcXrKbGZR6iRLxR6WrLQgFeVj3Z5RXvLLdYLmspQpJTU5q6s15Rt3nvOzrRr8fHwHC8YVIo+mOYUJvbWWUUm8HBbVe+KzNw0uyQ7oBwQU7JTLdjW5ovF3rxIpZ8G3tIU7whUk6Vq1RyXZhfcA4SqVXPcDrwBnFTwP01Ro24LcSXwIvCbkm9oTbRvxhhYBewE/lLyP6QxIIGXgVO68hDkNIUvAxHQpaRvmOCLT2bgHeB0KoIj1Bb2UxYCJ4BzSazh2MdAlZZbgDuBO4C7Ue7WBogM+CWgLn2jDmZxGwFfhLw5xJPAG8BfKdbxQNJ4+4Cv0C6tNyG0qS5CDQmOivAS4IpUo1MgbRsNOBY3QXqhTkVpQM1FY2Dfg9WTyI5H/cCaCg8CzwMfpB6ZAl3ZsI+AZ4C5QBw4lDQeH45wQ/JWRG2gcCLC/XlDl0RcMfm/AvYCB4BfmLyF+jRlGpLG42eMa05H+Naa4zRPxr2N+zBmI/AGsIzJBbpewX3fjDs4r5xmCmIUBrYCTwFfFCt9lHt7uTg4jwudCzgyNMwvvxdOiXAI+ByYA9yquAQlxeOlRoaLC7p2lKszRylO1MeD+TXlfHDXLBLN5/G7vKLTlJZ7FCUD/Ay8O+c4S3JjeB68/Mlx3v1KfYlvCsIYGXJjLO0e5/NNvbqyIY2JjQOF9RlLPj/GQ2uCFAM/AlNUmPiT7TvLrC0ewpfJr/JOzkzN4GsM3P9mgc17x3m812HjGodcdnZhYFYO3nl8Dj19o6zfdprNe8c5uKXONxM6E48B64rHOLJuHv/EvVw5ItRjZd6sLDu39PLq4H5e+nhU13Ri0DvuseqVEYLgjJuGsb3L2fLYHPJZx6+VYgbkgcKFUTL+PB0NLXjdQTFhp37jXF6VHfgGfBPcl7sWFscPWb9hHhdLRlP2y/r5POKb0TUIN+2jObEZ0zZu/m3o8/qTOJtmwMDjt3Z7vnN8QlNiCNlYaZpvQGhrrUREo2L+lkOTZ0C4J2dYP78x1VFT5zGNP1Y6lTxqRFP4+EZ4blUAEVkPrPKdCWLbAzO8TYsccV0c51bgLV35qysTrCkYB6EH2AG4mvJXVisNnJeQXGf2KeB1oKLgTzfDDVjL4mPcKVmJDhyOO/I9eLvS8JMwHtEYqYKMuSw6L9wfuQ56FJHlIs4aifmlROm6qA1c/qk31yvfTkyoPy/lZMbcGZl8y8VN/mZBj0Y16WZfMjmRIWfqCGbT53/2fZLxoXRWoj4jrugRZJWILDXXxk/Nh0qnIzFjLt29PknTVU3jlbj6tNRo/KdaR38BxpjGl/2ttNJKK620chH4F0QPJG6tcbkXAAAAAElFTkSuQmCC'

// 从存储获取用户数据
const getUserInfo = () => {
  try {
    const userString = sessionStorage.getItem("currentUser")
    if (userString) {
      return JSON.parse(userString)
    }
    return { avatar: 'default.jpg', username: 'unknown' }
  } catch (error) {
    console.error("解析用户信息失败:", error)
    return { avatar: 'default.jpg', username: 'unknown' }
  }
}

// 获取用户头像URL
const avatarUrl = computed(() => {
  const user = getUserInfo()
  if (!user || !user.avatar) {
    return defaultAvatar
  }
  return getServerUrl() + 'media/userAvatar/' + user.avatar
})

// 获取用户名
const getUserName = () => {
  const user = getUserInfo()
  return user?.username || 'unknown'
}

// 头像加载失败处理
const handleAvatarError = () => {
  console.warn("头像加载失败，使用默认头像")
  return true // 使用默认头像
}

const logout = () => {
  try {
    // 使用Vuex的action清理状态
    store.commit('LOGOUT')
    
    // 为了兼容旧代码，也清理sessionStorage
    window.sessionStorage.clear()
    
    // 跳转到登录页
    router.replace("/login")
    
    ElMessage.success("已安全退出")
  } catch (error) {
    console.error("退出登录失败:", error)
    ElMessage.error("退出失败，请重试")
  }
}
</script>

<style lang="scss" scoped>
.el-dropdown-link {
  cursor: pointer;
  color: var(--el-color-primary);
  display: flex;
  align-items: center;
}
</style>