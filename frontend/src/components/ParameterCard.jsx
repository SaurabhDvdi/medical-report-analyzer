import React from 'react'
import { ChevronRight, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import RiskBadge from './RiskBadge'

/**
 * ParameterCard Component
 * Displays a card with parameter information including latest value, trend, and risk
 */
export default function ParameterCard({
  parameter,
  latestValue,
  unit,
  trend,
  riskLevel,
  confidence,
  isLoading = false,
  onClick,
}) {
  const getTrendIcon = () => {
    switch (trend) {
      case 'Increasing':
        return <TrendingUp className="w-4 h-4 text-rose-600" />
      case 'Decreasing':
        return <TrendingDown className="w-4 h-4 text-emerald-600" />
      case 'Stable':
      default:
        return <Minus className="w-4 h-4 text-teal-600" />
    }
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs animate-pulse space-y-3">
        <div className="w-24 h-4 bg-slate-200 rounded" />
        <div className="w-32 h-7 bg-slate-200 rounded" />
        <div className="w-20 h-4 bg-slate-100 rounded" />
      </div>
    )
  }

  const hasValidValue = latestValue !== null && latestValue !== undefined && !isNaN(latestValue)

  return (
    <button
      onClick={onClick}
      className="w-full text-left clinical-card p-5 hover:border-teal-300 cursor-pointer space-y-3 flex flex-col justify-between"
    >
      {/* Header */}
      <div className="flex justify-between items-start">
        <p className="text-xs font-bold text-slate-900 truncate pr-2">{parameter}</p>
        <ChevronRight className="w-4 h-4 text-slate-400 shrink-0" />
      </div>

      {/* Latest Value */}
      <div>
        <div className="flex items-baseline gap-1.5">
          <span className="text-2xl font-extrabold text-slate-900">
            {hasValidValue ? Number(latestValue).toFixed(2) : 'Unavailable'}
          </span>
          {hasValidValue && unit && <span className="text-xs font-medium text-slate-500">{unit}</span>}
        </div>
      </div>

      {/* Trend and Risk */}
      <div className="flex justify-between items-center pt-2 border-t border-slate-100">
        <div className="flex items-center gap-1.5">
          {getTrendIcon()}
          <span className="text-xs font-semibold text-slate-700">{trend || 'Stable'}</span>
        </div>
        <RiskBadge riskLevel={riskLevel} confidence={confidence} size="sm" />
      </div>
    </button>
  )
}
