import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../utils/api'
import { FileText, TrendingUp, AlertCircle, Activity } from 'lucide-react'

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalReports: 0,
    abnormalValues: 0,
    totalMedicines: 0,
    recentReports: []
  })
  const [healthChart, setHealthChart] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [reportsRes, medicinesRes] = await Promise.all([
        api.get('/api/reports'),
        api.get('/api/medicines')
      ])

      const reports = reportsRes.data
      const medicines = medicinesRes.data
      
      // Count abnormal values
      let abnormalCount = 0
      for (const report of reports) {
        try {
          const reportDetail = await api.get(`/api/reports/${report.id}`)
          abnormalCount += reportDetail.data.lab_values?.filter(lv => lv.is_abnormal).length || 0
        } catch (err) {
          console.error(`Error fetching report ${report.id}:`, err)
        }
      }

      setStats({
        totalReports: reports.length,
        abnormalValues: abnormalCount,
        totalMedicines: medicines.filter(m => m.status === 'current').length,
        recentReports: reports.slice(0, 5)
      })

      // Try to load health summary chart
      try {
        const healthSummaryRes = await api.get('/api/analytics/health-summary', { responseType: 'blob' })
        const imageUrl = URL.createObjectURL(healthSummaryRes.data)
        setHealthChart(imageUrl)
      } catch (err) {
        console.error('Error loading health summary chart:', err)
        // Chart will not be displayed if there's no data
      }

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
    <div className="px-4 py-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <FileText className="w-8 h-8 text-blue-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Reports</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalReports}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <AlertCircle className="w-8 h-8 text-red-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Abnormal Values</p>
              <p className="text-2xl font-bold text-gray-900">{stats.abnormalValues}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Activity className="w-8 h-8 text-green-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Current Medicines</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalMedicines}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Health Summary Chart */}
      {healthChart && (
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Health Summary</h2>
          <img src={healthChart} alt="Health Summary" className="w-full" />
        </div>
      )}

      {/* Recent Reports */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Recent Reports</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {stats.recentReports.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              No reports yet. <Link to="/reports" className="text-blue-600 hover:underline">Upload your first report</Link>
            </div>
          ) : (
            stats.recentReports.map((report) => (
              <Link
                key={report.id}
                to={`/reports/${report.id}`}
                className="block px-6 py-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{report.file_name}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(report.upload_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className={`px-2 py-1 text-xs rounded ${
                      report.ocr_status === 'completed' 
                        ? 'bg-green-100 text-green-800' 
                        : report.ocr_status === 'processing'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {report.ocr_status}
                    </span>
                    <TrendingUp className="w-5 h-5 text-gray-400" />
                  </div>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

