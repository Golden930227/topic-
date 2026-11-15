import { Activity, Sparkles, Wind, AlertTriangle } from 'lucide-react'
import './App.css'
import { getHomeUrl } from './homeNavigation'

import CurrentPrediction from './components/CurrentPrediction'
import PredictionHistory from './components/PredictionHistory'
import RecentEvents from './components/RecentEvents'

import { categoryConfig as baseCategories } from './data/categories'
import { timeLabel, formatTaipei, freshnessLabel } from '../../../../../../../monitor_shared/liveData.js'
const categoryConfig = { ...baseCategories, unknown: {label:'未提供', english:'Unknown', color:'#777', softColor:'#eee', icon:AlertTriangle} }
import { useLiveData } from './useLiveData'
import ArchivedData from '../../../../../../../monitor_shared/ArchivedData.jsx'
import RefreshStatus from '../../../../../../../monitor_shared/RefreshStatus.jsx'
const key = (value) => ({normal:'normal',voltage_sag:'voltageSag',load_spike:'loadSpike',severe_anomaly:'severeFault',severe_fault:'severeFault'}[value] || 'unknown')
const pct = (value) => value == null ? null : Number(value) * 100
const probabilities = (row) => ({ normal:pct(row.probability_normal), voltageSag:pct(row.probability_voltage_sag), loadSpike:pct(row.probability_load_spike), severeFault:pct(row.probability_severe_anomaly) })
function App({ role = 'visitor', getToken, apiBase = '' }) {
  const live = useLiveData('/api/ai', {role, getToken, apiBase})
  const {data, error, refreshSeconds} = live
  const row = data?.currentPrediction
  const currentPrediction = row ? {result:key(row.predicted_class_key), displayLabel:row.predicted_class_zh || '未提供', confidence:pct(row.confidence), summary:row.final_result || row.decision_state || '未提供', lastUpdated:timeLabel(row,'prediction_time'), probabilities:Object.entries(probabilities(row)).map(([type,value])=>({type,value}))} : null
  const predictionHistory = (data?.predictionHistory || []).map(row=>({id:row.prediction_uid, time:timeLabel(row,'prediction_time'), result:key(row.predicted_class_key), confidence:pct(row.confidence), probabilities:probabilities(row), status:row.decision_state || '未提供', statusKey:row.review_required?'pending':'ended'}))
  const recentEvents = (data?.recentEvents || []).map(row=>({id:row.event_uid, time:formatTaipei(row._time?.occurredAt), type:key(row.class_key), status:'已確認', statusKey:'ended', description:row.class_name_zh || '未提供'}))
  return (
    <div className="app-shell">
      <header className="topbar">
        <a
          className="brand"
          href={getHomeUrl()}
          aria-label="WindMind AI：返回主站首頁"
        >
          <span className="brand-mark">
            <Wind size={23} aria-hidden="true" />
          </span>

          <span>
            <strong>WindMind AI</strong>
            <small>人工智能模型</small>
          </span>
        </a>

        <div className="system-state">
          <Activity size={16} />
          {error ? '刷新失敗，重試中' : row ? freshnessLabel(row) : '尚無預測資料'}
        </div>
      </header>

      <main id="top" className="dashboard">
        <RefreshStatus live={live} />
        <p>最後判斷時間：{timeLabel(row,'prediction_time')}</p>
        <p>接收時間：{formatTaipei(row?._time?.receivedAt)} · SQL 寫入時間：{formatTaipei(row?._time?.insertedAt)}</p>
        {!row && <p className="waiting-hardware" role="status">尚無預測資料</p>}

        <section className="hero-copy">
          <div className="eyebrow">
            <Sparkles size={15} />
            AI POWER MONITORING
          </div>

          <h1>人工智能模型</h1>
          <p>此AI是我們組拿資料下去做偏移學習。</p>
        </section>

        {currentPrediction && <CurrentPrediction prediction={currentPrediction} categories={categoryConfig} />}

        <RecentEvents
          events={recentEvents}
          categories={categoryConfig}
        />

        <PredictionHistory
          history={predictionHistory}
          categories={categoryConfig}
        />
        <ArchivedData kind="ai" getToken={getToken} apiBase={apiBase} />
      </main>

      <footer>
        WindMind AI · SQL Server · 每 {refreshSeconds} 秒刷新
      </footer>
    </div>
  )
}

export default App
