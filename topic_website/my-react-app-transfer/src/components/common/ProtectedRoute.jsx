import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom"

function ProtectedRoute({ user, authReady, onMemberLogin }) {
  const location = useLocation()

  /*
   * Firebase 還在確認登入狀態時，
   * 不能直接判斷 user 為空並送回首頁。
   */
  if (!authReady) {
    return (
      <div className="route-loading">
        正在確認登入狀態…
      </div>
    )
  }

  /*
   * 尚未登入：
   * 先回首頁，並記住原本想去的網址。
   */
  if (!user) {
    if (import.meta.env.VITE_WORKER_REMOTE === '1') {
      return (
        <main className="access-page">
          <section className="access-card">
            <h1>同組 Google 登入</h1>
            <p>Cloudflare Email 驗證已完成。請使用同組 Google 帳號登入 WindMind。</p>
            <button type="button" className="primary-action" onClick={() => onMemberLogin('member')}>
              同組 Google 登入
            </button>
          </section>
        </main>
      )
    }
    return (
      <Navigate
        to="/"
        replace
        state={{ from: location }}
      />
    )
  }

  /*
   * 已登入：
   * 顯示 /worker 等被保護的頁面。
   */
  return <Outlet />
}

export default ProtectedRoute
