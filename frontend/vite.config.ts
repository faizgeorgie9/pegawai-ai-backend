import { defineConfig, loadEnv } from 'vite'
import type { ProxyOptions } from 'vite'
import type { ServerResponse } from 'node:http'
import react from '@vitejs/plugin-react'

// The API key is read here, on the dev/preview server only. It has no VITE_ prefix and is never
// passed to `define`, so it cannot reach browser code. The proxy adds it to every /api request.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const key = env.FRONTEND_API_KEY
  const proxy = {
    '/api': {
      target: 'http://127.0.0.1:8080',
      changeOrigin: true,
      timeout: 330_000, // above the 300 s run limit
      proxyTimeout: 330_000,
      configure(p) {
        p.on('proxyReq', (req) => {
          if (key) req.setHeader('X-Pegawai-AI-Key', key)
        })
        p.on('error', (_err, _req, res) => {
          const r = res as ServerResponse
          if (!r.headersSent) r.writeHead(502, { 'Content-Type': 'application/json' })
          r.end(JSON.stringify({ error: 'Backend tidak terjangkau' }))
        })
      },
    } satisfies ProxyOptions,
    // Budi's banner comes back as image_url "/banner_promo_kreatif.png", served by the backend itself.
    // Public static file, so no key is added; only image paths at the root are forwarded.
    '^/[\\w.-]+\\.(png|jpe?g|webp)$': {
      target: 'http://127.0.0.1:8080',
      changeOrigin: true,
    } satisfies ProxyOptions,
  }
  return { base: './', plugins: [react()], server: { proxy }, preview: { proxy } }
})
