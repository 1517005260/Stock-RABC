<template>
  <el-form
      ref="formRef"
      :model="form"
      label-width="100px"
      style="text-align: center;padding-bottom:10px"
  >
    <el-upload
        name="avatar"
        :headers="headers"
        class="avatar-uploader"
        :action="uploadUrl"
        :show-file-list="false"
        :on-success="handleAvatarSuccess"
        :on-error="handleAvatarError"
        :before-upload="beforeAvatarUpload"
    >
      <img v-if="imageUrl" :src="imageUrl" class="avatar"/>
      <el-icon v-else class="avatar-uploader-icon">
        <Plus/>
      </el-icon>
    </el-upload>

    <el-button @click="handleConfirm" :disabled="!form.avatar" type="primary">确认更换</el-button>

  </el-form>
</template>

<script setup>
import {defineProps, ref, computed, onMounted} from "vue";
import requestUtil, {getServerUrl} from "@/util/request";
import {ElMessage} from 'element-plus'
import {Plus} from '@element-plus/icons-vue'

const props = defineProps({
  user: {
    type: Object,
    default: () => ({}),
    required: true
  }
})

const headers = ref({
  Authorization: window.sessionStorage.getItem('token') || ''
})

const form = ref({
  id: -1,
  avatar: ''
})

const uploadUrl = computed(() => getServerUrl() + 'user/uploadImage')
const formRef = ref(null)
const imageUrl = ref("")

// 初始化表单数据
const initForm = () => {
  if (props.user && props.user.id) {
    form.value.id = props.user.id
    form.value.avatar = props.user.avatar || ''
    
    if (form.value.avatar) {
      imageUrl.value = getServerUrl() + 'media/userAvatar/' + form.value.avatar
    } else {
      imageUrl.value = getServerUrl() + 'media/userAvatar/default.jpg'
    }
  }
}

onMounted(() => {
  initForm()
})

const handleAvatarSuccess = (res) => {
  try {
    if (res && res.title) {
      imageUrl.value = getServerUrl() + 'media/userAvatar/' + res.title
      form.value.avatar = res.title
      ElMessage.success('头像上传成功，点击确认以保存')
    } else {
      ElMessage.error('头像上传失败，服务器返回无效数据')
    }
  } catch (error) {
    console.error('处理头像上传响应失败:', error)
    ElMessage.error('处理上传响应时出错')
  }
}

const handleAvatarError = (err) => {
  console.error('头像上传失败:', err)
  ElMessage.error('头像上传失败，请重试')
}

const beforeAvatarUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('上传头像必须是图片格式')
  }
  if (!isLt2M) {
    ElMessage.error('上传头像大小不能超过2MB!')
  }
  return isImage && isLt2M
}

const handleConfirm = async () => {
  if (!form.value.avatar) {
    ElMessage.warning('请先上传新头像')
    return
  }
  
  try {
    let result = await requestUtil.post("user/updateAvatar", form.value)
    let data = result.data
    if (data.code == 200) {
      ElMessage.success("头像更新成功！")
      
      // 更新sessionStorage中的用户信息
      try {
        const currentUser = JSON.parse(sessionStorage.getItem('currentUser') || '{}')
        currentUser.avatar = form.value.avatar
        sessionStorage.setItem('currentUser', JSON.stringify(currentUser))
      } catch (e) {
        console.error('更新存储的用户信息失败:', e)
      }
    } else {
      ElMessage.error(data.msg || data.errorInfo || "更新头像失败")
    }
  } catch (error) {
    console.error('更新头像请求失败:', error)
    ElMessage.error("更新头像失败，请重试")
  }
}
</script>

<style>
.avatar-uploader .el-upload {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.avatar-uploader .el-upload:hover {
  border-color: #409eff;
}

.el-icon.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 178px;
  height: 178px;
  text-align: center;
}

.avatar {
  width: 120px;
  height: 120px;
  display: block;
}
</style>