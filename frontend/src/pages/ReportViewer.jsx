import { useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../utils/api'
import { ArrowLeft, Download, FileDown, Loader, BarChart2 } from 'lucide-react'
import { downloadLabValuesCsv } from './Reports'

export default function ReportViewer() {
  const { id } = useParams()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [trendChart, setTrendChart] = useState(null)
  const [trendLoading, setTrendLoading] = useState(null)
  const [trendError, setTrendError] = useState('')
  const [downloadError, setDownloadError] = useState('')
  const [exporting, setExporting] = useState(false)

  const [filterParam, setFilterParam] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [filteredLabs, setFilteredLabs] = useState([])
  const [filteredLoading, setFilteredLoading] = useState(false)
  const [filteredError, setFilteredError] = useState('')

  const [comparisonSelection, setComparisonSelection] = useState(new Set())
  const [comparisonUrl, setComparisonUrl] = useState(null)
  const [comparisonLoading, setComparisonLoading] = useState(false)
  const [comparisonError, setComparisonError] = useState('')

  const fetchReport = useCallback(async () => {
    setLoadError('')
    try {
      const response = await api.get(`/api/reports/${id}`)
      setReport(response.data)
    } catch (error) {
      console.error('Error fetching report:', error)
      setLoadError(
        error.response?.data?.detail || error.message || 'Failed to load report.'
      )
      setReport(null)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    setLoading(true)
    fetchReport()
  }, [fetchReport])

  useEffect(() => {
    return () => {
      if (trendChart?.url) URL.revokeObjectURL(trendChart.url)
      if (comparisonUrl) URL.revokeObjectURL(comparisonUrl)
    }
  }, [trendChart, comparisonUrl])

  const parameterNames = useMemo(
    () => [...new Set((report?.lab_values || []).map((lv) => lv.parameter_name))],
    [report]
  )

  const toggleComparisonParam = (name) => {
    setComparisonSelection((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  const loadComparisonChart = async () => {
    const names = [...comparisonSelection]
    if (names.length < 2) {
      setComparisonError('Select at least two parameters to compare.')
      return
    }
    setComparisonError('')
    setComparisonLoading(true)
    if (comparisonUrl) {
      URL.revokeObjectURL(comparisonUrl)
      setComparisonUrl(null)
    }
    try {
      const response = await api.get('/api/analytics/comparison', {
        params: { parameter_names: names.join(',') },
        responseType: 'blob',
      })
      const blob =
        response.data instanceof Blob
          ? response.data
          : new Blob([response.data], { type: 'image/png' })
      setComparisonUrl(URL.createObjectURL(blob))
    } catch (error) {
      console.error('Comparison chart error:', error)
      setComparisonError(
        error.response?.data?.detail || 'Could not load comparison chart.'
      )
    } finally {
      setComparisonLoading(false)
    }
  }

  const applyLabFilters = async () => {
    setFilteredError('')
    setFilteredLoading(true)
    try {
      const params = {}
      if (filterParam) params.parameter_name = filterParam
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate
      const response = await api.get('/api/lab-values', { params })
      setFilteredLabs(response.data)
    } catch (error) {
      console.error('Lab values filter error:', error)
      setFilteredError(
        error.response?.data?.detail || 'Could not load filtered lab values.'
      )
      setFilteredLabs([])
    } finally {
      setFilteredLoading(false)
    }
  }

  const handleDownload = async () => {
    setDownloadError('')
    try {
      const response = await api.get(`/api/reports/${id}/download`, {
        responseType: 'blob',
      })
      const blob =
        response.data instanceof Blob
          ? response.data
          : new Blob([response.data])
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = report.file_name
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error downloading report:', error)
      setDownloadError(
        error.response?.data?.detail || 'Error downloading report. Please try again.'
      )
    }
  }

  const loadTrendChart = async (parameterName) => {
    setTrendError('')
    setTrendLoading(parameterName)
    if (trendChart?.url) {
      URL.revokeObjectURL(trendChart.url)
    }
    try {
      const response = await api.get(
        `/api/analytics/trend/${encodeURIComponent(parameterName)}`,
        { responseType: 'blob' }
      )
      const blob =
        response.data instanceof Blob
          ? response.data
          : new Blob([response.data], { type: 'image/png' })
      const imageUrl = URL.createObjectURL(blob)
      setTrendChart({ parameter: parameterName, url: imageUrl })
    } catch (error) {
      console.error('Error loading trend chart:', error)
      setTrendChart(null)
      setTrendError(
        error.response?.data?.detail || 'Could not load trend chart for this parameter.'
      )
    } finally {
      setTrendLoading(null)
    }
  }

  const handleExportCsv = async () => {
    setExporting(true)
    try {
      await downloadLabValuesCsv()
    } catch (error) {
      console.error('CSV export failed:', error)
      alert(
        error.response?.data?.detail || 'Could not export CSV. Please try again.'
      )
    } finally {
      setExporting(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading report...</div>
  }

  if (!report) {
    return (
      <div className="text-center py-12 px-4">
        {loadError && (
          <p className="text-red-600 mb-4 bg-red-50 border border-red-200 rounded-md px-4 py-3 inline-block">
            {loadError}
          </p>
        )}
        {!loadError && <p className="text-gray-500">Report not found</p>}
        <Link to="/reports" className="text-blue-600 hover:underline mt-4 inline-block">
          Back to Reports
        </Link>
      </div>
    )
  }

  return (
    <div className="px-4 py-6">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
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
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleExportCsv}
            disabled={exporting}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            {exporting ? (
              <Loader className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <FileDown className="w-4 h-4 mr-2" />
            )}
            Export CSV
          </button>
          <button
            type="button"
            onClick={handleDownload}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <Download className="w-4 h-4 mr-2" />
            Download
          </button>
        </div>
      </div>
      {downloadError && (
        <div className="mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-4 py-3">
          {downloadError}
        </div>
      )}

      {/* AI Summary */}
      {report.ai_summary && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">AI Summary</h2>
          <p className="text-gray-700">{report.ai_summary}</p>
        </div>
      )}

      {/* Compare parameters (this report) */}
      {parameterNames.length >= 2 && (
        <div className="bg-white rounded-lg shadow mb-6 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-2 flex items-center gap-2">
            <BarChart2 className="w-5 h-5" />
            Compare parameters
          </h2>
          <p className="text-sm text-gray-600 mb-3">
            Select two or more parameters from this report, then load the comparison chart.
          </p>
          <div className="flex flex-wrap gap-2 mb-4">
            {parameterNames.map((name) => (
              <label
                key={name}
                className="inline-flex items-center gap-2 text-sm border rounded-md px-3 py-1 cursor-pointer hover:bg-gray-50"
              >
                <input
                  type="checkbox"
                  checked={comparisonSelection.has(name)}
                  onChange={() => toggleComparisonParam(name)}
                />
                {name}
              </label>
            ))}
          </div>
          <button
            type="button"
            onClick={loadComparisonChart}
            disabled={comparisonLoading}
            className="inline-flex items-center px-4 py-2 rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-sm"
          >
            {comparisonLoading && <Loader className="w-4 h-4 mr-2 animate-spin" />}
            Show comparison chart
          </button>
          {comparisonError && (
            <p className="mt-2 text-sm text-red-700">{comparisonError}</p>
          )}
          {comparisonUrl && (
            <div className="mt-4">
              <img src={comparisonUrl} alt="Parameter comparison" className="w-full max-w-4xl rounded border" />
            </div>
          )}
        </div>
      )}

      {/* Lab Values (this report) */}
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
                    className={
                      lv.is_abnormal ? 'bg-red-50 text-red-700' : ''
                    }
                  >
                    <td
                      className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                        lv.is_abnormal ? 'text-red-700' : 'text-gray-900'
                      }`}
                    >
                      {lv.parameter_name}
                    </td>
                    <td
                      className={`px-6 py-4 whitespace-nowrap text-sm font-semibold ${
                        lv.is_abnormal ? 'text-red-700' : 'text-green-700'
                      }`}
                    >
                      {lv.value} {lv.unit}
                    </td>
                    <td
                      className={`px-6 py-4 whitespace-nowrap text-sm ${
                        lv.is_abnormal ? 'text-red-600' : 'text-gray-500'
                      }`}
                    >
                      {lv.reference_range}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs rounded ${
                          lv.is_abnormal
                            ? 'bg-red-100 text-red-800'
                            : 'bg-green-100 text-green-800'
                        }`}
                      >
                        {lv.is_abnormal ? 'Abnormal' : 'Normal'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        type="button"
                        onClick={() => loadTrendChart(lv.parameter_name)}
                        disabled={trendLoading === lv.parameter_name}
                        className="text-blue-600 hover:text-blue-800 disabled:opacity-50 inline-flex items-center gap-1"
                      >
                        {trendLoading === lv.parameter_name && (
                          <Loader className="w-3 h-3 animate-spin" />
                        )}
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

      {trendError && (
        <div className="mb-6 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-4 py-3">
          {trendError}
        </div>
      )}

      {/* Trend Chart */}
      {trendChart && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Trend: {trendChart.parameter}
          </h2>
          <img src={trendChart.url} alt={`Trend for ${trendChart.parameter}`} className="w-full" />
        </div>
      )}

      {/* Filtered lab values (GET /api/lab-values) */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Lab history & filters</h2>
          <p className="text-sm text-gray-500 mt-1">
            Query all of your lab values with optional filters (same data as the API).
          </p>
        </div>
        <div className="p-6 space-y-4">
          <div className="flex flex-wrap gap-4 items-end">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Parameter</label>
              <select
                className="border border-gray-300 rounded-md px-3 py-2 text-sm min-w-[180px]"
                value={filterParam}
                onChange={(e) => setFilterParam(e.target.value)}
              >
                <option value="">All parameters</option>
                {parameterNames.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Start date</label>
              <input
                type="date"
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">End date</label>
              <input
                type="date"
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
            <button
              type="button"
              onClick={applyLabFilters}
              disabled={filteredLoading}
              className="px-4 py-2 rounded-md bg-gray-800 text-white text-sm hover:bg-gray-900 disabled:opacity-50"
            >
              {filteredLoading ? 'Loading…' : 'Apply filters'}
            </button>
          </div>
          {filteredError && (
            <p className="text-sm text-red-700">{filteredError}</p>
          )}
          {filteredLabs.length > 0 && (
            <div className="overflow-x-auto border rounded-md">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Parameter
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Value
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Report date
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredLabs.map((lv) => (
                    <tr
                      key={lv.id}
                      className={lv.is_abnormal ? 'bg-red-50 text-red-700' : ''}
                    >
                      <td className="px-4 py-2 text-sm">{lv.parameter_name}</td>
                      <td className="px-4 py-2 text-sm font-medium">
                        {lv.value} {lv.unit}
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-600">
                        {lv.report_date
                          ? new Date(lv.report_date).toLocaleDateString()
                          : '—'}
                      </td>
                      <td className="px-4 py-2 text-sm">
                        {lv.is_abnormal ? 'Abnormal' : 'Normal'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

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
