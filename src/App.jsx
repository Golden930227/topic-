import { useEffect, useState } from "react"
import { BrowserRouter, Route, Routes } from "react-router-dom"
import { onAuthStateChanged, signInWithPopup, signOut } from "firebase/auth"
import { auth, googleProvider } from "./firebase.js"
import ProtectedRoute from "./components/common/ProtectedRoute.jsx"
import HomePage from "./pages/HomePage.jsx"
import WorkerPage from "./pages/WorkerPage.jsx"
import ReportPage from "./pages/ReportPage.jsx"
import "./App.css"

const allowedEmails = ["g99226@gmail.com"]

function App() {
  const [user, setUser] = useState(null)
  const [authReady, setAuthReady] = useState(false)

  useEffect(() => onAuthStateChanged(auth, (currentUser) => {
    setUser(currentUser)
    setAuthReady(true)
  }), [])

  const onAuthButtonClick = async () => {
    if (user) return signOut(auth)

    try {
      const result = await signInWithPopup(auth, googleProvider)
      if (!allowedEmails.includes(result.user.email)) {
        await signOut(auth)
        window.alert("此帳號沒有同組成員權限。")
      }
    } catch (error) {
      window.alert(`登入失敗：${error.message}`)
    }
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage user={user} onAuthButtonClick={onAuthButtonClick} />} />
        <Route path="/report" element={<ReportPage />} />
        <Route element={<ProtectedRoute user={user} authReady={authReady} />}>
          <Route path="/worker" element={<WorkerPage user={user} onAuthButtonClick={onAuthButtonClick} />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
