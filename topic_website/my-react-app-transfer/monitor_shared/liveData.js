export function mergeMeasurements(previous, incoming) {
  const rows = new Map(previous.map(row => [row.measurement_uid, row]))
  incoming.forEach(row => rows.set(row.measurement_uid, row))
  return [...rows.values()].slice(-200)
}

export function mergeEvents(previous, incoming) {
  const rows = new Map(previous.map(row => [row.event_uid, row]))
  incoming.forEach(row => rows.set(row.event_uid, row))
  return [...rows.values()].sort((a, b) => {
    const first = `${a._time?.insertedAt || a.confirmation_time}|${a.event_uid}`
    const second = `${b._time?.insertedAt || b.confirmation_time}|${b.event_uid}`
    return first < second ? 1 : first > second ? -1 : 0
  })
}

const taipei = new Intl.DateTimeFormat('en-CA', {
  timeZone:'Asia/Taipei', year:'numeric', month:'2-digit', day:'2-digit',
  hour:'2-digit', minute:'2-digit', second:'2-digit', hourCycle:'h23',
})

export function formatTaipei(value) {
  if (!value || !/(Z|[+-]\d{2}:\d{2})$/i.test(value)) return '未提供'
  const date = new Date(value)
  if (!Number.isFinite(date.getTime()) || date.getUTCFullYear() <= 2000) return '未提供'
  const parts = Object.fromEntries(taipei.formatToParts(date).map(part => [part.type, part.value]))
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second}`
}

export function timeLabel(row, field) { return formatTaipei(row?.[field]) }

export function freshnessLabel(row) {
  const basis = row?._time?.receivedAt
  const stamp = basis && Date.parse(basis)
  if (!Number.isFinite(stamp) || Date.now()-stamp < -5000) return '接收時間未提供'
  return Date.now()-stamp <= 30000 ? '最近收到資料' : '資料超過 30 秒未更新'
}

export function refreshSeconds() { return 1 }

export function mergeResponse(path, previous, incoming, incremental) {
  if (previous && incoming.windowSeconds === 600 && incoming.serverNow) {
    const cutoff = Date.parse(incoming.serverNow)-600000
    const recent = (rows,field)=>(rows || []).filter(row=>Date.parse(row._time?.receivedAt)>=cutoff)
    if (path === '/api/cnn') {
      const rows=recent(previous.measurementHistory,'measurement_time')
      const expired=rows.length!==previous.measurementHistory.length
      if (expired) previous={...previous,measurementHistory:rows,latestMeasurement:rows.at(-1) || null}
    } else {
      const predictions=recent(previous.predictionHistory,'prediction_time')
      const events=(previous.recentEvents || []).filter(row=>Date.parse(row._time?.receivedAt)>=cutoff)
      const expired=predictions.length!==previous.predictionHistory.length || events.length!==previous.recentEvents.length
      if (expired) previous={...previous,predictionHistory:predictions,recentEvents:events,currentPrediction:predictions[0] || null}
    }
  }
  if (path === '/api/cnn') {
    const old = previous?.measurementHistory || []
    const ids = new Set(old.map(row => row.measurement_uid))
    const added = incoming.measurementHistory.some(row => !ids.has(row.measurement_uid))
    const rows = incremental ? mergeMeasurements(old, incoming.measurementHistory) : incoming.measurementHistory
    return {data:{...incoming, measurementHistory:rows, latestMeasurement:rows.at(-1) || null},added}
  }
  const oldPredictions = new Set((previous?.predictionHistory || []).map(row => row.prediction_uid))
  const oldEvents = new Set((previous?.recentEvents || []).map(row => row.event_uid))
  const added = (incoming.predictionHistory || []).some(row=>!oldPredictions.has(row.prediction_uid)) || (incoming.recentEvents || []).some(row=>!oldEvents.has(row.event_uid))
  return {data:{...incoming,recentEvents:mergeEvents(previous?.recentEvents || [],incoming.recentEvents || [])},added}
}
