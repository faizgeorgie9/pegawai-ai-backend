import { useCallback, useEffect, useRef, useState } from 'react'
import Activity from './Activity'
import { AgentDetail, AgentEdit, AgentList, AgentNew } from './Agents'
import { api, errText, isAbort } from './bff'
import type { Bot, Session } from './bff'
import Chat from './Chat'
import Dashboard from './Dashboard'
import { DataProvider, useData } from './data'
import { Dialogs } from './Dialogs'
import GroupChat from './Group'
import { ComputerUse, Scheduler, Tools } from './Platform'
import CS from './CS'
import Marketing from './Marketing'
import Uji from './Uji'
import { botPath, go, groupPath, useRoute } from './router'
import type { Route } from './router'
import { BotAvatar, CLOSE, DOTS, ErrorLine, Icon, MENU, PENCIL, PLUS, TRASH, ago, botColor, elapsed, teamLabel } from './ui'
import { statusText } from './ui-extra'

export default function App() {
  return (
    <DataProvider>
      <Shell />
    </DataProvider>
  )
}

function Mark() {
  return (
    <svg className="mark" viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
      <circle cx="21.5" cy="11.5" r="4.5" fill="var(--accent-track)" />
      <path d="M13.5 28c.4-4.700 3.600-8 8-8s7.600 3.300 8 8z" fill="var(--accent-track)" />
      <circle cx="12" cy="10.500" r="5.500" fill="var(--accent)" />
      <path d="M2.500 28c0-5.500 4.300-9.500 9.500-9.500s9.500 4 9.500 9.500z" fill="var(--accent)" />
    </svg>
  )
}

const titleOf = (s: Session) => s.title || s.preview.replace(/\.{3}$/, '') || 'Topik tanpa judul'

// The session list of the open bot: owned by the shell because both the sidebar and the chat use it.
function useSessions(botId?: string) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [state, setState] = useState<'loading' | 'ok' | 'error'>('loading')
  const [error, setError] = useState('')
  const ctl = useRef<AbortController | null>(null)
  const refresh = useCallback(
    (quiet = false) => {
      if (!botId) return
      ctl.current?.abort()
      const c = (ctl.current = new AbortController())
      api.sessions(botId, c.signal).then(
        (l) => {
          setSessions(l)
          setState('ok')
        },
        (e) => {
          if (isAbort(e)) return
          if (!quiet) {
            setError(errText(e))
            setState('error')
          }
        },
      )
    },
    [botId],
  )
  useEffect(() => {
    setSessions([])
    setState('loading')
    refresh()
    return () => ctl.current?.abort()
  }, [refresh])
  return { sessions, state, error, refresh, setSessions }
}

function Shell() {
  const route = useRoute()
  const { bots, loadState, error, reload, conn, toasts, dismissToast, notifyAsk, answerNotify } = useData()
  const [drawer, setDrawer] = useState(false)
  const botId = route.name === 'bot' ? route.id : undefined
  const hist = useSessions(botId)
  const bot = bots.find((b) => b.id === botId)

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
      <Sidebar route={route} hist={hist} bot={bot} onClose={() => setDrawer(false)} />
      {drawer && <button className="scrim" aria-label="Tutup menu" onClick={() => setDrawer(false)} />}

      <main className="stage">
        {conn === 'retry' && (
          <p className="conn-bar" role="status">
            <span className="dots" aria-hidden="true" />
            Menyambung ulang…
          </p>
        )}
        {route.name === 'bot' &&
          (bot ? (
            <Chat key={bot.id} bot={bot} sid={route.sid} sessions={hist.sessions} onSessions={() => hist.refresh(true)} />
          ) : (
            <PageState what="Agen" loadState={loadState} error={error} reload={reload} />
          ))}
        {route.name === 'grup' && <GroupChat key={route.id} id={route.id} />}
        {route.name === 'aktivitas' && <Activity />}
        {route.name === 'home' && <Dashboard />}
        {route.name === 'agen' && <AgentList />}
        {route.name === 'agen-baru' && <AgentNew />}
        {route.name === 'agen-detail' && <AgentDetail key={route.id} id={route.id} />}
        {route.name === 'agen-ubah' && <AgentEdit key={route.id} id={route.id} />}
        {route.name === 'tools' && <Tools />}
        {route.name === 'computer-use' && <ComputerUse />}
        {route.name === 'scheduler' && <Scheduler />}
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

function PageState({ what, loadState, error, reload }: { what: string; loadState: string; error: string; reload: () => void }) {
  return (
    <section className="page center-page">
      {loadState === 'loading' ? <p className="quiet">Memuat...</p> : loadState === 'error' ? <ErrorLine text={error} onRetry={reload} /> : <p className="quiet">{what} tidak ditemukan. Mungkin sudah dihapus.</p>}
    </section>
  )
}

// ---------- sidebar ----------
type Hist = ReturnType<typeof useSessions>

function Sidebar({ route, hist, bot, onClose }: { route: Route; hist: Hist; bot?: Bot; onClose: () => void }) {
  const { bots, groups, loadState, error, reload, setDialog } = useData()
  const [menu, setMenu] = useState<string | null>(null)
  const teams = bots.reduce<Record<string, Bot[]>>((acc, b) => ((acc[b.team] ??= []).push(b), acc), {})

  useEffect(() => {
    if (!menu) return
    const off = () => setMenu(null)
    document.addEventListener('click', off)
    return () => document.removeEventListener('click', off)
  }, [menu])

  return (
    <aside className="side" aria-label="Menu utama">
      <div className="side-top">
        <span className="brand">
          <Mark />
          <span className="brand-text">
            Pegawai AI
            <small>AI Top Trends</small>
          </span>
        </span>
        <button className="icon-btn close-drawer" aria-label="Tutup menu" onClick={onClose}>
          <Icon d={CLOSE} />
        </button>
      </div>

      <div className="side-scroll">
        <nav className="side-sec nav-list" aria-label="Dashboard">
          <a className="nav-link" href="#/" aria-current={route.name === 'home' ? 'page' : undefined}>
            Dashboard
          </a>
        </nav>
        <section className="side-sec" aria-labelledby="sb">
          <div className="sec-head">
            <h2 id="sb">Chat</h2>
            <button className="btn new" onClick={() => go('/agen/baru')}>
              <Icon d={PLUS} />
              Agen baru
            </button>
          </div>
          {loadState === 'loading' && <p className="quiet pad">Memuat agen...</p>}
          {loadState === 'error' && bots.length === 0 && <ErrorLine text={error} onRetry={reload} />}
          {loadState === 'ok' && bots.length === 0 && <p className="quiet pad">Belum ada agen.</p>}
          {Object.entries(teams).map(([team, list]) => (
            <div key={team} className="bot-group">
              <h3>{teamLabel(team)}</h3>
              <ul>
                {list.map((b) => (
                  <li key={b.id} className="bot-li">
                    <a
                      className="row"
                      href={'#' + botPath(b.id)}
                      aria-current={route.name === 'bot' && route.id === b.id ? 'page' : undefined}
                      title={statusText(b)}
                      style={{ ['--bot' as string]: botColor(b) }}
                    >
                      <BotAvatar bot={b} size={32} />
                      <span className="bot-text">
                        <b>{b.name}</b>
                        <small>{b.role}</small>
                        <small className="st">{statusText(b)}</small>
                      </span>
                      <span className="status-dot" data-s={b.status} role="img" aria-label={b.status === 'idle' ? 'Siap' : b.status === 'working' ? 'Bekerja' : 'Berdiskusi'} />
                    </a>
                    {!b.builtin && (
                      <span className="row-menu">
                        <button
                          className="icon-btn"
                          aria-label={`Menu ${b.name}`}
                          aria-expanded={menu === b.id}
                          onClick={(e) => {
                            e.stopPropagation()
                            setMenu(menu === b.id ? null : b.id)
                          }}
                        >
                          <Icon d={DOTS} />
                        </button>
                        {menu === b.id && (
                          <div className="popmenu" role="menu">
                            <button role="menuitem" onClick={() => setDialog({ kind: 'delete', bot: b })}>
                              <Icon d={TRASH} />
                              Hapus agen
                            </button>
                          </div>
                        )}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </section>

        {bot && <History bot={bot} hist={hist} sid={route.name === 'bot' ? route.sid : undefined} />}
        <section className="side-sec" aria-labelledby="sg">
          <div className="sec-head">
            <h2 id="sg">Grup</h2>
            <button className="btn new" onClick={() => setDialog({ kind: 'group' })}>
              <Icon d={PLUS} />
              Grup baru
            </button>
          </div>
          {loadState === 'loading' && <p className="quiet pad">Memuat grup...</p>}
          {loadState === 'error' && groups.length === 0 && <ErrorLine text={error} onRetry={reload} />}
          {loadState === 'ok' && groups.length === 0 && <p className="quiet pad">Belum ada grup. Gabungkan 2 sampai 6 agen.</p>}
          <ul>
            {groups.map((g) => {
              const ms = g.members.map((m) => bots.find((b) => b.id === m)).filter((b): b is Bot => !!b)
              return (
                <li key={g.id}>
                  <a className="row" href={'#' + groupPath(g.id)} aria-current={route.name === 'grup' && route.id === g.id ? 'page' : undefined}>
                    <span className="avatar-stack" aria-hidden="true">
                      {ms.slice(0, 3).map((b) => (
                        <BotAvatar key={b.id} bot={b} size={24} />
                      ))}
                    </span>
                    <span className="bot-text">
                      <b>{g.name}</b>
                      <small>{g.running ? 'Diskusi berjalan' : `${g.members.length} anggota`}</small>
                    </span>
                    {g.running && <span className="live-dot" role="img" aria-label="Diskusi berjalan" />}
                  </a>
                </li>
              )
            })}
          </ul>
        </section>

        <nav className="side-sec nav-list" aria-label="Halaman">
          <a className="nav-link" href="#/agen" aria-current={route.name.startsWith('agen') ? 'page' : undefined}>
            Agen
          </a>
          <a className="nav-link" href="#/tools" aria-current={route.name === 'tools' ? 'page' : undefined}>
            Tools / Plugins
          </a>
          <a className="nav-link" href="#/computer-use" aria-current={route.name === 'computer-use' ? 'page' : undefined}>
            Computer Use <span className="nav-tag">Diblokir</span>
          </a>
          <a className="nav-link" href="#/scheduler" aria-current={route.name === 'scheduler' ? 'page' : undefined}>
            Scheduler <span className="nav-tag">Diblokir</span>
          </a>
          <a className="nav-link" href="#/marketing" aria-current={route.name === 'marketing' ? 'page' : undefined}>
            Workspace Marketing
          </a>
          <a className="nav-link" href="#/cs" aria-current={route.name === 'cs' ? 'page' : undefined}>
            Workspace CS
          </a>
          <a className="nav-link" href="#/uji" aria-current={route.name === 'uji' ? 'page' : undefined}>
            Skenario uji &amp; evaluasi
          </a>
          <a className="nav-link" href="#/aktivitas" aria-current={route.name === 'aktivitas' ? 'page' : undefined}>
            Aktivitas
          </a>
        </nav>
      </div>

      <footer className="side-foot">
        <div className="runs-slot">
          <RunsPill />
        </div>
      </footer>
    </aside>
  )
}

function History({ bot, hist, sid }: { bot: Bot; hist: Hist; sid?: string }) {
  const { sessions, state, error, refresh, setSessions } = hist
  const [problem, setProblem] = useState('')

  async function rename(s: Session, title: string) {
    const t = title.trim()
    if (!t || t === s.title) return
    const before = sessions
    setSessions((cur) => cur.map((x) => (x.id === s.id ? { ...x, title: t } : x)))
    try {
      await api.renameSession(bot.id, s.id, t)
    } catch (e) {
      setSessions(before)
      setProblem(errText(e))
    }
  }
  async function remove(s: Session) {
    try {
      await api.deleteSession(bot.id, s.id)
      setSessions((cur) => cur.filter((x) => x.id !== s.id))
      if (s.id === sid) go(botPath(bot.id))
    } catch (e) {
      setProblem(errText(e))
    }
  }

  return (
    <section className="side-sec history" aria-label={`Riwayat chat ${bot.name}`}>
      <div className="sec-head">
        <h2>Riwayat {bot.name}</h2>
        <button className="btn new" title="Mulai percakapan baru, riwayat lama tetap ada" onClick={() => go(botPath(bot.id))}>
          <Icon d={PLUS} />
          Topik baru
        </button>
      </div>
      {problem && (
        <p className="problem-bar small" role="alert">
          {problem}
        </p>
      )}
      {state === 'loading' && <p className="quiet pad">Memuat riwayat...</p>}
      {state === 'error' && <ErrorLine text={error} onRetry={() => { hist.setSessions([]); refresh() }} />}
      {state === 'ok' && sessions.length === 0 && <p className="quiet pad">Belum ada percakapan dengan {bot.name}.</p>}
      <ul>
        {sessions.map((s) => (
          <SessionRow key={s.id} botId={bot.id} s={s} current={s.id === sid} onRename={(t) => void rename(s, t)} onDelete={() => void remove(s)} />
        ))}
      </ul>
    </section>
  )
}

function SessionRow(p: { botId: string; s: Session; current: boolean; onRename: (t: string) => void; onDelete: () => void }) {
  const [mode, setMode] = useState<'view' | 'edit' | 'confirm'>('view')
  const [name, setName] = useState('')
  const title = titleOf(p.s)
  if (mode === 'edit') {
    return (
      <li className="sess editing">
        <input
          className="rename"
          autoFocus
          value={name}
          maxLength={80}
          aria-label="Judul baru"
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              p.onRename(name)
              setMode('view')
            } else if (e.key === 'Escape') setMode('view')
          }}
          onBlur={() => {
            p.onRename(name)
            setMode('view')
          }}
        />
      </li>
    )
  }
  if (mode === 'confirm') {
    return (
      <li className="sess confirm" role="alert">
        <span>Hapus &ldquo;{title}&rdquo;?</span>
        <span className="confirm-actions">
          <button
            className="btn danger"
            onClick={() => {
              setMode('view')
              p.onDelete()
            }}
          >
            Hapus
          </button>
          <button className="btn quiet-btn" onClick={() => setMode('view')}>
            Batal
          </button>
        </span>
      </li>
    )
  }
  return (
    <li className="sess" aria-current={p.current ? 'true' : undefined}>
      <a className="sess-main" href={'#' + botPath(p.botId, p.s.id)}>
        <span className="sess-title">{title}</span>
        <span className="sess-time">{ago(p.s.lastActive)}</span>
      </a>
      <span className="sess-actions">
        <button
          className="icon-btn"
          aria-label={`Ubah judul ${title}`}
          onClick={() => {
            setName(title)
            setMode('edit')
          }}
        >
          <Icon d={PENCIL} />
        </button>
        <button className="icon-btn" aria-label={`Hapus ${title}`} onClick={() => setMode('confirm')}>
          <Icon d={TRASH} />
        </button>
      </span>
    </li>
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
