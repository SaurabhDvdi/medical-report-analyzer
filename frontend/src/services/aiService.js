import api from '../utils/api'

export const askAIChat = (payload) =>
  api.post('/api/ai/chat', payload).then((res) => res.data)

export const clearAIChat = (payload = {}) =>
  api.post('/api/ai/clear-chat', payload).then((res) => res.data)

export const compareReports = (oldReportId, newReportId) =>
  api.post('/api/ai/compare-reports', {
    old_report_id: oldReportId,
    new_report_id: newReportId,
  }).then((res) => res.data)

/**
 * Server-Sent Events (SSE) streaming client for AI Clinical Assistant.
 * Streams incremental response tokens, emitting metadata, token, and complete events.
 */
export const streamAIChat = async (payload, { onMetadata, onToken, onComplete, onError }) => {
  const token = sessionStorage.getItem('token')
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  try {
    const response = await fetch(`${baseUrl}/api/ai/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify(payload)
    })

    if (!response.ok) {
      if (response.status === 401) {
        sessionStorage.removeItem('token')
        sessionStorage.removeItem('user')
        window.location.replace('/login')
        return
      }
      const errText = await response.text()
      throw new Error(errText || `Server responded with ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop() // keep unparsed remainder

      for (const block of lines) {
        if (!block.trim()) continue
        const eventMatch = block.match(/^event:\s*(.+)$/m)
        const dataMatch = block.match(/^data:\s*(.+)$/m)
        if (eventMatch && dataMatch) {
          const eventType = eventMatch[1].trim()
          let parsedData = {}
          try {
            parsedData = JSON.parse(dataMatch[1].trim())
          } catch (e) {
            parsedData = dataMatch[1].trim()
          }

          if (eventType === 'metadata' && onMetadata) onMetadata(parsedData)
          else if (eventType === 'token' && onToken) onToken(parsedData.token || '')
          else if (eventType === 'complete' && onComplete) onComplete(parsedData)
          else if (eventType === 'error') throw new Error(parsedData.error || 'Stream error')
        }
      }
    }
  } catch (err) {
    if (onError) onError(err)
    else throw err
  }
}
