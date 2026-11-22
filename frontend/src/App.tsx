import { useEffect, useRef, useState } from 'react'
import Activity from './Activity'
import { useActions } from './ActionCard'
import { AgentDetail, AgentEdit, AgentList, AgentNew } from './Agents'
import { useAdminMode } from './adminMode'
import { ApiError, api, errText, isKeyError, onSessionEnd } from './bff'
import type { AuthUser } from './bff'
import { ChatLayout, GroupLayout } from './ChatLayout'
import Dashboard from './Dashboard'
import Kanban from './Kanban'
import { DataProvider, useData } from './data'
import { Dialogs } from './Dialogs'
import { Kemampuan } from './Platform'
import { AppsPage } from './connections'
import CS from './CS'
import { LoginModal } from './LoginModal'
import Marketing from './Marketing'
import Pengetahuan from './Pengetahuan'
import Settings from './Settings'
import Uji from './Uji'
import { botPath, go, groupPath, useRoute } from './router'
import type { Route } from './router'
import { BotAvatar, CLOSE, I, Icon, MENU, elapsed } from './ui'

const TOKEN_KEY = 'pegawai_ai_token'
const SESSION_ENDED = 'Sesi Anda berakhir, silakan masuk lagi.'

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
    localStorage.removeItem('pa.lastBot')
    localStorage.removeItem('pa.lastGroup')
  } catch {
    /* private mode: nothing persisted */
  }
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
        setUser(res.user)
        setBooting(false)
      },
      (e) => {
        if (cancelled) return
        setBooting(false)
        // A key, network or server problem says nothing about the session: keep the token and show what happened.
        if (!(e instanceof ApiError) || e.status === 0 || e.status >= 500 || isKeyError(e)) {
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
  const { conn, toasts, dismissToast, notifyAsk, answerNotify } = useData()
  const [drawer, setDrawer] = useState(false)

  useEffect(() => setDrawer(false), [route])

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
        {(route.name === 'bot' || route.name === 'chat') && <ChatLayout route={route} />}
        {(route.name === 'grup' || route.name === 'grup-list') && <GroupLayout route={route} />}
        {route.name === 'aktivitas' && <Activity />}
        {route.name === 'kanban' && <Kanban />}
        {route.name === 'home' && <Dashboard />}
        {route.name === 'agen' && <AgentList />}
        {route.name === 'agen-baru' && <AgentNew />}
        {route.name === 'agen-detail' && <AgentDetail key={route.id} id={route.id} />}
        {route.name === 'agen-ubah' && <AgentEdit key={route.id} id={route.id} />}
        {(route.name === 'tools' || route.name === 'computer-use') && <Kemampuan tab={route.name} />}
        {route.name === 'aplikasi' && <AppsPage />}
        {route.name === 'pengetahuan' && <Pengetahuan />}
        {route.name === 'marketing' && <Marketing />}
        {route.name === 'cs' && <CS />}
        {route.name === 'uji' && <Uji />}
        {route.name === 'pengaturan' && <Settings section={route.section} />}
      </main>

      <div className="toasts" aria-live="polite">
        {notifyAsk && (
          <div className="toast ask">
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
      <Dialogs />
    </div>
  )
}

// ---------- sidebar ----------
// Seven items for everyone; the Admin group (developer and QA screens) shows with admin mode. Admin routes open either way.
function Sidebar({ route, authUser, onLogout, onClose }: { route: Route; authUser: AuthUser | null; onLogout: () => void; onClose: () => void }) {
  const { settings } = useData()
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
          <NavItem href="#/kanban" icon={I.board} current={route.name === 'kanban'}>
            Jadwal &amp; tugas
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
              <b>{authUser.name}</b>
              <small>{/^(owner|admin|super_?admin)$/i.test(authUser.role) ? 'Pemilik' : 'Staf'}{authUser.company ? ` · ${authUser.company}` : ''}</small>
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

function NavItem({ href, icon, current, team, badge, children }: { href: string; icon: string; current: boolean; team?: string; badge?: number; children: React.ReactNode }) {
  return (
    <a className="nav-link" data-team={team} href={href} aria-current={current ? 'page' : undefined}>
      <Icon d={icon} size={16} />
      {children}
      {!!badge && (
        <span className="nav-badge" aria-label={`${badge} menunggu persetujuan`}>
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
