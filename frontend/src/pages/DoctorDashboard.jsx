import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  getDoctorStatistics,
  getPatients,
  getAssignmentStats,
  getPatientAccessRequests,
  approvePatientAccess,
} from '../services/userService'
import {
  Users,
  FileText,
  AlertTriangle,
  Calendar,
  Activity,
  TrendingUp,
  UserCheck,
  ChevronRight,
  ShieldAlert,
  Stethoscope,
  CheckCircle2,
  XCircle,
} from 'lucide-react'
import { DashboardSkeleton } from '../components/Skeletons'

export default function DoctorDashboard() {
  const queryClient = useQueryClient()

  // 1. Doctor statistics query
  const { data: stats = { total_patients: 0, recent_patients: 0, weekly_consultations: 0, critical_cases: 0, total_reports: 0 }, isLoading: statsLoading, error: statsErr } = useQuery({
    queryKey: ['doctor-statistics'],
    queryFn: getDoctorStatistics,
    staleTime: 2 * 60 * 1000,
  })

  // 2. Patients list query
  const { data: patients = [], isLoading: patientsLoading } = useQuery({
    queryKey: ['patients'],
    queryFn: getPatients,
    staleTime: 2 * 60 * 1000,
  })

  // 3. Assignment stats query
  const { data: assignmentStats = { total_patients_on_platform: 0, active_clinical_patients: 0 } } = useQuery({
    queryKey: ['assignment-stats'],
    queryFn: getAssignmentStats,
    staleTime: 2 * 60 * 1000,
  })

  // 4. Access requests query
  const { data: accessRequests = [], isLoading: requestsLoading, refetch: refetchRequests } = useQuery({
    queryKey: ['patient-access-requests'],
    queryFn: () => getPatientAccessRequests().then((res) => res.data),
    staleTime: 30 * 1000,
  })

  const loading = statsLoading || patientsLoading || requestsLoading
  const statsError = statsErr ? 'Could not load doctor statistics.' : ''
  const pendingAccess = Array.isArray(accessRequests) ? accessRequests.filter(r => r.status === 'pending') : []
  const recentPatients = patients.slice(0, 5)

  // Mutation to approve/reject access request
  const respondMutation = useMutation({
    mutationFn: ({ requestId, action }) => approvePatientAccess(requestId, action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patient-access-requests'] })
      queryClient.invalidateQueries({ queryKey: ['doctor-statistics'] })
      queryClient.invalidateQueries({ queryKey: ['assignment-stats'] })
      queryClient.invalidateQueries({ queryKey: ['patients'] })
    },
  })

  const respondToRequest = (requestId, action) => {
    respondMutation.mutate({ requestId, action })
  }

  if (loading) {
    return <DashboardSkeleton />
  }

  return (
    <div className="space-y-6">
      {/* Physician Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-950 to-teal-950 rounded-2xl p-6 sm:p-8 text-white shadow-md relative overflow-hidden border border-slate-800">
        <div className="relative z-10 max-w-3xl space-y-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-teal-500/20 border border-teal-400/30 text-teal-200">
            <Stethoscope className="w-3.5 h-3.5 text-teal-400" /> Physician Decision Support Workspace
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Clinical Patient Dashboard
          </h1>
          <p className="text-slate-300 text-xs sm:text-sm leading-relaxed max-w-2xl">
            Inspect authorized patient health profiles, track lab parameter deltas, review doctor notes, and grant or reject patient access requests.
          </p>
        </div>
      </div>

      {statsError && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800">
          {statsError}
        </div>
      )}

      {/* Top Patient Volume Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="clinical-card p-5 flex items-center justify-between border-l-4 border-l-teal-600">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Platform Patients</p>
            <p className="text-3xl font-extrabold text-slate-900">{assignmentStats.total_patients_on_platform}</p>
            <p className="text-[11px] text-slate-400 font-medium">Registered patient population</p>
          </div>
          <div className="p-3 bg-teal-50 text-teal-600 rounded-xl border border-teal-100">
            <Users className="w-6 h-6" />
          </div>
        </div>

        <div className="clinical-card p-5 flex items-center justify-between border-l-4 border-l-emerald-600">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Your Assigned Patients</p>
            <p className="text-3xl font-extrabold text-emerald-600">{assignmentStats.your_assigned_patients}</p>
            <p className="text-[11px] text-slate-400 font-medium">Approved clinical access</p>
          </div>
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl border border-emerald-100">
            <UserCheck className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Pending Access Requests Warning Section */}
      {pendingAccess.length > 0 && (
        <div className="clinical-card border border-amber-200/80 bg-amber-50/30 overflow-hidden">
          <div className="p-4 border-b border-amber-200/60 bg-amber-50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-600" />
              <h3 className="font-bold text-amber-900 text-sm sm:text-base">
                Pending Patient Access Requests ({pendingAccess.length})
              </h3>
            </div>
            <span className="text-xs text-amber-700 font-semibold">Requires Action</span>
          </div>

          <div className="divide-y divide-amber-100">
            {pendingAccess.map((req) => (
              <div key={req.id} className="p-4 flex flex-wrap items-center justify-between gap-3 bg-white hover:bg-amber-50/50 transition-colors">
                <div>
                  <p className="text-sm font-bold text-slate-900">{req.patient_name}</p>
                  <p className="text-xs text-slate-500">Access Request #{req.id} · Received {req.created_at ? new Date(req.created_at).toLocaleDateString() : 'recently'}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => respondToRequest(req.id, 'accept')}
                    disabled={respondMutation.isLoading}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition-colors disabled:opacity-50 inline-flex items-center gap-1"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" /> Accept Access
                  </button>
                  <button
                    type="button"
                    onClick={() => respondToRequest(req.id, 'reject')}
                    disabled={respondMutation.isLoading}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50 inline-flex items-center gap-1"
                  >
                    <XCircle className="w-3.5 h-3.5 text-slate-400" /> Reject Request
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Clinical Practice Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="clinical-card p-5 space-y-1">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">New Patients (7d)</p>
          <p className="text-2xl font-extrabold text-slate-900">{stats.recent_patients}</p>
          <p className="text-[11px] text-slate-400 font-medium">Recently registered</p>
        </div>

        <div className="clinical-card p-5 space-y-1">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Weekly Consults</p>
          <p className="text-2xl font-extrabold text-indigo-600">{stats.weekly_consultations}</p>
          <p className="text-[11px] text-slate-400 font-medium">Report reviews this week</p>
        </div>

        <div className="clinical-card p-5 space-y-1">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Critical Flagged Cases</p>
          <p className="text-2xl font-extrabold text-rose-600">{stats.critical_cases}</p>
          <p className="text-[11px] text-rose-600/80 font-medium">Abnormal lab observations</p>
        </div>

        <div className="clinical-card p-5 space-y-1">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Reports In Database</p>
          <p className="text-2xl font-extrabold text-slate-900">{stats.total_reports}</p>
          <p className="text-[11px] text-slate-400 font-medium">Accessible lab records</p>
        </div>
      </div>

      {/* Recent Patients Table */}
      <div className="clinical-card overflow-hidden">
        <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-indigo-600" />
            <h3 className="font-bold text-slate-900 text-sm">Assigned Patients Directory</h3>
          </div>
          <Link to="/doctor/patients" className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
            View All <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="divide-y divide-slate-100">
          {recentPatients.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-400">
              No assigned patients registered yet.
            </div>
          ) : (
            recentPatients.map((patient) => (
              <Link
                key={patient.id}
                to={`/doctor/patient/${patient.id}`}
                className="p-4 sm:p-5 flex items-center justify-between hover:bg-slate-50 transition-colors group"
              >
                <div className="flex items-center gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-700 font-bold flex items-center justify-center text-sm shrink-0">
                    {patient.full_name?.charAt(0) || 'P'}
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm group-hover:text-indigo-700 transition-colors flex items-center gap-1.5">
                      <span>{patient.full_name}</span>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-600" />
                    </h4>
                    <p className="text-xs text-slate-500">{patient.email}</p>
                    {patient.age && (
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        {patient.age} yrs · {patient.gender || '—'} · Blood Group: {patient.blood_group || '—'}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="clinical-badge-info">Inspect Record</span>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
