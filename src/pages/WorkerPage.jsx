import WorkerDashboard from "../components/worker/WorkerDashboard.jsx"
import WorkerSidebar from "../components/worker/WorkerSidebar.jsx"
import "../styles/worker.css"

function WorkerPage({ user, onAuthButtonClick }) {
  return (
    <div className="worker-page">
      <WorkerSidebar onAuthButtonClick={onAuthButtonClick} />
      <main className="worker-main" id="dashboard">
        <header className="worker-header">
          <div>
            <p className="worker-eyebrow">WORKSPACE</p>
            <h1>風機監測工作頁</h1>
            <p>集中管理感測資料、人工智能模型與設備監測工具。</p>
          </div>
          <div className="worker-user">
            {user?.photoURL && <img src={user.photoURL} alt="" />}
            <span>{user?.displayName || user?.email}</span>
          </div>
        </header>
        <WorkerDashboard />
      </main>
    </div>
  )
}

export default WorkerPage
