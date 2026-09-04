import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getCategories,
  getSpecialties,
  getDoctors,
  grantDoctorAccess,
  getDoctorAccess
} from '../services/userService'
import {
  Search,
  User,
  Stethoscope,
  Loader,
  HeartHandshake,
  ShieldCheck,
  Filter,
  Clock,
  CheckCircle2,
  AlertCircle
} from 'lucide-react'
import { CardSkeleton } from '../components/Skeletons'

function getDoctorInitials(name) {
  if (!name) return 'DR'
  const cleanName = name.replace(/^(dr|doctor)\.?\s*/i, '').trim()
  const parts = cleanName.split(/\s+/).filter(Boolean)
  if (parts.length === 0) return 'DR'
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

export default function FindDoctors() {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [specialtyId, setSpecialtyId] = useState('')
  const [actionMsg, setActionMsg] = useState({})
  const [actionBusy, setActionBusy] = useState({})

  // 1. Categories query
  const { data: categories = [], isLoading: catLoading, error: catError } = useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
    staleTime: 30 * 60 * 1000,
  })

  // 2. Specialties query
  const { data: specialties = [] } = useQuery({
    queryKey: ['specialties', categoryId],
    queryFn: () => getSpecialties(categoryId),
    enabled: !!categoryId,
    staleTime: 30 * 60 * 1000,
  })

  // 3. Existing Patient Doctor Access list
  const { data: doctorAccessList = [] } = useQuery({
    queryKey: ['doctor-access'],
    queryFn: getDoctorAccess,
    staleTime: 5 * 60 * 1000,
  })

  // Map doctor_id to access status
  const doctorAccessMap = {}
  doctorAccessList.forEach((acc) => {
    if (acc.doctor_id) {
      doctorAccessMap[acc.doctor_id] = acc.status
    }
  })

  // 4. Doctors directory query
  const { data: doctors = [], isLoading: listLoading, error: docsError, refetch: fetchDoctors } = useQuery({
    queryKey: ['doctors', name, categoryId, specialtyId],
    queryFn: () => {
      const params = {}
      if (name.trim()) params.name = name.trim()
      if (categoryId) params.category_id = categoryId
      if (specialtyId) params.specialty_id = specialtyId
      return getDoctors(params)
    },
    staleTime: 2 * 60 * 1000,
  })

  const loading = catLoading
  const error = catError ? 'Could not load categories.' : (docsError ? (docsError.response?.data?.detail || 'Could not load doctors.') : '')

  // Request Access Mutation
  const requestMutation = useMutation({
    mutationFn: (doctorId) => grantDoctorAccess(doctorId),
    onMutate: (doctorId) => {
      setActionBusy((b) => ({ ...b, [doctorId]: true }))
      setActionMsg((m) => ({ ...m, [doctorId]: '' }))
    },
    onSuccess: (_, doctorId) => {
      setActionMsg((m) => ({ ...m, [doctorId]: 'Request sent' }))
      queryClient.invalidateQueries({ queryKey: ['doctor-access'] })
      queryClient.invalidateQueries({ queryKey: ['discovery-stats'] })
      queryClient.invalidateQueries({ queryKey: ['doctors'] })
    },
    onError: (err, doctorId) => {
      const d = err.response?.data?.detail
      setActionMsg((m) => ({
        ...m,
        [doctorId]: typeof d === 'string' ? d : 'Request failed',
      }))
    },
    onSettled: (_, __, doctorId) => {
      setActionBusy((b) => ({ ...b, [doctorId]: false }))
    }
  })

  const requestAccess = (doctorId) => {
    requestMutation.mutate(doctorId)
  }

  if (loading) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Stethoscope className="w-6 h-6 text-[#0F766E]" />
            Find Doctors
          </h1>
          <p className="text-xs text-slate-500 mt-1 font-medium max-w-2xl leading-relaxed">
            Find qualified physicians and specialists and request secure access to your medical records.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="inline-flex items-center gap-1.5 text-xs bg-slate-100 border border-slate-200 text-slate-700 px-3 py-1.5 rounded-full font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            API Connected
          </span>
        </div>
      </div>

      {/* 2. Compact Filter Toolbar Card */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h2 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Filter className="w-4 h-4 text-[#0F766E]" />
            Physician & Specialist Directory
          </h2>
          <span className="text-[11px] font-semibold text-slate-400">
            {doctors.length} {doctors.length === 1 ? 'doctor' : 'doctors'} available
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 items-end">
          {/* Doctor Name Search */}
          <div className="space-y-1">
            <label className="block text-[11px] font-semibold text-slate-600">Doctor Name</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="search"
                className="w-full bg-slate-50 border border-slate-200/90 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-white transition-all h-[38px]"
                placeholder="Search by physician name..."
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
          </div>

          {/* Category Dropdown */}
          <div className="space-y-1">
            <label className="block text-[11px] font-semibold text-slate-600">Category</label>
            <select
              className="w-full bg-slate-50 border border-slate-200/90 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-white transition-all h-[38px] cursor-pointer"
              value={categoryId}
              onChange={(e) => {
                setCategoryId(e.target.value)
                setSpecialtyId('')
              }}
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Specialty Dropdown */}
          <div className="space-y-1">
            <label className="block text-[11px] font-semibold text-slate-600">Specialty</label>
            <select
              className="w-full bg-slate-50 border border-slate-200/90 rounded-xl px-3 py-2 text-xs text-slate-900 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-white transition-all h-[38px] cursor-pointer"
              value={specialtyId}
              onChange={(e) => setSpecialtyId(e.target.value)}
              disabled={!categoryId}
            >
              <option value="">All Specialties{categoryId ? '' : ' (select category first)'}</option>
              {specialties.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          {/* Filter Action Button */}
          <div>
            <button
              type="button"
              onClick={fetchDoctors}
              disabled={listLoading}
              className="w-full bg-[#0F766E] hover:bg-teal-800 disabled:opacity-50 text-white font-semibold rounded-xl px-4 py-2.5 text-xs transition-all shadow-xs flex items-center justify-center gap-2 h-[38px] cursor-pointer"
            >
              {listLoading ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : (
                <Filter className="w-4 h-4" />
              )}
              <span>Filter Directory</span>
            </button>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-xs text-rose-800 rounded-xl flex items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span className="font-medium">{error}</span>
          </div>
          <button
            onClick={() => fetchDoctors()}
            className="text-[11px] font-bold underline hover:text-rose-900"
          >
            Retry
          </button>
        </div>
      )}

      {/* 3. Doctor Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5">
        {listLoading ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : doctors.length === 0 ? (
          <div className="col-span-full bg-white rounded-2xl border border-slate-200/90 p-12 text-center space-y-3 shadow-xs">
            <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 mx-auto flex items-center justify-center">
              <User className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-slate-800 tracking-tight">No physicians found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">
              Try adjusting your name, category, or specialty search filters to find available clinical specialists.
            </p>
          </div>
        ) : (
          doctors.map((d) => {
            const currentStatus = doctorAccessMap[d.id] || (actionMsg[d.id] === 'Request sent' ? 'pending' : null)
            const isPending = currentStatus === 'pending'
            const isApproved = currentStatus === 'approved' || currentStatus === 'accepted'
            const isRejected = currentStatus === 'rejected'
            const isRevoked = currentStatus === 'revoked'
            const isBusy = actionBusy[d.id]

            const initials = getDoctorInitials(d.full_name)

            let buttonLabel = 'Request Clinical Access'
            if (isPending) buttonLabel = 'Request Pending'
            else if (isApproved) buttonLabel = 'Access Granted'
            else if (isRejected) buttonLabel = 'Request Again'
            else if (isRevoked) buttonLabel = 'Request Access'

            return (
              <div
                key={d.id}
                className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between space-y-4"
              >
                {/* Doctor Identity Header */}
                <div className="flex items-start gap-4">
                  {/* Initials Avatar */}
                  <div className="w-11 h-11 rounded-xl bg-teal-50 border border-teal-200/80 text-[#0F766E] font-bold text-sm flex items-center justify-center shrink-0 shadow-2xs">
                    {initials}
                  </div>

                  <div className="space-y-1 min-w-0 flex-1">
                    <h3 className="font-bold text-slate-900 text-base tracking-tight leading-snug truncate">
                      {d.full_name}
                    </h3>
                    <div className="flex items-center gap-1.5 text-xs text-slate-500 flex-wrap">
                      <Stethoscope className="w-3.5 h-3.5 text-[#0F766E] shrink-0" />
                      <span>{d.category_name || 'General Practice'}</span>
                      <span className="text-slate-300">·</span>
                      <span className="font-semibold text-slate-700">{d.specialty_name || 'Specialist'}</span>
                    </div>
                  </div>
                </div>

                {/* Footer Action & Status */}
                <div className="pt-3.5 border-t border-slate-100 flex items-center justify-between gap-3 flex-wrap">
                  {isApproved ? (
                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200/80 px-3.5 py-2 rounded-xl">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      Access Granted
                    </span>
                  ) : isPending ? (
                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200/80 px-3.5 py-2 rounded-xl">
                      <Clock className="w-3.5 h-3.5 text-amber-600 animate-pulse" />
                      Request Pending
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={() => requestAccess(d.id)}
                      disabled={isBusy || isApproved || isPending}
                      className="bg-[#0F766E] hover:bg-teal-800 disabled:opacity-50 text-white text-xs font-semibold rounded-xl px-4 py-2.5 transition-all shadow-2xs flex items-center gap-2 cursor-pointer"
                    >
                      {isBusy ? (
                        <Loader className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <HeartHandshake className="w-3.5 h-3.5" />
                      )}
                      <span>{isBusy ? 'Sending Request...' : buttonLabel}</span>
                    </button>
                  )}

                  {actionMsg[d.id] && !isPending && !isApproved && (
                    <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                      {actionMsg[d.id]}
                    </span>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
