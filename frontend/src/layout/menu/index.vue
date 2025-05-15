<template>
  <el-menu
      active-text-color="#ffd04b"
      background-color="#2d3a4b"
      class="el-menu-vertical-demo"
      text-color="#fff"
      router
      :default-active="defaultActive"
  >
    <el-menu-item index="/index" @click="openTab({name:'首页', path:'/index'})">
      <el-icon>
        <home-filled/>
      </el-icon>
      <span>首页</span>
    </el-menu-item>
    <template v-if="menuList && menuList.length">
      <el-sub-menu :index="menu.path" v-for="(menu, index) in menuList" :key="index">
        <template #title>
          <el-icon>
            <svg-icon :icon="menu.icon || 'dashboard'"/>
          </el-icon>
          <span>{{menu.name}}</span>
        </template>
        <template v-if="menu.children && menu.children.length">
          <el-menu-item 
            :index="item.path" 
            v-for="(item, itemIndex) in menu.children" 
            :key="itemIndex" 
            @click="openTab(item)"
          >
            <el-icon>
              <svg-icon :icon="item.icon || 'form'"/>
            </el-icon>
            <span>{{item.name}}</span>
          </el-menu-item>
        </template>
      </el-sub-menu>
    </template>
  </el-menu>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import store from "@/store";
import { useRoute } from 'vue-router'
import { HomeFilled } from '@element-plus/icons-vue'

const route = useRoute()
const defaultActive = computed(() => route.path)

// 安全地获取菜单数据
const menuList = ref([])

// 从store或sessionStorage获取菜单数据
const loadMenuList = () => {
  try {
    const storedMenuList = sessionStorage.getItem("menuList")
    if (storedMenuList) {
      menuList.value = JSON.parse(storedMenuList)
    } else {
      menuList.value = []
    }
  } catch (error) {
    console.error("加载菜单数据失败:", error)
    menuList.value = []
  }
}

onMounted(() => {
  loadMenuList()
})

const openTab = (item) => {
  if (item && item.path) {
    store.commit('ADD_TABS', item)
  }
}
</script>

<style lang="scss" scoped>
</style>