import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { api, asStr, errText, subscribe, toGroupMsg } from './bff'
import type { Bot, BotStatus, Group, Me, Raw, RunInfo, Settings, SseState } from './bff'
import { botPath, go, groupPath } from './router'

// App-wide data: the account, the bots, the groups and the active runs, kept fresh by the one global /api/events
// stream. Views subscribe to the live events they care about (group messages, typing) through `on`.

export type DialogState = { kind: 'bot' } | { kind: 'group'; id?: string } | { kind: 'plan' } | { kind: 'delete'; bot: Bot } | null
export interface Toast {
  id: number
  text: string
  href: string
}
type Listener = (d: Raw) => void

interface Data {
  loadState: 'loading' | 'ok' | 'error'
  error: string
  me: Me | null
  settings: Settings
  saveSettings: (p: Partial<Settings>) => Promise<void>
  bots: Bot[]
  groups: Group[]
  runs: RunInfo[]
  conn: SseState
  reload: () => void
  refreshMe: () => void
  refreshBots: () => Promise<Bot[]>
  refreshGroups: () => Promise<Group[]>
  setGroup: (g: Group) => void
  on: (type: string, fn: Listener) => () => void
  dialog: DialogState
  setDialog: (d: DialogState) => void
  toasts: Toast[]
  dismissToast: (id: number) => void
  notifyAsk: boolean
  askNotify: () => void
  answerNotify: (yes: boolean) => void
  viewing: (href: string) => void
  flash: (text: string) => void
}

const Ctx = createContext<Data | null>(null)
export const useData = () => {
  const d = useContext(Ctx)
  if (!d) throw new Error('DataProvider missing')
  return d
}

const ENDED = ['done', 'completed', 'finished', 'stopped', 'failed', 'error', 'idle', 'cancelled', 'canceled', 'interrupted', 'limit']
export const sendEnded = (status: unknown) => ENDED.includes(asStr(status).toLowerCase())
const DEFAULT_SETTINGS: Settings = { company_name: 'Colorbox', language: 'id', timezone: 'Asia/Jakarta', model: null, provider: null, reasoning_effort: null, notify: { done: true, failed: true, input: true } }
const NOTIFY_KEY = 'pegawai.notifyAsked'
const clip = (s: string, n = 60) => (s.length > n ? s.slice(0, n).trimEnd() + '…' : s)

// CS runs answer in JSON: the toast shows the reply draft, never the raw JSON.
const csPreview = (m: unknown): string | undefined => {
  const x = (m as { workflow?: string; structured?: { customer_reply_draft?: unknown } } | undefined)
  return typeof x?.structured?.customer_reply_draft === 'string' ? x.structured.customer_reply_draft : x?.workflow === 'cs' ? 'draf balasan belum terstruktur' : undefined
}

export function DataProvider({ children }: { children: ReactNode }) {
  const [loadState, setLoadState] = useState<Data['loadState']>('loading')
  const [error, setError] = useState('')
  const [me, setMe] = useState<Me | null>(null)
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS)
  const [bots, setBots] = useState<Bot[]>([])
  const [groups, setGroups] = useState<Group[]>([])
  const [runs, setRuns] = useState<RunInfo[]>([])
  const [conn, setConn] = useState<SseState>('open')
  const [dialog, setDialog] = useState<DialogState>(null)
  const [toasts, setToasts] = useState<Toast[]>([])
  const [notifyAsk, setNotifyAsk] = useState(false)
  const listeners = useRef(new Map<string, Set<Listener>>())
  const botsRef = useRef<Bot[]>([])
  const groupsRef = useRef<Group[]>([])
  const notified = useRef(new Set<string>())
  const seen = useRef(false) // true after a connection error, so the next open triggers a refresh
  const watching = useRef('') // route path the user is looking at: no toast for it while the tab is visible
  const settingsRef = useRef(settings)
  botsRef.current = bots
  settingsRef.current = settings
  groupsRef.current = groups

  const refreshMe = useCallback(() => void api.me().then(setMe, () => {}), [])
  const refreshBots = useCallback(async () => {
    const b = await api.bots()
    setBots(b)
    return b
  }, [])
  const refreshGroups = useCallback(async () => {
    const g = await api.groups()
    setGroups(g)
    return g
  }, [])
  const loadRuns = useCallback(() => void api.runs('active').then(setRuns, () => {}), [])
  const reload = useCallback(() => {
    Promise.all([api.me(), api.bots(), api.groups(), api.runs('active')]).then(
      ([m, b, g, r]) => {
        void api.settings().then(setSettings, () => {})
        setMe(m)
        setBots(b)
        setGroups(g)
        setRuns(r)
        setLoadState('ok')
        setError('')
      },
      (e) => {
        setError(errText(e))
        setLoadState((s) => (s === 'ok' ? s : 'error')) // keep what we have when a background refresh fails
      },
    )
  }, [])

  const on = useCallback((type: string, fn: Listener) => {
    let set = listeners.current.get(type)
    if (!set) listeners.current.set(type, (set = new Set()))
    set.add(fn)
    return () => void set.delete(fn)
  }, [])
  const emit = (type: string, d: Raw) => listeners.current.get(type)?.forEach((fn) => fn(d))

  // kind: which Notifikasi switch lets this toast also reach the browser (the in-page toast is always shown)
  const toast = useCallback((text: string, href: string, kind: 'done' | 'failed' | 'input' = 'done') => {
    const hidden = document.hidden
    if (!(hidden === false && watching.current === href)) {
      const id = Date.now() + Math.random()
      setToasts((t) => [...t.slice(-3), { id, text, href }])
      window.setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 7000)
    }
    if (hidden && settingsRef.current.notify[kind] && 'Notification' in window && Notification.permission === 'granted') {
      const n = new Notification('Pegawai AI', { body: text, tag: href })
      n.onclick = () => {
        window.focus()
        go(href)
        n.close()
      }
    }
  }, [])

  // Plain success toast (no link).
  const flash = useCallback((text: string) => {
    const id = Date.now() + Math.random()
    setToasts((t) => [...t.slice(-3), { id, text, href: '' }])
    window.setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000)
  }, [])

  const viewing = useCallback((href: string) => {
    watching.current = href
  }, [])

  useEffect(reload, [reload])

  // One global stream for the sidebar, the runs pill, group chat and notifications.
  useEffect(() => {
    let timer = 0
    const runChanged = (d: Raw) => {
      window.clearTimeout(timer)
      timer = window.setTimeout(() => {
        loadRuns()
        refreshMe()
      }, 250)
      const status = asStr(d.status).toLowerCase()
      const id = asStr(d.id)
      if (asStr(d.kind) === 'group' || notified.current.has(id)) return
      if (!['completed', 'done', 'finished', 'failed'].includes(status)) return
      notified.current.add(id)
      const botName = botsRef.current.find((b) => b.id === asStr(d.bot_id))?.name ?? 'Bot'
      void api.run(id).then(
        (r) => toast(status === 'failed' ? `${botName} gagal` : `${botName} selesai: ${clip(csPreview(r.meta) ?? (r.output || r.input))}`, botPath(r.bot_id || asStr(d.bot_id), r.session_id), status === 'failed' ? 'failed' : 'done'),
        () => toast(`${botName} selesai`, botPath(asStr(d.bot_id)), status === 'failed' ? 'failed' : 'done'),
      )
    }
    return subscribe(
      '/events',
      {
        run: runChanged,
        run_input: (d) => {
          if (asStr(d.kind) === 'group') return
          const botName = botsRef.current.find((b) => b.id === asStr(d.bot_id))?.name ?? 'Bot'
          toast(`${botName} ${asStr(d.what) === 'clarify' ? 'butuh jawaban Anda' : 'butuh izin Anda'}`, botPath(asStr(d.bot_id)), 'input')
        },
        bot_status: (d) =>
          setBots((cur) => cur.map((b) => (b.id === asStr(d.bot_id) ? { ...b, status: (['working', 'discussing'].includes(asStr(d.status)) ? asStr(d.status) : 'idle') as BotStatus, activity: asStr(d.activity) } : b))),
        group_message: (d) => emit('group_message', { ...d, message: toGroupMsg((d.message ?? {}) as Raw), group_id: asStr(d.group_id) }),
        group_typing: (d) => emit('group_typing', d),
        group_reasoning: (d) => emit('group_reasoning', d),
        group_send: (d) => {
          const gid = asStr(d.group_id)
          const ended = sendEnded(d.status)
          setGroups((cur) => cur.map((g) => (g.id === gid ? { ...g, running: !ended } : g)))
          if (ended) {
            const g = groupsRef.current.find((x) => x.id === gid)
            if (g) toast(`Diskusi di ${g.name} selesai`, groupPath(gid))
          }
          emit('group_send', d)
        },
      },
      (s) => {
        setConn(s)
        if (s === 'retry') seen.current = true
        else if (seen.current) {
          seen.current = false
          reload() // events may have been missed while disconnected
        }
      },
    )
  }, [loadRuns, refreshMe, reload, toast])

  const value = useMemo<Data>(
    () => ({
      loadState,
      error,
      me,
      settings,
      saveSettings: async (p) => setSettings(await api.saveSettings(p)),
      bots,
      groups,
      runs,
      conn,
      reload,
      refreshMe,
      refreshBots,
      refreshGroups,
      setGroup: (g) => setGroups((cur) => (cur.some((x) => x.id === g.id) ? cur.map((x) => (x.id === g.id ? g : x)) : [...cur, g])),
      on,
      dialog,
      setDialog,
      toasts,
      dismissToast: (id) => setToasts((t) => t.filter((x) => x.id !== id)),
      notifyAsk,
      // The permission prompt is shown once, as a small inline question on the first send, never on page load.
      askNotify: () => {
        if (!('Notification' in window) || Notification.permission !== 'default') return
        try {
          if (localStorage.getItem(NOTIFY_KEY)) return
        } catch {
          /* private mode: ask once per visit */
        }
        setNotifyAsk(true)
      },
      answerNotify: (yes) => {
        setNotifyAsk(false)
        try {
          localStorage.setItem(NOTIFY_KEY, '1')
        } catch {
          /* ignore */
        }
        if (yes) void Notification.requestPermission()
      },
      viewing,
      flash,
    }),
    [loadState, error, me, settings, bots, groups, runs, conn, reload, refreshMe, refreshBots, refreshGroups, on, dialog, toasts, notifyAsk, viewing, flash],
  )
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

