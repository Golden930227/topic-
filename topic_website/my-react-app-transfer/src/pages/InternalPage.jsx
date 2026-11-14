import { Link } from "react-router-dom"
import WorkerSidebar from "../components/worker/WorkerSidebar.jsx"
import "../styles/worker.css"

function serviceUrl(configuredUrl, port, path) {
  if (import.meta.env.VITE_WORKER_REMOTE === '1') {
    return ({ 8502: '/sql-monitor/', 8501: '/pipeline/', 8000: '/api/docs' })[port]
  }
  if (import.meta.env.DEV) return `http://127.0.0.1:${port}${path}`
  try {
    const url = new URL(configuredUrl)
    return url.protocol === "https:" ? url.href : null
  } catch {
    return null
  }
}

const services = [
  { title: "專題主網站", description: "專題介紹與訪客入口", route: "/" },
  { title: "AI 模型分析", description: "在 React 內檢視模型預測與監測資料", route: "/ai-model" },
  { title: "CNN 即時監測", description: "在 React 內檢視風機與異常資料", route: "/cnn-monitor" },
  { title: "SQL Streamlit", description: "SQL 資料表與 Gateway 日誌", url: serviceUrl(import.meta.env.VITE_SQL_MONITOR_URL, 8502, "/") },
  { title: "Pipeline 監控中心", description: "Gateway、SQL、API 流程監控", url: serviceUrl(import.meta.env.VITE_PIPELINE_MONITOR_URL, 8501, "/") },
  { title: "API 互動文件", description: "查看後端端點與測試資料回應", url: serviceUrl(import.meta.env.VITE_API_DOCS_URL, 8000, "/docs") },
]

export default function InternalPage({ onAuthButtonClick }) {
  return (
    <div className="worker-page">
      <WorkerSidebar onAuthButtonClick={onAuthButtonClick} />
      <main className="worker-main">
        <header className="worker-header">
          <div>
            <p className="worker-eyebrow">WINDMIND WORKSPACE</p>
            <h1>內網總網站</h1>
            <p>集中開啟模型分析、風機監測、SQL 與流程監控工具。</p>
            <p>後台服務需由監測電腦啟動；連線狀態請以各工具實際回應為準。</p>
          </div>
        </header>
        <section className="worker-dashboard" aria-label="內網服務">
          {services.map((service) => {
            const content = <><strong>{service.title}</strong><span>{service.description}</span><small>{service.route || service.url ? "開啟工具 →" : "遠端連線尚未設定"}</small></>
            return service.route
              ? <Link className="worker-card" key={service.title} to={service.route}>{content}</Link>
              : service.url
                ? <a className="worker-card" key={service.title} href={service.url} target="_blank" rel="noopener noreferrer">{content}</a>
                : <div className="worker-card" key={service.title}>{content}</div>
          })}
        </section>
      </main>
    </div>
  )
}
