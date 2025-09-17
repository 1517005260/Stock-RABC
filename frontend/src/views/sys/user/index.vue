<template>
  <div class="app-container">
    <el-row :gutter="20" class="header">
      <el-col :span="7">
        <el-input placeholder="请输入用户名..." v-model="queryForm.query" clearable></el-input>
      </el-col>
      <el-button type="primary" :icon="Search" @click="initUserList">搜索</el-button>
      <el-button 
        type="success" 
        :icon="DocumentAdd" 
        @click="handleDialogValue()"
        v-permission="'system:user:add'"
      ></el-button>
      <el-popconfirm 
        title="您确定批量删除这些记录吗？" 
        @confirm="handleDelete(null)"
        v-permission="'system:user:remove'"
      >
        <template #reference>
          <el-button type="danger" :disabled="delBtnStatus" :icon="Delete">批量删除</el-button>
        </template>
      </el-popconfirm>
    </el-row>

    <el-table 
      v-loading="tableLoading"
      :data="tableData" 
      stripe 
      style="width: 100%" 
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55"/>
      <el-table-column prop="avatar" label="头像" width="80" align="center">
        <template v-slot="scope">
          <img
            :src="buildAvatarUrl(scope.row.avatar)"
            width="50"
            height="50"
            @error="handleImageError"
          />
        </template>
      </el-table-column>
      <el-table-column prop="username" label="用户名" width="100" align="center"/>
      <el-table-column prop="roles" label="拥有角色" width="200" align="center">
        <template v-slot="scope">
          <el-tag 
            size="small" 
            type="warning" 
            v-for="(item, index) in scope.row.roleList" 
            :key="index"
          > 
            {{ item.name }}
          </el-tag>
          <span v-if="!scope.row.roleList || scope.row.roleList.length === 0">无角色</span>
        </template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱" width="200" align="center"/>
      <el-table-column prop="phonenumber" label="手机号" width="120" align="center"/>
      <el-table-column prop="status" label="状态？" width="200" align="center">
        <template v-slot="{row}">
          <el-switch 
            v-model="row.status" 
            @change="statusChangeHandle(row)" 
            active-text="正常" 
            inactive-text="禁用"
            :active-value="0" 
            :inactive-value="1"
          >
          </el-switch>
        </template>
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" width="200" align="center"/>
      <el-table-column prop="login_date" label="最后登录时间" width="200" align="center"/>
      <el-table-column prop="remark" label="备注" min-width="100"/>
      <el-table-column prop="action" label="操作" width="400" fixed="right" align="center">
        <template v-slot="scope">
          <el-button-group>
            <el-button 
              type="primary" 
              size="small"
              :icon="Tools" 
              @click="handleRoleDialogValue(scope.row.id, scope.row.roleList || [])"
              v-permission="'system:user:edit'"
            >分配角色</el-button>
            <el-button 
              type="primary" 
              size="small" 
              @click="handlePwd(scope.row.id)"
              v-permission="'system:user:reset'"
            >重置密码</el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="handleSelectionRemove([scope.row.id])"
              v-permission="'system:user:remove'"
            >删除</el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
        v-model:current-page="queryForm.pageNum"
        v-model:page-size="queryForm.pageSize"
        :page-sizes="[10, 20, 30, 40]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
    />
    <Dialog 
      v-model="dialogVisible" 
      :dialogVisible="dialogVisible" 
      :id="id" 
      :dialogTitle="dialogTitle"
      @initUserList="initUserList"
    ></Dialog>
    <RoleDialog 
      v-model="roleDialogVisible" 
      :sysRoleList="sysRoleList" 
      :roleDialogVisible="roleDialogVisible" 
      :id="id"
      @initUserList="initUserList"
    ></RoleDialog>
  </div>
</template>

<script setup>
import {Search, Delete, DocumentAdd, Edit, Tools, RefreshRight} from '@element-plus/icons-vue'
import requestUtil, {getServerUrl} from '@/util/request'
import Dialog from './components/dialog'
import RoleDialog from "./components/roleDialog.vue";
import {ref, onMounted} from "vue";
import {ElMessage} from "element-plus";

const tableData = ref([])
const tableLoading = ref(false)
const total = ref(0)

const queryForm = ref({
  query: '',
  pageNum: 1,
  pageSize: 10
})

const dialogVisible = ref(false)
const dialogTitle = ref("")
const id = ref(-1)
const sysRoleList = ref([])
const roleDialogVisible = ref(false)
const delBtnStatus = ref(true)
const multipleSelection = ref([])

const handleSelectionChange = (selection) => {
  multipleSelection.value = selection || [];
  delBtnStatus.value = selection.length === 0;
}

const handleDialogValue = (userId) => {
  if (userId) {
    id.value = userId;
    dialogTitle.value = "用户修改"
  } else {
    id.value = -1;
    dialogTitle.value = "用户添加"
  }
  dialogVisible.value = true
}

const initUserList = async () => {
  try {
    tableLoading.value = true
    const res = await requestUtil.post("user/search", queryForm.value)

    if (res.data && res.data.code === 200 && res.data.data) {
      tableData.value = res.data.data.userList || []
      total.value = res.data.data.total || 0
    } else if (res.data && res.data.userList) {
      tableData.value = res.data.userList || []
      total.value = res.data.total || 0
    } else {
      tableData.value = []
      total.value = 0
      ElMessage.warning("获取用户数据失败")
    }
  } catch (error) {
    console.error("加载用户列表失败:", error)
    ElMessage.error("加载用户列表失败，请重试")
    tableData.value = []
    total.value = 0
  } finally {
    tableLoading.value = false
  }
}

const handleCurrentChange = (pageNum) => {
  queryForm.value.pageNum = pageNum
  initUserList()
}

const handleSizeChange = (pageSize) => {
  queryForm.value.pageSize = pageSize
  queryForm.value.pageNum = 1
  initUserList()
}

const handleDelete = async (id) => {
  try {
    var ids = []
    if (id) {
      ids.push(id)
    } else {
      if (multipleSelection.value.length === 0) {
        ElMessage.warning("请选择要删除的记录")
        return
      }
      
      multipleSelection.value.forEach(row => {
        ids.push(row.id)
      })
    }
    
    const res = await requestUtil.del("user/action", ids)
    if (res.data && res.data.code === 200) {
      ElMessage.success('删除成功!')
      // 重新加载列表
      initUserList()
    } else {
      ElMessage.error(res.data?.msg || '删除失败')
    }
  } catch (error) {
    console.error("删除用户失败:", error)
    ElMessage.error("删除失败，请重试")
  }
}

const handleResetPassword = async (id) => {
  try {
    if (!id) {
      ElMessage.warning("用户ID无效")
      return
    }
    
    const res = await requestUtil.get("user/resetPassword?id=" + id)
    if (res.data && res.data.code === 200) {
      ElMessage.success('密码重置成功!')
      initUserList()
    } else {
      ElMessage.error(res.data?.msg || '密码重置失败')
    }
  } catch (error) {
    console.error("重置密码失败:", error)
    ElMessage.error("重置密码失败，请重试")
  }
}

const statusChangeHandle = async (row) => {
  try {
    if (!row || !row.id) {
      ElMessage.warning("用户数据无效")
      return
    }
    
    let res = await requestUtil.post("user/status", {id: row.id, status: row.status})
    if (res.data && res.data.code === 200) {
      ElMessage.success('状态修改成功!')
    } else {
      ElMessage.error(res.data?.msg || '状态修改失败')
      // 修改失败，恢复原状态
      initUserList()
    }
  } catch (error) {
    console.error("修改用户状态失败:", error)
    ElMessage.error("修改状态失败，请重试")
    // 出错，恢复原状态
    initUserList()
  }
}

const handleRoleDialogValue = (userId, roleList) => {
  if (!userId) {
    ElMessage.warning("用户ID无效")
    return
  }
  
  id.value = userId
  sysRoleList.value = Array.isArray(roleList) ? roleList : []
  roleDialogVisible.value = true
}

const handlePwd = (id) => {
  if (!id) {
    ElMessage.warning("用户ID无效")
    return
  }
  
  handleResetPassword(id)
}

const handleSelectionRemove = (ids) => {
  if (ids.length === 0) {
    ElMessage.warning("请选择要删除的记录")
    return
  }
  
  handleDelete(ids[0])
}

const buildAvatarUrl = (avatar) => {
  const baseUrl = getServerUrl().replace(/\/$/, '')
  const avatarName = avatar || 'default.jpg'
  return `${baseUrl}/media/userAvatar/${avatarName}`
}

const handleImageError = (event) => {
  event.target.src = buildAvatarUrl('default.jpg')
}

onMounted(() => {
  initUserList()
})
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