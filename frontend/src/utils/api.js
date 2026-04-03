import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    } else if (
      config.data &&
      typeof config.data === 'object' &&
      !(config.data instanceof ArrayBuffer) &&
      !(config.data instanceof URLSearchParams)
    ) {
      config.headers['Content-Type'] = 'application/json'
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      delete api.defaults.headers.common.Authorization
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.assign('/login')
      }
    }
    return Promise.reject(error)
  }
)

export default api
