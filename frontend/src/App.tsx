import { Component, Suspense, lazy, useEffect, useRef, useState } from 'react'
import type { ComponentType, ReactNode } from 'react'
import { useActions } from './ActionCard'
import { isAdminRole, setAuthRole, useAdminMode, useIsAdmin } from './adminMode'
import { ApiError, api, canWhatsApp, errText, onSessionEnd } from './bff'
import type { AuthUser } from './bff'
import Dashboard from './Dashboard'
import { DataProvider, useData } from './data'
import { useHandoverQueue } from './handover'
import { LoginModal } from './LoginModal'
import { botPath, go, groupPath, useRoute } from './router'
import type { Route } from './router'
import { onLinkIntent } from './session-cache'
import { BotAvatar, CLOSE, ErrorLine, I, Icon, MENU, elapsed } from './ui'
import { Loading } from './ui-extra'

// Pages load when first opened. The shell, Dashboard, login and the small shared pieces stay in the
// first chunk, so Beranda paints without paying for chat, the board or the admin screens.
// Named exports are wrapped here instead of adding a default export to every page. The module may
// export hooks beside its components, so only the picked key is narrowed to a component.
const lazyNamed = <T, K extends keyof T>(load: () => Promise<T>, key: K) =>
  lazy(() => load().then((m) => ({ default: m[key] as unknown as ComponentType<any> })))

const Marketing = lazy(() => import('./Marketing'))
const Uji = lazy(() => import('./Uji'))
const CS = lazy(() => import('./CS'))
const Activity = lazy(() => import('./Activity'))
const Kanban = lazy(() => import('./Kanban'))
const Settings = lazy(() => import('./Settings'))
const Pengetahuan = lazy(() => import('./Pengetahuan'))
const Kemampuan = lazyNamed(() => import('./Platform'), 'Kemampuan')
const AppsPage = lazyNamed(() => import('./connections'), 'AppsPage')
const AgentList = lazyNamed(() => import('./Agents'), 'AgentList')
const AgentNew = lazyNamed(() => import('./Agents'), 'AgentNew')
const AgentDetail = lazyNamed(() => import('./Agents'), 'AgentDetail')
const AgentEdit = lazyNamed(() => import('./Agents'), 'AgentEdit')
const ChatLayout = lazyNamed(() => import('./ChatLayout'), 'ChatLayout')
const GroupLayout = lazyNamed(() => import('./ChatLayout'), 'GroupLayout')
const Dialogs = lazyNamed(() => import('./Dialogs'), 'Dialogs')
const Output = lazy(() => import('./Output'))
const Pelanggan = lazy(() => import('./Pelanggan'))
const Mulai = lazy(() => import('./Mulai'))

// A page chunk that fails to arrive (an old tab after a deploy) shows one honest line instead of a
// blank screen. `main.tsx` already reloads once for a preload error; this covers the rest.
class RouteBoundary extends Component<{ children: ReactNode; resetKey?: string }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  // A new screen clears an earlier failure without remounting the next screen (chat keeps its state).
  componentDidUpdate(prev: { resetKey?: string }) {
    if (this.state.failed && prev.resetKey !== this.props.resetKey) this.setState({ failed: false })
  }
  render() {
    if (!this.state.failed) return this.props.children
    return (
      <section className="page">
        <ErrorLine text="Halaman ini gagal dimuat. Biasanya karena aplikasi baru saja diperbarui." onRetry={() => location.reload()} />
      </section>
    )
  }
}

const pageFallback = (
  <section className="page">
    <Loading text="Memuat halaman..." shape="page" />
  </section>
)

const TOKEN_KEY = 'pegawai_ai_token'
const SESSION_ENDED = 'Sesi Anda berakhir, silakan masuk lagi.'
// Routes behind the Admin sidebar group. A member is sent back to Beranda instead of seeing them.
const ADMIN_ROUTES: Record<string, true> = {
  marketing: true,
  cs: true,
  agen: true,
  'agen-baru': true,
  'agen-detail': true,
  'agen-ubah': true,
  tools: true,
  'computer-use': true,
  uji: true,
  aktivitas: true,
  mulai: true,
}

const storedToken = () => {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

// Everything this browser kept about the signed-in account goes on logout, so the next account starts clean.
function clearSession() {
  try {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem('pegawai_ai_user') // cached profile from older builds; only the token is trusted now
    localStorage.removeItem('pegawai-ai.admin-mode') // next admin login starts with the Admin group open again
    localStorage.removeItem('pa.lastBot')
    localStorage.removeItem('pa.lastGroup')
  } catch {
    /* private mode: nothing persisted */
  }
  setAuthRole(null)
}

// The app is only mounted after the stored session is validated, so no data or event stream is fetched before login.
export default function App() {
  return <AuthGate />
}

function AuthGate() {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [booting, setBooting] = useState(() => !!storedToken())
  const [notice, setNotice] = useState('')

  useEffect(
    () =>
      onSessionEnd(() => {
        clearSession()
        setUser(null)
        setBooting(false)
        setNotice(SESSION_ENDED)
        go('/', true)
      }),
    [],
  )

  useEffect(() => {
    if (!storedToken()) return
    let cancelled = false
    api.auth.me().then(
      (res) => {
        if (cancelled) return
        setAuthRole(res.user.role)
        setUser(res.user)
        setBooting(false)
      },
      (e) => {
        if (cancelled) return
        setBooting(false)
        // A network or server problem says nothing about the session: keep the token and show what happened.
        if (!(e instanceof ApiError) || e.status === 0 || e.status >= 500) {
          setNotice(errText(e))
          return
        }
        clearSession()
        setNotice(SESSION_ENDED)
      },
    )
    return () => {
      cancelled = true
    }
  }, [])

  function signIn(next: AuthUser, token: string) {
    try {
      localStorage.setItem(TOKEN_KEY, token)
      localStorage.removeItem('pa.lastBot')
      localStorage.removeItem('pa.lastGroup')
    } catch {
      /* private mode: the session lasts until reload */
    }
    setAuthRole(next.role)
    setNotice('')
    go('/', true)
    setUser(next)
  }

  async function signOut() {
    try {
      await api.auth.logout()
    } catch {
      /* the server ack is best-effort: the local session is cleared anyway */
    }
    clearSession()
    setNotice('')
    go('/', true)
    setUser(null)
  }

  if (booting) {
    return (
      <main
        role="status"
        aria-live="polite"
        style={{
          minHeight: '100svh',
          display: 'grid',
          placeItems: 'center',
          padding: 24,
          background: 'var(--ground)',
          color: 'var(--muted)',
          textAlign: 'center',
        }}
      >
        <div>
          <Mark />
          <p style={{ marginTop: 12, fontSize: 14 }}>Menyiapkan ruang kerja Anda…</p>
        </div>
      </main>
    )
  }
  if (!user) return <LoginModal notice={notice} onSuccess={signIn} />
  return (
    <DataProvider key={user.id}>
      <Shell authUser={user} onLogout={signOut} />
    </DataProvider>
  )
}

// Colorbox as a box: three flat faces (top, ink, the one blue).
function Mark() {
  return (
    <svg className="mark" viewBox="0 0 32 32" width="26" height="26" aria-hidden="true">
      <path d="M16 3 28 9.500 16 16 4 9.500z" fill="var(--control)" />
      <path d="M4 9.500 16 16v13L4 22.500z" fill="var(--text)" />
      <path d="M28 9.500 16 16v13l12-6.500z" fill="var(--accent)" />
    </svg>
  )
}

function Shell({ authUser, onLogout }: { authUser: AuthUser; onLogout: () => void | Promise<void> }) {
  const route = useRoute()
  const { conn, toasts, dismissToast, notifyAsk, answerNotify, dialog } = useData()
  const [drawer, setDrawer] = useState(false)
  const isAdmin = useIsAdmin()

  useEffect(() => setDrawer(false), [route])

  // The menu warms the page chunk while the pointer or focus is still on the link, so the click
  // lands on content. Marketing, CS and Evaluasi are admin-only and stay cold.
  useEffect(() => {
    onLinkIntent('a[href="#/aplikasi"]', () => void import('./connections'))
    onLinkIntent('a[href="#/kanban"]', () => void import('./Kanban'))
    onLinkIntent('a[href="#/pengaturan"]', () => void import('./Settings'))
    onLinkIntent('a[href="#/pengetahuan"]', () => void import('./Pengetahuan'))
    onLinkIntent('a[href="#/agen"]', () => void import('./Agents'))
    onLinkIntent('a[href="#/output"]', () => void import('./Output'))
    onLinkIntent('a[href="#/pelanggan"]', () => void import('./Pelanggan'))
  }, [])

  // After Beranda has painted, fill idle time with the two screens a day usually starts with.
  const warmed = useRef(false)
  useEffect(() => {
    if (route.name !== 'home' || warmed.current) return
    const warm = () => {
      warmed.current = true
      void import('./Kanban')
      void import('./Settings')
    }
    if (typeof window.requestIdleCallback === 'function') {
      const id = window.requestIdleCallback(warm, { timeout: 4000 })
      return () => window.cancelIdleCallback(id)
    }
    const id = window.setTimeout(warm, 2000)
    return () => window.clearTimeout(id)
  }, [route.name])

  // A member who reaches an admin route (old link, typed hash, restored tab) goes back to Beranda.
  useEffect(() => {
    if (!isAdmin && ADMIN_ROUTES[route.name]) go('/', true)
  }, [route.name, isAdmin])

  // Phone drawer: focus moves into it when it opens; Escape closes it and gives focus back to the menu button.
  const menuBtn = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (!drawer) return
    document.querySelector<HTMLElement>('.side a[href], .side button')?.focus()
    const esc = (e: KeyboardEvent) => {
      if (e.key !== 'Escape' || e.defaultPrevented) return
      setDrawer(false)
      menuBtn.current?.focus()
    }
    document.addEventListener('keydown', esc)
    return () => document.removeEventListener('keydown', esc)
  }, [drawer])

  return (
    <div className="app" data-drawer={drawer || undefined}>
      <a
        className="skip-link"
        href="#isi"
        onClick={(e) => {
          e.preventDefault() // the hash is the router: a real #isi jump would leave the page
          document.getElementById('isi')?.focus()
        }}
      >
        Lewati ke isi halaman
      </a>
      <header className="mbar">
        <button ref={menuBtn} className="icon-btn" aria-label="Buka menu" onClick={() => setDrawer(true)}>
          <Icon d={MENU} size={20} />
        </button>
        <span className="brand">
          <Mark />
          Pegawai AI
        </span>
        <RunsPill />
      </header>
      <Sidebar route={route} authUser={authUser} onLogout={onLogout} onClose={() => setDrawer(false)} />
      {drawer && <button className="scrim" aria-label="Tutup menu" onClick={() => setDrawer(false)} />}

      <main className="stage" id="isi" tabIndex={-1}>
        {conn === 'retry' && (
          <p className="conn-bar" role="status">
            <span className="dots" aria-hidden="true" />
            Menyambung ulang…
          </p>
        )}
        <RouteBoundary resetKey={route.name}>
          <Suspense fallback={pageFallback}>
            {(route.name === 'bot' || route.name === 'chat') && <ChatLayout route={route} />}
            {(route.name === 'grup' || route.name === 'grup-list') && <GroupLayout route={route} />}
            {isAdmin && route.name === 'aktivitas' && <Activity />}
            {route.name === 'kanban' && <Kanban />}
            {route.name === 'home' && <Dashboard />}
            {isAdmin && route.name === 'agen' && <AgentList />}
            {isAdmin && route.name === 'agen-baru' && <AgentNew />}
            {isAdmin && route.name === 'agen-detail' && <AgentDetail key={route.id} id={route.id} />}
            {isAdmin && route.name === 'agen-ubah' && <AgentEdit key={route.id} id={route.id} />}
            {isAdmin && (route.name === 'tools' || route.name === 'computer-use') && <Kemampuan tab={route.name} />}
            {route.name === 'aplikasi' && <AppsPage />}
            {route.name === 'pengetahuan' && <Pengetahuan />}
            {isAdmin && route.name === 'marketing' && <Marketing />}
            {isAdmin && route.name === 'cs' && <CS />}
            {isAdmin && route.name === 'uji' && <Uji />}
            {route.name === 'pengaturan' && <Settings section={route.section} />}
            {route.name === 'output' && <Output />}
            {route.name === 'pelanggan' && <Pelanggan id={route.id} />}
            {isAdmin && route.name === 'mulai' && <Mulai />}
          </Suspense>
        </RouteBoundary>
      </main>

      <div className="toasts" aria-live="polite">
        {notifyAsk && (
          <div className="toast toast-ask">
            <p>Mau diberi tahu saat pegawai selesai bekerja, walau tab ini tidak dibuka?</p>
            <div className="toast-actions">
              <button className="btn primary" onClick={() => answerNotify(true)}>
                Aktifkan
              </button>
              <button className="btn quiet-btn" onClick={() => answerNotify(false)}>
                Nanti
              </button>
            </div>
          </div>
        )}
        {toasts.map((t) => (
          <div key={t.id} className="toast">
            <button
              className="toast-main"
              onClick={() => {
                dismissToast(t.id)
                if (t.href) go(t.href)
              }}
            >
              {t.text}
            </button>
            <button className="icon-btn" aria-label="Tutup" onClick={() => dismissToast(t.id)}>
              <Icon d={CLOSE} size={14} />
            </button>
          </div>
        ))}
      </div>
      {dialog && (
        <RouteBoundary>
          <Suspense fallback={null}>
            <Dialogs />
          </Suspense>
        </RouteBoundary>
      )}
    </div>
  )
}

// ---------- sidebar ----------
// The main group for everyone (Pelanggan only when a customer-service employee exists or the handover queue
// is readable); the Admin group (developer and QA screens) belongs to admin roles and can be decluttered with
// the Mode admin switch. Members are redirected away from those routes in Shell.
function Sidebar({ route, authUser, onLogout, onClose }: { route: Route; authUser: AuthUser | null; onLogout: () => void; onClose: () => void }) {
  const { settings, bots } = useData()
  // The Sidebar is where the Pelanggan entry is decided. With a CS employee on the list the queue also feeds
  // the badge, so it polls; without one the entry is hidden and the first read is only a probe: if the endpoint
  // answers (a staff member may not see the employees they hand over to) the entry appears and polling starts,
  // and if it does not exist it is not asked again this session.
  const hasCs = bots.some(canWhatsApp)
  const hv = useHandoverQueue(hasCs)
  const showPelanggan = hasCs || hv.ready
  const admin = useAdminMode()
  const waiting = useActions().filter((a) => a.status === 'pending').length // risky agent actions (delete a file, send an email) waiting for the user
  return (
    <aside className="side" aria-label="Menu utama">
      <div className="side-top">
        <span className="brand">
          <Mark />
          <span className="brand-text">
            Pegawai AI
            <small>{settings.company_name}</small>
          </span>
        </span>
        <button className="icon-btn close-drawer" aria-label="Tutup menu" onClick={onClose}>
          <Icon d={CLOSE} />
        </button>
      </div>

      <nav className="side-scroll" aria-label="Halaman">
        <NavGroup>
          <NavItem href="#/" icon={I.home} current={route.name === 'home'} badge={waiting}>
            Beranda
          </NavItem>
          <NavItem href="#/grup" icon={I.group} current={route.name === 'grup-list' || route.name === 'grup'}>
            Tim
          </NavItem>
          <NavItem href="#/chat" icon={I.chat} current={route.name === 'chat' || route.name === 'bot'}>
            Chat
          </NavItem>
          {showPelanggan && (
            <NavItem href="#/pelanggan" icon={I.support} current={route.name === 'pelanggan'} badge={hv.counts.needs_human} badgeLabel="pelanggan menunggu manusia">
              Pelanggan
            </NavItem>
          )}
          <NavItem href="#/kanban" icon={I.board} current={route.name === 'kanban'}>
            Jadwal &amp; tugas
          </NavItem>
          <NavItem href="#/output" icon={I.output} current={route.name === 'output'}>
            Output
          </NavItem>
          <NavItem href="#/pengetahuan" icon={I.book} current={route.name === 'pengetahuan'}>
            Pengetahuan
          </NavItem>
          <NavItem href="#/aplikasi" icon={I.apps} current={route.name === 'aplikasi'}>
            Aplikasi
          </NavItem>
          <NavItem href="#/pengaturan" icon={I.settings} current={route.name === 'pengaturan'}>
            Pengaturan
          </NavItem>
        </NavGroup>

        {admin && (
          <NavGroup label="Admin">
            <NavItem href="#/marketing" team="marketing" icon={I.marketing} current={route.name === 'marketing'}>
              Marketing (formulir)
            </NavItem>
            <NavItem href="#/cs" team="customer_support" icon={I.support} current={route.name === 'cs'}>
              Layanan pelanggan
            </NavItem>
            <NavItem href="#/agen" icon={I.agent} current={route.name.startsWith('agen')}>
              Agen
            </NavItem>
            <NavItem href="#/tools" icon={I.skills} current={route.name === 'tools' || route.name === 'computer-use'}>
              Kemampuan
            </NavItem>
            <NavItem href="#/uji" icon={I.test} current={route.name === 'uji'}>
              Evaluasi
            </NavItem>
            <NavItem href="#/aktivitas" icon={I.log} current={route.name === 'aktivitas'}>
              Aktivitas
            </NavItem>
          </NavGroup>
        )}
      </nav>

      <footer className="side-foot">
        {authUser && (
          <div className="side-user">
            <div className="side-user-who">
              <b
                title={authUser.name}
                style={{
                  display: '-webkit-box',
                  WebkitBoxOrient: 'vertical',
                  WebkitLineClamp: 2,
                  whiteSpace: 'normal',
                  overflow: 'hidden',
                  overflowWrap: 'anywhere',
                  maxWidth: 160,
                }}
              >
                {authUser.name}
              </b>
              <small>{isAdminRole(authUser.role) ? 'Pemilik' : 'Staf'}{authUser.company ? ` · ${authUser.company}` : ''}</small>
            </div>
            <button type="button" className="btn quiet-btn sm side-user-out" onClick={onLogout} title="Keluar dari akun">
              Keluar
            </button>
          </div>
        )}
        <div className="runs-slot">
          <RunsPill />
        </div>
      </footer>
    </aside>
  )
}

function NavItem({ href, icon, current, team, badge, badgeLabel, children }: { href: string; icon: string; current: boolean; team?: string; badge?: number; badgeLabel?: string; children: React.ReactNode }) {
  return (
    <a className="nav-link" data-team={team} href={href} aria-current={current ? 'page' : undefined}>
      <Icon d={icon} size={16} />
      {children}
      {!!badge && (
        <span className="nav-badge" aria-label={`${badge} ${badgeLabel ?? 'menunggu persetujuan'}`}>
          {badge}
        </span>
      )}
    </a>
  )
}

function NavGroup({ label, children }: { label?: string; children: React.ReactNode }) {
  const id = 'ng-' + (label ?? 'utama').toLowerCase()
  return (
    <section className="nav-group" aria-labelledby={id}>
      <h2 id={id} className={label ? undefined : 'sr'}>
        {label ?? 'Menu'}
      </h2>
      <div className="group-body">{children}</div>
    </section>
  )
}

// ---------- active runs ----------
function RunsPill() {
  const { runs, bots } = useData()
  const [open, setOpen] = useState(false)
  const [now, setNow] = useState(Date.now())
  const [problem, setProblem] = useState('')
  const box = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    setNow(Date.now())
    const t = window.setInterval(() => setNow(Date.now()), 1000)
    const away = (e: MouseEvent) => {
      if (!box.current?.contains(e.target as Node)) setOpen(false)
    }
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', away)
    document.addEventListener('keydown', esc)
    return () => {
      window.clearInterval(t)
      document.removeEventListener('mousedown', away)
      document.removeEventListener('keydown', esc)
    }
  }, [open])

  async function stop(id: string) {
    setProblem('')
    try {
      await api.stopRun(id)
    } catch (e) {
      setProblem(errText(e))
    }
  }

  return (
    <div className="runs" ref={box}>
      <button className="runs-pill" data-busy={runs.length > 0 || undefined} aria-expanded={open} onClick={() => setOpen(!open)}>
        <span className="status-dot" data-s={runs.length ? 'working' : 'idle'} aria-hidden="true" />
        Sedang dikerjakan
        <b className="num">{runs.length}</b>
      </button>
      {open && (
        <div className="runs-pop" role="dialog" aria-label="Tugas yang sedang berjalan">
          {runs.length === 0 && <p className="quiet pad">Tidak ada tugas yang berjalan.</p>}
          {problem && <p className="problem-bar small">{problem}</p>}
          <ul>
            {runs.map((r) => {
              const b = bots.find((x) => x.id === r.bot_id)
              const o = r.origin
              const href = r.group_id ? groupPath(r.group_id) : o.type === 'evaluasi' ? `/uji${o.case_id ? `?case=${encodeURIComponent(o.case_id)}` : ''}` : o.type === 'cs' ? '/cs' : o.type === 'marketing' ? '/marketing' : botPath(r.bot_id, r.session_id)
              const where = o.type === 'evaluasi' ? ['Evaluasi', o.case_id, o.of > 1 ? `giliran ${o.turn} dari ${o.of}` : ''].filter(Boolean).join(' · ') : o.type === 'cs' ? 'Layanan pelanggan' : o.type === 'marketing' ? 'Marketing' : ''
              return (
                <li key={r.id} className="run-row">
                  <BotAvatar bot={b ?? { name: r.bot_name || '?', color: '' }} size={28} />
                  <a className="run-text" href={'#' + href} onClick={() => setOpen(false)}>
                    <b>{r.bot_name || b?.name || r.bot_id}</b>
                    {where && <small className="run-where">{where}</small>}
                    <small>{r.input || 'Tanpa keterangan'}</small>
                    <small className="num">{r.started_at ? elapsed(r.started_at, now) : ''}</small>
                  </a>
                  <button className="btn quiet-btn stop-sm" onClick={() => void stop(r.id)}>
                    Stop
                  </button>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}
