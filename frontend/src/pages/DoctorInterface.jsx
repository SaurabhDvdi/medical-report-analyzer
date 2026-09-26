import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../utils/api'
import { getPatients, getPatientDetail, getDoctorNotes, createDoctorNote } from '../services/userService'
import { useAuth } from '../contexts/AuthContext'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import {
  User,
  Save,
  Search,
  ArrowLeft,
  AlertTriangle,
  StickyNote,
  FileText,
  Clock,
  ShieldCheck,
  CheckCircle2,
  ChevronRight,
  Pill
} from 'lucide-react'
import AIAssistantModal from '../components/AIAssistantModal'
import { TableSkeleton, DashboardSkeleton } from '../components/Skeletons'

export default function DoctorInterface() {
  const { user } = useAuth()
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPatient, setSelectedPatient] = useState(id ? parseInt(id, 10) : null)
  const [noteText, setNoteText] = useState('')
  const [showNoteEditor, setShowNoteEditor] = useState(false)
  const [contextReportId, setContextReportId] = useState(null)
  const [saveError, setSaveError] = useState('')

  useEffect(() => {
    if (id) {
      setSelectedPatient(parseInt(id, 10))
    }
  }, [id])

  // 1. Patients query
  const { data: patients = [], isLoading: patientsLoading, error: patientsErr } = useQuery({
    queryKey: ['patients', searchTerm],
    queryFn: () => getPatients(searchTerm ? { search: searchTerm } : {}),
    enabled: user?.role === 'doctor',
    staleTime: 2 * 60 * 1000,
  })

  // 2. Patient Detail query
  const { data: rawPatientData, isLoading: detailLoading, error: detailErr } = useQuery({
    queryKey: ['patient-detail', selectedPatient],
    queryFn: async () => {
      if (!selectedPatient) return null
      const detail = await getPatientDetail(selectedPatient)
      let notes = []
      try {
        notes = await getDoctorNotes({ patient_id: selectedPatient })
      } catch (e) {
        console.error('Error fetching doctor notes:', e)
      }
      return { ...detail, notes: Array.isArray(notes) ? notes : (notes.data || []) }
    },
    enabled: !!selectedPatient && user?.role === 'doctor',
    staleTime: 2 * 60 * 1000,
  })

  const loading = patientsLoading
  const listError = patientsErr ? (patientsErr.response?.data?.detail || 'Unable to load patients.') : ''
  const accessError = detailErr ? (
    detailErr.response?.status === 403
      ? 'Access not granted. This patient’s access was revoked.'
      : (detailErr.response?.data?.detail || 'Unable to load patient details.')
  ) : ''

  const patientData = rawPatientData || null

  // Save Note Mutation
  const saveNoteMutation = useMutation({
    mutationFn: (body) => createDoctorNote(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patient-detail', selectedPatient] })
      setNoteText('')
      setShowNoteEditor(false)
      setContextReportId(null)
    },
    onError: (err) => {
      setSaveError(err.response?.data?.detail || 'Error saving note. Please try again.')
    }
  })

  const handleSaveNote = () => {
    if (!noteText.trim() || !selectedPatient || user?.role !== 'doctor') return
    setSaveError('')
    const body = {
      doctor_id: user.id,
      patient_id: selectedPatient,
      note_text: noteText,
    }
    if (contextReportId != null) {
      body.report_id = contextReportId
    }
    saveNoteMutation.mutate(body)
  }

  const saving = saveNoteMutation.isPending

  const openReportNote = (reportId) => {
    setContextReportId(reportId)
    setNoteText('')
    setShowNoteEditor(true)
    setSaveError('')
  }

  const openGeneralNote = () => {
    setContextReportId(null)
    setNoteText('')
    setShowNoteEditor(true)
    setSaveError('')
  }

  const handlePatientSelect = (patientId) => {
    setSelectedPatient(patientId)
    navigate(`/doctor/patient/${patientId}`)
  }

  const filteredPatients = patients.filter(
    (p) =>
      p.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.email?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (user?.role !== 'doctor') {
    return null
  }

  if (loading && !listError) {
    return <DashboardSkeleton />
  }

  if (id) {
    if (detailLoading) {
      return <DashboardSkeleton />
    }

    if (!patientData) {
      return (
        <div className="clinical-card p-12 text-center space-y-4 max-w-xl mx-auto">
          {accessError ? (
            <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl inline-block">
              {accessError}
            </div>
          ) : (
            <p className="text-xs text-slate-500 font-medium">Loading patient record...</p>
          )}
          <div>
            <button
              type="button"
              onClick={() => navigate('/doctor/patients')}
              className="clinical-button-secondary text-xs"
            >
              ← Back to Patients Directory
            </button>
          </div>
        </div>
      )
    }

    return (
      <div className="space-y-6">
        {/* Navigation & Header */}
        <div className="flex items-center justify-between border-b border-slate-200 pb-4">
          <button
            type="button"
            onClick={() => navigate('/doctor/patients')}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700 hover:text-teal-900"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Patients Directory
          </button>
          <span className="clinical-badge-normal">
            <ShieldCheck className="w-3 h-3 mr-1" /> Clinical Access Active
          </span>
        </div>

        {/* Patient Profile Banner */}
        <div className="bg-gradient-to-r from-slate-900 via-slate-950 to-teal-950 text-white rounded-2xl p-6 shadow-md border border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-teal-500/20 border border-teal-400/30 text-teal-300 font-extrabold flex items-center justify-center text-xl">
              {patientData.patient.full_name?.charAt(0) || 'P'}
            </div>
            <div className="space-y-1">
              <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight">
                {patientData.patient.full_name}
              </h1>
              <p className="text-xs text-slate-300">{patientData.patient.email}</p>
            </div>
          </div>
        </div>

        {/* Physical Metrics Grid */}
        {patientData.profile && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="clinical-card p-4 space-y-1">
              <p className="text-[11px] font-semibold text-slate-500 uppercase">Age</p>
              <p className="text-2xl font-extrabold text-slate-900">{patientData.profile.age || 'N/A'}</p>
              <p className="text-[11px] text-slate-400">Years old</p>
            </div>
            <div className="clinical-card p-4 space-y-1">
              <p className="text-[11px] font-semibold text-slate-500 uppercase">Biological Gender</p>
              <p className="text-2xl font-extrabold text-slate-900 capitalize">{patientData.profile.gender || 'N/A'}</p>
              <p className="text-[11px] text-slate-400">Gender record</p>
            </div>
            <div className="clinical-card p-4 space-y-1">
              <p className="text-[11px] font-semibold text-slate-500 uppercase">Blood Group</p>
              <p className="text-2xl font-extrabold text-teal-700">{patientData.profile.blood_group || 'N/A'}</p>
              <p className="text-[11px] text-slate-400">ABO/Rh factor</p>
            </div>
          </div>
        )}

        {/* Abnormal Lab Values Warning Alert */}
        {patientData.abnormal_values && patientData.abnormal_values.length > 0 && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-900 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
            <div>
              <p className="font-bold">{patientData.abnormal_values.length} out-of-range lab result(s) identified for this patient</p>
              <p className="text-[11px] text-rose-700 mt-0.5">Inspect reports and historical lab values below.</p>
            </div>
          </div>
        )}

        {/* Medical Reports */}
        <div className="clinical-card overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-teal-600" />
              <h3 className="font-bold text-slate-900 text-sm">Medical Reports ({patientData.reports.length})</h3>
            </div>
          </div>

          <div className="divide-y divide-slate-100">
            {patientData.reports.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">No medical reports uploaded by patient yet.</div>
            ) : (
              patientData.reports.map((report) => (
                <div key={report.id} className="p-4 sm:p-5 flex items-center justify-between hover:bg-slate-50 transition-colors">
                  <div className="space-y-1 min-w-0 pr-4">
                    <p className="text-sm font-bold text-slate-900 truncate">{report.file_name}</p>
                    <p className="text-xs text-slate-500">Uploaded {new Date(report.upload_date).toLocaleDateString()}</p>
                    {report.ai_summary && (
                      <p className="text-xs text-slate-600 line-clamp-1 italic">&quot;{report.ai_summary}&quot;</p>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => openReportNote(report.id)}
                    className="clinical-button-secondary text-xs"
                  >
                    + Add Report Note
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Active Regimens */}
        {patientData.medicines && patientData.medicines.length > 0 && (
          <div className="clinical-card overflow-hidden">
            <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Pill className="w-4 h-4 text-indigo-600" />
                <h3 className="font-bold text-slate-900 text-sm">Patient Prescriptions ({patientData.medicines.length})</h3>
              </div>
            </div>

            <div className="divide-y divide-slate-100">
              {patientData.medicines.map((m) => (
                <div key={m.id} className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-900">{m.name}</p>
                    <p className="text-[11px] text-slate-500">{m.dosage} · {m.frequency}</p>
                  </div>
                  <span className="clinical-badge-info">{m.status}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Doctor Consultation Notes Editor & History */}
        <div className="clinical-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <StickyNote className="w-5 h-5 text-indigo-600" />
              <h3 className="font-bold text-slate-900 text-base">Physician Consultation Notes</h3>
            </div>
            {!showNoteEditor && (
              <button
                type="button"
                onClick={openGeneralNote}
                className="clinical-button-primary text-xs"
              >
                + New Consultation Note
              </button>
            )}
          </div>

          {showNoteEditor ? (
            <div className="space-y-4">
              <p className="text-xs font-semibold text-slate-600">
                {contextReportId != null
                  ? `Clinical note linked to Report #${contextReportId}`
                  : 'General clinical consultation note'}
              </p>
              {saveError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-xs text-rose-800 rounded-xl">
                  {saveError}
                </div>
              )}
              <div className="rounded-xl overflow-hidden border border-slate-300">
                <ReactQuill
                  theme="snow"
                  value={noteText}
                  onChange={setNoteText}
                  placeholder="Enter detailed clinical impressions, lab evaluations, or treatment plan notes..."
                  className="bg-white"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowNoteEditor(false)
                    setContextReportId(null)
                    setNoteText('')
                    setSaveError('')
                  }}
                  className="clinical-button-secondary text-xs"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveNote}
                  disabled={saving}
                  className="clinical-button-primary text-xs"
                >
                  <Save className="w-3.5 h-3.5 mr-1" />
                  {saving ? 'Saving Note...' : 'Save Consultation Note'}
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {!patientData.notes || patientData.notes.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-400">
                  No physician notes created for this patient yet. Click above to write a consultation note.
                </div>
              ) : (
                patientData.notes.map((note) => (
                  <div key={note.id} className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2">
                    <div className="flex items-center justify-between text-[11px] text-slate-400 border-b border-slate-200/60 pb-1.5">
                      <span>Recorded {new Date(note.created_at).toLocaleString()}</span>
                      {note.report_id != null && (
                        <span className="font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                          Report #{note.report_id}
                        </span>
                      )}
                    </div>
                    <div
                      className="text-xs text-slate-800 leading-relaxed font-sans prose prose-sm max-w-none"
                      dangerouslySetInnerHTML={{ __html: note.note_text }}
                    />
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        <AIAssistantModal role="doctor" patientId={selectedPatient} activePatientId={selectedPatient} patientName={patientData?.patient?.full_name} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
          <User className="w-6 h-6 text-teal-600" /> Patient Workspace Directory
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Search and select authorized patients to review medical history, lab parameter deltas, and consultation notes.
        </p>
      </div>

      {listError && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800">
          {listError}
        </div>
      )}

      {/* Search Input Bar */}
      <div className="clinical-card p-4">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search authorized patients by full name or email address..."
            className="clinical-input pl-10 text-xs"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* All Patients List */}
      <div className="clinical-card overflow-hidden">
        <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
          <h3 className="font-bold text-slate-900 text-sm">All Accessible Patients ({filteredPatients.length})</h3>
        </div>

        <div className="divide-y divide-slate-100">
          {filteredPatients.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-400">
              No authorized patients match the entered search filter.
            </div>
          ) : (
            filteredPatients.map((patient) => (
              <button
                type="button"
                key={patient.id}
                onClick={() => handlePatientSelect(patient.id)}
                className="w-full p-4 sm:p-5 text-left hover:bg-slate-50 transition-colors flex items-center justify-between group"
              >
                <div className="flex items-center gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-100 text-teal-700 font-bold flex items-center justify-center text-sm shrink-0">
                    {patient.full_name?.charAt(0) || 'P'}
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm group-hover:text-teal-700 transition-colors flex items-center gap-1.5">
                      <span>{patient.full_name || patient.email}</span>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-600" />
                    </h4>
                    <p className="text-xs text-slate-500">{patient.email}</p>
                    {patient.age && (
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        {patient.age} yrs · {patient.gender || '—'} · Blood Group: {patient.blood_group || '—'}
                      </p>
                    )}
                  </div>
                </div>

                <span className="clinical-button-secondary text-xs">Inspect Patient →</span>
              </button>
            ))
          )}
        </div>
      </div>

      <AIAssistantModal role="doctor" patientId={selectedPatient} activePatientId={selectedPatient} patientName={patientData?.patient?.full_name} />
    </div>
  )
}
