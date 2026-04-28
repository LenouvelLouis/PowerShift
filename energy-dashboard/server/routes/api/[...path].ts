/**
 * Runtime proxy : /api/** → http://backend:8000/api/**
 *
 * Ce handler tourne côté serveur Nitro à chaque requête,
 * donc process.env.NUXT_API_BASE_URL est lu au runtime
 * (pas au build), ce qui permet à Docker de l'injecter.
 */
export default defineEventHandler((event) => {
  const base = process.env.NUXT_API_BASE_URL ?? 'http://localhost:8000'
  const target = base + event.path // event.path = /api/v1/...

  const apiKey = process.env.NUXT_API_KEY
  const headers: Record<string, string> = {}
  if (apiKey) {
    headers['X-API-Key'] = apiKey
  }

  return proxyRequest(event, target, { headers })
})
