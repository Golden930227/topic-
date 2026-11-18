import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readFile } from 'node:fs/promises'
import { once } from 'node:events'
import http from 'node:http'
import { spawn } from 'node:child_process'
import { fetchApiResponse } from '../monitor_shared/apiResponse.js'

async function apiBaseFor(env) {
  const source = (await readFile(new URL('../src/utils/monitorClient.js', import.meta.url), 'utf8'))
    .replace("import { auth } from '../firebase.js'", 'const auth = { currentUser: null }')
    .replaceAll('import.meta.env', JSON.stringify(env))
  return (await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`)).apiBase
}

test('development and tunnel builds keep all APIs on the page origin', async () => {
  for (const base of ['http://127.0.0.1:8001', 'http://localhost:8001', 'https://other.example']) {
    assert.equal(await apiBaseFor({DEV: true, VITE_API_BASE_URL: base}), '')
    assert.equal(await apiBaseFor({DEV: false, VITE_WORKER_REMOTE: '1', VITE_API_BASE_URL: base}), '')
  }
  assert.equal(await apiBaseFor({DEV: false}), '')
  assert.equal(await apiBaseFor({DEV: false, VITE_API_BASE_URL: 'https://api.example/'}), 'https://api.example')
})

test('login redirects are reported before fetch follows a cross-origin login page', async () => {
  for (const response of [{type: 'opaqueredirect', status: 0}, {type: 'basic', status: 302}]) {
    await assert.rejects(fetchApiResponse('/api/cnn', {credentials: 'include'}, async (_, options) => {
      assert.equal(options.redirect, 'manual')
      assert.equal(options.credentials, 'include')
      return response
    }), /驗證已失效/)
  }
  await assert.rejects(fetchApiResponse('/api/cnn', {}, async () => new Response('<html>login</html>', {headers: {'content-type': 'text/html'}})), /JSON/)
  const response = new Response('{"connected":true}', {headers: {'content-type': 'application/json'}})
  assert.equal(await fetchApiResponse('/api/cnn', {}, async () => response), response)
  const unauthorized = new Response('{}', {status: 401})
  assert.equal(await fetchApiResponse('/api/cnn', {}, async () => unauthorized), unauthorized)
})

test('production proxy forwards every API route and preserves login without forwarding privileged headers', async () => {
  const upstream = http.createServer((req, res) => {
    res.writeHead(req.headers.authorization === 'Bearer test-user-token' ? 200 : 401, {'content-type': 'application/json'})
    res.end(JSON.stringify({url: req.url, method: req.method, headers: req.headers}))
  })
  upstream.listen(0, '127.0.0.1')
  await once(upstream, 'listening')
  const apiPort = upstream.address().port
  const reservation = http.createServer()
  reservation.listen(0, '127.0.0.1')
  await once(reservation, 'listening')
  const port = reservation.address().port
  await new Promise(resolve => reservation.close(resolve))
  const child = spawn(process.execPath, ['windmind_remote_proxy.cjs'], {
    cwd: new URL('..', import.meta.url), windowsHide: true,
    env: {...process.env, WINDMIND_PROXY_PORT: String(port), WINDMIND_REMOTE_API_PORT: String(apiPort)},
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  try {
    await Promise.race([once(child.stdout, 'data'), new Promise((_, reject) => { const timeout = setTimeout(() => reject(new Error('proxy did not start')), 5000); timeout.unref() })])
    for (const path of ['/api/health', '/api/cnn', '/api/ai', '/api/access', '/api/session']) {
      const response = await fetch(`http://127.0.0.1:${port}${path}`, {
        method: path === '/api/session' ? 'POST' : 'GET',
        headers: {authorization: 'Bearer test-user-token', cookie: 'windmind_session=test-cookie', 'x-windmind-service': 'must-be-stripped', 'cf-access-authenticated-user-email': 'spoof@example.com'},
      })
      assert.equal(response.status, 200)
      const body = await response.json()
      assert.equal(body.url, path)
      assert.equal(body.headers.authorization, 'Bearer test-user-token')
      assert.equal(body.headers.cookie, 'windmind_session=test-cookie')
      assert.equal(body.headers['x-windmind-service'], undefined)
      assert.equal(body.headers['cf-access-authenticated-user-email'], undefined)
    }
    const response = await fetch(`http://127.0.0.1:${port}/api/cnn`)
    assert.equal(response.status, 401)
    assert.match(response.headers.get('content-type'), /application\/json/)
  } finally {
    child.kill()
    await new Promise(resolve => upstream.close(resolve))
  }
})
