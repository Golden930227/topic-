import { useState } from "react"
import { useNavigate } from "react-router-dom"
import {
  doc,
  serverTimestamp,
  setDoc,
} from "firebase/firestore"

import { db } from "../firebase.js"

function VisitorRegisterPage({
  user,
  onRegistered,
}) {
  const navigate = useNavigate()

  const [formData, setFormData] =
    useState({
      organization: "",
      identity: "學生",
      purpose: "",
    })

  const [submitting, setSubmitting] =
    useState(false)

  function handleChange(event) {
    const { name, value } = event.target

    setFormData((currentData) => ({
      ...currentData,
      [name]: value,
    }))
  }

  async function handleSubmit(event) {
    event.preventDefault()

    if (!formData.organization.trim()) {
      window.alert(
        "請填寫學校或公司名稱。"
      )
      return
    }

    if (!formData.purpose.trim()) {
      window.alert("請填寫參訪目的。")
      return
    }

    setSubmitting(true)

    try {
      await setDoc(
        doc(db, "visitors", user.uid),
        {
          uid: user.uid,
          name:
            user.displayName?.trim() ||
            "未提供姓名",
          email: user.email || "",
          photoURL: user.photoURL || "",
          organization:
            formData.organization.trim(),
          identity: formData.identity,
          purpose:
            formData.purpose.trim(),
          accountType: "visitor",
          createdAt: serverTimestamp(),
          updatedAt: serverTimestamp(),
        }
      )

      onRegistered()

      navigate("/visitor", {
        replace: true,
      })
    } catch (error) {
      console.error(
        "儲存訪客資料失敗：",
        error
      )

      window.alert(
        `註冊失敗：${error.message}`
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="visitor-register-page">
      <section className="visitor-register-card">
        <div className="visitor-heading">
          <span className="visitor-logo">
            W
          </span>

          <div>
            <p className="visitor-eyebrow">
              WIND TURBINE
            </p>

            <h1>訪客資料登記</h1>
          </div>
        </div>

        <p className="visitor-description">
          第一次進入訪客專區前，請先填寫基本資料。
          下次使用相同 Google 帳號即可直接進入。
        </p>

        <form
          className="visitor-form"
          onSubmit={handleSubmit}
        >
          <label>
            Google 姓名

            <input
              type="text"
              value={
                user.displayName ||
                "未提供姓名"
              }
              disabled
            />
          </label>

          <label>
            Google Email

            <input
              type="email"
              value={user.email || ""}
              disabled
            />
          </label>

          <label>
            學校／公司

            <input
              type="text"
              name="organization"
              value={
                formData.organization
              }
              onChange={handleChange}
              placeholder="例如：國立虎尾科技大學"
              maxLength={80}
              required
            />
          </label>

          <label>
            身分類別

            <select
              name="identity"
              value={formData.identity}
              onChange={handleChange}
            >
              <option value="學生">
                學生
              </option>

              <option value="教師">
                教師
              </option>

              <option value="業界">
                業界
              </option>

              <option value="其他">
                其他
              </option>
            </select>
          </label>

          <label>
            參訪目的

            <textarea
              name="purpose"
              value={formData.purpose}
              onChange={handleChange}
              placeholder="例如：查看智慧風力發電監測成果"
              rows="4"
              maxLength={300}
              required
            />
          </label>

          <p className="visitor-privacy-note">
            資料僅用於本專題的訪客識別與使用紀錄。
          </p>

          <div className="visitor-form-actions">
            <button
              type="button"
              className="secondary-action"
              onClick={() => {
                navigate("/")
              }}
              disabled={submitting}
            >
              返回首頁
            </button>

            <button
              type="submit"
              className="primary-action"
              disabled={submitting}
            >
              {submitting
                ? "正在建立資料……"
                : "完成並進入訪客頁"}
            </button>
          </div>
        </form>
      </section>
    </main>
  )
}

export default VisitorRegisterPage