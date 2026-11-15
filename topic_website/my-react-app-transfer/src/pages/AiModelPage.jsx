import { apiBase, getMonitorToken } from '../utils/monitorClient.js'
import StandaloneAiMonitor from "../../su_data_蘇崇維資料/data_preprocessing/output/pages/ai_model/ai_monitor_web/src/App.jsx"

export default function AiModelPage({ role }) {
  return <StandaloneAiMonitor role={role} getToken={getMonitorToken} apiBase={apiBase} />
}