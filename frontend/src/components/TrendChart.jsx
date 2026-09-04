import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { format, parseISO } from 'date-fns'
import { safeFormatNumber } from '../utils/numeric'

/**
 * TrendChart Component
 * Displays a line chart showing parameter trend over time
 */
export default function TrendChart({ data = [], parameter, unit, height = 300 }) {
  if (!data || data.length === 0) {
    return (
      <div
        className="flex flex-col items-center justify-center bg-slate-50 rounded-xl border border-slate-200 p-6 text-center space-y-1"
        style={{ height: `${height}px` }}
      >
        <p className="text-xs font-semibold text-slate-700">Insufficient Trend Observations</p>
        <p className="text-[11px] text-slate-400">Additional report dates required to generate longitudinal trend curves.</p>
      </div>
    )
  }

  // Format data for recharts (parse ISO dates safely)
  const chartData = data.map((item) => {
    let displayDate = item.date
    let fullDate = item.date
    try {
      const parsed = parseISO(item.date)
      displayDate = format(parsed, 'MMM dd')
      fullDate = format(parsed, 'PPP')
    } catch (e) {
      // Fallback
    }
    return {
      ...item,
      displayDate,
      fullDate,
    }
  })

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const val = payload[0].value
      const displayVal = safeFormatNumber(val)
      return (
        <div className="bg-slate-900 text-white p-3 border border-slate-800 rounded-xl shadow-lg text-xs space-y-1">
          <p className="font-semibold text-slate-300">
            {payload[0].payload.fullDate}
          </p>
          <p className="text-teal-400 font-extrabold">
            {parameter}: {displayVal} {unit || ''}
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="w-full bg-white rounded-xl border border-slate-200 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-900">
          {parameter} Trend {unit ? `(${unit})` : ''}
        </h3>
        <span className="text-[11px] text-slate-500 font-medium">{chartData.length} Observation(s)</span>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="displayDate"
            stroke="#64748b"
            style={{ fontSize: '11px' }}
          />
          <YAxis
            stroke="#64748b"
            style={{ fontSize: '11px' }}
            label={{
              value: unit || 'Value',
              angle: -90,
              position: 'insideLeft',
              style: { textAnchor: 'middle', fill: '#64748b', fontSize: '11px' },
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#0d9488"
            strokeWidth={2.5}
            dot={{ fill: '#0d9488', r: 4 }}
            activeDot={{ r: 6, fill: '#0f766e' }}
            name={parameter}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
