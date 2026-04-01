import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../utils/api'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { User, FileText, Save, Search, ArrowLeft, AlertTriangle, Pill, Calendar } from 'lucide-react'

export default function DoctorInterface() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [patients, setPatients] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPatient, setSelectedPatient] = useState(id ? parseInt(id) : null)
  const [patientData, setPatientData] = useState(null)
  const [noteText, setNoteText] = useState('')
  const [selectedReport, setSelectedReport] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPatients()
  }, [])

  useEffect(() => {
    if (selectedPatient) {
      fetchPatientData()
    }
  }, [selectedPatient])

  const fetchPatients = async () => {
    try {
      const response = await api.get('/api/users/patients', {
        params: searchTerm ? { search: searchTerm } : {}
      })
      setPatients(response.data)
      if (!selectedPatient && response.data.length > 0) {
        setSelectedPatient(response.data[0].id)
      }
      setLoading(false)
    } catch (error) {
      console.error('Error fetching patients:', error)
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPatients()
  }, [searchTerm])

  useEffect(() => {
    if (id) {
      setSelectedPatient(parseInt(id))
    }
  }, [id])

  useEffect(() => {
    if (selectedPatient) {
      fetchPatientData()
    }
  }, [selectedPatient])

  const fetchPatientData = async () => {
    if (!selectedPatient) return

    try {
      const response = await api.get(`/api/doctor/patient/${selectedPatient}`)
      setPatientData(response.data)
    } catch (error) {
      console.error('Error fetching patient data:', error)
    }
  }

  const handleSaveNote = async () => {
    if (!noteText.trim() || !selectedPatient) return

    try {
      await api.post('/api/doctor-notes', {
        patient_id: selectedPatient,
        report_id: selectedReport,
        note_text: noteText
      })

      setNoteText('')
      setSelectedReport(null)
      fetchPatientData()
    } catch (error) {
      console.error('Error saving note:', error)
      alert('Error saving note. Please try again.')
    }
  }

  const handlePatientSelect = (patientId) => {
    setSelectedPatient(patientId)
    navigate(`/doctor/patient/${patientId}`)
  }

  const filteredPatients = patients.filter(p =>
    p.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.email?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return <div className="text-center py-12">Loading...</div>
  }

  // If patient ID in URL, show detail view
  if (id) {
    if (!patientData) {
      return <div className="text-center py-12">Loading patient data...</div>
    }
    return (
      <div className="px-4 py-6 bg-gray-50 min-h-screen">
        <div className="max-w-7xl mx-auto">
          <button
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

          {/* Patient Profile Summary */}
          {patientData.profile && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="bg-white rounded-lg shadow-md p-6">
                <p className="text-sm text-gray-600">Age</p>
                <p className="text-2xl font-bold text-gray-900">{patientData.profile.age || 'N/A'}</p>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <p className="text-sm text-gray-600">Gender</p>
                <p className="text-2xl font-bold text-gray-900">{patientData.profile.gender || 'N/A'}</p>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <p className="text-sm text-gray-600">Blood Group</p>
                <p className="text-2xl font-bold text-gray-900">{patientData.profile.blood_group || 'N/A'}</p>
              </div>
            </div>
          )}

          {/* Abnormal Values Alert */}
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

          {/* Reports */}
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
                      onClick={() => {
                        setSelectedReport(report.id)
                        setNoteText('')
                      }}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      Add Note
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Medicines */}
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

          {/* Notes Editor */}
          <div className="bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                {selectedReport ? 'Add Examination Note' : 'Consultation Notes'}
              </h2>
            </div>
            <div className="p-6">
              {selectedReport ? (
                <div className="space-y-4">
                  <ReactQuill
                    theme="snow"
                    value={noteText}
                    onChange={setNoteText}
                    placeholder="Write your examination notes here..."
                    className="bg-white"
                  />
                  <div className="flex justify-end space-x-3">
                    <button
                      onClick={() => {
                        setSelectedReport(null)
                        setNoteText('')
                      }}
                      className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveNote}
                      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-white bg-blue-600 hover:bg-blue-700"
                    >
                      <Save className="w-4 h-4 mr-2" />
                      Save Note
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {patientData.notes.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">
                      No notes yet. Select a report to add a note.
                    </p>
                  ) : (
                    patientData.notes.map((note) => (
                      <div key={note.id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <p className="text-sm text-gray-500">
                            {new Date(note.created_at).toLocaleString()}
                          </p>
                          {note.report_id && (
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

  // Patient List View
  return (
    <div className="px-4 py-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Patient Management</h1>

        {/* Search */}
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

        {/* Patient List */}
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
                  key={patient.id}
                  onClick={() => handlePatientSelect(patient.id)}
                  className="w-full px-6 py-4 text-left hover:bg-blue-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <User className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="font-medium text-gray-900">{patient.full_name || patient.email}</p>
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

