<template>
  <div class="contracts-page">
    <el-card shadow="hover">
      <div class="page-header">
        <h3>合同管理</h3>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 新建合同
        </el-button>
      </div>

      <div class="filter-bar">
        <el-select v-model="filters.status" placeholder="状态筛选" clearable style="width: 140px" @change="loadContracts">
          <el-option label="草稿" value="draft" />
          <el-option label="生效" value="effective" />
          <el-option label="进行中" value="ongoing" />
          <el-option label="结束" value="completed" />
          <el-option label="争议" value="disputed" />
        </el-select>
        <el-input v-model="filters.keyword" placeholder="搜索合同编号/果园/蜂农" clearable style="width: 240px" @clear="loadContracts" @keyup.enter="loadContracts">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="loadContracts">搜索</el-button>
      </div>

      <el-table :data="contracts" stripe v-loading="loading">
        <el-table-column prop="contract_no" label="合同编号" width="140" />
        <el-table-column prop="orchard_name" label="果园" width="120" />
        <el-table-column prop="beekeeper_name" label="蜂农" width="100" />
        <el-table-column prop="hive_count" label="蜂箱数量" width="100" align="center" />
        <el-table-column label="投放期" width="200">
          <template #default="{ row }">{{ row.start_date }} ~ {{ row.end_date }}</template>
        </el-table-column>
        <el-table-column prop="unit_price" label="单价(元/箱/天)" width="130" align="center" />
        <el-table-column prop="total_amount" label="总额(元)" width="110" align="center" />
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="statusColor(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="$router.push(`/contracts/${row.id}`)">查看详情</el-button>
            <el-button text type="primary" size="small" v-if="row.status === 'draft'" @click="openEditDialog(row)">编辑</el-button>
            <el-button text type="warning" size="small" @click="openStatusDialog(row)">状态变更</el-button>
            <el-button text type="danger" size="small" v-if="row.status === 'draft'" @click="handleDelete(row)">删除</el-button>
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
          @size-change="loadContracts"
          @current-change="loadContracts"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑合同' : '新建合同'" width="600px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="果园" prop="orchard_id">
          <el-select v-model="form.orchard_id" placeholder="选择果园" filterable style="width: 100%">
            <el-option v-for="o in orchardList" :key="o.id" :label="o.name" :value="o.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="蜂农" prop="beekeeper_id">
          <el-select v-model="form.beekeeper_id" placeholder="选择蜂农" filterable style="width: 100%">
            <el-option v-for="f in farmerList" :key="f.id" :label="f.real_name" :value="f.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="蜂箱数量" prop="hive_count">
          <el-input-number v-model="form.hive_count" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" placeholder="选择开始日期" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束日期" prop="end_date">
          <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" placeholder="选择结束日期" style="width: 100%" />
        </el-form-item>
        <el-form-item label="单价(元)" prop="unit_price">
          <el-input-number v-model="form.unit_price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="违约条款">
          <el-input v-model="form.penalty_clause" type="textarea" :rows="3" placeholder="请输入违约条款" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="statusDialogVisible" title="状态变更" width="400px">
      <el-form label-width="80px">
        <el-form-item label="当前状态">
          <el-tag :type="statusColor(currentContract?.status)">{{ statusLabel(currentContract?.status) }}</el-tag>
        </el-form-item>
        <el-form-item label="新状态">
          <el-select v-model="newStatus" placeholder="选择新状态" style="width: 100%">
            <el-option label="草稿" value="draft" />
            <el-option label="生效" value="effective" />
            <el-option label="进行中" value="ongoing" />
            <el-option label="结束" value="completed" />
            <el-option label="争议" value="disputed" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="statusLoading" @click="handleChangeStatus">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { contractApi, orchardApi, authApi } from '../api'

const loading = ref(false)
const contracts = ref([])
const dialogVisible = ref(false)
const statusDialogVisible = ref(false)
const submitLoading = ref(false)
const statusLoading = ref(false)
const editingId = ref(null)
const currentContract = ref(null)
const newStatus = ref('')
const formRef = ref(null)
const orchardList = ref([])
const farmerList = ref([])

const filters = reactive({ status: '', keyword: '' })
const pagination = reactive({ page: 1, size: 10, total: 0 })

const form = reactive({
  orchard_id: null,
  beekeeper_id: null,
  hive_count: 1,
  start_date: '',
  end_date: '',
  unit_price: 0,
  penalty_clause: '',
  notes: ''
})

const formRules = {
  orchard_id: [{ required: true, message: '请选择果园', trigger: 'change' }],
  beekeeper_id: [{ required: true, message: '请选择蜂农', trigger: 'change' }],
  hive_count: [{ required: true, message: '请输入蜂箱数量', trigger: 'blur' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
  unit_price: [{ required: true, message: '请输入单价', trigger: 'blur' }]
}

function statusColor(s) {
  const map = { draft: 'info', effective: 'warning', ongoing: 'success', completed: '', disputed: 'danger' }
  return map[s] || 'info'
}

function statusLabel(s) {
  const map = { draft: '草稿', effective: '生效', ongoing: '进行中', completed: '结束', disputed: '争议' }
  return map[s] || s
}

async function loadContracts() {
  loading.value = true
  try {
    const { data } = await contractApi.list({
      page: pagination.page,
      size: pagination.size,
      status: filters.status,
      keyword: filters.keyword
    })
    contracts.value = data.items || data || []
    pagination.total = data.total || contracts.value.length
  } catch {
    contracts.value = []
  } finally {
    loading.value = false
  }
}

async function loadOrchards() {
  try {
    const { data } = await orchardApi.list({ size: 1000 })
    orchardList.value = data.items || data || []
  } catch { /* ignore */ }
}

async function loadFarmers() {
  try {
    const { data } = await authApi.listUsers({ role: 'beekeeper' })
    farmerList.value = data || []
  } catch { /* ignore */ }
}

function resetForm() {
  form.orchard_id = null
  form.beekeeper_id = null
  form.hive_count = 1
  form.start_date = ''
  form.end_date = ''
  form.unit_price = 0
  form.penalty_clause = ''
  form.notes = ''
}

function openCreateDialog() {
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEditDialog(row) {
  editingId.value = row.id
  Object.assign(form, {
    orchard_id: row.orchard_id,
    beekeeper_id: row.beekeeper_id,
    hive_count: row.hive_count,
    start_date: row.start_date,
    end_date: row.end_date,
    unit_price: row.unit_price,
    penalty_clause: row.penalty_clause || '',
    notes: row.notes || ''
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitLoading.value = true
  try {
    if (editingId.value) {
      await contractApi.update(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await contractApi.create(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadContracts()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

function openStatusDialog(row) {
  currentContract.value = row
  newStatus.value = ''
  statusDialogVisible.value = true
}

async function handleChangeStatus() {
  if (!newStatus.value) {
    ElMessage.warning('请选择新状态')
    return
  }
  statusLoading.value = true
  try {
    await contractApi.changeStatus(currentContract.value.id, newStatus.value)
    ElMessage.success('状态变更成功')
    statusDialogVisible.value = false
    loadContracts()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '状态变更失败')
  } finally {
    statusLoading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除该合同？', '提示', { type: 'warning' })
    await contractApi.delete(row.id)
    ElMessage.success('删除成功')
    loadContracts()
  } catch { /* cancelled */ }
}

onMounted(() => {
  loadContracts()
  loadOrchards()
  loadFarmers()
})
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
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
