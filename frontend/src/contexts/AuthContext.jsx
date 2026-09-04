import { createContext, useContext, useState, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import api from '../utils/api'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const queryClient = useQueryClient()

  // Initialize auth state & refresh identity from /api/auth/me
  useEffect(() => {
    async function initAuth() {
      try {
        const token = sessionStorage.getItem('token')
        const userData = sessionStorage.getItem('user')

        if (token && userData) {
          const parsed = JSON.parse(userData)
          setUser(parsed)

          // Verify/refresh user state from backend to ensure full_name is populated
          try {
            const response = await api.get('/api/auth/me')
            if (response.data) {
              const freshUser = response.data
              sessionStorage.setItem('user', JSON.stringify(freshUser))
              setUser(freshUser)
            }
          } catch (e) {
            // Silently swallow session validation error; API interceptors handle 401
          }
        }
      } catch (err) {
        sessionStorage.removeItem('token')
        sessionStorage.removeItem('user')
        queryClient.clear()
        setUser(null)
      } finally {
        setLoading(false)
      }
    }
    initAuth()
  }, [queryClient])

  // Login
  const login = async (email, password) => {
    try {
      queryClient.clear()
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
      queryClient.clear()
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
    queryClient.clear()
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