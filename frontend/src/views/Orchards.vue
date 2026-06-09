<template>
  <div class="orchards-page">
    <el-card shadow="hover">
      <div class="page-header">
        <h3>果园管理</h3>
        <el-button type="primary" @click="openDialog()">
          <el-icon><Plus /></el-icon> 新建果园
        </el-button>
      </div>

      <el-table :data="orchards" stripe v-loading="loading">
        <el-table-column prop="name" label="名称" width="140" />
        <el-table-column prop="owner" label="所有者" width="120" />
        <el-table-column prop="location" label="位置" width="160" />
        <el-table-column prop="area" label="面积(亩)" width="100" align="center" />
        <el-table-column prop="crop_type" label="作物类型" width="120" />
        <el-table-column label="GPS" width="200">
          <template #default="{ row }">{{ row.gps_lat }}, {{ row.gps_lng }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="openDialog(row)">编辑</el-button>
            <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadOrchards"
          @current-change="loadOrchards"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑果园' : '新建果园'" width="550px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入果园名称" />
        </el-form-item>
        <el-form-item label="所有者" prop="owner">
          <el-input v-model="form.owner" placeholder="请输入所有者" />
        </el-form-item>
        <el-form-item label="位置" prop="location">
          <el-input v-model="form.location" placeholder="请输入位置" />
        </el-form-item>
        <el-form-item label="面积(亩)" prop="area">
          <el-input-number v-model="form.area" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="作物类型" prop="crop_type">
          <el-input v-model="form.crop_type" placeholder="请输入作物类型，如：苹果、樱桃" />
        </el-form-item>
        <el-form-item label="纬度" prop="gps_lat">
          <el-input-number v-model="form.gps_lat" :precision="6" :controls="false" style="width: 100%" placeholder="纬度" />
        </el-form-item>
        <el-form-item label="经度" prop="gps_lng">
          <el-input-number v-model="form.gps_lng" :precision="6" :controls="false" style="width: 100%" placeholder="经度" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { orchardApi } from '../api'

const loading = ref(false)
const orchards = ref([])
const dialogVisible = ref(false)
const submitLoading = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const pagination = reactive({ page: 1, size: 10, total: 0 })

const form = reactive({
  name: '',
  owner: '',
  location: '',
  area: 0,
  crop_type: '',
  gps_lat: null,
  gps_lng: null
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  owner: [{ required: true, message: '请输入所有者', trigger: 'blur' }],
  location: [{ required: true, message: '请输入位置', trigger: 'blur' }],
  crop_type: [{ required: true, message: '请输入作物类型', trigger: 'blur' }]
}

async function loadOrchards() {
  loading.value = true
  try {
    const { data } = await orchardApi.list({ page: pagination.page, size: pagination.size })
    orchards.value = data.items || data || []
    pagination.total = data.total || orchards.value.length
  } catch {
    orchards.value = []
  } finally {
    loading.value = false
  }
}

function resetForm() {
  Object.assign(form, { name: '', owner: '', location: '', area: 0, crop_type: '', gps_lat: null, gps_lng: null })
}

function openDialog(row) {
  if (row) {
    editingId.value = row.id
    Object.assign(form, {
      name: row.name,
      owner: row.owner,
      location: row.location,
      area: row.area,
      crop_type: row.crop_type,
      gps_lat: row.gps_lat,
      gps_lng: row.gps_lng
    })
  } else {
    editingId.value = null
    resetForm()
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitLoading.value = true
  try {
    if (editingId.value) {
      await orchardApi.update(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await orchardApi.create(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadOrchards()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除该果园？', '提示', { type: 'warning' })
    await orchardApi.delete(row.id)
    ElMessage.success('删除成功')
    loadOrchards()
  } catch { /* cancelled */ }
}

onMounted(loadOrchards)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h3 {
  margin: 0;
  color: #1a3a2a;
}
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
