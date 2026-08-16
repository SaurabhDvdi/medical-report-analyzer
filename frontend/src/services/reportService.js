import api from '../utils/api'

// Report Service
export const getReports = () =>
  api.get('/api/reports').then((res) => res.data)

export const getReportDetail = (reportId) =>
  api.get(`/api/reports/${reportId}`).then((res) => res.data)

export const getReportsSummary = () =>
  api.get('/api/reports/summary').then((res) => res.data)

export const uploadReport = (formData, onUploadProgress) =>
  api.post('/api/reports/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress
  }).then((res) => res.data)

export const deleteReport = (reportId) =>
  api.delete(`/api/reports/${reportId}`).then((res) => res.data)

export const downloadReport = (reportId) =>
  api.get(`/api/reports/${reportId}/download`, { responseType: 'blob' }).then((res) => res.data)

export const exportReportsCsv = () =>
  api.get('/api/export/csv', { responseType: 'blob' }).then((res) => res.data)