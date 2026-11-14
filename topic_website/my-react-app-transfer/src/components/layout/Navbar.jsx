import {
  useEffect,
  useRef,
  useState,
} from "react"

import {
  Link,
  useLocation,
} from "react-router-dom"

import Logo from "../common/Logo.jsx"

function Navbar({
  user,
  onAuthButtonClick,
}) {
  const [
    mobileMenuOpen,
    setMobileMenuOpen,
  ] = useState(false)

  const navbarRef = useRef(null)
  const location = useLocation()

  const isVisitorPage =
    location.pathname === "/visitor"

  function closeMobileMenu() {
    setMobileMenuOpen(false)
  }

  useEffect(() => {
    const closeOnOutsideClick = (event) => {
      if (
        navbarRef.current &&
        !navbarRef.current.contains(
          event.target
        )
      ) {
        setMobileMenuOpen(false)
      }
    }

    document.addEventListener(
      "mousedown",
      closeOnOutsideClick
    )

    return () => {
      document.removeEventListener(
        "mousedown",
        closeOnOutsideClick
      )
    }
  }, [])

  const handleMemberClick = async (
    event
  ) => {
    event.preventDefault()
    event.stopPropagation()

    await onAuthButtonClick("member")
  }

  const handleVisitorClick = async (
    event
  ) => {
    event.preventDefault()
    event.stopPropagation()

    try {
      await onAuthButtonClick("visitor")
    } finally {
      closeMobileMenu()
    }
  }

  return (
    <header
      className="navbar"
      ref={navbarRef}
    >
      <Logo />

      <nav
        className={`main-nav ${
          mobileMenuOpen
            ? "mobile-menu-open"
            : ""
        }`}
        onClick={(event) => {
          if (
            event.target.closest?.("a")
          ) {
            closeMobileMenu()
          }
        }}
      >
        <a
          href="https://docs.google.com/presentation/d/1ytDy_Np1tneWL0554-NldsedGhtqcNuv/edit?usp=sharing&ouid=103734357927532998525&rtpof=true&sd=true"
          target="_blank"
          rel="noreferrer"
        >
          整體方塊圖
        </a>

        {isVisitorPage && (
          <>
            <Link to="/cnn-monitor">風機數據監測</Link>
            <Link to="/report">問題回報</Link>
          </>
        )}

        <a
          href="https://ee.nfu.edu.tw/zh_tw/teacher01/faculty/%E7%8E%8B%E9%B4%B4%E7%AB%8B-Ming-Li-Wang-77332159"
          target="_blank"
          rel="noreferrer"
        >
          王鴻立教授
        </a>

        <a
          href="https://ee.nfu.edu.tw/zh_tw/teacher01/faculty/%E6%B1%AA%E6%A5%B7%E8%8C%97-82164242"
          target="_blank"
          rel="noreferrer"
        >
          汪楷茗教授
        </a>

        <a
          href="https://zenodo.org/records/14870023?preview_file=2024.zip"
          target="_blank"
          rel="noreferrer"
        >
          參考資料
        </a>
        <a href="https://lin.ee/VImRwnH" target="_blank" rel="noopener noreferrer">LINE 客服</a>
      </nav>

      <div className="actions">
        <button
          type="button"
          className="login"
          onClick={handleMemberClick}
        >
          {user ? "進入員工內網" : "同組登入"}
        </button>

        {user && <button type="button" className="login" onClick={() => onAuthButtonClick("logout")}>登出</button>}

        <button
          type="button"
          className="start"
          onClick={handleVisitorClick}
        >
          {user
            ? "進入訪客頁"
            : "訪客登入"}
        </button>
      </div>

      <button
        type="button"
        className="mobile-menu-toggle"
        aria-label={
          mobileMenuOpen
            ? "關閉導覽選單"
            : "開啟導覽選單"
        }
        aria-expanded={mobileMenuOpen}
        onClick={() => {
          setMobileMenuOpen(
            (isOpen) => !isOpen
          )

        }}
      >
        ☰
      </button>
    </header>
  )
}

export default Navbar
