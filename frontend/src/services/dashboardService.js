import api from '../utils/api'

// Dashboard Service
export const getDashboardData = (parameter = null) => {
  const params = new URLSearchParams()
  if (parameter) {
    params.append('parameter', parameter)
  }
  
  return api.get(`/api/dashboard${params.toString() ? '?' + params.toString() : ''}`).then((res) => res.data)
}

export const getDashboardParameter = (parameter) => {
  return getDashboardData(parameter)
}
