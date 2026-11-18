// An API redirect to an external login page must not become a CORS fetch failure.
export async function fetchApiResponse(url, options, fetcher = fetch) {
  const response = await fetcher(url, { ...options, redirect: 'manual' })
  if (response.type === 'opaqueredirect' || (response.status >= 300 && response.status < 400)) {
    throw new Error('外網入口驗證已失效，請重新整理頁面完成驗證')
  }
  if (response.ok && !response.headers.get('content-type')?.includes('application/json')) {
    throw new Error('API 未回傳 JSON，請檢查外網入口驗證與代理設定')
  }
  return response
}
