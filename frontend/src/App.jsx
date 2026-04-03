import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
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
import Layout from './components/Layout'

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
            <Route path="dashboard" element={<DoctorDashboard />} />
            <Route path="doctor/profile" element={<DoctorProfile />} />
            <Route path="doctor/patients" element={<DoctorInterface />} />
            <Route path="doctor/patient/:id" element={<DoctorInterface />} />
            <Route path="reports" element={<Reports />} />
            <Route path="reports/:id" element={<ReportViewer />} />
            <Route path="medicines" element={<Medicines />} />
          </>
        ) : (
          <>
            <Route path="dashboard" element={<PatientDashboard />} />
            <Route path="find-doctors" element={<FindDoctors />} />
            <Route path="profile" element={<PatientProfile />} />
            <Route path="reports" element={<Reports />} />
            <Route path="reports/:id" element={<ReportViewer />} />
            <Route path="medicines" element={<Medicines />} />
          </>
        )}
      </Route>
    </Routes>
  )
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  )
}

export default App

