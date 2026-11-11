import { Link } from "react-router-dom"
import Logo from "../common/Logo.jsx"

function WorkerSidebar({ onAuthButtonClick }) {
  return (
    <aside className="worker-sidebar">
      <Logo />
      <nav className="worker-nav" aria-label="工作頁導覽">
        <Link to="/worker">主儀表板</Link>
        <Link to="/internal">內網總網站</Link>
        <Link to="/report">問題與回報</Link>
        <Link to="/">返回首頁</Link>
      </nav>
      <button className="worker-signout" type="button" onClick={onAuthButtonClick}>登出</button>
    </aside>
  )
}

export default WorkerSidebar
