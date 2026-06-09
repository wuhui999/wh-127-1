<template>
  <div class="settlements-page">
    <el-card shadow="hover">
      <div class="page-header">
        <h3>结算管理</h3>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 创建结算
        </el-button>
      </div>

      <div class="filter-bar">
        <el-select v-model="filters.contract_id" placeholder="合同筛选" clearable filterable style="width: 200px" @change="loadSettlements">
          <el-option v-for="c in contractOptions" :key="c.id" :label="c.contract_no" :value="c.id" />
        </el-select>
        <el-select v-model="filters.status" placeholder="状态筛选" clearable style="width: 130px" @change="loadSettlements">
          <el-option label="待确认" value="pending" />
          <el-option label="已确认" value="confirmed" />
          <el-option label="已支付" value="paid" />
        </el-select>
        <el-button type="primary" @click="loadSettlements">搜索</el-button>
      </div>

      <el-table :data="settlements" stripe v-loading="loading">
        <el-table-column prop="contract_no" label="合同编号" width="140" />
        <el-table-column prop="orchard_name" label="果园" width="120" />
        <el-table-column prop="total_hive_days" label="蜂箱日数" width="100" align="center" />
        <el-table-column prop="base_amount" label="基础金额(元)" width="120" align="center" />
        <el-table-column prop="anomaly_deduction" label="异常扣费(元)" width="120" align="center" />
        <el-table-column prop="penalty_deduction" label="违约扣费(元)" width="120" align="center" />
        <el-table-column prop="total_amount" label="应付金额(元)" width="120" align="center">
          <template #default="{ row }">
            <span style="font-weight: 700; color: #f56c6c;">{{ row.total_amount }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="settlementStatusColor(row.status)" size="small">{{ settlementStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="$router.push(`/settlements/${row.id}`)">详情</el-button>
            <el-button v-if="row.status === 'pending'" text type="success" size="small" @click="handleConfirm(row)">确认</el-button>
            <el-button v-if="row.status === 'confirmed'" text type="warning" size="small" @click="handlePay(row)">支付</el-button>
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
          @size-change="loadSettlements"
          @current-change="loadSettlements"
        />
      </div>
    </el-card>

    <el-dialog v-model="createVisible" title="创建结算" width="600px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="选择合同">
          <el-select v-model="selectedContractId" placeholder="选择合同" filterable style="width: 100%" @change="loadCalculation">
            <el-option v-for="c in contractOptions" :key="c.id" :label="`${c.contract_no} - ${c.orchard_name || ''}`" :value="c.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <div v-if="calculation" class="calculation-preview">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="蜂箱日数">{{ calculation.total_hive_days }}</el-descriptions-item>
          <el-descriptions-item label="单价">{{ calculation.unit_price }} 元/箱/天</el-descriptions-item>
          <el-descriptions-item label="基础金额">{{ calculation.base_amount }} 元</el-descriptions-item>
          <el-descriptions-item label="异常扣费">{{ calculation.anomaly_deduction }} 元</el-descriptions-item>
          <el-descriptions-item label="违约扣费">{{ calculation.penalty_deduction }} 元</el-descriptions-item>
          <el-descriptions-item label="应付金额">
            <span style="font-weight: 700; color: #f56c6c;">{{ calculation.total_amount }} 元</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" :disabled="!calculation" @click="handleCreate">确认创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { settlementApi, contractApi } from '../api'

const loading = ref(false)
const settlements = ref([])
const createVisible = ref(false)
const createLoading = ref(false)
const selectedContractId = ref(null)
const calculation = ref(null)
const contractOptions = ref([])

const filters = reactive({ contract_id: '', status: '' })
const pagination = reactive({ page: 1, size: 10, total: 0 })

function settlementStatusColor(status) {
  const map = { pending: 'warning', confirmed: '', paid: 'success' }
  return map[status] || 'info'
}

function settlementStatusLabel(status) {
  const map = { pending: '待确认', confirmed: '已确认', paid: '已支付' }
  return map[status] || status
}

async function loadSettlements() {
  loading.value = true
  try {
    const { data } = await settlementApi.list({
      page: pagination.page,
      size: pagination.size,
      contract_id: filters.contract_id,
      status: filters.status
    })
    settlements.value = data.items || data || []
    pagination.total = data.total || settlements.value.length
  } catch {
    settlements.value = []
  } finally {
    loading.value = false
  }
}

async function loadContractOptions() {
  try {
    const { data } = await contractApi.list({ size: 500 })
    contractOptions.value = data.items || data || []
  } catch { /* ignore */ }
}

async function loadCalculation() {
  if (!selectedContractId.value) {
    calculation.value = null
    return
  }
  try {
    const { data } = await settlementApi.calculate(selectedContractId.value)
    calculation.value = data
  } catch (err) {
    ElMessage.error('无法计算结算金额')
    calculation.value = null
  }
}

function openCreateDialog() {
  selectedContractId.value = null
  calculation.value = null
  createVisible.value = true
}

async function handleCreate() {
  if (!selectedContractId.value) {
    ElMessage.warning('请选择合同')
    return
  }
  createLoading.value = true
  try {
    await settlementApi.create({ contract_id: selectedContractId.value })
    ElMessage.success('结算创建成功')
    createVisible.value = false
    loadSettlements()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '创建失败')
  } finally {
    createLoading.value = false
  }
}

async function handleConfirm(row) {
  try {
    await ElMessageBox.confirm('确认该结算？', '提示', { type: 'info' })
    await settlementApi.confirm(row.id)
    ElMessage.success('确认成功')
    loadSettlements()
  } catch { /* cancelled */ }
}

async function handlePay(row) {
  try {
    await ElMessageBox.confirm('确认支付该结算？', '提示', { type: 'warning' })
    await settlementApi.pay(row.id)
    ElMessage.success('支付成功')
    loadSettlements()
  } catch { /* cancelled */ }
}

onMounted(() => {
  loadSettlements()
  loadContractOptions()
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
.calculation-preview {
  margin-top: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}
</style>
