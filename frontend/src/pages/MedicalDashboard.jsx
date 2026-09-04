import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { X, Filter, RotateCcw, Activity } from 'lucide-react'
import ParameterCard from '../components/ParameterCard'
import TrendChart from '../components/TrendChart'
import InsightsPanel from '../components/InsightsPanel'
import RiskBadge from '../components/RiskBadge'
import { getDashboardData } from '../services/dashboardService'
import { CardSkeleton } from '../components/Skeletons'

export default function MedicalDashboard() {
  const [selectedParameter, setSelectedParameter] = useState(null)
  const [filterParameter, setFilterParameter] = useState('')
  const [allParameters, setAllParameters] = useState([])

  // Fetch dashboard data
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard', filterParameter],
    queryFn: () => getDashboardData(filterParameter),
    staleTime: 1000 * 60 * 5,
  })

  // Extract all unique parameters on load
  useEffect(() => {
    if (data?.parameters) {
      const params = data.parameters.map((p) => p.parameter)
      setAllParameters(params)
    }
  }, [data])

  const parameters = data?.parameters || []
  const selectedData = parameters.find((p) => p.parameter === selectedParameter)

  const getLatestValue = (analytics) => {
    if (analytics?.values && analytics.values.length > 0) {
      return analytics.values[analytics.values.length - 1]?.value
    }
    return null
  }

  const getUnit = (analytics) => {
    return ''
  }

  const handleCloseDetail = () => {
    setSelectedParameter(null)
  }

  const handleReset = () => {
    setFilterParameter('')
    handleCloseDetail()
  }

  // Loading skeleton
  if (isLoading && parameters.length === 0) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="clinical-card p-6 bg-rose-50 border border-rose-200 text-rose-800 space-y-3">
        <h3 className="font-bold text-base">Error Loading Clinical Dashboard</h3>
        <p className="text-xs">{error?.message || 'Failed to load dashboard analytics'}</p>
        <button
          onClick={() => refetch()}
          className="clinical-button-primary bg-rose-600 hover:bg-rose-700 text-xs"
        >
          <RotateCcw className="w-3.5 h-3.5 mr-1" /> Retry Query
        </button>
      </div>
    )
  }

  // Empty state
  if (!isLoading && parameters.length === 0) {
    return (
      <div className="clinical-card p-12 text-center space-y-4">
        <Activity className="w-12 h-12 text-slate-300 mx-auto" />
        <div>
          <h3 className="font-bold text-slate-900 text-lg">No Medical Parameters Recorded</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Upload medical laboratory PDF reports to start tracking biomarker analytics and longitudinal risks.
          </p>
        </div>
        <button
          onClick={() => handleReset()}
          className="clinical-button-secondary text-xs"
        >
          <RotateCcw className="w-3.5 h-3.5 mr-1" /> Refresh Dashboard
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header & Filter Row */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <Activity className="w-6 h-6 text-teal-600" /> Clinical Biomarker Analytics
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Aggregated statistical distribution, risk scoring, and longitudinal trends.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 bg-white px-3 py-1.5 border border-slate-300 rounded-lg text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={filterParameter}
              onChange={(e) => {
                setFilterParameter(e.target.value)
                setSelectedParameter(null)
              }}
              className="bg-transparent text-slate-700 font-semibold focus:outline-none"
            >
              <option value="">All Parameters ({allParameters.length})</option>
              {allParameters.map((param) => (
                <option key={param} value={param}>
                  {param}
                </option>
              ))}
            </select>
          </div>

          {filterParameter && (
            <button
              onClick={() => handleReset()}
              className="text-xs font-semibold text-rose-600 hover:underline flex items-center gap-1"
            >
              <X className="w-3.5 h-3.5" /> Clear Filter
            </button>
          )}

          <button
            onClick={() => refetch()}
            className="clinical-button-secondary text-xs"
          >
            <RotateCcw className="w-3.5 h-3.5 mr-1" /> Refresh
          </button>
        </div>
      </div>

      {/* Parameter Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {parameters.map((item) => (
          <ParameterCard
            key={item.parameter}
            parameter={item.parameter}
            latestValue={getLatestValue(item.analytics)}
            unit={getUnit(item.analytics)}
            trend={item.analytics?.trend}
            riskLevel={item.risk?.risk_level}
            confidence={item.risk?.confidence}
            isLoading={false}
            onClick={() => setSelectedParameter(item.parameter)}
          />
        ))}
      </div>

      {/* Detailed View Modal */}
      {selectedData && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto space-y-6 p-6">
            {/* Modal Header */}
            <div className="flex justify-between items-center border-b border-slate-100 pb-4">
              <div>
                <h2 className="text-xl font-extrabold text-slate-900">{selectedData.parameter}</h2>
                <p className="text-xs text-slate-500 mt-0.5">Detailed statistical analysis and risk evaluation</p>
              </div>
              <button
                onClick={handleCloseDetail}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80">
                <p className="text-[10px] font-semibold text-slate-500 uppercase">Latest Value</p>
                <p className="text-xl font-extrabold text-slate-900 mt-1">
                  {getLatestValue(selectedData.analytics)?.toFixed(2) || 'N/A'}
                </p>
              </div>

              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80">
                <p className="text-[10px] font-semibold text-slate-500 uppercase">Average</p>
                <p className="text-xl font-extrabold text-slate-900 mt-1">
                  {selectedData.analytics?.avg?.toFixed(2) || 'N/A'}
                </p>
              </div>

              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80">
                <p className="text-[10px] font-semibold text-slate-500 uppercase">Trend</p>
                <p className="text-sm font-extrabold text-teal-700 mt-1">
                  {selectedData.analytics?.trend || 'Stable'}
                </p>
              </div>

              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80">
                <p className="text-[10px] font-semibold text-slate-500 uppercase mb-1">Risk Evaluation</p>
                <RiskBadge
                  riskLevel={selectedData.risk?.risk_level}
                  confidence={selectedData.risk?.confidence}
                  size="md"
                />
              </div>
            </div>

            {/* Trend Chart */}
            <div className="clinical-card p-4">
              <TrendChart
                data={selectedData.analytics?.values || []}
                parameter={selectedData.parameter}
                unit={getUnit(selectedData.analytics)}
                height={350}
              />
            </div>

            {/* Insights Panel */}
            <InsightsPanel
              insights={selectedData.insights}
              parameter={selectedData.parameter}
            />

            {/* Risk Reason */}
            {selectedData.risk?.reason && (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 space-y-1">
                <h4 className="font-bold">Risk Rationale</h4>
                <p>{selectedData.risk.reason}</p>
              </div>
            )}

            <div className="pt-2 flex justify-end">
              <button
                onClick={handleCloseDetail}
                className="clinical-button-secondary text-xs"
              >
                Close Analytical Modal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
