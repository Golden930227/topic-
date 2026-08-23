function buildChart(values, width, height, padding) {
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const innerWidth = width - padding * 2
  const innerHeight = height - padding * 2
  const points = values.map((value, index) => {
    const x = padding + (index / Math.max(values.length - 1, 1)) * innerWidth
    const y = padding + ((max - value) / range) * innerHeight
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  return { min, max, points: points.join(" ") }
}

function LineChart({ title, description, data, dataKey, unit, color }) {
  const width = 680
  const height = 230
  const padding = 22
  const values = data.map((item) => item[dataKey])
  const chart = buildChart(values, width, height, padding)

  return (
    <article className="monitor-panel monitor-chart-card">
      <header className="monitor-panel-heading">
        <div>
          <span className="monitor-section-kicker">LIVE TREND</span>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
        <span className="monitor-live-badge"><i /> 即時</span>
      </header>
      <div className="monitor-chart-wrap">
        <div className="monitor-chart-scale">
          <span>{chart.max.toFixed(2)} {unit}</span>
          <span>{chart.min.toFixed(2)} {unit}</span>
        </div>
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${title} 折線圖`}>
          <defs>
            <linearGradient id={`area-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity="0.22" />
              <stop offset="100%" stopColor={color} stopOpacity="0" />
            </linearGradient>
          </defs>
          {[0, 1, 2, 3, 4].map((line) => (
            <line key={line} x1="22" x2="658" y1={22 + line * 46.5} y2={22 + line * 46.5} className="monitor-grid-line" />
          ))}
          <polygon points={`22,208 ${chart.points} 658,208`} fill={`url(#area-${dataKey})`} />
          <polyline points={chart.points} fill="none" stroke={color} strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
          {chart.points.split(" ").map((point, index) => {
            const [cx, cy] = point.split(",")
            return index === values.length - 1 ? <circle key={point} cx={cx} cy={cy} r="6" fill="white" stroke={color} strokeWidth="4" /> : null
          })}
        </svg>
        <div className="monitor-chart-axis"><span>{data[0].time}</span><span>{data.at(-1).time}</span></div>
      </div>
    </article>
  )
}

export default LineChart
