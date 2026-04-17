import api from '../utils/api'

// Authentication
export const login = (email, password) =>
  api.post('/api/auth/login', { email, password })

export const register = (userData) =>
  api.post('/api/auth/register', userData)

// User Profile
export const getProfile = () =>
  api.get('/api/patient/profile').then((res) => res.data)

// Medicines
export const getMedicines = () =>
  api.get('/api/medicines').then((res) => res.data)

// Categories and Specialties
export const getCategories = () =>
  api.get('/api/categories').then((res) => res.data)

export const getSpecialties = (categoryId) =>
  api.get('/api/specialties', { params: { category_id: categoryId } }).then((res) => res.data)

// Doctors
export const getDoctors = (params) =>
  api.get('/api/doctors', { params }).then((res) => res.data)

// Patients
export const getPatients = (params) =>
  api.get('/api/users/patients', { params }).then((res) => res.data)

export const getPatientDetail = (patientId) =>
  api.get(`/api/doctor/patient/${patientId}`).then((res) => res.data)

// Doctor Statistics
export const getDoctorStatistics = () =>
  api.get('/api/doctor/statistics').then((res) => res.data)

export const getAssignmentStats = () =>
  api.get('/api/doctor/assignment-stats').then((res) => res.data)

// Patient Access Management
export const getPatientAccessRequests = (params) =>
  api.get('/api/doctor/patient-access-requests', { params })

export const approvePatientAccess = (requestId, action) =>
  api.post(`/api/doctor/patient-access-requests/${requestId}/${action}`)

// Discovery Stats
export const getDiscoveryStats = () =>
  api.get('/api/patient/discovery-stats').then((res) => res.data)

// Doctor Access
export const getDoctorAccess = () =>
  api.get('/api/patient/doctor-access').then((res) => res.data)

export const grantDoctorAccess = (doctorId) =>
  api.post('/api/patient/doctor-access', { doctor_id: doctorId }).then((res) => res.data)

export const revokeDoctorAccess = (accessId) =>
  api.post(`/api/patient/doctor-access/${accessId}/revoke`).then((res) => res.data)

// Doctor Notes
export const getDoctorNotes = (params) =>
  api.get('/api/doctor-notes', { params }).then((res) => res.data)

export const createDoctorNote = (noteData) =>
  api.post('/api/doctor-notes', noteData).then((res) => res.data)