import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { X, Filter, RotateCcw } from 'lucide-react'
import Skeleton from 'react-loading-skeleton'
import 'react-loading-skeleton/dist/skeleton.css'

import ParameterCard from '../components/ParameterCard'
import TrendChart from '../components/TrendChart'
import InsightsPanel from '../components/InsightsPanel'
import RiskBadge from '../components/RiskBadge'
import { getDashboardData } from '../services/dashboardService'

/**
 * MedicalDashboard Component
 * Main medical dashboard displaying parameters with analytics, risk, and insights
 */
export default function MedicalDashboard() {
  const [selectedParameter, setSelectedParameter] = useState(null)
  const [filterParameter, setFilterParameter] = useState('')
  const [allParameters, setAllParameters] = useState([])

  // Fetch dashboard data
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard', filterParameter],
    queryFn: () => getDashboardData(filterParameter),
    staleTime: 1000 * 60 * 5, // 5 minutes
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

  // Determine latest value from analytics values
  const getLatestValue = (analytics) => {
    if (analytics?.values && analytics.values.length > 0) {
      return analytics.values[analytics.values.length - 1]?.value
    }
    return null
  }

  // Get unit from analytics
  const getUnit = (analytics) => {
    if (analytics?.values && analytics.values.length > 0) {
      // In a real scenario, you might store unit separately
      // For now, return empty string
      return ''
    }
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
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <Skeleton height={40} width="200px" className="mb-4" />
            <Skeleton height={20} width="400px" />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-white rounded-lg border border-gray-200 p-6">
                <Skeleton height={24} width="50%" className="mb-4" />
                <Skeleton height={32} width="60%" className="mb-4" />
                <Skeleton height={20} width="40%" />
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 mb-2">Error Loading Dashboard</h2>
            <p className="text-red-700 mb-4">
              {error?.message || 'Failed to load dashboard data'}
            </p>
            <button
              onClick={() => refetch()}
              className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              Try Again
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Empty state
  if (!isLoading && parameters.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <h2 className="text-2xl font-semibold text-gray-800 mb-2">No Data Available</h2>
            <p className="text-gray-600 mb-6">
              Upload medical reports to see your health analytics and insights.
            </p>
            <button
              onClick={() => handleReset()}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Health Dashboard</h1>
              <p className="text-gray-600 mt-1">
                Monitor your medical parameters and track health trends
              </p>
            </div>
            <button
              onClick={() => refetch()}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              title="Refresh data"
            >
              <RotateCcw className="w-4 h-4" />
              Refresh
            </button>
          </div>

          {/* Filter Bar */}
          <div className="flex gap-3 items-center">
            <Filter className="w-5 h-5 text-gray-600" />
            <select
              value={filterParameter}
              onChange={(e) => {
                setFilterParameter(e.target.value)
                setSelectedParameter(null)
              }}
              className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-700 text-sm font-medium hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Parameters</option>
              {allParameters.map((param) => (
                <option key={param} value={param}>
                  {param}
                </option>
              ))}
            </select>

            {filterParameter && (
              <button
                onClick={() => handleReset()}
                className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-800 text-sm font-medium"
              >
                <X className="w-4 h-4" />
                Clear filter
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Parameter Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
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
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              {/* Modal Header */}
              <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{selectedData.parameter}</h2>
                  <p className="text-sm text-gray-600 mt-1">Detailed analysis and insights</p>
                </div>
                <button
                  onClick={handleCloseDetail}
                  className="text-gray-500 hover:text-gray-700 transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6 space-y-8">
                {/* Key Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <p className="text-xs font-medium text-blue-600 uppercase tracking-wide">Latest</p>
                    <p className="text-2xl font-bold text-blue-900 mt-1">
                      {getLatestValue(selectedData.analytics)?.toFixed(2) || 'N/A'}
                    </p>
                  </div>

                  <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                    <p className="text-xs font-medium text-green-600 uppercase tracking-wide">Average</p>
                    <p className="text-2xl font-bold text-green-900 mt-1">
                      {selectedData.analytics?.avg?.toFixed(2) || 'N/A'}
                    </p>
                  </div>

                  <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                    <p className="text-xs font-medium text-purple-600 uppercase tracking-wide">Trend</p>
                    <p className="text-lg font-bold text-purple-900 mt-1">
                      {selectedData.analytics?.trend || 'Unknown'}
                    </p>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">Risk Level</p>
                    <div className="mt-1">
                      <RiskBadge
                        riskLevel={selectedData.risk?.risk_level}
                        confidence={selectedData.risk?.confidence}
                        size="md"
                      />
                    </div>
                  </div>
                </div>

                {/* Trend Chart */}
                <div>
                  <TrendChart
                    data={selectedData.analytics?.values || []}
                    parameter={selectedData.parameter}
                    unit={getUnit(selectedData.analytics)}
                    height={400}
                  />
                </div>

                {/* Insights Panel */}
                <div>
                  <InsightsPanel
                    insights={selectedData.insights}
                    parameter={selectedData.parameter}
                  />
                </div>

                {/* Risk Reason */}
                {selectedData.risk?.reason && (
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                    <h4 className="font-semibold text-amber-900 mb-2">Risk Analysis</h4>
                    <p className="text-sm text-amber-800">{selectedData.risk.reason}</p>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="border-t border-gray-200 bg-gray-50 px-6 py-4">
                <button
                  onClick={handleCloseDetail}
                  className="w-full bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
