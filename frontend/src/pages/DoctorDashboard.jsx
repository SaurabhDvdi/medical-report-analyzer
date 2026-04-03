import {useState, useEffect} from 'react'
import {Link} from 'react-router-dom'
import api from '../utils/api'
import {Users, FileText, AlertTriangle, Calendar, Activity, TrendingUp, UserCheck} from 'lucide-react'

export default function DoctorDashboard() {
  const [assignmentStats, setAssignmentStats] = useState({
    total_patients_on_platform: 0,
    your_assigned_patients: 0,
  })
  const [pendingAccess, setPendingAccess] = useState([])
  const [stats, setStats] = useState({
    total_patients: 0,
    recent_patients: 0,
    weekly_consultations: 0,
    critical_cases: 0,
    total_reports: 0,
  })
  const [recentPatients, setRecentPatients] = useState([])
  const [healthChart, setHealthChart] = useState(null)
  const [healthChartError, setHealthChartError] = useState('')
  const [correlationChart, setCorrelationChart] = useState(null)
  const [correlationError, setCorrelationError] = useState('')
  const [loading, setLoading] = useState(true)
  const [statsError, setStatsError] = useState('')

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setStatsError('')
      setLoading(true)
      try {
        const [statsRes, patientsRes] = await Promise.all([
          api.get('/api/doctor/statistics'),
          api.get('/api/users/patients'),
        ])
        if (cancelled) return
        setStats(statsRes.data)
        setRecentPatients(patientsRes.data.slice(0, 5))
        try {
          const assignRes = await api.get('/api/doctor/assignment-stats')
          if (!cancelled) setAssignmentStats(assignRes.data)
        } catch (e) {
          console.error('Assignment stats:', e)
        }
        try {
          const pend = await api.get('/api/doctor/patient-access-requests', {
            params: { status: 'pending' },
          })
          if (!cancelled) setPendingAccess(pend.data)
        } catch (e) {
          console.error('Access requests:', e)
        }
      } catch (error) {
        if (cancelled) return
        console.error('Error fetching dashboard data:', error)
        setStatsError(
          error.response?.data?.detail || 'Failed to load doctor dashboard.'
        )
      } finally {
        if (!cancelled) setLoading(false)
      }

      try {
        const healthSummaryRes = await api.get('/api/analytics/health-summary', {
          responseType: 'blob',
        })
        if (cancelled) return
        const blob =
          healthSummaryRes.data instanceof Blob
            ? healthSummaryRes.data
            : new Blob([healthSummaryRes.data], {type: 'image/png'})
        setHealthChart(URL.createObjectURL(blob))
        setHealthChartError('')
      } catch (err) {
        if (cancelled) return
        console.error('Error loading health summary chart:', err)
        setHealthChart(null)
        setHealthChartError(
          err.response?.data?.detail || 'Health summary chart is unavailable.'
        )
      }

      try {
        const corrRes = await api.get('/api/analytics/correlation', {
          responseType: 'blob',
        })
        if (cancelled) return
        const blob =
          corrRes.data instanceof Blob
            ? corrRes.data
            : new Blob([corrRes.data], {type: 'image/png'})
        setCorrelationChart(URL.createObjectURL(blob))
        setCorrelationError('')
      } catch (err) {
        if (cancelled) return
        console.error('Error loading correlation chart:', err)
        setCorrelationChart(null)
        setCorrelationError(
          err.response?.data?.detail || 'Correlation heatmap is unavailable.'
        )
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    return () => {
      if (healthChart) URL.revokeObjectURL(healthChart)
      if (correlationChart) URL.revokeObjectURL(correlationChart)
    }
  }, [healthChart, correlationChart])

  const respondToRequest = async (requestId, action) => {
    try {
      await api.post(`/api/doctor/patient-access-requests/${requestId}/${action}`)
      const pend = await api.get('/api/doctor/patient-access-requests', {
        params: { status: 'pending' },
      })
      setPendingAccess(pend.data)
      const assignRes = await api.get('/api/doctor/assignment-stats')
      setAssignmentStats(assignRes.data)
    } catch (e) {
      console.error(e)
      alert(e.response?.data?.detail || 'Action failed')
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading dashboard...</div>
  }

  return (
    <div className="px-4 py-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Doctor Dashboard</h1>

        {statsError && (
          <div className="mb-6 rounded-md bg-red-50 border border-red-200 text-red-800 px-4 py-3 text-sm">
            {statsError}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-600">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total patients</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {assignmentStats.total_patients_on_platform}
                </p>
                <p className="text-xs text-gray-500 mt-1">Registered on the platform</p>
              </div>
              <Users className="w-12 h-12 text-blue-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-emerald-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Your patients</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {assignmentStats.your_assigned_patients}
                </p>
                <p className="text-xs text-gray-500 mt-1">Accepted access requests</p>
              </div>
              <UserCheck className="w-12 h-12 text-emerald-500" />
            </div>
          </div>
        </div>

        {pendingAccess.length > 0 && (
          <div className="bg-white rounded-lg shadow-md mb-8 border border-amber-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Pending patient access requests</h2>
            </div>
            <ul className="divide-y divide-gray-200">
              {pendingAccess.map((req) => (
                <li key={req.id} className="px-6 py-4 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-gray-900">{req.patient_name}</p>
                    <p className="text-xs text-gray-500">Request #{req.id}</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => respondToRequest(req.id, 'accept')}
                      className="px-3 py-1.5 rounded-md text-sm bg-green-600 text-white hover:bg-green-700"
                    >
                      Accept
                    </button>
                    <button
                      type="button"
                      onClick={() => respondToRequest(req.id, 'reject')}
                      className="px-3 py-1.5 rounded-md text-sm border border-gray-300 text-gray-700 hover:bg-gray-50"
                    >
                      Reject
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Recent patients</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.recent_patients}</p>
                <p className="text-xs text-gray-500 mt-1">Last 7 days (new accounts)</p>
              </div>
              <TrendingUp className="w-12 h-12 text-green-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Weekly Consultations</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {stats.weekly_consultations}
                </p>
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

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-500" />
              Health summary (all data)
            </h2>
            {healthChart && (
              <img src={healthChart} alt="Health summary" className="w-full rounded-lg border" />
            )}
            {!healthChart && healthChartError && (
              <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-md px-4 py-3">
                {healthChartError}
              </p>
            )}
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Correlation heatmap</h2>
            {correlationChart && (
              <img
                src={correlationChart}
                alt="Correlation heatmap"
                className="w-full rounded-lg border"
              />
            )}
            {!correlationChart && correlationError && (
              <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-md px-4 py-3">
                {correlationError}
              </p>
            )}
          </div>
        </div>

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
