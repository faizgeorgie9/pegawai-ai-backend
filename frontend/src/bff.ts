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
  if (status === 402) return 'Batas paket Anda tercapai.'
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
      headers: body === undefined || body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body),
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
    // 402 = plan limit reached. The BFF message says which limit; the plan UI is hidden, so never offer an upgrade button.
    throw new ApiError(msg, res.status, res.status !== 402 && j.upgrade === true)
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
  notify: { done: boolean; failed: boolean; input: boolean }
}
export interface ModelCatalog {
  default: { model: string | null; provider: string | null; reasoning_effort?: string | null }
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
// Knowledge Base item (a file or link the user added; the BFF extracts the text and keeps it per user).
export interface KbItem {
  id: string | null // null: a link that could not even be stored (e.g. the Knowledge Base is full)
  kind: 'file' | 'gdrive' | 'url'
  name: string
  source: string | null
  status: 'processing' | 'ready' | 'failed'
  error: string | null
  size_bytes: number | null
  chars: number | null
  created_at: string | null
}
export interface Template {
  id: string
  name: string
  role: string
  team: string
  color: string
  description: string
}
// Exact USD amount as the BFF formats it: `usd` is the exact decimal string, `label` the rounded text to show ("$0.50", "< $0.01").
export interface Money {
  usd: string
  label: string
}
export type LimitState = 'normal' | 'warning' | 'exceeded'
// Why a cost is an estimate ("perkiraan"): unverified_price, model_not_recorded or no_price, with the models involved.
export interface EstimateReason {
  code: 'unverified_price' | 'model_not_recorded' | 'no_price'
  models: string[]
}
// The limit part of a usage view. limit/remaining/percent are null when the plan has no USD limit.
export interface LimitInfo {
  cost: Money
  limit: Money | null
  remaining: Money | null
  percent: number | null
  state: LimitState
  basis: 'measured' | 'estimated'
}
// null means "no limit" (shown as "Tanpa batas")
export interface Limits {
  monthly_usd: Money | null
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
  usage: { tokens_month: number; bots: number; groups: number; active_runs: number } & LimitInfo
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
  plan?: ContentPlan // the message ends with a valid content plan (the BFF validated it): shown as an approval card
}
export interface PlanDay {
  date: string // YYYY-MM-DD
  theme: string
  products: string[]
  brief: string
  time: string // HH:MM
}
export interface ContentPlan {
  title: string
  days: PlanDay[]
  schedule_id: string | null // set once the user approved it
}
// Kanban board (GET /kanban): our own work in four columns, plus Hermes' own Kanban when it is connected.
export type KanbanColumnId = 'todo' | 'running' | 'blocked' | 'done'
export interface KanbanCard {
  key: string
  source: 'chat' | 'group' | 'schedule' | 'sequence' | 'plan' | 'hermes'
  title: string
  column: KanbanColumnId
  outcome: 'ok' | 'failed' | 'cancelled' | null
  note: string
  agents: { id: string; name: string; color: string }[]
  group: { id: string; name: string } | null
  at: number // epoch seconds, 0 when unknown
  link: string // app route, '' when the card cannot be opened
  cost: Money | null
  estimated: boolean
}
export interface KanbanBoard {
  columns: { id: KanbanColumnId; label: string; total: number; cards: KanbanCard[] }[]
  hermes: { state: 'ok' | 'unavailable' | 'pending'; count: number }
  period: string
}
export interface KanbanFilter {
  agent?: string
  group?: string
  period?: string
}
export type OccStatus = 'planned' | 'running' | 'done' | 'skipped' | 'failed' | 'cancelled'
export interface Occurrence {
  id: string
  schedule_id: string
  planned_at: number // epoch seconds
  title: string
  brief: string
  status: OccStatus
  skip_reason: string
  agents: string[] // plan days: writer, visual; empty = the schedule's own target
  run_id: string
  cost: Money | null
  estimated: boolean
}
export interface Schedule {
  id: string
  kind: 'recurring' | 'plan'
  title: string
  status: 'active' | 'paused' | 'cancelled'
  target: string // agent or group name
  bot_id: string
  group_id: string
  prompt: string
  days: number[] // 0 = Monday
  time: string
  timezone: string
  next_at: number // 0 when none
  occurrences: Occurrence[]
}
export interface ScheduleInput {
  title: string
  prompt: string
  days: number[]
  time: string
  bot_id?: string
  group_id?: string
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
  by_bot: { bot_id: string; name: string; input: number; output: number; total: number; runs: number; cost: Money; estimated: boolean }[]
  turns: { run_id: string; bot_id: string; created_at: number; input: number; output: number; total: number; status: string; cost: Money; estimated: boolean }[]
  cost: Money
  basis: 'measured' | 'estimated'
  estimate_reasons: EstimateReason[]
  month: LimitInfo
}
export interface BotUsage {
  bot_id: string
  name: string
  input: number
  output: number
  total: number
  runs: number
  cost: Money
  estimated: boolean
}
interface Slice {
  cost: Money
  tokens: number
  runs: number
}
// GET /usage without a scope: this month's USD view of the account.
export interface MonthUsage extends LimitInfo {
  currency: 'USD'
  period: { start: string; end: string; timezone: string }
  updated_at: string
  tokens: { input: number; output: number; cache_read: number; total: number; runs: number }
  unpriced_tokens: number
  estimate_reasons: EstimateReason[]
  by_agent: (Slice & { bot_id: string; name: string; estimated: boolean })[]
  by_model: (Slice & { provider: string; model: string; estimated: boolean; priced: boolean })[]
  by_day: (Slice & { day: string })[]
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
  kb?: KbItem[] // Knowledge Base items saved from this message's links (result), shown under the bubble
  kbBusy?: boolean // the message asks to save a link and the BFF is still reading it
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
const toMoney = (r: Raw): Money => ({ usd: asStr(r.usd, '0'), label: asStr(r.label, '$0') })
const toLimits = (r: Raw = {}): Limits => ({
  monthly_usd: r.monthly_usd == null ? null : toMoney(r.monthly_usd),
  group_send_token_budget: r.group_send_token_budget == null ? null : asNum(r.group_send_token_budget),
  max_bots: asNum(r.max_bots),
  max_groups: asNum(r.max_groups),
  max_concurrent_runs: asNum(r.max_concurrent_runs),
})
const toLimitInfo = (u: Raw = {}): LimitInfo => ({
  cost: toMoney(u.cost ?? {}),
  limit: u.limit ? toMoney(u.limit) : null,
  remaining: u.remaining ? toMoney(u.remaining) : null,
  percent: u.percent == null ? null : asNum(u.percent),
  state: u.state === 'warning' || u.state === 'exceeded' ? u.state : 'normal',
  basis: u.basis === 'estimated' ? 'estimated' : 'measured',
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
    usage: {
      tokens_month: asNum(u.tokens_month),
      bots: asNum(u.bots),
      groups: asNum(u.groups),
      active_runs: asNum(u.active_runs),
      ...toLimitInfo(u),
    },
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
    plan: r.plan ? toContentPlan(r.plan) : undefined,
  }
}
const toContentPlan = (p: Raw): ContentPlan => ({
  title: asStr(p.title),
  days: list(p.days).map((d) => ({ date: asStr(d.date), theme: asStr(d.theme), products: list(d.products).map((x) => asStr(x)), brief: asStr(d.brief), time: asStr(d.time, '09:00') })),
  schedule_id: p.schedule_id ? asStr(p.schedule_id) : null,
})
const OCC_STATUS = ['planned', 'running', 'done', 'skipped', 'failed', 'cancelled'] as const
const toSchedule = (r: Raw): Schedule => ({
  id: asStr(r.id),
  kind: r.kind === 'plan' ? 'plan' : 'recurring',
  title: asStr(r.title),
  status: r.status === 'paused' ? 'paused' : r.status === 'cancelled' ? 'cancelled' : 'active',
  target: asStr(r.target),
  bot_id: asStr(r.bot_id),
  group_id: asStr(r.group_id),
  prompt: asStr(r.prompt),
  days: list(r.days).map((d) => asNum(d)),
  time: asStr(r.time),
  timezone: asStr(r.timezone),
  next_at: epoch(r.next_at),
  occurrences: list(r.occurrences).map((o) => ({
    id: asStr(o.id),
    schedule_id: asStr(o.schedule_id),
    planned_at: epoch(o.planned_at),
    title: asStr(o.title),
    brief: asStr(o.brief),
    status: OCC_STATUS.find((t) => t === o.status) ?? 'failed',
    skip_reason: asStr(o.skip_reason),
    agents: list(o.agents).map((x) => asStr(x)),
    run_id: asStr(o.run_id),
    cost: o.cost ? toMoney(o.cost) : null,
    estimated: o.estimated === true,
  })),
})
const KCOL: KanbanColumnId[] = ['todo', 'running', 'blocked', 'done']
const toKanbanCard = (r: Raw): KanbanCard => ({
  key: asStr(r.key),
  source: (['chat', 'group', 'schedule', 'sequence', 'plan', 'hermes'] as const).find((x) => x === r.source) ?? 'chat',
  title: asStr(r.title),
  column: KCOL.find((x) => x === r.column) ?? 'done',
  outcome: (['ok', 'failed', 'cancelled'] as const).find((x) => x === r.outcome) ?? null,
  note: asStr(r.note),
  agents: list(r.agents).map((a) => ({ id: asStr(a.id), name: asStr(a.name), color: asStr(a.color, 'slate') })),
  group: r.group ? { id: asStr(r.group.id), name: asStr(r.group.name) } : null,
  at: epoch(r.at),
  link: asStr(r.link),
  cost: r.cost ? toMoney(r.cost) : null,
  estimated: r.estimated === true,
})
const toKanban = (r: Raw): KanbanBoard => ({
  columns: list(r.columns).map((c) => ({ id: KCOL.find((x) => x === c.id) ?? 'done', label: asStr(c.label), total: asNum(c.total), cards: list(c.cards).map(toKanbanCard) })),
  hermes: { state: (['ok', 'unavailable', 'pending'] as const).find((x) => x === r.hermes?.state) ?? 'unavailable', count: asNum(r.hermes?.count) },
  period: asStr(r.period, '7d'),
})
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
  kbItems: () => call<KbItem[]>('GET', '/kb/items'),
  kbUpload: (file: File) => {
    const f = new FormData()
    f.append('file', file)
    return call<KbItem>('POST', '/kb/files', f)
  },
  kbAddLink: (url: string) => call<KbItem>('POST', '/kb/links', { url }),
  kbDelete: (id: string) => call<void>('DELETE', `/kb/items/${enc(id)}`),
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
  startRun: async (botId: string, input: string, session_id?: string, instructions?: string, ctx?: RunCtx, kb_items?: string[]) => {
    const r = await call<Raw>('POST', `/bots/${enc(botId)}/runs`, { input, ...(kb_items?.length ? { kb_items } : {}), ...(session_id ? { session_id } : {}), ...(instructions ? { instructions } : {}), ...(ctx?.workflow ? { workflow: ctx.workflow, ...(ctx.stage ? { stage: ctx.stage } : {}), ...(ctx.test_mode ? { test_mode: true } : {}) } : {}) })
    return { run: toRun(r.run ?? r), session_id: asStr(r.session_id ?? r.run?.session_id), kb: (Array.isArray(r.kb) ? r.kb : []) as KbItem[] }
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
  sendGroup: async (id: string, text: string, mode: 'queue' | 'steer', kb_items?: string[]) => {
    const r = await call<Raw>('POST', `/groups/${enc(id)}/messages`, { text, mode, ...(kb_items?.length ? { kb_items } : {}) })
    return { message: toGroupMsg(r.message ?? {}), queued: r.queued === true }
  },
  deleteGroup: (id: string) => call<void>('DELETE', `/groups/${enc(id)}`),
  stopGroup: (id: string) => call<void>('POST', `/groups/${enc(id)}/stop`),
  approvePlan: async (gid: string, messageId: string) => toSchedule(await call<Raw>('POST', `/groups/${enc(gid)}/plans/${enc(messageId)}/approve`)),
  revisePlan: (gid: string, messageId: string, feedback: string) => call<void>('POST', `/groups/${enc(gid)}/plans/${enc(messageId)}/revise`, { feedback }),
  kanban: async (f: KanbanFilter) => toKanban(await call<Raw>('GET', `/kanban${q({ ...f })}`)),
  schedules: async () => list(await call('GET', '/schedules')).map(toSchedule),
  createSchedule: async (b: ScheduleInput) => toSchedule(await call<Raw>('POST', '/schedules', b)),
  scheduleAction: async (id: string, what: 'pause' | 'resume' | 'cancel') => toSchedule(await call<Raw>('POST', `/schedules/${enc(id)}/${what}`)),
  deleteSchedule: (id: string) => call<void>('DELETE', `/schedules/${enc(id)}`),
  stopOccurrence: (id: string) => call<void>('POST', `/schedule-occurrences/${enc(id)}/stop`),
  usage: async (s: Scope): Promise<Usage> => {
    const u = await call<Usage>('GET', `/usage${q({ ...s })}`)
    return { ...u, turns: u.turns.map((t) => ({ ...t, created_at: epoch(t.created_at) })) }
  },
  usageMonth: () => call<MonthUsage>('GET', '/usage'),
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
