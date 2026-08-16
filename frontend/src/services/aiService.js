import api from '../utils/api'

export const askAIChat = (payload) =>
  api.post('/api/ai/chat', payload).then((res) => res.data)

export const compareReports = (oldReportId, newReportId) =>
  api.post('/api/ai/compare-reports', {
    old_report_id: oldReportId,
    new_report_id: newReportId,
  }).then((res) => res.data)
