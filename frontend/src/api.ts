// The only file that knows about the backend contract and its differences from server.py:
// flat error shapes, "success" with a failed run, token_usage vs metrics, timeout code names.
import marketingSample from './mock/marketing.json'
import supportSample from './mock/customer_support.json'
import bannerLocal from './mock/banner_promo_kreatif.png'

export type Department = 'marketing' | 'customer_support'
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export type ErrorKind = 'network' | 'invalid' | 'server' | 'timeout' | 'suspicious'

export class RunError extends Error {
  kind: ErrorKind
  detail?: string
  constructor(kind: ErrorKind, message: string, detail?: string) {
    super(message)
    this.kind = kind
    this.detail = detail
  }
}

export interface Agent {
  id: string
  name: string
  role: string
  content: string
  score?: number
  color?: string
  badge?: string
  imageUrl?: string
}
export interface RunResult {
  agents: Agent[]
  score?: number
  seconds: number
  tokens: number
  model: string
  provider: string
  session: string
  fallback: boolean
}

const CUSTOMER_ID = 'cust_aitt_001'
export const MIN_PROMPT = 5
export const MAX_PROMPT = 4000
// The contract's maximum; a run stopped early still costs the tokens it used.
const RUN_TIMEOUT_SECONDS = 300
const CLIENT_TIMEOUT_MS = 330_000 // above the limit sent to the backend

// Backend returns HTTP 200 "success" even when Hermes was rejected for credentials (known bug).
const CREDENTIAL_REJECTION =
  /api[\s_-]?key|credential|kredensial|unauthori[sz]ed|authentication|invalid (token|key)|\b40[13]\b|not configured/i

/* eslint-disable @typescript-eslint/no-explicit-any */
// Only same-origin images are shown (live: proxied to the backend; sample: the local copy).
function sameOriginImage(v: unknown): string | undefined {
  if (typeof v !== 'string' || !v) return undefined
  try {
    const u = new URL(v, location.href)
    return u.origin === location.origin ? u.href : undefined
  } catch {
    return undefined
  }
}

export function toResult(raw: any): RunResult {
  const fail = (why: string) =>
    new RunError(
      'suspicious',
      'Hasil dari tim tidak bisa dipercaya, jadi tidak kami tampilkan. Coba kirim ulang sebentar lagi.',
      why,
    )
  if (!raw || typeof raw !== 'object') throw new RunError('server', 'Layanan mengirim jawaban yang tidak dikenali.')
  const tokens = Number(raw.token_usage?.total_tokens ?? raw.metrics?.total_tokens ?? 0)
  const output = typeof raw.output === 'string' ? raw.output.trim() : ''
  const agents: Agent[] = (raw.multi_agent_data?.agents ?? []).map((a: any) => ({
    id: String(a.id),
    name: String(a.name),
    role: String(a.role ?? ''),
    content: String(a.content ?? '').replace(/\n{3,}/g, '\n\n').trim(),
    score: typeof a.score === 'number' ? a.score : undefined,
    color: typeof a.color === 'string' ? a.color : undefined,
    badge: typeof a.badge === 'string' ? a.badge : undefined,
    imageUrl: sameOriginImage(a.image_url),
  }))
  if (raw.status !== 'success') throw fail(`status: ${String(raw.status)}`)
  if (!output || agents.length === 0 || agents.every((a) => !a.content)) throw fail('keluaran kosong')
  if (output.length < 1000 && CREDENTIAL_REJECTION.test(output)) throw fail(`keluaran: ${output.slice(0, 160)}`)
  if (!tokens) throw fail('jumlah token kosong')
  return {
    agents,
    score: agents.find((a) => a.score !== undefined)?.score,
    seconds: Number(raw.execution_time_seconds ?? 0),
    tokens,
    model: String(raw.model ?? '-'),
    provider: String(raw.provider ?? '-'),
    session: String(raw.session_id ?? '-'),
    fallback: Boolean(raw.fallback_applied),
  }
}

// Flat shapes seen: {error:"text"}, {status:"error",error_code,message}; contract shape: {error:{code,message}}.
function errorFrom(status: number, body: any): RunError {
  const code = String(body?.error_code ?? body?.error?.code ?? '')
  const text = String(body?.message ?? body?.error?.message ?? (typeof body?.error === 'string' ? body.error : '') ?? '')
  if (status === 504 || code.startsWith('EXECUTION_TIMEOUT'))
    return new RunError('timeout', 'Tim butuh waktu lebih lama dari batas yang ada. Coba lagi, atau persingkat tugasnya.', text)
  if (status === 400) return new RunError('invalid', 'Tugas ditolak oleh layanan. Periksa isinya lalu kirim lagi.', text)
  if (status === 502 || status === 503) return new RunError('network', 'Layanan belum bisa dijangkau. Pastikan backend menyala, lalu coba lagi.', text)
  return new RunError('server', 'Layanan sedang bermasalah. Coba lagi sebentar lagi.', text || code)
}

async function liveRun(department: Department, prompt: string, signal: AbortSignal): Promise<RunResult> {
  let res: Response
  try {
    res = await fetch('/api/v1/agent/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: CUSTOMER_ID,
        department,
        prompt,
        multi_agent: true,
        timeout_seconds: RUN_TIMEOUT_SECONDS,
      }),
      signal: AbortSignal.any([signal, AbortSignal.timeout(CLIENT_TIMEOUT_MS)]),
    })
  } catch (e) {
    if (signal.aborted) throw e
    if ((e as Error).name === 'TimeoutError')
      throw new RunError('timeout', 'Tim butuh waktu lebih lama dari batas yang ada. Coba lagi, atau persingkat tugasnya.')
    throw new RunError('network', 'Tidak bisa terhubung ke layanan. Periksa koneksi Anda, lalu coba lagi.')
  }
  let body: unknown = null
  try {
    body = await res.json()
  } catch {
    /* non-JSON body */
  }
  if (!res.ok) throw errorFrom(res.status, body)
  return toResult(body)
}

// ---- sample adapter (VITE_USE_MOCK=true): real evidence content, same toResult path ----
const samples: Record<Department, any> = { marketing: marketingSample, customer_support: supportSample }
const wait = (ms: number, signal: AbortSignal) =>
  new Promise<void>((resolve, reject) => {
    const t = setTimeout(resolve, ms)
    signal.addEventListener('abort', () => (clearTimeout(t), reject(signal.reason)), { once: true })
  })

// The sample's banner is a local copy of the file the backend serves in live mode.
function sampleBody(department: Department) {
  const base = structuredClone(samples[department])
  base.multi_agent_data.agents.forEach((a: any) => a.image_url && (a.image_url = bannerLocal))
  return base
}
// Sample mode only: lets a review jump straight to the result screen (#hasil, #hasil-cs).
export const sampleResult = (department: Department) => toResult(sampleBody(department))

async function mockRun(department: Department, prompt: string, signal: AbortSignal): Promise<RunResult> {
  await wait(3000, signal)
  // Test triggers so every error path can be driven from the UI in sample mode.
  if (prompt.includes('[uji-jaringan]')) throw new RunError('network', 'Tidak bisa terhubung ke layanan. Periksa koneksi Anda, lalu coba lagi.')
  if (prompt.includes('[uji-400]')) throw errorFrom(400, { error: 'Field prompt is required' })
  if (prompt.includes('[uji-500]')) throw errorFrom(500, { status: 'error', error_code: 'INTERNAL_SERVER_ERROR', message: 'boom' })
  if (prompt.includes('[uji-504]')) throw errorFrom(504, { status: 'error', error_code: 'EXECUTION_TIMEOUT', message: 'melebihi 300 detik' })
  const base = sampleBody(department)
  if (prompt.includes('[uji-rusak]')) {
    const msg = 'Error: API key rejected. Invalid credentials (401) for provider opencode-go.'
    base.output = msg
    base.multi_agent_data.agents.forEach((a: any) => (a.content = msg))
    base.token_usage = { input_tokens: 0, output_tokens: 0, total_tokens: 0 }
  }
  if (prompt.includes('[uji-token]')) base.token_usage = { input_tokens: 0, output_tokens: 0, total_tokens: 0 }
  return toResult(base)
}

export function runTask(department: Department, prompt: string, signal: AbortSignal): Promise<RunResult> {
  return USE_MOCK ? mockRun(department, prompt, signal) : liveRun(department, prompt, signal)
}
