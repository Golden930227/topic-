import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import WorkerPage from './pages/WorkerPage.jsx'
import InternalPage from './pages/InternalPage.jsx'
import RemoteLivePage from './pages/RemoteLivePage.jsx'

export default function RemoteWorkerApp() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/internal" replace />} />
        <Route path="/worker" element={<WorkerPage />} />
        <Route path="/internal" element={<InternalPage />} />
        <Route path="/ai-model" element={<RemoteLivePage kind="ai" />} />
        <Route path="/cnn-monitor" element={<RemoteLivePage kind="cnn" />} />
        <Route path="*" element={<Navigate to="/internal" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
