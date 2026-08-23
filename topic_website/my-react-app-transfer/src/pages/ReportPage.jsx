import { useState } from "react"
import { Link } from "react-router-dom"
import Logo from "../components/common/Logo.jsx"
import "../styles/report.css"

function ReportPage() {
  const [notice, setNotice] = useState("")

  const handleSubmit = (event) => {
    event.preventDefault()
    setNotice("功能尚未接上")
  }

  return (
    <div className="report-page">
      <header className="report-navbar"><Logo /><Link to="/worker">返回工作頁</Link></header>
      <main className="report-main">
        <section className="report-panel">
          <p className="report-eyebrow">FEEDBACK</p>
          <h1>問題與回報</h1>
          <p className="report-intro">請填寫問題資訊。目前表單僅供版面預覽，不會傳送資料。</p>
          <form className="report-form" onSubmit={handleSubmit}>
            <label>問題類型<select defaultValue=""><option value="" disabled>請選擇問題類型</option><option>智慧感測器</option><option>人工智能模型</option><option>CNN 監測</option><option>其他</option></select></label>
            <label>標題<input type="text" placeholder="簡短描述問題" required /></label>
            <label>問題描述<textarea rows="7" placeholder="請說明發生情況與操作步驟" required /></label>
            <button type="submit">送出回報</button>
            {notice && <p className="report-notice" role="status">{notice}</p>}
          </form>
        </section>
      </main>
    </div>
  )
}

export default ReportPage
