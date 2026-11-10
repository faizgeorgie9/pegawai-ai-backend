import { useEffect, useRef, useState } from 'react'
import Activity from './Activity'
import { AgentDetail, AgentEdit, AgentList, AgentNew } from './Agents'
import { api, errText } from './bff'
import { ChatLayout, GroupLayout } from './ChatLayout'
import Dashboard from './Dashboard'
import { DataProvider, useData } from './data'
import { Dialogs } from './Dialogs'
import { Kemampuan } from './Platform'
import CS from './CS'
import Marketing from './Marketing'
import Uji from './Uji'
import { botPath, go, groupPath, useRoute } from './router'
import type { Route } from './router'
import { BotAvatar, CLOSE, I, Icon, MENU, elapsed } from './ui'

export default function App() {
  return (
    <DataProvider>
      <Shell />
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

function Shell() {
  const route = useRoute()
  const { conn, toasts, dismissToast, notifyAsk, answerNotify } = useData()
  const [drawer, setDrawer] = useState(false)

  useEffect(() => setDrawer(false), [route])

  return (
    <div className="app" data-drawer={drawer || undefined}>
      <header className="mbar">
        <button className="icon-btn" aria-label="Buka menu" onClick={() => setDrawer(true)}>
          <Icon d={MENU} size={20} />
        </button>
        <span className="brand">
          <Mark />
          Pegawai AI
        </span>
        <RunsPill />
      </header>
      <Sidebar route={route} onClose={() => setDrawer(false)} />
      {drawer && <button className="scrim" aria-label="Tutup menu" onClick={() => setDrawer(false)} />}

      <main className="stage">
        {conn === 'retry' && (
          <p className="conn-bar" role="status">
            <span className="dots" aria-hidden="true" />
            Menyambung ulang…
          </p>
        )}
        {(route.name === 'bot' || route.name === 'chat') && <ChatLayout route={route} />}
        {(route.name === 'grup' || route.name === 'grup-list') && <GroupLayout route={route} />}
        {route.name === 'aktivitas' && <Activity />}
        {route.name === 'home' && <Dashboard />}
        {route.name === 'agen' && <AgentList />}
        {route.name === 'agen-baru' && <AgentNew />}
        {route.name === 'agen-detail' && <AgentDetail key={route.id} id={route.id} />}
        {route.name === 'agen-ubah' && <AgentEdit key={route.id} id={route.id} />}
        {(route.name === 'tools' || route.name === 'computer-use' || route.name === 'scheduler') && <Kemampuan tab={route.name} />}
        {route.name === 'marketing' && <Marketing />}
        {route.name === 'cs' && <CS />}
        {route.name === 'uji' && <Uji />}
      </main>

      <div className="toasts" aria-live="polite">
        {notifyAsk && (
          <div className="toast ask">
            <p>Mau diberi tahu saat bot selesai, walau tab ini tidak dibuka?</p>
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
// Nine places in three groups. The agent and group lists live on the Chat and Grup pages, not here.
function Sidebar({ route, onClose }: { route: Route; onClose: () => void }) {
  return (
    <aside className="side" aria-label="Menu utama">
      <div className="side-top">
        <span className="brand">
          <Mark />
          <span className="brand-text">
            Pegawai AI
            <small>Colorbox</small>
          </span>
        </span>
        <button className="icon-btn close-drawer" aria-label="Tutup menu" onClick={onClose}>
          <Icon d={CLOSE} />
        </button>
      </div>

      <nav className="side-scroll" aria-label="Halaman">
        <NavGroup label="Kerja">
          <NavItem href="#/" icon={I.home} current={route.name === 'home'}>
            Beranda
          </NavItem>
          <NavItem href="#/chat" icon={I.chat} current={route.name === 'chat' || route.name === 'bot'}>
            Chat
          </NavItem>
          <NavItem href="#/grup" icon={I.group} current={route.name === 'grup-list' || route.name === 'grup'}>
            Grup
          </NavItem>
          <NavItem href="#/marketing" icon={I.marketing} current={route.name === 'marketing'}>
            Marketing
          </NavItem>
          <NavItem href="#/cs" icon={I.support} current={route.name === 'cs'}>
            Customer Service
          </NavItem>
        </NavGroup>

        <NavGroup label="Pengujian">
          <NavItem href="#/uji" icon={I.test} current={route.name === 'uji'}>
            Evaluasi
          </NavItem>
          <NavItem href="#/aktivitas" icon={I.log} current={route.name === 'aktivitas'}>
            Log aktivitas
          </NavItem>
        </NavGroup>

        <NavGroup label="Pengaturan">
          <NavItem href="#/agen" icon={I.agent} current={route.name.startsWith('agen')}>
            Agen
          </NavItem>
          <NavItem href="#/tools" icon={I.skills} current={route.name === 'tools' || route.name === 'computer-use' || route.name === 'scheduler'}>
            Kemampuan
          </NavItem>
        </NavGroup>
      </nav>

      <footer className="side-foot">
        <div className="runs-slot">
          <RunsPill />
        </div>
        <ThemeToggle />
      </footer>
    </aside>
  )
}

function NavItem({ href, icon, current, children }: { href: string; icon: string; current: boolean; children: React.ReactNode }) {
  return (
    <a className="nav-link" href={href} aria-current={current ? 'page' : undefined}>
      <Icon d={icon} size={16} />
      {children}
    </a>
  )
}

function NavGroup({ label, children }: { label: string; children: React.ReactNode }) {
  const id = 'ng-' + label.toLowerCase()
  return (
    <section className="nav-group" aria-labelledby={id}>
      <h2 id={id}>{label}</h2>
      <div className="group-body">{children}</div>
    </section>
  )
}

// Light is the default. Dark is a choice, remembered when storage works.
function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.dataset.theme === 'dark')
  function toggle() {
    const v = !dark
    setDark(v)
    if (v) document.documentElement.dataset.theme = 'dark'
    else delete document.documentElement.dataset.theme
    try {
      localStorage.setItem('pa.theme', v ? 'dark' : 'light')
    } catch {
      /* not remembered */
    }
  }
  return (
    <button className="theme-btn" onClick={toggle}>
      {dark ? 'Pakai tema terang' : 'Pakai tema gelap'}
    </button>
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
              const href = r.group_id ? groupPath(r.group_id) : botPath(r.bot_id, r.session_id)
              return (
                <li key={r.id} className="run-row">
                  <BotAvatar bot={b ?? { name: r.bot_name || '?', color: '' }} size={28} />
                  <a className="run-text" href={'#' + href} onClick={() => setOpen(false)}>
                    <b>{r.bot_name || b?.name || r.bot_id}</b>
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
