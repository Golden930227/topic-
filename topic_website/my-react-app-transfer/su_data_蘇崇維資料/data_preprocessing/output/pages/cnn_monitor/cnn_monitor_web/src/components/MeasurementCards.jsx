const cards = [
  { key: "vin", label: "Vin", symbol: "Vin", unit: "V", digits: 2 },
  { key: "vo", label: "Vo", symbol: "Vo", unit: "V", digits: 2 },
  { key: "vl", label: "VL", symbol: "VL", unit: "V", digits: 2 },
  { key: "duty", label: "Duty", symbol: "Duty", unit: "%", digits: 0 },
  { key: "estimated_rpm", label: "RPM", symbol: "RPM", unit: "rpm", digits: 0 },
  { key: "estimated_power_w", label: "Power", symbol: "Power", unit: "mW", digits: 0, scale: 1000 },
]

function MeasurementCards({ measurement }) {
  return (
    <section className="monitor-kpi-grid" aria-label="即時量測">
      {cards.map((card) => (
        <article className="monitor-kpi-card" key={card.key}>
          <div className={`monitor-kpi-icon monitor-kpi-icon-${card.key}`} aria-hidden="true">
            {card.symbol}
          </div>
          <div>
            <strong>
              {measurement?.[card.key] == null
                ? '未提供'
                : (measurement[card.key] * (card.scale ?? 1)).toFixed(card.digits)}
            </strong>
            <span>{card.unit}</span>
          </div>
        </article>
      ))}
    </section>
  )
}

export default MeasurementCards
