import { auth } from '../firebase.js'
// Tunnel builds always use the same origin, even if an old API base is configured.
export const apiBase = import.meta.env.DEV || import.meta.env.VITE_WORKER_REMOTE === '1'
  ? '' : (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
export async function getMonitorToken() {
  if (!auth.currentUser) throw new Error('請先登入')
  return auth.currentUser.getIdToken()
}
export async function syncSession() {
  const response = await fetch(`${apiBase}/api/session`, {method:'POST', credentials:'include', headers:{Authorization:`Bearer ${await getMonitorToken()}`}})
  if (!response.ok) throw new Error(`登入驗證失敗（HTTP ${response.status}）`)
  return response.json()
}
