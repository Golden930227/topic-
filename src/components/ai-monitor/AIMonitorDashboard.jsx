import "./ai-monitor.css"
import CurrentPredictionCard from "./CurrentPredictionCard.jsx"
import PredictionHistoryTable from "./PredictionHistoryTable.jsx"
import RecentEventsTable from "./RecentEventsTable.jsx"

function AIMonitorDashboard({ currentPrediction, recentEvents = [], predictionHistory = [] }) {
  return (
    <section className="ai-monitor-dashboard" aria-label="人工智能監測儀表板">
      <CurrentPredictionCard prediction={currentPrediction} />
      <RecentEventsTable events={recentEvents} />
      <PredictionHistoryTable predictions={predictionHistory} />
    </section>
  )
}

export default AIMonitorDashboard
