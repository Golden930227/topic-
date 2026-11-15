import { apiBase, getMonitorToken } from '../utils/monitorClient.js'
import StandaloneCNNMonitor from "../../su_data_蘇崇維資料/data_preprocessing/output/pages/cnn_monitor/cnn_monitor_web/src/App.jsx"

export default function CNNMonitorPage({ role }) {
  return (
    <div className="standalone-cnn-page">
      <StandaloneCNNMonitor role={role} getToken={getMonitorToken} apiBase={apiBase} />
    </div>
  )
}