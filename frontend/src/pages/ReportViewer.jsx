import { useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../utils/api'
import {
  ArrowLeft,
  Download,
  FileDown,
  Loader,
  BarChart2,
  Brain,
  FileText,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  Filter,
  Calendar,
  ChevronDown,
  ChevronUp,
  FlaskConical,
  Activity
} from 'lucide-react'
import { downloadLabValuesCsv } from './Reports'
import { TableSkeleton } from '../components/Skeletons'
import { safeFormatNumber } from '../utils/numeric'

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
  const [showRawOcr, setShowRawOcr] = useState(false)

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

  const labValues = useMemo(() => report?.lab_values || [], [report])
  const totalParameters = labValues.length
  const normalCount = useMemo(
    () =>
      labValues.filter(
        (lv) => !lv.is_abnormal || (lv.status && lv.status.toLowerCase() === 'normal')
      ).length,
    [labValues]
  )
  const attentionCount = useMemo(
    () =>
      labValues.filter(
        (lv) => lv.is_abnormal || (lv.status && lv.status.toLowerCase() !== 'normal')
      ).length,
    [labValues]
  )

  const renderStatusBadge = (status, isAbnormal) => {
    const st = (status || (isAbnormal ? 'Abnormal' : 'Normal')).toLowerCase()
    if (st === 'normal') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Normal
        </span>
      )
    }
    if (st === 'high') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
          <AlertTriangle className="w-3 h-3 text-amber-600" /> High
        </span>
      )
    }
    if (st === 'low') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
          <AlertTriangle className="w-3 h-3 text-amber-600" /> Low
        </span>
      )
    }
    if (st === 'critical') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-200">
          <AlertTriangle className="w-3 h-3 text-rose-600" /> Critical
        </span>
      )
    }
    if (st === 'abnormal') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-200">
          <AlertTriangle className="w-3 h-3 text-rose-600" /> Abnormal
        </span>
      )
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
        Unavailable
      </span>
    )
  }

  const formatLabValue = (val) => {
    if (val === null || val === undefined || val === '') return '—'
    if (typeof val === 'string' && isNaN(Number(val))) {
      return val
    }
    return safeFormatNumber(val, 'auto')
  }

  const parameterNames = useMemo(
    () => [...new Set(labValues.map((lv) => lv.parameter_name))],
    [labValues]
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
    return <TableSkeleton rows={8} />
  }

  if (!report) {
    return (
      <div className="p-12 text-center space-y-4">
        {loadError ? (
          <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl inline-block max-w-md">
            {loadError}
          </div>
        ) : (
          <p className="text-sm font-medium text-slate-600">Report details not found.</p>
        )}
        <div>
          <Link to="/reports" className="clinical-button-secondary text-xs">
            ← Back to Reports List
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Top Action & Navigation Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div className="flex items-center gap-3.5">
          <Link
            to="/reports"
            className="p-2 bg-white hover:bg-slate-100 border border-slate-200 text-slate-600 rounded-xl transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
                {report.file_name}
              </h1>
              <span
                className={
                  report.ocr_status === 'completed'
                    ? 'clinical-badge-normal'
                    : 'clinical-badge-high'
                }
              >
                {report.ocr_status}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Uploaded on {new Date(report.upload_date).toLocaleDateString()} · Category:{' '}
              <span className="font-semibold text-slate-700">{report.category || 'Uncategorized'}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleExportCsv}
            disabled={exporting}
            className="clinical-button-secondary text-xs"
          >
            {exporting ? (
              <Loader className="w-3.5 h-3.5 mr-2 animate-spin" />
            ) : (
              <FileDown className="w-3.5 h-3.5 mr-2 text-slate-500" />
            )}
            Export CSV
          </button>
          <button
            type="button"
            onClick={handleDownload}
            className="clinical-button-primary text-xs"
          >
            <Download className="w-3.5 h-3.5 mr-2" />
            Download Source
          </button>
        </div>
      </div>

      {downloadError && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{downloadError}</span>
        </div>
      )}

      {/* AI Summary Banner */}
      {report.ai_summary && (
        <div className="bg-gradient-to-r from-teal-900 to-slate-900 text-white rounded-2xl p-5 sm:p-6 shadow-md border border-teal-800/60 space-y-2">
          <div className="flex items-center gap-2 text-teal-300 font-bold text-xs uppercase tracking-wider">
            <Brain className="w-4 h-4 text-teal-400" /> AI Clinical Intelligence Summary
          </div>
          <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-sans">
            {report.ai_summary}
          </p>
        </div>
      )}

      {/* Extracted Medical Values (Primary Section) */}
      <div className="clinical-card overflow-hidden space-y-4 p-5 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <FlaskConical className="w-5 h-5 text-teal-600" />
              <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 tracking-tight">
                Extracted Medical Values
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Structured laboratory results extracted from this report.
            </p>
          </div>

          {/* Dynamic Summary Statistics */}
          {labValues.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 text-xs font-semibold">
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                <Activity className="w-3.5 h-3.5 text-slate-500" />
                {totalParameters} {totalParameters === 1 ? 'Parameter' : 'Parameters'}
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                {normalCount} Normal
              </span>
              {attentionCount > 0 && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  {attentionCount} Need Attention
                </span>
              )}
            </div>
          )}
        </div>

        {labValues.length === 0 ? (
          <div className="p-8 text-center bg-slate-50/60 rounded-xl border border-dashed border-slate-200 space-y-1.5">
            <p className="text-sm font-semibold text-slate-700">
              No structured medical values were extracted from this report.
            </p>
            <p className="text-xs text-slate-500">
              The raw extracted text is available below for review.
            </p>
          </div>
        ) : (
          <>
            {/* Desktop Table View (sm and above) */}
            <div className="hidden sm:block overflow-x-auto border border-slate-100 rounded-xl">
              <table className="min-w-full divide-y divide-slate-100 text-left">
                <thead className="bg-slate-50 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3">Test / Parameter</th>
                    <th className="px-5 py-3">Result</th>
                    <th className="px-5 py-3">Unit</th>
                    <th className="px-5 py-3">Reference Range</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3 text-right">Trend Analytics</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {labValues.map((lv) => (
                    <tr
                      key={lv.id}
                      className={`transition-colors ${
                        lv.is_abnormal ? 'bg-amber-50/30 hover:bg-amber-50/50' : 'hover:bg-slate-50/80'
                      }`}
                    >
                      <td className="px-5 py-3.5 font-bold text-slate-900">
                        {lv.parameter_name}
                      </td>
                      <td className="px-5 py-3.5 font-black text-sm text-slate-900">
                        {formatLabValue(lv.value)}
                      </td>
                      <td className="px-5 py-3.5 text-slate-500 font-medium">
                        {lv.unit || '—'}
                      </td>
                      <td className="px-5 py-3.5 text-slate-600 font-medium">
                        {lv.reference_range ? lv.reference_range.replace('-', '–') : 'Not provided'}
                      </td>
                      <td className="px-5 py-3.5">
                        {renderStatusBadge(lv.status, lv.is_abnormal)}
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button
                          type="button"
                          onClick={() => loadTrendChart(lv.parameter_name)}
                          disabled={trendLoading === lv.parameter_name}
                          className="text-xs font-semibold text-teal-700 hover:text-teal-900 inline-flex items-center gap-1 disabled:opacity-50"
                        >
                          {trendLoading === lv.parameter_name ? (
                            <Loader className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <TrendingUp className="w-3.5 h-3.5" />
                          )}
                          View Trend
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Stacked Cards View (< sm / 390px) */}
            <div className="grid grid-cols-1 gap-3 sm:hidden">
              {labValues.map((lv) => (
                <div
                  key={lv.id}
                  className={`p-4 rounded-xl border transition-all ${
                    lv.is_abnormal
                      ? 'bg-amber-50/20 border-amber-200'
                      : 'bg-white border-slate-200 shadow-2xs'
                  } space-y-2.5`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-0.5">
                      <h4 className="font-bold text-slate-900 text-sm leading-tight break-words">
                        {lv.parameter_name}
                      </h4>
                      <p className="text-lg font-black text-slate-900 tracking-tight">
                        {formatLabValue(lv.value)}{' '}
                        <span className="text-xs font-semibold text-slate-500">{lv.unit || ''}</span>
                      </p>
                    </div>
                    {renderStatusBadge(lv.status, lv.is_abnormal)}
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
                    <span className="truncate mr-2">
                      Ref:{' '}
                      <span className="font-medium text-slate-700">
                        {lv.reference_range ? lv.reference_range.replace('-', '–') : 'Not provided'}
                      </span>
                    </span>
                    <button
                      type="button"
                      onClick={() => loadTrendChart(lv.parameter_name)}
                      disabled={trendLoading === lv.parameter_name}
                      className="font-semibold text-teal-700 hover:text-teal-900 inline-flex items-center gap-1 shrink-0"
                    >
                      <TrendingUp className="w-3.5 h-3.5" /> Trend
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Raw Extracted OCR Text (Collapsible/Verbatim) */}
      {report.extracted_text && (
        <div className="clinical-card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Raw Extracted OCR Text</h3>
              <p className="text-xs text-slate-500 mt-0.5">Verbatim extracted text preserved from original document.</p>
            </div>
            <button
              type="button"
              onClick={() => setShowRawOcr((prev) => !prev)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
            >
              {showRawOcr ? (
                <>
                  <ChevronUp className="w-3.5 h-3.5 text-slate-500" />
                  Hide raw OCR text
                </>
              ) : (
                <>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
                  Show raw OCR text
                </>
              )}
            </button>
          </div>

          {showRawOcr && (
            <div className="bg-slate-900 text-slate-200 p-4 rounded-xl max-h-72 overflow-y-auto text-xs font-mono leading-relaxed transition-all">
              <pre className="whitespace-pre-wrap font-mono">{report.extracted_text}</pre>
            </div>
          )}
        </div>
      )}

      {/* Parameter Comparison Matrix */}
      {parameterNames.length >= 2 && (
        <div className="clinical-card p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <BarChart2 className="w-5 h-5 text-indigo-600" />
              <h3 className="font-bold text-slate-900 text-sm sm:text-base">Compare Report Parameters</h3>
            </div>
            <span className="text-xs text-slate-500 font-medium">Multi-Biomarker Matrix</span>
          </div>

          <p className="text-xs text-slate-500 leading-relaxed">
            Select two or more parameters from this report to generate a side-by-side analytical chart.
          </p>

          <div className="flex flex-wrap gap-2">
            {parameterNames.map((name) => {
              const isChecked = comparisonSelection.has(name)
              return (
                <button
                  key={name}
                  type="button"
                  onClick={() => toggleComparisonParam(name)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                    isChecked
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs'
                      : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  {isChecked ? '✓ ' : '+ '}
                  {name}
                </button>
              )
            })}
          </div>

          <div className="pt-2 flex items-center gap-3">
            <button
              type="button"
              onClick={loadComparisonChart}
              disabled={comparisonLoading}
              className="clinical-button-primary bg-indigo-600 hover:bg-indigo-700 text-xs"
            >
              {comparisonLoading && <Loader className="w-3.5 h-3.5 mr-2 animate-spin" />}
              Generate Comparison Chart
            </button>
          </div>

          {comparisonError && <p className="text-xs font-medium text-rose-600">{comparisonError}</p>}

          {comparisonUrl && (
            <div className="pt-3 border-t border-slate-100">
              <img
                src={comparisonUrl}
                alt="Parameter comparison chart"
                className="w-full max-w-4xl rounded-xl border border-slate-200 shadow-sm"
              />
            </div>
          )}
        </div>
      )}

      {trendError && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl">
          {trendError}
        </div>
      )}

      {/* Trend Chart Image Overlay */}
      {trendChart && (
        <div className="clinical-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-teal-600" /> Longitudinal Trend: {trendChart.parameter}
            </h3>
            <button
              onClick={() => setTrendChart(null)}
              className="text-xs font-semibold text-slate-500 hover:text-slate-900"
            >
              Close Chart
            </button>
          </div>
          <img
            src={trendChart.url}
            alt={`Trend for ${trendChart.parameter}`}
            className="w-full max-w-4xl rounded-xl border border-slate-200 shadow-sm"
          />
        </div>
      )}

      {/* Filtered Lab History Query */}
      <div className="clinical-card p-5 space-y-4">
        <div className="border-b border-slate-100 pb-3">
          <h3 className="font-bold text-slate-900 text-sm sm:text-base">Lab History & Date Filtering</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Query your historical lab values across all reports.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
          <div>
            <label className="block text-[11px] font-semibold text-slate-600 mb-1">Parameter</label>
            <select
              className="clinical-input text-xs"
              value={filterParam}
              onChange={(e) => setFilterParam(e.target.value)}
            >
              <option value="">All Parameters</option>
              {parameterNames.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-600 mb-1">Start Date</label>
            <input
              type="date"
              className="clinical-input text-xs"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-600 mb-1">End Date</label>
            <input
              type="date"
              className="clinical-input text-xs"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>

          <button
            type="button"
            onClick={applyLabFilters}
            disabled={filteredLoading}
            className="clinical-button-primary text-xs"
          >
            {filteredLoading ? <Loader className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Filter className="w-3.5 h-3.5 mr-1" />}
            Apply Filters
          </button>
        </div>

        {filteredError && <p className="text-xs text-rose-600 font-medium">{filteredError}</p>}

        {filteredLabs.length > 0 && (
          <div className="overflow-x-auto border border-slate-200 rounded-xl">
            <table className="min-w-full divide-y divide-slate-100 text-left text-xs">
              <thead className="bg-slate-50 font-semibold text-slate-500 uppercase">
                <tr>
                  <th className="px-4 py-2.5">Parameter</th>
                  <th className="px-4 py-2.5">Value</th>
                  <th className="px-4 py-2.5">Report Date</th>
                  <th className="px-4 py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredLabs.map((lv) => (
                  <tr key={lv.id} className={lv.is_abnormal ? 'bg-rose-50/70' : 'hover:bg-slate-50'}>
                    <td className="px-4 py-2.5 font-bold text-slate-900">{lv.parameter_name}</td>
                    <td className="px-4 py-2.5 font-semibold text-slate-800">
                      {lv.value} {lv.unit}
                    </td>
                    <td className="px-4 py-2.5 text-slate-500">
                      {lv.report_date ? new Date(lv.report_date).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={lv.is_abnormal ? 'clinical-badge-high' : 'clinical-badge-normal'}>
                        {lv.is_abnormal ? 'Abnormal' : 'Normal'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
