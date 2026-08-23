const statusLabels = {
  voltageSag: "電壓驟降",
  loadSpike: "負載突升",
  severe: "嚴重異常",
}

function RecentEventsTable({ events = [] }) {
  const visibleEvents = events.slice(0, 10)

  return (
    <article className="ai-monitor-panel">
      <header className="ai-panel-heading ai-table-heading">
        <div><span className="ai-section-kicker">RECENT EVENTS</span><h2>近10筆異常事件</h2><p>依偵測時間由新到舊顯示</p></div>
        <span className="ai-record-count">{visibleEvents.length} 筆</span>
      </header>
      <div className="ai-table-scroll">
        <table className="ai-monitor-table">
          <thead><tr><th>偵測時間</th><th>事件類型</th><th>持續時間</th><th>Confidence</th><th>來源</th></tr></thead>
          <tbody>
            {visibleEvents.map((event) => (
              <tr key={event.id}>
                <td className="ai-date-cell">{event.detectedAt}</td>
                <td><span className={`ai-status-pill status-${event.status}`}><span aria-hidden="true">●</span>{event.label || statusLabels[event.status]}</span></td>
                <td>{event.duration}</td>
                <td className="ai-numeric-cell">{Math.round(event.confidence * 100)}%</td>
                <td>{event.source}</td>
              </tr>
            ))}
            {!visibleEvents.length && <tr><td className="ai-empty-cell" colSpan="5">目前沒有異常事件。</td></tr>}
          </tbody>
        </table>
      </div>
    </article>
  )
}

export default RecentEventsTable
