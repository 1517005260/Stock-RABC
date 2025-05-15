<template>
  <el-tabs
      v-model="editableTabsValue"
      type="card"
      class="demo-tabs"
      closable
      @tab-remove="removeTab"
      @tab-click="clickTab"
  >
    <el-tab-pane
        v-for="(item, index) in editableTabs"
        :key="index"
        :label="item.title"
        :name="item.name"
    />
  </el-tabs>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import store from "@/store";
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

const editableTabsValue = ref('/index')
const editableTabs = ref([{title: '首页', name: '/index'}])

// 安全移除标签页
const removeTab = (targetName) => {
  try {
    if (!targetName) return
    
    store.commit('REMOVE_TAB', targetName)
    
    // 同步本地状态与store状态
    editableTabsValue.value = store.state.editableTabsValue
    editableTabs.value = store.state.editableTabs
    
    // 更新路由
    router.push({path: editableTabsValue.value})
  } catch (error) {
    console.error('移除标签页失败:', error)
    ElMessage.error('操作失败，请重试')
  }
}

// 安全点击标签页
const clickTab = (target) => {
  try {
    if (target && target.props && target.props.name) {
      router.push({path: target.props.name})
    }
  } catch (error) {
    console.error('标签页点击处理失败:', error)
  }
}

// 初始化同步state
const refreshTabs = () => {
  if (store.state.editableTabs && store.state.editableTabs.length) {
    editableTabsValue.value = store.state.editableTabsValue
    editableTabs.value = [...store.state.editableTabs]
  } else {
    // 使用默认值
    editableTabsValue.value = '/index'
    editableTabs.value = [{title: '首页', name: '/index'}]
    
    // 同步回store
    store.commit('RESET_TABS')
  }
}

// 监听store变化
watch(() => store.state.editableTabs, () => {
  refreshTabs()
}, {deep: true})

watch(() => store.state.editableTabsValue, (newVal) => {
  if (newVal) {
    editableTabsValue.value = newVal
  }
})

onMounted(() => {
  refreshTabs()
})
</script>

<style>
.demo-tabs > .el-tabs__content {
  padding: 32px;
  color: #6b778c;
  font-size: 32px;
  font-weight: 600;
}

.el-tabs--card > .el-tabs__header .el-tabs__item.is-active {
  background-color: lightgray;
}

.el-main {
  padding: 0px;
}

.el-tabs__content {
  padding: 0px !important;;
}
</style>