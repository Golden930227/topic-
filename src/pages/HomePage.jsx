import Navbar from "../components/layout/Navbar.jsx"
import HeroSection from "../components/home/HeroSection.jsx"

function HomePage(props) {
  return <div className="home-page"><Navbar {...props} /><HeroSection /></div>
}

export default HomePage
