import { Navigate, Outlet, useLocation } from "react-router-dom"

function ProtectedRoute({ user, authReady }) {
  const location = useLocation()
  if (!authReady) return <div className="route-loading">正在確認登入狀態…</div>
  return user ? <Outlet /> : <Navigate to="/" replace state={{ from: location }} />
}

export default ProtectedRoute
