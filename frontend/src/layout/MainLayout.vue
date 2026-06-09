<template>
  <el-container class="main-layout">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="logo-area">
        <el-icon :size="28" color="#fff"><Promotion /></el-icon>
        <span v-show="!isCollapse" class="logo-text">蜜蜂授粉平台</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        router
        background-color="#1a3a2a"
        text-color="#c0d0c8"
        active-text-color="#67c23a"
      >
        <el-menu-item v-for="item in visibleMenus" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.label }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="main-header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse" :size="20">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>{{ currentLabel }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <span class="user-name">{{ userStore.state.user?.name || '用户' }}</span>
          <el-tag size="small" type="success" class="role-tag">{{ roleLabel }}</el-tag>
          <el-button type="danger" text @click="handleLogout">
            <el-icon><SwitchButton /></el-icon> 退出
          </el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const isCollapse = ref(false)

const allMenus = [
  { path: '/dashboard', label: '首页', icon: 'HomeFilled', roles: ['蜂农', '果园主', '监管员', '管理员'] },
  { path: '/contracts', label: '合同管理', icon: 'Document', roles: ['果园主', '监管员', '管理员'] },
  { path: '/hive-map', label: '投放地图', icon: 'MapLocation', roles: ['蜂农', '管理员'] },
  { path: '/inspections', label: '巡检管理', icon: 'View', roles: ['蜂农', '监管员', '管理员'] },
  { path: '/anomalies', label: '异常管理', icon: 'Warning', roles: ['蜂农', '监管员', '管理员'] },
  { path: '/settlements', label: '结算管理', icon: 'Money', roles: ['果园主', '监管员', '管理员'] },
  { path: '/orchards', label: '果园管理', icon: 'Cherry', roles: ['果园主', '管理员'] }
]

const visibleMenus = computed(() => {
  const role = userStore.getRole()
  if (!role) return allMenus
  return allMenus.filter(m => m.roles.includes(role))
})

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/contracts')) return '/contracts'
  if (path.startsWith('/settlements')) return '/settlements'
  return path
})

const currentLabel = computed(() => {
  const m = allMenus.find(m => activeMenu.value.startsWith(m.path))
  return m ? m.label : '首页'
})

const roleMap = { '蜂农': '蜂农', '果园主': '果园主', '监管员': '监管员', '管理员': '管理员' }
const roleLabel = computed(() => roleMap[userStore.getRole()] || '未知')

function handleLogout() {
  userStore.clearUser()
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}
.sidebar {
  background-color: #1a3a2a;
  transition: width 0.3s;
  overflow: hidden;
}
.logo-area {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}
.main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  padding: 0 20px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.collapse-btn {
  cursor: pointer;
  color: #606266;
}
.collapse-btn:hover {
  color: #1a3a2a;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-name {
  font-size: 14px;
  color: #303133;
}
.role-tag {
  font-size: 12px;
}
.main-content {
  background: #f0f2f5;
  overflow-y: auto;
}
.el-menu {
  border-right: none;
}
</style>
