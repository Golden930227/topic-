import { signInWithPopup, signOut } from "firebase/auth"
import { auth, googleProvider } from "../../firebase.js"

const allowedEmails = [
  "g99226@gmail.com",
   "P124826960@gmail.com",
   "44o3249@gmaiil.com",
   "chenhongrui416@gmail.com",
]

function LoginPanel({ user }) {
  const handleLogin = async () => {
    const result = await signInWithPopup(auth, googleProvider)

    if (!allowedEmails.includes(result.user.email)) {
      await signOut(auth)
      alert("你沒有權限查看此網站")
    }
  }

  const handleLogout = async () => {
    await signOut(auth)
  }

  if (!user) {
    return <button onClick={handleLogin}>使用 Google 登入</button>
  }

  return (
    <div>
      <p>目前登入：{user.email}</p>
      <button onClick={handleLogout}>登出</button>
    </div>
  )
}

export default LoginPanel