const statusRows = [
  { key: "raspberryPi", label: "Raspberry Pi", labels: { online: "Online", offline: "Offline" } },
  { key: "webSocket", label: "WebSocket", labels: { connected: "Connected", disconnected: "Disconnected" } },
  { key: "sensor", label: "Sensor / Data", labels: { receiving: "Receiving", noData: "No Data" } },
]

function ConnectionStatus({ status }) {
  return (
    <article className="monitor-panel monitor-status-panel">
      <header className="monitor-panel-heading">
        <div><span className="monitor-section-kicker">CONNECTION</span><h2>系統連線狀態</h2><p>裝置與資料通道即時健康狀態</p></div>
      </header>
      <div className="monitor-status-list">
        {statusRows.map((row) => {
          const value = status[row.key]
          const healthy = ["online", "connected", "receiving"].includes(value)
          return <div className="monitor-status-row" key={row.key}><span>{row.label}</span><strong className={healthy ? "status-good" : "status-bad"}><i />{row.labels[value]}</strong></div>
        })}
        <div className="monitor-status-row"><span>Last Update</span><strong className="status-neutral">{status.lastUpdateSeconds.toFixed(1)} sec ago</strong></div>
      </div>
    </article>
  )
}

export default ConnectionStatus
