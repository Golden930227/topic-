function DataStatus({ status }) {
  const isStale = status.state === "interrupted"
  return (
    <article className="monitor-panel monitor-status-panel">
      <header className="monitor-panel-heading">
        <div><span className="monitor-section-kicker">DATA HEALTH</span><h2>即時資料狀態</h2><p>確認最新量測是否可供後續服務使用</p></div>
        <span className={`monitor-data-state ${isStale ? "is-bad" : "is-good"}`}><i />{isStale ? "資料中斷" : "資料狀態：正常"}</span>
      </header>
      <dl className="monitor-data-grid">
        <div><dt>Missing Values</dt><dd>{status.missingValues}</dd></div>
        <div><dt>Data Delay</dt><dd>{status.delayMs} ms</dd></div>
        <div><dt>Sampling</dt><dd className={isStale ? "text-bad" : "text-good"}>{isStale ? "中斷" : "正常"}</dd></div>
        <div><dt>Latest Timestamp</dt><dd>{status.latestTimestamp}</dd></div>
      </dl>
    </article>
  )
}

export default DataStatus
