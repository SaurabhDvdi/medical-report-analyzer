import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../utils/api'
import { Users, FileText, AlertTriangle, Calendar, Activity, TrendingUp } from 'lucide-react'

export default function DoctorDashboard() {
  const [stats, setStats] = useState({
    total_patients: 0,
    recent_patients: 0,
    weekly_consultations: 0,
    critical_cases: 0,
    total_reports: 0
  })
  const [recentPatients, setRecentPatients] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [statsRes, patientsRes] = await Promise.all([
        api.get('/api/doctor/statistics'),
        api.get('/api/users/patients')
      ])

      setStats(statsRes.data)
      // Get recent patients (last 5)
      setRecentPatients(patientsRes.data.slice(0, 5))
      setLoading(false)
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading dashboard...</div>
  }

  return (
    <div className="px-4 py-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Doctor Dashboard</h1>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Patients</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total_patients}</p>
              </div>
              <Users className="w-12 h-12 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Recent Patients</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.recent_patients}</p>
                <p className="text-xs text-gray-500 mt-1">Last 7 days</p>
              </div>
              <TrendingUp className="w-12 h-12 text-green-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Weekly Consultations</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.weekly_consultations}</p>
                <p className="text-xs text-gray-500 mt-1">This week</p>
              </div>
              <Calendar className="w-12 h-12 text-purple-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Critical Cases</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.critical_cases}</p>
                <p className="text-xs text-gray-500 mt-1">Abnormal values</p>
              </div>
              <AlertTriangle className="w-12 h-12 text-red-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-indigo-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Reports</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total_reports}</p>
              </div>
              <FileText className="w-12 h-12 text-indigo-500" />
            </div>
          </div>
        </div>

        {/* Recent Patients Panel */}
        <div className="bg-white rounded-lg shadow-md mb-8">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">Recent Patients</h2>
            <Link
              to="/doctor/patients"
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              View All →
            </Link>
          </div>
          <div className="divide-y divide-gray-200">
            {recentPatients.length === 0 ? (
              <div className="px-6 py-12 text-center text-gray-500">
                <Users className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p>No patients yet</p>
              </div>
            ) : (
              recentPatients.map((patient) => (
                <Link
                  key={patient.id}
                  to={`/doctor/patient/${patient.id}`}
                  className="block px-6 py-4 hover:bg-blue-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{patient.full_name}</p>
                      <p className="text-sm text-gray-500">{patient.email}</p>
                      {patient.age && (
                        <p className="text-xs text-gray-400 mt-1">
                          {patient.age} years • {patient.gender} • {patient.blood_group}
                        </p>
                      )}
                    </div>
                    <Activity className="w-5 h-5 text-gray-400" />
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link
            to="/doctor/patients"
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow border-2 border-transparent hover:border-blue-500"
          >
            <Users className="w-8 h-8 text-blue-500 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">View All Patients</h3>
            <p className="text-sm text-gray-600">Browse and search patient database</p>
          </Link>

          <Link
            to="/doctor/profile"
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow border-2 border-transparent hover:border-blue-500"
          >
            <Activity className="w-8 h-8 text-blue-500 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Edit Profile</h3>
            <p className="text-sm text-gray-600">Update your professional information</p>
          </Link>

          <Link
            to="/reports"
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow border-2 border-transparent hover:border-blue-500"
          >
            <FileText className="w-8 h-8 text-blue-500 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">View Reports</h3>
            <p className="text-sm text-gray-600">Access all medical reports</p>
          </Link>
        </div>
      </div>
    </div>
  )
}

