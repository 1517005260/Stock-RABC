<template>
  <div class="app-container">
    <el-row :gutter="20" class="header">
      <el-col :span="7">
        <el-input placeholder="请输入用户名..." v-model="queryForm.query" clearable></el-input>
      </el-col>
      <el-button type="primary" :icon="Search" @click="initUserList">搜索</el-button>
      <el-button type="success" :icon="DocumentAdd" @click="handleDialogValue()">新增</el-button>
      <el-popconfirm title="您确定批量删除这些记录吗？" @confirm="handleDelete(null)">
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
            :src="getServerUrl()+'media/userAvatar/'+(scope.row.avatar || 'default.jpg')" 
            width="50" 
            height="50"
            onerror="this.src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAACXBIWXMAAAsTAAALEwEAmpwYAAAFEmlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDAgNzkuMTYwNDUxLCAyMDE3LzA1LzA2LTAxOjA4OjIxICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOCAoTWFjaW50b3NoKSIgeG1wOkNyZWF0ZURhdGU9IjIwMTktMDctMDdUMTY6Mzk6MjMrMDg6MDAiIHhtcDpNb2RpZnlEYXRlPSIyMDE5LTA3LTA3VDE2OjQwOjI5KzA4OjAwIiB4bXA6TWV0YWRhdGFEYXRlPSIyMDE5LTA3LTA3VDE2OjQwOjI5KzA4OjAwIiBkYzpmb3JtYXQ9ImltYWdlL3BuZyIgcGhvdG9zaG9wOkNvbG9yTW9kZT0iMyIgcGhvdG9zaG9wOklDQ1Byb2ZpbGU9InNSR0IgSUVDNjE5NjYtMi4xIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOmM1OThjMGI1LTEwMjgtNGE5Ni04M2E5LTg5NmViODRmYTRmZSIgeG1wTU06RG9jdW1lbnRJRD0ieG1wLmRpZDpjNTk4YzBiNS0xMDI4LTRhOTYtODNhOS04OTZlYjg0ZmE0ZmUiIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDpjNTk4YzBiNS0xMDI4LTRhOTYtODNhOS04OTZlYjg0ZmE0ZmUiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmM1OThjMGI1LTEwMjgtNGE5Ni04M2E5LTg5NmViODRmYTRmZSIgc3RFdnQ6d2hlbj0iMjAxOS0wNy0wN1QxNjozOToyMyswODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTggKE1hY2ludG9zaCkiLz4gPC9yZGY6U2VxPiA8L3htcE1NOkhpc3Rvcnk+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5kPSJyIj8+4/OoWwAABhVJREFUaIHFmn1oVXUYxz/PuXebzrfe7Wo5X8q1RZYUlRWZLCQsKoIiCaL6I4z+sHcikv4of+gPsUiLoiCRCKmwgiijP4zQJJA0U8QXfL/OzTnnbvfebc8953f7Y/eeae7e3bvrvR98Yefe85zn+X2f83uec54jqKMuH0IpB+i3GWe0IWSeQGYJkclCTEKI8UAjQBfQhqIdoR0hTqCMw+jag0TjpZoSCPi5AXAEmmQeYJUSskwJmY9QcxEYfhIiUTqE0HYjGA0G+8n4rxfdusCW21BUNaA9I2SOx+PxZWQkJzN+fBMNDRnk5GSRnp7GpEkT2L17P8lkksHBQbq6uuju7qGtrYO2tg4SiT6ktA4LYX5DIfAIpLNt4mM6cBUaHpRCm5+RkTG/pCSPgoKpFBffR1bWdW6NL18e4vjxFg4daubYsRY6OrpAcQ5FLWr4B0qqKhF4TjAIrA8H7YdCoVDB1Kk5zJlTSllZCTfeGLii8ebN9Rw92sLRoy20tp5CGKwm4/+5Af05QLXnOJfDhRGkNiMUCt2VlzeF8vIwJSWF+HxXb2YYBu+/X8PatR9y6VI/QpoDMnZ6OxD1DKQv4TpFRbfPuL+8vDC/oqKU/PybUtrp6Ohm8+Z6Nm3aRXf3BYTiBYrDV0RteCB9CdeZM2dqQWVlmIKCqWnb+vXXI9TUrKe19R8hpApojR8sH9I7gp1QKFRYXj5jeiiU66r/5ct9fPDB56xfX4dlifdkLP5m2h7ZPYJYXZ0FzC4vLywoKrrDlY3e3n4++uhLNmzYYf0tHMrYhccJz0kFpEwUTaZ2795Jc+fef5crm/X1B1m58m0GB4eK/fF4Y1p7noBksln4/VllZdNvKC29x7W9hoZDrF1bB4pfZOz8M67sXM6ULw5lCHFnSUl+9rxFJSil5ySV8tmzF6ipeQtDqAoZa3vTld1UQEHKlOLiOzPnzi1JqYhh9GCaF7Gs3wEMOwi1B6VGbFtHRxdr1rxLX9/ADBlvW+PKdqpqFQgGAwtz9+wpT2ljaOiMHUB5tOVYK2O/CqA1ckVHx8XNm+stra9l3J2HU/VJNYfSs7Kybq2sDKeUbhpnMc1eW5jRpVnYj5BF1NUVOW3bduCMEOIn1z5SCY+FEAuvhj5du/ZDhND+kHFq3NpMtfpdHAqFHnMr3DAM6up2YTn9ZijkPkXkpwChJyUULmQ3N//drygNKYLofnVFQCg1OxgMTsvPn+5a+IEDv5JMWI+SvW67OyLVkUa/31+alpD9N91cX7/bFv9g2gKuICQWCtU4q9nWdp5Tp9pQmtvEdZ+ROSJEyY03BugquZqGYfDDD/utlj9VYuZwEwivV/X1eydxcPAiDQeaUZhFMuY+IadUbEDMF0LMuBrhiYTB4cPHQcgpqUycngHl9/uLnZUcPnx8xIqqnOo42l5fX23PrlgGBgY5caINFONlvM/11uRIQEqFG8M8ffq8NdnrRRFc6yXPdQOhc6lhv5zHzvaB+jNXo9MJqK7eXqdgCYD+jx1B3YA87Q6kvb1jOAuuHgAC2tra7TA0pAGkpj0vZ3+svaOjy17+Lm6oi+GnGRQ9mmbSbuQGxFzb0ZFwfDd7LoYH0DMTE+OXlRJmBs5VyIwgZw8GSCQSl63rPgcfx1UpNQkzrrGUMrOUBc5Y3jFRVZ1RNhZzFnX91oiSieGAkCnlJ5zSUlISGYN5H9u37RN1S1KaZ51fMjL845ikPOj3+6/H52sc8enmZrXk5uY4v/3NfKf6x9E2T0esFY94XgKWtLR00tlpv9j9PKqoSqVF01o/fV7MIR0lkwYnTrShFNcJsf+qhIxsLWS8Rdd9DTt27E3Ztbh4mn1LFQqxYWRJQTbRdV+dYRgNO3fuSynklltynA1fAJvGrMNoc0YI4+X6+j07t279KWWf22/PJTMzCFBjFcY+Zj1GllNSml/09Q08t3v3oa+am3+nry85omtWVgbTp48LwFsIXrETWaKuH8hOq65OA16VUk5LJJI3X7gwkJNImJnJpMrWNG5CG9xHMnlRmGYcRQ9K5dUHAv4uYBxw1vr9RgqlPsBKwCk1JUT7LULdQqgsGcQdUtpnUAb6qP/mxlCOlOa3fv/AVpjwHzNQxiDLa5sEAAAAAElFTkSuQmCC'"
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
            :active-value="1" 
            :inactive-value="0"
          >
          </el-switch>
        </template>
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" width="200" align="center"/>
      <el-table-column prop="login_date" label="最后登录时间" width="200" align="center"/>
      <el-table-column prop="remark" label="备注" min-width="100"/>
      <el-table-column prop="action" label="操作" width="400" fixed="right" align="center">
        <template v-slot="scope">
          <el-button 
            type="primary" 
            :icon="Tools" 
            @click="handleRoleDialogValue(scope.row.id, scope.row.roleList || [])"
            >分配角色
          </el-button>
          <el-popconfirm 
            v-if="scope.row.username!=='long'" 
            title="您确定要对这个用户重置密码吗？"
            @confirm="handleResetPassword(scope.row.id)"
          >
            <template #reference>
              <el-button type="warning" :icon="RefreshRight">重置密码</el-button>
            </template>
          </el-popconfirm>
          <el-button 
            type="primary" 
            v-if="scope.row.username!=='long'" 
            :icon="Edit"
            @click="handleDialogValue(scope.row.id)"
          ></el-button>
          <el-popconfirm 
            v-if="scope.row.username!=='long'" 
            title="您确定要删除这条记录吗？"
            @confirm="handleDelete(scope.row.id)"
          >
            <template #reference>
              <el-button type="danger" :icon="Delete"/>
            </template>
          </el-popconfirm>
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
    if (res.data && res.data.userList) {
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