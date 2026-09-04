import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../utils/api'
import { getProfile } from '../services/userService'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../components/Toast'
import { safeFormatNumber } from '../utils/numeric'
import {
  User,
  Activity,
  Heart,
  AlertTriangle,
  PhoneCall,
  Save,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Mail,
  Calendar,
  Lock,
  FileText,
  Loader,
  Check
} from 'lucide-react'
import { FormSkeleton } from '../components/Skeletons'

function getPatientInitials(name) {
  if (!name) return 'P'
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return 'P'
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

export default function PatientProfile() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const queryClient = useQueryClient()

  const [profile, setProfile] = useState({
    age: '',
    gender: '',
    height_cm: '',
    weight_kg: '',
    blood_group: '',
    allergies: '',
    chronic_conditions: '',
    lifestyle_indicators: '',
    emergency_contact_name: '',
    emergency_contact_phone: ''
  })

  const [bmi, setBmi] = useState(null)
  const [validationErrors, setValidationErrors] = useState({})
  const [successBanner, setSuccessBanner] = useState('')

  // Server Profile Query
  const { data: serverProfile, isLoading: loading } = useQuery({
    queryKey: ['profile'],
    queryFn: getProfile,
    staleTime: 5 * 60 * 1000,
  })

  // Populate local form state when server profile resolves
  useEffect(() => {
    if (serverProfile && serverProfile.exists) {
      setProfile({
        age: serverProfile.age ?? '',
        gender: serverProfile.gender ?? '',
        height_cm: serverProfile.height_cm ?? '',
        weight_kg: serverProfile.weight_kg ?? '',
        blood_group: serverProfile.blood_group ?? '',
        allergies: serverProfile.allergies ?? '',
        chronic_conditions: serverProfile.chronic_conditions ?? '',
        lifestyle_indicators: serverProfile.lifestyle_indicators ?? '',
        emergency_contact_name: serverProfile.emergency_contact_name ?? '',
        emergency_contact_phone: serverProfile.emergency_contact_phone ?? ''
      })
      if (serverProfile.bmi) {
        setBmi(serverProfile.bmi)
      }
    }
  }, [serverProfile])

  // Recalculate derived client-side BMI for immediate feedback
  useEffect(() => {
    if (profile.height_cm && profile.weight_kg) {
      const height_m = parseFloat(profile.height_cm) / 100
      const weight_kg = parseFloat(profile.weight_kg)
      if (height_m > 0 && weight_kg > 0) {
        const calculatedBmi = weight_kg / (height_m * height_m)
        setBmi(calculatedBmi)
      } else {
        setBmi(null)
      }
    } else {
      setBmi(serverProfile?.bmi || null)
    }
  }, [profile.height_cm, profile.weight_kg, serverProfile])

  // Profile Save Mutation
  const saveMutation = useMutation({
    mutationFn: (payload) => api.put('/api/patient/profile', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      showToast('Profile updated successfully!', 'success')
      setSuccessBanner('Profile updated successfully.')
      setTimeout(() => setSuccessBanner(''), 4000)
    },
    onError: (error) => {
      const errMsg = error.response?.data?.detail || 'Error updating profile. Please try again.'
      showToast(errMsg, 'error')
      console.error('Error updating profile:', error)
    }
  })

  // Basic UI Input Validation
  const validateForm = () => {
    const errors = {}
    if (profile.age !== '' && profile.age !== null) {
      const ageNum = parseInt(profile.age, 10)
      if (isNaN(ageNum) || ageNum < 1 || ageNum > 120) {
        errors.age = 'Age must be between 1 and 120'
      }
    }
    if (profile.height_cm !== '' && profile.height_cm !== null) {
      const hNum = parseFloat(profile.height_cm)
      if (isNaN(hNum) || hNum < 30 || hNum > 300) {
        errors.height_cm = 'Height must be between 30 and 300 cm'
      }
    }
    if (profile.weight_kg !== '' && profile.weight_kg !== null) {
      const wNum = parseFloat(profile.weight_kg)
      if (isNaN(wNum) || wNum < 2 || wNum > 500) {
        errors.weight_kg = 'Weight must be between 2 and 500 kg'
      }
    }
    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setSuccessBanner('')
    if (!validateForm()) {
      showToast('Please fix input errors before saving.', 'error')
      return
    }

    const payload = {
      ...profile,
      age: profile.age !== '' && profile.age !== null ? parseInt(profile.age, 10) : null,
      height_cm: profile.height_cm !== '' && profile.height_cm !== null ? parseFloat(profile.height_cm) : null,
      weight_kg: profile.weight_kg !== '' && profile.weight_kg !== null ? parseFloat(profile.weight_kg) : null
    }
    saveMutation.mutate(payload)
  }

  const saving = saveMutation.isPending

  // Calculate Profile Completeness
  const calculateCompleteness = () => {
    const fields = [
      profile.age,
      profile.gender,
      profile.height_cm,
      profile.weight_kg,
      profile.blood_group,
      profile.allergies,
      profile.chronic_conditions,
      profile.lifestyle_indicators,
      profile.emergency_contact_name,
      profile.emergency_contact_phone
    ]
    const filled = fields.filter((f) => f !== '' && f !== null && f !== undefined).length
    return Math.round((filled / fields.length) * 100)
  }

  const completenessPct = calculateCompleteness()

  const getBmiCategory = (val) => {
    if (!val) return ''
    if (val < 18.5) return 'Underweight'
    if (val < 25) return 'Normal Weight'
    if (val < 30) return 'Overweight'
    return 'Obese'
  }

  if (loading) {
    return <FormSkeleton />
  }

  // Resolve Real Patient Name & Identity
  const patientName = user?.full_name || user?.name || serverProfile?.full_name || 'Patient'
  const userEmail = user?.email || 'patient@medpulse.ai'
  const initials = getPatientInitials(patientName)

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-32">
      {/* 1. Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            My Profile
          </h1>
          <p className="text-xs text-slate-500 mt-1 font-medium">
            Manage your personal information and health profile.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 text-xs bg-slate-100 border border-slate-200 text-slate-700 px-3 py-1.5 rounded-full font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            API Connected
          </span>
        </div>
      </div>

      {/* Success Notification Banner */}
      {successBanner && (
        <div className="p-4 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200/80 flex items-center gap-2 shadow-xs animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successBanner}</span>
        </div>
      )}

      {/* 2. Patient Identity Card (White Hero Surface matching reference) */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-2xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex items-center gap-5">
          {/* Avatar circle */}
          <div className="w-16 h-16 rounded-full bg-[#0F766E] text-white flex items-center justify-center font-extrabold text-xl shadow-md shrink-0">
            {initials}
          </div>

          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2.5">
              <h2 className="text-xl font-bold text-slate-900 tracking-tight leading-tight">
                {patientName}
              </h2>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                <Check className="w-3 h-3 text-emerald-600" />
                Patient
              </span>
            </div>

            <p className="text-xs text-slate-500 flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5 text-slate-400" />
              <span>{userEmail}</span>
            </p>

            {/* Profile Completeness Bar */}
            <div className="pt-1 space-y-1 max-w-xs">
              <div className="flex items-center justify-between text-[11px] font-semibold text-slate-600">
                <span>Profile completeness</span>
                <span className="font-bold text-slate-900">{completenessPct}%</span>
              </div>
              <div className="w-48 bg-slate-100 h-2 rounded-full overflow-hidden border border-slate-200">
                <div
                  className="bg-[#0F766E] h-full rounded-full transition-all duration-500"
                  style={{ width: `${completenessPct}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Timestamp */}
        <div className="text-right text-xs text-slate-500 space-y-1">
          <p className="flex items-center justify-end gap-1 font-medium text-slate-400 text-[11px]">
            <Calendar className="w-3.5 h-3.5" /> Last updated
          </p>
          <p className="font-semibold text-slate-700">Aug 27, 2025</p>
          <p className="text-[11px] text-slate-400">11:24 AM</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 3. Middle Section: Personal Details + Physical Health + Security Info Card */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          {/* Personal Details Card (5 cols) */}
          <div className="xl:col-span-5 bg-white p-5 rounded-2xl border border-slate-200/90 shadow-2xs flex flex-col justify-between space-y-4">
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
                <User className="w-4 h-4 text-[#0F766E]" />
                <h3 className="font-bold text-slate-900 text-sm">Personal Details</h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Age</label>
                  <input
                    type="number"
                    min="1"
                    max="120"
                    className={`clinical-input text-xs ${validationErrors.age ? 'border-rose-400 focus:ring-rose-400' : ''}`}
                    placeholder="34"
                    value={profile.age}
                    onChange={(e) => setProfile({ ...profile, age: e.target.value })}
                  />
                  {validationErrors.age && (
                    <p className="text-[11px] text-rose-600 font-medium mt-1">{validationErrors.age}</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Biological Gender</label>
                  <select
                    className="clinical-input text-xs"
                    value={profile.gender}
                    onChange={(e) => setProfile({ ...profile, gender: e.target.value })}
                  >
                    <option value="">Select</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Blood Group</label>
                  <select
                    className="clinical-input text-xs font-bold"
                    value={profile.blood_group}
                    onChange={(e) => setProfile({ ...profile, blood_group: e.target.value })}
                  >
                    <option value="">Select</option>
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                  </select>
                </div>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 font-medium pt-2 border-t border-slate-50">
              Keep your personal details up to date.
            </p>
          </div>

          {/* Physical Health Card (5 cols) */}
          <div className="xl:col-span-5 bg-white p-5 rounded-2xl border border-slate-200/90 shadow-2xs flex flex-col justify-between space-y-4">
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
                <Activity className="w-4 h-4 text-[#0F766E]" />
                <h3 className="font-bold text-slate-900 text-sm">Physical Health</h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-center">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Height (cm)</label>
                  <input
                    type="number"
                    step="0.1"
                    className={`clinical-input text-xs ${validationErrors.height_cm ? 'border-rose-400 focus:ring-rose-400' : ''}`}
                    placeholder="175"
                    value={profile.height_cm}
                    onChange={(e) => setProfile({ ...profile, height_cm: e.target.value })}
                  />
                  {validationErrors.height_cm && (
                    <p className="text-[11px] text-rose-600 font-medium mt-1">{validationErrors.height_cm}</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Weight (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    className={`clinical-input text-xs ${validationErrors.weight_kg ? 'border-rose-400 focus:ring-rose-400' : ''}`}
                    placeholder="72"
                    value={profile.weight_kg}
                    onChange={(e) => setProfile({ ...profile, weight_kg: e.target.value })}
                  />
                  {validationErrors.weight_kg && (
                    <p className="text-[11px] text-rose-600 font-medium mt-1">{validationErrors.weight_kg}</p>
                  )}
                </div>

                {/* Calculated BMI embedded Box */}
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200/80 text-center space-y-0.5">
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Calculated BMI</p>
                  <p className="text-lg font-extrabold text-slate-900">
                    {bmi ? safeFormatNumber(bmi, 1) : '—'}
                  </p>
                  {bmi ? (
                    <span
                      className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        bmi < 18.5
                          ? 'bg-sky-100 text-sky-800'
                          : bmi < 25
                          ? 'bg-emerald-100 text-emerald-800'
                          : bmi < 30
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-rose-100 text-rose-800'
                      }`}
                    >
                      {getBmiCategory(bmi)}
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-400 italic">Enter measurements</span>
                  )}
                </div>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 font-medium flex items-center gap-1 pt-2 border-t border-slate-50">
              <span className="text-[#0F766E] font-bold">ⓘ</span> BMI is calculated from your height and weight.
            </p>
          </div>

          {/* Privacy Callout Card (2 cols) */}
          <div className="xl:col-span-2 bg-white p-5 rounded-2xl border border-slate-200/90 shadow-2xs flex flex-col justify-between space-y-3">
            <div className="space-y-2">
              <div className="p-2 bg-teal-50 text-[#0F766E] rounded-xl w-max border border-teal-100">
                <Lock className="w-5 h-5" />
              </div>
              <h4 className="font-bold text-slate-900 text-xs leading-tight">Your Information is Private</h4>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                Your information is private and secure. Changes are saved to your personal health profile.
              </p>
            </div>
          </div>
        </div>

        {/* 4. Clinical History Card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-2xs space-y-5">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Heart className="w-4 h-4 text-[#0F766E]" />
            <h3 className="font-bold text-slate-900 text-sm sm:text-base">Clinical Information</h3>
          </div>

          <div className="space-y-4">
            {/* Allergies & Sensitivities */}
            <div className="bg-amber-50/30 rounded-xl p-4 border border-amber-200/70 space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  <span>Allergies & Sensitivities</span>
                </label>
                <span className="text-[10px] font-semibold text-amber-800 bg-amber-100 px-2.5 py-0.5 rounded-md border border-amber-200">
                  {profile.allergies?.trim() ? 'Allergies Recorded' : 'No allergy information provided'}
                </span>
              </div>
              <textarea
                rows="2"
                className="clinical-input text-xs bg-white border-slate-200 focus:border-[#0F766E] focus:ring-[#0F766E]"
                placeholder="e.g. Penicillin, Peanuts, Latex"
                value={profile.allergies}
                onChange={(e) => setProfile({ ...profile, allergies: e.target.value })}
              />
              <p className="text-[11px] text-slate-400">List all known drug, food, or environmental allergies.</p>
            </div>

            {/* Chronic Medical Conditions */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-[#0F766E]" />
                <span>Chronic Medical Conditions</span>
              </label>
              <textarea
                rows="2"
                className="clinical-input text-xs bg-white"
                placeholder="e.g. Type 2 Diabetes, Hypertension, Asthma"
                value={profile.chronic_conditions}
                onChange={(e) => setProfile({ ...profile, chronic_conditions: e.target.value })}
              />
              <p className="text-[11px] text-slate-400">List diagnosed chronic medical conditions.</p>
            </div>

            {/* Lifestyle Indicators */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <User className="w-4 h-4 text-[#0F766E]" />
                <span>Lifestyle Indicators</span>
              </label>
              <textarea
                rows="2"
                className="clinical-input text-xs bg-white"
                placeholder="e.g. Non-smoker; 3x weekly exercise, low sodium diet"
                value={profile.lifestyle_indicators}
                onChange={(e) => setProfile({ ...profile, lifestyle_indicators: e.target.value })}
              />
              <p className="text-[11px] text-slate-400">e.g. Diet, exercise, smoking, alcohol, sleep, etc.</p>
            </div>
          </div>
        </div>

        {/* 5. Emergency Contact Card */}
        <div className="bg-amber-50/30 rounded-2xl p-6 border border-amber-200/80 space-y-4 shadow-2xs">
          <div className="flex items-center gap-2 border-b border-amber-200/60 pb-3">
            <PhoneCall className="w-4 h-4 text-amber-600" />
            <h3 className="font-bold text-slate-900 text-sm sm:text-base">Emergency Contact</h3>
          </div>
          <p className="text-xs text-slate-600 font-medium">
            {profile.emergency_contact_name || profile.emergency_contact_phone
              ? 'A person your care team can contact in an emergency.'
              : 'No emergency contact provided yet. Please add a trusted contact.'}
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Contact Name</label>
              <input
                type="text"
                className="clinical-input text-xs bg-white"
                placeholder="e.g. Rohit Sharma"
                value={profile.emergency_contact_name}
                onChange={(e) => setProfile({ ...profile, emergency_contact_name: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Contact Phone</label>
              <input
                type="text"
                className="clinical-input text-xs bg-white"
                placeholder="e.g. +91 98765 43210"
                value={profile.emergency_contact_phone}
                onChange={(e) => setProfile({ ...profile, emergency_contact_phone: e.target.value })}
              />
            </div>
          </div>
          <p className="text-[11px] text-slate-400">Ensure your emergency contact information is always current.</p>
        </div>

        {/* 6. Save Action Bar */}
        <div className="bg-teal-50/40 border border-teal-100 p-4 sm:p-5 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4 shadow-2xs">
          <div className="flex items-center gap-2 text-xs text-slate-600 font-medium">
            <Lock className="w-4 h-4 text-[#0F766E] shrink-0" />
            <div>
              <p className="font-semibold text-slate-800">Your information is private and secure.</p>
              <p className="text-[11px] text-slate-500">Changes are saved to your personal health profile.</p>
            </div>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="w-full sm:w-auto px-6 py-2.5 bg-[#0F766E] hover:bg-teal-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-xs transition-all flex items-center justify-center gap-2 cursor-pointer shrink-0"
          >
            {saving ? (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                <span>Saving Changes...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Save Changes</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
