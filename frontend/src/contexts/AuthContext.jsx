import { createContext, useContext, useState, useEffect } from 'react'
import api from '../utils/api'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      setUser(JSON.parse(localStorage.getItem('user') || 'null'))
    }
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    try {
      const response = await api.post('/api/auth/login', { email, password })
      const { access_token, user: userData } = response.data
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))
      setUser(userData)
      return { success: true }
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' }
    }
  }

  const register = async (email, password, fullName, role, doctorPayload = null) => {
    try {
      const body = {
        email,
        password,
        full_name: fullName,
        role,
      }
      if (role === 'doctor' && doctorPayload) {
        Object.assign(body, doctorPayload)
      }
      const response = await api.post('/api/auth/register', body)
      const { access_token, user: userData } = response.data
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))
      setUser(userData)
      return { success: true }
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' }
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}

