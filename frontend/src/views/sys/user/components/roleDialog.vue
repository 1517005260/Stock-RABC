<template>
  <el-dialog
      model-value="roleDialogVisible"
      title="分配角色"
      width="30%"
      @close="handleClose"
  >
    <el-form
        ref="formRef"
        :model="form"
        label-width="100px"
    >
      <el-checkbox-group v-model="form.checkedRoles">
        <el-checkbox v-for="role in form.roleList" :id="role.id" :key="role.id" :label="role.id" name="checkedRoles">
          {{ role.name }}
        </el-checkbox>
      </el-checkbox-group>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button type="primary" @click="handleConfirm">确认</el-button>
        <el-button @click="handleClose">取消</el-button>
      </span>
    </template>
  </el-dialog>
</template>
<script setup>
import {defineEmits, defineProps, ref, watch} from "vue";
import requestUtil, {getServerUrl} from "@/util/request";
import {ElMessage} from 'element-plus'
import {useStore} from 'vuex'
import {useRouter} from 'vue-router'

const store = useStore()
const router = useRouter()

const props = defineProps(
    {
      id: {
        type: Number,
        default: -1,
        required: true
      },
      roleDialogVisible: {
        type: Boolean,
        default: false,
        required: true
      },
      sysRoleList: {
        type: Array,
        default: [],
        required: true
      }
    }
)

const form = ref({
  id: -1,
  roleList: [],
  checkedRoles: []
})

const formRef = ref(null)

const initFormData = async (id) => {
  const res = await requestUtil.get("role/listAll");
  form.value.roleList = res.data.roleList;
  form.value.id = id;
}


watch(
    () => props.roleDialogVisible,
    () => {
      let id = props.id;
      console.log("id=" + id)
      if (id != -1) {
        form.value.checkedRoles = []
        props.sysRoleList.forEach(item => {
          form.value.checkedRoles.push(item.id);
        })
        initFormData(id)
      }
    }
)


const emits = defineEmits(['update:modelValue', 'initUserList'])

const handleClose = () => {
  emits('update:modelValue', false)
}


const handleConfirm = () => {
  formRef.value.validate(async (valid) => {
    if (valid) {
      // 获取当前用户ID
      const currentUser = store.getters.getCurrentUser
      const isCurrentUser = currentUser && currentUser.id === form.value.id
      
      try {
        let result = await requestUtil.post("user/grantRole", {"id": form.value.id, "roleIds": form.value.checkedRoles});
        let data = result.data;
        if (data.code == 200) {
          // 如果是当前用户的角色被修改，后端会返回新的token和权限
          if (data.token && data.permissions) {
            // 更新Vuex中的token和权限
            store.commit('SET_TOKEN', data.token)
            store.commit('SET_PERMISSIONS', data.permissions)
            
            // 如果角色从高权限变为低权限，提示用户权限已更改
            if (data.message) {
              ElMessage.success(data.message)
            } else {
              ElMessage.success("执行成功！")
            }
            
            // 角色变更后重置标签页并重定向到首页
            if (isCurrentUser) {
              store.commit('RESET_TABS')
              setTimeout(() => {
                router.push('/')
              }, 100)
            }
          } else {
            ElMessage.success("执行成功！")
          }

          emits("initUserList")
          handleClose();
        } else {
          ElMessage.error(data.msg || "操作失败");
        }
      } catch (error) {
        console.error("角色分配出错:", error)
        ElMessage.error("操作失败，请稍后重试")
      }
    } else {
      console.log("fail")
    }
  })
}


</script>

<style scoped>

</style>