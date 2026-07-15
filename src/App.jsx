import { useEffect, useState } from "react"
import {
  BrowserRouter,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom"
import {
  onAuthStateChanged,
  signInWithPopup,
  signOut,
} from "firebase/auth"

import { auth, googleProvider } from "./firebase.js"
import ProtectedRoute from "./components/common/ProtectedRoute.jsx"
import HomePage from "./pages/HomePage.jsx"
import WorkerPage from "./pages/WorkerPage.jsx"
import ReportPage from "./pages/ReportPage.jsx"
import "./App.css"

const allowedEmails = [
  "g99226@gmail.com",
  "chenhongrui416@gmail.com",
  "p124826960@gmail.com",

  // 請確認這個信箱是不是 gmaiil.com。
  // 如果是一般 Gmail，應該改成 44o3249@gmail.com
  "44o3249@gmaiil.com",

  "xindongh522@gmail.com",
]

function AppRoutes() {
  const [user, setUser] = useState(null)
  const [authReady, setAuthReady] = useState(false)

  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser)
      setAuthReady(true)
    })

    return unsubscribe
  }, [])

  const onAuthButtonClick = async () => {
    // 已登入時，按按鈕就是登出
    if (user) {
      try {
        await signOut(auth)
        navigate("/", { replace: true })
      } catch (error) {
        window.alert(`登出失敗：${error.message}`)
      }

      return
    }

    try {
      const result = await signInWithPopup(auth, googleProvider)

      const loginEmail = result.user.email?.trim().toLowerCase()

      if (!loginEmail || !allowedEmails.includes(loginEmail)) {
        await signOut(auth)
        window.alert("此帳號沒有同組成員權限。")
        return
      }

      /*
       * 如果使用者原本直接開 /worker，
       * ProtectedRoute 會把原始位置放進 location.state.from。
       *
       * 登入完成後，回到原本要開的頁面。
       * 沒有原始位置時，預設進入 /worker。
       */
      const destination =
        location.state?.from?.pathname || "/worker"

      navigate(destination, {
        replace: true,
        state: null,
      })
    } catch (error) {
      /*
       * 使用者自己關掉 Google 登入視窗時，
       * Firebase 可能回傳 popup-closed-by-user。
       * 這種情況不需要顯示很長的錯誤。
       */
      if (error.code === "auth/popup-closed-by-user") {
        return
      }

      window.alert(`登入失敗：${error.message}`)
    }
  }

  return (
    <Routes>
      <Route
        path="/"
        element={
          <HomePage
            user={user}
            onAuthButtonClick={onAuthButtonClick}
          />
        }
      />

      <Route
        path="/report"
        element={<ReportPage />}
      />

      <Route
        element={
          <ProtectedRoute
            user={user}
            authReady={authReady}
          />
        }
      >
        <Route
          path="/worker"
          element={
            <WorkerPage
              user={user}
              onAuthButtonClick={onAuthButtonClick}
            />
          }
        />
      </Route>

      {/* 打錯網址時回首頁 */}
      <Route
        path="*"
        element={
          <HomePage
            user={user}
            onAuthButtonClick={onAuthButtonClick}
          />
        }
      />
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}

export default App