// Structured results (frontend proposal, to be agreed with backend: docs/sprint3/kebutuhan-api-frontend.md, section
// "Skema hasil terstruktur"). The agent appends one fenced block ```pegawai-result + JSON to its normal answer; we parse it,
// check it with the guards below and draw cards. Nothing here is validated by the backend. On any failure the caller shows
// the plain answer, never invented cards.

export type Cls = 'public_data' | 'research_findings' | 'assumptions' | 'dummy'
export const CLS_LABEL: Record<Cls, string> = { public_data: 'Public Data', research_findings: 'Research Findings', assumptions: 'Assumptions', dummy: 'Dummy/Simulated' }

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
  if (!isObj(x)) return null
  
  // Support both legacy kind: 'cs' and Colorbox CS v2.1 schema
  const draft = str(x.customer_reply_draft || x.draft)
  if (!draft) return null

  // Priority mapping: support P0, P1, P2, P3 as well as rendah, sedang, tinggi
  const rawPrio = str(x.priority).toUpperCase()
  let p: Priority = 'sedang'
  if (rawPrio === 'P0' || rawPrio === 'P1' || rawPrio.toLowerCase() === 'tinggi') {
    p = 'tinggi'
  } else if (rawPrio === 'P2' || rawPrio.toLowerCase() === 'sedang') {
    p = 'sedang'
  } else if (rawPrio === 'P3' || rawPrio.toLowerCase() === 'rendah') {
    p = 'rendah'
  }

  // Escalation: support { recommended, reason } and { escalate, escalation_reason }
  let escalate = false
  let escalationReason = ''
  if (typeof x.escalate === 'boolean') {
    escalate = x.escalate
    escalationReason = str(x.escalation_reason)
  } else if (isObj(x.escalation)) {
    escalate = Boolean(x.escalation.recommended)
    escalationReason = str(x.escalation.reason)
  }

  // Classification / Primary Intent
  const classification = str(x.primary_intent || x.classification || x.intent)

  // Simulation
  let simulated = false
  if (x.simulated === true) {
    simulated = true
  } else if (isObj(x.simulation)) {
    simulated = Boolean(x.simulation.is_simulated)
  }

  // Sources / Knowledge refs
  let sources: Source[] = []
  if (Array.isArray(x.sources)) {
    sources = x.sources.map((s) => (isObj(s) ? { ref: str(s.ref ?? s.title ?? s.name), excerpt: str(s.excerpt), classification: cls(s.classification) } : { ref: str(s), excerpt: '' })).filter((s) => s.ref)
  } else if (Array.isArray(x.knowledge_refs)) {
    sources = x.knowledge_refs.map((k) => (isObj(k) ? { ref: str(k.knowledge_id || k.source_url), excerpt: str(k.used_for || k.source_url), classification: 'public_data' as Cls } : { ref: str(k), excerpt: '' })).filter((s) => s.ref)
  }

  // Summary & Context notes
  let summary = str(x.summary)
  let contextNotes = str(x.context_notes)
  if (isObj(x.ticket_summary)) {
    const ts = x.ticket_summary
    if (!summary) summary = str(ts.issue || '')
    if (!contextNotes) {
      const parts: string[] = []
      if (Array.isArray(ts.customer_reported_facts) && ts.customer_reported_facts.length) {
        parts.push(`Pelanggan: ${ts.customer_reported_facts.join('; ')}`)
      }
      if (Array.isArray(ts.publicly_verified_facts) && ts.publicly_verified_facts.length) {
        parts.push(`Verifikasi: ${ts.publicly_verified_facts.join('; ')}`)
      }
      if (Array.isArray(ts.unknowns) && ts.unknowns.length) {
        parts.push(`Unknown: ${ts.unknowns.join('; ')}`)
      }
      contextNotes = parts.join('\n')
    }
  }

  return {
    kind: 'cs',
    inquiry: str(x.inquiry),
    classification,
    sources,
    draft,
    context_notes: contextNotes,
    summary,
    priority: p,
    escalate,
    escalation_reason: escalationReason,
    simulated,
  }
}

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

// ---- instructions sent with the run (BFF -> Hermes /v1/runs `instructions`) ----
const HEAD = 'Jawab seperti biasa dalam bahasa Indonesia. Di akhir jawaban, tambahkan tepat satu blok kode berpagar dengan label pegawai-result berisi JSON valid (tanpa komentar, tanpa koma sisa) dengan bentuk ini. Isi semua teks dalam bahasa Indonesia. Kolom classification salah satu dari public_data, research_findings, assumptions, dummy. Jangan menaruh teks apa pun setelah blok itu.\n'
const SHAPES: Record<MarketingKind | 'cs', string> = {
  brief: '{"kind":"brief","fields":{"tujuan":"","produk":"","kanal":"","tipe_konten":"","jumlah_output":"","audiens":"","nada":"","pesan_kunci":"","cta":""},"assumptions":[""],"questions":[""],"ready":true}\n"ready" true hanya jika brief cukup untuk dikerjakan; jika tidak, isi questions.',
  plan: '{"kind":"plan","creative_brief":"","ideas":[{"title":"","reason":"","classification":"assumptions"}],"calendar":[{"date":"","channel":"","type":"","idea":"","message":"","cta":""}]}',
  content: '{"kind":"content","type":"caption","items":[{"text":"","alt_angle":"","classification":"assumptions"}],"sources":[""],"assumptions":[""],"warnings":[""]}\nSatu item per opsi. sources memuat sumber klaim; kosongkan jika tidak ada dan tulis di warnings.',
  review: '{"kind":"review","findings":[""],"evidence":[""],"recommendations":[""],"scores":{"accuracy":1,"relevance":1,"brand":1,"consistency":1,"knowledge":1,"instruction":1,"completeness":1,"error_handling":1,"human_review":1}}\nSkor bilangan bulat 1 sampai 5 untuk setiap dimensi.',
  revision: '{"kind":"revision","before":"","after":"","feedback_applied":[""],"change_log":[""],"open_issues":[""]}\nbefore adalah draf lama, after adalah draf baru lengkap.',
  cs: '{"kind":"cs","inquiry":"","classification":"","sources":[{"ref":"","excerpt":""}],"draft":"","context_notes":"","summary":"","priority":"sedang","escalate":false,"escalation_reason":"","simulated":false}\nclassification (tingkat atas): jenis pertanyaan, mis. ukuran, harga, stok, keluhan, retur; bukan kategori data. priority: rendah, sedang, atau tinggi. draft: balasan untuk pelanggan, hanya dari sumber yang ada. simulated true untuk pesanan, retur, dan refund (data simulasi). Jika info tidak ada, katakan tidak tahu dan sarankan eskalasi.',
}
export const instructionsFor = (k: MarketingKind | 'cs') => HEAD + SHAPES[k]
