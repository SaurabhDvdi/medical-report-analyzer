import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../components/Toast'
import { Activity, ShieldCheck, ArrowRight, Lock, Mail } from 'lucide-react'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const { showToast } = useToast()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    const result = await login(email, password)
    setLoading(false)

    if (result.success) {
      showToast('Welcome back! Authentication successful.', 'success')
      navigate('/dashboard')
    } else {
      showToast(result.error || 'Login failed. Please check credentials.', 'error')
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Glow ambient background element */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md space-y-4 text-center relative z-10">
        <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-2xl bg-teal-500/10 border border-teal-500/20 text-teal-400 font-bold text-base">
          <Activity className="w-6 h-6 animate-pulse" />
          <span>MedPulse AI Platform</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
          Sign In to Clinical Portal
        </h2>
        <p className="text-xs text-slate-400 max-w-xs mx-auto">
          Grounded medical report analytics & secure physician access workspace
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6">
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="email"
                  required
                  disabled={loading}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@healthcare.org"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Account Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="password"
                  required
                  disabled={loading}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white font-semibold text-xs rounded-xl shadow-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <span>Verifying Credentials...</span>
              ) : (
                <>
                  <span>Sign In to Workspace</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="pt-4 border-t border-slate-800 text-center space-y-2">
            <p className="text-xs text-slate-400">
              New to MedPulse AI?{' '}
              <Link to="/register" className="font-semibold text-teal-400 hover:text-teal-300 transition-colors">
                Create an account
              </Link>
            </p>
            <div className="flex items-center justify-center gap-1.5 text-[11px] text-slate-500">
              <ShieldCheck className="w-3.5 h-3.5 text-teal-500" />
              <span>HIPAA Compliant & Encrypted Portal</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
