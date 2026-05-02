import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Reports from './pages/Reports'
import ReportViewer from './pages/ReportViewer'
import Medicines from './pages/Medicines'
import DoctorInterface from './pages/DoctorInterface'
import DoctorDashboard from './pages/DoctorDashboard'
import DoctorProfile from './pages/DoctorProfile'
import PatientDashboard from './pages/PatientDashboard'
import PatientProfile from './pages/PatientProfile'
import FindDoctors from './pages/FindDoctors'
import HealthSummaryPage from './pages/HealthSummaryPage'
import CorrelationPage from './pages/CorrelationPage'
import MedicalDashboard from './pages/MedicalDashboard'
import Layout from './components/Layout'
import { ToastProvider } from './components/Toast'
import RoleRoute from './components/RoleRoute'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 10, // 10 minutes
    },
  },
})

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }
  
  if (!user) {
    return <Navigate to="/login" />
  }
  
  return children
}

function AppRoutes() {
  const { user } = useAuth()
  
  return (
    <Routes>
      <Route path="/login" element={!user ? <Login /> : <Navigate to="/dashboard" />} />
      <Route path="/register" element={!user ? <Register /> : <Navigate to="/dashboard" />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" />} />
        {user?.role === 'doctor' ? (
          <>
            <Route
              path="dashboard"
              element={
                <RoleRoute requiredRole="doctor">
                  <DoctorDashboard />
                </RoleRoute>
              }
            />
            <Route
              path="doctor/profile"
              element={
                <RoleRoute requiredRole="doctor">
                  <DoctorProfile />
                </RoleRoute>
              }
            />
            <Route
              path="doctor/patients"
              element={
                <RoleRoute requiredRole="doctor">
                  <DoctorInterface />
                </RoleRoute>
              }
            />
            <Route
              path="doctor/patient/:id"
              element={
                <RoleRoute requiredRole="doctor">
                  <DoctorInterface />
                </RoleRoute>
              }
            />
            <Route path="reports" element={<Reports />} />
            <Route path="reports/:id" element={<ReportViewer />} />
            <Route path="medicines" element={<Medicines />} />
          </>
        ) : (
          <>
            <Route path="dashboard" element={<PatientDashboard />} />
            <Route path="medical-dashboard" element={<MedicalDashboard />} />
            <Route path="find-doctors" element={<FindDoctors />} />
            <Route path="profile" element={<PatientProfile />} />
            <Route path="reports" element={<Reports />} />
            <Route path="reports/:id" element={<ReportViewer />} />
            <Route path="medicines" element={<Medicines />} />
            <Route
              path="analytics/health-summary"
              element={
                <RoleRoute requiredRole="patient">
                  <HealthSummaryPage />
                </RoleRoute>
              }
            />
            <Route
              path="analytics/correlation"
              element={
                <RoleRoute requiredRole="patient">
                  <CorrelationPage />
                </RoleRoute>
              }
            />
          </>
        )}
      </Route>
    </Routes>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AuthProvider>
          <ToastProvider>
            <AppRoutes />
          </ToastProvider>
        </AuthProvider>
      </Router>
    </QueryClientProvider>
  )
}

export default App

