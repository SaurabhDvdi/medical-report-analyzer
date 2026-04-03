import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import api from '../utils/api'

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
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Or{' '}
            <Link to="/login" className="font-medium text-blue-600 hover:text-blue-500">
              sign in to existing account
            </Link>
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-gray-700">
                Full Name
              </label>
              <input
                id="fullName"
                name="fullName"
                type="text"
                required
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                value={formData.fullName}
                onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="role" className="block text-sm font-medium text-gray-700">
                Role
              </label>
              <select
                id="role"
                name="role"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                value={formData.role}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    role: e.target.value,
                    doctor_category_id: '',
                    doctor_specialty_id: '',
                    useNewSpecialty: false,
                    new_specialty_name: '',
                    new_specialty_description: '',
                  })
                }
              >
                <option value="patient">Patient</option>
                <option value="doctor">Doctor</option>
              </select>
            </div>

            {formData.role === 'doctor' && (
              <div className="border border-gray-200 rounded-md p-4 space-y-3 bg-white">
                <p className="text-sm font-medium text-gray-800">Clinical profile</p>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Category</label>
                  <select
                    required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md sm:text-sm"
                    value={formData.doctor_category_id}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        doctor_category_id: e.target.value,
                        doctor_specialty_id: '',
                      })
                    }
                  >
                    <option value="">Select category…</option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
                <label className="flex items-center gap-2 text-sm text-gray-700">
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
                  My specialty is not listed — add a new one
                </label>
                {!formData.useNewSpecialty ? (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Specialty</label>
                    <select
                      required={!!formData.doctor_category_id}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md sm:text-sm disabled:bg-gray-100"
                      value={formData.doctor_specialty_id}
                      onChange={(e) =>
                        setFormData({ ...formData, doctor_specialty_id: e.target.value })
                      }
                      disabled={!formData.doctor_category_id}
                    >
                      <option value="">
                        {formData.doctor_category_id
                          ? 'Select specialty…'
                          : 'Choose a category first'}
                      </option>
                      {specialties.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                        </option>
                      ))}
                    </select>
                  </div>
                ) : (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        New specialty name
                      </label>
                      <input
                        type="text"
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md sm:text-sm"
                        value={formData.new_specialty_name}
                        onChange={(e) =>
                          setFormData({ ...formData, new_specialty_name: e.target.value })
                        }
                        placeholder="e.g. Interventional cardiology"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Description (optional)
                      </label>
                      <textarea
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md sm:text-sm"
                        rows={2}
                        value={formData.new_specialty_description}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            new_specialty_description: e.target.value,
                          })
                        }
                      />
                    </div>
                  </>
                )}
              </div>
            )}
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
