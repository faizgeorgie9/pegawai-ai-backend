import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react'
import type { ReactNode } from 'react'
import Activity from './Activity'
import { api, errText } from './bff'
import type { Bot, Group, Scope, Usage } from './bff'
import { useData } from './data'
import { go } from './router'
import { BotAvatar, CLOSE, DOTS, ErrorLine, Icon, botColor, clock, nf, teamLabel } from './ui'
import './panel.css'

// Side panel of a conversation (spec-panel-samping): Berpikir, Token, Aktivitas, Info. The open tab and the width
// live in a tiny module store (shared by bot chat and group chat) and are remembered in localStorage.
export type Tab = 'token' | 'aktivitas' | 'info'
const KEY = 'pegawai.panel'
const MIN_W = 300
const MAX_W = 560
const clampW = (w: number) => Math.min(MAX_W, Math.max(MIN_W, Math.round(w)))

interface PS {
  tab: Tab | null
  width: number
  focus: { run: string; n: number } | null // a turn the Berpikir tab should scroll to
}
function load(): PS {
  const base: PS = { tab: null, width: 360, focus: null }
  try {
    const j = JSON.parse(localStorage.getItem(KEY) ?? '{}') as { tab?: unknown; width?: unknown }
    // the panel always starts closed; only the width is remembered
    if (typeof j.width === 'number') base.width = clampW(j.width)
  } catch {
    /* private mode or bad JSON: defaults */
  }
  return base
}
let state = load()
const subs = new Set<() => void>()
function patch(p: Partial<PS>) {
  state = { ...state, ...p }
  subs.forEach((f) => f())
  try {
    localStorage.setItem(KEY, JSON.stringify({ tab: state.tab, width: state.width }))
  } catch {
    /* private mode: remembered for this visit only */
  }
}
const subscribe = (f: () => void) => (subs.add(f), () => void subs.delete(f))
export const usePanel = () => useSyncExternalStore(subscribe, () => state)
export const closePanel = () => patch({ tab: null })

const ICONS: Record<Tab, string> = {
  token: 'M4.5 17a8 8 0 0115 0M12 17l3.5-5',
  aktivitas: 'M3 12h4l3-8 4 16 3-8h4',
  info: 'M12 21a9 9 0 100-18 9 9 0 000 18zM12 11v5M12 8h.01',
}
const GROUP_INFO = 'M16 20v-1a4 4 0 00-4-4H8a4 4 0 00-4 4v1M10 11a3.5 3.5 0 100-7 3.5 3.5 0 000 7zM20 20v-1a3.5 3.5 0 00-2.5-3.4M15.5 4.3a3.5 3.5 0 010 6.4'
const LABEL: Record<Tab, string> = { token: 'Token', aktivitas: 'Aktivitas', info: 'Info' }
const TABS: Tab[] = ['token', 'aktivitas', 'info']

// Toolbar in the conversation header: the active icon is highlighted, clicking it again closes the panel.
export function PanelButtons({ group }: { group?: boolean }) {
  const { tab } = usePanel()
  const [menu, setMenu] = useState(false)
  const box = useRef<HTMLSpanElement>(null)
  useEffect(() => {
    if (!menu) return
    const away = (e: MouseEvent) => !box.current?.contains(e.target as Node) && setMenu(false)
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && setMenu(false)
    document.addEventListener('mousedown', away)
    document.addEventListener('keydown', esc)
    return () => {
      document.removeEventListener('mousedown', away)
      document.removeEventListener('keydown', esc)
    }
  }, [menu])
  return (
    <div className="ptools" role="toolbar" aria-label="Panel samping">
      {TABS.map((t) => (
        <button
          key={t}
          className="icon-btn ptool"
          data-tip={LABEL[t]}
          data-on={tab === t || undefined}
          aria-label={LABEL[t]}
          aria-pressed={tab === t}
          onClick={() => patch({ tab: tab === t ? null : t })}
        >
          <Icon d={t === 'info' && group ? GROUP_INFO : ICONS[t]} size={18} />
        </button>
      ))}
      <span className="ptool-menu" ref={box}>
        <button className="icon-btn ptool" data-tip="Lainnya" aria-label="Lainnya" aria-haspopup="menu" aria-expanded={menu} onClick={() => setMenu(!menu)}>
          <Icon d={DOTS} size={18} />
        </button>
        {menu && (
          <div className="popmenu" role="menu">
            <button
              role="menuitem"
              disabled={!tab}
              onClick={() => {
                setMenu(false)
                closePanel()
              }}
            >
              Tutup panel
            </button>
            <button
              role="menuitem"
              onClick={() => {
                setMenu(false)
                go('/aktivitas')
              }}
            >
              Buka halaman Aktivitas
            </button>
          </div>
        )}
      </span>
    </div>
  )
}

// Wraps a conversation: the chat on the left, the panel (when open) on the right.
export function Split({ children, panel }: { children: ReactNode; panel: ReactNode }) {
  const { tab } = usePanel()
  useEffect(() => {
    if (!tab) return
    const esc = (e: KeyboardEvent) => {
      if (e.key !== 'Escape' || e.defaultPrevented || document.querySelector('dialog[open], .mention')) return
      const t = e.target as HTMLElement
      if (t.tagName === 'INPUT' || t.tagName === 'SELECT') return // inline rename and filters use Esc themselves
      closePanel()
    }
    document.addEventListener('keydown', esc)
    return () => document.removeEventListener('keydown', esc)
  }, [tab])
  return (
    <div className="split">
      {children}
      {tab && (
        <>
          <button className="pscrim" aria-label="Tutup panel" tabIndex={-1} onClick={closePanel} />
          {panel}
        </>
      )}
    </div>
  )
}

// Refetches when `key` changes at once, and when `version` changes after a short pause (a burst of events = one fetch).
function useRemote<T>(fn: () => Promise<T>, key: string, version: number) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const epoch = useRef(0)
  const lastKey = useRef('')
  const run = useCallback(() => {
    const mine = ++epoch.current
    fn().then(
      (d) => {
        if (mine !== epoch.current) return
        setData(d)
        setError('')
        setLoading(false)
      },
      (e) => {
        if (mine !== epoch.current) return
        setError(errText(e))
        setLoading(false)
      },
    )
    // fn closes over the key, which is part of the deps below
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])
  useEffect(() => {
    if (lastKey.current !== key) {
      lastKey.current = key
      setData(null)
      setLoading(true)
      run()
      return
    }
    const t = window.setTimeout(run, 350)
    return () => window.clearTimeout(t)
  }, [key, version, run])
  return { data, error, loading, retry: run }
}

export interface PanelProps {
  scope: Scope | null // null: a new bot chat that has no session yet
  version: number
  bot?: Bot // bot chat
  group?: Group // group chat
  members?: Bot[]
}

export function SidePanel(p: PanelProps) {
  const { tab, width } = usePanel()
  const resizing = useRef(false)
  if (!tab) return null
  const onMove = (e: React.PointerEvent) => {
    if (resizing.current) patch({ width: clampW(window.innerWidth - e.clientX) })
  }
  return (
    <aside className="panel" style={{ ['--panel-w' as string]: `${width}px` }} aria-label={`Panel ${LABEL[tab]}`}>
      <div
        className="p-resize"
        role="separator"
        aria-orientation="vertical"
        aria-label="Ubah lebar panel"
        aria-valuemin={MIN_W}
        aria-valuemax={MAX_W}
        aria-valuenow={width}
        tabIndex={0}
        onPointerDown={(e) => {
          resizing.current = true
          e.currentTarget.setPointerCapture(e.pointerId)
        }}
        onPointerMove={onMove}
        onPointerUp={() => (resizing.current = false)}
        onKeyDown={(e) => {
          if (e.key === 'ArrowLeft') patch({ width: clampW(width + 16) })
          else if (e.key === 'ArrowRight') patch({ width: clampW(width - 16) })
        }}
      />
      <header className="p-head">
        <h2>{LABEL[tab]}</h2>
        <div className="p-tabs" role="tablist" aria-label="Tab panel">
          {TABS.map((t) => (
            <button key={t} role="tab" className="icon-btn ptool" data-on={tab === t || undefined} aria-selected={tab === t} aria-label={LABEL[t]} onClick={() => patch({ tab: t })}>
              <Icon d={t === 'info' && p.group ? GROUP_INFO : ICONS[t]} size={18} />
            </button>
          ))}
        </div>
        <button className="icon-btn" aria-label="Tutup panel" onClick={closePanel}>
          <Icon d={CLOSE} />
        </button>
      </header>
      <div className="p-body">
        {tab !== 'info' && !p.scope && <p className="quiet pad">Belum ada percakapan. Kirim pesan dulu, lalu datanya muncul di sini.</p>}
        {tab === 'token' && p.scope && <Tokens {...p} scope={p.scope} />}
        {tab === 'aktivitas' && p.scope && <Activity scope={p.scope} version={p.version} />}
        {tab === 'info' && (p.group ? <GroupInfo group={p.group} members={p.members ?? []} /> : p.bot ? <BotInfo bot={p.bot} /> : null)}
      </div>
    </aside>
  )
}

const scopeKey = (s: Scope) => (s.group_id ? `g:${s.group_id}` : `s:${s.session_id}`)

// ---------- Berpikir ----------
type Scoped = PanelProps & { scope: Scope }
// ---------- Token ----------
const dash = (n: number) => nf.format(n)
function Bar({ ratio, color }: { ratio: number; color: string }) {
  return (
    <span className="bar" aria-hidden="true">
      <span style={{ transform: `scaleX(${Math.max(0.02, Math.min(1, ratio))})`, background: color }} />
    </span>
  )
}

function Tokens({ scope, version, bot, members, group }: Scoped) {
  const { bots, me } = useData()
  const u = useRemote<Usage>(() => api.usage(scope), scopeKey(scope), version)
  const month = useRemote(() => api.usageBots('month'), 'month', version)
  const lookup = (id: string) => members?.find((b) => b.id === id) ?? (bot && bot.id === id ? bot : undefined) ?? bots.find((b) => b.id === id)
  const limit = me?.limits.monthly_tokens
  const used = me?.usage.tokens_month ?? 0

  return (
    <div className="p-scroll">
      <section className="p-sec" aria-labelledby="pt1">
        <h3 id="pt1">Percakapan ini</h3>
        {u.loading && <p className="quiet">Memuat...</p>}
        {u.error && !u.data && <ErrorLine text={u.error} onRetry={u.retry} />}
        {u.data && u.data.total.runs === 0 && <p className="quiet">Belum ada pemakaian token di percakapan ini.</p>}
        {u.data && u.data.total.runs > 0 && (
          <>
            <dl className="stats num">
              <div>
                <dt>Masuk</dt>
                <dd>{dash(u.data.total.input)}</dd>
              </div>
              <div>
                <dt>Keluar</dt>
                <dd>{dash(u.data.total.output)}</dd>
              </div>
              <div>
                <dt>Cache</dt>
                <dd>{dash(u.data.total.cache_read)}</dd>
              </div>
              <div>
                <dt>Total</dt>
                <dd>
                  <b>{dash(u.data.total.total)}</b>
                </dd>
              </div>
            </dl>
            {group && (
              <p className="quiet small">
                Batas per kiriman grup: <b>{me?.limits.group_send_token_budget == null ? 'Tanpa batas' : `${dash(me.limits.group_send_token_budget)} token`}</b>
              </p>
            )}
            <h4>Per agen</h4>
            <ul className="bars">
              {u.data.by_bot.map((b) => {
                const bb = lookup(b.bot_id)
                return (
                  <li key={b.bot_id}>
                    <span className="bar-top">
                      <span>{b.name}</span>
                      <span className="num">
                        {dash(b.total)} <small className="quiet">· {b.runs} giliran</small>
                      </span>
                    </span>
                    <Bar ratio={b.total / Math.max(1, u.data!.by_bot[0].total)} color={botColor(bb)} />
                    <small className="quiet num">
                      {dash(b.input)} masuk, {dash(b.output)} keluar
                    </small>
                  </li>
                )
              })}
            </ul>
            <h4>Giliran terbaru</h4>
            <ul className="turn-list num">
              {u.data.turns.map((t) => (
                <li key={t.run_id} data-bad={t.status === 'failed' || undefined}>
                  <span className="turn-who">
                    <i style={{ background: botColor(lookup(t.bot_id)) }} aria-hidden="true" />
                    {lookup(t.bot_id)?.name ?? t.bot_id}
                  </span>
                  <span className="quiet">{clock(t.created_at)}</span>
                  <span className="turn-tok">
                    <small className="quiet">
                      {dash(t.input)} / {dash(t.output)}
                    </small>{' '}
                    <b>{dash(t.total)}</b>
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section className="p-sec" aria-labelledby="pt2">
        <h3 id="pt2">Bulan ini</h3>
        {month.loading && <p className="quiet">Memuat...</p>}
        {month.error && !month.data && <ErrorLine text={month.error} onRetry={month.retry} />}
        {month.data && month.data.length === 0 && <p className="quiet">Belum ada pemakaian bulan ini.</p>}
        {month.data && month.data.length > 0 && (
          <ul className="bars">
            {month.data.map((b) => (
              <li key={b.bot_id}>
                <span className="bar-top">
                  <span>{b.name}</span>
                  <span className="num">{dash(b.total)}</span>
                </span>
                <Bar ratio={b.total / Math.max(1, month.data![0].total)} color={botColor(lookup(b.bot_id))} />
              </li>
            ))}
          </ul>
        )}
        {me && (
          <div className="meter">
            <span className="bar-top">
              <span>Paket {me.plan.name}</span>
              <span className="num">{limit === null ? 'Tanpa batas' : `${dash(used)} dari ${dash(limit ?? 0)}`}</span>
            </span>
            {limit !== null && <Bar ratio={limit ? used / limit : 0} color="var(--accent)" />}
            {limit === null && <small className="quiet num">{dash(used)} token terpakai bulan ini</small>}
          </div>
        )}
      </section>
    </div>
  )
}

// ---------- Info ----------
const STATUS = { idle: 'Siap', working: 'Bekerja', discussing: 'Berdiskusi' } as const

function BotInfo({ bot }: { bot: Bot }) {
  return (
    <div className="p-scroll">
      <div className="info-top" style={{ ['--bot' as string]: botColor(bot) }}>
        <BotAvatar bot={bot} size={48} />
        <div>
          <h3>{bot.name}</h3>
          <p className="quiet">{bot.role}</p>
        </div>
      </div>
      <dl className="kv">
        <div>
          <dt>Tim</dt>
          <dd>{teamLabel(bot.team)}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{bot.status === 'working' && bot.activity ? `Bekerja: ${bot.activity}` : STATUS[bot.status]}</dd>
        </div>
      </dl>
      <h4>Kepribadian</h4>
      <p className="about">{bot.about || 'Belum ada ringkasan kepribadian.'}</p>
    </div>
  )
}

function GroupInfo({ group, members }: { group: Group; members: Bot[] }) {
  const { setDialog, setGroup, refreshGroups } = useData()
  const [name, setName] = useState(group.name)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const [confirm, setConfirm] = useState(false)
  useEffect(() => setName(group.name), [group.name])

  async function rename() {
    const n = name.trim()
    if (!n || n === group.name) return setName(group.name)
    setBusy(true)
    setProblem('')
    try {
      setGroup(await api.patchGroup(group.id, { name: n }))
    } catch (e) {
      setProblem(errText(e))
    } finally {
      setBusy(false)
    }
  }
  async function remove() {
    setBusy(true)
    setProblem('')
    try {
      await api.deleteGroup(group.id)
      go('/')
      await refreshGroups().catch(() => {})
    } catch (e) {
      setProblem(errText(e))
      setBusy(false)
    }
  }

  return (
    <div className="p-scroll">
      <label className="field">
        <span>Nama grup</span>
        <input
          value={name}
          maxLength={60}
          onChange={(e) => setName(e.target.value)}
          onBlur={() => void rename()}
          onKeyDown={(e) => {
            if (e.key === 'Enter') e.currentTarget.blur()
            else if (e.key === 'Escape') setName(group.name)
          }}
        />
      </label>
      <div className="sec-line">
        <h4>Anggota ({members.length})</h4>
        <button className="btn soft sm" onClick={() => setDialog({ kind: 'group', id: group.id })}>
          Atur anggota
        </button>
      </div>
      <ul className="members">
        {members.map((b) => (
          <li key={b.id} style={{ ['--bot' as string]: botColor(b) }}>
            <BotAvatar bot={b} size={32} />
            <span className="bot-text">
              <b>{b.name}</b>
              <small>{b.role}</small>
            </span>
            <span className="status-dot" data-s={b.status} role="img" aria-label={STATUS[b.status]} />
            <small className="quiet">{STATUS[b.status]}</small>
          </li>
        ))}
      </ul>
      {problem && (
        <p className="problem-bar small" role="alert">
          {problem}
        </p>
      )}
      <div className="danger-zone">
        {!confirm ? (
          <button className="btn quiet-btn danger-text" onClick={() => setConfirm(true)}>
            Hapus grup
          </button>
        ) : (
          <div role="alert" className="confirm-box">
            <p>
              Hapus grup &ldquo;{group.name}&rdquo;? Diskusi yang berjalan dihentikan dan grup hilang dari daftar.
            </p>
            <div className="confirm-actions">
              <button className="btn danger" disabled={busy} onClick={() => void remove()}>
                {busy ? 'Menghapus...' : 'Hapus grup'}
              </button>
              <button className="btn quiet-btn" disabled={busy} onClick={() => setConfirm(false)}>
                Batal
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
