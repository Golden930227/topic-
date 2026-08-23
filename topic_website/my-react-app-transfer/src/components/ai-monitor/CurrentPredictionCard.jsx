const statusMeta = {
  normal: { label: "正常", icon: "✓" },
  voltageSag: { label: "電壓驟降", icon: "↓" },
  loadSpike: { label: "負載突升", icon: "↑" },
  severe: { label: "嚴重異常", icon: "!" },
}

const probabilityItems = [
  { key: "normal", label: "正常" },
  { key: "voltageSag", label: "電壓驟降" },
  { key: "loadSpike", label: "負載突升" },
  { key: "severe", label: "嚴重異常" },
]

function formatPercent(value = 0) {
  return `${Math.round(value * 100)}%`
}

function CurrentPredictionCard({ prediction }) {
  if (!prediction) {
    return (
      <article className="ai-monitor-panel ai-current-card">
        <header className="ai-panel-heading">
          <div><span className="ai-section-kicker">LIVE ANALYSIS</span><h2>AI目前判斷</h2></div>
        </header>
        <p className="ai-empty-state">目前沒有可顯示的模型判斷。</p>
      </article>
    )
  }

  const meta = statusMeta[prediction.status] || statusMeta.normal

  return (
    <article className="ai-monitor-panel ai-current-card">
      <header className="ai-panel-heading">
        <div>
          <span className="ai-section-kicker">LIVE ANALYSIS</span>
          <h2>AI目前判斷</h2>
          <p>綜合電壓、電流與近期趨勢所得的最新模型結果</p>
        </div>
        <span className="ai-updated-time">更新於 {prediction.updatedAt}</span>
      </header>

      <div className="ai-current-summary">
        <div className={`ai-primary-status status-${prediction.status}`}>
          <span className="ai-status-icon" aria-hidden="true">{meta.icon}</span>
          <div><span>目前狀態</span><strong>{prediction.label || meta.label}</strong></div>
        </div>
        <div className="ai-confidence-block">
          <span>Confidence</span>
          <strong>{formatPercent(prediction.confidence)}</strong>
          <div className="ai-confidence-track" aria-label={`信心度 ${formatPercent(prediction.confidence)}`}>
            <span style={{ width: formatPercent(prediction.confidence) }} />
          </div>
          <small>{prediction.confidenceNote}</small>
        </div>
      </div>

      <div className="ai-probability-grid" aria-label="四分類機率">
        {probabilityItems.map((item) => {
          const value = prediction.probabilities?.[item.key] || 0
          return (
            <div className={`ai-probability-item probability-${item.key}`} key={item.key}>
              <div><span>{item.label}</span><strong>{formatPercent(value)}</strong></div>
              <div className="ai-probability-track"><span style={{ width: formatPercent(value) }} /></div>
            </div>
          )
        })}
      </div>
    </article>
  )
}

export default CurrentPredictionCard
