// Typed client for the BFF contract (docs/bff-spec.md section 5). Every call goes to /bff/api/...; the Vite proxy
// adds the shared key, so browser code never holds a key or a Hermes URL. Response shapes are read defensively
// (the BFF is built in parallel): the normalisers below are the one place that knows about alternative field names.

const BASE = '/bff/api'

export class ApiError extends Error {
  status: number
  upgrade: boolean
  constructor(message: string, status = 0, upgrade = false) {
    super(message)
    this.status = status
    this.upgrade = upgrade
  }
}

function fallbackMessage(status: number): string {
  if (status === 401) return 'Akses ditolak. Kunci BFF belum diisi atau salah.'
  if (status === 402) return 'Kuota paket habis. Naikkan paket untuk melanjutkan.'
  if (status === 404) return 'Data tidak ditemukan. Mungkin sudah dihapus.'
  if (status === 409) return 'Permintaan bentrok dengan keadaan saat ini. Coba lagi.'
  if (status === 429) return 'Terlalu banyak tugas berjalan, coba sebentar lagi.'
  if (status >= 500) return 'Server belum terjangkau. Pastikan BFF menyala, lalu coba lagi.'
  return `Permintaan gagal (kode ${status}).`
}

async function call<T>(method: string, path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  let res: Response
  try {
    res = await fetch(BASE + path, {
      method,
      signal,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch (e) {
    if (signal?.aborted) throw e
    throw new ApiError('Server belum terjangkau. Pastikan BFF menyala, lalu coba lagi.')
  }
  if (!res.ok) {
    let j: Record<string, unknown> = {}
    try {
      j = (await res.json()) as Record<string, unknown>
    } catch {
      /* empty or non-JSON error body */
    }
    const msg = typeof j.error === 'string' && j.error ? j.error : fallbackMessage(res.status)
    throw new ApiError(msg, res.status, j.upgrade === true || res.status === 402)
  }
  if (res.status === 204) return undefined as T
  try {
    return (await res.json()) as T
  } catch {
    return undefined as T
  }
}

export const isAbort = (e: unknown) => e instanceof DOMException && e.name === 'AbortError'
export const errText = (e: unknown) => (e instanceof ApiError ? e.message : 'Terjadi kesalahan yang tidak dikenal.')

// shortcut: untyped wire objects, normalised right below; tighten once the BFF publishes a schema
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Raw = Record<string, any>
export const asNum = (x: unknown, d = 0) => (x !== null && x !== '' && x !== undefined && Number.isFinite(Number(x)) ? Number(x) : d)
export const asStr = (x: unknown, d = '') => (typeof x === 'string' ? x : x == null ? d : String(x))
const list = (x: unknown): Raw[] => (Array.isArray(x) ? x : Array.isArray((x as Raw)?.data) ? (x as Raw).data : Array.isArray((x as Raw)?.items) ? (x as Raw).items : [])
const epoch = (x: unknown): number => {
  if (typeof x === 'number') return x > 1e12 ? x / 1000 : x
  const t = Date.parse(asStr(x))
  return Number.isNaN(t) ? 0 : t / 1000
}

// ---- types ----
export type BotStatus = 'idle' | 'working' | 'discussing'
export interface Bot {
  id: string
  name: string
  role: string
  team: string
  color: string
  builtin: boolean
  status: BotStatus
  activity: string
  about: string
}
export interface Template {
  id: string
  name: string
  role: string
  team: string
  color: string
  description: string
}
// null means "no limit" (shown as "Tanpa batas")
export interface Limits {
  monthly_tokens: number | null
  group_send_token_budget: number | null
  max_bots: number
  max_groups: number
  max_concurrent_runs: number
}
export interface Plan extends Limits {
  id: string
  name: string
  price: string
}
export interface Me {
  plan: { id: string; name: string }
  limits: Limits
  usage: { tokens_month: number; bots: number; groups: number; active_runs: number }
}
export interface Group {
  id: string
  name: string
  members: string[]
  running: boolean
}
export interface GroupMsg {
  id: string
  group_id: string
  role: 'user' | 'bot' | 'system'
  bot_id: string
  text: string
  run_id: string
  created_at: number
}
export interface Thought {
  run_id: string
  bot_id: string
  status: string
  created_at: number
  reasoning: string
}
export interface Usage {
  total: { input: number; output: number; cache_read: number; total: number; runs: number }
  by_bot: { bot_id: string; name: string; input: number; output: number; total: number; runs: number }[]
  turns: { run_id: string; bot_id: string; created_at: number; input: number; output: number; total: number; status: string }[]
}
export interface BotUsage {
  bot_id: string
  name: string
  input: number
  output: number
  total: number
  runs: number
}
export type Scope = { session_id: string; group_id?: undefined } | { group_id: string; session_id?: undefined }
export interface RunInfo {
  id: string
  bot_id: string
  bot_name: string
  input: string
  status: string
  kind: string
  session_id: string
  group_id: string
  started_at: number
}
export interface Session {
  id: string
  title: string
  preview: string
  messageCount: number
  lastActive: number // epoch seconds
  model: string
}
export interface ToolChip {
  id: string
  tool: string
  preview?: string
  status: 'run' | 'done' | 'bad'
}
export interface Approval {
  request_id: string
  description: string
  choices: string[]
}
export interface ChatMessage {
  key: string
  role: 'user' | 'assistant'
  content: string
  reasoning: string
  tools: ToolChip[]
  tokens?: { input: number; output: number }
  stopped?: boolean
  error?: string
  approval?: Approval
  notes?: string[]
}
export interface ActivityRow {
  id: string
  time: number
  bot_id: string
  bot_name: string
  tool: string
  status: 'ok' | 'error'
  duration: number // seconds
  preview: string
  link: string // hash route or ''
  where: string
}

// ---- normalisers ----
const toBot = (r: Raw): Bot => ({
  id: asStr(r.id),
  name: asStr(r.name, asStr(r.id)),
  role: asStr(r.role),
  team: asStr(r.team, 'Tanpa tim'),
  color: asStr(r.color),
  builtin: r.builtin === true,
  status: r.status === 'working' || r.status === 'discussing' ? r.status : 'idle',
  activity: asStr(r.activity),
  about: asStr(r.about),
})
const toLimits = (r: Raw = {}): Limits => ({
  monthly_tokens: r.monthly_tokens == null ? null : asNum(r.monthly_tokens),
  group_send_token_budget: r.group_send_token_budget == null ? null : asNum(r.group_send_token_budget),
  max_bots: asNum(r.max_bots),
  max_groups: asNum(r.max_groups),
  max_concurrent_runs: asNum(r.max_concurrent_runs),
})
const toPlan = (r: Raw): Plan => ({
  id: asStr(r.id),
  name: asStr(r.name, asStr(r.id)),
  price: asStr(r.price_label ?? r.price),
  ...toLimits(r.limits ?? r),
})
const toMe = (r: Raw): Me => {
  const p = typeof r.plan === 'string' ? { id: r.plan, name: r.plan } : { id: asStr(r.plan?.id), name: asStr(r.plan?.name, asStr(r.plan?.id)) }
  const u = r.usage ?? {}
  return {
    plan: p,
    limits: toLimits(r.limits ?? r.plan),
    usage: { tokens_month: asNum(u.tokens_month), bots: asNum(u.bots), groups: asNum(u.groups), active_runs: asNum(u.active_runs) },
  }
}
const toGroup = (r: Raw): Group => {
  const m: unknown[] = Array.isArray(r.members) ? r.members : Array.isArray(r.bot_ids) ? r.bot_ids : []
  return {
    id: asStr(r.id),
    name: asStr(r.name),
    members: m.map((x) => (typeof x === 'string' ? x : asStr((x as Raw).bot_id ?? (x as Raw).id))),
    running: r.running === true || r.status === 'running',
  }
}
export const toGroupMsg = (r: Raw): GroupMsg => {
  const role = asStr(r.author ?? r.role ?? r.kind ?? r.sender)
  return {
    id: asStr(r.id),
    group_id: asStr(r.group_id),
    role: role === 'user' ? 'user' : role === 'system' ? 'system' : 'bot',
    bot_id: asStr(r.bot_id),
    text: asStr(r.text ?? r.content),
    run_id: asStr(r.run_id),
    created_at: epoch(r.created_at ?? r.time),
  }
}
export const toRun = (r: Raw): RunInfo => ({
  id: asStr(r.id),
  bot_id: asStr(r.bot_id),
  bot_name: asStr(r.bot_name ?? r.bot),
  input: asStr(r.input ?? r.input_short),
  status: asStr(r.status),
  kind: asStr(r.kind, 'chat'),
  session_id: asStr(r.session_id),
  group_id: asStr(r.group_id),
  started_at: epoch(r.started_at ?? r.created_at),
})
const toSession = (s: Raw): Session => ({
  id: asStr(s.id),
  title: asStr(s.title),
  preview: asStr(s.preview),
  messageCount: asNum(s.message_count ?? s.messageCount),
  lastActive: epoch(s.last_active ?? s.started_at ?? s.updated_at),
  model: asStr(s.model),
})
const toActivity = (r: Raw): ActivityRow => {
  const group_id = asStr(r.group_id)
  const bot_id = asStr(r.bot_id)
  const sid = asStr(r.session_id)
  return {
    id: asStr(r.id),
    time: epoch(r.time ?? r.created_at ?? r.ts),
    bot_id,
    bot_name: asStr(r.bot_name ?? r.bot, bot_id),
    tool: asStr(r.tool),
    status: asStr(r.status) === 'error' ? 'error' : 'ok',
    duration: asNum(r.duration),
    preview: asStr(r.preview),
    link: group_id ? `/grup/${encodeURIComponent(group_id)}` : bot_id ? `/bot/${encodeURIComponent(bot_id)}${sid ? '/' + encodeURIComponent(sid) : ''}` : '',
    where: asStr(r.group_name ?? r.chat_name ?? r.session_title),
  }
}

// Folds stored Hermes rows into chat turns: every assistant/tool row after a user row belongs to one assistant turn.
function foldMessages(rows: Raw[]): ChatMessage[] {
  const out: ChatMessage[] = []
  let turn: ChatMessage | null = null
  for (const m of rows) {
    const key = `h-${m.id ?? out.length}`
    if (m.role === 'user') {
      turn = null
      out.push({ key, role: 'user', content: asStr(m.content), reasoning: '', tools: [] })
    } else if (m.role === 'assistant' || m.role === 'tool') {
      if (!turn) {
        turn = { key, role: 'assistant', content: '', reasoning: '', tools: [] }
        out.push(turn)
      }
      if (m.role === 'tool') {
        turn.tools.push({ id: asStr(m.tool_call_id, key), tool: asStr(m.tool_name, 'tool'), status: 'done' })
      } else {
        const text = asStr(m.content).trim()
        if (text) turn.content += (turn.content ? '\n\n' : '') + text
        const why = asStr(m.reasoning_content || m.reasoning).trim()
        if (why) turn.reasoning += (turn.reasoning ? '\n\n' : '') + why
      }
    } // session_meta and anything else: hidden
  }
  return out
}

export const newKey = (p: string) => p + '-' + Math.random().toString(36).slice(2, 10)

// ---- calls ----
const q = (o: Record<string, string | number | undefined>) => {
  const s = new URLSearchParams()
  for (const [k, v] of Object.entries(o)) if (v !== undefined && v !== '') s.set(k, String(v))
  const t = s.toString()
  return t ? '?' + t : ''
}
const enc = encodeURIComponent

export const api = {
  me: async () => toMe(await call<Raw>('GET', '/me')),
  plans: async () => list(await call('GET', '/plans')).map(toPlan),
  setPlan: (plan_id: string) => call<unknown>('PUT', '/me/plan', { plan_id }),
  templates: async (): Promise<Template[]> =>
    list(await call('GET', '/templates')).map((r) => ({
      id: asStr(r.id),
      name: asStr(r.name),
      role: asStr(r.role),
      team: asStr(r.team),
      color: asStr(r.color),
      description: asStr(r.description ?? r.short),
    })),
  bots: async () => list(await call('GET', '/bots')).map(toBot),
  createBot: async (b: { name: string; role: string; team: string; color?: string; template?: string; persona?: string }) =>
    toBot(await call<Raw>('POST', '/bots', b)),
  deleteBot: (id: string) => call<void>('DELETE', `/bots/${enc(id)}`),
  sessions: async (botId: string, signal?: AbortSignal) =>
    list(await call('GET', `/bots/${enc(botId)}/sessions`, undefined, signal))
      .map(toSession)
      .sort((a, b) => b.lastActive - a.lastActive),
  messages: async (botId: string, sid: string, signal?: AbortSignal) =>
    foldMessages(list(await call('GET', `/bots/${enc(botId)}/sessions/${enc(sid)}/messages`, undefined, signal))),
  renameSession: (botId: string, sid: string, title: string) => call<void>('PATCH', `/bots/${enc(botId)}/sessions/${enc(sid)}`, { title }),
  deleteSession: (botId: string, sid: string) => call<void>('DELETE', `/bots/${enc(botId)}/sessions/${enc(sid)}`),
  startRun: async (botId: string, input: string, session_id?: string) => {
    const r = await call<Raw>('POST', `/bots/${enc(botId)}/runs`, session_id ? { input, session_id } : { input })
    return { run: toRun(r.run ?? r), session_id: asStr(r.session_id ?? r.run?.session_id) }
  },
  runs: async (status: 'active' | 'recent', limit?: number) => list(await call('GET', `/runs${q({ status, limit })}`)).map(toRun),
  run: async (id: string) => {
    const r = await call<Raw>('GET', `/runs/${enc(id)}`)
    return { ...toRun(r.run ?? r), output: asStr((r.run ?? r).output) }
  },
  stopRun: (id: string) => call<void>('POST', `/runs/${enc(id)}/stop`),
  steerRun: (id: string, text: string) => call<void>('POST', `/runs/${enc(id)}/steer`, { text }),
  approve: (id: string, choice: string) => call<void>('POST', `/runs/${enc(id)}/approval`, { choice }),
  groups: async () => list(await call('GET', '/groups')).map(toGroup),
  createGroup: async (name: string, bot_ids: string[]) => toGroup(await call<Raw>('POST', '/groups', { name, bot_ids })),
  patchGroup: async (id: string, p: { name?: string; bot_ids?: string[] }) => toGroup(await call<Raw>('PATCH', `/groups/${enc(id)}`, p)),
  groupMessages: async (id: string, before?: string) => list(await call('GET', `/groups/${enc(id)}/messages${q({ before, limit: 50 })}`)).map(toGroupMsg),
  sendGroup: async (id: string, text: string, mode: 'queue' | 'steer') => {
    const r = await call<Raw>('POST', `/groups/${enc(id)}/messages`, { text, mode })
    return { message: toGroupMsg(r.message ?? {}), queued: r.queued === true }
  },
  deleteGroup: (id: string) => call<void>('DELETE', `/groups/${enc(id)}`),
  stopGroup: (id: string) => call<void>('POST', `/groups/${enc(id)}/stop`),
  usage: async (s: Scope): Promise<Usage> => {
    const u = await call<Usage>('GET', `/usage${q({ ...s })}`)
    return { ...u, turns: u.turns.map((t) => ({ ...t, created_at: epoch(t.created_at) })) }
  },
  usageBots: (period: 'month' | 'all') => call<BotUsage[]>('GET', `/usage/bots${q({ period })}`),
  thinking: async (s: Scope): Promise<Thought[]> =>
    list(await call('GET', `/thinking${q({ ...s })}`)).map((r) => ({
      run_id: asStr(r.run_id),
      bot_id: asStr(r.bot_id),
      status: asStr(r.status),
      created_at: epoch(r.created_at),
      reasoning: asStr(r.reasoning),
    })),
  activity: async (f: { bot?: string; status?: string; before?: string; session_id?: string; group_id?: string }) => list(await call('GET', `/activity${q({ ...f, limit: 100 })}`)).map(toActivity),
}

// ---- SSE ----
// EventSource reconnects by itself (the server sends retry: 3000 and event ids). `onState('retry')` fires on every
// error so the UI can show "Menyambung ulang…"; when the browser gives up (readyState CLOSED, e.g. after a 5xx on the
// first request) we reopen after 3 s ourselves. Returns a function that closes it for good.
export type SseState = 'open' | 'retry'
export function subscribe(path: string, on: Record<string, (data: Raw) => void>, onState?: (s: SseState) => void): () => void {
  let es: EventSource | null = null
  let timer = 0
  let closed = false
  const open = () => {
    es = new EventSource(BASE + path)
    es.onopen = () => onState?.('open')
    es.onerror = () => {
      if (closed) return
      onState?.('retry')
      if (es?.readyState === EventSource.CLOSED) timer = window.setTimeout(open, 3000)
    }
    for (const [name, fn] of Object.entries(on)) {
      es.addEventListener(name, (e) => {
        let d: Raw
        try {
          d = JSON.parse((e as MessageEvent<string>).data) as Raw
        } catch {
          return // keepalive or partial frame
        }
        fn(d)
      })
    }
  }
  open()
  return () => {
    closed = true
    window.clearTimeout(timer)
    es?.close()
  }
}

export const usageOf = (u: Raw | undefined) => ({ input: asNum(u?.input_tokens ?? u?.prompt_tokens), output: asNum(u?.output_tokens ?? u?.completion_tokens) })
