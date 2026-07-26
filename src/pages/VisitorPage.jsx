import { Link } from "react-router-dom"

function VisitorPage({
  user,
  onAuthButtonClick,
}) {
  async function handleLogout() {
    await onAuthButtonClick("member")
  }

  return (
    <main className="visitor-page">
      <section className="visitor-shell">
        <header className="visitor-topbar">
          <div>
            <p className="visitor-eyebrow">
              WIND TURBINE
            </p>

            <h1>訪客專區</h1>
          </div>

          <button
            type="button"
            className="secondary-action"
            onClick={handleLogout}
          >
            登出
          </button>
        </header>

        <section className="visitor-profile">
          {user.photoURL ? (
            <img
              className="visitor-avatar"
              src={user.photoURL}
              alt="Google 帳號頭像"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="visitor-avatar-fallback">
              {user.displayName
                ?.charAt(0)
                .toUpperCase() || "V"}
            </div>
          )}

          <div>
            <h2>
              歡迎，
              {user.displayName || "訪客"}
            </h2>

            <p>{user.email}</p>
          </div>
        </section>

        <section className="visitor-grid">
          <article className="visitor-panel">
            <h2>智慧風力發電監測</h2>

            <p>
              查看本專題的系統介紹、感測資料與研究成果。
            </p>

            <Link
              className="primary-action visitor-link"
              to="/"
            >
              查看專題首頁
            </Link>
          </article>

          <article className="visitor-panel">
            <h2>問題回報</h2>

            <p>
              如果使用過程中發現問題，可以前往問題回報頁面。
            </p>

            <Link
              className="secondary-action visitor-link"
              to="/report"
            >
              前往問題回報
            </Link>
          </article>
        </section>

        <aside className="visitor-permission-note">
          <strong>目前身分：訪客</strong>

          <p>
            訪客只能使用訪客專區。若要進入工作人員頁面，
            請聯絡管理員g99226@gmail.com 申請權限。
          </p>
        </aside>
      </section>
    </main>
  )
}

export default VisitorPage