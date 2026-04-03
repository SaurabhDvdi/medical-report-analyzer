import { useState, useEffect, useCallback } from 'react'
import api from '../utils/api'
import { Search, User, Stethoscope, Loader, HeartHandshake } from 'lucide-react'

export default function FindDoctors() {
  const [doctors, setDoctors] = useState([])
  const [categories, setCategories] = useState([])
  const [specialties, setSpecialties] = useState([])
  const [name, setName] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [specialtyId, setSpecialtyId] = useState('')
  const [loading, setLoading] = useState(true)
  const [listLoading, setListLoading] = useState(false)
  const [error, setError] = useState('')
  const [actionMsg, setActionMsg] = useState({})
  const [actionBusy, setActionBusy] = useState({})

  useEffect(() => {
    const loadMeta = async () => {
      try {
        const catRes = await api.get('/api/categories')
        setCategories(catRes.data)
      } catch (e) {
        console.error(e)
        setError('Could not load categories.')
      } finally {
        setLoading(false)
      }
    }
    loadMeta()
  }, [])

  useEffect(() => {
    const loadSpec = async () => {
      if (!categoryId) {
        setSpecialties([])
        setSpecialtyId('')
        return
      }
      try {
        const res = await api.get('/api/specialties', {
          params: { category_id: categoryId },
        })
        setSpecialties(res.data)
        setSpecialtyId('')
      } catch (e) {
        console.error(e)
      }
    }
    loadSpec()
  }, [categoryId])

  const fetchDoctors = useCallback(async () => {
    setListLoading(true)
    setError('')
    try {
      const params = {}
      if (name.trim()) params.name = name.trim()
      if (categoryId) params.category_id = categoryId
      if (specialtyId) params.specialty_id = specialtyId
      const res = await api.get('/api/doctors', { params })
      setDoctors(res.data)
    } catch (e) {
      console.error(e)
      setError(e.response?.data?.detail || 'Could not load doctors.')
      setDoctors([])
    } finally {
      setListLoading(false)
    }
  }, [name, categoryId, specialtyId])

  useEffect(() => {
    if (loading) return
    fetchDoctors()
    // Intentionally run once when taxonomy is ready; use "Search" for filter updates.
     
  }, [loading])

  const requestAccess = async (doctorId) => {
    setActionBusy((b) => ({ ...b, [doctorId]: true }))
    setActionMsg((m) => ({ ...m, [doctorId]: '' }))
    try {
      await api.post('/api/patient/doctor-access', { doctor_id: doctorId })
      setActionMsg((m) => ({ ...m, [doctorId]: 'Request sent' }))
    } catch (e) {
      const d = e.response?.data?.detail
      setActionMsg((m) => ({
        ...m,
        [doctorId]: typeof d === 'string' ? d : 'Request failed',
      }))
    } finally {
      setActionBusy((b) => ({ ...b, [doctorId]: false }))
    }
  }

  if (loading) {
    return (
      <div className="text-center py-12 flex flex-col items-center gap-2">
        <Loader className="w-8 h-8 text-blue-500 animate-spin" />
        Loading…
      </div>
    )
  }

  return (
    <div className="px-4 py-6 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Find Doctors</h1>
      <p className="text-gray-600 mb-6">
        Search by name or narrow by clinical category and specialty. Results are sorted by
        category, specialty, then name.
      </p>

      <div className="bg-white rounded-lg shadow p-6 mb-8 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Doctor name</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="search"
                className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md text-sm"
                placeholder="Search…"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Category</label>
            <select
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
            >
              <option value="">All categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Specialty</label>
            <select
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm bg-white disabled:bg-gray-100"
              value={specialtyId}
              onChange={(e) => setSpecialtyId(e.target.value)}
              disabled={!categoryId}
            >
              <option value="">All specialties{categoryId ? '' : ' (pick category)'}</option>
              {specialties.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button
          type="button"
          onClick={fetchDoctors}
          disabled={listLoading}
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {listLoading && <Loader className="w-4 h-4 mr-2 animate-spin" />}
          Search
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 border border-red-200 text-red-800 px-4 py-3 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {doctors.length === 0 && !listLoading ? (
          <p className="text-gray-500 col-span-full text-center py-12">No doctors match your filters.</p>
        ) : (
          doctors.map((d) => (
            <div
              key={d.id}
              className="bg-white rounded-lg border border-gray-200 shadow-sm p-5 flex flex-col gap-3"
            >
              <div className="flex items-start gap-3">
                <div className="p-2 bg-blue-50 rounded-lg">
                  <User className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">{d.full_name}</h2>
                  <div className="flex items-center gap-2 text-sm text-gray-600 mt-1">
                    <Stethoscope className="w-4 h-4" />
                    <span>{d.category_name || '—'}</span>
                    <span className="text-gray-400">·</span>
                    <span>{d.specialty_name || '—'}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => requestAccess(d.id)}
                  disabled={actionBusy[d.id]}
                  className="inline-flex items-center text-sm px-3 py-2 rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  <HeartHandshake className="w-4 h-4 mr-2" />
                  {actionBusy[d.id] ? 'Sending…' : 'Request access'}
                </button>
                {actionMsg[d.id] && (
                  <span className="text-xs text-gray-600">{actionMsg[d.id]}</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
