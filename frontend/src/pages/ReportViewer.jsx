import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../utils/api'
import { ArrowLeft, Download } from 'lucide-react'

export default function ReportViewer() {
  const { id } = useParams()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [trendChart, setTrendChart] = useState(null)

  useEffect(() => {
    fetchReport()
  }, [id])

  const fetchReport = async () => {
    try {
      const response = await api.get(`/api/reports/${id}`)
      setReport(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching report:', error)
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    try {
      const response = await api.get(`/api/reports/${id}/download`, {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', report.file_name)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Error downloading report:', error)
      alert('Error downloading report. Please try again.')
    }
  }

  const loadTrendChart = async (parameterName) => {
    try {
      const response = await api.get(
        `/api/analytics/trend/${encodeURIComponent(parameterName)}`,
        { responseType: 'blob' }
      )
      const imageUrl = URL.createObjectURL(response.data)
      setTrendChart({ parameter: parameterName, url: imageUrl })
    } catch (error) {
      console.error('Error loading trend chart:', error)
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading report...</div>
  }

  if (!report) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Report not found</p>
        <Link to="/reports" className="text-blue-600 hover:underline mt-4 inline-block">
          Back to Reports
        </Link>
      </div>
    )
  }

  return (
    <div className="px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <Link
            to="/reports"
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{report.file_name}</h1>
            <p className="text-sm text-gray-500 mt-1">
              Uploaded on {new Date(report.upload_date).toLocaleDateString()}
            </p>
          </div>
        </div>
        <button
          onClick={handleDownload}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          <Download className="w-4 h-4 mr-2" />
          Download
        </button>
      </div>

      {/* AI Summary */}
      {report.ai_summary && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">AI Summary</h2>
          <p className="text-gray-700">{report.ai_summary}</p>
        </div>
      )}

      {/* Lab Values */}
      {report.lab_values && report.lab_values.length > 0 && (
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Lab Values</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Parameter
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Value
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reference Range
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {report.lab_values.map((lv) => (
                  <tr
                    key={lv.id}
                    className={lv.is_abnormal ? 'bg-red-50' : ''}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {lv.parameter_name}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-semibold ${
                      lv.is_abnormal ? 'text-red-600 bg-red-50' : 'text-green-600 bg-green-50'
                    }`}>
                      {lv.value} {lv.unit}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lv.reference_range}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded ${
                        lv.is_abnormal
                          ? 'bg-red-100 text-red-800'
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {lv.is_abnormal ? 'Abnormal' : 'Normal'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => loadTrendChart(lv.parameter_name)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        View Trend
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Trend Chart */}
      {trendChart && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Trend: {trendChart.parameter}
          </h2>
          <img src={trendChart.url} alt={`Trend for ${trendChart.parameter}`} className="w-full" />
        </div>
      )}

      {/* Extracted Text */}
      {report.extracted_text && (
        <div className="bg-white rounded-lg shadow p-6 mt-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Extracted Text</h2>
          <div className="bg-gray-50 rounded p-4 max-h-96 overflow-y-auto">
            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">
              {report.extracted_text}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}

