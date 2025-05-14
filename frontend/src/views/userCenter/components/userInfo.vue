<template>
  <el-form ref="userRef" :model="form" :rules="rules" label-width="100px">
    <el-form-item label="手机号码：" prop="phonenumber">
      <el-input v-model="form.phonenumber" maxlength="11"/>
    </el-form-item>
    <el-form-item label="用户邮箱：" prop="email">
      <el-input v-model="form.email" maxlength="50"/>
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="handleSubmit">保存</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import {defineProps, ref} from 'vue';
import requestUtil from "@/util/request";
import {ElMessage} from "element-plus";

const props = defineProps(
    {
      user:{
        type: Object,
        default:()=>{
        },
        required:true
      }
    }
)

const form = ref({
  id: -1,
  phonenumber: '',
  email: ''
})

const userRef = ref(null)

form.value = props.user;

const rules = ref({
  email: [{required: true, message: "邮箱地址不能为空", trigger: "blur"}, {
    type: "email",
    message: "请输入正确的邮箱地址",
    trigger: ["blur", "change"]
  }],
  phonenumber: [{required: true, message: "手机号码不能为空", trigger: "blur"}, {
    pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/,
    message: "请输入正确的手机号码",
    trigger: "blur"
  }],
});

const handleSubmit = () => {
  userRef.value.validate(async (valid) => {
    if (valid) {
      let result = await requestUtil.post("user/save", form.value);
      let data = result.data;
      if (data.code == 200) {
        ElMessage.success("执行成功！")
        window.sessionStorage.setItem("currentUser", JSON.stringify(form.value))
      }
    }
  })
}
</script>

<style scoped lang="scss">

</style>