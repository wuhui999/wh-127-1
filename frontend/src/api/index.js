import axios from 'axios'
import router from '../router'

const http = axios.create({
  baseURL: '/api',
  timeout: 15000
})

http.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  res => res,
  err => {
    if (err.response && err.response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      router.push({ name: 'Login' })
    }
    return Promise.reject(err)
  }
)

export const authApi = {
  login: data => http.post('/auth/login', data),
  getMe: () => http.get('/auth/me'),
  register: data => http.post('/auth/register', data),
  listUsers: params => http.get('/auth/users', { params })
}

export const contractApi = {
  list: params => http.get('/contracts', { params }),
  get: id => http.get(`/contracts/${id}`),
  create: data => http.post('/contracts', data),
  update: (id, data) => http.put(`/contracts/${id}`, data),
  changeStatus: (id, status) => http.put(`/contracts/${id}/status`, { status }),
  delete: id => http.delete(`/contracts/${id}`)
}

export const hiveApi = {
  list: params => http.get('/hives', { params }),
  get: id => http.get(`/hives/${id}`),
  create: data => http.post('/hives', data),
  update: (id, data) => http.put(`/hives/${id}`, data),
  deploy: (id, data) => http.post(`/hives/${id}/deploy`, data),
  withdraw: id => http.post(`/hives/${id}/withdraw`)
}

export const inspectionApi = {
  list: params => http.get('/inspections', { params }),
  get: id => http.get(`/inspections/${id}`),
  create: data => http.post('/inspections', data),
  getOverdue: params => http.get('/inspections/overdue', { params })
}

export const anomalyApi = {
  list: params => http.get('/anomalies', { params }),
  get: id => http.get(`/anomalies/${id}`),
  create: data => http.post('/anomalies', data),
  update: (id, data) => http.put(`/anomalies/${id}`, data),
  resolve: (id, data) => http.put(`/anomalies/${id}/resolve`, data)
}

export const settlementApi = {
  list: params => http.get('/settlements', { params }),
  get: id => http.get(`/settlements/${id}`),
  create: data => http.post('/settlements', data),
  confirm: id => http.put(`/settlements/${id}/confirm`),
  pay: id => http.put(`/settlements/${id}/pay`),
  calculate: contractId => http.get(`/settlements/calculate/${contractId}`)
}

export const orchardApi = {
  list: params => http.get('/orchards', { params }),
  get: id => http.get(`/orchards/${id}`),
  create: data => http.post('/orchards', data),
  update: (id, data) => http.put(`/orchards/${id}`, data),
  delete: id => http.delete(`/orchards/${id}`)
}

export const dashboardApi = {
  getStats: () => http.get('/dashboard/stats')
}

export default http
