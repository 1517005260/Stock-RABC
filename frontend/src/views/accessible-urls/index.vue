<template>
  <div class="accessible-urls-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>我的可访问URL</span>
          <el-button type="primary" @click="refreshData">刷新</el-button>
        </div>
      </template>
      <el-table :data="urlList" style="width: 100%">
        <el-table-column prop="name" label="页面名称" width="180" />
        <el-table-column prop="path" label="URL路径" width="200" />
        <el-table-column label="操作">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click="navigateTo(scope.row.path)"
            >
              访问
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import requestUtil from '@/util/request'
import store from '@/store'

const router = useRouter()
const urlList = ref([])

// 获取用户可访问的URL列表
const fetchAccessibleUrls = async () => {
  try {
    const token = store.getters.getToken
    if (!token) {
      ElMessage.error('请先登录')
      router.push('/login')
      return
    }

    console.log('正在获取可访问URL列表')
    
    const result = await requestUtil.get('user/accessibleUrls')
    console.log('API响应:', result.data)

    if (result.data.code === 200) {
      urlList.value = result.data.accessibleUrls
      console.log('获取到的URL列表:', urlList.value)
    } else {
      ElMessage.error(result.data.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取URL列表失败:', error)
    // 显示更详细的错误信息
    if (error.response) {
      console.error('错误状态:', error.response.status)
      console.error('错误详情:', error.response.data)
      ElMessage.error(`获取URL列表失败: ${error.response.status} ${error.response.statusText || '未知错误'}`)
    } else if (error.request) {
      console.error('请求发送但未收到响应:', error.request)
      ElMessage.error('服务器无响应，请检查后端服务是否正常运行')
    } else {
      console.error('请求配置错误:', error.message)
      ElMessage.error(`请求错误: ${error.message}`)
    }
  }
}

// 刷新数据
const refreshData = () => {
  fetchAccessibleUrls()
}

// 导航到指定路径
const navigateTo = (path) => {
  router.push(path)
  // 添加到标签页
  const name = urlList.value.find(item => item.path === path)?.name || '页面'
  store.commit('ADD_TABS', { name, path })
}

onMounted(() => {
  fetchAccessibleUrls()
})
</script>

<style scoped>
.accessible-urls-container {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 