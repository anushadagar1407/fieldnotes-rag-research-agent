const API_BASE = import.meta.env.VITE_API_BASE || ''

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || 'The research service returned an error.')
  return body
}

export const getHealth = () => request('/api/health')
export const getSources = () => request('/api/sources')
export const getActivity = () => request('/api/activity')
export const queryResearch = (question, top_k) => request('/api/query', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, top_k }) })
export const createReport = (query) => request('/api/report', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query }) })
export const uploadSources = (files) => {
  const form = new FormData()
  files.forEach((file) => form.append('files', file))
  return request('/api/ingest', { method: 'POST', body: form })
}
