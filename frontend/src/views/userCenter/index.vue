<script setup>
import { ref, onMounted } from "vue";
import requestUtil from '@/util/request';
import { ElMessage } from 'element-plus';
import avatar from './components/avatar.vue'
import userInfo from './components/userInfo.vue'
import resetPwd from './components/resetPwd.vue'

// 安全获取当前用户信息
const currentUser = ref({})
const activeTab = ref("userinfo");
const loading = ref(false);

const loadUserInfo = async () => {
  try {
    // 首先尝试从sessionStorage获取
    const userString = sessionStorage.getItem("currentUser")
    if (userString) {
      currentUser.value = JSON.parse(userString)
    }
    
    // 如果没有完整数据，尝试从API获取最新数据
    if (!currentUser.value || !currentUser.value.username) {
      loading.value = true
      const res = await requestUtil.get("user/current")
      if (res.data.code === 200) {
        currentUser.value = res.data.user
        sessionStorage.setItem("currentUser", JSON.stringify(res.data.user))
      } else {
        ElMessage.warning("获取用户信息失败")
      }
    }
  } catch (error) {
    console.error("加载用户信息失败:", error)
    ElMessage.error("获取用户数据失败，请刷新页面重试")
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadUserInfo()
})
</script>

<template>
  <div class="app-container">
    <el-skeleton :loading="loading" animated>
      <template #template>
        <div style="padding: 20px;">
          <el-skeleton-item variant="p" style="width: 100%; height: 400px;" />
        </div>
      </template>
      
      <template #default>
        <el-row :gutter="20" v-if="currentUser && currentUser.username">
          <el-col :span="6">
            <el-card class="box-card">
              <template v-slot:header>
                <div class="clearfix">
                  <span>个人信息</span>
                </div>
              </template>
              <div>
                <div class="text-center">
                  <avatar :user="currentUser"/>
                </div>
                <ul class="list-group list-group-striped">
                  <li class="list-group-item">
                    <svg-icon icon="user"/>&nbsp;&nbsp;用户名称
                    <div class="pull-right">{{ currentUser.username || '未设置' }}</div>
                  </li>
                  <li class="list-group-item">
                    <svg-icon icon="phone"/>&nbsp;&nbsp;手机号码
                    <div class="pull-right">{{ currentUser.phonenumber || '未设置' }}</div>
                  </li>
                  <li class="list-group-item">
                    <svg-icon icon="email"/>&nbsp;&nbsp;用户邮箱
                    <div class="pull-right">{{ currentUser.email || '未设置' }}</div>
                  </li>
                  <li class="list-group-item">
                    <svg-icon icon="peoples"/>&nbsp;&nbsp;所属角色
                    <div class="pull-right">{{ currentUser.roles || '无角色' }}</div>
                  </li>
                  <li class="list-group-item">
                    <svg-icon icon="date"/>&nbsp;&nbsp;创建日期
                    <div class="pull-right">{{ currentUser.login_date || '未知' }}</div>
                  </li>
                </ul>
              </div>
            </el-card>
          </el-col>
          <el-col :span="18">
            <el-card>
              <template v-slot:header>
                <div class="clearfix">
                  <span>基本资料</span>
                </div>
              </template>
              <el-tabs v-model="activeTab">
                <el-tab-pane label="基本资料" name="userinfo">
                  <userInfo :user="currentUser"/>
                </el-tab-pane>
                <el-tab-pane label="修改密码" name="resetPwd">
                  <resetPwd :user="currentUser"/>
                </el-tab-pane>
              </el-tabs>
            </el-card>
          </el-col>
        </el-row>
        <el-empty v-else description="用户信息加载失败，请刷新页面重试"></el-empty>
      </template>
    </el-skeleton>
  </div>
</template>

<style scoped lang="scss">
.list-group-striped > .list-group-item {
  border-left: 0;
  border-right: 0;
  border-radius: 0;
  padding-left: 0;
  padding-right: 0;
}

.list-group-item {
  border-bottom: 1px solid #e7eaec;
  border-top: 1px solid #e7eaec;
  margin-bottom: -1px;
  padding: 11px 0;
  font-size: 13px;
}

.pull-right {
  float: right !important;
}

::v-deep .el-card__body {
  min-height: 230px;
}

::v-deep .box-card {
  min-height: 450px;
}
</style>