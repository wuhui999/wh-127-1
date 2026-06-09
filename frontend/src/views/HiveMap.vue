<template>
  <div class="hive-map-page">
    <div class="map-sidebar">
      <div class="sidebar-header">
        <h4>蜂箱列表</h4>
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable size="small" style="width: 120px" @change="filterHives">
          <el-option label="在投" value="deployed" />
          <el-option label="巡检中" value="inspecting" />
          <el-option label="异常" value="anomaly" />
          <el-option label="闲置" value="idle" />
          <el-option label="已撤回" value="withdrawn" />
        </el-select>
      </div>
      <div class="hive-list">
        <div
          v-for="hive in filteredHives"
          :key="hive.id"
          class="hive-item"
          :class="{ active: selectedHive?.id === hive.id }"
          @click="focusHive(hive)"
        >
          <div class="hive-item-header">
            <span class="hive-no">{{ hive.hive_no }}</span>
            <el-tag :color="markerColor(hive.status)" size="small" effect="dark" style="border: none; color: #fff;">{{ statusLabel(hive.status) }}</el-tag>
          </div>
          <div class="hive-info">
            <span v-if="hive.gps_lat">GPS: {{ hive.gps_lat }}, {{ hive.gps_lng }}</span>
          </div>
          <div class="hive-info">
            <span v-if="hive.last_inspection_at">最近巡检: {{ hive.last_inspection_at }}</span>
            <span v-else style="color: #f56c6c;">未巡检</span>
          </div>
          <div class="hive-info" v-if="hive.contract_no">
            <span>合同: {{ hive.contract_no }}</span>
          </div>
        </div>
        <el-empty v-if="filteredHives.length === 0" description="暂无蜂箱数据" :image-size="40" />
      </div>
    </div>
    <div class="map-container" ref="mapContainer"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import L from 'leaflet'
import { hiveApi } from '../api'

const mapContainer = ref(null)
const hives = ref([])
const filteredHives = ref([])
const statusFilter = ref('')
const selectedHive = ref(null)
let map = null
let markers = []

const statusColorMap = {
  deployed: '#67c23a',
  inspecting: '#409eff',
  anomaly: '#f56c6c',
  idle: '#909399',
  withdrawn: '#e6a23c'
}

function markerColor(status) {
  return statusColorMap[status] || '#909399'
}

function statusLabel(status) {
  const map = { deployed: '在投', inspecting: '巡检中', anomaly: '异常', idle: '闲置', withdrawn: '已撤回' }
  return map[status] || status
}

function filterHives() {
  if (!statusFilter.value) {
    filteredHives.value = hives.value
  } else {
    filteredHives.value = hives.value.filter(h => h.status === statusFilter.value)
  }
  updateMarkers()
}

function createMarkerIcon(status) {
  const color = markerColor(status)
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="width:24px;height:24px;border-radius:50%;background:${color};border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.3);"></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -14]
  })
}

function updateMarkers() {
  markers.forEach(m => map.removeLayer(m))
  markers = []
  filteredHives.value.forEach(hive => {
    if (hive.gps_lat && hive.gps_lng) {
      const marker = L.marker([hive.gps_lat, hive.gps_lng], { icon: createMarkerIcon(hive.status) })
      marker.bindPopup(`
        <div style="min-width:180px;">
          <div style="font-weight:700;margin-bottom:6px;">蜂箱: ${hive.hive_no}</div>
          <div>GPS: ${hive.gps_lat}, ${hive.gps_lng}</div>
          <div>状态: ${statusLabel(hive.status)}</div>
          <div>最近巡检: ${hive.last_inspection_at || '暂无'}</div>
        </div>
      `)
      marker.on('click', () => { selectedHive.value = hive })
      marker.addTo(map)
      markers.push(marker)
    }
  })
}

function focusHive(hive) {
  selectedHive.value = hive
  if (hive.gps_lat && hive.gps_lng) {
    map.setView([hive.gps_lat, hive.gps_lng], 12)
    const marker = markers.find(m => {
      const ll = m.getLatLng()
      return ll.lat === hive.gps_lat && ll.lng === hive.gps_lng
    })
    if (marker) marker.openPopup()
  }
}

async function loadHives() {
  try {
    const { data } = await hiveApi.list({ size: 5000 })
    hives.value = data.items || data || []
    filteredHives.value = hives.value
  } catch {
    hives.value = []
    filteredHives.value = []
  }
}

function initMap() {
  map = L.map(mapContainer.value, {
    center: [30, 110],
    zoom: 5,
    zoomControl: true
  })
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(map)
}

onMounted(async () => {
  await nextTick()
  initMap()
  await loadHives()
  updateMarkers()
})

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style scoped>
.hive-map-page {
  display: flex;
  height: calc(100vh - 120px);
  margin: -20px;
}
.map-sidebar {
  width: 320px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-header {
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e4e7ed;
}
.sidebar-header h4 {
  margin: 0;
  color: #1a3a2a;
}
.hive-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.hive-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.2s;
}
.hive-item:hover {
  background: #f0f9eb;
}
.hive-item.active {
  background: #e1f3d8;
}
.hive-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.hive-no {
  font-weight: 600;
  color: #303133;
}
.hive-info {
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
}
.map-container {
  flex: 1;
}
</style>
