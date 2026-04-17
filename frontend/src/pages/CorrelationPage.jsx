import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../utils/api'
import { ArrowLeft, Loader, AlertCircle, Activity } from 'lucide-react'
import { ChartContainer } from '../components/EnhancedCards'
import { useToast } from '../components/Toast'

export default function CorrelationPage() {
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [correlationChart, setCorrelationChart] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const fetchCorrelation = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get('/api/analytics/correlation', {
        responseType: 'blob',
      })

      const blob =
        response.data instanceof Blob
          ? response.data
          : new Blob([response.data], { type: 'image/png' })
      setCorrelationChart(URL.createObjectURL(blob))
      showToast('Correlation heatmap loaded successfully', 'success')
    } catch (err) {
      console.error('Error loading correlation chart:', err)
      const errorMessage = err.response?.data?.detail ||
        'Unable to load correlation heatmap. Please try again later.'
      setError(errorMessage)
      showToast(errorMessage, 'error')
    } finally {
      setLoading(false)
    }
  }

useEffect(() => {
  fetchCorrelation()
}, [])

useEffect(() => {
  return () => {
    if (correlationChart) {
      URL.revokeObjectURL(correlationChart)
    }
  }
}, [correlationChart])

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
            <Activity className="w-8 h-8 text-purple-500" />
            <h1 className="text-3xl font-bold text-gray-900">Lab Correlation</h1>
          </div>
          <p className="text-gray-600">
            Analysis of relationships between different laboratory parameters from your medical reports.
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <Loader className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" />
            <p className="text-gray-600">Generating correlation heatmap...</p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="bg-white rounded-xl shadow-md p-8">
            <div className="flex items-start gap-4">
              <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-red-800 mb-2">Unable to Load Correlation</h3>
                <p className="text-red-700">{error}</p>
                <p className="text-sm text-gray-600 mt-4">
                  Possible reasons:
                </p>
                <ul className="text-sm text-gray-600 list-disc list-inside mt-2 space-y-1">
                  <li>Insufficient medical reports with lab data</li>
                  <li>Reports are still being processed</li>
                  <li>Not enough parameters to calculate correlations</li>
                  <li>Server is temporarily unavailable</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Success State */}
        {!loading && correlationChart && (
          <ChartContainer
            title="Lab Parameter Correlation"
            onRefresh={fetchCorrelation}
            isLoading={false}
            error={null}
          >
            <img
              src={correlationChart}
              alt="Lab Parameter Correlation Heatmap"
              className="w-full rounded-lg border border-gray-200"
            />
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="font-semibold text-gray-900 mb-2">Understanding the Heatmap</h3>
              <p className="text-sm text-gray-600 mb-4">
                This heatmap shows correlations between different laboratory parameters:
              </p>
              <ul className="text-sm text-gray-600 space-y-2 list-disc list-inside">
                <li>
                  <strong>Colors:</strong> Red indicates positive correlation, blue indicates negative correlation
                </li>
                <li>
                  <strong>Intensity:</strong> Darker colors indicate stronger relationships
                </li>
                <li>
                  <strong>Interpretation:</strong> Strong correlations can highlight how changes in one parameter may relate to changes in another
                </li>
              </ul>
            </div>
          </ChartContainer>
        )}

        {/* Empty State */}
        {!loading && !error && !correlationChart && (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">No correlation data available yet</p>
            <p className="text-sm text-gray-500">
              Upload multiple medical reports with lab values to see parameter correlations.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
