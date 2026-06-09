import { reactive } from 'vue'

const state = reactive({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('token') || null
})

export function useUserStore() {
  function setUser(user, token) {
    state.user = user
    state.token = token
    localStorage.setItem('user', JSON.stringify(user))
    localStorage.setItem('token', token)
  }

  function clearUser() {
    state.user = null
    state.token = null
    localStorage.removeItem('user')
    localStorage.removeItem('token')
  }

  function getRole() {
    return state.user?.role || ''
  }

  function isLoggedIn() {
    return !!state.token
  }

  return { state, setUser, clearUser, getRole, isLoggedIn }
}
