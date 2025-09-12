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
    <el-menu-item index="/chat" @click="openTab({name:'AI聊天', path:'/chat'})">
      <el-icon>
        <chat-dot-round />
      </el-icon>
      <span>AI聊天助手</span>
    </el-menu-item>

    <!-- 股票交易模块 -->
    <el-sub-menu index="/stock">
      <template #title>
        <el-icon>
          <svg-icon icon="stock" />
        </el-icon>
        <span>股票交易</span>
      </template>
      <el-menu-item index="/stock/dashboard" @click="openTab({name:'股票首页', path:'/stock/dashboard'})">
        <el-icon>
          <svg-icon icon="dashboard"/>
        </el-icon>
        <span>股票首页</span>
      </el-menu-item>
      <el-menu-item index="/stock/list" @click="openTab({name:'股票列表', path:'/stock/list'})">
        <el-icon>
          <svg-icon icon="list"/>
        </el-icon>
        <span>股票列表</span>
      </el-menu-item>
      <el-menu-item index="/stock/watchlist" @click="openTab({name:'自选股票', path:'/stock/watchlist'})">
        <el-icon>
          <svg-icon icon="star"/>
        </el-icon>
        <span>自选股票</span>
      </el-menu-item>
      <el-menu-item index="/stock/positions" @click="openTab({name:'持仓管理', path:'/stock/positions'})">
        <el-icon>
          <svg-icon icon="wallet"/>
        </el-icon>
        <span>持仓管理</span>
      </el-menu-item>
      <el-menu-item index="/stock/records" @click="openTab({name:'交易记录', path:'/stock/records'})">
        <el-icon>
          <svg-icon icon="document"/>
        </el-icon>
        <span>交易记录</span>
      </el-menu-item>
      <el-menu-item index="/stock/account" @click="openTab({name:'账户总览', path:'/stock/account'})">
        <el-icon>
          <svg-icon icon="money"/>
        </el-icon>
        <span>账户总览</span>
      </el-menu-item>
      <el-menu-item index="/stock/news" @click="openTab({name:'股票新闻', path:'/stock/news'})">
        <el-icon>
          <svg-icon icon="news"/>
        </el-icon>
        <span>股票新闻</span>
      </el-menu-item>
    </el-sub-menu>
    <el-sub-menu index="/sys" v-if="hasAdminPermission">
      <template #title>
        <el-icon>
          <svg-icon icon="system"/>
        </el-icon>
        <span>系统管理</span>
      </template>
      <el-menu-item index="/sys/user" @click="openTab({name:'用户管理', path:'/sys/user'})" v-if="hasUserPermission">
        <el-icon>
          <svg-icon icon="user"/>
        </el-icon>
        <span>用户管理</span>
      </el-menu-item>
      <el-menu-item index="/sys/role" @click="openTab({name:'角色管理', path:'/sys/role'})" v-if="hasRolePermission">
        <el-icon>
          <svg-icon icon="peoples"/>
        </el-icon>
        <span>角色管理</span>
      </el-menu-item>
    </el-sub-menu>
    <el-menu-item index="/userCenter" @click="openTab({name:'个人中心', path:'/userCenter'})">
      <el-icon>
        <svg-icon icon="user"/>
      </el-icon>
      <span>个人中心</span>
    </el-menu-item>
    <el-menu-item index="/accessibleUrls" @click="openTab({name:'我的可访问URL', path:'/accessibleUrls'})">
      <el-icon>
        <menu/>
      </el-icon>
      <span>我的可访问URL</span>
    </el-menu-item>
  </el-menu>
</template>

<script setup>
import { computed } from 'vue'
import store from "@/store";
import { useRoute } from 'vue-router'
import { HomeFilled, ChatDotRound, Menu } from '@element-plus/icons-vue'

const route = useRoute()
const defaultActive = computed(() => route.path)

// 检查用户权限
const hasAdminPermission = computed(() => {
  const userRoles = store.getters.getCurrentUser.roles || ''
  return userRoles.includes('超级管理员') || userRoles.includes('管理员')
})

const hasUserPermission = computed(() => {
  const userRoles = store.getters.getCurrentUser.roles || ''
  return userRoles.includes('超级管理员') || userRoles.includes('管理员')
})

const hasRolePermission = computed(() => {
  const userRoles = store.getters.getCurrentUser.roles || ''
  return userRoles.includes('超级管理员')
})

const openTab = (item) => {
  if (item && item.path) {
    store.commit('ADD_TABS', item)
  }
}
</script>

<style lang="scss" scoped>
</style> 