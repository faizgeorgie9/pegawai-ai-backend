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
  // The mock API answers the new endpoints in `npm run dev:mock` only; a production build must never
  // ship it, because the flag also decides which code the compiler keeps.
  if (mode === 'production' && env.VITE_MOCK_API === '1') throw new Error('VITE_MOCK_API=1 dilarang pada build produksi')
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
          r.end(JSON.stringify({ error: 'Layanan belum bisa dihubungi. Coba lagi sebentar lagi.' }))
        })
      },
    } satisfies ProxyOptions,
    '/output': {
      target: 'http://127.0.0.1:8090',
      changeOrigin: true,
    } satisfies ProxyOptions,
    '/images': {
      target: 'http://127.0.0.1:8090',
      changeOrigin: true,
    } satisfies ProxyOptions,
  }
  return {
    base: './',
    plugins: [react()],
    server: { proxy },
    preview: { proxy },
    build: {
      // Vendor chunks shared by every page. Rolldown 1.x names this option `codeSplitting`
      // (`advancedChunks` is its deprecated former name); `manualChunks` does not exist here.
      rolldownOptions: {
        output: {
          codeSplitting: {
            groups: [
              { name: 'react', test: /node_modules[\\/](react|react-dom|scheduler)[\\/]/ },
              {
                name: 'markdown',
                test: /node_modules[\\/](react-markdown|remark-[^\\/]+|mdast-[^\\/]+|micromark[^\\/]*|unified|unist-[^\\/]+|hast-[^\\/]+|vfile[^\\/]*|property-information|hast-util-[^\\/]+|mdast-util-[^\\/]+|micromark-[^\\/]+|unist-util-[^\\/]+|bail|ccount|character-entities[^\\/]*|comma-separated-tokens|decode-named-character-reference|devlop|escape-string-regexp|estree-[^\\/]+|html-url-attributes|inline-style-parser|is-plain-obj|longest-streak|markdown-table|space-separated-tokens|stringify-entities|style-to-[^\\/]+|trim-lines|trough|zwitch|@ungap[\\/][^\\/]+)[\\/]/,
              },
              { name: 'qr', test: /node_modules[\\/]uqr[\\/]/ },
            ],
          },
        },
      },
    },
  }
})
