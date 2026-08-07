const API_BASE = '/api'

export async function uploadVideos(files) {
  const fd = new FormData()
  files.forEach(file => fd.append('files', file))
  const resp = await fetch(`${API_BASE}/videos/upload`, { method: 'POST', body: fd })
  if (!resp.ok) throw new Error((await resp.json()).detail || '上传失败')
  return resp.json()
}

export async function getTasks() {
  const resp = await fetch(`${API_BASE}/tasks`)
  return resp.json()
}

export async function getTask(taskId) {
  const resp = await fetch(`${API_BASE}/tasks/${taskId}`)
  return resp.json()
}

export async function deleteTask(taskId) {
  const resp = await fetch(`${API_BASE}/tasks/${taskId}`, { method: 'DELETE' })
  return resp.json()
}

export async function cancelTask(taskId) {
  const resp = await fetch(`${API_BASE}/tasks/${taskId}/cancel`, { method: 'POST' })
  return resp.json()
}

export async function getHistory(page = 1, pageSize = 20) {
  const resp = await fetch(`${API_BASE}/history?page=${page}&page_size=${pageSize}`)
  return resp.json()
}

export async function deleteHistory(taskId) {
  const resp = await fetch(`${API_BASE}/history/${taskId}`, { method: 'DELETE' })
  return resp.json()
}

export async function getFullResult(taskId) {
  const resp = await fetch(`${API_BASE}/results/${taskId}`)
  return resp.json()
}

export function getVideoUrl(taskId) {
  return `/api/video/${taskId}`
}

export function createProgressSocket(taskId, onMessage) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/progress/${taskId}`
  const ws = new WebSocket(wsUrl)
  ws.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)) } catch (_) { /* ignore */ }
  }
  return ws
}
