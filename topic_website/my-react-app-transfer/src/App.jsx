import {
  useEffect,
  useState,
} from "react"

import {
  BrowserRouter,
  Navigate,
  Outlet,
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

import {
  auth,
  googleProvider,
} from "./firebase.js"

import ProtectedRoute from "./components/common/ProtectedRoute.jsx"

import HomePage from "./pages/HomePage.jsx"
import WorkerPage from "./pages/WorkerPage.jsx"
import InternalPage from "./pages/InternalPage.jsx"
import ReportPage from "./pages/ReportPage.jsx"
import AiModelPage from "./pages/AiModelPage.jsx"
import CNNMonitorPage from "./pages/CNNMonitorPage.jsx"
import RemoteLivePage from "./pages/RemoteLivePage.jsx"
import RemoteWorkerApp from "./RemoteWorkerApp.jsx"

import "./App.css"
import "./pages/VisitorPages.css"

const allowedEmails = [
  "g99226@gmail.com",
  "chenhongrui416@gmail.com",
  "p124826960@gmail.com",

  // 請確認這個是不是拼錯。
  // 如果是一般 Gmail，可能應為 44o3249@gmail.com
  "44o3249@gmaiil.com",

  "xindongh522@gmail.com",
]

const workerTunnelUrl = import.meta.env.VITE_WORKER_TUNNEL_URL

function getWorkerTunnelUrl() {
  try {
    const url = new URL(workerTunnelUrl)
    if (url.protocol !== 'https:' || !url.hostname.endsWith('.trycloudflare.com')) return null
    return `${url.origin}/internal`
  } catch {
    return null
  }
}

function isAllowedMember(email) {
  const normalizedEmail =
    email?.trim().toLowerCase()

  return Boolean(
    normalizedEmail &&
      allowedEmails.includes(
        normalizedEmail
      )
  )
}

async function getAccessStatus(currentUser) {
  await auth.authStateReady()
  const activeUser = auth.currentUser
  if (!activeUser || activeUser.uid !== currentUser?.uid) {
    throw new Error('登入帳號已改變，請重新登入。')
  }
  return isAllowedMember(activeUser.email) ? 'member' : 'visitor'
}

function AccessLoading() {
  return (
    <main className="access-page">
      <section className="access-card">
        <h1>正在確認登入資料</h1>
        <p>請稍候……</p>
      </section>
    </main>
  )
}

function VisitorAccessGate({
  user,
  authReady,
  accessStatus,
}) {
  const location = useLocation()

  if (
    !authReady ||
    (user &&
      accessStatus === "checking")
  ) {
    return <AccessLoading />
  }

  if (!user) {
    return (
      <Navigate
        to="/"
        replace
        state={{ from: location }}
      />
    )
  }

  if (
    accessStatus === "member" ||
    accessStatus === "visitor"
  ) {
    return <Outlet />
  }

  return (
    <main className="access-page">
      <section className="access-card">
        <h1>
          無法確認登入狀態
        </h1>

        <p>
          請重新整理頁面後再試一次。
        </p>
      </section>
    </main>
  )
}

function WorkerAccessGate({
  user,
  authReady,
  accessStatus,
}) {
  const location = useLocation()
  const navigate = useNavigate()

  if (
    !authReady ||
    (user &&
      accessStatus === "checking")
  ) {
    return <AccessLoading />
  }

  if (!user) {
    return (
      <Navigate
        to="/"
        replace
        state={{ from: location }}
      />
    )
  }

  /*
   * /worker 只允許白名單中的 member。
   * visitor 不能進入。
   */
  if (
    accessStatus === "member"
  ) {
    return <Outlet />
  }

  if (
    accessStatus === "error"
  ) {
    return (
      <main className="access-page">
        <section className="access-card">
          <h1>
            無法確認工作人員權限
          </h1>

          <p>
            請重新整理頁面後再試一次。
          </p>

          <button
            type="button"
            className="primary-action"
            onClick={() => {
              navigate("/", {
                replace: true,
              })
            }}
          >
            返回首頁
          </button>
        </section>
      </main>
    )
  }

  return (
    <main className="access-page">
      <section className="access-card">
        <h1>
          沒有工作人員權限
        </h1>

        <p>
          此頁面僅限專題成員使用。如需工作人員權限，
          請聯絡管理員將你的 Google Email
          加入白名單。
        </p>

        <button
          type="button"
          className="primary-action"
          onClick={() => {
            navigate("/", {
              replace: true,
            })
          }}
        >
          返回首頁
        </button>
      </section>
    </main>
  )
}

function AppRoutes() {
  const [user, setUser] =
    useState(null)

  const [
    authReady,
    setAuthReady,
  ] = useState(false)

  const [
    accessStatus,
    setAccessStatus,
  ] = useState("signed-out")

  const navigate = useNavigate()

  useEffect(() => {
    const unsubscribe =
      onAuthStateChanged(
        auth,
        (currentUser) => {
          setUser(currentUser)
          setAuthReady(true)
        }
      )

    return unsubscribe
  }, [])

  useEffect(() => {
    let cancelled = false

    if (!user) {
      return undefined
    }

    queueMicrotask(() => {
      if (!cancelled) setAccessStatus("checking")
    })

    getAccessStatus(user)
      .then((status) => {
        if (!cancelled) {
          setAccessStatus(status)
        }
      })
      .catch((error) => {
        console.error(
          "確認登入權限失敗：",
          error
        )

        if (!cancelled) {
          setAccessStatus("error")
        }
      })

    return () => {
      cancelled = true
    }
  }, [user])

  const onAuthButtonClick =
    async (
      loginMode = "member"
    ) => {
      /*
       * 已登入時：
       * - 按同組按鈕：進入受 Cloudflare 保護的員工內網
       * - 按訪客按鈕：進訪客頁
       * - 按登出按鈕：登出
       */
      if (user) {
        if (loginMode === "member") {
          if (!isAllowedMember(user.email)) {
            window.alert("此帳號沒有工作人員權限，請聯絡管理員。")
            return
          }
          const destination = getWorkerTunnelUrl()
          if (destination) window.location.assign(destination)
          else window.alert("員工遠端入口目前未啟動，請稍後再試。")
          return
        }
        if (
          loginMode === "visitor"
        ) {
          try {
            const status =
              await getAccessStatus(
                user
              )

            setAccessStatus(status)

            navigate(
              "/visitor",
              {
                replace: true,
              }
            )
          } catch (error) {
            window.alert(
              `確認訪客登入失敗：${error.message}`
            )
          }

          return
        }

        try {
          await signOut(auth)

          navigate("/", {
            replace: true,
          })
        } catch (error) {
          window.alert(
            `登出失敗：${error.message}`
          )
        }

        return
      }

      try {
        const result =
          await signInWithPopup(
            auth,
            googleProvider
          )

        const signedInUser =
          result.user

        setUser(signedInUser)

        /*
         * 同組登入：
         * 必須存在 allowedEmails 白名單。
         */
        if (
          loginMode === "member"
        ) {
          if (
            !isAllowedMember(
              signedInUser.email
            )
          ) {
            await signOut(auth)

            window.alert(
              "此帳號沒有工作人員權限，請聯絡管理員。"
            )

            navigate("/", {
              replace: true,
            })

            return
          }

          setAccessStatus("member")

          if (import.meta.env.VITE_WORKER_REMOTE === '1') {
            navigate("/worker", { replace: true })
          } else {
            const destination = getWorkerTunnelUrl()
            if (destination) {
              window.location.assign(destination)
            } else {
              window.alert('員工遠端入口目前未啟動，請稍後再試。')
            }
          }

          return
        }

        /*
         * 訪客登入：
         * 不在白名單也不會被拒絕。
         * Google 登入後直接進訪客頁，不查詢或寫入訪客表單。
         */
        const status =
          await getAccessStatus(
            signedInUser
          )

        setAccessStatus(status)

        navigate(
          "/visitor",
          {
            replace: true,
          }
        )
      } catch (error) {
        if (
          error.code ===
            "auth/popup-closed-by-user" ||
          error.code ===
            "auth/cancelled-popup-request"
        ) {
          return
        }

        window.alert(
          `登入失敗：${error.message}`
        )
      }
    }

  return (
    <Routes>
      <Route
        path="/"
        element={
          <HomePage
            user={user}
            onAuthButtonClick={
              onAuthButtonClick
            }
          />
        }
      />

      <Route
        element={
          <ProtectedRoute
            user={user}
            authReady={authReady}
            onMemberLogin={onAuthButtonClick}
          />
        }
      >
        <Route path="/visitor-register" element={<Navigate to="/visitor" replace />} />

        <Route
          element={
            <VisitorAccessGate
              user={user}
              authReady={authReady}
              accessStatus={
                accessStatus
              }
            />
          }
        >
          <Route
            path="/visitor"
            element={
              <HomePage
                user={user}
                onAuthButtonClick={
                  onAuthButtonClick
                }
              />
            }
          />
          <Route path="/report" element={<ReportPage user={user} role={accessStatus} />} />
          <Route
            path="/cnn-monitor"
            element={
              import.meta.env.VITE_WORKER_REMOTE === '1'
                ? <RemoteLivePage kind="cnn" />
                : <CNNMonitorPage />
            }
          />
        </Route>

        <Route
          element={
            <WorkerAccessGate
              user={user}
              authReady={authReady}
              accessStatus={
                accessStatus
              }
            />
          }
        >
          <Route path="/internal" element={<InternalPage onAuthButtonClick={onAuthButtonClick} />} />
          <Route path="/ai-model" element={import.meta.env.VITE_WORKER_REMOTE === '1' ? <RemoteLivePage kind="ai" /> : <AiModelPage />} />
          <Route
            path="/worker"
            element={
              <WorkerPage
                user={user}
                onAuthButtonClick={
                  onAuthButtonClick
                }
              />
            }
          />
        </Route>
      </Route>

      <Route
        path="*"
        element={
          <Navigate
            to="/"
            replace
          />
        }
      />
    </Routes>
  )
}

function App() {
  if (import.meta.env.VITE_WORKER_REMOTE === '1') return <RemoteWorkerApp />
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}

export default App
