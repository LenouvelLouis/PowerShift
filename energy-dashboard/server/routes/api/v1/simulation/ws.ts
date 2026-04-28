/**
 * WebSocket proxy: /api/v1/simulation/ws -> backend WS endpoint.
 *
 * Handles the HTTP upgrade to WebSocket and proxies frames in both
 * directions between the browser and the FastAPI backend.
 */
export default defineEventHandler((event) => {
  // Only handle WebSocket upgrade requests
  if (!event.node.req.headers.upgrade?.toLowerCase().includes('websocket')) {
    return // Let other handlers deal with non-WS requests
  }

  const base = (process.env.NUXT_API_BASE_URL ?? 'http://localhost:8000')
    .replace(/^http/, 'ws')

  const apiKey = process.env.NUXT_API_KEY
  const query = apiKey ? `?api_key=${encodeURIComponent(apiKey)}` : ''
  const target = `${base}/api/v1/simulation/ws${query}`

  return proxyRequest(event, target)
})
