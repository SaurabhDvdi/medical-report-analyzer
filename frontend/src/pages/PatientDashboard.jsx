import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Heart,
  Pill,
  AlertTriangle,
  TrendingUp,
  FileText,
  Activity,
  Stethoscope,
  UserCheck,
  ChevronRight,
  Shield,
  Search,
  CheckCircle2,
  Clock,
  XCircle,
  Plus
} from 'lucide-react'
import { useToast } from '../components/Toast'
import { useAuth } from '../contexts/AuthContext'
import { DashboardSkeleton } from '../components/Skeletons'
import {
  getProfile,
  getMedicines,
  getDiscoveryStats,
  getDoctorAccess,
  grantDoctorAccess,
  revokeDoctorAccess
} from '../services/userService'
import { getReportsSummary } from '../services/reportService'

export default function PatientDashboard() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const queryClient = useQueryClient()

  // Profile query
  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: getProfile,
    staleTime: 5 * 60 * 1000,
    onError: (error) => {
      showToast(error.response?.data?.detail || 'Failed to load profile', 'error')
    }
  })

  // Medicines query
  const { data: medicines, isLoading: medicinesLoading } = useQuery({
    queryKey: ['medicines'],
    queryFn: getMedicines,
    staleTime: 5 * 60 * 1000,
    onError: () => {
      showToast('Failed to load medicines', 'error')
    }
  })

  // Reports summary query
  const { data: reportsSummary, isLoading: reportsLoading } = useQuery({
    queryKey: ['reports-summary'],
    queryFn: getReportsSummary,
    staleTime: 5 * 60 * 1000,
    onError: (error) => {
      showToast(error.response?.data?.detail || 'Failed to load reports', 'error')
    }
  })

  // Discovery stats query
  const { data: discovery = { total_doctors_on_platform: 0, your_active_doctors: 0 }, isLoading: discoveryLoading } = useQuery({
    queryKey: ['discovery-stats'],
    queryFn: getDiscoveryStats,
    staleTime: 5 * 60 * 1000,
    onError: (error) => {
      console.error('Discovery stats error:', error)
    }
  })

  // Doctor access query
  const { data: doctorAccess = [], isLoading: doctorAccessLoading } = useQuery({
    queryKey: ['doctor-access'],
    queryFn: getDoctorAccess,
    staleTime: 5 * 60 * 1000,
    onError: () => {
      showToast('Failed to load doctor access', 'error')
    }
  })

  // Mutations for doctor access
  const grantAccessMutation = useMutation({
    mutationFn: grantDoctorAccess,
    onSuccess: () => {
      showToast('Access request sent successfully', 'success')
      queryClient.invalidateQueries(['doctor-access'])
      queryClient.invalidateQueries(['discovery-stats'])
    },
    onError: (error) => {
      showToast(error.response?.data?.detail || 'Failed to request access', 'error')
    }
  })

  const revokeAccessMutation = useMutation({
    mutationFn: revokeDoctorAccess,
    onSuccess: () => {
      showToast('Access revoked successfully', 'success')
      queryClient.invalidateQueries(['doctor-access'])
      queryClient.invalidateQueries(['discovery-stats'])
    },
    onError: (error) => {
      showToast(error.response?.data?.detail || 'Failed to revoke access', 'error')
    }
  })

  // Combined loading state
  const isLoading = profileLoading || medicinesLoading || reportsLoading || discoveryLoading || doctorAccessLoading

  // Stats calculation
  const stats = {
    activeMedicines: medicines?.filter((m) => m.status === 'current').length || 0,
    abnormalValues: reportsSummary?.abnormal_count || 0,
    totalReports: reportsSummary?.total_reports || 0,
    recentReports: reportsSummary?.recent_reports || [],
  }

  const handleGrantAccess = (doctorId) => {
    grantAccessMutation.mutate(doctorId)
  }

  const handleRevokeAccess = (accessId) => {
    revokeAccessMutation.mutate(accessId)
  }

  if (isLoading) {
    return <DashboardSkeleton />
  }

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome */}
      <div className="bg-gradient-to-r from-teal-700 via-teal-800 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-lg relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-10 -translate-y-10 w-64 h-64 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-teal-500/20 border border-teal-400/30 text-teal-200">
            <Activity className="w-3.5 h-3.5" /> Clinical Health Overview
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Welcome back, {profile?.full_name || user?.full_name || user?.name || 'Patient'}
          </h1>
          <p className="text-slate-300 text-xs sm:text-sm leading-relaxed max-w-2xl">
            Your personal medical intelligence workspace. Track lab parameter shifts over time, monitor medication regimens, and consult authorized clinical specialists.
          </p>
        </div>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Reports */}
        <div className="clinical-card p-5 flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Reports</p>
            <p className="text-2xl font-extrabold text-slate-900">{stats.totalReports}</p>
            <p className="text-[11px] text-slate-500 font-medium">Uploaded PDF & Image documents</p>
          </div>
          <div className="p-3 bg-teal-50 text-teal-600 rounded-xl border border-teal-100">
            <FileText className="w-6 h-6" />
          </div>
        </div>

        {/* Abnormal Biomarkers */}
        <div className="clinical-card p-5 flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Abnormal Flags</p>
            <p className="text-2xl font-extrabold text-rose-600">{stats.abnormalValues}</p>
            <p className="text-[11px] text-rose-600/80 font-medium">Out-of-range lab observations</p>
          </div>
          <div className="p-3 bg-rose-50 text-rose-600 rounded-xl border border-rose-100">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        {/* Active Regimens */}
        <div className="clinical-card p-5 flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Regimens</p>
            <p className="text-2xl font-extrabold text-slate-900">{stats.activeMedicines}</p>
            <p className="text-[11px] text-slate-500 font-medium">Current prescribed medications</p>
          </div>
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl border border-indigo-100">
            <Pill className="w-6 h-6" />
          </div>
        </div>

        {/* BMI / Clinical Metrics */}
        <div className="clinical-card p-5 flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Doctors</p>
            <p className="text-2xl font-extrabold text-emerald-600">{discovery.your_active_doctors}</p>
            <p className="text-[11px] text-slate-500 font-medium">Out of {discovery.total_doctors_on_platform} on platform</p>
          </div>
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl border border-emerald-100">
            <UserCheck className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Analytics Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link
          to="/analytics/health-summary"
          className="clinical-card p-6 flex items-start gap-4 group hover:border-teal-300 transition-all"
        >
          <div className="p-3 bg-teal-50 text-teal-600 rounded-xl border border-teal-100 group-hover:scale-105 transition-transform">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-slate-900 text-base group-hover:text-teal-700 transition-colors">
                Biomarker Health Insights
              </h3>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-teal-600 group-hover:translate-x-0.5 transition-all" />
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Explore interactive longitudinal charts, lab value changes across time, and abnormal parameter shifts.
            </p>
          </div>
        </Link>

        <Link
          to="/analytics/trends"
          className="clinical-card p-6 flex items-start gap-4 group hover:border-teal-300 transition-all"
        >
          <div className="p-3 bg-purple-50 text-purple-600 rounded-xl border border-purple-100 group-hover:scale-105 transition-transform">
            <Activity className="w-6 h-6" />
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-slate-900 text-base group-hover:text-purple-700 transition-colors">
                Health Trends & Trajectories
              </h3>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-purple-600 group-hover:translate-x-0.5 transition-all" />
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Track biomarker shifts, parameter trajectories, and longitudinal health changes over time.
            </p>
          </div>
        </Link>
      </div>

      {/* Main Content Grid: Recent Reports & Doctor Access Management */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Reports List (2 Cols) */}
        <div className="lg:col-span-2 clinical-card overflow-hidden flex flex-col">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-teal-600" />
              <h3 className="font-bold text-slate-900 text-sm sm:text-base">Recent Medical Reports</h3>
            </div>
            <Link
              to="/reports"
              className="text-xs font-semibold text-teal-700 hover:text-teal-800 flex items-center gap-1"
            >
              View All <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="divide-y divide-slate-100 flex-1">
            {stats.recentReports.length === 0 ? (
              <div className="p-8 text-center space-y-3">
                <FileText className="w-10 h-10 text-slate-300 mx-auto" />
                <p className="text-sm font-medium text-slate-600">No medical reports uploaded yet.</p>
                <Link
                  to="/reports"
                  className="clinical-button-primary inline-flex items-center gap-1 text-xs"
                >
                  <Plus className="w-3.5 h-3.5" /> Upload First Report
                </Link>
              </div>
            ) : (
              stats.recentReports.map((report) => (
                <Link
                  key={report.id}
                  to={`/reports/${report.id}`}
                  className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors group"
                >
                  <div className="space-y-1 min-w-0 pr-4">
                    <p className="text-sm font-semibold text-slate-900 group-hover:text-teal-700 transition-colors truncate">
                      {report.file_name}
                    </p>
                    <p className="text-[11px] text-slate-400 flex items-center gap-2">
                      <span>Uploaded {new Date(report.upload_date).toLocaleDateString()}</span>
                    </p>
                    {report.ai_summary && (
                      <p className="text-xs text-slate-600 line-clamp-1 italic">
                        &quot;{report.ai_summary}&quot;
                      </p>
                    )}
                  </div>
                  <span
                    className={
                      report.ocr_status === 'completed'
                        ? 'clinical-badge-normal'
                        : report.ocr_status === 'failed'
                        ? 'clinical-badge-high'
                        : 'clinical-badge-low'
                    }
                  >
                    {report.ocr_status === 'completed' && <CheckCircle2 className="w-3 h-3 mr-1" />}
                    {report.ocr_status === 'failed' && <XCircle className="w-3 h-3 mr-1" />}
                    {report.ocr_status === 'processing' && <Clock className="w-3 h-3 mr-1 animate-spin" />}
                    {report.ocr_status}
                  </span>
                </Link>
              ))
            )}
          </div>
        </div>

        {/* Doctor Access Care Sidebar (1 Col) */}
        <div className="clinical-card p-5 flex flex-col space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-indigo-600" />
              <h3 className="font-bold text-slate-900 text-sm sm:text-base">Care Team Access</h3>
            </div>
            <Link to="/find-doctors" className="text-xs font-semibold text-indigo-600 hover:text-indigo-800">
              Browse Directory
            </Link>
          </div>

          <p className="text-xs text-slate-500 leading-relaxed">
            Authorized doctors have explicit clinical access to your lab parameters and reports. You can revoke authorization at any time.
          </p>

          <div className="space-y-3 flex-1">
            {doctorAccess.length === 0 ? (
              <div className="p-6 text-center border border-dashed border-slate-200 rounded-xl bg-slate-50/50 space-y-2">
                <Stethoscope className="w-8 h-8 text-slate-300 mx-auto" />
                <p className="text-xs text-slate-600 font-medium">No active doctor access requests.</p>
                <Link to="/find-doctors" className="text-xs font-semibold text-teal-700 hover:underline block">
                  Find & Request Doctor Access
                </Link>
              </div>
            ) : (
              doctorAccess.map((row) => {
                const status = row.status === 'accepted' ? 'approved' : row.status
                const isApproved = status === 'approved'
                const isPending = status === 'pending'

                return (
                  <div
                    key={row.id}
                    className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-xs font-bold text-slate-900">
                          {row.doctor_full_name || row.doctor_email || `Doctor #${row.doctor_id}`}
                        </p>
                        <p className="text-[11px] text-slate-500">
                          {row.doctor_category ? `${row.doctor_category} · ${row.doctor_specialty || ''}` : 'Specialist'}
                        </p>
                      </div>
                      <span
                        className={
                          isApproved
                            ? 'clinical-badge-normal'
                            : isPending
                            ? 'clinical-badge-low'
                            : 'clinical-badge-high'
                        }
                      >
                        {status}
                      </span>
                    </div>

                    <div className="pt-1 flex justify-end">
                      {(isApproved || isPending) && (
                        <button
                          type="button"
                          disabled={revokeAccessMutation.isLoading}
                          onClick={() => handleRevokeAccess(row.id)}
                          className="px-2.5 py-1 text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 rounded-lg transition-colors disabled:opacity-50"
                        >
                          {revokeAccessMutation.isLoading ? 'Revoking...' : 'Revoke Access'}
                        </button>
                      )}

                      {(status === 'rejected' || status === 'revoked') && (
                        <button
                          type="button"
                          disabled={grantAccessMutation.isLoading}
                          onClick={() => handleGrantAccess(row.doctor_id)}
                          className="px-2.5 py-1 text-[11px] font-semibold bg-teal-50 text-teal-700 border border-teal-200 hover:bg-teal-100 rounded-lg transition-colors disabled:opacity-50"
                        >
                          {grantAccessMutation.isLoading ? 'Requesting...' : 'Grant Access'}
                        </button>
                      )}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
