import windBg from "../../assets/wind-bg.jpg"
import Icon from "../common/Icon.jsx"
import ImageCarousel from "../common/ImageCarousel.jsx"

function HeroSection() {
  return (
    <main className="home-hero">
      <img
        src={windBg}
        className="home-hero-bg"
        alt=""
      />

      <div className="home-hero-overlay" />

      <div className="home-hero-layout">
        <section className="home-hero-text">
          <p className="home-hero-eyebrow">
            SMART WIND ENERGY
          </p>

          <h1>
            <span className="hero-title-main">
              智能風力發電機
            </span>

            <span className="hero-title-sub">
              數據監測網
            </span>
          </h1>

          <p className="home-hero-description">
            整合智慧感測、機械學習系統，提供風力發電設備的工作入口與專題成果展示。
          </p>

          <a
            className="github-btn"
            href="https://github.com/Golden930227/topic-"
            target="_blank"
            rel="noreferrer"
          >
            <Icon name="github" />
            GitHub
          </a>
        </section>

        <ImageCarousel className="home-carousel" />
      </div>
    </main>
  )
}

export default HeroSection
