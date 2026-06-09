import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layout/MainLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'contracts', name: 'Contracts', component: () => import('../views/Contracts.vue') },
      { path: 'contracts/:id', name: 'ContractDetail', component: () => import('../views/ContractDetail.vue') },
      { path: 'hive-map', name: 'HiveMap', component: () => import('../views/HiveMap.vue') },
      { path: 'inspections', name: 'Inspections', component: () => import('../views/Inspections.vue') },
      { path: 'inspections/new', name: 'InspectionForm', component: () => import('../views/InspectionForm.vue') },
      { path: 'anomalies', name: 'Anomalies', component: () => import('../views/Anomalies.vue') },
      { path: 'settlements', name: 'Settlements', component: () => import('../views/Settlements.vue') },
      { path: 'settlements/:id', name: 'SettlementDetail', component: () => import('../views/SettlementDetail.vue') },
      { path: 'orchards', name: 'Orchards', component: () => import('../views/Orchards.vue') }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.matched.some(r => r.meta.requiresAuth) && !token) {
    next({ name: 'Login' })
  } else if (to.name === 'Login' && token) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
