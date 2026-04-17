import api from '../utils/api'

// Report Service
export const getReports = () =>
  api.get('/api/reports').then((res) => res.data)

export const getReportDetail = (reportId) =>
  api.get(`/api/reports/${reportId}`).then((res) => res.data)

export const getReportsSummary = () =>
  api.get('/api/reports/summary').then((res) => res.data)