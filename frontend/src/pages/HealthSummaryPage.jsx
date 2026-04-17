import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../utils/api'
import { ArrowLeft, Loader, AlertCircle, TrendingUp } from 'lucide-react'
import { ChartContainer } from '../components/EnhancedCards'
import { useToast } from '../components/Toast'

export default function HealthSummaryPage() {
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [healthChart, setHealthChart] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const fetchHealthSummary = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get('/api/analytics/health-summary', {
        responseType: 'blob',
      })

      const blob =
        response.data instanceof Blob
          ? response.data
          : new Blob([response.data], { type: 'image/png' })
      setHealthChart(URL.createObjectURL(blob))
      showToast('Health summary loaded successfully', 'success')
    } catch (err) {
      console.error('Error loading health summary:', err)
      const errorMessage = err.response?.data?.detail ||
        'Unable to load health summary. Please try again later.'
      setError(errorMessage)
      showToast(errorMessage, 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false

    fetchHealthSummary()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    return () => {
      if (healthChart) URL.revokeObjectURL(healthChart)
    }
  }, [healthChart])

  return (
    <div className="px-4 py-6 bg-gradient-to-br from-blue-50 to-indigo-50 min-h-screen">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-800 font-medium mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </button>
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="w-8 h-8 text-blue-500" />
            <h1 className="text-3xl font-bold text-gray-900">Health Summary</h1>
          </div>
          <p className="text-gray-600">
            Detailed overview of your health trends and insights based on your medical reports.
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <Loader className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" />
            <p className="text-gray-600">Generating your health summary...</p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="bg-white rounded-xl shadow-md p-8">
            <div className="flex items-start gap-4">
              <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-red-800 mb-2">Unable to Load Summary</h3>
                <p className="text-red-700">{error}</p>
                <p className="text-sm text-gray-600 mt-4">
                  Possible reasons:
                </p>
                <ul className="text-sm text-gray-600 list-disc list-inside mt-2 space-y-1">
                  <li>No medical reports have been uploaded yet</li>
                  <li>Reports are still being processed</li>
                  <li>Server is temporarily unavailable</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Success State */}
        {!loading && healthChart && (
          <ChartContainer
            title="Health Summary"
            onRefresh={fetchHealthSummary}
            isLoading={false}
            error={null}
          >
            <img
              src={healthChart}
              alt="Health Summary Analytics"
              className="w-full rounded-lg border border-gray-200"
            />
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="font-semibold text-gray-900 mb-2">About this chart</h3>
              <p className="text-sm text-gray-600">
                This visualization shows your health metrics over time, including trends in key
                parameters extracted from your medical reports. Use this data to track your health
                progress and identify any concerning patterns.
              </p>
            </div>
          </ChartContainer>
        )}

        {/* Empty State */}
        {!loading && !error && !healthChart && (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">No health summary data available yet</p>
            <p className="text-sm text-gray-500">
              Upload some medical reports to see your health trends and analytics.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
