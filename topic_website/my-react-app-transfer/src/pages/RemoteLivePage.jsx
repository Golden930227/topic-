import { useEffect, useState } from 'react'

export default function RemoteLivePage({ kind }) {
  const [result, setResult] = useState({ state: 'loading', data: null })
  useEffect(() => {
    let active = true
    const load = async () => {
      try {
        const response = await fetch(`/api/${kind}`, { cache: 'no-store' })
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const data = await response.json()
        if (!data.connected) throw new Error('Backend disconnected')
        if (active) setResult({ state: 'online', data })
      } catch {
        if (active) setResult({ state: 'offline', data: null })
      }
    }
    load()
    const timer = setInterval(load, 15000)
    return () => { active = false; clearInterval(timer) }
  }, [kind])

  const title = kind === 'ai' ? 'AI 模型監測' : 'CNN 即時監測'
  const current = kind === 'ai' ? result.data?.currentPrediction : result.data?.latestMeasurement
  const history = kind === 'ai' ? result.data?.predictionHistory : result.data?.measurementHistory
  return (
    <main className="access-page">
      <section className="access-card" style={{ maxWidth: 900, width: '100%' }}>
        <p><a href="/internal">← 返回員工入口</a></p>
        <h1>{title}</h1>
        <p role="status">{result.state === 'online' ? '後端連線正常' : result.state === 'loading' ? '正在連接後端…' : '後端離線或資料庫不可用'}</p>
        {result.state === 'online' && <>
          <h2>最新資料</h2>
          {current ? <pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify(current, null, 2)}</pre> : <p>目前沒有資料</p>}
          <p>歷史資料筆數：{history?.length ?? 0}</p>
        </>}
      </section>
    </main>
  )
}
