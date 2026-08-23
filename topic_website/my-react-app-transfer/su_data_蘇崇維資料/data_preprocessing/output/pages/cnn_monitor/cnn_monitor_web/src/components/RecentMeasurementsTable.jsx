function RecentMeasurementsTable({ measurements }) {
  const recent = measurements.slice(-15).reverse()
  return (
    <article className="monitor-panel">
      <header className="monitor-panel-heading">
        <div><span className="monitor-section-kicker">RECENT DATA</span><h2>最近接收資料</h2><p>最近 15 筆直流發電機量測紀錄</p></div>
        <span className="monitor-record-count">{recent.length} 筆</span>
      </header>
      <div className="monitor-table-scroll">
        <table className="monitor-table">
          <thead><tr><th>Time</th><th>Vdc</th><th>Idc</th><th>Power</th><th>RPM</th></tr></thead>
          <tbody>{recent.map((item) => <tr key={item.time}><td>{item.time}</td><td>{item.vdc.toFixed(2)} V</td><td>{item.idc.toFixed(2)} A</td><td>{item.power.toFixed(2)} W</td><td>{item.rpm} rpm</td></tr>)}</tbody>
        </table>
      </div>
    </article>
  )
}

export default RecentMeasurementsTable
