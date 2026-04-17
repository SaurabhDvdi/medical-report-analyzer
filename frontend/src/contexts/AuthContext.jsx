import { createContext, useContext, useState, useEffect } from 'react'
import api from '../utils/api'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Initialize auth state
  useEffect(() => {
    try {
      const token = sessionStorage.getItem('token')
      const userData = sessionStorage.getItem('user')

      if (token && userData) {
        setUser(JSON.parse(userData))
      }
    } catch (err) {
      // Corrupted storage cleanup
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('user')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  // Login
  const login = async (email, password) => {
    try {
      const response = await api.post('/api/auth/login', { email, password })
      const { access_token, user: userData } = response.data

      sessionStorage.setItem('token', access_token)
      sessionStorage.setItem('user', JSON.stringify(userData))

      setUser(userData)
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed'
      }
    }
  }

  // Register
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

      sessionStorage.setItem('token', access_token)
      sessionStorage.setItem('user', JSON.stringify(userData))

      setUser(userData)
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed'
      }
    }
  }

  // Logout
  const logout = () => {
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('user')
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