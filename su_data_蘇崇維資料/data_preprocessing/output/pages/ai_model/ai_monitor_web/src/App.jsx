import { useEffect, useState } from 'react'
import { Activity, Sparkles, Wind } from 'lucide-react'
import './App.css'

import CurrentPrediction from './components/CurrentPrediction'
import PredictionHistory from './components/PredictionHistory'
import RecentEvents from './components/RecentEvents'

import {
  categoryConfig,
  predictionCycle,
  predictionHistory,
  recentEvents,
} from './data/mockData'

function App() {
  const [predictionIndex, setPredictionIndex] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setPredictionIndex(
        (currentIndex) =>
          (currentIndex + 1) % predictionCycle.length
      )
    }, 3000)

    return () => clearInterval(timer)
  }, [])

  const currentPrediction = {
    ...predictionCycle[predictionIndex],
    lastUpdated: new Date().toLocaleTimeString('zh-TW', {
      hour12: false,
    }),
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a
          className="brand"
          href="#top"
          aria-label="風智監測首頁"
        >
          <span className="brand-mark">
            <Wind size={23} aria-hidden="true" />
          </span>

          <span>
            <strong>WindMind AI</strong>
            <small>風力發電智慧監測</small>
          </span>
        </a>

        <div className="system-state">
          <Activity size={16} />
          系統運作正常
        </div>
      </header>

      <main id="top" className="dashboard">
        <section className="hero-copy">
          <div className="eyebrow">
            <Sparkles size={15} />
            AI POWER MONITORING
          </div>

          <h1>訓練模型</h1>
          <p>此AI是我們組拿資料下去訓練的。</p>
        </section>

        <CurrentPrediction
          prediction={currentPrediction}
          categories={categoryConfig}
        />

        <RecentEvents
          events={recentEvents}
          categories={categoryConfig}
        />

        <PredictionHistory
          history={predictionHistory}
          categories={categoryConfig}
        />
      </main>

      <footer>
        WindMind AI Monitoring · Frontend demonstration
      </footer>
    </div>
  )
}

export default App