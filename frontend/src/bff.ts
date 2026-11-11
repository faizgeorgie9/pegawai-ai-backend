// Typed client for the BFF contract (docs/bff-spec.md section 5). Every call goes to /bff/api/...; the Vite proxy
// adds the shared key, so browser code never holds a key or a Hermes URL. Response shapes are read defensively
// (the BFF is built in parallel): the normalisers below are the one place that knows about alternative field names.

import { toRunResult } from './results'
import type { RunResult } from './results'

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
  if (status === 402) return 'Batas penggunaan tercapai. Coba lagi nanti.'
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
    // 402 = quota reached. The plan UI is hidden, so show a plain error (no upgrade hint).
    if (res.status === 402) throw new ApiError('Batas penggunaan tercapai. Coba lagi nanti.', 402, false)
    throw new ApiError(msg, res.status, j.upgrade === true)
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
  createdAt: number // epoch seconds, 0 when unknown
  deleteError: string // set when the background removal of the profile failed, else ''
  model: string // '' = follow the default
  provider: string
  effort: string // reasoning_effort, '' = follow the default
}
export interface BotDetail extends Bot {
  persona: string
  template: string
}
export interface Toolset {
  name: string
  label: string
  description: string
  tools: string[]
  enabled: boolean
}
export interface BotTools {
  bot_id: string
  name: string
  ok: boolean
  toolsets: Toolset[]
}
export interface ToolsInfo {
  deny: string[]
  bots: BotTools[]
}
export interface Settings {
  company_name: string
  language: string
  timezone: string
  model: string | null
  provider: string | null
  reasoning_effort: string | null
  notify: { done: boolean; failed: boolean; input: boolean }
}
export interface ModelCatalog {
  default: { model: string | null; provider: string | null }
  providers: { slug: string; name: string; models: string[] }[]
}
export interface Security {
  deny: string[]
  bots: { bot_id: string; name: string; ok: boolean; blocked: string[]; approvals: string | null }[]
}
export interface KnowledgeInfo {
  retention_days: number
  docs: { id: string; title: string; workflow: string; version: string | null; date: string | null; files: { name: string; title: string }[] }[]
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
  seconds?: number
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
  origin: RunOrigin
}
// Where a run came from. `turn` and `of` are set for the turns of an Evaluasi sequence.
export interface RunOrigin {
  type: 'chat' | 'cs' | 'marketing' | 'evaluasi' | 'group'
  case_id: string
  turn: number
  of: number
}
export interface SeqTurn {
  turn: number
  run_id: string
  status: string
  input: string
  output: string
  error: string
  result: RunResult
}
export interface Sequence {
  id: string
  bot_id: string
  session_id: string
  case_id: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'stopped'
  current_turn: number
  of: number
  run_ids: string[]
  turns: SeqTurn[]
  error: string
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
export interface Clarify {
  request_id: string
  execution_generation: number
  question: string
  choices: string[]
}
export const toClarify = (d: Raw | null | undefined): Clarify | undefined =>
  d && typeof d.question === 'string' && d.question
    ? { request_id: asStr(d.request_id), execution_generation: Number(d.execution_generation) || 0, question: d.question, choices: Array.isArray(d.choices) ? d.choices.map((c: unknown) => asStr(c)) : [] }
    : undefined
export interface ChatMessage {
  key: string
  role: 'user' | 'assistant'
  content: string
  reasoning: string
  seconds?: number // whole-run duration, matched from /thinking by identical reasoning text
  tools: ToolChip[]
  tokens?: { input: number; output: number }
  stopped?: boolean
  error?: string
  approval?: Approval
  clarify?: Clarify
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

export interface EvalScore {
  score: number | null
  reason: string
}
// Version snapshot the BFF records on every run. Values are real or "tidak diketahui".
export interface RunMeta {
  hermes_version: string
  model: string
  provider: string
  bot_id: string
  soul_hash: string
  toolsets: string[] | string
  instructions_mode: string
  bff_commit?: string
}
// Optional workflow context of a run (contract section 2): the BFF builds instructions and retrieves knowledge.
export interface RunCtx {
  workflow?: 'cs' | 'marketing'
  stage?: string
  test_mode?: boolean
}
export interface CompareRun {
  run_id: string
  session_id: string | null
  bot_id: string
  output: string
  tokens: number
  duration: number | null
  meta: Partial<RunMeta>
}
export interface Comparison {
  mode: 'repeat' | 'agents'
  consistency: 'konsisten' | 'tidak_konsisten'
  note: string
  runs: CompareRun[]
}
export interface EvalSummary {
  cases: { case_id: string; verdict: 'pass' | 'fail' | 'blocked' }[]
  counts: { pass: number; fail: number; blocked: number }
  total_evaluations: number
  dimensions: Record<string, { avg: number | null; n: number }>
  latest_at: number
}
export interface EvalInput {
  case_id: string
  bot_id: string
  session_id: string | null
  run_id: string | null
  prompt: string
  expected: string
  actual: string
  scores: Record<string, EvalScore>
  verdict: 'pass' | 'fail' | 'blocked'
  notes: { errors: string; improvements: string; critical: boolean; reviewed_on: string }
  reviewer: string
  comparison?: Comparison | null
}
export interface Evaluation extends EvalInput {
  id: string
  created_at: number
  meta: Partial<RunMeta>
}
const toEval = (r: Raw): Evaluation => ({
  id: asStr(r.id),
  case_id: asStr(r.case_id),
  bot_id: asStr(r.bot_id),
  session_id: r.session_id ?? null,
  run_id: r.run_id ?? null,
  prompt: asStr(r.prompt),
  expected: asStr(r.expected),
  actual: asStr(r.actual),
  scores: (r.scores ?? {}) as Record<string, EvalScore>,
  verdict: r.verdict === 'pass' || r.verdict === 'blocked' ? r.verdict : 'fail',
  notes: { errors: asStr(r.notes?.errors), improvements: asStr(r.notes?.improvements), critical: r.notes?.critical === true, reviewed_on: asStr(r.notes?.reviewed_on) },
  reviewer: asStr(r.reviewer),
  created_at: epoch(r.created_at),
  meta: r.meta && typeof r.meta === 'object' ? r.meta : {},
  comparison: r.comparison && typeof r.comparison === 'object' && Array.isArray(r.comparison.runs) ? (r.comparison as Comparison) : null,
})

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
  createdAt: epoch(r.created_at),
  deleteError: asStr(r.delete_error),
  model: asStr(r.model),
  provider: asStr(r.provider),
  effort: asStr(r.reasoning_effort),
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
  origin: toOrigin(r.origin),
})
const ORIGINS = ['chat', 'cs', 'marketing', 'evaluasi', 'group'] as const
const toOrigin = (o: Raw | null | undefined): RunOrigin => ({
  type: ORIGINS.find((t) => t === o?.type) ?? 'chat',
  case_id: asStr(o?.case_id),
  turn: asNum(o?.turn),
  of: asNum(o?.of),
})
const SEQ_STATUS = ['queued', 'running', 'completed', 'failed', 'stopped'] as const
const toSeq = (r: Raw): Sequence => ({
  id: asStr(r.id),
  bot_id: asStr(r.bot_id),
  session_id: asStr(r.session_id),
  case_id: asStr(r.origin?.case_id),
  status: SEQ_STATUS.find((t) => t === r.status) ?? 'failed',
  current_turn: asNum(r.current_turn),
  of: asNum(r.of),
  run_ids: list(r.run_ids).map((x) => asStr(x)),
  turns: list(r.turns).map((t) => ({ turn: asNum(t.turn), run_id: asStr(t.run_id), status: asStr(t.status), input: asStr(t.input), output: asStr(t.output), error: asStr(t.error), result: toRunResult(t) })),
  error: asStr(r.error),
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
    link: group_id ? `/grup/${encodeURIComponent(group_id)}` : bot_id ? `/chat/${encodeURIComponent(bot_id)}${sid ? '/' + encodeURIComponent(sid) : ''}` : '',
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
  settings: () => call<Settings>('GET', '/settings'),
  saveSettings: (p: Partial<Settings>) => call<Settings>('PATCH', '/settings', p),
  models: () => call<ModelCatalog>('GET', '/models'),
  security: () => call<Security>('GET', '/settings/security'),
  knowledge: () => call<KnowledgeInfo>('GET', '/settings/knowledge'),
  exportHistory: async (): Promise<Blob> => {
    let res: Response
    try {
      res = await fetch(BASE + '/export/history')
    } catch {
      throw new ApiError('Server belum terjangkau. Pastikan BFF menyala, lalu coba lagi.')
    }
    if (!res.ok) throw new ApiError(fallbackMessage(res.status), res.status)
    return res.blob()
  },
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
  bot: async (id: string): Promise<BotDetail> => {
    const r = await call<Raw>('GET', `/bots/${enc(id)}`)
    return { ...toBot(r), persona: asStr(r.persona), template: asStr(r.template) }
  },
  updateBot: async (id: string, p: { name?: string; role?: string; team?: string; color?: string; persona?: string; model?: string | null; provider?: string | null; reasoning_effort?: string | null }): Promise<BotDetail> => {
    const r = await call<Raw>('PATCH', `/bots/${enc(id)}`, p)
    return { ...toBot(r), persona: asStr(r.persona), template: asStr(r.template) }
  },
  tools: async (bot?: string): Promise<ToolsInfo> => {
    const r = await call<Raw>('GET', `/tools${q({ bot })}`)
    return {
      deny: Array.isArray(r.deny) ? r.deny.map((x: unknown) => asStr(x)) : [],
      bots: list(r.bots).map((b) => ({
        bot_id: asStr(b.bot_id),
        name: asStr(b.name),
        ok: b.ok === true,
        toolsets: list(b.toolsets).map((t) => ({
          name: asStr(t.name),
          label: asStr(t.label, asStr(t.name)),
          description: asStr(t.description),
          tools: Array.isArray(t.tools) ? t.tools.map((x: unknown) => asStr(x)) : [],
          enabled: t.enabled === true,
        })),
      })),
    }
  },
  deleteBot: (id: string) => call<void>('DELETE', `/bots/${enc(id)}`),
  sessions: async (botId: string, signal?: AbortSignal) =>
    list(await call('GET', `/bots/${enc(botId)}/sessions`, undefined, signal))
      .map(toSession)
      .sort((a, b) => b.lastActive - a.lastActive),
  messages: async (botId: string, sid: string, signal?: AbortSignal) =>
    foldMessages(list(await call('GET', `/bots/${enc(botId)}/sessions/${enc(sid)}/messages`, undefined, signal))),
  renameSession: (botId: string, sid: string, title: string) => call<void>('PATCH', `/bots/${enc(botId)}/sessions/${enc(sid)}`, { title }),
  deleteSession: (botId: string, sid: string) => call<void>('DELETE', `/bots/${enc(botId)}/sessions/${enc(sid)}`),
  startRun: async (botId: string, input: string, session_id?: string, instructions?: string, ctx?: RunCtx) => {
    const r = await call<Raw>('POST', `/bots/${enc(botId)}/runs`, { input, ...(session_id ? { session_id } : {}), ...(instructions ? { instructions } : {}), ...(ctx?.workflow ? { workflow: ctx.workflow, ...(ctx.stage ? { stage: ctx.stage } : {}), ...(ctx.test_mode ? { test_mode: true } : {}) } : {}) })
    return { run: toRun(r.run ?? r), session_id: asStr(r.session_id ?? r.run?.session_id) }
  },
  runs: async (status: 'active' | 'recent', limit?: number, bot?: string) => list(await call('GET', `/runs${q({ status, limit, bot })}`)).map(toRun),
  run: async (id: string) => {
    const r = await call<Raw>('GET', `/runs/${enc(id)}`)
    const x = r.run ?? r
    const t0 = epoch(x.started_at)
    const t1 = epoch(x.finished_at)
    return {
      ...toRun(x),
      output: asStr(x.output),
      tokens: asNum(x.total_tokens),
      seconds: t0 && t1 ? Math.max(0, t1 - t0) : null,
      meta: (x.meta && typeof x.meta === 'object' ? x.meta : {}) as Partial<RunMeta>,
    }
  },
  startSequence: async (botId: string, turns: string[], caseId: string, ctx?: RunCtx) =>
    toSeq(await call<Raw>('POST', `/bots/${enc(botId)}/sequences`, { turns, origin: { type: 'evaluasi', case_id: caseId }, ...(ctx?.workflow ? { workflow: ctx.workflow, ...(ctx.stage ? { stage: ctx.stage } : {}), ...(ctx.test_mode ? { test_mode: true } : {}) } : {}) })),
  sequence: async (id: string) => toSeq(await call<Raw>('GET', `/sequences/${enc(id)}`)),
  latestSequence: async (caseId: string): Promise<Sequence | null> => {
    const r = list(await call('GET', `/sequences${q({ case_id: caseId, limit: 1 })}`))
    return r[0] ? toSeq(r[0]) : null
  },
  stopSequence: (id: string) => call<void>('POST', `/sequences/${enc(id)}/stop`),
  stopRun: (id: string) => call<void>('POST', `/runs/${enc(id)}/stop`),
  steerRun: (id: string, text: string) => call<void>('POST', `/runs/${enc(id)}/steer`, { text }),
  approve: (id: string, choice: string) => call<void>('POST', `/runs/${enc(id)}/approval`, { choice }),
  clarify: (id: string, answer: string) => call<void>('POST', `/runs/${enc(id)}/clarify`, { answer }),
  groups: async () => list(await call('GET', '/groups')).map(toGroup),
  createGroup: async (name: string, bot_ids: string[]) => toGroup(await call<Raw>('POST', '/groups', { name, bot_ids })),
  patchGroup: async (id: string, p: { name?: string; bot_ids?: string[] }) => toGroup(await call<Raw>('PATCH', `/groups/${enc(id)}`, p)),
  groupMessages: async (id: string, before?: string) => list(await call('GET', `/groups/${enc(id)}/messages${q({ before, limit: 50 })}`)).map(toGroupMsg),
  groupLive: async (id: string) => {
    const t = (await call<Raw>('GET', `/groups/${enc(id)}/live`)).turn as Raw | null // the bot turn on screen, if any
    return t ? { bot: asStr(t.bot_id), run: asStr(t.run_id) } : null
  },
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
      seconds: typeof r.seconds === 'number' ? r.seconds : undefined,
      reasoning: asStr(r.reasoning),
    })),
  evaluations: async (): Promise<Evaluation[]> => list(await call('GET', '/evaluations')).map(toEval),
  evaluationSummary: async (): Promise<EvalSummary> => {
    const r = await call<Raw>('GET', '/evaluations/summary')
    return {
      cases: list(r.cases).map((c) => ({ case_id: asStr(c.case_id), verdict: c.verdict === 'pass' || c.verdict === 'blocked' ? c.verdict : 'fail' })),
      counts: { pass: asNum(r.counts?.pass), fail: asNum(r.counts?.fail), blocked: asNum(r.counts?.blocked) },
      total_evaluations: asNum(r.total_evaluations),
      dimensions: Object.fromEntries(Object.entries((r.dimensions ?? {}) as Raw).map(([k, v]) => [k, { avg: typeof v?.avg === 'number' ? v.avg : null, n: asNum(v?.n) }])),
      latest_at: epoch(r.latest_at),
    }
  },
  saveEvaluation: async (b: EvalInput, id?: string) => toEval(await call<Raw>(id ? 'PATCH' : 'POST', id ? `/evaluations/${enc(id)}` : '/evaluations', b)),
  activity: async (f: { bot?: string; status?: string; before?: string; session_id?: string; group_id?: string; limit?: number }) => list(await call('GET', `/activity${q({ limit: 100, ...f })}`)).map(toActivity),
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
