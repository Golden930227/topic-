const http = require('node:http')
const net = require('node:net')
const fs = require('node:fs')
const path = require('node:path')

const host = '127.0.0.1'
const port = Number(process.env.WINDMIND_PROXY_PORT || 18764)
const apiPort = Number(process.env.WINDMIND_REMOTE_API_PORT || 8001)
const staticRoot = path.resolve(__dirname, '.windmind-remote-dist')
const upstreams = [
  { prefix: '/pipeline/', port: 18501 },
  { prefix: '/sql-monitor/', port: 18502 },
  { prefix: '/api/', port: apiPort },
]
const mime = {
  '.html': 'text/html; charset=utf-8', '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.svg': 'image/svg+xml', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.ico': 'image/x-icon',
}

function route(rawUrl) {
  const parsed = new URL(rawUrl, 'http://localhost')
  const pathname = parsed.pathname
  if (pathname === '/pipeline' || pathname === '/sql-monitor') return { redirect: pathname + '/' }
  if (pathname === '/api/docs' || pathname.startsWith('/api/docs/') || pathname === '/api/openapi.json') {
    return { port: apiPort, target: pathname.slice(4) + parsed.search }
  }
  if (pathname === '/openapi.json' || pathname.startsWith('/docs/')) return { port: apiPort, target: pathname + parsed.search }
  const upstream = upstreams.find(item => pathname.startsWith(item.prefix))
  if (upstream) return { port: upstream.port, target: pathname + parsed.search }
  if (pathname === '/healthz') return { health: true }
  return { static: pathname }
}

function safeHeaders(headers) {
  const copy = { ...headers }
  for (const key of ['host', 'connection', 'proxy-connection', 'x-forwarded-for', 'x-forwarded-host', 'x-forwarded-proto', 'cf-access-authenticated-user-email']) delete copy[key]
  copy.host = '127.0.0.1'
  copy['x-forwarded-proto'] = 'https'
  return copy
}

function serveStatic(req, res, pathname) {
  if (!['GET', 'HEAD'].includes(req.method)) { res.writeHead(405).end(); return }
  let decoded
  try { decoded = decodeURIComponent(pathname) } catch { res.writeHead(400).end(); return }
  if (decoded.includes('\0') || decoded.includes('\\') || decoded.split('/').includes('..')) { res.writeHead(400).end(); return }
  const asset = decoded.startsWith('/assets/') || ['/favicon.svg', '/icons.svg'].includes(decoded)
  const file = asset ? path.resolve(staticRoot, '.' + decoded) : path.join(staticRoot, 'index.html')
  if (!file.startsWith(staticRoot + path.sep)) { res.writeHead(403).end(); return }
  fs.stat(file, (error, stat) => {
    if (error || !stat.isFile()) { res.writeHead(404).end(); return }
    res.writeHead(200, { 'content-type': mime[path.extname(file)] || 'application/octet-stream', 'cache-control': 'no-store', 'content-length': stat.size })
    if (req.method === 'HEAD') { res.end(); return }
    fs.createReadStream(file).pipe(res)
  })
}

// Opt-in diagnostics record only validated role and counts, never credentials.
const historyTraceKeys = new Set()
function traceAiHistory(req, upstream) {
  if (process.env.WINDMIND_TRACE_AI_HISTORY !== '1' || upstream.statusCode !== 200 ||
      new URL(req.url, 'http://localhost').pathname !== '/api/ai' ||
      new URL(req.url, 'http://localhost').searchParams.get('archive') === 'true') return
  let size = 0
  const chunks = []
  upstream.on('data', chunk => {
    size += chunk.length
    if (size <= 4 * 1024 * 1024) chunks.push(chunk)
  })
  upstream.on('end', async () => {
    if (size > 4 * 1024 * 1024) return
    try {
      const response = await fetch(`http://127.0.0.1:${apiPort}/api/access`, {
        headers: {cookie: req.headers.cookie || '', authorization: req.headers.authorization || ''},
        signal: AbortSignal.timeout(10000),
      })
      if (!response.ok) return
      const {role} = await response.json()
      const data = JSON.parse(Buffer.concat(chunks).toString('utf8'))
      const count = data.predictionHistory?.length || 0
      const traceKey = `${role}:${count}`
      if (historyTraceKeys.has(traceKey)) return
      historyTraceKeys.add(traceKey)
      console.log(JSON.stringify({event:'ai_history', apiPort, role, historyCount:count,
        currentIsLatest:data.currentPrediction?.prediction_uid === data.predictionHistory?.[0]?.prediction_uid,
        recentEventsCount:data.recentEvents?.length || 0}))
    } catch { /* Diagnostics must never interfere with the API response. */ }
  })
}

const server = http.createServer((req, res) => {
  const selected = route(req.url)
  if (selected.redirect) { res.writeHead(308, { location: selected.redirect }).end(); return }
  if (selected.health) { res.writeHead(200, { 'content-type': 'text/plain' }).end('WindMind proxy ready'); return }
  if (selected.static) { serveStatic(req, res, selected.static); return }
  const request = http.request({ host, port: selected.port, path: selected.target, method: req.method, headers: safeHeaders(req.headers), timeout: 10000 }, upstream => {
    res.writeHead(upstream.statusCode, upstream.headers)
    traceAiHistory(req, upstream)
    upstream.pipe(res)
  })
  request.on('timeout', () => request.destroy(new Error('upstream timeout')))
  request.on('error', () => { if (!res.headersSent) res.writeHead(502, { 'content-type': 'text/plain' }); res.end('Service offline') })
  req.pipe(request)
})

server.on('upgrade', (req, client, head) => {
  const selected = route(req.url)
  if (!selected.port || !['/pipeline/', '/sql-monitor/'].some(prefix => req.url.startsWith(prefix))) {
    client.end('HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n'); return
  }
  const upstream = net.connect(selected.port, host)
  upstream.setTimeout(10000, () => upstream.destroy())
  upstream.on('connect', () => {
    upstream.setTimeout(0)
    const headers = safeHeaders(req.headers)
    headers.connection = 'Upgrade'
    headers.upgrade = 'websocket'
    const lines = [`${req.method} ${selected.target} HTTP/1.1`, ...Object.entries(headers).map(([key, value]) => `${key}: ${value}`), '', '']
    upstream.write(lines.join('\r\n'))
    if (head.length) upstream.write(head)
    client.pipe(upstream).pipe(client)
  })
  upstream.on('error', () => client.destroy())
  client.on('error', () => upstream.destroy())
})

server.listen(port, host, () => console.log(`WindMind proxy ready at http://${host}:${port}`))
