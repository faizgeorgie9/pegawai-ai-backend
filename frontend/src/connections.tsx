import { useCallback, useEffect, useRef, useState } from 'react'
import { AppLogo } from './app-logos'
import { createPortal } from 'react-dom'
import { api, canWhatsApp, errText } from './bff'
import { useAdminMode } from './adminMode'
import type { ConnProvider, Connection, HermesApp } from './bff'
import { useData } from './data'
import { go } from './router'
import { SourcePicker } from './pick-ui'
import { SkillsSection, primeSkills } from './skills-ui'
import { Dialog, ErrorLine } from './ui'
import { CapChip, PageHead, Spinner, useLoad } from './ui-extra'
import { cachedRead, forgetReads, onLinkIntent } from './session-cache'
import { InstagramGuide, SocialPostList } from './social-ui'
import { WhatsAppAppCard } from './whatsapp-ui'

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
  instagram: {
    name: 'Instagram',
    enables: 'Pegawai AI bisa menyiapkan postingan (foto, carousel, atau Reels) dan membaca ringkasan performa akun Instagram Bisnis atau Kreator Anda. Postingan baru terbit setelah Anda menyetujuinya.',
    where: 'Kartu persetujuan di chat, lalu daftar Posting di kartu ini.',
  },
  canva: {
    name: 'Canva',
    enables: 'Pegawai AI bisa membuat dan mengubah desain di akun Canva Anda, lalu mengekspornya sebagai gambar atau dokumen. Setiap orang menyambungkan akun Canva miliknya sendiri.',
    where: 'Hasil desain muncul sebagai kartu Gambar atau Dokumen di chat.',
  },
}
const WHY: Record<string, string> = {
  denied: 'Izin tidak diberikan, jadi akun belum tersambung.',
  state: 'Permintaan sambungan sudah kedaluwarsa atau tidak dikenal. Coba hubungkan lagi.',
  exchange: 'Sambungan tidak diterima. Coba lagi; jika terus gagal, hubungi admin Anda.',
  scope: 'Izin yang diperlukan tidak dicentang. Hubungkan lagi dan centang semua izin yang diminta.',
  personal: 'Akun Instagram ini masih akun pribadi. Ubah dulu ke akun Bisnis atau Kreator (gratis), lalu hubungkan lagi.',
}

// The BFF sends the browser back to #/aplikasi?connect=ok|error&app=...&reason=... after the provider's consent page.
function readResult(): { ok: boolean; text: string; app: ConnProvider | null; reason: string } | null {
  const q = new URLSearchParams(location.hash.split('?')[1] ?? '')
  const c = q.get('connect')
  if (c !== 'ok' && c !== 'error') return null
  const appId = q.get('app') as ConnProvider
  const app = APPS[appId] as AppDef | undefined
  const reason = q.get('reason') ?? ''
  if (c === 'ok') return { ok: true, text: `${app?.name ?? 'Aplikasi'} tersambung.`, app: app ? appId : null, reason }
  return {
    ok: false,
    text: `${app ? `${app.name} belum tersambung. ` : ''}${WHY[reason] ?? 'Sambungan gagal. Coba lagi.'}`,
    app: app ? appId : null,
    reason,
  }
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
onLinkIntent('a[href="#/aplikasi"]', primeApps, 'apps-data')

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

const OAUTH_CAT: Record<ConnProvider, string> = { gdrive: 'docs', gmail: 'comms', instagram: 'social', canva: 'design' }
const OAUTH_NAME: Record<ConnProvider, string> = { gdrive: 'Google Drive', gmail: 'Gmail', instagram: 'Instagram', canva: 'Canva' }
// Our own connections, in the order their cards lead the catalog. Instagram and Canva exist even when the
// Hermes catalog has no matching category, so they are added outside `groups` below.
const OAUTH_IDS: ConnProvider[] = ['gdrive', 'gmail', 'instagram', 'canva']
const IG_TYPE: Record<NonNullable<Connection['account_type']>, string> = { BUSINESS: 'Bisnis', CREATOR: 'Kreator', PERSONAL: 'Pribadi' }

// One-card rule: an app that exists both as our own connection and as a Hermes connector gets ONE card. The Hermes connector
// wins (it is always connectable); our connection stays reachable through its extra action (e.g. "Pilih dari Drive") when
// it is connected too. Our connection alone is shown when the catalog has no matching connector. Add a line per known overlap
// (our provider -> Hermes ids); the live catalog has no overlaps today.
const OWN_AS_HERMES: Record<ConnProvider, string[]> = { gdrive: ['google_drive', 'googledrive'], gmail: ['gmail'], instagram: [], canva: [] } // Canva is handled separately (slice R2): the old Hermes connector is switched off.

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

// Each part of the page waits for its own read. The connections answer in tens of milliseconds; the catalog runs
// two Hermes CLI calls in the BFF (up to ~10 s on a cold cache). One page-wide skeleton hid the connected apps
// behind the slow catalog, so every part now shows the shape of its own block instead.
function LinkedRowSkeleton() {
  return (
    <li className="app-card app-row skel-app-row" aria-hidden="true">
      <span className="skel-head">
        <i className="skel-mark" />
        <span className="skel-lines">
          <i className="skel-bar w40" />
          <i className="skel-bar w70 thin" />
        </span>
      </span>
      <i className="skel-btn" />
    </li>
  )
}

function LinkedSkeleton() {
  return (
    <ul className="app-rows" aria-hidden="true">
      <LinkedRowSkeleton />
      <LinkedRowSkeleton />
    </ul>
  )
}

// Keeps the search row's real height while the category names, which come with the catalog, are on the way.
function ToolsSkeleton() {
  return (
    <div className="skel skel-apps" aria-hidden="true">
      <div className="skel-body">
        <div className="skel-app-tools">
          <i className="skel-search" />
          <span className="skel-pills">
            {[70, 132, 106, 118, 104, 88].map((w, i) => (
              <i key={i} className="skel-pill" style={{ width: w }} />
            ))}
          </span>
        </div>
      </div>
    </div>
  )
}

function CatalogSkeleton() {
  return (
    <div className="skel skel-apps" role="status" aria-busy="true">
      <span className="sr">Sedang memuat daftar aplikasi…</span>
      <div className="skel-body" aria-hidden="true">
        <ul className="app-grid app-mini-grid">
          {Array.from({ length: 9 }, (_, i) => (
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
      </div>
    </div>
  )
}

export function AppsPage() {
  const conns = useConnections()
  const catFn = useCallback(() => cachedRead('apps-catalog', () => api.appsCatalog()), [])
  const cat = useLoad(catFn)
  const admin = useAdminMode()
  const { bots } = useData()
  const [result] = useState(readResult)
  const personal = !!result && !result.ok && result.app === 'instagram' && result.reason === 'personal'
  const [problem, setProblem] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [asking, setAsking] = useState<string | null>(null)
  const [picker, setPicker] = useState<'gdrive' | null>(null)
  const [saved, setSaved] = useState('')
  const [joined, setJoined] = useState('')
  const [how, setHow] = useState(false)
  const [igGuide, setIgGuide] = useState(personal)
  const [igPosts, setIgPosts] = useState(false)
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

  // WhatsApp belongs to the account, not to one connector: one card under the "comms" category while a
  // customer-service employee exists. It only points at that employee's tab; the channel is set up there.
  const waShown =
    bots.some(canWhatsApp) && hit('WhatsApp', 'Pelanggan chat ke nomor bisnis Anda dan dijawab oleh pegawai layanan pelanggan.', 'comms')

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
    const acct = id === 'instagram' && c.account_type ? `${c.account} · ${IG_TYPE[c.account_type]}` : c.account
    const ask =
      id === 'instagram'
        ? 'Putuskan Instagram? Postingan yang sudah terbit tidak terhapus. Pegawai tidak bisa lagi menyiapkan postingan.'
        : id === 'canva'
          ? 'Putuskan Canva? Desain Anda di Canva tidak terhapus.'
          : `Putuskan ${a.name}?`
    const connectLabel = status === 'reconnect' || status === 'broken' || status === 'needs_scope' ? 'Sambungkan ulang' : 'Hubungkan'
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
        {(status === 'connected' || status === 'needs_scope') && acct && mode === 'row' && (
          <p className="connect-acct" title={acct}>
            Akun: {acct}
          </p>
        )}
        {id === 'canva' && (
          <p className="quiet small app-platform-note">Akun Canva gratis sudah cukup untuk membuat dan mengekspor desain. Isi otomatis dan Brand Kit butuh Canva Pro.</p>
        )}
        {id === 'instagram' && status === 'disconnected' && (
          <p className="quiet small app-platform-note">Hanya untuk akun Instagram Bisnis atau Kreator.</p>
        )}
        {status === 'reconnect' && <p className="connect-warn">{c.reason ?? 'Izin akses sudah tidak berlaku. Hubungkan ulang agar bisa dipakai lagi.'}</p>}
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
        {id === 'instagram' && status === 'disconnected' && (
          <button type="button" className="btn link small app-how" aria-expanded={igGuide} aria-controls="ig-guide" onClick={() => setIgGuide((v) => !v)}>
            Akun saya masih pribadi
          </button>
        )}
        {id === 'instagram' && igGuide && <InstagramGuide autoFocus={personal} onClose={() => setIgGuide(false)} />}
        {status === 'not_configured' && admin && (c.setup.length > 0 || (id !== 'instagram' && id !== 'canva')) && <AdminHint c={c} />}
        <div className="app-card-act">
          {asking === id ? (
            <span className="confirm-actions" role="alert">
              <span className="app-ask">{ask}</span>
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
                  {busy === id ? `Membuka ${name}…` : connectLabel}
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
        {id === 'instagram' && status === 'connected' && (
          <button type="button" className="btn soft app-ig-toggle" aria-expanded={igPosts} aria-controls="ig-posts" onClick={() => setIgPosts((v) => !v)}>
            Lihat posting
          </button>
        )}
        {id === 'instagram' && status === 'connected' && igPosts && <SocialPostList />}
      </li>
    )
  }

  function appCard(a: HermesApp, mode: 'row' | 'mini') {
    const on = a.status === 'connected'
    const accounts = shownAccounts(a.accounts, admin).join(', ')
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
        {on && accounts.length > 0 && (
          <p className="connect-acct" title={accounts}>
            {mode === 'row' ? <>Akun: {accounts}</> : <>Tersambung sebagai {accounts}</>}
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

  // Tersambung (only fully working connections) first, then the ones that need reconnecting, then one flat catalog of everything else.
  // The old Hermes Canva connector is switched off while our own Canva connection exists (contract: it is disabled).
  const apps = (cat.data?.apps ?? [])
    .filter((a) => admin || !a.technical)
    .filter((a) => !(by.has('canva') && ['canva', 'canva_mcp'].includes(a.id)))
  const cats = (cat.data?.categories ?? []).filter((c) => admin || c.id !== 'dev')
  const merged = new Map<ConnProvider, HermesApp>()
  for (const id of Object.keys(OWN_AS_HERMES) as ConnProvider[]) {
    const h = apps.find((a) => OWN_AS_HERMES[id].includes(a.id))
    if (h) merged.set(id, h)
  }
  const oauthIds = OAUTH_IDS.filter((id) => by.has(id) && !merged.has(id))
  const linkedHermes = apps.filter((a) => a.status === 'connected')
  // "Tersambung" only counts apps that really work; every problem gets its own group below.
  // A connection already represented by a connected Hermes card is not repeated as its own card.
  const connectedOauth: ConnProvider[] = []
  const problemOauth: ConnProvider[] = []
  for (const id of OAUTH_IDS) {
    const c = by.get(id)
    if (!c || merged.get(id)?.status === 'connected') continue
    if (c.status === 'connected') connectedOauth.push(id)
    else if (['needs_scope', 'reconnect', 'broken'].includes(c.status)) problemOauth.push(id)
  }
  // Instagram and Canva have no guaranteed Hermes category; their cards are added next to the Google ones.
  const ownExtra = (['instagram', 'canva'] as ConnProvider[]).filter((id) => by.has(id) && hit(OAUTH_NAME[id], APPS[id].enables, OAUTH_CAT[id]))
  const groups = cats
    .map((c) => ({
      c,
      oauth: oauthIds.filter((id) => id !== 'instagram' && id !== 'canva' && OAUTH_CAT[id] === c.id && hit(OAUTH_NAME[id], APPS[id].enables, c.id)),
      apps: apps.filter((a) => a.category === c.id && hit(a.name, a.description, c.id)),
    }))
    .filter((g) => g.oauth.length + g.apps.length > 0)
  type CatItem = { k: 'o'; id: ConnProvider } | { k: 'a'; a: HermesApp } | { k: 'wa' }
  const catalog: CatItem[] = [
    ...groups.flatMap((g): CatItem[] => [...g.oauth.map((id) => ({ k: 'o' as const, id })), ...g.apps.map((a) => ({ k: 'a' as const, a }))]),
    ...ownExtra.map((id): CatItem => ({ k: 'o', id })),
  ]
    .filter((x) => (x.k === 'o' ? !['connected', 'needs_scope', 'reconnect', 'broken'].includes(by.get(x.id)?.status ?? '') : x.k === 'a' ? x.a.status !== 'connected' : true))
    .sort((x, y) => Number(x.k !== 'o') - Number(y.k !== 'o')) // the built-in apps lead the first page
  if (waShown) {
    // Right after Gmail (the one "comms" card every workspace has), or at the start of the catalog apps.
    const gmailAt = catalog.findIndex((x) => x.k === 'o' && x.id === 'gmail')
    const start = catalog.findIndex((x) => x.k !== 'o')
    const at = gmailAt >= 0 ? gmailAt + 1 : start
    catalog.splice(at < 0 ? catalog.length : at, 0, { k: 'wa' })
  }
  const shown = catalog.slice(0, limit)
  const linkedCount = connectedOauth.length + linkedHermes.length
  const problemCount = problemOauth.length
  const connsReady = !!conns.data
  const connsFailed = !conns.data && conns.state === 'error'
  const catReady = !!cat.data
  const catFailed = !cat.data && cat.state === 'error'

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
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            onPointerEnter={id === 'skills' ? primeSkills : undefined}
            onFocus={id === 'skills' ? primeSkills : undefined}
            onClick={() => setTab(id)}
          >
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
          {/* The category names arrive with the catalog: hold the row's height instead of hiding it. */}
          {catReady ? (
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
          ) : catFailed ? null : (
            <ToolsSkeleton />
          )}
          <div className="apps-scroll">
            {(!catFailed || linkedCount > 0 || connsFailed) && (
              <section className="apps-group apps-linked-sec" aria-labelledby="g-linked">
                <header>
                  <h2 id="g-linked">
                    Tersambung
                    {catReady && !connsFailed && <span className="quiet"> · {linkedCount}</span>}
                    {!connsFailed && !catFailed && (!connsReady || !catReady) && <span className="slow-note"> · Sedang memuat…</span>}
                  </h2>
                </header>
                {connsFailed && <ErrorLine text={conns.error} onRetry={() => conns.retry()} />}
                {!connsFailed && !connsReady ? (
                  <LinkedSkeleton />
                ) : linkedCount > 0 || (!catReady && !catFailed && !connsFailed) ? (
                  <ul className="app-rows">
                    {connectedOauth.map((id) => oauthCard(id, 'row'))}
                    {linkedHermes.map((a) => appCard(a, 'row'))}
                    {/* Connected Hermes apps arrive with the catalog: one row keeps their place until then. */}
                    {!catReady && !catFailed && !connsFailed && <LinkedRowSkeleton />}
                  </ul>
                ) : catReady && !connsFailed ? (
                  <p className="quiet">Belum ada aplikasi tersambung. Pilih salah satu di bawah.</p>
                ) : null}
              </section>
            )}
            {problemCount > 0 && (
              <section className="apps-group" aria-labelledby="g-problem">
                <header>
                  <h2 id="g-problem">
                    Perlu dihubungkan ulang<span className="quiet"> · {problemCount}</span>
                  </h2>
                </header>
                <ul className="app-rows">{problemOauth.map((id) => oauthCard(id, 'row'))}</ul>
              </section>
            )}
            <section className="apps-group" aria-labelledby="g-catalog">
              <header>
                <h2 id="g-catalog">
                  Aplikasi lain{catReady && <span className="quiet"> · {catalog.length}</span>}
                </h2>
              </header>
              {catFailed ? (
                <ErrorLine text={cat.error} onRetry={() => cat.retry()} />
              ) : !catReady ? (
                <CatalogSkeleton />
              ) : (
                <>
                  {shown.length > 0 && (
                    <ul className="app-grid app-mini-grid">
                      {shown.map((x) => (x.k === 'o' ? oauthCard(x.id, 'mini') : x.k === 'a' ? appCard(x.a, 'mini') : <WhatsAppAppCard key="whatsapp" />))}
                    </ul>
                  )}
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
                </>
              )}
            </section>
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
