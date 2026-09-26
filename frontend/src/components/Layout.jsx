import { useState } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  FileText,
  Home,
  Pill,
  User,
  LogOut,
  Stethoscope,
  Search,
  TrendingUp,
  Activity,
  Menu,
  X,
  ShieldCheck,
  ChevronRight,
  PieChart
} from 'lucide-react'
import AIAssistantModal from './AIAssistantModal'
import DoctorNotificationBell from './DoctorNotificationBell'

export default function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isDoctor = user?.role === 'doctor'

  const patientNav = [
    { path: '/dashboard', label: 'Dashboard', icon: Home },
    { path: '/reports', label: 'My Reports', icon: FileText },
    { path: '/analytics/health-summary', label: 'Health Insights', icon: TrendingUp },
    { path: '/analytics/trends', label: 'Health Trends', icon: PieChart },
    { path: '/medicines', label: 'Medications', icon: Pill },
    { path: '/find-doctors', label: 'Find Doctors', icon: Search },
    { path: '/profile', label: 'My Profile', icon: User },
  ]

  const doctorNav = [
    { path: '/dashboard', label: 'Dashboard', icon: Home },
    { path: '/doctor/patients', label: 'My Patients', icon: User },
    { path: '/medical-dashboard', label: 'Clinical Analytics', icon: TrendingUp },
    { path: '/doctor/profile', label: 'Doctor Profile', icon: Stethoscope },
  ]

  const navItems = isDoctor ? doctorNav : patientNav

  const getPageTitle = () => {
    const current = navItems.find((item) => item.path === location.pathname)
    if (current) return current.label
    if (location.pathname.startsWith('/reports/')) return 'Report Details'
    if (location.pathname.startsWith('/doctor/patient/')) return 'Patient Inspection'
    return 'Clinical Platform'
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar - Desktop */}
      <aside className="hidden lg:flex flex-col w-64 bg-slate-900 text-slate-300 border-r border-slate-800 shrink-0 sticky top-0 h-screen">
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800 flex items-center gap-3">
          <div className="p-2 bg-teal-500/10 border border-teal-500/20 rounded-xl text-teal-400">
            <Activity className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="font-bold text-slate-100 text-base leading-tight tracking-tight">
              MedPulse AI
            </h1>
            <p className="text-[11px] text-slate-400 font-medium">Clinical Intelligence</p>
          </div>
        </div>

        {/* Role Badge */}
        <div className="px-5 py-3 border-b border-slate-800/60 bg-slate-950/40 flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Workspace
          </span>
          <span
            className={`inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full font-semibold ${
              isDoctor
                ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                : 'bg-teal-500/20 text-teal-300 border border-teal-500/30'
            }`}
          >
            <ShieldCheck className="w-3 h-3" />
            {isDoctor ? 'Physician Care' : 'Patient Access'}
          </span>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive =
              location.pathname === item.path ||
              (item.path !== '/dashboard' && location.pathname.startsWith(item.path))
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group ${
                  isActive
                    ? 'bg-teal-600 text-white shadow-sm font-semibold'
                    : 'text-slate-400 hover:bg-slate-800/80 hover:text-slate-200'
                }`}
              >
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? 'text-white' : 'text-slate-400 group-hover:text-teal-400'
                  }`}
                />
                <span className="flex-1">{item.label}</span>
                {isActive && <ChevronRight className="w-4 h-4 text-white/80" />}
              </Link>
            )
          })}
        </nav>

        {/* User Info & Logout */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-xl bg-teal-500/20 border border-teal-500/30 text-teal-300 flex items-center justify-center font-bold text-sm shrink-0">
              {(user?.full_name || user?.name || user?.email || 'P').charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-bold text-slate-200 truncate">
                {user?.full_name || user?.name || 'Patient'}
              </p>
              <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-slate-800/80 hover:bg-rose-950/60 text-slate-300 hover:text-rose-300 border border-slate-700 hover:border-rose-800/60 text-xs font-medium rounded-lg transition-all"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Layout Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Navbar */}
        <header className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-slate-200/80 px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="lg:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>

            <div>
              <h2 className="text-lg font-bold text-slate-900 tracking-tight leading-none">
                {getPageTitle()}
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {isDoctor ? 'Clinical Decision Support Workspace' : 'Personal Medical Health Intelligence'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {isDoctor && <DoctorNotificationBell />}
            <span className="hidden sm:inline-flex items-center gap-1.5 text-xs bg-slate-100 border border-slate-200 text-slate-700 px-3 py-1.5 rounded-full font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              API Connected
            </span>
          </div>
        </header>

        {/* Mobile Navigation Overlay */}
        {mobileOpen && (
          <div className="lg:hidden fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-sm flex">
            <div className="w-64 bg-slate-900 text-slate-300 h-full flex flex-col p-4 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2 text-slate-100 font-bold">
                  <Activity className="w-5 h-5 text-teal-400" />
                  <span>MedPulse AI</span>
                </div>
                <button onClick={() => setMobileOpen(false)} className="text-slate-400 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <nav className="flex-1 space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname === item.path
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileOpen(false)}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium ${
                        isActive ? 'bg-teal-600 text-white' : 'text-slate-400 hover:bg-slate-800'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      {item.label}
                    </Link>
                  )
                })}
              </nav>

              <button
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-rose-900/40 text-rose-300 border border-rose-800 rounded-lg text-xs font-medium"
              >
                <LogOut className="w-3.5 h-3.5" />
                Sign Out
              </button>
            </div>
            <div className="flex-1" onClick={() => setMobileOpen(false)} />
          </div>
        )}

        {/* Content Outlet Container */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>

      {/* Floating AI Assistant Integration for Patients */}
      {user?.role === 'patient' && (
        <AIAssistantModal role="patient" patientName={user?.full_name || user?.name} />
      )}
    </div>
  )
}
