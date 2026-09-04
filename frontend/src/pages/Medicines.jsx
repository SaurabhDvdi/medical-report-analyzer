import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../utils/api'
import { getMedicines } from '../services/userService'
import { Plus, Edit, Trash2, Calendar, Pill, Clock, AlertCircle, X } from 'lucide-react'
import { TableSkeleton } from '../components/Skeletons'

const emptyForm = {
  name: '',
  dosage: '',
  frequency: '',
  start_date: '',
  end_date: '',
  status: 'current',
}

export default function Medicines() {
  const queryClient = useQueryClient()
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedMedicine, setSelectedMedicine] = useState(null)
  const [formData, setFormData] = useState(emptyForm)

  const { data: medicines = [], isLoading: loading, error } = useQuery({
    queryKey: ['medicines'],
    queryFn: getMedicines,
    staleTime: 5 * 60 * 1000,
  })

  const listError = error ? (error.response?.data?.detail || 'Could not load medicines.') : ''

  const saveMutation = useMutation({
    mutationFn: async (payload) => {
      if (selectedMedicine) {
        return api.put(`/api/medicines/${selectedMedicine.id}`, payload)
      }
      return api.post('/api/medicines', payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['medicines'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      closeModal()
    },
    onError: (err) => {
      alert(err.response?.data?.detail || 'Error saving medicine. Please try again.')
    }
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/api/medicines/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['medicines'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: (err) => {
      alert(err.response?.data?.detail || 'Error deleting medicine. Please try again.')
    }
  })

  const openAddModal = () => {
    setSelectedMedicine(null)
    setFormData(emptyForm)
    setModalOpen(true)
  }

  const openEditModal = (medicine) => {
    setSelectedMedicine(medicine)
    setFormData({
      name: medicine.name,
      dosage: medicine.dosage,
      frequency: medicine.frequency,
      start_date: medicine.start_date || '',
      end_date: medicine.end_date || '',
      status: medicine.status,
    })
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    setSelectedMedicine(null)
    setFormData(emptyForm)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = {
      ...formData,
      start_date: formData.start_date || null,
      end_date: formData.end_date || null,
    }
    saveMutation.mutate(payload)
  }

  const handleDelete = (id) => {
    if (!window.confirm('Are you sure you want to delete this medicine?')) {
      return
    }
    deleteMutation.mutate(id)
  }

  const currentMedicines = medicines.filter(
    (m) => m.status?.toLowerCase() === 'current'
  )

  const pastMedicines = medicines.filter(
    (m) => m.status?.toLowerCase() === 'past'
  )

  if (loading) {
    return <TableSkeleton rows={5} />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <Pill className="w-6 h-6 text-indigo-600" /> Prescribed Medications
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Track active medical prescriptions, dosage frequencies, and treatment histories.
          </p>
        </div>

        <button
          type="button"
          onClick={openAddModal}
          className="clinical-button-primary text-xs"
        >
          <Plus className="w-3.5 h-3.5 mr-1.5" /> Add Medication Regimen
        </button>
      </div>

      {listError && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{listError}</span>
        </div>
      )}

      {/* Add / Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 w-full max-w-md shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-base">
                {selectedMedicine ? 'Edit Medication Regimen' : 'Add Medication Regimen'}
              </h3>
              <button onClick={closeModal} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Medicine Name *</label>
                <input
                  type="text"
                  required
                  className="clinical-input text-xs"
                  placeholder="e.g. Metformin, Atorvastatin"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Dosage *</label>
                  <input
                    type="text"
                    required
                    className="clinical-input text-xs"
                    placeholder="e.g. 500mg"
                    value={formData.dosage}
                    onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Frequency *</label>
                  <input
                    type="text"
                    required
                    className="clinical-input text-xs"
                    placeholder="e.g. Twice Daily"
                    value={formData.frequency}
                    onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Start Date</label>
                  <input
                    type="date"
                    className="clinical-input text-xs"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">End Date</label>
                  <input
                    type="date"
                    className="clinical-input text-xs"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Prescription Status</label>
                <select
                  className="clinical-input text-xs"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  <option value="current">Active / Current</option>
                  <option value="past">Past / Discontinued</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={closeModal}
                  className="clinical-button-secondary text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saveMutation.isLoading}
                  className="clinical-button-primary text-xs"
                >
                  {saveMutation.isLoading ? 'Saving...' : selectedMedicine ? 'Update Regimen' : 'Add Regimen'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Active Prescriptions Table/Grid */}
      <div className="clinical-card overflow-hidden">
        <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-emerald-600" />
            <h3 className="font-bold text-slate-900 text-sm">Active Medications ({currentMedicines.length})</h3>
          </div>
          <span className="clinical-badge-normal">Current Regimens</span>
        </div>

        <div className="divide-y divide-slate-100">
          {currentMedicines.length === 0 ? (
            <div className="p-8 text-center space-y-2">
              <Pill className="w-8 h-8 text-slate-300 mx-auto" />
              <p className="text-xs text-slate-500">No active medications registered.</p>
            </div>
          ) : (
            currentMedicines.map((m) => (
              <div key={m.id} className="p-4 sm:p-5 flex items-center justify-between hover:bg-slate-50 transition-colors">
                <div className="space-y-1">
                  <h4 className="font-bold text-slate-900 text-sm sm:text-base flex items-center gap-2">
                    <span>{m.name}</span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {m.dosage}
                    </span>
                  </h4>
                  <p className="text-xs text-slate-500">
                    Frequency: <span className="font-medium text-slate-700">{m.frequency}</span>
                    {m.start_date && (
                      <span className="ml-3 inline-flex items-center gap-1 text-[11px] text-slate-400">
                        <Calendar className="w-3 h-3 text-slate-400" /> Started {new Date(m.start_date).toLocaleDateString()}
                      </span>
                    )}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => openEditModal(m)}
                    className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition-colors"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(m.id)}
                    className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Historical / Past Prescriptions */}
      <div className="clinical-card overflow-hidden">
        <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
          <h3 className="font-bold text-slate-900 text-sm">Discontinued / Past Medications ({pastMedicines.length})</h3>
          <span className="clinical-badge-info">Past Regimens</span>
        </div>

        <div className="divide-y divide-slate-100">
          {pastMedicines.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-400">No past medications recorded.</div>
          ) : (
            pastMedicines.map((m) => (
              <div key={m.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                <div className="space-y-1">
                  <h4 className="font-bold text-slate-700 text-sm flex items-center gap-2 line-through">
                    <span>{m.name}</span>
                    <span className="no-underline text-xs text-slate-500">({m.dosage})</span>
                  </h4>
                  <p className="text-xs text-slate-400">
                    {m.frequency}
                    {m.start_date && m.end_date && (
                      <span className="ml-2">
                        ({new Date(m.start_date).toLocaleDateString()} — {new Date(m.end_date).toLocaleDateString()})
                      </span>
                    )}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => openEditModal(m)}
                    className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition-colors"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(m.id)}
                    className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
