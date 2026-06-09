<template>
  <div class="contract-detail" v-loading="loading">
    <el-page-header @back="$router.push('/contracts')" content="合同详情" />

    <div style="margin-top: 20px;" v-if="contract">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>合同基本信息</span>
            <div>
              <el-button v-if="nextStatusOptions.length" type="warning" size="small" @click="showStatusChange = true">状态变更</el-button>
            </div>
          </div>
        </template>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="合同编号">{{ contract.contract_no }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusColor(contract.status)">{{ statusLabel(contract.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="果园">{{ contract.orchard?.name }}</el-descriptions-item>
          <el-descriptions-item label="蜂农">{{ contract.beekeeper?.real_name }}</el-descriptions-item>
          <el-descriptions-item label="蜂箱数量">{{ contract.hive_count }}</el-descriptions-item>
          <el-descriptions-item label="单价(元/箱/天)">{{ contract.unit_price }}</el-descriptions-item>
          <el-descriptions-item label="投放期">{{ contract.start_date }} ~ {{ contract.end_date }}</el-descriptions-item>
          <el-descriptions-item label="总额(元)">{{ contract.total_amount }}</el-descriptions-item>
          <el-descriptions-item label="违约条款">{{ contract.penalty_clause || '无' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="3">{{ contract.notes || '无' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card shadow="hover" style="margin-top: 16px;">
        <template #header><span>合同生命周期</span></template>
        <el-steps :active="activeStep" finish-status="success" align-center>
          <el-step title="草稿" />
          <el-step title="生效" />
          <el-step title="进行中" />
          <el-step title="结束" />
        </el-steps>
        <div v-if="contract.status === 'disputed'" style="text-align: center; margin-top: 12px;">
          <el-tag type="danger" size="large">合同存在争议</el-tag>
        </div>
      </el-card>

      <el-row :gutter="16" style="margin-top: 16px;">
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header><span>关联蜂箱</span></template>
            <el-table :data="contract.hives || []" stripe size="small">
              <el-table-column prop="hive_no" label="蜂箱编号" />
              <el-table-column prop="status" label="状态">
                <template #default="{ row }">
                  <el-tag :type="hiveStatusColor(row.status)" size="small">{{ hiveStatusLabel(row.status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="gps_lat" label="GPS" width="160">
                <template #default="{ row }">{{ row.gps_lat }}, {{ row.gps_lng }}</template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!(contract.hives && contract.hives.length)" description="暂无蜂箱" :image-size="40" />
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header><span>巡检摘要</span></template>
            <el-table :data="contract.inspections || []" stripe size="small">
              <el-table-column prop="hive_no" label="蜂箱" width="100" />
              <el-table-column prop="inspector" label="巡检员" width="80" />
              <el-table-column prop="colony_strength" label="蜂群强度" width="80" align="center" />
              <el-table-column prop="inspected_at" label="巡检时间" />
            </el-table>
            <el-empty v-if="!(contract.inspections && contract.inspections.length)" description="暂无巡检记录" :image-size="40" />
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header><span>异常记录</span></template>
            <el-table :data="contract.anomalies || []" stripe size="small">
              <el-table-column prop="type" label="类型" width="80">
                <template #default="{ row }">
                  <el-tag :type="anomalyTypeColor(row.type)" size="small">{{ anomalyTypeLabel(row.type) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="severity" label="严重程度" width="80">
                <template #default="{ row }">
                  <el-tag :type="severityColor(row.severity)" size="small">{{ severityLabel(row.severity) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  {{ row.status === 'resolved' ? '已处理' : row.status === 'processing' ? '处理中' : '待处理' }}
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="时间" />
            </el-table>
            <el-empty v-if="!(contract.anomalies && contract.anomalies.length)" description="暂无异常" :image-size="40" />
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="hover" style="margin-top: 16px;" v-if="contract.settlements && contract.settlements.length">
        <template #header><span>结算信息</span></template>
        <el-descriptions :column="3" border v-for="s in contract.settlements" :key="s.id">
          <el-descriptions-item label="蜂箱日数">{{ s.total_hive_days }}</el-descriptions-item>
          <el-descriptions-item label="基础金额">{{ s.base_amount }} 元</el-descriptions-item>
          <el-descriptions-item label="异常扣费">{{ s.anomaly_deduction }} 元</el-descriptions-item>
          <el-descriptions-item label="违约扣费">{{ s.penalty_deduction }} 元</el-descriptions-item>
          <el-descriptions-item label="应付金额">
            <span style="font-weight: 700; color: #f56c6c;">{{ s.total_amount }} 元</span>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="settlementStatusColor(s.status)">{{ settlementStatusLabel(s.status) }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>

    <el-dialog v-model="showStatusChange" title="状态变更" width="400px">
      <el-form label-width="80px">
        <el-form-item label="当前状态">
          <el-tag :type="statusColor(contract?.status)">{{ statusLabel(contract?.status) }}</el-tag>
        </el-form-item>
        <el-form-item label="新状态">
          <el-select v-model="newStatus" placeholder="选择新状态" style="width: 100%">
            <el-option v-for="s in nextStatusOptions" :key="s" :label="statusLabel(s)" :value="s" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showStatusChange = false">取消</el-button>
        <el-button type="primary" :loading="changing" @click="handleChangeStatus">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { contractApi } from '../api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const contract = ref(null)
const showStatusChange = ref(false)
const newStatus = ref('')
const changing = ref(false)

const statusFlow = {
  draft: ['effective'],
  effective: ['ongoing'],
  ongoing: ['completed', 'disputed'],
  completed: [],
  disputed: []
}

const nextStatusOptions = computed(() => {
  if (!contract.value) return []
  return statusFlow[contract.value.status] || []
})

const activeStep = computed(() => {
  if (!contract.value) return 0
  const map = { draft: 0, effective: 1, ongoing: 2, completed: 3 }
  return map[contract.value.status] ?? 2
})

function statusColor(s) {
  const map = { draft: 'info', effective: 'warning', ongoing: 'success', completed: '', disputed: 'danger' }
  return map[s] || 'info'
}

function statusLabel(s) {
  const map = { draft: '草稿', effective: '生效', ongoing: '进行中', completed: '结束', disputed: '争议' }
  return map[s] || s
}

function hiveStatusColor(status) {
  const map = { deployed: 'success', inspecting: '', anomaly: 'danger', idle: 'info', withdrawn: 'warning' }
  return map[status] || 'info'
}

function hiveStatusLabel(status) {
  const map = { deployed: '在投', inspecting: '巡检中', anomaly: '异常', idle: '闲置', withdrawn: '已撤回' }
  return map[status] || status
}

function anomalyTypeColor(type) {
  const map = { '逃蜂': 'warning', '病虫害': 'danger', '天气影响': 'info', '其他': 'info', 'swarm_escape': 'warning', 'disease': 'danger', 'weather': 'info', 'other': 'info' }
  return map[type] || 'info'
}

function anomalyTypeLabel(type) {
  const map = { 'swarm_escape': '逃蜂', 'disease': '病虫害', 'weather': '天气影响', 'other': '其他' }
  return map[type] || type
}

function severityColor(severity) {
  const map = { low: 'info', medium: 'warning', high: 'danger' }
  return map[severity] || 'info'
}

function severityLabel(severity) {
  const map = { low: '低', medium: '中', high: '高' }
  return map[severity] || severity
}

function settlementStatusColor(status) {
  const map = { pending: 'warning', confirmed: '', paid: 'success' }
  return map[status] || 'info'
}

function settlementStatusLabel(status) {
  const map = { pending: '待确认', confirmed: '已确认', paid: '已支付' }
  return map[status] || status
}

async function loadContract() {
  loading.value = true
  try {
    const { data } = await contractApi.get(route.params.id)
    contract.value = data
  } catch (err) {
    ElMessage.error('加载合同详情失败')
    router.push('/contracts')
  } finally {
    loading.value = false
  }
}

async function handleChangeStatus() {
  if (!newStatus.value) {
    ElMessage.warning('请选择新状态')
    return
  }
  changing.value = true
  try {
    await contractApi.changeStatus(contract.value.id, newStatus.value)
    ElMessage.success('状态变更成功')
    showStatusChange.value = false
    loadContract()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '状态变更失败')
  } finally {
    changing.value = false
  }
}

onMounted(loadContract)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
