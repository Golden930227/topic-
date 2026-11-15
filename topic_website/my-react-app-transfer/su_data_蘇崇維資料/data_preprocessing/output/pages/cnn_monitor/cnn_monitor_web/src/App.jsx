import LineChart from "./components/LineChart.jsx"
import MeasurementCards from "./components/MeasurementCards.jsx"
import RecentMeasurementsTable from "./components/RecentMeasurementsTable.jsx"
import { useLiveData } from "./useLiveData.js"
import { freshnessLabel, formatTaipei } from "../../../../../../../monitor_shared/liveData.js"
import ArchivedData from "../../../../../../../monitor_shared/ArchivedData.jsx"
import RefreshStatus from "../../../../../../../monitor_shared/RefreshStatus.jsx"
import "./cnn-monitor.css"

function App({ role = 'visitor', getToken, apiBase = '' }) {
  const live = useLiveData('/api/cnn', {role, getToken, apiBase})
  const {data} = live
  const number = value=>value == null ? null : Number(value)
  const measurementHistory = (data?.measurementHistory || []).map(row=>({id:row.measurement_uid, time:formatTaipei(row._time?.insertedAt), sampleMillis:Date.parse(row._time?.insertedAt), vdc:number(row.vout2), idc:number(row.ids), power:number(row.load_power_est), rpm:number(row.rpm)}))
  const row = data?.latestMeasurement
  return <main className="cnn-monitor-page"><div className="cnn-monitor-shell">
    <header className="cnn-monitor-hero"><div>
      <a href="/">返回首頁</a><span className="monitor-eyebrow">DC WIND TURBINE MONITORING</span>
      <h1>CNN 即時監測</h1><p>風機量測資料</p>
      <p>最新 SQL 入庫時間：{formatTaipei(row?._time?.insertedAt)}</p>
      <p>曲線保留最近 200 筆量測</p>
    </div></header>
    <RefreshStatus live={live} />
    {!row && <p className="waiting-hardware" role="status">等待資料</p>}
    {row && <>
      <MeasurementCards measurement={measurementHistory.at(-1)} />
      <section className="monitor-chart-grid" aria-label="量測曲線">
        <LineChart title="DC Voltage vs Time" description="最近 200 筆電壓量測" data={measurementHistory} dataKey="vdc" unit="V" color="#7548d1" />
        <LineChart title="DC Current vs Time" description="最近 200 筆電流量測" data={measurementHistory} dataKey="idc" unit="A" color="#23875a" />
      </section>
    </>}
    <section className="monitor-panel"><h2>資料來源與硬體狀態</h2>
      <p>{freshnessLabel(row)}；裝置心跳未提供。</p>
      <p>CSV 內接收時間：{formatTaipei(row?._time?.receivedAt)} · SQL 寫入時間：{formatTaipei(row?._time?.insertedAt)}</p>
    </section>
    <RecentMeasurementsTable measurements={measurementHistory} />
    <ArchivedData kind="cnn" getToken={getToken} apiBase={apiBase} />
  </div></main>
}
export default App
