<template>
  <el-dialog
      v-model="dialogVisibleValue"
      :title="dialogTitle"
      width="30%"
      @close="handleClose"
  >
    <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
    >
      <el-form-item label="上级菜单" prop="parent_id">
        <el-select v-model="form.parent_id" placeholder="请选择上级菜单">
          <template v-for="(item, index) in tableDataList" :key="index">
            <el-option :label="item.name" :value="item.id"></el-option>
            <template v-if="item.children && item.children.length">
              <template v-for="(child, childIndex) in item.children" :key="`${index}-${childIndex}`">
                <el-option :label="'    -- ' + child.name" :value="child.id"></el-option>
              </template>
            </template>
          </template>
        </el-select>
      </el-form-item>
      <el-form-item label="菜单类型" prop="menu_type" label-width="100px">
        <el-radio-group v-model="form.menu_type">
          <el-radio :label="'M'">目录</el-radio>
          <el-radio :label="'C'">菜单</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="菜单图标" prop="icon">
        <el-input v-model="form.icon" />
      </el-form-item>

      <el-form-item label="菜单名称" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>

      <el-form-item label="权限标识" prop="perms">
        <el-input v-model="form.perms" />
      </el-form-item>

      <el-form-item label="路由路径" prop="path">
        <el-input v-model="form.path" />
      </el-form-item>

      <el-form-item label="组件路径" prop="component">
        <el-input v-model="form.component" />
      </el-form-item>

      <el-form-item label="显示顺序" prop="order_num" >
        <el-input-number v-model="form.order_num" :min="1" label="显示顺序"></el-input-number>
      </el-form-item>

      <el-form-item label="备注" prop="remark">
        <el-input v-model="form.remark" />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button type="primary" @click="handleConfirm" :loading="loading">确认</el-button>
        <el-button @click="handleClose">取消</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import {defineEmits, defineProps, ref, watch, computed} from "vue";
import requestUtil from "@/util/request";
import { ElMessage } from 'element-plus'

const props = defineProps({
  id: {
    type: Number,
    default: -1,
    required: true
  },
  dialogTitle: {
    type: String,
    default: '',
    required: true
  },
  dialogVisible: {
    type: Boolean,
    default: false,
    required: true
  },
  tableData: {
    type: Array,
    default: () => [],
    required: true
  }
})

// 计算属性，解决弹框无法关闭问题
const dialogVisibleValue = computed({
  get: () => props.dialogVisible,
  set: (val) => emits('update:modelValue', val)
})

// 本地处理的表格数据
const tableDataList = ref([])

const loading = ref(false)
const form = ref({
  id: -1,
  parent_id: '',
  menu_type: "M",
  icon: '',
  name: '',
  perms: '',
  path: '',
  component: '',
  order_num: 1,
  remark: ''
})

const rules = ref({
  name: [{ required: true, message: "菜单名称不能为空", trigger: "blur" }]
})

const formRef = ref(null)

const initFormData = async (id) => {
  try {
    loading.value = true
    const res = await requestUtil.get("menu/action?id=" + id);
    if (res.data && res.data.menu) {
      form.value = res.data.menu;
    } else {
      ElMessage.warning("获取菜单数据失败")
      resetForm()
    }
  } catch (error) {
    console.error("加载菜单数据失败:", error)
    ElMessage.error("获取菜单信息失败")
    resetForm()
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = {
    id: -1,
    parent_id: '',
    menu_type: "M",
    icon: '',
    name: '',
    perms: '',
    path: '',
    component: '',
    order_num: 1,
    remark: ''
  }
}

watch(() => props.dialogVisible, (newVal) => {
  if (newVal) {
    tableDataList.value = props.tableData || []
    let id = props.id
    if (id !== -1) {
      initFormData(id)
    } else {
      resetForm()
    }
  }
})

const emits = defineEmits(['update:modelValue', 'initMenuList'])

const handleClose = () => {
  emits('update:modelValue', false)
}

const handleConfirm = () => {
  if (!formRef.value) return
  
  formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        loading.value = true
        let result = await requestUtil.post("menu/save", form.value);
        let data = result.data;
        if (data && data.code === 200) {
          ElMessage.success("保存成功！")
          formRef.value.resetFields();
          emits("initMenuList")
          handleClose();
        } else {
          ElMessage.error(data?.msg || "保存失败");
        }
      } catch (error) {
        console.error("保存菜单失败:", error)
        ElMessage.error("保存失败，请重试")
      } finally {
        loading.value = false
      }
    } else {
      ElMessage.warning("请填写必要的表单项")
    }
  })
}
</script>

<style scoped>
</style>