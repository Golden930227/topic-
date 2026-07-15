import { useEffect, useRef, useState } from "react"
import { Link } from "react-router-dom"
import Logo from "../common/Logo.jsx"
import { openCnnMonitor } from "../../utils/openCnnMonitor.js"

function Navbar({ user, onAuthButtonClick }) {
  const [openMenu, setOpenMenu] = useState(null)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const navbarRef = useRef(null)

  const closeMenu = () => setOpenMenu(null)

  function closeMobileMenu() {
    setMobileMenuOpen(false)
    setOpenMenu(null)
  }

  useEffect(() => {
    const closeOnOutsideClick = (event) => {
      if (navbarRef.current && !navbarRef.current.contains(event.target)) {
        setOpenMenu(null)
        setMobileMenuOpen(false)
      }
    }

    document.addEventListener("mousedown", closeOnOutsideClick)

    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick)
    }
  }, [])

  const dropdown = (name, label, children) => (
    <div className="small-dropdown">
      <button
        type="button"
        className={`small-dropdown-button ${
          openMenu === name ? "active" : ""
        }`}
        onClick={() => {
          setOpenMenu(openMenu === name ? null : name)
        }}
        aria-expanded={openMenu === name}
      >
        {label}
        <span className="dropdown-arrow">⌄</span>
      </button>

      {openMenu === name && (
        <div className="small-dropdown-menu">{children}</div>
      )}
    </div>
  )

  const handleAuthClick = async (event) => {
    event.preventDefault()
    event.stopPropagation()

    try {
      await onAuthButtonClick()
    } finally {
      setOpenMenu(null)
    }
  }

  return (
    <header className="navbar" ref={navbarRef}>
      <Logo />

      <nav
        className={`main-nav ${
          mobileMenuOpen ? "mobile-menu-open" : ""
        }`}
        onClick={(event) => {
          if (event.target.closest("a")) {
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

        {dropdown(
          "sensor",
          "智慧感測器",
          <>
            <a
              href="http://localhost:8501"
              target="_blank"
              rel="noreferrer"
              onClick={closeMenu}
            >
              智慧感測器
            </a>

            <a
              href="http://localhost:8502"
              target="_blank"
              rel="noreferrer"
              onClick={closeMenu}
            >
              人工智能模型
            </a>
          </>
        )}

        {dropdown(
          "cnn",
          "CNN監測與問題回報",
          <>
            <a
              href="#cnn-monitor"
              onClick={(event) => {
                closeMenu()
                openCnnMonitor(event)
              }}
            >
              CNN監測
            </a>

            <a href="/report" onClick={closeMenu}>
              問題回報
            </a>
          </>
        )}

        <a
          href="https://ee.nfu.edu.tw/zh_tw/teacher01/faculty/%E7%8E%8B%E9%B3%B4%E7%AB%8B-Ming-Li-Wang-77332159"
          target="_blank"
          rel="noreferrer"
        >
          專題教授
        </a>

        <a href="#references">參考資料</a>
      </nav>

      <div className="actions">
        <button
          type="button"
          className="login"
          onClick={handleAuthClick}
        >
          {user ? "登出" : "同組登入"}
        </button>

        <Link
          className="start"
          to="/worker"
          onClick={closeMobileMenu}
        >
          Get started
        </Link>
      </div>

      <button
        type="button"
        className="mobile-menu-toggle"
        aria-label={mobileMenuOpen ? "關閉導覽選單" : "開啟導覽選單"}
        aria-expanded={mobileMenuOpen}
        onClick={() => {
          setMobileMenuOpen((isOpen) => !isOpen)
          setOpenMenu(null)
        }}
      >
        ☰
      </button>
    </header>
  )
}

export default Navbar