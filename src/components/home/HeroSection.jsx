import windBg from "../../assets/wind-bg.jpg"

import ImageCarousel from "../common/ImageCarousel.jsx"

function HeroSection() {
  function handleCustomerServiceClick() {
    window.alert(
      "客服功能建置中，下一步將接上固定 FAQ 聊天視窗。"
    )
  }

  return (
    <main className="home-hero">
      <img
        src={windBg}
        className="home-hero-bg"
        alt="風力發電機組"
      />

      <div className="home-hero-layout">
        <section className="home-hero-text">
          <h1>
            <span className="hero-title-main">
              智能風力發電機
            </span>

            <span className="hero-title-sub">
              數據監測網
            </span>
          </h1>

          <p>
            整合智慧感測、機械學習系統，
            提供風力發電設備的工作入口與專題成果展示。
          </p>

          <button
            type="button"
            className="customer-service-btn"
            onClick={
              handleCustomerServiceClick
            }
          >
            客服
          </button>
        </section>

        <ImageCarousel />
      </div>
    </main>
  )
}

export default HeroSection