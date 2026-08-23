import { Link } from "react-router-dom"

function Logo() {
  return (
    <Link className="brand" to="/" aria-label="風力發電監測系統首頁">
      <span className="logo" aria-hidden="true">W</span>
      <span>wind turbine</span>
    </Link>
  )
}

export default Logo
