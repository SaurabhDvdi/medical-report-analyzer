import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../utils/api'
import {
  ArrowLeft,
  Loader,
  AlertCircle,
  TrendingUp,
  Activity,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  FileText,
  ChevronRight,
  Info,
  TrendingDown,
  Minus,
  Sliders
} from 'lucide-react'
import TrendChart from '../components/TrendChart'
import { useToast } from '../components/Toast'
import { safeFormatNumber } from '../utils/numeric'

export default function HealthSummaryPage() {
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [selectedParamName, setSelectedParamName] = useState(null)

  // Fetch health summary JSON
  const {
    data: summaryData,
    isLoading: loadingSummary,
    error: summaryError,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ['healthSummaryJson'],
    queryFn: () => api.get('/api/analytics/health-summary-json').then((res) => res.data),
    staleTime: 5 * 60 * 1000,
  })

  // Fetch per-parameter timeseries analytics
  const {
    data: trendsData,
    isLoading: loadingTrends,
    refetch: refetchTrends,
  } = useQuery({
    queryKey: ['healthTrendsJson'],
    queryFn: () => api.get('/api/analytics/health-trends-json').then((res) => res.data),
    staleTime: 5 * 60 * 1000,
  })

  const isLoading = loadingSummary || loadingTrends

  const handleRefresh = () => {
    refetchSummary()
    refetchTrends()
  }

  if (summaryError) {
    showToast('Error loading health insights: ' + (summaryError?.message || 'Unknown error'), 'error')
  }

  // Reports and Parameters
  const reports = summaryData?.reports || []
  const parameters = trendsData?.parameters || []
  const flatParams = summaryData?.parameters || []

  // Date metadata range
  const reportDates = reports
    .map((r) => r.date)
    .filter(Boolean)
  const earliestDate = reportDates.length > 0 ? reportDates[reportDates.length - 1] : null
  const latestDate = reportDates.length > 0 ? reportDates[0] : null

  // Parameters with history >= 2 reports
  const multiReportParams = parameters.filter(
    (p) => (p.analytics?.values || []).length >= 2
  )

  // Selected parameter for Trend Snapshot
  const currentSnapshotParam =
    parameters.find((p) => p.parameter === selectedParamName) ||
    multiReportParams[0] ||
    parameters[0]

  // Calculations for Needs Attention section
  const needsAttentionList = flatParams.filter((p) => p.is_abnormal)

  // Calculations for What Changed section (comparing latest vs previous report)
  const changedList = parameters
    .map((p) => {
      const vals = p.analytics?.values || []
      if (vals.length < 2) return null
      const latestObj = vals[vals.length - 1]
      const prevObj = vals[vals.length - 2]

      const latestVal = latestObj?.value
      const prevVal = prevObj?.value

      if (
        latestVal === null ||
        latestVal === undefined ||
        prevVal === null ||
        prevVal === undefined ||
        isNaN(latestVal) ||
        isNaN(prevVal)
      ) {
        return null
      }

      const diff = latestVal - prevVal
      const pct = prevVal !== 0 ? (Math.abs(diff) / Math.abs(prevVal)) * 100 : 0
      const direction = diff > 0.001 ? 'Increased' : diff < -0.001 ? 'Decreased' : 'Stable'

      return {
        parameter: p.parameter,
        unit: p.unit || '',
        latestVal,
        prevVal,
        diff,
        pct,
        direction,
        isAbnormal: p.risk?.risk_level === 'HIGH' || p.risk?.risk_level === 'MEDIUM',
      }
    })
    .filter(Boolean)
    .sort((a, b) => b.pct - a.pct)
    .slice(0, 5)

  // Calculations for Abnormality Patterns (Persistent vs Recent)
  const persistentAbnormalities = parameters.filter((p) => {
    const vals = p.analytics?.values || []
    if (vals.length < 2) return false
    // check if last 2 observations were abnormal
    const recent2 = vals.slice(-2)
    return recent2.every((v) => v.is_abnormal)
  })

  const recentAbnormalities = parameters.filter((p) => {
    const vals = p.analytics?.values || []
    if (vals.length === 0) return false
    const latest = vals[vals.length - 1]
    const isPersistent = persistentAbnormalities.some((pa) => pa.parameter === p.parameter)
    return latest.is_abnormal && !isPersistent
  })

  // Format Helper using strict numeric validation (safeFormatNumber)
  const formatVal = (val, dec = 2) => safeFormatNumber(val, dec, 'Unavailable')

  // Determine direction label for abnormal value using strict finite number validation
  const getAbnormalDirection = (refRange, val) => {
    if (!refRange || val === null || val === undefined || (typeof val === 'string' && val.trim() === '')) {
      return 'Outside reference range'
    }
    const num = Number(val)
    if (!Number.isFinite(num)) return 'Outside reference range'
    if (refRange.startsWith('<')) {
      const maxVal = parseFloat(refRange.replace('<', ''))
      if (Number.isFinite(maxVal) && num > maxVal) return 'Above reference range'
    } else if (refRange.startsWith('>')) {
      const minVal = parseFloat(refRange.replace('>', ''))
      if (Number.isFinite(minVal) && num < minVal) return 'Below reference range'
    } else if (refRange.includes('-') || refRange.includes('–')) {
      const parts = refRange.split(/[-–]/)
      const lo = parseFloat(parts[0])
      const hi = parseFloat(parts[1])
      if (Number.isFinite(lo) && num < lo) return 'Below reference range'
      if (Number.isFinite(hi) && num > hi) return 'Above reference range'
    }
    return 'Outside reference range'
  }

  // Empty state if no reports exist
  if (!isLoading && reports.length === 0) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto">
        <button
          onClick={() => navigate('/dashboard')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700 hover:text-teal-900"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </button>

        <div className="clinical-card p-12 text-center space-y-4">
          <Activity className="w-12 h-12 text-slate-300 mx-auto" />
          <div>
            <h3 className="font-bold text-slate-900 text-lg">No Health Data Available</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Upload PDF or image medical reports to generate structured clinical health insights and trajectory analytics.
            </p>
          </div>
          <button
            onClick={() => navigate('/reports')}
            className="clinical-button-primary text-xs inline-flex items-center gap-2"
          >
            <FileText className="w-4 h-4" /> Upload First Medical Report
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* 1. PAGE HEADER */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <button
            onClick={() => navigate('/dashboard')}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700 hover:text-teal-900 mb-2"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </button>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
            <TrendingUp className="w-7 h-7 text-teal-600" /> Health Insights & Clinical Summary
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Understand your current health picture, recent lab changes, and areas that may need clinical attention.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Metadata Badge */}
          {reports.length > 0 && (
            <div className="bg-slate-100 border border-slate-200 rounded-xl px-3.5 py-1.5 text-xs text-slate-700 font-medium flex items-center gap-2">
              <Calendar className="w-3.5 h-3.5 text-slate-500" />
              <span>
                <strong className="text-slate-900 font-bold">{reports.length}</strong> reports analyzed
                {earliestDate && latestDate ? ` (${earliestDate} – ${latestDate})` : ''}
              </span>
            </div>
          )}

          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="clinical-button-secondary text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh Data
          </button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="clinical-card p-12 text-center space-y-3">
          <Loader className="w-8 h-8 text-teal-600 animate-spin mx-auto" />
          <p className="text-xs font-medium text-slate-600">Synthesizing clinical health insights...</p>
        </div>
      )}

      {!isLoading && (
        <>
          {/* 2. HEALTH OVERVIEW */}
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-extrabold text-slate-900 tracking-tight">Health Overview</h2>
              <span className="text-[11px] font-medium text-slate-400">Current Health Picture</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {/* Overall Health Indicator */}
              <div className="clinical-card p-5 space-y-1.5 border-l-4 border-l-teal-600 bg-gradient-to-br from-teal-50/40 to-white">
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Health Indicator</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-extrabold text-teal-800">
                    {summaryData?.overall_score !== null && summaryData?.overall_score !== undefined
                      ? summaryData.overall_score
                      : 'N/A'}
                  </span>
                  <span className="text-xs font-semibold text-slate-400">/ 100</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-tight">Application-derived indicator</p>
              </div>

              {/* Reports Analyzed */}
              <div className="clinical-card p-5 space-y-1.5">
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Reports Analyzed</p>
                <p className="text-3xl font-extrabold text-slate-900">{reports.length}</p>
                <p className="text-[11px] text-slate-400 leading-tight">Uploaded OCR documents</p>
              </div>

              {/* Parameters Tracked */}
              <div className="clinical-card p-5 space-y-1.5">
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Parameters Tracked</p>
                <p className="text-3xl font-extrabold text-slate-900">{parameters.length}</p>
                <p className="text-[11px] text-slate-400 leading-tight">Unique lab biomarkers</p>
              </div>

              {/* Results within Reference Range */}
              <div className="clinical-card p-5 space-y-1.5">
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">In-Range Results</p>
                <p className="text-3xl font-extrabold text-emerald-600">
                  {flatParams.length > 0
                    ? `${Math.round((summaryData?.normal_count / flatParams.length) * 100)}%`
                    : '100%'}
                </p>
                <p className="text-[11px] text-emerald-700/80 font-medium">Within reference bounds</p>
              </div>

              {/* Parameters Needing Attention */}
              <div className="clinical-card p-5 space-y-1.5">
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Needing Attention</p>
                <p className="text-3xl font-extrabold text-rose-600">{needsAttentionList.length}</p>
                <p className="text-[11px] text-rose-600/80 font-medium">Out-of-range observations</p>
              </div>
            </div>
          </section>

          {/* 3. NEEDS ATTENTION (Prominent Clinical Section) */}
          <section className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-2">
              <div>
                <h2 className="text-lg font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-rose-600" /> Needs Attention
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Parameters currently outside their available reference ranges requiring clinical review.
                </p>
              </div>
              {needsAttentionList.length > 0 && (
                <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200">
                  {needsAttentionList.length} Flagged Item(s)
                </span>
              )}
            </div>

            {needsAttentionList.length === 0 ? (
              <div className="clinical-card p-6 text-center space-y-2 bg-emerald-50/40 border-emerald-200">
                <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
                <h3 className="font-bold text-slate-900 text-sm">All Observed Parameters Within Reference Bounds</h3>
                <p className="text-xs text-slate-600 max-w-md mx-auto">
                  No biomarkers in your recent lab reports are flagged outside standard clinical reference ranges.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {needsAttentionList.map((item, idx) => {
                  const abnormalStatusText = getAbnormalDirection(item.ref_range, item.value)
                  return (
                    <div
                      key={idx}
                      className="clinical-card p-5 border-l-4 border-l-rose-600 space-y-3 flex flex-col justify-between hover:shadow-md transition-shadow"
                    >
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <h3 className="font-bold text-slate-900 text-base">{item.name}</h3>
                          <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
                            {abnormalStatusText}
                          </span>
                        </div>

                        <div className="bg-slate-50 rounded-xl p-3 space-y-1.5 border border-slate-200">
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-500 font-medium">Measured Value:</span>
                            <span className="font-extrabold text-rose-700 text-sm">
                              {formatVal(item.value)} {item.unit || ''}
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-500 font-medium">Reference Range:</span>
                            <span className="font-semibold text-slate-800">{item.ref_range || 'Not specified'}</span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-500 font-medium">Source Report:</span>
                            <span className="font-medium text-slate-600 truncate max-w-[140px]">{item.report_name}</span>
                          </div>
                        </div>
                      </div>

                      <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                        <span className="text-slate-400 text-[11px]">Observational finding</span>
                        <button
                          onClick={() => {
                            setSelectedParamName(item.name)
                            const el = document.getElementById('trend-snapshot-section')
                            if (el) el.scrollIntoView({ behavior: 'smooth' })
                          }}
                          className="font-bold text-teal-700 hover:text-teal-900 inline-flex items-center gap-1"
                        >
                          View Trend <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </section>

          {/* 4. WHAT CHANGED */}
          <section className="space-y-4">
            <div className="border-b border-slate-200 pb-2">
              <h2 className="text-lg font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                <Activity className="w-5 h-5 text-teal-600" /> What Changed
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Biomarker shifts between your latest report and the previous available report.
              </p>
            </div>

            {changedList.length === 0 ? (
              <div className="clinical-card p-6 text-center text-xs text-slate-500 space-y-1">
                <p className="font-semibold text-slate-700">Insufficient Report History for Comparison</p>
                <p>Upload at least 2 medical reports over time to observe parameter shift deltas.</p>
              </div>
            ) : (
              <div className="clinical-card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-700">
                    <thead className="bg-slate-100/80 text-slate-900 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="p-3.5">Parameter</th>
                        <th className="p-3.5">Previous Value</th>
                        <th className="p-3.5">Latest Value</th>
                        <th className="p-3.5">Absolute Shift ($\Delta$)</th>
                        <th className="p-3.5">Percentage Shift</th>
                        <th className="p-3.5">Direction</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {changedList.map((row) => (
                        <tr key={row.parameter} className="hover:bg-slate-50/80 transition-colors">
                          <td className="p-3.5 font-bold text-slate-900">{row.parameter}</td>
                          <td className="p-3.5 text-slate-600">
                            {formatVal(row.prevVal)} {row.unit}
                          </td>
                          <td className="p-3.5 font-extrabold text-slate-900">
                            {formatVal(row.latestVal)} {row.unit}
                          </td>
                          <td className="p-3.5 font-semibold text-slate-800">
                            {row.diff > 0 ? `+${formatVal(row.diff)}` : formatVal(row.diff)} {row.unit}
                          </td>
                          <td className="p-3.5 font-bold text-slate-900">
                            {formatVal(row.pct, 1)}%
                          </td>
                          <td className="p-3.5">
                            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                              row.direction === 'Increased'
                                ? 'bg-amber-100 text-amber-800'
                                : row.direction === 'Decreased'
                                ? 'bg-indigo-100 text-indigo-800'
                                : 'bg-slate-100 text-slate-700'
                            }`}>
                              {row.direction === 'Increased' && <TrendingUp className="w-3 h-3 text-amber-700" />}
                              {row.direction === 'Decreased' && <TrendingDown className="w-3 h-3 text-indigo-700" />}
                              {row.direction === 'Stable' && <Minus className="w-3 h-3 text-slate-500" />}
                              <span>{row.direction}</span>
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </section>

          {/* 5. HEALTH TREND SNAPSHOT */}
          <section id="trend-snapshot-section" className="space-y-4 scroll-mt-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-2">
              <div>
                <h2 className="text-lg font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                  <Sliders className="w-5 h-5 text-teal-600" /> Health Trend Snapshot
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Interactive time-series preview for individual laboratory biomarkers.
                </p>
              </div>

              <Link
                to="/analytics/trends"
                className="clinical-button-secondary text-xs inline-flex items-center gap-1.5"
              >
                <span>View Full Health Trends</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {currentSnapshotParam ? (
              <div className="clinical-card p-6 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <label className="text-xs font-bold text-slate-700">Select Biomarker:</label>
                    <select
                      value={currentSnapshotParam.parameter}
                      onChange={(e) => setSelectedParamName(e.target.value)}
                      className="bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                    >
                      {parameters.map((p) => (
                        <option key={p.parameter} value={p.parameter}>
                          {p.parameter}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Summary Metric Stats */}
                  <div className="flex items-center gap-4 text-xs">
                    <div>
                      <span className="text-slate-400 text-[11px] block font-semibold">Latest</span>
                      <span className="font-extrabold text-slate-900">
                        {formatVal(
                          (currentSnapshotParam.analytics?.values || []).slice(-1)[0]?.value
                        )}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[11px] block font-semibold">Previous</span>
                      <span className="font-semibold text-slate-700">
                        {formatVal(
                          (currentSnapshotParam.analytics?.values || []).slice(-2)[0]?.value
                        )}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[11px] block font-semibold">Trend</span>
                      <span className="font-bold text-teal-700">
                        {currentSnapshotParam.analytics?.trend || 'Stable'}
                      </span>
                    </div>
                  </div>
                </div>

                <TrendChart
                  data={currentSnapshotParam.analytics?.values || []}
                  parameter={currentSnapshotParam.parameter}
                  unit={currentSnapshotParam.unit || ''}
                  height={260}
                />
              </div>
            ) : (
              <div className="clinical-card p-6 text-center text-xs text-slate-500">
                No parameter data available for trend preview.
              </div>
            )}
          </section>

          {/* 6. ABNORMALITY PATTERNS */}
          <section className="space-y-4">
            <div className="border-b border-slate-200 pb-2">
              <h2 className="text-lg font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-amber-600" /> Abnormality Patterns
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Evaluation of persistent vs recent out-of-range observation trajectories.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Persistent Abnormalities */}
              <div className="clinical-card p-5 space-y-3 border-l-4 border-l-rose-600">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-rose-600" /> Persistent Abnormalities
                  </h3>
                  <span className="text-[11px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded">
                    $\ge 2$ Consecutive Reports
                  </span>
                </div>

                {persistentAbnormalities.length === 0 ? (
                  <p className="text-xs text-slate-500 italic py-2">
                    {reports.length < 2
                      ? 'Insufficient history to determine persistence across multiple reports.'
                      : 'No persistent abnormal biomarker patterns detected.'}
                  </p>
                ) : (
                  <div className="space-y-2">
                    {persistentAbnormalities.map((pa) => {
                      const count = pa.analytics?.values?.filter((v) => v.is_abnormal).length || 2
                      return (
                        <div
                          key={pa.parameter}
                          className="bg-rose-50/60 border border-rose-200 rounded-xl p-3 space-y-1 text-xs"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-slate-900">{pa.parameter}</span>
                            <span className="font-extrabold text-rose-800">Persistent Shift</span>
                          </div>
                          <p className="text-[11px] text-rose-700/90 font-medium">
                            Outside reference range in {count} consecutive reports
                          </p>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>

              {/* Recent Abnormalities */}
              <div className="clinical-card p-5 space-y-3 border-l-4 border-l-amber-500">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                    <Info className="w-4 h-4 text-amber-600" /> Recent Abnormalities
                  </h3>
                  <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">
                    Latest Report Only
                  </span>
                </div>

                {recentAbnormalities.length === 0 ? (
                  <p className="text-xs text-slate-500 italic py-2">
                    No newly isolated abnormal biomarkers in latest report.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {recentAbnormalities.map((ra) => (
                      <div
                        key={ra.parameter}
                        className="bg-amber-50/60 border border-amber-200 rounded-xl p-3 space-y-1 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-900">{ra.parameter}</span>
                          <span className="font-extrabold text-amber-800">Isolated Flag</span>
                        </div>
                        <p className="text-[11px] text-amber-800/90 font-medium">
                          Recently observed outside reference range in latest lab report
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </section>

          {/* 7. DATA COVERAGE & METHODOLOGY */}
          <section className="clinical-card p-6 space-y-4 bg-slate-50/70 border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <Info className="w-4 h-4 text-teal-600" /> Data Coverage & Indicator Methodology
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-slate-600 leading-relaxed">
              <div className="space-y-2">
                <h4 className="font-bold text-slate-800">Longitudinal Data Coverage</h4>
                <p>
                  A total of <strong className="text-slate-900 font-bold">{reports.length} reports</strong> and{' '}
                  <strong className="text-slate-900 font-bold">{parameters.length} unique biomarkers</strong> are currently indexed in your profile.
                </p>
                <p>
                  <strong className="text-slate-900 font-bold">{multiReportParams.length} biomarkers</strong> have observations across multiple report dates, enabling trend curve evaluation. Single-observation biomarkers require additional report uploads for trend calculation.
                </p>
              </div>

              <div className="space-y-2 border-t md:border-t-0 md:border-l border-slate-200 pt-3 md:pt-0 md:pl-6">
                <h4 className="font-bold text-slate-800">Health Indicator Score Definition</h4>
                <p>
                  The <strong className="text-slate-900 font-bold">Overall Health Indicator (0–100)</strong> is an application-derived metric. It evaluates quantitative lab values against standard clinical reference range midpoints.
                </p>
                <p className="text-[11px] text-slate-500 italic">
                  Note: This indicator is designed exclusively for personal wellness and trajectory tracking. It does not constitute a medical diagnosis or formal clinical evaluation.
                </p>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
