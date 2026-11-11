// The main app and standalone Vite app share this component.
export function getHomeUrl() {
  const configured = import.meta.env.VITE_HOME_URL?.trim()
  if (configured) return configured
  const home = new URL('/', window.location.href)
  if (import.meta.env.DEV && home.port === '5174') home.port = '5173'
  return home.href
}
