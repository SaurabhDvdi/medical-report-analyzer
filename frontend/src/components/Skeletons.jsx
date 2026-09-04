import React from 'react'

export const CardSkeleton = ({ className = "" }) => (
  <div className={`bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm animate-pulse space-y-3 ${className}`}>
    <div className="flex items-center justify-between">
      <div className="w-24 h-4 bg-slate-200 rounded" />
      <div className="w-8 h-8 bg-slate-200 rounded-lg" />
    </div>
    <div className="w-3/4 h-6 bg-slate-200 rounded" />
    <div className="w-1/2 h-3 bg-slate-200 rounded" />
  </div>
)

export const MetricSkeleton = () => (
  <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm animate-pulse space-y-2">
    <div className="flex items-center justify-between">
      <div className="w-20 h-3 bg-slate-200 rounded" />
      <div className="w-8 h-8 bg-slate-100 rounded-xl" />
    </div>
    <div className="w-16 h-7 bg-slate-200 rounded" />
    <div className="w-32 h-3 bg-slate-100 rounded" />
  </div>
)

export const DashboardSkeleton = () => (
  <div className="space-y-6 animate-pulse">
    <div className="space-y-2">
      <div className="w-48 h-7 bg-slate-200 rounded-lg" />
      <div className="w-80 h-4 bg-slate-100 rounded" />
    </div>

    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricSkeleton />
      <MetricSkeleton />
      <MetricSkeleton />
      <MetricSkeleton />
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-6 space-y-4">
        <div className="w-40 h-5 bg-slate-200 rounded" />
        <div className="w-full h-64 bg-slate-100 rounded-lg" />
      </div>
      <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
        <div className="w-36 h-5 bg-slate-200 rounded" />
        <div className="space-y-3">
          <div className="w-full h-12 bg-slate-100 rounded-lg" />
          <div className="w-full h-12 bg-slate-100 rounded-lg" />
          <div className="w-full h-12 bg-slate-100 rounded-lg" />
        </div>
      </div>
    </div>
  </div>
)

export const ChartSkeleton = () => (
  <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm animate-pulse space-y-4">
    <div className="flex items-center justify-between">
      <div className="w-40 h-5 bg-slate-200 rounded" />
      <div className="w-20 h-4 bg-slate-100 rounded" />
    </div>
    <div className="w-full h-72 bg-slate-100 rounded-xl" />
  </div>
)

export const TableSkeleton = ({ rows = 5 }) => (
  <div className="bg-white rounded-xl border border-slate-200 shadow-sm animate-pulse overflow-hidden">
    <div className="p-4 border-b border-slate-100 flex items-center justify-between">
      <div className="w-36 h-5 bg-slate-200 rounded" />
      <div className="w-24 h-8 bg-slate-100 rounded-lg" />
    </div>
    <div className="divide-y divide-slate-100">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="p-4 flex items-center justify-between">
          <div className="space-y-2 flex-1">
            <div className="w-44 h-4 bg-slate-200 rounded" />
            <div className="w-28 h-3 bg-slate-100 rounded" />
          </div>
          <div className="w-20 h-6 bg-slate-200 rounded-full" />
        </div>
      ))}
    </div>
  </div>
)

export const FormSkeleton = () => (
  <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm animate-pulse space-y-5">
    <div className="w-36 h-5 bg-slate-200 rounded" />
    <div className="space-y-4">
      <div className="w-full h-10 bg-slate-100 rounded-lg" />
      <div className="w-full h-10 bg-slate-100 rounded-lg" />
      <div className="w-full h-24 bg-slate-100 rounded-lg" />
    </div>
    <div className="w-32 h-10 bg-slate-200 rounded-lg" />
  </div>
)