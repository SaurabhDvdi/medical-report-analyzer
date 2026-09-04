import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../utils/api'
import { useAuth } from '../contexts/AuthContext'
import {
  Save,
  User,
  GraduationCap,
  Building,
  FileText,
  CheckCircle2,
  AlertCircle,
  Stethoscope,
  Mail,
  ShieldCheck,
  Calendar,
  Lock,
  Loader,
  Check,
  Award,
  Shield
} from 'lucide-react'
import { FormSkeleton } from '../components/Skeletons'

function getDoctorInitials(name) {
  if (!name) return 'DR'
  const cleanName = name.replace(/^(dr|doctor)\.?\s*/i, '').trim()
  const parts = cleanName.split(/\s+/).filter(Boolean)
  if (parts.length === 0) return 'DR'
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

export default function DoctorProfile() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [profile, setProfile] = useState({
    degrees: '',
    specialization: '',
    experience_years: '',
    license_number: '',
    license_issuing_authority: '',
    clinic_name: '',
    clinic_address: '',
    clinic_phone: '',
    clinic_email: '',
    bio: ''
  })
  const [message, setMessage] = useState('')

  // Doctor profile query
  const { data: serverProfile, isLoading: loading } = useQuery({
    queryKey: ['doctor-profile'],
    queryFn: () => api.get('/api/doctor/profile').then((res) => res.data),
    staleTime: 5 * 60 * 1000,
  })

  useEffect(() => {
    if (serverProfile && serverProfile.exists) {
      setProfile({
        degrees: serverProfile.degrees || '',
        specialization: serverProfile.specialization || '',
        experience_years: serverProfile.experience_years || '',
        license_number: serverProfile.license_number || '',
        license_issuing_authority: serverProfile.license_issuing_authority || '',
        clinic_name: serverProfile.clinic_name || '',
        clinic_address: serverProfile.clinic_address || '',
        clinic_phone: serverProfile.clinic_phone || '',
        clinic_email: serverProfile.clinic_email || '',
        bio: serverProfile.bio || ''
      })
    }
  }, [serverProfile])

  // Save Mutation
  const saveMutation = useMutation({
    mutationFn: (payload) => api.put('/api/doctor/profile', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor-profile'] })
      setMessage('Doctor profile updated successfully!')
      setTimeout(() => setMessage(''), 4000)
    },
    onError: (error) => {
      setMessage(error.response?.data?.detail || 'Error updating doctor profile. Please try again.')
      console.error('Error updating profile:', error)
    }
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    setMessage('')
    saveMutation.mutate(profile)
  }

  const saving = saveMutation.isPending

  if (loading) {
    return <FormSkeleton />
  }

  // Resolve Authoritative Doctor Identity
  const doctorName = user?.full_name || user?.name || serverProfile?.full_name || 'Doctor'
  const formattedDoctorTitle = doctorName.toLowerCase().startsWith('dr') ? doctorName : `Dr. ${doctorName}`
  const userEmail = user?.email || 'doctor@medpulse.ai'
  const initials = getDoctorInitials(doctorName)

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-32">
      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Stethoscope className="w-6 h-6 text-[#0F766E]" />
            Doctor Profile
          </h1>
          <p className="text-xs text-slate-500 mt-1 font-medium">
            Manage your professional profile and account information.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 text-xs bg-slate-100 border border-slate-200 text-slate-700 px-3 py-1.5 rounded-full font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            API Connected
          </span>
        </div>
      </div>

      {/* Success / Notification Banner */}
      {message && (
        <div
          className={`p-4 rounded-xl text-xs font-semibold flex items-center gap-2 shadow-2xs ${
            message.includes('success')
              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200/80'
              : 'bg-rose-50 text-rose-800 border border-rose-200/80'
          }`}
        >
          {message.includes('success') ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          )}
          <span>{message}</span>
        </div>
      )}

      {/* 2. Doctor Identity Hero Card */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-2xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex items-center gap-5">
          {/* Avatar circle */}
          <div className="w-16 h-16 rounded-full bg-[#0F766E] text-white flex items-center justify-center font-extrabold text-xl shadow-md shrink-0">
            {initials}
          </div>

          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2.5">
              <h2 className="text-xl font-bold text-slate-900 tracking-tight leading-tight">
                {formattedDoctorTitle}
              </h2>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                <Check className="w-3 h-3 text-emerald-600" />
                Physician
              </span>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-600 flex-wrap font-medium">
              <span className="text-[#0F766E] font-bold">
                {profile.degrees || 'Medical Practitioner'}
              </span>
              {profile.specialization && (
                <>
                  <span className="text-slate-300">·</span>
                  <span className="text-slate-700">{profile.specialization}</span>
                </>
              )}
            </div>

            <p className="text-xs text-slate-500 flex items-center gap-1.5 pt-0.5">
              <Mail className="w-3.5 h-3.5 text-slate-400" />
              <span>{userEmail}</span>
            </p>
          </div>
        </div>

        {/* Right Credentials Info */}
        <div className="text-right text-xs text-slate-500 space-y-1 border-t md:border-t-0 md:border-l border-slate-100 pt-3 md:pt-0 md:pl-6">
          <p className="flex items-center justify-start md:justify-end gap-1 font-medium text-slate-400 text-[11px]">
            <Award className="w-3.5 h-3.5 text-[#0F766E]" /> Registration License
          </p>
          <p className="font-bold text-slate-800">{profile.license_number || 'Verification Active'}</p>
          <p className="text-[11px] text-slate-400">{profile.license_issuing_authority || 'State Medical Board'}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 3. Professional Information Section */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-2xs space-y-5">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <GraduationCap className="w-4 h-4 text-[#0F766E]" />
            <h3 className="font-bold text-slate-900 text-sm sm:text-base">Professional Information</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Degrees & Credentials</label>
              <input
                type="text"
                className="clinical-input text-xs bg-white"
                placeholder="e.g. MBBS, MD (Internal Medicine)"
                value={profile.degrees}
                onChange={(e) => setProfile({ ...profile, degrees: e.target.value })}
              />
              <p className="text-[11px] text-slate-400 mt-1">Medical degrees and certifications.</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Clinical Specialization</label>
              <input
                type="text"
                className="clinical-input text-xs bg-white"
                placeholder="e.g. Cardiology, Endocrinology"
                value={profile.specialization}
                onChange={(e) => setProfile({ ...profile, specialization: e.target.value })}
              />
              <p className="text-[11px] text-slate-400 mt-1">Primary field of medical practice.</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Years of Practice</label>
              <input
                type="number"
                min="0"
                max="70"
                className="clinical-input text-xs bg-white"
                placeholder="e.g. 12"
                value={profile.experience_years}
                onChange={(e) => setProfile({ ...profile, experience_years: e.target.value })}
              />
              <p className="text-[11px] text-slate-400 mt-1">Total years in clinical practice.</p>
            </div>
          </div>
        </div>

        {/* 4. Medical Registration & Licensing */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-2xs space-y-5">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <FileText className="w-4 h-4 text-[#0F766E]" />
            <h3 className="font-bold text-slate-900 text-sm sm:text-base">Medical Registration & Licensing</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Medical Registration / License #</label>
              <input
                type="text"
                className="clinical-input text-xs bg-white"
                placeholder="e.g. MCI-2018-8742"
                value={profile.license_number}
                onChange={(e) => setProfile({ ...profile, license_number: e.target.value })}
              />
              <p className="text-[11px] text-slate-400 mt-1">Official state or national medical registration code.</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Issuing Medical Authority</label>
              <input
                type="text"
                className="clinical-input text-xs bg-white"
                placeholder="e.g. Medical Council of India / State Board"
                value={profile.license_issuing_authority}
                onChange={(e) => setProfile({ ...profile, license_issuing_authority: e.target.value })}
              />
              <p className="text-[11px] text-slate-400 mt-1">Body issuing active clinical practice permit.</p>
            </div>
          </div>
        </div>

        {/* 5. Practice & Clinic Information */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-2xs space-y-5">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Building className="w-4 h-4 text-[#0F766E]" />
            <h3 className="font-bold text-slate-900 text-sm sm:text-base">Clinic & Practice Information</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Clinic / Hospital Practice Name</label>
              <input
                type="text"
                className="clinical-input text-xs bg-white"
                placeholder="e.g. City Heart & Health Medical Center"
                value={profile.clinic_name}
                onChange={(e) => setProfile({ ...profile, clinic_name: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Clinic Contact Phone</label>
              <input
                type="text"
                className="clinical-input text-xs bg-white"
                placeholder="e.g. +91 11 2345 6789"
                value={profile.clinic_phone}
                onChange={(e) => setProfile({ ...profile, clinic_phone: e.target.value })}
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Full Clinic Street Address</label>
              <textarea
                rows="2"
                className="clinical-input text-xs bg-white"
                placeholder="Physical clinic street address, suite, city, state"
                value={profile.clinic_address}
                onChange={(e) => setProfile({ ...profile, clinic_address: e.target.value })}
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Clinic Contact Email</label>
              <input
                type="email"
                className="clinical-input text-xs bg-white"
                placeholder="e.g. contact@cityhealthcenter.org"
                value={profile.clinic_email}
                onChange={(e) => setProfile({ ...profile, clinic_email: e.target.value })}
              />
            </div>
          </div>
        </div>

        {/* 6. Professional Bio */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-2xs space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <User className="w-4 h-4 text-[#0F766E]" />
            <h3 className="font-bold text-slate-900 text-sm sm:text-base">Professional Summary & Bio</h3>
          </div>

          <textarea
            rows="4"
            className="clinical-input text-xs bg-white"
            placeholder="Summarize your clinical background, research interests, and patient care philosophy..."
            value={profile.bio}
            onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
          />
          <p className="text-[11px] text-slate-400">
            {profile.bio?.trim() ? 'Bio recorded.' : 'No additional professional bio provided.'}
          </p>
        </div>

        {/* 7. Account Information Card */}
        <div className="bg-slate-50/80 rounded-2xl p-6 border border-slate-200/90 space-y-4 shadow-2xs">
          <div className="flex items-center gap-2 border-b border-slate-200/60 pb-3">
            <Shield className="w-4 h-4 text-[#0F766E]" />
            <h3 className="font-bold text-slate-900 text-sm sm:text-base">Account Information</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 space-y-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Account Email</span>
              <span className="font-semibold text-slate-800 truncate block">{userEmail}</span>
            </div>

            <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 space-y-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Practitioner Role</span>
              <span className="font-semibold text-[#0F766E] block">Physician / Specialist</span>
            </div>

            <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 space-y-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Account Status</span>
              <span className="inline-flex items-center gap-1 font-bold text-emerald-700">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Active Practitioner
              </span>
            </div>
          </div>
        </div>

        {/* 8. Save Action Bar */}
        <div className="bg-teal-50/40 border border-teal-100 p-4 sm:p-5 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4 shadow-2xs">
          <div className="flex items-center gap-2 text-xs text-slate-600 font-medium">
            <Lock className="w-4 h-4 text-[#0F766E] shrink-0" />
            <div>
              <p className="font-semibold text-slate-800">Your professional record is secure.</p>
              <p className="text-[11px] text-slate-500">Changes are saved to your professional doctor profile.</p>
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
                <span>Saving Profile...</span>
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
