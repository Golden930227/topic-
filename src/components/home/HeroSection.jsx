import windBg from "../../assets/wind-bg.jpg"
import Icon from "../common/Icon.jsx"

function HeroSection() {
  return (
    <main className="home-hero">
      <img src={windBg} className="home-hero-bg" alt="風力發電機組" />
      <section className="home-hero-text">
        <h1>智慧風機<br />監測平台</h1>
        <p>整合智慧感測、CNN 影像辨識與即時資料監控，提供風力發電設備的工作入口與專題成果展示。</p>
        <a className="github-btn" href="https://github.com/Golden930227/topic-" target="_blank" rel="noreferrer"><Icon name="github" />GitHub</a>
      </section>
    </main>
  )
}

export default HeroSection
