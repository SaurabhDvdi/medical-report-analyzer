import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import api from '../utils/api'
import { Activity, ShieldCheck, ArrowRight, User, Stethoscope } from 'lucide-react'

export default function Register() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    fullName: '',
    role: 'patient',
    doctor_category_id: '',
    doctor_specialty_id: '',
    useNewSpecialty: false,
    new_specialty_name: '',
    new_specialty_description: '',
  })
  const [categories, setCategories] = useState([])
  const [specialties, setSpecialties] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const res = await api.get('/api/categories')
        setCategories(res.data)
      } catch (e) {
        console.error(e)
      }
    }
    loadCategories()
  }, [])

  useEffect(() => {
    const cid = formData.doctor_category_id
    if (!cid || formData.role !== 'doctor') {
      setSpecialties([])
      return
    }
    const load = async () => {
      try {
        const res = await api.get('/api/specialties', { params: { category_id: cid } })
        setSpecialties(res.data)
      } catch (e) {
        console.error(e)
        setSpecialties([])
      }
    }
    load()
  }, [formData.doctor_category_id, formData.role])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    let doctorPayload = null
    if (formData.role === 'doctor') {
      if (!formData.doctor_category_id) {
        setError('Please select a clinical category.')
        setLoading(false)
        return
      }
      doctorPayload = {
        doctor_category_id: Number(formData.doctor_category_id),
      }
      if (formData.useNewSpecialty) {
        if (!formData.new_specialty_name.trim()) {
          setError('Enter a name for your new specialty.')
          setLoading(false)
          return
        }
        doctorPayload.new_specialty_name = formData.new_specialty_name.trim()
        doctorPayload.new_specialty_description =
          formData.new_specialty_description.trim() || null
      } else {
        if (!formData.doctor_specialty_id) {
          setError('Please select a specialty or choose “Add new specialty”.')
          setLoading(false)
          return
        }
        doctorPayload.doctor_specialty_id = Number(formData.doctor_specialty_id)
      }
    }

    const result = await register(
      formData.email,
      formData.password,
      formData.fullName,
      formData.role,
      doctorPayload
    )
    setLoading(false)

    if (result.success) {
      navigate('/dashboard')
    } else {
      setError(result.error)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md space-y-3 text-center relative z-10">
        <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-2xl bg-teal-500/10 border border-teal-500/20 text-teal-400 font-bold text-base">
          <Activity className="w-6 h-6 animate-pulse" />
          <span>MedPulse AI Platform</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
          Create Clinical Account
        </h2>
        <p className="text-xs text-slate-400">
          Register as a Patient or Licensed Healthcare Provider
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-5">
          {error && (
            <div className="p-3.5 bg-rose-950/80 border border-rose-800 text-rose-300 text-xs rounded-xl">
              {error}
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Full Name</label>
              <input
                type="text"
                required
                value={formData.fullName}
                onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                placeholder="Dr. Jane Doe or John Smith"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Email Address</label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="name@domain.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Password</label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="Create strong password"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            {/* Role Toggle Selector */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Select Account Role</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setFormData({
                      ...formData,
                      role: 'patient',
                      doctor_category_id: '',
                      doctor_specialty_id: '',
                      useNewSpecialty: false,
                      new_specialty_name: '',
                      new_specialty_description: '',
                    })
                  }
                  className={`p-3 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                    formData.role === 'patient'
                      ? 'bg-teal-600 text-white border-teal-500 shadow-sm'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-800/50'
                  }`}
                >
                  <User className="w-4 h-4" />
                  <span>Patient</span>
                </button>

                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, role: 'doctor' })}
                  className={`p-3 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                    formData.role === 'doctor'
                      ? 'bg-indigo-600 text-white border-indigo-500 shadow-sm'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-800/50'
                  }`}
                >
                  <Stethoscope className="w-4 h-4" />
                  <span>Doctor</span>
                </button>
              </div>
            </div>

            {/* Doctor Specialty Extra Inputs */}
            {formData.role === 'doctor' && (
              <div className="p-4 bg-slate-950 rounded-xl border border-indigo-900/60 space-y-3">
                <p className="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                  <Stethoscope className="w-3.5 h-3.5" /> Physician Category Credentials
                </p>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">Category</label>
                  <select
                    required
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200"
                    value={formData.doctor_category_id}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        doctor_category_id: e.target.value,
                        doctor_specialty_id: '',
                      })
                    }
                  >
                    <option value="">Select Category...</option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.useNewSpecialty}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        useNewSpecialty: e.target.checked,
                        doctor_specialty_id: '',
                        new_specialty_name: '',
                        new_specialty_description: '',
                      })
                    }
                  />
                  <span>Add new custom specialty</span>
                </label>

                {!formData.useNewSpecialty ? (
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-400 mb-1">Specialty</label>
                    <select
                      required={!!formData.doctor_category_id}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 disabled:opacity-50"
                      value={formData.doctor_specialty_id}
                      onChange={(e) =>
                        setFormData({ ...formData, doctor_specialty_id: e.target.value })
                      }
                      disabled={!formData.doctor_category_id}
                    >
                      <option value="">
                        {formData.doctor_category_id ? 'Select Specialty...' : 'Choose Category First'}
                      </option>
                      {specialties.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                        </option>
                      ))}
                    </select>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-400 mb-1">Specialty Name</label>
                      <input
                        type="text"
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200"
                        placeholder="e.g. Pediatric Cardiology"
                        value={formData.new_specialty_name}
                        onChange={(e) =>
                          setFormData({ ...formData, new_specialty_name: e.target.value })
                        }
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-400 mb-1">Description (Optional)</label>
                      <textarea
                        rows={2}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200"
                        value={formData.new_specialty_description}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            new_specialty_description: e.target.value,
                          })
                        }
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs rounded-xl shadow-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <span>Registering Account...</span>
              ) : (
                <>
                  <span>Complete Account Registration</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="pt-3 border-t border-slate-800 text-center space-y-2">
            <p className="text-xs text-slate-400">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold text-teal-400 hover:text-teal-300">
                Sign in
              </Link>
            </p>
            <div className="flex items-center justify-center gap-1.5 text-[11px] text-slate-500">
              <ShieldCheck className="w-3.5 h-3.5 text-teal-500" />
              <span>Grounded Decision Support Platform</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
