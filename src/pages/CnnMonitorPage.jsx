import { Link } from "react-router-dom"
import ConnectionStatus from "../components/cnn-monitor/ConnectionStatus.jsx"
import DataStatus from "../components/cnn-monitor/DataStatus.jsx"
import LineChart from "../components/cnn-monitor/LineChart.jsx"
import MeasurementCards from "../components/cnn-monitor/MeasurementCards.jsx"
import RecentMeasurementsTable from "../components/cnn-monitor/RecentMeasurementsTable.jsx"
import { connectionStatus, dataStatus, latestMeasurement, measurementHistory } from "../data/monitorMockData.js"
import "../components/cnn-monitor/cnn-monitor.css"

function CnnMonitorPage() {
  const resolvedDataStatus = {
    ...dataStatus,
    state: connectionStatus.lastUpdateSeconds > dataStatus.staleAfterSeconds
      ? "interrupted"
      : dataStatus.state,
  }

  return (
    <main className="cnn-monitor-page">
      <div className="cnn-monitor-shell">
        <header className="cnn-monitor-hero">
          <div>
            <span className="monitor-eyebrow">DC WIND TURBINE MONITORING</span>
            <h1>風機即時監測</h1>
            <p>換向器式直流發電機 · DC 實機量測</p>
          </div>
          <div className="monitor-hero-actions"><span className="monitor-live-badge"><i /> 系統運行中</span><Link to="/worker">返回工作區</Link></div>
        </header>

        <MeasurementCards measurement={latestMeasurement} />
        <section className="monitor-chart-grid" aria-label="即時曲線">
          <LineChart title="DC Voltage vs Time" description="最近 24 筆 DC 電壓量測" data={measurementHistory} dataKey="vdc" unit="V" color="#7548d1" />
          <LineChart title="DC Current vs Time" description="最近 24 筆 DC 電流量測" data={measurementHistory} dataKey="idc" unit="A" color="#23875a" />
        </section>
        <section className="monitor-status-grid" aria-label="系統與資料狀態">
          <ConnectionStatus status={connectionStatus} />
          <DataStatus status={resolvedDataStatus} />
        </section>
        <RecentMeasurementsTable measurements={measurementHistory} />
      </div>
    </main>
  )
}

export default CnnMonitorPage
