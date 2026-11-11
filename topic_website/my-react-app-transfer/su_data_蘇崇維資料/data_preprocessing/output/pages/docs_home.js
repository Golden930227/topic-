(() => {
  const homeUrl = document.currentScript.dataset.homeUrl
  function linkTitle() {
    const title = document.querySelector('#swagger-ui .info .title')
    if (!title || title.querySelector('.windmind-home-link')) return
    // Preserve Swagger's version badges and other children.
    const label = [...title.childNodes].find(node =>
      node.nodeType === Node.TEXT_NODE && node.textContent.trim()
    )
    if (!label) return
    const link = document.createElement('a')
    link.className = 'windmind-home-link'
    link.href = homeUrl
    link.setAttribute('aria-label', `${label.textContent.trim()}: 返回 WindMind 主站首頁`)
    label.replaceWith(link)
    link.append(label)
  }
  // Swagger renders asynchronously and can render again after spec changes.
  const container = document.getElementById('swagger-ui')
  if (container) {
    new MutationObserver(linkTitle).observe(container, { childList: true, subtree: true })
    linkTitle()
  }
})()
