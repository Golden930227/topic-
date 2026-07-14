export async function openCnnMonitor(event) {
  event?.preventDefault()
  const newWindow = window.open("", "_blank")
  try {
    const response = await fetch("http://127.0.0.1:5000/api/open-cnn-monitor", { method: "POST" })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || "無法啟動 CNN 監測")
    if (newWindow) newWindow.location.href = data.url
    else window.open(data.url, "_blank", "noopener,noreferrer")
  } catch (error) {
    newWindow?.close()
    window.alert(error.message)
  }
}
