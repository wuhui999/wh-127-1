<template>
  <div class="settlement-detail" v-loading="loading">
    <el-page-header @back="$router.push('/settlements')" content="结算详情" />

    <div style="margin-top: 20px;" v-if="settlement">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>结算信息</span>
            <div>
              <el-button v-if="settlement.status === 'pending'" type="success" size="small" @click="handleConfirm">确认结算</el-button>
              <el-button v-if="settlement.status === 'confirmed'" type="warning" size="small" @click="handlePay">确认支付</el-button>
            </div>
          </div>
        </template>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="合同编号">{{ settlement.contract_no }}</el-descriptions-item>
          <el-descriptions-item label="果园">{{ settlement.orchard_name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusColor(settlement.status)">{{ statusLabel(settlement.status) }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card shadow="hover" style="margin-top: 16px;">
        <template #header><span>费用明细</span></template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="蜂箱日数">{{ settlement.total_hive_days }}</el-descriptions-item>
          <el-descriptions-item label="单价">{{ settlement.unit_price }} 元/箱/天</el-descriptions-item>
          <el-descriptions-item label="基础金额">{{ settlement.base_amount }} 元</el-descriptions-item>
          <el-descriptions-item label="异常扣费">
            <span :style="{ color: settlement.anomaly_deduction > 0 ? '#f56c6c' : '' }">{{ settlement.anomaly_deduction }} 元</span>
          </el-descriptions-item>
          <el-descriptions-item label="违约扣费">
            <span :style="{ color: settlement.penalty_deduction > 0 ? '#f56c6c' : '' }">{{ settlement.penalty_deduction }} 元</span>
          </el-descriptions-item>
          <el-descriptions-item label="应付金额">
            <span style="font-size: 20px; font-weight: 700; color: #f56c6c;">{{ settlement.total_amount }} 元</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { settlementApi } from '../api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const settlement = ref(null)

function statusColor(status) {
  const map = { pending: 'warning', confirmed: '', paid: 'success' }
  return map[status] || 'info'
}

function statusLabel(status) {
  const map = { pending: '待确认', confirmed: '已确认', paid: '已支付' }
  return map[status] || status
}

async function loadSettlement() {
  loading.value = true
  try {
    const { data } = await settlementApi.get(route.params.id)
    settlement.value = data
  } catch (err) {
    ElMessage.error('加载结算详情失败')
    router.push('/settlements')
  } finally {
    loading.value = false
  }
}

async function handleConfirm() {
  try {
    await ElMessageBox.confirm('确认该结算？', '提示', { type: 'info' })
    await settlementApi.confirm(settlement.value.id)
    ElMessage.success('确认成功')
    loadSettlement()
  } catch { /* cancelled */ }
}

async function handlePay() {
  try {
    await ElMessageBox.confirm('确认支付该结算？', '提示', { type: 'warning' })
    await settlementApi.pay(settlement.value.id)
    ElMessage.success('支付成功')
    loadSettlement()
  } catch { /* cancelled */ }
}

onMounted(loadSettlement)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
