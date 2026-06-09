<template>
  <div class="anomalies-page">
    <el-card shadow="hover">
      <div class="page-header">
        <h3>异常管理</h3>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 上报异常
        </el-button>
      </div>

      <div class="filter-bar">
        <el-select v-model="filters.type" placeholder="类型筛选" clearable style="width: 130px" @change="loadAnomalies">
          <el-option label="逃蜂" value="逃蜂" />
          <el-option label="病虫害" value="病虫害" />
          <el-option label="天气影响" value="天气影响" />
          <el-option label="其他" value="其他" />
        </el-select>
        <el-select v-model="filters.status" placeholder="状态筛选" clearable style="width: 130px" @change="loadAnomalies">
          <el-option label="待处理" value="reported" />
          <el-option label="处理中" value="processing" />
          <el-option label="已处理" value="resolved" />
        </el-select>
        <el-select v-model="filters.severity" placeholder="严重程度" clearable style="width: 130px" @change="loadAnomalies">
          <el-option label="低" value="low" />
          <el-option label="中" value="medium" />
          <el-option label="高" value="high" />
        </el-select>
        <el-button type="primary" @click="loadAnomalies">搜索</el-button>
      </div>

      <el-table :data="anomalies" stripe v-loading="loading">
        <el-table-column prop="hive_no" label="蜂箱" width="100" />
        <el-table-column prop="contract_no" label="合同" width="120" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="typeColor(row.type)" size="small">{{ typeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="severityColor(row.severity)" size="small">{{ severityLabel(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusColor(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="报告时间" width="160" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status !== 'resolved'" text type="success" size="small" @click="openResolveDialog(row)">处理</el-button>
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
          @size-change="loadAnomalies"
          @current-change="loadAnomalies"
        />
      </div>
    </el-card>

    <el-dialog v-model="createVisible" title="上报异常" width="500px" destroy-on-close>
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="90px">
        <el-form-item label="蜂箱" prop="hive_id">
          <el-select v-model="createForm.hive_id" placeholder="选择蜂箱" filterable style="width: 100%">
            <el-option v-for="h in hiveOptions" :key="h.id" :label="h.hive_no" :value="h.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="合同" prop="contract_id">
          <el-select v-model="createForm.contract_id" placeholder="选择合同" filterable style="width: 100%">
            <el-option v-for="c in contractOptions" :key="c.id" :label="c.contract_no" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="createForm.type" placeholder="选择类型" style="width: 100%">
            <el-option label="逃蜂" value="逃蜂" />
            <el-option label="病虫害" value="病虫害" />
            <el-option label="天气影响" value="天气影响" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重程度" prop="severity">
          <el-select v-model="createForm.severity" placeholder="选择严重程度" style="width: 100%">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="createForm.description" type="textarea" :rows="4" placeholder="请描述异常情况" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resolveVisible" title="处理异常" width="500px">
      <el-form ref="resolveFormRef" :model="resolveForm" :rules="resolveRules" label-width="100px">
        <el-form-item label="处理结果" prop="resolution">
          <el-input v-model="resolveForm.resolution" type="textarea" :rows="4" placeholder="请描述处理结果" />
        </el-form-item>
        <el-form-item label="恢复蜂箱状态">
          <el-switch v-model="resolveForm.restore_hive" active-text="是" inactive-text="否" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resolveVisible = false">取消</el-button>
        <el-button type="primary" :loading="resolveLoading" @click="handleResolve">确认处理</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { anomalyApi, hiveApi, contractApi } from '../api'

const loading = ref(false)
const anomalies = ref([])
const createVisible = ref(false)
const resolveVisible = ref(false)
const createLoading = ref(false)
const resolveLoading = ref(false)
const currentAnomaly = ref(null)
const createFormRef = ref(null)
const resolveFormRef = ref(null)
const hiveOptions = ref([])
const contractOptions = ref([])

const filters = reactive({ type: '', status: '', severity: '' })
const pagination = reactive({ page: 1, size: 10, total: 0 })

const createForm = reactive({
  hive_id: null,
  contract_id: null,
  type: '',
  severity: '',
  description: ''
})

const resolveForm = reactive({
  resolution: '',
  restore_hive: false
})

const createRules = {
  hive_id: [{ required: true, message: '请选择蜂箱', trigger: 'change' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  severity: [{ required: true, message: '请选择严重程度', trigger: 'change' }],
  description: [{ required: true, message: '请描述异常', trigger: 'blur' }]
}

const resolveRules = {
  resolution: [{ required: true, message: '请填写处理结果', trigger: 'blur' }]
}

function typeColor(type) {
  const map = { '逃蜂': 'warning', '病虫害': 'danger', '天气影响': 'info', '其他': 'info', 'swarm_escape': 'warning', 'disease': 'danger', 'weather': 'info', 'other': 'info' }
  return map[type] || 'info'
}

function typeLabel(type) {
  const map = { 'swarm_escape': '逃蜂', 'disease': '病虫害', 'weather': '天气影响', 'other': '其他' }
  return map[type] || type
}

function statusLabel(status) {
  const map = { 'reported': '待处理', 'processing': '处理中', 'resolved': '已处理' }
  return map[status] || status
}

function statusColor(status) {
  const map = { 'reported': 'warning', 'processing': '', 'resolved': 'success' }
  return map[status] || 'info'
}

function severityColor(s) {
  const map = { low: 'info', medium: 'warning', high: 'danger' }
  return map[s] || 'info'
}

function severityLabel(s) {
  const map = { low: '低', medium: '中', high: '高' }
  return map[s] || s
}

async function loadAnomalies() {
  loading.value = true
  try {
    const { data } = await anomalyApi.list({
      page: pagination.page,
      size: pagination.size,
      type: filters.type,
      status: filters.status,
      severity: filters.severity
    })
    anomalies.value = data.items || data || []
    pagination.total = data.total || anomalies.value.length
  } catch {
    anomalies.value = []
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  try {
    const [hiveRes, contractRes] = await Promise.all([
      hiveApi.list({ size: 500 }),
      contractApi.list({ size: 500 })
    ])
    hiveOptions.value = hiveRes.data.items || hiveRes.data || []
    contractOptions.value = contractRes.data.items || contractRes.data || []
  } catch { /* ignore */ }
}

function openCreateDialog() {
  Object.assign(createForm, { hive_id: null, contract_id: null, type: '', severity: '', description: '' })
  createVisible.value = true
}

async function handleCreate() {
  const valid = await createFormRef.value.validate().catch(() => false)
  if (!valid) return
  createLoading.value = true
  try {
    await anomalyApi.create(createForm)
    ElMessage.success('异常上报成功')
    createVisible.value = false
    loadAnomalies()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '上报失败')
  } finally {
    createLoading.value = false
  }
}

function openResolveDialog(row) {
  currentAnomaly.value = row
  resolveForm.resolution = ''
  resolveForm.restore_hive = false
  resolveVisible.value = true
}

async function handleResolve() {
  const valid = await resolveFormRef.value.validate().catch(() => false)
  if (!valid) return
  resolveLoading.value = true
  try {
    await anomalyApi.resolve(currentAnomaly.value.id, resolveForm)
    ElMessage.success('处理成功')
    resolveVisible.value = false
    loadAnomalies()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '处理失败')
  } finally {
    resolveLoading.value = false
  }
}

onMounted(() => {
  loadAnomalies()
  loadOptions()
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
