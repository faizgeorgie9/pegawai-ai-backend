import { defineConfig, loadEnv } from 'vite'
import type { ProxyOptions } from 'vite'
import type { ServerResponse } from 'node:http'
import react from '@vitejs/plugin-react'

// The browser only talks to /bff/api/... (bff-spec section 9). This dev/preview proxy strips the /bff prefix, forwards to
// the BFF on 127.0.0.1:8090 and adds the shared key. The key has no VITE_ prefix and is never passed to `define`,
// so it cannot reach browser code. Hermes keys live in bff/.env and the browser never sees a Hermes URL.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const key = env.BFF_API_KEY
  const proxy = {
    '/bff': {
      target: 'http://127.0.0.1:8090',
      changeOrigin: true,
      timeout: 0, // SSE streams stay open
      proxyTimeout: 0,
      rewrite: (path: string) => path.replace(/^\/bff/, ''),
      configure(p) {
        p.on('proxyReq', (req) => {
          if (key) req.setHeader('X-Pegawai-AI-Key', key)
        })
        p.on('error', (_err, _req, res) => {
          const r = res as ServerResponse
          if (!r.headersSent) r.writeHead(502, { 'Content-Type': 'application/json' })
          r.end(JSON.stringify({ error: 'Server belum terjangkau. Pastikan BFF menyala, lalu coba lagi.' }))
        })
      },
    } satisfies ProxyOptions,
  }
  return { base: './', plugins: [react()], server: { proxy }, preview: { proxy } }
})
