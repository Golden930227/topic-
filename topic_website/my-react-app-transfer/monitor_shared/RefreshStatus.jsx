import { formatTaipei } from './liveData.js'
import './refresh-status.css'

export default function RefreshStatus({ live }) {
  const message = live.error ? '刷新失敗，重試中'
    : live.receivedNew ? '收到新資料' : live.lastSuccess ? '監測頁刷新正常 · 暫無新資料' : '正在連線'
  return <section className="refresh-status" aria-label="監測頁刷新狀態">
    <p role="status"><span key={live.successSequence} className={`refresh-dot ${live.error ? 'failed' : live.lastSuccess ? 'pulse' : ''}`} aria-hidden="true" />{message}</p>
    <p>最後成功刷新：<time data-testid="last-success">{formatTaipei(live.lastSuccess)}</time> · 刷新間隔：{live.refreshSeconds} 秒 · 台灣時間</p>
    {live.error && <p role="alert">{live.error}；保留最後成功資料。</p>}
  </section>
}
