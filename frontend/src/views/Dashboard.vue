<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <el-card shadow="hover" class="stat-card" :style="{ borderTop: `3px solid ${card.color}` }">
          <div class="stat-content">
            <div class="stat-info">
              <div class="stat-number" :style="{ color: card.color }">{{ card.value }}</div>
              <div class="stat-label">{{ card.label }}</div>
            </div>
            <el-icon :size="48" :style="{ color: card.color, opacity: 0.2 }"><component :is="card.icon" /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>最近异常</span>
              <el-button text type="primary" @click="$router.push('/anomalies')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentAnomalies" stripe size="small" v-if="recentAnomalies.length">
            <el-table-column prop="hive_no" label="蜂箱" width="100" />
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="anomalyTypeColor(row.type)" size="small">{{ anomalyTypeLabel(row.type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="severity" label="严重程度" width="100">
              <template #default="{ row }">
                <el-tag :type="severityColor(row.severity)" size="small">{{ severityLabel(row.severity) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'resolved' ? 'success' : 'warning'" size="small">{{ anomalyStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" />
          </el-table>
          <el-empty v-else description="暂无异常记录" :image-size="60" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>待巡检</span>
              <el-button text type="primary" @click="$router.push('/inspections')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="upcomingInspections" stripe size="small" v-if="upcomingInspections.length">
            <el-table-column prop="hive_no" label="蜂箱编号" width="120" />
            <el-table-column prop="location" label="位置" />
            <el-table-column prop="last_inspection_at" label="上次巡检" />
            <el-table-column prop="days_overdue" label="逾期天数" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.days_overdue > 0" type="danger" size="small">逾期{{ row.days_overdue }}天</el-tag>
                <el-tag v-else type="success" size="small">正常</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无待巡检" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { dashboardApi } from '../api'

const stats = ref({ total_contracts: 0, deployed_hives: 0, pending_inspections: 0, pending_anomalies: 0 })
const recentAnomalies = ref([])
const upcomingInspections = ref([])

const statCards = ref([
  { label: '合同总数', value: 0, icon: 'Document', color: '#409eff' },
  { label: '在投蜂箱', value: 0, icon: 'MapLocation', color: '#67c23a' },
  { label: '待巡检', value: 0, icon: 'View', color: '#e6a23c' },
  { label: '异常待处理', value: 0, icon: 'Warning', color: '#f56c6c' }
])

function anomalyTypeColor(type) {
  const map = { '逃蜂': 'warning', '病虫害': 'danger', '天气影响': 'info', '其他': 'info', 'swarm_escape': 'warning', 'disease': 'danger', 'weather': 'info', 'other': 'info' }
  return map[type] || 'info'
}

function anomalyTypeLabel(type) {
  const map = { 'swarm_escape': '逃蜂', 'disease': '病虫害', 'weather': '天气影响', 'other': '其他' }
  return map[type] || type
}

function anomalyStatusLabel(status) {
  const map = { 'reported': '待处理', 'processing': '处理中', 'resolved': '已处理' }
  return map[status] || status
}

function severityColor(severity) {
  const map = { low: 'info', medium: 'warning', high: 'danger' }
  return map[severity] || 'info'
}

function severityLabel(s) {
  const map = { low: '低', medium: '中', high: '高' }
  return map[s] || s
}

async function loadData() {
  try {
    const { data } = await dashboardApi.getStats()
    stats.value = data
    statCards.value[0].value = data.total_contracts || 0
    statCards.value[1].value = data.deployed_hives || 0
    statCards.value[2].value = data.pending_inspections || 0
    statCards.value[3].value = data.pending_anomalies || 0
    recentAnomalies.value = data.recent_anomalies || []
    upcomingInspections.value = data.upcoming_inspections || []
  } catch {
    // keep default values
  }
}

onMounted(loadData)
</script>

<style scoped>
.dashboard {
  padding: 0;
}
.stat-row {
  margin-bottom: 0;
}
.stat-card {
  border-radius: 8px;
}
.stat-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.stat-number {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
}
.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
