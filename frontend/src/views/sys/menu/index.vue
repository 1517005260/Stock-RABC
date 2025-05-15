<template>
  <div class="app-container">
    <el-row class="header">
      <el-button type="success" :icon="DocumentAdd" @click="handleDialogValue()">新增</el-button>
    </el-row>
    <el-table
        v-loading="tableLoading"
        :data="tableData"
        style="width: 100%; margin-bottom: 20px"
        row-key="id"
        border
        stripe
        default-expand-all
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
    >
      <el-table-column prop="name" label="菜单名称" width="180"/>
      <el-table-column prop="icon" label="图标" width="70" align="center">
        <template v-slot="scope">
          <el-icon v-if="scope.row && scope.row.icon">
            <svg-icon :icon="scope.row.icon"/>
          </el-icon>
        </template>
      </el-table-column>
      <el-table-column prop="order_num" label="排序" width="70" align="center"/>
      <el-table-column prop="perms" label="权限标识" width="200"/>
      <el-table-column prop="path" label="组件路径" width="180"/>
      <el-table-column prop="menu_type" label="菜单类型" width="120" align="center">
        <template v-slot="scope">
          <el-tag size="small" v-if="scope.row.menu_type === 'M'" type="danger" effect="dark">目录</el-tag>
          <el-tag size="small" v-else-if="scope.row.menu_type === 'C'" type="success" effect="dark">菜单</el-tag>
          <el-tag size="small" v-else>未知</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" align="center"/>
      <el-table-column prop="action" label="操作" width="300" fixed="right" align="center">
        <template v-slot="scope">
          <el-button 
            type="primary" 
            :icon="Edit" 
            @click="handleDialogValue(scope.row.id)"
            v-if="scope.row && scope.row.id"
          />
          <el-popconfirm 
            title="您确定要删除这条记录吗？" 
            @confirm="handleDelete(scope.row.id)"
            v-if="scope.row && scope.row.id"
          >
            <template #reference>
              <el-button type="danger" :icon="Delete"/>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
  </div>
  <Dialog 
    v-model="dialogVisible" 
    :tableData="tableData" 
    :dialogVisible="dialogVisible" 
    :id="id"
    :dialogTitle="dialogTitle" 
    @initMenuList="initMenuList"
  ></Dialog>
</template>

<script setup>
import {Search, Delete, DocumentAdd, Edit, Tools, RefreshRight} from '@element-plus/icons-vue'
import {ref, onMounted} from 'vue'
import requestUtil, {getServerUrl} from "@/util/request";
import Dialog from './components/dialog'
import {ElMessage} from 'element-plus'

const tableData = ref([])
const tableLoading = ref(false)
const id = ref(-1)
const dialogVisible = ref(false)
const dialogTitle = ref('')

const initMenuList = async () => {
  try {
    tableLoading.value = true
    const res = await requestUtil.get("menu/treeList");
    if (res.data && res.data.treeList) {
      tableData.value = res.data.treeList || [];
    } else {
      tableData.value = []
      ElMessage.warning("获取菜单数据失败")
    }
  } catch (error) {
    console.error("加载菜单数据失败:", error)
    ElMessage.error("获取菜单列表失败，请重试")
    tableData.value = []
  } finally {
    tableLoading.value = false
  }
}

onMounted(() => {
  initMenuList();
})

const handleDialogValue = (menuId) => {
  if (menuId) {
    id.value = menuId;
    dialogTitle.value = "菜单修改"
  } else {
    id.value = -1;
    dialogTitle.value = "菜单添加"
  }
  dialogVisible.value = true
}

const handleDelete = async (id) => {
  try {
    if (!id) {
      ElMessage.warning("菜单ID无效")
      return
    }
    
    const res = await requestUtil.del("menu/action", id)
    if (res.data && res.data.code === 200) {
      ElMessage.success('删除成功!')
      initMenuList();
    } else {
      ElMessage.error(res.data?.msg || '删除失败')
    }
  } catch (error) {
    console.error("删除菜单失败:", error)
    ElMessage.error("删除失败，请重试")
  }
}
</script>

<style lang="scss" scoped>
.header {
  padding-bottom: 16px;
  box-sizing: border-box;
}

.el-pagination {
  float: right;
  padding: 20px;
  box-sizing: border-box;
}

::v-deep th.el-table__cell {
  word-break: break-word;
  background-color: #f8f8f9 !important;
  color: #515a6e;
  height: 40px;
  font-size: 13px;
}

.el-tag--small {
  margin-left: 5px;
}
</style>