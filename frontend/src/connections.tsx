import { useCallback, useEffect, useRef, useState } from 'react'
import { AppLogo } from './app-logos'
import { createPortal } from 'react-dom'
import { api, errText } from './bff'
import { useAdminMode } from './adminMode'
import type { ConnProvider, Connection, HermesApp } from './bff'
import { go } from './router'
import { SourcePicker } from './pick-ui'
import { SkillsSection } from './skills-ui'
import { Dialog, ErrorLine } from './ui'
import { CapChip, PageHead, Spinner, useLoad } from './ui-extra'
import { cachedRead, forgetReads, onLinkIntent } from './session-cache'

// Real per-user connections (BFF: bff/connections.py). The state comes from the BFF; nothing here pretends to be connected.
type AppDef = { name: string; enables: string; where: string }
const APPS: Record<ConnProvider, AppDef> = {
  gdrive: {
    name: 'Google Drive',
    enables: 'Pegawai AI bisa mencari, membaca, membuat, mengubah, mengganti nama, dan memindahkan berkas Drive Anda; menghapus berkas selalu menunggu persetujuan Anda.',
    where: 'Halaman Pengetahuan dan lampiran chat.',
  },
  gmail: {
    name: 'Gmail',
    enables: 'Pegawai AI bisa membaca email, membuat draf, memberi label, mengarsipkan, dan memindahkan email ke Sampah; mengirim email selalu menunggu persetujuan Anda.',
    where: 'Tombol "Simpan sebagai draf Gmail" di bawah jawaban pegawai.',
  },
}
const WHY: Record<string, string> = {
  denied: 'Izin tidak diberikan, jadi akun belum tersambung.',
  state: 'Permintaan sambungan sudah kedaluwarsa atau tidak dikenal. Coba hubungkan lagi.',
  exchange: 'Sambungan tidak diterima. Coba lagi; jika terus gagal, hubungi admin Anda.',
  scope: 'Izin yang diperlukan tidak dicentang. Hubungkan lagi dan centang semua izin yang diminta.',
}

// The BFF sends the browser back to #/aplikasi?connect=ok|error&app=...&reason=... after the provider's consent page.
function readResult(): { ok: boolean; text: string } | null {
  const q = new URLSearchParams(location.hash.split('?')[1] ?? '')
  const c = q.get('connect')
  if (c !== 'ok' && c !== 'error') return null
  const app = APPS[q.get('app') as ConnProvider] as AppDef | undefined
  if (c === 'ok') return { ok: true, text: `${app?.name ?? 'Aplikasi'} tersambung.` }
  return { ok: false, text: `${app ? `${app.name} belum tersambung. ` : ''}${WHY[q.get('reason') ?? ''] ?? 'Sambungan gagal. Coba lagi.'}` }
}

// Old links (#/tools?connect=..., from before the Aplikasi page existed) are forwarded with their query.
export function forwardOldConnectLink() {
  const q = location.hash.split('?')[1]
  if (q && new URLSearchParams(q).has('connect')) go(`/aplikasi?${q}`, true)
}

export function useConnections() {
  const fn = useCallback(() => cachedRead('connections', () => api.connections()), [])
  return useLoad(fn)
}

// One read, shared by the menu prefetch and the page. The BFF caches its app catalog for 60 s; this keeps
// the same data on screen when the user leaves Aplikasi and comes back, instead of a new skeleton.
const primeApps = () => {
  void cachedRead('connections', () => api.connections()).catch(() => {})
  void cachedRead('apps-catalog', () => api.appsCatalog()).catch(() => {})
}
onLinkIntent('a[href="#/aplikasi"]', primeApps)

// Marks drawn here in each product's colours (simple shapes, not the official artwork).
function Mark({ id }: { id: string }) {
  const p = { width: 28, height: 28, viewBox: '0 0 32 32', 'aria-hidden': true } as const
  if (id === 'gdrive')
    return (
      <svg {...p}>
        <path d="M11 4h10l10 17H21z" fill="#f4b400" />
        <path d="M11 4 1 21l5 8 10-17z" fill="#0f9d58" />
        <path d="M6 29h20l5-8H11z" fill="#4285f4" />
      </svg>
    )
  if (id === 'gmail')
    return (
      <svg {...p}>
        <rect x="2" y="6" width="28" height="20" rx="3" fill="#fff" />
        <path d="M2 9v14a3 3 0 0 0 3 3h3V13zM30 9v14a3 3 0 0 1-3 3h-3V13z" fill="#4285f4" />
        <path d="m2 9 14 11L30 9l-1-2a3 3 0 0 0-3-1H6a3 3 0 0 0-3 1z" fill="#ea4335" />
        <path d="m8 13 8 6 8-6v-3l-8 6-8-6z" fill="#c5221f" />
      </svg>
    )
  if (id === 'whatsapp')
    return (
      <svg {...p}>
        <path d="M16 3a13 13 0 0 0-11 19.7L3 29l6.5-2A13 13 0 1 0 16 3z" fill="#25d366" />
        <path d="M11.5 10c.5 4.8 4.2 8.5 9 9l1.8-2.2-2.8-1.4-1.2 1c-1.6-.6-3-2-3.6-3.6l1-1.2L13.3 8z" fill="#fff" />
      </svg>
    )
  return (
    <svg {...p}>
      <circle cx="16" cy="16" r="13" fill="#2aabee" />
      <path d="m7.5 15.5 15.500-6-2.600 12.500-4.400-3.200-2.300 2.200-.4-4.400 6.600-5.600-8.200 4.600z" fill="#fff" />
    </svg>
  )
}

// Only "filled or not" per value, from the BFF. Never a secret, never whether it is correct.
function AdminHint({ c }: { c: Connection }) {
  const missing = c.setup.filter((s) => !s.filled).length
  return (
    <details className="app-admin">
      <summary>Petunjuk untuk admin</summary>
      <div className="app-admin-in">
        <p>
          {missing > 0
            ? `${c.name} belum bisa disambungkan. Isi ${missing} nilai yang belum terisi di file bff/.env, lalu jalankan ulang BFF.`
            : `Semua nilai ${c.name} sudah terisi.`}
        </p>
        <ul className="app-setup">
          {c.setup.map((s) => (
            <li key={s.env} data-filled={s.filled}>
              <span>
                {s.label} <code>{s.env}</code>
              </span>
              <span className={`pill ${s.filled ? 'cap-ok' : 'cap-mock'}`}>{s.filled ? 'Terisi' : 'Belum diisi'}</span>
            </li>
          ))}
        </ul>
        <p>Daftarkan alamat ini sebagai redirect URI di layanan penyedia, ditempel persis:</p>
        <p>
          <code className="app-uri">{c.redirect_uri}</code>
        </p>
        <p className="quiet small">Langkah lengkapnya ada di panduan docs/sprint4/setup-koneksi.md. Nilai rahasia tidak pernah ditampilkan di sini.</p>
      </div>
    </details>
  )
}

// Initial in a soft circle for Hermes apps (no official logos); the colour comes from the name so it stays the same.
function Initial({ name }: { name: string }) {
  let h = 0
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) % 360
  return (
    <span className="app-initial" style={{ ['--hue' as string]: h }} aria-hidden="true">
      {name.charAt(0).toUpperCase()}
    </span>
  )
}

const OAUTH_CAT: Record<ConnProvider, string> = { gdrive: 'docs', gmail: 'comms' }
const OAUTH_NAME: Record<ConnProvider, string> = { gdrive: 'Google Drive', gmail: 'Gmail' }

// One-card rule: an app that exists both as our own connection and as a Hermes connector gets ONE card. The Hermes connector
// wins (it is always connectable); our connection stays reachable through its extra action (e.g. "Pilih dari Drive") when
// it is connected too. Our connection alone is shown when the catalog has no matching connector. Add a line per known overlap
// (our provider -> Hermes ids); the live catalog has no overlaps today.
const OWN_AS_HERMES: Record<ConnProvider, string[]> = { gdrive: ['google_drive', 'googledrive'], gmail: ['gmail'] }

// The CLI names accounts like canva_mcp_batty-rory: users only see a label that looks like an email address; admins see everything.
const shownAccounts = (accounts: string[], admin: boolean) => (admin ? accounts : accounts.filter((a) => a.includes('@')))

// Opened synchronously inside the click so the browser allows it; the BFF call takes seconds. Static page, no data interpolated.
function openLoadingTab(): Window | null {
  const w = window.open('', '_blank')
  if (!w) return null
  const d = w.document
  d.title = 'Menyiapkan halaman login…'
  const st = d.createElement('style')
  st.textContent =
    ':root{color-scheme:light dark}body{margin:0;min-height:100vh;display:grid;place-content:center;gap:12px;justify-items:center;font:16px system-ui,sans-serif;text-align:center;padding:24px}' +
    '.s{width:28px;height:28px;border:3px solid rgba(128,128,128,.3);border-top-color:#2563eb;border-radius:50%;animation:r 1s linear infinite}@keyframes r{to{transform:rotate(360deg)}}' +
    '@media (prefers-reduced-motion:reduce){.s{animation:none}}p{margin:0;opacity:.75}h1{font-size:18px;margin:0}'
  d.head.appendChild(st)
  const sp = d.createElement('div')
  sp.className = 's'
  sp.setAttribute('aria-hidden', 'true')
  const h = d.createElement('h1')
  h.textContent = 'Menyiapkan halaman login…'
  const p = d.createElement('p')
  p.textContent = 'Mohon tunggu sebentar, Anda akan dialihkan otomatis.'
  d.body.append(sp, h, p)
  return w
}

// Login links last 10 minutes on the portal and the BFF keeps the pending login for 9: ask for a new one after 8.
const LINK_MAX_AGE = 8 * 60_000
type Link = { p: Promise<{ url?: string; connected?: boolean }>; at: number }

// Guided connect: the login link is requested as soon as the dialog opens (the Hermes CLI needs seconds), the click opens the tab
// at once and sends it to the link when it is there. Then wait until the app shows up as connected and close the login tab again.
function ConnectDialog({ app, onClose, onDone }: { app: HermesApp; onClose: () => void; onDone: (message: string) => void }) {
  const [phase, setPhase] = useState<'intro' | 'starting' | 'waiting' | 'late' | 'error' | 'done'>('intro')
  const [url, setUrl] = useState('')
  const [blocked, setBlocked] = useState(false)
  const [problem, setProblem] = useState('')
  const live = useRef(true)
  const tab = useRef<Window | null>(null)
  const link = useRef<Link | null>(null)
  const success = `${app.name} tersambung. Pegawai AI sekarang bisa memakainya.`
  const closeTab = () => {
    try {
      tab.current?.close()
    } catch {
      /* already gone */
    }
  }
  function prefetch(force = false): Link {
    if (!force && link.current && Date.now() - link.current.at < LINK_MAX_AGE) return link.current
    const p = api.appConnect(app.id)
    p.catch(() => {}) // the click handler reports it; no unhandled rejection before that
    return (link.current = { p, at: Date.now() })
  }
  useEffect(() => {
    live.current = true // StrictMode runs the cleanup once before the real mount
    prefetch() // the ref keeps the first request, so the remount does not start a second login
    return () => {
      live.current = false
      closeTab() // cancelled or failed; after a finished login the tab is already closed
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  // Closing before the login is finished stops the pending login on the server (the app is not connected yet).
  function cancel() {
    if (phase !== 'done' && link.current) void link.current.p.then(() => api.appDisconnect(app.id), () => {}).catch(() => {})
    onClose()
  }
  async function start() {
    tab.current = openLoadingTab() // before any await: still counts as the user's click
    setBlocked(!tab.current) // pop-up blocked anyway: offer a real link once the URL is ready
    setPhase('starting')
    setProblem('')
    try {
      let cur = prefetch()
      let r = await cur.p.catch(() => null)
      if (!r) {
        cur = prefetch(true) // the early request failed: ask once more now that the user is waiting
        r = await cur.p
      }
      if (!live.current) return
      if (r.connected || !r.url) {
        closeTab()
        return onDone(success)
      }
      let ok = false
      try {
        ok = new URL(r.url).protocol === 'https:'
      } catch {
        /* not a URL */
      }
      if (!ok) throw new Error('Alamat login dari server tidak aman, sambungan dibatalkan.')
      setUrl(r.url)
      if (tab.current) {
        tab.current.opener = null
        tab.current.location.replace(r.url)
      }
      setPhase('waiting')
      const end = Math.min(Date.now() + 180_000, cur.at + 530_000)
      while (live.current && Date.now() < end) {
        await new Promise((res) => setTimeout(res, 4000))
        if (!live.current) return
        try {
          if ((await api.appStatus(app.id)).status === 'connected') return finish()
        } catch {
          /* one failed check is not the end: keep waiting */
        }
      }
      if (live.current) setPhase('late')
    } catch (e) {
      closeTab()
      if (!live.current) return
      link.current = null // a failed or expired link is never reused
      setProblem(errText(e))
      setPhase('error')
    }
  }
  // Back to our app: close the login tab we opened (allowed for script-opened tabs) and bring this one to the front.
  function finish() {
    const w = tab.current
    closeTab()
    window.focus()
    if (!w || w.closed) return onDone(success)
    setPhase('done') // the browser kept the tab open: tell the user
  }
  return (
    <Dialog title={`Hubungkan ${app.name}`} onClose={cancel}>
      <div className="dlg-body">
      {phase === 'done' ? (
        <p className="note-box connect-ok" role="status">
          {success} Anda boleh menutup tab login.
        </p>
      ) : (
        <ol className="connect-steps">
          <li>Anda akan diarahkan ke halaman login {app.name}.</li>
          <li>Masuk dan setujui izin yang diminta.</li>
          <li>Setelah selesai, kembali ke sini. Halaman ini akan memberi tahu bila sudah tersambung.</li>
        </ol>
      )}
      {phase === 'waiting' && (
        <p className="note-box" role="status">
          <span className="runprog-row"><Spinner /><span>Menunggu Anda menyelesaikan login di tab lain…</span></span>{' '}
          <a href={url} target="_blank" rel="noopener noreferrer">Buka halaman login lagi</a>
        </p>
      )}
      {phase === 'late' && (
        <p className="problem-bar" role="alert">
          Waktu habis sebelum login selesai. Tutup dialog ini lalu coba hubungkan lagi.
        </p>
      )}
      {phase === 'error' && (
        <p className="problem-bar" role="alert">
          {problem}
        </p>
      )}
      <div className="dlg-actions">
        {phase === 'done' ? (
          <button type="button" className="btn primary" onClick={() => onDone(success)}>
            Selesai
          </button>
        ) : (
          <button type="button" className="btn quiet-btn" onClick={cancel}>
            {phase === 'waiting' ? 'Batal' : 'Tutup'}
          </button>
        )}
        {phase === 'waiting' && blocked && (
          <a className="btn primary" href={url} target="_blank" rel="noopener noreferrer">
            Buka halaman login
          </a>
        )}
        {(phase === 'intro' || phase === 'error' || phase === 'starting') && (
          <button type="button" className="btn primary" disabled={phase === 'starting'} onClick={() => void start()}>
            {phase === 'starting' ? <span className="runprog-row"><Spinner />Menyiapkan…</span> : 'Lanjut ke halaman login'}
          </button>
        )}
      </div>
      </div>
    </Dialog>
  )
}

// Same blocks as the loaded page (search row, linked cards, catalog grid), so the first paint already
// shows the shape of the list and nothing jumps when the data lands. The note appears after 3 s (CSS).
function AppsSkeleton() {
  return (
    <div className="skel skel-apps" role="status" aria-busy="true">
      <span className="sr">Memuat daftar aplikasi…</span>
      <div className="skel-body" aria-hidden="true">
        <div className="skel-app-tools">
          <i className="skel-search" />
          <span className="skel-pills">
            {[70, 132, 106, 118, 104, 88].map((w, i) => (
              <i key={i} className="skel-pill" style={{ width: w }} />
            ))}
          </span>
        </div>
        <section className="apps-group apps-linked-sec">
          <header>
            <h2>
              Tersambung <span className="slow-note">· Sedang memuat daftar aplikasi…</span>
            </h2>
          </header>
          <ul className="app-rows">
            {[0, 1, 2].map((i) => (
              <li key={i} className="app-card app-row skel-app-row">
                <span className="skel-head">
                  <i className="skel-mark" />
                  <span className="skel-lines">
                    <i className="skel-bar w40" />
                    <i className="skel-bar w70 thin" />
                  </span>
                </span>
                <i className="skel-btn" />
              </li>
            ))}
          </ul>
        </section>
        <section className="apps-group">
          <header>
            <h2>Aplikasi lain</h2>
          </header>
          <ul className="app-grid app-mini-grid">
            {Array.from({ length: 12 }, (_, i) => (
              <li key={i} className="app-card app-mini skel-app-mini">
                <span className="skel-head">
                  <i className="skel-mark sm" />
                  <i className="skel-bar w40" />
                </span>
                <i className="skel-btn sm" />
                <span className="skel-desc">
                  <i className="skel-bar w70 thin" />
                  <i className="skel-bar w40 thin" />
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}

export function AppsPage() {
  const conns = useConnections()
  const catFn = useCallback(() => cachedRead('apps-catalog', () => api.appsCatalog()), [])
  const cat = useLoad(catFn)
  const admin = useAdminMode()
  const [result] = useState(readResult)
  const [problem, setProblem] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [asking, setAsking] = useState<string | null>(null)
  const [picker, setPicker] = useState<'gdrive' | null>(null)
  const [saved, setSaved] = useState('')
  const [joined, setJoined] = useState('')
  const [how, setHow] = useState(false)
  const [q, setQ] = useState('')
  const [only, setOnly] = useState('')
  const [limit, setLimit] = useState(12)
  const [tab, setTabState] = useState<'apps' | 'skills'>(() => {
    try {
      return localStorage.getItem('pegawai-ai.apps-tab') === 'skills' ? 'skills' : 'apps'
    } catch {
      return 'apps'
    }
  })
  const setTab = (t: 'apps' | 'skills') => {
    setTabState(t)
    try {
      localStorage.setItem('pegawai-ai.apps-tab', t)
    } catch {
      // storage blocked: the tab just does not persist
    }
  }
  const [connecting, setConnecting] = useState<HermesApp | null>(null)
  useEffect(() => {
    if (result) go('/aplikasi', true) // drop the flag so a refresh does not show the banner again
  }, [result])
  useEffect(() => setLimit(12), [q, only]) // a new search starts at the first page

  async function connect(p: ConnProvider) {
    setBusy(p)
    setProblem('')
    try {
      window.location.assign((await api.connectStart(p)).url)
    } catch (e) {
      setProblem(errText(e))
      setBusy(null)
    }
  }
  async function disconnect(p: ConnProvider) {
    setBusy(p)
    setProblem('')
    setAsking(null)
    try {
      await api.disconnect(p)
      forgetReads('connections')
      conns.retry()
    } catch (e) {
      setProblem(errText(e))
    }
    setBusy(null)
  }
  async function disconnectApp(a: HermesApp) {
    setBusy(a.id)
    setProblem('')
    setAsking(null)
    try {
      await api.appDisconnect(a.id)
      forgetReads('apps-catalog')
      cat.retry()
    } catch (e) {
      setProblem(errText(e))
    }
    setBusy(null)
  }

  async function recheck(id: ConnProvider) {
    setBusy(id)
    try {
      await api.connections(true) // bypass the 60 s cache, then reload the list (served from the fresh cache)
    } catch {
      /* the reload below shows the error */
    }
    forgetReads('connections')
    conns.retry()
    setBusy(null)
  }

  const by = new Map<string, Connection>((conns.data ?? []).map((c) => [c.provider, c]))
  const term = q.trim().toLowerCase()
  const hit = (name: string, text: string, category: string) => (!term || `${name} ${text}`.toLowerCase().includes(term)) && (!only || only === category)

  const pickDrive = (
    <button type="button" className="btn outline" onClick={() => setPicker('gdrive')}>
      Pilih dari Drive
    </button>
  )

  function oauthCard(id: ConnProvider, mode: 'row' | 'mini') {
    const a = APPS[id]
    const c = by.get(id)
    if (!c) return null
    const name = OAUTH_NAME[id]
    const status = c.status
    const soon = status === 'not_configured' && !admin // not set up by the admin: users only see "Segera hadir"
    const mustAsk = status === 'broken' && c.needs === 'admin'
    return (
      <li key={id} className={`app-card ${mode === 'row' ? 'app-row' : 'app-mini'}`} data-app={id} data-s={status}>
        <div className="app-card-head">
          <div className="app-mark">
            <AppLogo id={id} name={name} size={32} fallback={<Mark id={id} />} />
          </div>
          <div className="app-top">
            <h3>{name}</h3>
            {status === 'connected' && mode !== 'row' && <CapChip cap="ok" label="Tersambung" />}
            {status === 'reconnect' && <CapChip cap="mock" label="Perlu disambungkan ulang" />}
            {status === 'broken' && <CapChip cap="mock" label="Perlu perbaikan" />}
            {status === 'needs_scope' && <CapChip cap="mock" label="Perlu izin tambahan" />}
            {status === 'not_configured' && <CapChip cap="none" label={soon ? 'Segera hadir' : 'Belum diatur admin'} />}
          </div>
        </div>
        <p>{a.enables}</p>
        {(status === 'connected' || status === 'needs_scope') && c.account && mode === 'row' && (
          <p className="connect-acct" title={c.account}>
            Akun: <b>{c.account}</b>
          </p>
        )}
        {status === 'reconnect' && <p className="connect-warn">Izin akses sudah tidak berlaku. Hubungkan ulang agar bisa dipakai lagi.</p>}
        {(status === 'broken' || status === 'needs_scope') && (
          <p className="connect-warn" role="status">
            {c.reason ?? `${a.name} sedang bermasalah.`}
          </p>
        )}
        {status === 'not_configured' && admin && (
          <p className="quiet small" id={`why-${id}`}>
            Administrator belum mengatur {a.name}, jadi belum bisa disambungkan.
          </p>
        )}
        {id === 'gmail' && admin && (
          <p className="quiet small">Google menganggap akses baca Drive dan Gmail sebagai izin terbatas (restricted scope), jadi pemakaian produksi di atas 100 pengguna perlu verifikasi aplikasi oleh Google.</p>
        )}
        {id === 'gmail' && (
          <button type="button" className="btn link app-how" aria-expanded={how} aria-controls="how-gmail" onClick={() => setHow((v) => !v)}>
            {how ? 'Sembunyikan cara kerja' : 'Cara kerja tombol draf'}
          </button>
        )}
        {id === 'gmail' && how && (
          <p className="note-box" id="how-gmail">
            Di bawah setiap jawaban pegawai ada tombol &ldquo;Simpan sebagai draf Gmail&rdquo;. Anda bisa mengubah penerima, subjek, dan isinya dulu. Hasilnya hanya draf di Gmail Anda. Anda sendiri yang membuka dan mengirimnya.
          </p>
        )}
        {status === 'not_configured' && admin && <AdminHint c={c} />}
        <div className="app-card-act">
          {asking === id ? (
            <span className="confirm-actions" role="alert">
              <span className="app-ask">Putuskan {a.name}?</span>
              <button type="button" className="btn danger" disabled={busy === id} onClick={() => void disconnect(id)}>
                Putuskan
              </button>
              <button type="button" className="btn quiet-btn" onClick={() => setAsking(null)}>
                Batal
              </button>
            </span>
          ) : (
            <>
              {status === 'connected' ? (
                <button type="button" className="btn soft" disabled={busy === id} onClick={() => setAsking(id)}>
                  Putuskan
                </button>
              ) : soon ? null : status === 'broken' && c.needs !== 'reconnect' ? (
                <button type="button" className="btn primary" disabled={busy === id} onClick={() => void recheck(id)}>
                  {mustAsk ? 'Sudah diaktifkan? Periksa lagi' : 'Periksa lagi'}
                </button>
              ) : (
                <button
                  type="button"
                  className={`btn ${status === 'reconnect' || status === 'broken' || status === 'needs_scope' ? 'primary' : 'soft'}`}
                  disabled={status === 'not_configured' || busy === id}
                  aria-describedby={status === 'not_configured' ? `why-${id}` : undefined}
                  onClick={() => void connect(id)}
                >
                  {status === 'reconnect' || status === 'broken' || status === 'needs_scope' ? 'Sambungkan ulang' : 'Hubungkan'}
                </button>
              )}
              {(status === 'reconnect' || status === 'broken' || status === 'needs_scope') && (
                <button type="button" className="btn link" disabled={busy === id} onClick={() => setAsking(id)}>
                  Putuskan
                </button>
              )}
              {(status === 'connected' || status === 'needs_scope') && id === 'gdrive' && pickDrive}
            </>
          )}
        </div>
      </li>
    )
  }

  function appCard(a: HermesApp, mode: 'row' | 'mini') {
    const on = a.status === 'connected'
    const ownDrive = merged.get('gdrive') === a && ['connected', 'needs_scope'].includes(by.get('gdrive')?.status ?? '') // our Drive connection folded into this card
    return (
      <li key={a.id} className={`app-card ${mode === 'row' ? 'app-row' : 'app-mini'}`} data-app={a.id} data-s={on ? 'connected' : 'disconnected'}>
        <div className="app-card-head">
          <div className="app-mark">
            <AppLogo id={a.id} name={a.name} size={32} fallback={<Initial name={a.name} />} />
          </div>
          <div className="app-top">
            <h3>{a.name}</h3>
            {on && mode !== 'row' && <CapChip cap="ok" label="Tersambung" />}
          </div>
        </div>
        <p>{a.description}</p>
        {on && shownAccounts(a.accounts, admin).length > 0 && (
          <p className="connect-acct" title={shownAccounts(a.accounts, admin).join(', ')}>
            {mode === 'row' ? (
              <>
                Akun: <b>{shownAccounts(a.accounts, admin).join(', ')}</b>
              </>
            ) : (
              <>
                Tersambung sebagai <b>{shownAccounts(a.accounts, admin).join(', ')}</b>
              </>
            )}
          </p>
        )}
        {admin && (
          <p className="quiet small app-code">
            Kode: <code>{a.id}</code>
          </p>
        )}
        <div className="app-card-act">
          {asking === a.id ? (
            <span className="confirm-actions" role="alert">
              <span className="app-ask">Putuskan {a.name}?</span>
              <button type="button" className="btn danger" disabled={busy === a.id} onClick={() => void disconnectApp(a)}>
                Putuskan
              </button>
              <button type="button" className="btn quiet-btn" onClick={() => setAsking(null)}>
                Batal
              </button>
            </span>
          ) : (
            <>
              {on ? (
                <button type="button" className="btn soft" disabled={busy === a.id} onClick={() => setAsking(a.id)}>
                  Putuskan
                </button>
              ) : (
                <button type="button" className="btn soft" disabled={busy === a.id} onClick={() => setConnecting(a)}>
                  Hubungkan
                </button>
              )}
              {ownDrive && pickDrive}
            </>
          )}
        </div>
      </li>
    )
  }

  // Tersambung first (our Google sign-in plus Hermes apps already connected), then one flat catalog of everything else.
  const apps = (cat.data?.apps ?? []).filter((a) => admin || !a.technical)
  const cats = (cat.data?.categories ?? []).filter((c) => admin || c.id !== 'dev')
  const merged = new Map<ConnProvider, HermesApp>()
  for (const id of Object.keys(OWN_AS_HERMES) as ConnProvider[]) {
    const h = apps.find((a) => OWN_AS_HERMES[id].includes(a.id))
    if (h) merged.set(id, h)
  }
  const oauthIds = (['gdrive', 'gmail'] as ConnProvider[]).filter((id) => by.has(id) && !merged.has(id))
  const linkedHermes = apps.filter((a) => a.status === 'connected')
  // Every state in which the owner can already act on the connection counts as linked; problems come first.
  const linkedOauth = (Object.keys(OWN_AS_HERMES) as ConnProvider[])
    .filter((id) => ['connected', 'needs_scope', 'reconnect', 'broken'].includes(by.get(id)?.status ?? '') && (!merged.has(id) || merged.get(id)?.status !== 'connected') && by.has(id))
    .sort((a, b) => Number(!['needs_scope', 'reconnect', 'broken'].includes(by.get(a)?.status ?? '')) - Number(!['needs_scope', 'reconnect', 'broken'].includes(by.get(b)?.status ?? '')))
  const groups = cats
    .map((c) => ({
      c,
      oauth: oauthIds.filter((id) => OAUTH_CAT[id] === c.id && hit(OAUTH_NAME[id], APPS[id].enables, c.id)),
      apps: apps.filter((a) => a.category === c.id && hit(a.name, a.description, c.id)),
    }))
    .filter((g) => g.oauth.length + g.apps.length > 0)
  type CatItem = { k: 'o'; id: ConnProvider } | { k: 'a'; a: HermesApp }
  const catalog = groups
    .flatMap((g): CatItem[] => [...g.oauth.map((id) => ({ k: 'o' as const, id })), ...g.apps.map((a) => ({ k: 'a' as const, a }))])
    .filter((x) => (x.k === 'o' ? !['connected', 'needs_scope', 'reconnect', 'broken'].includes(by.get(x.id)?.status ?? '') : x.a.status !== 'connected'))
    .sort((x, y) => Number(x.k !== 'o') - Number(y.k !== 'o')) // the built-in Google apps lead the first page
  const shown = catalog.slice(0, limit)
  const linkedCount = linkedOauth.length + linkedHermes.length
  const ready = (conns.data || conns.state === 'error') && (cat.data || cat.state === 'error')
  const failed = conns.state === 'error' && !conns.data ? conns : cat.state === 'error' && !cat.data ? cat : null

  return (
    <section className="page apps" data-tab={tab}>
      <PageHead title="Aplikasi" sub="Hubungkan aplikasi yang Anda pakai agar pegawai AI bisa membantu di sana." />
      {result && (
        <p className={result.ok ? 'note-box connect-ok' : 'problem-bar'} role={result.ok ? 'status' : 'alert'}>
          {result.text}
        </p>
      )}
      {joined && (
        <p className="note-box connect-ok" role="status">
          {joined}
        </p>
      )}
      {saved && (
        <p className="note-box connect-ok" role="status">
          {saved} <a href="#/pengetahuan">Lihat di Pengetahuan</a>
        </p>
      )}
      {problem && (
        <p className="problem-bar" role="alert">
          {problem}
        </p>
      )}
      <div className="tabs" role="tablist" aria-label="Aplikasi dan keahlian pegawai">
        {([['apps', 'Aplikasi'], ['skills', 'Keahlian pegawai']] as const).map(([id, label]) => (
          <button key={id} type="button" role="tab" aria-selected={tab === id} onClick={() => setTab(id)}>
            {label}
          </button>
        ))}
      </div>
      {tab === 'skills' && (
        <>
          <div className="apps-tools apps-tools-row apps-tools-solo">
            <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari keahlian" aria-label="Cari keahlian" />
          </div>
          <SkillsSection q={q} />
        </>
      )}
      {tab === 'apps' && (
        <>
          {ready && !failed && (
            <div className="apps-tools apps-tools-row">
              <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari aplikasi" aria-label="Cari aplikasi" />
              <div className="apps-cats" role="group" aria-label="Kategori">
                <button type="button" aria-pressed={only === ''} onClick={() => setOnly('')}>
                  Semua
                </button>
                {cats.map((c) => (
                  <button key={c.id} type="button" aria-pressed={only === c.id} onClick={() => setOnly(only === c.id ? '' : c.id)}>
                    {c.name}
                  </button>
                ))}
              </div>
            </div>
          )}
          <div className="apps-scroll">
            {!ready && !failed && <AppsSkeleton />}
            {failed && (
              <ErrorLine
                text={failed.error}
                onRetry={() => {
                  conns.retry()
                  cat.retry()
                }}
              />
            )}
            {ready && !failed && (
              <>
                <section className="apps-group apps-linked-sec" aria-labelledby="g-linked">
                  <header>
                    <h2 id="g-linked">
                      Tersambung{linkedCount > 0 && <span className="quiet"> · {linkedCount}</span>}
                    </h2>
                  </header>
                  {linkedCount === 0 ? (
                    <p className="quiet">Belum ada aplikasi tersambung. Pilih salah satu di bawah.</p>
                  ) : (
                    <ul className="app-rows">
                      {linkedOauth.map((id) => oauthCard(id, 'row'))}
                      {linkedHermes.map((a) => appCard(a, 'row'))}
                    </ul>
                  )}
                </section>
                <section className="apps-group" aria-labelledby="g-catalog">
                  <header>
                    <h2 id="g-catalog">
                      Aplikasi lain<span className="quiet"> · {catalog.length}</span>
                    </h2>
                  </header>
                  {shown.length > 0 && <ul className="app-grid app-mini-grid">{shown.map((x) => (x.k === 'o' ? oauthCard(x.id, 'mini') : appCard(x.a, 'mini')))}</ul>}
                  {catalog.length > limit && (
                    <button type="button" className="btn soft apps-more" onClick={() => setLimit((n) => n + 12)}>
                      Tampilkan lebih banyak ({catalog.length - limit} lagi)
                    </button>
                  )}
                  {catalog.length === 0 && (term || only) && (
                    <p className="quiet">
                      Tidak ada aplikasi yang cocok.{' '}
                      <button
                        type="button"
                        className="btn link small"
                        onClick={() => {
                          setQ('')
                          setOnly('')
                        }}
                      >
                        Hapus pencarian
                      </button>
                    </p>
                  )}
                </section>
              </>
            )}
          </div>
        </>
      )}
      {picker && createPortal(<SourcePicker provider={picker} onClose={() => setPicker(null)} onDone={(ok) => setSaved(`${ok.length} item disimpan ke Pengetahuan.`)} />, document.body)}
      {connecting && (
        <ConnectDialog
          app={connecting}
          onClose={() => {
            setConnecting(null)
            cat.retry()
          }}
          onDone={(message) => {
            setConnecting(null)
            setJoined(message)
            void api.appsCatalog(true).finally(() => {
              forgetReads('apps-catalog')
              cat.retry()
            })
          }}
        />
      )}
    </section>
  )
}

// Compact pointer on Kemampuan > Alat.
export function AppsLink() {
  return (
    <p className="apps-link">
      Menyambungkan Google Drive atau Gmail? Buka <a href="#/aplikasi">Aplikasi</a>.
    </p>
  )
}
