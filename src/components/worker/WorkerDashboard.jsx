import { Link } from "react-router-dom"
import Icon from "../common/Icon.jsx"
import { openCnnMonitor } from "../../utils/openCnnMonitor.js"

const entries = [
  { title: "智慧感測器", description: "檢視風機感測器與即時環境資料。", href: "http://localhost:8501", icon: "social", label: "開啟感測器" },
  { title: "人工智能模型", description: "進入模型分析與推論工作區。", href: "http://localhost:8502", icon: "documentation", label: "開啟模型" },
  { title: "CNN 監測", description: "啟動 Streamlit CNN 即時監測介面。", action: openCnnMonitor, icon: "documentation", label: "啟動監測" },
  { title: "問題回報", description: "記錄系統、設備或監測結果問題。", route: "/report", icon: "social", label: "建立回報" },
]

function CardContent({ entry }) {
  return <><span className="worker-card-icon"><Icon name={entry.icon} size={26} /></span><strong>{entry.title}</strong><span>{entry.description}</span><small>{entry.label} →</small></>
}

function WorkerDashboard() {
  return (
    <section className="worker-dashboard" id="worker-tools" aria-label="工作工具">
      {entries.map((entry) => {
        if (entry.action) return <button className="worker-card" key={entry.title} type="button" onClick={entry.action}><CardContent entry={entry} /></button>
        if (entry.route) return <Link className="worker-card" key={entry.title} to={entry.route}><CardContent entry={entry} /></Link>
        return <a className="worker-card" key={entry.title} href={entry.href} target="_blank" rel="noreferrer"><CardContent entry={entry} /></a>
      })}
    </section>
  )
}

export default WorkerDashboard
