import { Link } from "react-router-dom"
import Icon from "../common/Icon.jsx"

const entries = [
  { title: "內網總網站", description: "集中管理 WindMind 內部監測、API 與資料庫工具。", route: "/internal", icon: "social", label: "開啟內網" },
  { title: "人工智能模型", description: "進入模型分析與推論工作區。", route: "/ai-model", icon: "documentation", label: "開啟模型" },
  { title: "風機數據監測", description: "查看風機量測資訊。", route: "/cnn-monitor", icon: "documentation", label: "查看監測" },
  { title: "問題回報", description: "記錄系統、設備或監測結果問題。", route: "/report", icon: "social", label: "建立回報" },
]

function CardContent({ entry }) {
  return <><span className="worker-card-icon"><Icon name={entry.icon} size={26} /></span><strong>{entry.title}</strong><span>{entry.description}</span><small>{entry.label} →</small></>
}

function WorkerDashboard() {
  return (
    <section className="worker-dashboard" id="worker-tools" aria-label="工作工具">
      {entries.map((entry) => {
        if (entry.route) return <Link className="worker-card" key={entry.title} to={entry.route}><CardContent entry={entry} /></Link>
        return <a className="worker-card" key={entry.title} href={entry.href} target={entry.external ? "_blank" : undefined} rel={entry.external ? "noopener noreferrer" : undefined}><CardContent entry={entry} /></a>
      })}
    </section>
  )
}

export default WorkerDashboard
