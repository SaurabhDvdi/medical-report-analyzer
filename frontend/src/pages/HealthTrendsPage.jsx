import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../utils/api'
import { ArrowLeft, Loader, AlertCircle, TrendingUp, TrendingDown, Minus, RefreshCw, Activity, Search } from 'lucide-react'
import TrendChart from '../components/TrendChart'
import { useToast } from '../components/Toast'
import { safeFormatNumber } from '../utils/numeric'

export default function HealthTrendsPage() {
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedParameter, setSelectedParameter] = useState(null)

  // Fetch health summary JSON for parameter scores and parameters list
  const {
    data: summaryData,
    isLoading: loadingSummary,
    error: summaryError,
    refetch,
  } = useQuery({
    queryKey: ['healthSummaryJson'],
    queryFn: () => api.get('/api/analytics/health-summary-json').then((res) => res.data),
    staleTime: 5 * 60 * 1000,
  })

  // Fetch per-parameter timeseries analytics for trend visualization
  const {
    data: trendsData,
    isLoading: loadingTrends,
  } = useQuery({
    queryKey: ['healthTrendsJson'],
    queryFn: () => api.get('/api/analytics/health-trends-json').then((res) => res.data),
    staleTime: 5 * 60 * 1000,
  })

  const isLoading = loadingSummary || loadingTrends

  if (summaryError) {
    showToast('Error loading health trends: ' + (summaryError?.message || 'Unknown error'), 'error')
  }

  const parameters = trendsData?.parameters || []
  const selectedParamData = parameters.find((p) => p.parameter === selectedParameter) || parameters[0]

  // Filter parameters by search term
  const filteredParameters = parameters.filter((p) =>
    p.parameter.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // Statistical counters
  const increasingCount = parameters.filter((p) => p.analytics?.trend === 'Increasing').length
  const decreasingCount = parameters.filter((p) => p.analytics?.trend === 'Decreasing').length
  const stableCount = parameters.filter((p) => p.analytics?.trend === 'Stable' || !p.analytics?.trend).length

  if (!isLoading && parameters.length === 0) {
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
            <h3 className="font-bold text-slate-900 text-lg">No Longitudinal Trend Data Available</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Upload multiple medical laboratory reports across different dates to track biomarker trajectory trends over time.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <button
            onClick={() => navigate('/dashboard')}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700 hover:text-teal-900 mb-2"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </button>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-teal-600" /> Longitudinal Health Trends & Trajectories
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Track parameter progression, rate of change, and longitudinal biomarker direction.
          </p>
        </div>

        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className="clinical-button-secondary text-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Trends
        </button>
      </div>

      {/* Overview Stat Tiles */}
      {!isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="clinical-card p-5 space-y-1">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tracked Biomarkers</p>
            <p className="text-3xl font-extrabold text-slate-900">{parameters.length}</p>
            <p className="text-[11px] text-slate-400 font-medium">Unique Laboratory Parameters</p>
          </div>

          <div className="clinical-card p-5 space-y-1">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Increasing Trends</p>
            <p className="text-3xl font-extrabold text-rose-600 flex items-center gap-1.5">
              <span>{increasingCount}</span>
              <TrendingUp className="w-5 h-5 text-rose-500" />
            </p>
            <p className="text-[11px] text-rose-600/80 font-medium">Upward Trajectory Shift</p>
          </div>

          <div className="clinical-card p-5 space-y-1">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Decreasing Trends</p>
            <p className="text-3xl font-extrabold text-emerald-600 flex items-center gap-1.5">
              <span>{decreasingCount}</span>
              <TrendingDown className="w-5 h-5 text-emerald-500" />
            </p>
            <p className="text-[11px] text-emerald-700/80 font-medium">Downward Trajectory Shift</p>
          </div>

          <div className="clinical-card p-5 space-y-1">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Stable Parameters</p>
            <p className="text-3xl font-extrabold text-teal-700 flex items-center gap-1.5">
              <span>{stableCount}</span>
              <Minus className="w-5 h-5 text-teal-600" />
            </p>
            <p className="text-[11px] text-slate-400 font-medium">Within Normal Variance</p>
          </div>
        </div>
      )}

      {/* Loading Indicator */}
      {isLoading && (
        <div className="clinical-card p-12 text-center space-y-3">
          <Loader className="w-8 h-8 text-teal-600 animate-spin mx-auto" />
          <p className="text-xs font-medium text-slate-600">Analyzing longitudinal biomarker trends...</p>
        </div>
      )}

      {/* Selected Parameter Trend Curve */}
      {!isLoading && selectedParamData && (
        <div className="clinical-card p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-extrabold text-slate-900">
                {selectedParamData.parameter} Longitudinal Trajectory
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Observed mean: {selectedParamData.analytics?.avg?.toFixed(2) || 'N/A'} | Range: [{selectedParamData.analytics?.min?.toFixed(2) || '—'} – {selectedParamData.analytics?.max?.toFixed(2) || '—'}]
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1 ${
                selectedParamData.analytics?.trend === 'Increasing'
                  ? 'bg-rose-50 text-rose-700 border border-rose-200'
                  : selectedParamData.analytics?.trend === 'Decreasing'
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-teal-50 text-teal-700 border border-teal-200'
              }`}>
                {selectedParamData.analytics?.trend === 'Increasing' && <TrendingUp className="w-3.5 h-3.5" />}
                {selectedParamData.analytics?.trend === 'Decreasing' && <TrendingDown className="w-3.5 h-3.5" />}
                {selectedParamData.analytics?.trend === 'Stable' && <Minus className="w-3.5 h-3.5" />}
                <span>{selectedParamData.analytics?.trend || 'Stable'}</span>
              </span>
            </div>
          </div>

          <TrendChart
            data={selectedParamData.analytics?.values || []}
            parameter={selectedParamData.parameter}
            unit=""
            height={320}
          />
        </div>
      )}

      {/* Parameter Trends Table & Search */}
      {!isLoading && parameters.length > 0 && (
        <div className="clinical-card p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="font-bold text-slate-900 text-base">All Parameter Trajectories</h3>
              <p className="text-xs text-slate-500 mt-0.5">Click any row to inspect its longitudinal trend curve</p>
            </div>

            <div className="relative w-full sm:w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Filter parameters..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
          </div>

          <div className="overflow-x-auto border border-slate-200 rounded-xl">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-100/80 text-slate-900 font-semibold border-b border-slate-200">
                <tr>
                  <th className="p-3.5">Parameter</th>
                  <th className="p-3.5">Latest Value</th>
                  <th className="p-3.5">Historical Avg</th>
                  <th className="p-3.5">Min / Max</th>
                  <th className="p-3.5">Trend Direction</th>
                  <th className="p-3.5">Risk Evaluation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {filteredParameters.map((param) => {
                  const values = param.analytics?.values || []
                  const latestVal = values.length > 0 ? values[values.length - 1]?.value : null
                  const isSelected = selectedParamData?.parameter === param.parameter

                  return (
                    <tr
                      key={param.parameter}
                      onClick={() => setSelectedParameter(param.parameter)}
                      className={`hover:bg-teal-50/50 cursor-pointer transition-colors ${
                        isSelected ? 'bg-teal-50 font-semibold' : ''
                      }`}
                    >
                      <td className="p-3.5 font-bold text-slate-900">{param.parameter}</td>
                      <td className="p-3.5 font-extrabold text-slate-900">
                        {safeFormatNumber(latestVal)}
                      </td>
                      <td className="p-3.5 text-slate-600">
                        {safeFormatNumber(param.analytics?.avg)}
                      </td>
                      <td className="p-3.5 text-slate-500">
                        [{safeFormatNumber(param.analytics?.min, 1, '—')} – {safeFormatNumber(param.analytics?.max, 1, '—')}]
                      </td>
                      <td className="p-3.5">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                          param.analytics?.trend === 'Increasing'
                            ? 'bg-rose-100 text-rose-800'
                            : param.analytics?.trend === 'Decreasing'
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-teal-100 text-teal-800'
                        }`}>
                          {param.analytics?.trend === 'Increasing' && <TrendingUp className="w-3 h-3" />}
                          {param.analytics?.trend === 'Decreasing' && <TrendingDown className="w-3 h-3" />}
                          {param.analytics?.trend === 'Stable' && <Minus className="w-3 h-3" />}
                          <span>{param.analytics?.trend || 'Stable'}</span>
                        </span>
                      </td>
                      <td className="p-3.5">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold ${
                          param.risk?.risk_level === 'HIGH'
                            ? 'bg-rose-100 text-rose-800'
                            : param.risk?.risk_level === 'MEDIUM'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-slate-100 text-slate-700'
                        }`}>
                          {param.risk?.risk_level || 'LOW'} Risk
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
