import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../utils/api'
import { useAuth } from '../contexts/AuthContext'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { User, Save, Search, ArrowLeft, AlertTriangle, StickyNote } from 'lucide-react'

export default function DoctorInterface() {
  const { user } = useAuth()
  const { id } = useParams()
  const navigate = useNavigate()
  const [patients, setPatients] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPatient, setSelectedPatient] = useState(id ? parseInt(id, 10) : null)
  const [patientData, setPatientData] = useState(null)
  const [noteText, setNoteText] = useState('')
  const [showNoteEditor, setShowNoteEditor] = useState(false)
  const [contextReportId, setContextReportId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [listError, setListError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (id) {
      setSelectedPatient(parseInt(id, 10))
    }
  }, [id])

  const fetchPatients = useCallback(async () => {
    if (user?.role !== 'doctor') return
    setListError('')
    try {
      const response = await api.get('/api/users/patients', {
        params: searchTerm ? { search: searchTerm } : {},
      })
      setPatients(response.data)
    } catch (error) {
      console.error('Error fetching patients:', error)
      setListError(
        error.response?.data?.detail || 'Unable to load patients.'
      )
    } finally {
      setLoading(false)
    }
  }, [user?.role, searchTerm])

  useEffect(() => {
    if (user?.role !== 'doctor') return
    fetchPatients()
  }, [user?.role, fetchPatients])

  const fetchPatientData = useCallback(async () => {
    if (!selectedPatient || user?.role !== 'doctor') return

    try {
      const detailRes = await api.get(`/api/doctor/patient/${selectedPatient}`)
      let notes = []
      try {
        const notesRes = await api.get('/api/doctor-notes', {
          params: { patient_id: selectedPatient },
        })
        notes = notesRes.data
      } catch (noteErr) {
        console.error('Error fetching doctor notes:', noteErr)
      }
      setPatientData({
        ...detailRes.data,
        notes,
      })
    } catch (error) {
      console.error('Error fetching patient data:', error)
      setPatientData(null)
    }
  }, [selectedPatient, user?.role])

  useEffect(() => {
    if (selectedPatient && user?.role === 'doctor') {
      fetchPatientData()
    }
  }, [selectedPatient, user?.role, fetchPatientData])

  const handleSaveNote = async () => {
    if (!noteText.trim() || !selectedPatient || user?.role !== 'doctor') return
    setSaveError('')
    setSaving(true)
    try {
      const body = {
        doctor_id: user.id,
        patient_id: selectedPatient,
        note_text: noteText,
      }
      if (contextReportId != null) {
        body.report_id = contextReportId
      }
      await api.post('/api/doctor-notes', body)

      setNoteText('')
      setShowNoteEditor(false)
      setContextReportId(null)
      await fetchPatientData()
    } catch (error) {
      console.error('Error saving note:', error)
      setSaveError(
        error.response?.data?.detail || 'Error saving note. Please try again.'
      )
    } finally {
      setSaving(false)
    }
  }

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
    return <div className="text-center py-12">Loading...</div>
  }

  if (id) {
    if (!patientData) {
      return <div className="text-center py-12">Loading patient data...</div>
    }
    return (
      <div className="px-4 py-6 bg-gray-50 min-h-screen">
        <div className="max-w-7xl mx-auto">
          <button
            type="button"
            onClick={() => navigate('/doctor/patients')}
            className="mb-4 inline-flex items-center text-blue-600 hover:text-blue-800"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Patients
          </button>

          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {patientData.patient.full_name}
            </h1>
            <p className="text-gray-600">{patientData.patient.email}</p>
          </div>

          {patientData.profile && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="bg-white rounded-lg shadow-md p-6">
                <p className="text-sm text-gray-600">Age</p>
                <p className="text-2xl font-bold text-gray-900">
                  {patientData.profile.age || 'N/A'}
                </p>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <p className="text-sm text-gray-600">Gender</p>
                <p className="text-2xl font-bold text-gray-900">
                  {patientData.profile.gender || 'N/A'}
                </p>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <p className="text-sm text-gray-600">Blood Group</p>
                <p className="text-2xl font-bold text-gray-900">
                  {patientData.profile.blood_group || 'N/A'}
                </p>
              </div>
            </div>
          )}

          {patientData.abnormal_values && patientData.abnormal_values.length > 0 && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded">
              <div className="flex items-center">
                <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
                <p className="font-semibold text-red-800">
                  {patientData.abnormal_values.length} abnormal lab value(s) detected
                </p>
              </div>
            </div>
          )}

          <div className="bg-white rounded-lg shadow-md mb-6">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Medical Reports</h2>
            </div>
            <div className="divide-y divide-gray-200">
              {patientData.reports.map((report) => (
                <div key={report.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{report.file_name}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(report.upload_date).toLocaleDateString()}
                      </p>
                      {report.ai_summary && (
                        <p className="text-sm text-gray-600 mt-1">{report.ai_summary}</p>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => openReportNote(report.id)}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      Add Note
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {patientData.medicines && patientData.medicines.length > 0 && (
            <div className="bg-white rounded-lg shadow-md mb-6">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Medications</h2>
              </div>
              <div className="divide-y divide-gray-200">
                {patientData.medicines.map((medicine) => (
                  <div key={medicine.id} className="px-6 py-4">
                    <p className="font-medium text-gray-900">{medicine.name}</p>
                    <p className="text-sm text-gray-600">
                      {medicine.dosage} • {medicine.frequency} • {medicine.status}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b border-gray-200 flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-xl font-semibold text-gray-900">Doctor Notes</h2>
              {!showNoteEditor && (
                <button
                  type="button"
                  onClick={openGeneralNote}
                  className="inline-flex items-center text-sm px-3 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700"
                >
                  <StickyNote className="w-4 h-4 mr-2" />
                  New consultation note
                </button>
              )}
            </div>
            <div className="p-6">
              {showNoteEditor ? (
                <div className="space-y-4">
                  <p className="text-sm text-gray-600">
                    {contextReportId != null
                      ? `Note for report #${contextReportId} (saved as HTML)`
                      : 'General consultation note (saved as HTML)'}
                  </p>
                  {saveError && (
                    <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">
                      {saveError}
                    </div>
                  )}
                  <ReactQuill
                    theme="snow"
                    value={noteText}
                    onChange={setNoteText}
                    placeholder="Write your notes here..."
                    className="bg-white"
                  />
                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      onClick={() => {
                        setShowNoteEditor(false)
                        setContextReportId(null)
                        setNoteText('')
                        setSaveError('')
                      }}
                      className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleSaveNote}
                      disabled={saving}
                      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                    >
                      <Save className="w-4 h-4 mr-2" />
                      {saving ? 'Saving…' : 'Save Note'}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {!patientData.notes || patientData.notes.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">
                      No notes yet. Add a consultation note or link a note to a report.
                    </p>
                  ) : (
                    patientData.notes.map((note) => (
                      <div key={note.id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <p className="text-sm text-gray-500">
                            {new Date(note.created_at).toLocaleString()}
                          </p>
                          {note.report_id != null && (
                            <span className="text-xs text-blue-600">Report #{note.report_id}</span>
                          )}
                        </div>
                        <div
                          className="text-gray-700 prose prose-sm max-w-none"
                          dangerouslySetInnerHTML={{ __html: note.note_text }}
                        />
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="px-4 py-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Patient Management</h1>

        {listError && (
          <div className="mb-4 rounded-md bg-red-50 border border-red-200 text-red-800 px-4 py-3 text-sm">
            {listError}
          </div>
        )}

        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search patients by name or email..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">
              All Patients ({filteredPatients.length})
            </h2>
          </div>
          <div className="divide-y divide-gray-200">
            {filteredPatients.length === 0 ? (
              <div className="px-6 py-12 text-center text-gray-500">
                <User className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p>No patients found</p>
              </div>
            ) : (
              filteredPatients.map((patient) => (
                <button
                  type="button"
                  key={patient.id}
                  onClick={() => handlePatientSelect(patient.id)}
                  className="w-full px-6 py-4 text-left hover:bg-blue-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <User className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="font-medium text-gray-900">
                          {patient.full_name || patient.email}
                        </p>
                        <p className="text-sm text-gray-500">{patient.email}</p>
                        {patient.age && (
                          <p className="text-xs text-gray-400 mt-1">
                            {patient.age} years • {patient.gender} • {patient.blood_group}
                          </p>
                        )}
                      </div>
                    </div>
                    <ArrowLeft className="w-5 h-5 text-gray-400 transform rotate-180" />
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
