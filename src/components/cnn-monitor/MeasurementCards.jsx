const cards = [
  { key: "vdc", label: "DC 電壓", symbol: "Vdc", unit: "V", digits: 2 },
  { key: "idc", label: "DC 電流", symbol: "Idc", unit: "A", digits: 2 },
  { key: "power", label: "輸出功率", symbol: "Power", unit: "W", digits: 2 },
  { key: "rpm", label: "轉速", symbol: "RPM", unit: "rpm", digits: 0 },
]

function MeasurementCards({ measurement }) {
  return (
    <section className="monitor-kpi-grid" aria-label="即時量測">
      {cards.map((card) => (
        <article className="monitor-kpi-card" key={card.key}>
          <div className={`monitor-kpi-icon monitor-kpi-icon-${card.key}`} aria-hidden="true">
            {card.symbol.slice(0, 1)}
          </div>
          <div>
            <p>{card.label}</p>
            <strong>{measurement[card.key].toFixed(card.digits)}</strong>
            <span>{card.unit}</span>
          </div>
          <small>{card.symbol}</small>
        </article>
      ))}
    </section>
  )
}

export default MeasurementCards
