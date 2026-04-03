import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../utils/api'
import { Heart, Pill, AlertCircle, TrendingUp, FileText, Activity, Loader, Stethoscope, UserCheck } from 'lucide-react'

export default function PatientDashboard() {
  const [profile, setProfile] = useState(null)
  const [discovery, setDiscovery] = useState({
    total_doctors_on_platform: 0,
    your_active_doctors: 0,
  })
  const [stats, setStats] = useState({
    activeMedicines: 0,
    abnormalValues: 0,
    totalReports: 0,
    recentReports: [],
  })
  const [healthChart, setHealthChart] = useState(null)
  const [healthChartError, setHealthChartError] = useState('')
  const [correlationChart, setCorrelationChart] = useState(null)
  const [correlationError, setCorrelationError] = useState('')
  const [loading, setLoading] = useState(true)
  const [statsError, setStatsError] = useState('')

  useEffect(() => {
    let cancelled = false

    const fetchDashboardData = async () => {
      setStatsError('')
      setHealthChartError('')
      setCorrelationError('')
      setLoading(true)
      try {
        const [profileRes, medicinesRes, reportsRes] = await Promise.all([
          api.get('/api/patient/profile'),
          api.get('/api/medicines'),
          api.get('/api/reports'),
        ])

        if (cancelled) return

        if (profileRes.data.exists) {
          setProfile(profileRes.data)
        }

        try {
          const discoveryRes = await api.get('/api/patient/discovery-stats')
          if (!cancelled) setDiscovery(discoveryRes.data)
        } catch (e) {
          console.error('Discovery stats:', e)
        }

        const medicines = medicinesRes.data
        const reports = reportsRes.data

        let abnormalCount = 0
        for (const report of reports) {
          try {
            const reportDetail = await api.get(`/api/reports/${report.id}`)
            if (cancelled) return
            abnormalCount +=
              reportDetail.data.lab_values?.filter((lv) => lv.is_abnormal).length || 0
          } catch (err) {
            console.error(`Error fetching report ${report.id}:`, err)
          }
        }

        if (cancelled) return

        setStats({
          activeMedicines: medicines.filter((m) => m.status === 'current').length,
          abnormalValues: abnormalCount,
          totalReports: reports.length,
          recentReports: reports.slice(0, 3),
        })

        try {
          const healthSummaryRes = await api.get('/api/analytics/health-summary', {
            responseType: 'blob',
          })
          if (cancelled) return
          const blob =
            healthSummaryRes.data instanceof Blob
              ? healthSummaryRes.data
              : new Blob([healthSummaryRes.data], { type: 'image/png' })
          setHealthChart(URL.createObjectURL(blob))
          setHealthChartError('')
        } catch (err) {
          if (cancelled) return
          console.error('Error loading health summary chart:', err)
          setHealthChart(null)
          setHealthChartError(
            err.response?.data?.detail || 'Health summary chart is unavailable right now.'
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
              : new Blob([corrRes.data], { type: 'image/png' })
          setCorrelationChart(URL.createObjectURL(blob))
          setCorrelationError('')
        } catch (err) {
          if (cancelled) return
          console.error('Error loading correlation chart:', err)
          setCorrelationChart(null)
          setCorrelationError(
            err.response?.data?.detail || 'Correlation heatmap is unavailable right now.'
          )
        }
      } catch (error) {
        if (cancelled) return
        console.error('Error fetching dashboard data:', error)
        setStatsError(
          error.response?.data?.detail || error.message || 'Failed to load dashboard.'
        )
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchDashboardData()
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

  if (loading) {
    return (
      <div className="text-center py-12 flex flex-col items-center gap-2">
        <Loader className="w-8 h-8 text-blue-500 animate-spin" />
        <span>Loading your health dashboard...</span>
      </div>
    )
  }

  return (
    <div className="px-4 py-6 bg-gradient-to-br from-blue-50 to-indigo-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Your Health Dashboard</h1>
          <p className="text-gray-600">Welcome back! Here&apos;s your health overview</p>
        </div>

        {statsError && (
          <div className="mb-6 rounded-md bg-red-50 border border-red-200 text-red-800 px-4 py-3 text-sm">
            {statsError}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-teal-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total doctors available</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {discovery.total_doctors_on_platform}
                </p>
                <p className="text-xs text-gray-500 mt-1">On the platform</p>
              </div>
              <Stethoscope className="w-12 h-12 text-teal-500" />
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-cyan-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Your active doctors</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {discovery.your_active_doctors}
                </p>
                <p className="text-xs text-gray-500 mt-1">Accepted access requests</p>
              </div>
              <UserCheck className="w-12 h-12 text-cyan-500" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Medicines</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.activeMedicines}</p>
              </div>
              <Pill className="w-12 h-12 text-green-500" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-red-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Abnormal Values</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.abnormalValues}</p>
                <p className="text-xs text-gray-500 mt-1">Across all reports</p>
              </div>
              <AlertCircle className="w-12 h-12 text-red-500" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Reports</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.totalReports}</p>
              </div>
              <FileText className="w-12 h-12 text-blue-500" />
            </div>
          </div>

          {profile && profile.bmi && (
            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">BMI</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {profile.bmi.toFixed(1)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {profile.bmi < 18.5
                      ? 'Underweight'
                      : profile.bmi < 25
                      ? 'Normal'
                      : profile.bmi < 30
                      ? 'Overweight'
                      : 'Obese'}
                  </p>
                </div>
                <Activity className="w-12 h-12 text-purple-500" />
              </div>
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="w-6 h-6 text-blue-500 mr-2" />
            Health Summary
          </h2>
          {healthChart && (
            <img src={healthChart} alt="Health Summary" className="w-full rounded-lg" />
          )}
          {!healthChart && healthChartError && (
            <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-md px-4 py-3">
              {healthChartError}
            </p>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Lab correlation</h2>
          {correlationChart && (
            <img
              src={correlationChart}
              alt="Correlation heatmap"
              className="w-full rounded-lg"
            />
          )}
          {!correlationChart && correlationError && (
            <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-md px-4 py-3">
              {correlationError}
            </p>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-md mb-8">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">Recent Reports</h2>
            <Link
              to="/reports"
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              View All →
            </Link>
          </div>
          <div className="divide-y divide-gray-200">
            {stats.recentReports.length === 0 ? (
              <div className="px-6 py-12 text-center text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p>No reports yet.</p>
                <Link to="/reports" className="text-blue-600 hover:underline mt-2 inline-block">
                  Upload your first report
                </Link>
              </div>
            ) : (
              stats.recentReports.map((report) => (
                <Link
                  key={report.id}
                  to={`/reports/${report.id}`}
                  className="block px-6 py-4 hover:bg-blue-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{report.file_name}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(report.upload_date).toLocaleDateString()}
                      </p>
                      {report.ai_summary && (
                        <p className="text-sm text-gray-600 mt-1 line-clamp-1">
                          {report.ai_summary}
                        </p>
                      )}
                    </div>
                    <span
                      className={`px-3 py-1 text-xs rounded-full ${
                        report.ocr_status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : report.ocr_status === 'failed'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {report.ocr_status}
                    </span>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Link
            to="/find-doctors"
            className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow border-2 border-transparent hover:border-blue-500"
          >
            <Stethoscope className="w-8 h-8 text-blue-500 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Find Doctors</h3>
            <p className="text-sm text-gray-600">Search by name, category, and specialty</p>
          </Link>
          <Link
            to="/reports"
            className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow border-2 border-transparent hover:border-blue-500"
          >
            <FileText className="w-8 h-8 text-blue-500 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">View Reports</h3>
            <p className="text-sm text-gray-600">See all your medical reports and lab results</p>
          </Link>

          <Link
            to="/medicines"
            className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow border-2 border-transparent hover:border-blue-500"
          >
            <Pill className="w-8 h-8 text-blue-500 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Manage Medicines</h3>
            <p className="text-sm text-gray-600">Track your current and past medications</p>
          </Link>

          <Link
            to="/profile"
            className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow border-2 border-transparent hover:border-blue-500"
          >
            <Heart className="w-8 h-8 text-blue-500 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Update Profile</h3>
            <p className="text-sm text-gray-600">Keep your health information up to date</p>
          </Link>
        </div>
      </div>
    </div>
  )
}
