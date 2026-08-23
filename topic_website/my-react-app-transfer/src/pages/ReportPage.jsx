import { useState } from "react"
import { Link } from "react-router-dom"
import { addDoc, collection, serverTimestamp } from "firebase/firestore"
import Logo from "../components/common/Logo.jsx"
import { db } from "../firebase.js"
import "../styles/report.css"

function ReportPage() {
  const [notice, setNotice] = useState("")
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()

    const form = event.currentTarget
    const formData = new FormData(form)

    setSubmitting(true)
    setNotice("")

    try {
      await addDoc(collection(db, "reports"), {
        type: formData.get("type"),
        title: formData.get("title")?.trim(),
        description: formData.get("description")?.trim(),
        status: "new",
        createdAt: serverTimestamp(),
      })

      form.reset()
      setNotice("回報已成功送出，謝謝你的回饋。")
    } catch (error) {
      console.error("送出回報失敗：", error)
      setNotice("送出失敗，請稍後再試。")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="report-page">
      <header className="report-navbar"><Logo /><Link to="/worker">返回工作頁</Link></header>
      <main className="report-main">
        <section className="report-panel">
          <p className="report-eyebrow">FEEDBACK</p>
          <h1>問題與回報</h1>
          <p className="report-intro">請填寫問題資訊，我們會查看並處理你的回報。</p>
          <form className="report-form" onSubmit={handleSubmit}>
            <label>問題類型<select name="type" defaultValue="" required><option value="" disabled>請選擇問題類型</option><option>智慧感測器</option><option>人工智能模型</option><option>CNN 監測</option><option>其他</option></select></label>
            <label>標題<input name="title" type="text" placeholder="簡短描述問題" required /></label>
            <label>問題描述<textarea name="description" rows="7" placeholder="請說明發生情況與操作步驟" required /></label>
            <button type="submit" disabled={submitting}>{submitting ? "送出中…" : "送出回報"}</button>
            {notice && <p className="report-notice" role="status">{notice}</p>}
          </form>
        </section>
      </main>
    </div>
  )
}

export default ReportPage
