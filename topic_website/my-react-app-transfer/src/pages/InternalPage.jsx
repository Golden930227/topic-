import { Link } from "react-router-dom"
import WorkerSidebar from "../components/worker/WorkerSidebar.jsx"
import "../styles/worker.css"

const services = [
  { title: "專題主網站", description: "專題介紹與訪客入口", route: "/" },
  { title: "AI 模型分析", description: "在 React 內檢視模型預測與監測資料", route: "/ai-model" },
  { title: "CNN 即時監測", description: "在 React 內檢視風機與異常資料", route: "/cnn-monitor" },
  { title: "SQL Streamlit", description: "SQL 資料表與 Gateway 日誌", port: 8502, path: "/" },
  { title: "Pipeline 監控中心", description: "Gateway、SQL、API 流程監控；使用本機存取碼登入", port: 8501, path: "/" },
  { title: "API 互動文件", description: "查看後端端點與測試資料回應", port: 8000, path: "/docs" },
  { title: "獨立 AI 儀表板", description: "開啟獨立 AI 監看網站", port: 5174, path: "/" },
  { title: "獨立 CNN 儀表板", description: "開啟獨立 CNN 監看網站", port: 5175, path: "/" },
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
            <p>本機服務入口。請先執行一鍵啟動；資料狀態請以各工具實際回應為準。</p>
          </div>
        </header>
        <section className="worker-dashboard" aria-label="內網服務">
          {services.map((service) => {
            const content = <><strong>{service.title}</strong><span>{service.description}</span><small>開啟工具 →</small></>
            return service.route
              ? <Link className="worker-card" key={service.title} to={service.route}>{content}</Link>
              : <a className="worker-card" key={service.title} href={`http://127.0.0.1:${service.port}${service.path}`} target="_blank" rel="noopener noreferrer">{content}</a>
          })}
        </section>
      </main>
    </div>
  )
}
