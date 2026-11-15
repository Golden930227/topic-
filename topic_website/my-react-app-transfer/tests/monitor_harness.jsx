/* eslint-disable react-refresh/only-export-components -- isolated browser mount entry */
// Only the isolated browser test API recognizes these fixture tokens.
// Production Firebase verification rejects them. This file is not a build entry.
import { createRoot } from 'react-dom/client'
import AiModelPage from '../src/pages/AiModelPage.jsx'
import CNNMonitorPage from '../src/pages/CNNMonitorPage.jsx'
import Ai from '../su_data_蘇崇維資料/data_preprocessing/output/pages/ai_model/ai_monitor_web/src/App.jsx'
import Cnn from '../su_data_蘇崇維資料/data_preprocessing/output/pages/cnn_monitor/cnn_monitor_web/src/App.jsx'
const params = new URLSearchParams(location.search)
const role = params.get('role') || 'visitor'
const getToken = async () => `browser-fixture-${role}`
const Component = params.get('kind') === 'ai' ? Ai : Cnn
// Also keep wrapper imports in the dev module graph so route builds are checked.
void AiModelPage
void CNNMonitorPage
const root = createRoot(document.getElementById('root'))
const unmount = document.createElement('button')
unmount.textContent = 'Unmount monitor'
unmount.id = 'unmount-monitor'
unmount.onclick = () => root.unmount()
document.body.prepend(unmount)
root.render(<Component role={role} getToken={getToken} apiBase="http://127.0.0.1:18080" />)
