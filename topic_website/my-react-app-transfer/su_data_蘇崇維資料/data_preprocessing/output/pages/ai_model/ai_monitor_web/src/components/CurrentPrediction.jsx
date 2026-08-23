import {
  BrainCircuit,
  CheckCircle2,
  Clock3,
} from 'lucide-react'

import SectionHeader from './SectionHeader'

export default function CurrentPrediction({
  prediction,
  categories,
}) {
  const current = categories[prediction.result]
  const CurrentIcon = current.icon

  const displayLabel =
    prediction.displayLabel ?? current.label

  return (
    <section className="panel prediction-panel">
      <SectionHeader
        icon={BrainCircuit}
        title="AI目前判斷"
        subtitle="即時分類結果與信心度"
        action={
          <div className="live-badge">
            <span />
            即時監測中
          </div>
        }
      />

      <div className="prediction-layout">
        <article className="result-card">
          <div
            className="result-icon"
            style={{ '--category': current.color }}
          >
            <CurrentIcon size={31} aria-hidden="true" />
          </div>

          <div className="result-label">
            目前判斷
          </div>

          <div className="result-main">
            <div>
              <h3 style={{ color: current.color }}>
                {displayLabel}
              </h3>

              <p>{prediction.summary}</p>
            </div>

            <CheckCircle2
              className="result-check"
              size={25}
              aria-label={`目前狀態：${displayLabel}`}
            />
          </div>

          <div className="confidence-row">
            <span>判斷信心度</span>
            <strong>
              {prediction.confidence.toFixed(1)}%
            </strong>
          </div>

          <div
            className="progress-track confidence-track"
            aria-label={`判斷信心度 ${prediction.confidence}%`}
          >
            <span
              style={{
                width: `${prediction.confidence}%`,
                background: current.color,
              }}
            />
          </div>

          <div className="prediction-time">
            <Clock3 size={15} />
            最後判斷時間：{prediction.lastUpdated}
          </div>
        </article>

        <div className="probability-card">
          <div className="subsection-title">
            <div>
              <strong>四分類即時機率</strong>
              <span>模型輸出分布</span>
            </div>

            <span className="total-tag">
              TOTAL 100%
            </span>
          </div>

          <div className="probability-list">
            {prediction.probabilities.map((item) => {
              const category = categories[item.type]
              const Icon = category.icon

              return (
                <div
                  className="probability-row"
                  key={item.type}
                >
                  <span
                    className="category-icon"
                    style={{
                      '--category': category.color,
                    }}
                  >
                    <Icon size={18} />
                  </span>

                  <span className="category-name">
                    <strong>{category.label}</strong>
                    <small>{category.english}</small>
                  </span>

                  <div className="progress-track">
                    <span
                      style={{
                        width: `${item.value}%`,
                        background: category.color,
                      }}
                    />
                  </div>

                  <strong className="probability-value">
                    {item.value.toFixed(1)}%
                  </strong>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}