import { useCallback, useEffect, useRef, useState } from 'react'
import { api, errText, isAbort } from './bff'
import type { Bot, Session } from './bff'
import Chat from './Chat'
import { useData } from './data'
import GroupChat from './Group'
import { botPath, go, groupPath } from './router'
import type { Route } from './router'
import { BotAvatar, CLOSE, DOTS, ErrorLine, Icon, PENCIL, PLUS, TRASH, ago, botColor, teamLabel } from './ui'
import { PageState, statusText } from './ui-extra'

// Chat and Grup: a left column with the list (agents by team, or groups) and the conversation on the right.
// Under 900 px the column is the page itself until something is chosen; after that it opens as a sheet from the header.
const WIDE = '(min-width: 901px)'
const remember = (key: string, id?: string) => {
  try {
    if (id) localStorage.setItem(key, id)
    return localStorage.getItem(key) ?? ''
  } catch {
    return ''
  }
}

const titleOf = (s: Session) => s.title || s.preview.replace(/\.{3}$/, '') || 'Topik tanpa judul'

// The session list of the open bot: both the rail and the chat use it.
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
type Hist = ReturnType<typeof useSessions>

function Rail({ label, title, action, open, onClose, children }: { label: string; title: string; action: React.ReactNode; open: boolean; onClose: () => void; children: React.ReactNode }) {
  return (
    <>
      <nav className="rail" aria-label={label} data-open={open || undefined}>
        <header className="rail-head">
          <h2>{title}</h2>
          {action}
          <button className="icon-btn close-rail" aria-label="Tutup daftar" onClick={onClose}>
            <Icon d={CLOSE} />
          </button>
        </header>
        <div className="rail-body">{children}</div>
      </nav>
      {open && <button className="scrim rail-scrim" aria-label="Tutup daftar" onClick={onClose} />}
    </>
  )
}

function Intro({ title, text, children }: { title: string; text: string; children?: React.ReactNode }) {
  return (
    <section className="page intro" aria-labelledby="intro-h">
      <div className="empty">
        <h1 id="intro-h">{title}</h1>
        <p>{text}</p>
        {children}
      </div>
    </section>
  )
}

export function ChatLayout({ route }: { route: Extract<Route, { name: 'bot' } | { name: 'chat' }> }) {
  const { bots, loadState, error, reload, setDialog } = useData()
  const botId = route.name === 'bot' ? route.id : undefined
  const sid = route.name === 'bot' ? route.sid : undefined
  const hist = useSessions(botId)
  const bot = bots.find((b) => b.id === botId)
  const [open, setOpen] = useState(false)
  const [menu, setMenu] = useState<string | null>(null)
  const teams = bots.reduce<Record<string, Bot[]>>((acc, b) => ((acc[b.team] ??= []).push(b), acc), {})

  useEffect(() => setOpen(false), [route])
  // On a wide screen "Chat" opens the agent you used last (or the first one); on a phone the list is the page.
  useEffect(() => {
    const last = remember('pa.lastBot', botId)
    if (route.name === 'chat' && loadState === 'ok' && window.matchMedia(WIDE).matches) {
      const target = bots.find((b) => b.id === last) ?? bots[0]
      if (target) go(botPath(target.id), true)
    }
  }, [route.name, botId, bots, loadState])
  useEffect(() => {
    if (!menu) return
    const off = () => setMenu(null)
    document.addEventListener('click', off)
    return () => document.removeEventListener('click', off)
  }, [menu])

  return (
    <div className="with-rail" data-picked={botId ? '' : undefined}>
      <Rail
        label="Agen dan riwayat chat"
        title="Agen"
        action={
          <a className="btn soft sm" href="#/agen/baru">
            Agen baru
          </a>
        }
        open={open}
        onClose={() => setOpen(false)}
      >
        {loadState === 'loading' && <p className="quiet pad">Memuat agen...</p>}
        {loadState === 'error' && bots.length === 0 && <ErrorLine text={error} onRetry={reload} />}
        {loadState === 'ok' && bots.length === 0 && <p className="quiet pad">Belum ada agen.</p>}
        {Object.entries(teams).map(([team, list]) => (
          <div key={team} className="bot-group">
            <h3>{teamLabel(team)}</h3>
            <ul>
              {list.map((b) => (
                <li key={b.id} className="bot-li">
                  <a className="row" href={'#' + botPath(b.id)} aria-current={botId === b.id ? 'page' : undefined} title={b.role} style={{ ['--bot' as string]: botColor(b) }}>
                    <BotAvatar bot={b} size={28} />
                    <span className="bot-text">
                      <b>{b.name}</b>
                      <small className="st">{b.status === 'idle' && !b.deleteError ? b.role : statusText(b)}</small>
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
        {bot && <History bot={bot} hist={hist} sid={sid} />}
      </Rail>

      <div className="rail-main">
        {route.name === 'bot' ? (
          bot ? (
            <Chat key={bot.id} bot={bot} sid={sid} sessions={hist.sessions} onSessions={() => hist.refresh(true)} onRail={() => setOpen(true)} />
          ) : (
            <PageState what="Agen" loadState={loadState} error={error} reload={reload} />
          )
        ) : (
          <Intro title="Chat" text="Tanya bebas ke satu agen. Pilih agen dari daftar.">
            <p className="quiet small">
              Butuh alur kerja? Buka{' '}
              <a className="empty-link" href="#/marketing">
                Marketing
              </a>{' '}
              atau{' '}
              <a className="empty-link" href="#/cs">
                Customer Service
              </a>
              .
            </p>
          </Intro>
        )}
      </div>
    </div>
  )
}

export function GroupLayout({ route }: { route: Extract<Route, { name: 'grup' } | { name: 'grup-list' }> }) {
  const { bots, groups, loadState, error, reload, setDialog } = useData()
  const gid = route.name === 'grup' ? route.id : undefined
  const [open, setOpen] = useState(false)
  useEffect(() => setOpen(false), [route])
  useEffect(() => {
    const last = remember('pa.lastGroup', gid)
    if (route.name === 'grup-list' && loadState === 'ok' && window.matchMedia(WIDE).matches) {
      const target = groups.find((g) => g.id === last) ?? groups[0]
      if (target) go(groupPath(target.id), true)
    }
  }, [route.name, gid, groups, loadState])

  return (
    <div className="with-rail" data-picked={gid ? '' : undefined}>
      <Rail
        label="Daftar grup"
        title="Grup"
        action={
          <button className="btn soft sm" onClick={() => setDialog({ kind: 'group' })}>
            Grup baru
          </button>
        }
        open={open}
        onClose={() => setOpen(false)}
      >
        {loadState === 'loading' && <p className="quiet pad">Memuat grup...</p>}
        {loadState === 'error' && groups.length === 0 && <ErrorLine text={error} onRetry={reload} />}
        {loadState === 'ok' && groups.length === 0 && <p className="quiet pad">Belum ada grup. Gabungkan 2 sampai 6 agen lewat Grup baru.</p>}
        <ul>
          {groups.map((g) => {
            const ms = g.members.map((m) => bots.find((b) => b.id === m)).filter((b): b is Bot => !!b)
            return (
              <li key={g.id}>
                <a className="row" href={'#' + groupPath(g.id)} aria-current={gid === g.id ? 'page' : undefined}>
                  <span className="avatar-stack" aria-hidden="true">
                    {ms.slice(0, 3).map((b) => (
                      <BotAvatar key={b.id} bot={b} size={24} />
                    ))}
                  </span>
                  <span className="bot-text">
                    <b>{g.name}</b>
                    <small className="st">{g.running ? 'Diskusi berjalan' : ms.map((b) => b.name).join(', ') || `${g.members.length} anggota`}</small>
                  </span>
                  {g.running && <span className="live-dot" role="img" aria-label="Diskusi berjalan" />}
                </a>
              </li>
            )
          })}
        </ul>
      </Rail>

      <div className="rail-main">
        {gid ? (
          <GroupChat key={gid} id={gid} onRail={() => setOpen(true)} />
        ) : (
          <Intro title="Grup" text="Beberapa agen berdiskusi dalam satu percakapan. Pilih grup dari daftar.">
            <button className="btn primary" onClick={() => setDialog({ kind: 'group' })}>
              Grup baru
            </button>
          </Intro>
        )}
      </div>
    </div>
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
    <section className="history" aria-label={`Riwayat chat ${bot.name}`}>
      <div className="sec-head">
        <h3>Riwayat {bot.name}</h3>
        <button className="btn soft sm" title="Mulai percakapan baru, riwayat lama tetap ada" onClick={() => go(botPath(bot.id))}>
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
      {state === 'error' && (
        <ErrorLine
          text={error}
          onRetry={() => {
            hist.setSessions([])
            refresh()
          }}
        />
      )}
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
