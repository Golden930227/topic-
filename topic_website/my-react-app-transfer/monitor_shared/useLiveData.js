import { useEffect, useState } from 'react'
import { mergeResponse, refreshSeconds } from './liveData.js'
import { fetchApiResponse } from './apiResponse.js'

export function useLiveData(path, { role = 'visitor', getToken, apiBase = '' } = {}) {
  const interval = refreshSeconds(role)
  const [state, setState] = useState({ data: null, error: '', lastSuccess: null, successSequence:0, receivedNew:false })
  useEffect(() => {
    let active = true
    let timer
    let controller
    let data = null
    let eventCursor = null
    const load = async () => {
      const started = Date.now()
      controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 15000)
      try {
        if (!getToken) throw new Error('請由主網站登入後開啟監測頁')
        const token = await getToken()
        if (!active) return
        let more = true
        while (more && active) {
          const params = new URLSearchParams()
          if (path === '/api/ai' && eventCursor) params.set('event_after', eventCursor)
          const response = await fetchApiResponse(`${apiBase}${path}${params.size ? '?' + params : ''}`, {
            headers: { Authorization: `Bearer ${token}` }, credentials: 'include',
            cache: 'no-store', signal: controller.signal,
          })
          if (!response.ok) throw new Error(`連線異常（HTTP ${response.status}）`)
          const incoming = await response.json()
          if (!incoming.connected) throw new Error(path === '/api/cnn' ? '等待可讀取的 CSV 資料' : 'SQL 連線異常')
          if (incoming.sourcePolicy !== (path === '/api/cnn' ? 'csv-latest' : 'sql-latest')) throw new Error('資料來源檢查尚未就緒')
          if (!active) return
          const merged = mergeResponse(path, data, incoming, false)
          data = merged.data
          if (path === '/api/cnn') {
            more = false
          } else {
            const previousCursor = eventCursor
            eventCursor = incoming.eventCursor || eventCursor
            more = incoming.eventsHaveMore && eventCursor !== previousCursor
          }
          setState(previous => ({data, error:'', lastSuccess:new Date().toISOString(),
            successSequence:previous.successSequence+1, receivedNew:merged.added}))
        }
      } catch (error) {
        if (active) setState(previous => ({ ...previous, error: error.name === 'AbortError' ? '連線逾時；保留最後成功資料' : error.message }))
      } finally {
        clearTimeout(timeout)
        if (active) timer = setTimeout(load, Math.max(0, interval * 1000 - (Date.now() - started)))
      }
    }
    // No overlap: schedule the next cycle only after all catch-up pages finish.
    setState({ data: null, error: '', lastSuccess: null, successSequence:0, receivedNew:false })
    load()
    return () => { active = false; clearTimeout(timer); controller?.abort() }
  }, [path, role, getToken, apiBase, interval])
  return { ...state, refreshSeconds: interval }
}
