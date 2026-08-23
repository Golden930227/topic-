const statusMeta = {
  normal: { label: "正常", icon: "✓" },
  voltageSag: { label: "電壓驟降", icon: "↓" },
  loadSpike: { label: "負載突升", icon: "↑" },
  severe: { label: "嚴重異常", icon: "!" },
}

function PredictionHistoryTable({ predictions = [] }) {
  const visiblePredictions = predictions.slice(0, 10)

  return (
    <article className="ai-monitor-panel">
      <header className="ai-panel-heading ai-table-heading">
        <div><span className="ai-section-kicker">PREDICTION HISTORY</span><h2>近10筆歷史結果</h2><p>保留每次模型判斷與四分類機率</p></div>
        <span className="ai-record-count">{visiblePredictions.length} 筆</span>
      </header>
      <div className="ai-table-scroll">
        <table className="ai-monitor-table ai-history-table">
          <thead><tr><th>判斷時間</th><th>AI結果</th><th>正常</th><th>電壓驟降</th><th>負載突升</th><th>嚴重異常</th><th>Confidence</th></tr></thead>
          <tbody>
            {visiblePredictions.map((prediction) => {
              const meta = statusMeta[prediction.status] || statusMeta.normal
              return (
                <tr key={prediction.id}>
                  <td className="ai-date-cell">{prediction.predictedAt}</td>
                  <td><span className={`ai-status-pill status-${prediction.status}`}><span aria-hidden="true">{meta.icon}</span>{prediction.label || meta.label}</span></td>
                  <td className="ai-numeric-cell">{Math.round(prediction.probabilities.normal * 100)}%</td>
                  <td className="ai-numeric-cell">{Math.round(prediction.probabilities.voltageSag * 100)}%</td>
                  <td className="ai-numeric-cell">{Math.round(prediction.probabilities.loadSpike * 100)}%</td>
                  <td className="ai-numeric-cell">{Math.round(prediction.probabilities.severe * 100)}%</td>
                  <td className="ai-numeric-cell ai-confidence-value">{Math.round(prediction.confidence * 100)}%</td>
                </tr>
              )
            })}
            {!visiblePredictions.length && <tr><td className="ai-empty-cell" colSpan="7">目前沒有歷史模型結果。</td></tr>}
          </tbody>
        </table>
      </div>
    </article>
  )
}

export default PredictionHistoryTable
