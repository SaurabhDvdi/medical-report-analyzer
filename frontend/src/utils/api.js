import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
})

// REQUEST INTERCEPTOR
api.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('token')

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

// RESPONSE INTERCEPTOR
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('user')

      // Prevent redirect loop
      if (window.location.pathname !== '/login') {
        window.location.replace('/login')
      }
    }

    return Promise.reject(error)
  }
)

export default api