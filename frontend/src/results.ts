// Structured results. Marketing: the agent appends one fenced block ```pegawai-result + JSON to its normal answer; we parse it
// and check it with the guards below (not validated by the backend). CS (v2.1): the BFF validates the JSON and sends it in the
// run's `done` event (docs/sprint3/kontrak-api-bff.md, sections 5 and 6); `toCs21` only normalises it. The old `kind:"cs"`
// block still parses (`toCs`). On any failure the caller shows the plain answer, never invented cards.

export type Cls = 'public_data' | 'research_findings' | 'assumptions' | 'dummy'
export const CLS_LABEL: Record<Cls, string> = { public_data: 'Public Data', research_findings: 'Research Findings', assumptions: 'Assumptions', dummy: 'Dummy/Simulated' }

// Marketing rubric (9 dimensions) and CS rubric (6 criteria, Hub 4.1). Evaluations store scores by key; the two sets share
// accuracy, relevance, brand and knowledge.
export const RUBRIC = [
  { key: 'accuracy', label: 'Akurasi dan keandalan fakta' },
  { key: 'relevance', label: 'Relevansi dan kecocokan audiens' },
  { key: 'brand', label: 'Kesesuaian brand' },
  { key: 'consistency', label: 'Konsistensi' },
  { key: 'knowledge', label: 'Pemakaian knowledge' },
  { key: 'instruction', label: 'Ikuti instruksi dan format' },
  { key: 'completeness', label: 'Kelengkapan dan kejelasan' },
  { key: 'error_handling', label: 'Penanganan error' },
  { key: 'human_review', label: 'Kebutuhan review manusia' },
] as const
export type RubricKey = (typeof RUBRIC)[number]['key']
export const CS_RUBRIC = [
  { key: 'accuracy', label: 'Accuracy: fakta sesuai sumber' },
  { key: 'relevance', label: 'Relevance: menjawab pertanyaan' },
  { key: 'brand', label: 'Brand Alignment: nada dan gaya Colorbox' },
  { key: 'knowledge', label: 'Knowledge Utilization: memakai knowledge yang benar' },
  { key: 'anti_hallucination', label: 'Anti-Hallucination: tidak mengarang' },
  { key: 'escalation', label: 'Escalation: rekomendasi eskalasi tepat' },
] as const
export const ALL_DIMENSIONS: { key: string; label: string }[] = [...RUBRIC, ...CS_RUBRIC.filter((c) => !RUBRIC.some((r) => r.key === c.key))]

export interface Idea { title: string; reason: string; classification?: Cls }
export interface CalRow { date: string; channel: string; type: string; idea: string; message: string; cta: string }
export interface Item { text: string; alt_angle: string; classification?: Cls }
export interface Source { ref: string; excerpt: string; classification?: Cls }

export type MarketingResult =
  | { kind: 'brief'; fields: Record<string, string>; assumptions: string[]; questions: string[]; ready: boolean }
  | { kind: 'plan'; creative_brief: string; ideas: Idea[]; calendar: CalRow[] }
  | { kind: 'content'; type: string; items: Item[]; sources: string[]; assumptions: string[]; warnings: string[] }
  | { kind: 'review'; findings: string[]; evidence: string[]; recommendations: string[]; scores: Partial<Record<RubricKey, number>> }
  | { kind: 'revision'; before: string; after: string; feedback_applied: string[]; change_log: string[]; open_issues: string[] }
export type Priority = 'rendah' | 'sedang' | 'tinggi'
export interface CsResult {
  kind: 'cs'
  inquiry: string
  classification: string
  sources: Source[]
  draft: string
  context_notes: string
  summary: string
  priority: Priority
  escalate: boolean
  escalation_reason: string
  simulated: boolean
}
export type Result = MarketingResult | CsResult

// ---- CS v2.1 (BFF-validated) ----
export const INTENT_LABEL: Record<string, string> = {
  PRODUCT_INFO: 'Info produk', PRODUCT_AVAILABILITY: 'Ketersediaan produk', SIZE_FIT: 'Ukuran dan fit', SHIPPING_DELIVERY: 'Pengiriman', CLICK_COLLECT: 'Click & Collect',
  ORDER_PROCESS: 'Proses pesanan', ORDER_STATUS: 'Status pesanan', COMPLAINT_DAMAGED: 'Keluhan: barang rusak', COMPLAINT_WRONG_ITEM: 'Keluhan: barang salah',
  COMPLAINT_LATE_MISSING: 'Keluhan: terlambat atau hilang', RETURN_REFUND: 'Retur dan refund', PAYMENT: 'Pembayaran', WEBSITE_TECHNICAL: 'Masalah website', OTHER: 'Lainnya', AMBIGUOUS: 'Ambigu',
}
export type P = 'P0' | 'P1' | 'P2' | 'P3'
export interface KnowledgeRef { knowledge_id: string; source_ids: string[]; source_url: string; accessed_date: string; used_for: string }
export interface Cs21 {
  primary_intent: string
  secondary_intents: string[]
  confidence: number
  priority: P
  reply: string
  summary: { issue: string; reported: string[]; verified: string[]; unknowns: string[]; references: string[]; outcome: string; context: string[] }
  refs: KnowledgeRef[]
  clarifying: string
  escalation: { recommended: boolean; reason: string }
  simulation: { simulated: boolean; ids: string[] }
}
export interface Validation { status: 'valid' | 'repaired' | 'invalid' | 'not_applicable'; errors: string[]; attempts?: number }
export interface ContextRef { type: 'knowledge' | 'product' | 'fixture'; id: string; title: string; classification: string; source_id: string; url: string; accessed_date: string }
// What the BFF returns with a run that had a workflow (SSE `done` or run meta).
export interface RunResult { structured: Cs21 | null; validation: Validation | null; refs: ContextRef[] }
export type MarketingKind = MarketingResult['kind']

// ---- guards (they also normalise: a model may send a string where we want a list) ----
type O = Record<string, unknown>
const isObj = (x: unknown): x is O => typeof x === 'object' && x !== null && !Array.isArray(x)
const str = (x: unknown): string => (typeof x === 'string' ? x : typeof x === 'number' ? String(x) : '')
const one = (x: unknown): string => (isObj(x) ? str(x.text ?? x.title ?? x.ref ?? x.name ?? x.question ?? x.change) || JSON.stringify(x) : str(x))
const strs = (x: unknown): string[] => (Array.isArray(x) ? x.map(one).filter(Boolean) : str(x) ? [str(x)] : [])
const cls = (x: unknown): Cls | undefined => {
  const s = str(x).toLowerCase().replace(/[\s/-]+/g, '_')
  if (s.startsWith('public')) return 'public_data'
  if (s.startsWith('research')) return 'research_findings'
  if (s.startsWith('assum')) return 'assumptions'
  if (s.startsWith('dummy') || s.startsWith('simul')) return 'dummy'
  return undefined
}
const arr = (x: unknown): O[] => (Array.isArray(x) ? x.filter(isObj) : [])

export function toMarketing(x: unknown): MarketingResult | null {
  if (!isObj(x)) return null
  switch (x.kind) {
    case 'brief': {
      if (!isObj(x.fields) || typeof x.ready !== 'boolean') return null
      return { kind: 'brief', fields: Object.fromEntries(Object.entries(x.fields).map(([k, v]) => [k, one(v)])), assumptions: strs(x.assumptions), questions: strs(x.questions), ready: x.ready }
    }
    case 'plan': {
      const ideas = Array.isArray(x.ideas) ? x.ideas : []
      const cal = arr(x.calendar)
      if (!str(x.creative_brief) || !ideas.length || !cal.length) return null
      return {
        kind: 'plan',
        creative_brief: str(x.creative_brief),
        ideas: ideas.map((i) => (isObj(i) ? { title: str(i.title ?? i.name), reason: str(i.reason), classification: cls(i.classification) } : { title: str(i), reason: '' })).filter((i) => i.title),
        calendar: cal.map((r) => ({ date: str(r.date), channel: str(r.channel), type: str(r.type), idea: str(r.idea), message: str(r.message), cta: str(r.cta) })),
      }
    }
    case 'content': {
      const items = Array.isArray(x.items) ? x.items : []
      if (!items.length) return null
      return {
        kind: 'content',
        type: str(x.type),
        items: items.map((i) => (isObj(i) ? { text: str(i.text), alt_angle: str(i.alt_angle), classification: cls(i.classification) } : { text: str(i), alt_angle: '' })).filter((i) => i.text),
        sources: strs(x.sources),
        assumptions: strs(x.assumptions),
        warnings: strs(x.warnings),
      }
    }
    case 'review': {
      if (!isObj(x.scores)) return null
      const scores: Partial<Record<RubricKey, number>> = {}
      for (const d of RUBRIC) {
        const v = Number((x.scores as O)[d.key])
        if (Number.isFinite(v) && v >= 1 && v <= 5) scores[d.key] = Math.round(v)
      }
      if (!Object.keys(scores).length) return null
      return { kind: 'review', findings: strs(x.findings), evidence: strs(x.evidence), recommendations: strs(x.recommendations), scores }
    }
    case 'revision': {
      if (!str(x.before) || !str(x.after)) return null
      return { kind: 'revision', before: str(x.before), after: str(x.after), feedback_applied: strs(x.feedback_applied), change_log: strs(x.change_log), open_issues: strs(x.open_issues) }
    }
  }
  return null
}

export function toCs(x: unknown): CsResult | null {
  if (!isObj(x) || x.kind !== 'cs' || !str(x.draft) || typeof x.escalate !== 'boolean') return null
  const p = str(x.priority).toLowerCase()
  if (p !== 'rendah' && p !== 'sedang' && p !== 'tinggi') return null
  return {
    kind: 'cs',
    inquiry: str(x.inquiry),
    classification: str(x.classification ?? x.intent),
    sources: Array.isArray(x.sources) ? x.sources.map((s) => (isObj(s) ? { ref: str(s.ref ?? s.title ?? s.name), excerpt: str(s.excerpt), classification: cls(s.classification) } : { ref: str(s), excerpt: '' })).filter((s) => s.ref) : [],
    draft: str(x.draft),
    context_notes: str(x.context_notes),
    summary: str(x.summary),
    priority: p,
    escalate: x.escalate,
    escalation_reason: str(x.escalation_reason),
    simulated: x.simulated === true,
  }
}

export function toCs21(x: unknown): Cs21 | null {
  if (!isObj(x) || !str(x.primary_intent) || !str(x.priority) || !str(x.customer_reply_draft)) return null
  const pr = str(x.priority).toUpperCase()
  if (pr !== 'P0' && pr !== 'P1' && pr !== 'P2' && pr !== 'P3') return null
  const ts = isObj(x.ticket_summary) ? x.ticket_summary : {}
  const es = isObj(x.escalation) ? x.escalation : {}
  const sim = isObj(x.simulation) ? x.simulation : {}
  const nz = (v: unknown) => (v === null || v === undefined ? '' : str(v))
  return {
    primary_intent: str(x.primary_intent),
    secondary_intents: strs(x.secondary_intents),
    confidence: Number.isFinite(Number(x.classification_confidence)) ? Number(x.classification_confidence) : 0,
    priority: pr,
    reply: str(x.customer_reply_draft),
    summary: { issue: str(ts.issue), reported: strs(ts.customer_reported_facts), verified: strs(ts.publicly_verified_facts), unknowns: strs(ts.unknowns), references: strs(ts.customer_provided_references), outcome: nz(ts.requested_outcome), context: strs(ts.context_retained) },
    refs: arr(x.knowledge_refs).map((k) => ({ knowledge_id: str(k.knowledge_id), source_ids: strs(k.source_ids), source_url: nz(k.source_url), accessed_date: nz(k.accessed_date), used_for: str(k.used_for) })),
    clarifying: nz(x.clarifying_question),
    escalation: { recommended: es.recommended === true, reason: nz(es.reason) },
    simulation: { simulated: sim.is_simulated === true, ids: strs(sim.scenario_ids) },
  }
}
export function toValidation(x: unknown): Validation | null {
  if (!isObj(x)) return null
  const s = str(x.status)
  if (s !== 'valid' && s !== 'repaired' && s !== 'invalid' && s !== 'not_applicable') return null
  const a = Number(x.attempts)
  return { status: s, errors: strs(x.errors), attempts: x.attempts !== undefined && Number.isFinite(a) ? a : undefined }
}
export const toRefs = (x: unknown): ContextRef[] =>
  arr(x).map((r) => ({ type: r.type === 'product' || r.type === 'fixture' ? r.type : 'knowledge', id: str(r.id), title: str(r.title), classification: str(r.classification), source_id: str(r.source_id), url: str(r.url), accessed_date: str(r.accessed_date) }))
// The `done` frame (structured, validation, context_refs) and the run detail (same keys inside `meta`) have the same shape.
export const toRunResult = (d: unknown): RunResult => (isObj(d) ? { structured: toCs21(d.structured), validation: toValidation(d.validation), refs: toRefs(d.context_refs) } : { structured: null, validation: null, refs: [] })

export const isMarketingResult = (x: unknown): x is MarketingResult => toMarketing(x) !== null
export const isCsResult = (x: unknown): x is CsResult => toCs(x) !== null

// ---- extraction ----
export type Parsed<T> = { text: string; result: T | null; state: 'none' | 'ok' | 'bad'; raw: string }
const FENCE = /```pegawai-result[^\S\n]*\n?([\s\S]*?)(?:```|$)/

function extract<T>(answer: string, conv: (x: unknown) => T | null): Parsed<T> {
  const m = FENCE.exec(answer)
  if (!m) return { text: answer.trim(), result: null, state: 'none', raw: '' }
  const text = (answer.slice(0, m.index) + answer.slice(m.index + m[0].length)).trim()
  let result: T | null = null
  try {
    result = conv(JSON.parse(m[1].trim()))
  } catch {
    result = null
  }
  return { text, result, state: result ? 'ok' : 'bad', raw: m[1] }
}
export const parseMarketing = (a: string, want?: MarketingKind): Parsed<MarketingResult> => {
  const p = extract(a, toMarketing)
  return want && p.result && p.result.kind !== want ? { ...p, result: null, state: 'bad' } : p
}
export const parseCs = (a: string): Parsed<CsResult> => extract(a, toCs)
// While streaming: hide the block (even half-written) from the visible answer.
export const stripBlock = (a: string) => a.replace(/```pegawai-result[\s\S]*$/, '').replace(/```pegawai-result[\s\S]*?```/g, '').trim()

// ---- instructions sent with the run (Marketing only; the BFF builds the CS v2.1 instructions) ----
const HEAD = 'Jawab seperti biasa dalam bahasa Indonesia. Di akhir jawaban, tambahkan tepat satu blok kode berpagar dengan label pegawai-result berisi JSON valid (tanpa komentar, tanpa koma sisa) dengan bentuk ini. Isi semua teks dalam bahasa Indonesia. Kolom classification salah satu dari public_data, research_findings, assumptions, dummy. Jangan menaruh teks apa pun setelah blok itu.\n'
const SHAPES: Record<MarketingKind, string> = {
  brief: '{"kind":"brief","fields":{"tujuan":"","produk":"","kanal":"","tipe_konten":"","jumlah_output":"","audiens":"","nada":"","pesan_kunci":"","cta":""},"assumptions":[""],"questions":[""],"ready":true}\n"ready" true hanya jika brief cukup untuk dikerjakan; jika tidak, isi questions.',
  plan: '{"kind":"plan","creative_brief":"","ideas":[{"title":"","reason":"","classification":"assumptions"}],"calendar":[{"date":"","channel":"","type":"","idea":"","message":"","cta":""}]}',
  content: '{"kind":"content","type":"caption","items":[{"text":"","alt_angle":"","classification":"assumptions"}],"sources":[""],"assumptions":[""],"warnings":[""]}\nSatu item per opsi. sources memuat sumber klaim; kosongkan jika tidak ada dan tulis di warnings.',
  review: '{"kind":"review","findings":[""],"evidence":[""],"recommendations":[""],"scores":{"accuracy":1,"relevance":1,"brand":1,"consistency":1,"knowledge":1,"instruction":1,"completeness":1,"error_handling":1,"human_review":1}}\nSkor bilangan bulat 1 sampai 5 untuk setiap dimensi.',
  revision: '{"kind":"revision","before":"","after":"","feedback_applied":[""],"change_log":[""],"open_issues":[""]}\nbefore adalah draf lama, after adalah draf baru lengkap.',
}
export const instructionsFor = (k: MarketingKind) => HEAD + SHAPES[k]

// ---- partial CS reply while the JSON is still streaming ----
// Start of the last JSON object in a stream: skips leading text and a ```json fence. After a complete object, a later "{" is a new
// attempt (the automatic repair retry), so the failed first attempt is dropped.
function lastObjectStart(t: string): number {
  let i = t.indexOf('{')
  if (i < 0) return -1
  for (;;) {
    let depth = 0
    let str = false
    let esc = false
    let end = -1
    for (let j = i; j < t.length && end < 0; j++) {
      const c = t[j]
      if (str) {
        if (esc) esc = false
        else if (c === '\\') esc = true
        else if (c === '"') str = false
      } else if (c === '"') str = true
      else if (c === '{') depth++
      else if (c === '}' && --depth === 0) end = j
    }
    const next = end < 0 ? -1 : t.indexOf('{', end + 1)
    if (next < 0) return i
    i = next
  }
}

const ESC: Record<string, string> = { '"': '"', '\\': '\\', '/': '/', n: '\n', r: '\r', t: '\t', b: '\b', f: '\f' }
// Reads a JSON string body starting after its opening quote. `closed` is false when the text ends inside the string.
function readString(t: string, from: number): { value: string; end: number; closed: boolean } {
  let out = ''
  for (let i = from; i < t.length; i++) {
    const c = t[i]
    if (c === '"') return { value: out, end: i, closed: true }
    if (c !== '\\') {
      out += c
      continue
    }
    const n = t[i + 1]
    if (n === undefined) break // lone backslash at the end: wait for the next chunk
    if (n === 'u') {
      const hex = t.slice(i + 2, i + 6)
      if (!/^[0-9a-fA-F]{4}$/.test(hex)) break
      out += String.fromCharCode(parseInt(hex, 16))
      i += 5
    } else {
      out += ESC[n] ?? n
      i++
    }
  }
  return { value: out.replace(/[\uD800-\uDBFF]$/, ''), end: t.length, closed: false } // never show half a surrogate pair
}

// The growing value of "customer_reply_draft" (top-level key) from incomplete CS JSON. null = key not seen yet (or not a string).
export function partialReplyDraft(text: string): string | null {
  const start = lastObjectStart(text)
  if (start < 0) return null
  let depth = 0
  for (let i = start; i < text.length; i++) {
    const c = text[i]
    if (c === '{' || c === '[') depth++
    else if (c === '}' || c === ']') depth--
    else if (c === '"') {
      const s = readString(text, i + 1)
      if (!s.closed) return null
      i = s.end
      if (depth !== 1 || s.value !== 'customer_reply_draft') continue
      const m = /^\s*:\s*"/.exec(text.slice(i + 1))
      return m ? readString(text, i + 1 + m[0].length).value : null
    }
  }
  return null
}
