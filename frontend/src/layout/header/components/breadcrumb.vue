<template>
  <el-icon>
    <HomeFilled/>
  </el-icon>
  <el-breadcrumb separator="/">
    <el-breadcrumb-item v-for="(item,index) in breadcrumbList"><span>{{ item.name }}</span></el-breadcrumb-item>

  </el-breadcrumb>
</template>


<script setup>
import {HomeFilled} from '@element-plus/icons-vue'
import {ref, watch} from 'vue'
import {useRoute} from 'vue-router'
import store from "@/store";

const route=useRoute()

const breadcrumbList=ref([])

const initBreadcrumbList=()=>{
  breadcrumbList.value=route.matched;
}
watch(route,()=>{
  initBreadcrumbList()
},{deep:true,immediate:true})



</script>

<style lang="scss" scoped>

</style>