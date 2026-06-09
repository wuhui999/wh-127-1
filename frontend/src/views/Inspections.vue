<template>
  <div class="inspections-page">
    <el-card shadow="hover">
      <div class="page-header">
        <h3>巡检管理</h3>
        <el-button type="primary" @click="$router.push('/inspections/new')">
          <el-icon><Plus /></el-icon> 新建巡检
        </el-button>
      </div>

      <el-alert
        v-if="overdueHives.length > 0"
        type="error"
        :closable="false"
        show-icon
        style="margin-bottom: 16px;"
      >
        <template #title>
          <span>有 <strong>{{ overdueHives.length }}</strong> 个蜂箱巡检已逾期！</span>
        </template>
        <div class="overdue-list">
          <el-tag
            v-for="hive in overdueHives"
            :key="hive.id"
            :type="hive.days_overdue > 14 ? 'danger' : 'warning'"
            style="margin: 2px 4px;"
          >
            {{ hive.hive_no }} - 逾期{{ hive.days_overdue }}天
            <span v-if="hive.risk_level"> (风险: {{ hive.risk_level }})</span>
          </el-tag>
        </div>
      </el-alert>

      <div class="filter-bar">
        <el-input v-model="filters.hive_no" placeholder="蜂箱编号" clearable style="width: 160px" @keyup.enter="loadInspections">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-date-picker
          v-model="filters.dateRange"
          type="daterange"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 260px"
          @change="loadInspections"
        />
        <el-input v-model="filters.inspector" placeholder="巡检员" clearable style="width: 140px" @keyup.enter="loadInspections" />
        <el-button type="primary" @click="loadInspections">搜索</el-button>
      </div>

      <el-table :data="inspections" stripe v-loading="loading">
        <el-table-column prop="hive_no" label="蜂箱编号" width="120" />
        <el-table-column prop="inspector" label="巡检员" width="100" />
        <el-table-column prop="colony_strength" label="蜂群强度" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="strengthColor(row.colony_strength)" size="small">{{ row.colony_strength }}/10</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="pest_disease" label="病虫害" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.pest_disease ? 'danger' : 'success'" size="small">{{ row.pest_disease ? '有' : '无' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="supplementary_feeding" label="补饲" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.supplementary_feeding ? 'warning' : 'info'" size="small">{{ row.supplementary_feeding ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="inspected_at" label="巡检时间" width="180" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="viewDetail(row)">查看</el-button>
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
          @size-change="loadInspections"
          @current-change="loadInspections"
        />
      </div>
    </el-card>

    <el-dialog v-model="detailVisible" title="巡检详情" width="550px">
      <el-descriptions :column="2" border v-if="currentInspection">
        <el-descriptions-item label="蜂箱编号">{{ currentInspection.hive_no }}</el-descriptions-item>
        <el-descriptions-item label="巡检员">{{ currentInspection.inspector }}</el-descriptions-item>
        <el-descriptions-item label="蜂群强度">{{ currentInspection.colony_strength }}/10</el-descriptions-item>
        <el-descriptions-item label="巡检时间">{{ currentInspection.inspected_at }}</el-descriptions-item>
        <el-descriptions-item label="病虫害">{{ currentInspection.pest_disease ? '有' : '无' }}</el-descriptions-item>
        <el-descriptions-item label="补饲">{{ currentInspection.supplementary_feeding ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="病虫害详情" :span="2">{{ currentInspection.pest_detail || '无' }}</el-descriptions-item>
        <el-descriptions-item label="补饲详情" :span="2">{{ currentInspection.feeding_detail || '无' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ currentInspection.remarks || '无' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { inspectionApi } from '../api'

const loading = ref(false)
const inspections = ref([])
const overdueHives = ref([])
const detailVisible = ref(false)
const currentInspection = ref(null)

const filters = reactive({ hive_no: '', dateRange: null, inspector: '' })
const pagination = reactive({ page: 1, size: 10, total: 0 })

function strengthColor(val) {
  if (val <= 3) return 'danger'
  if (val <= 6) return 'warning'
  return 'success'
}

async function loadInspections() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      hive_no: filters.hive_no,
      inspector: filters.inspector
    }
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_date = filters.dateRange[0]
      params.end_date = filters.dateRange[1]
    }
    const { data } = await inspectionApi.list(params)
    inspections.value = data.items || data || []
    pagination.total = data.total || inspections.value.length
  } catch {
    inspections.value = []
  } finally {
    loading.value = false
  }
}

async function loadOverdue() {
  try {
    const { data } = await inspectionApi.getOverdue()
    overdueHives.value = data.items || data || []
  } catch {
    overdueHives.value = []
  }
}

function viewDetail(row) {
  currentInspection.value = row
  detailVisible.value = true
}

onMounted(() => {
  loadInspections()
  loadOverdue()
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
.overdue-list {
  margin-top: 8px;
}
</style>
