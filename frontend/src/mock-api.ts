// DEV ONLY. Sample answers for the endpoints the BFF does not have yet, plus small decorations on real
// replies so the new cards can be built before the backend lands. Reached through bff.ts only when
// `npm run dev:mock` sets VITE_MOCK_API=1; a production build folds that check to false and drops this module.
//
// Console: __mock.set('ai','ok'), __mock.get(), __mock.reset(), __mock.latency(1500)

import { ApiError, asNum, asStr } from './bff'
import type { Raw } from './bff'
import { csvBlob, MockAssetError, pdfBlob, pngBlob, textBlob, wavBlob, webmBlob, zipLikeBlob } from './mock-assets'

export const MOCK_MARK = '__PA_MOCK__'
if (import.meta.env.PROD) throw new Error('mock-api tidak boleh ada di build produksi')

const KEY = 'pa.mock'
const LATENCY_KEY = 'pa.mock.latency'
const DEMO_KEY = 'pa.mock.demo'
const SOCIAL_KEY = 'pa.mock.social'
const HV_KEY = 'pa.mock.handover'
const FRESH_KEY = 'pa.mock.fresh'

const DEFAULTS: Record<string, string> = {
  attachments: 'ok', // ok | empty | gone | slow | huge
  artifactLink: 'on', // on | off
  skills: 'list', // list | empty | full | staff | fail | slowscan
  ai: 'none', // none | ok | invalid | fail | keyreject
  telegram: 'none', // none | pending | connected | error | fail
  telegramExpiry: '600', // seconds
  telegramConfirm: 'confirm', // never: the bot never finishes pairing
  instagram: 'disconnected', // disconnected | connected | personal | reconnect | broken | notconfigured
  canva: 'disconnected', // same, without personal
  posts: 'mixed', // mixed | empty | publishing
  publish: 'ok', // ok | fail
  output: 'many', // many | few | empty | fail | slow
  whatsapp: 'real', // real | ready | notconfigured | error | fail
  handover: 'queue', // queue | empty | fail
  handoverPing: 'off', // off | auto
  a2a: 'on', // on | off
  onboarding: 'off', // off | fresh | limit
  templates: 'real', // real | sample | few | fail
}

function scenarios(): Record<string, string> {
  try {
    return { ...DEFAULTS, ...(JSON.parse(localStorage.getItem(KEY) ?? '{}') as Record<string, string>) }
  } catch {
    return { ...DEFAULTS }
  }
}
const sc = (k: string) => scenarios()[k] ?? DEFAULTS[k]

function latency(): number {
  const raw = localStorage.getItem(LATENCY_KEY)
  const n = Number(raw)
  return raw != null && Number.isFinite(n) ? Math.max(0, n) : 400
}

async function wait(ms = latency()): Promise<void> {
  if (!ms) return
  await new Promise<void>((resolve) => window.setTimeout(resolve, ms))
}

// A quiet badge, so sample data is never mistaken for real data.
function mountBadge() {
  if (typeof document === 'undefined' || document.getElementById('pa-mock-badge')) return
  const el = document.createElement('div')
  el.id = 'pa-mock-badge'
  el.dataset.mock = MOCK_MARK
  el.setAttribute('role', 'status')
  el.textContent = 'Mode contoh: data palsu'
  Object.assign(el.style, {
    position: 'fixed',
    left: '12px',
    bottom: '12px',
    zIndex: '50',
    padding: '4px 10px',
    borderRadius: '999px',
    font: '600 12px var(--font)',
    background: 'var(--st-wait-bg)',
    color: 'var(--st-wait-ink)',
    pointerEvents: 'none',
  } satisfies Partial<CSSStyleDeclaration>)
  document.body.append(el)
}

declare global {
  interface Window {
    __mock?: {
      set: (key: string, value: string) => void
      get: () => Record<string, string>
      reset: () => void
      latency: (ms: number) => void
      emit: (kind: 'handover') => void
    }
  }
}

if (typeof window !== 'undefined') {
  window.__mock = {
    set(key, value) {
      const all = scenarios()
      all[key] = value
      localStorage.setItem(KEY, JSON.stringify(all))
    },
    get: () => scenarios(),
    reset() {
      localStorage.removeItem(KEY)
      localStorage.removeItem(LATENCY_KEY)
      localStorage.removeItem(HV_KEY)
      localStorage.removeItem(FRESH_KEY)
    },
    latency(ms) {
      localStorage.setItem(LATENCY_KEY, String(Math.max(0, ms)))
    },
    emit(kind) {
      if (kind === 'handover') pingHandover()
    },
  }
  mountBadge()
}

// ---- sample artifacts ----
type Att = {
  id: string
  name: string
  mime: string
  bytes: number
  width?: number
  height?: number
  duration_ms?: number
  url: string
  thumb_url?: string
}

const img = (id: string, name: string, w: number, h: number, bytes: number): Att => ({ id, name, mime: 'image/png', bytes, width: w, height: h, url: `/api/artifacts/${id}` })
const video = (id: string, name: string, w: number, h: number, bytes: number, ms: number): Att => ({ id, name, mime: 'video/webm', bytes, width: w, height: h, duration_ms: ms, url: `/api/artifacts/${id}`, thumb_url: `/api/artifacts/${id}?thumb=1` })

const A = {
  img1: img('mock-img-1080', 'gambar-carousel-1.png', 1080, 1350, 1_240_000),
  img2: img('mock-img-square', 'gambar-produk-square.png', 1080, 1080, 820_000),
  img3: img('mock-img-portrait', 'gambar-carousel-2.png', 1080, 1350, 1_100_000),
  img4: img('mock-img-wide', 'gambar-banner.png', 1920, 1080, 1_600_000),
  broken: img('mock-img-rusak', 'gambar-rusak.png', 1080, 1350, 900_000),
  video: video('mock-video-contoh', 'video-produk.webm', 1280, 720, 1_900_000, 2000),
  huge: video('mock-video-besar', 'video-panjang.webm', 1920, 1080, 94_371_840, 90_000),
  audio: { id: 'mock-audio-contoh', name: 'sapaan-suara.wav', mime: 'audio/wav', bytes: 64_044, duration_ms: 2000, url: '/api/artifacts/mock-audio-contoh' },
  pdf: { id: 'mock-pdf-katalog', name: 'katalog-produk.pdf', mime: 'application/pdf', bytes: 246_000, url: '/api/artifacts/mock-pdf-katalog' },
  docx: { id: 'mock-docx-sop', name: 'sop-pelanggan.docx', mime: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', bytes: 48_000, url: '/api/artifacts/mock-docx-sop' },
  csv: { id: 'mock-csv-stok', name: 'stok-november.csv', mime: 'text/csv', bytes: 1_900, url: '/api/artifacts/mock-csv-stok' },
  xlsx: { id: 'mock-xlsx-stok', name: 'stok-november.xlsx', mime: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', bytes: 15_000, url: '/api/artifacts/mock-xlsx-stok' },
} satisfies Record<string, Att>

const CATALOG: Record<string, Att> = Object.fromEntries(Object.values(A).map((a) => [a.id, a]))

function attById(id: string): Att | undefined {
  return CATALOG[id]
}

function atts(ids: string[]): Att[] {
  return ids.map((id) => CATALOG[id]).filter((a): a is Att => !!a)
}

// ---- sample outputs (K1): 30 files in 3 agents, registered in CATALOG so mockBlob can serve them ----
type OutAtt = Att & { bot_id: string; created_at: string; session_id?: string; group_id?: string; task_id?: string; run_id?: string }
type OutKind = 'image' | 'video' | 'audio' | 'document' | 'table'

// The kind cycle is fixed (15 images, 6 documents, 3 tables, 3 videos, 3 voices); the names are drawn from
// per-kind lists so an extension always matches its file kind.
const OUT_PATTERN: OutKind[] = ['image', 'image', 'document', 'image', 'table', 'video', 'image', 'audio', 'document', 'image']
const OUT_NAMES: Record<OutKind, string[]> = {
  image: ['poster-promo-november.png', 'foto-produk-jaket.png', 'banner-akhir-pekan.png', 'carousel-slide-1.png', 'kartu-ucapan.png', 'thumbnail-reels.png'],
  document: ['katalog-koleksi.pdf', 'sop-retur.docx'],
  table: ['stok-gudang.csv', 'laporan-penjualan.xlsx'],
  video: ['video-unboxing.webm'],
  audio: ['sapaan-pelanggan.wav'],
}
const OUT_MIME: Record<string, string> = {
  png: 'image/png',
  pdf: 'application/pdf',
  csv: 'text/csv',
  webm: 'video/webm',
  wav: 'audio/wav',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}

const outKind = (mime: string): OutKind => (mime.startsWith('image/') ? 'image' : mime.startsWith('video/') ? 'video' : mime.startsWith('audio/') ? 'audio' : mime === 'text/csv' || /spreadsheetml/.test(mime) ? 'table' : 'document')

function buildOutputs(): OutAtt[] {
  const now = Date.now()
  const midnight = new Date(now)
  midnight.setHours(0, 0, 0, 0)
  const names = Object.fromEntries(Object.entries(OUT_NAMES).map(([k, v]) => [k, [...v]])) as Record<OutKind, string[]>
  const used: Record<OutKind, number> = { image: 0, video: 0, audio: 0, document: 0, table: 0 }
  const out: OutAtt[] = []
  for (let i = 0; i < 30; i++) {
    const n = i + 1
    const kind = OUT_PATTERN[i % OUT_PATTERN.length]
    const pool = names[kind]
    const name = pool[used[kind]++ % pool.length]
    const ext = name.split('.').pop() ?? ''
    const mime = OUT_MIME[ext] ?? 'application/octet-stream'
    // 4 today (40 minutes apart), 6 yesterday, the rest 2 to 9 days back, always newest first.
    const at = i < 4 ? now - i * 40 * 60_000 : i < 10 ? midnight.getTime() - (2 + (i - 4) * 2) * 3_600_000 : midnight.getTime() - (2 + Math.floor((i - 10) / 3)) * 86_400_000 - ((i - 10) % 3) * 600_000
    const file: OutAtt = {
      id: `mock-out-${String(n).padStart(2, '0')}`,
      name,
      mime,
      bytes: Math.round(40_960 + ((i * 7919) % 1_000) * 3_104),
      url: `/api/artifacts/mock-out-${String(n).padStart(2, '0')}`,
      bot_id: ['siti', 'rian', 'budi'][i % 3],
      created_at: new Date(at).toISOString(),
    }
    if (kind === 'image') {
      const sizes: [number, number][] = [
        [1080, 1080],
        [1080, 1350],
        [1920, 1080],
      ]
      const [w, h] = sizes[(used.image - 1) % sizes.length]
      file.width = w
      file.height = h
    }
    if (kind === 'video' || kind === 'audio') file.duration_ms = kind === 'video' ? 12_000 : 2_000
    if (n % 2 === 0) file.session_id = 'mock-sess-1'
    if (n % 7 === 0) file.group_id = 'mock-grp-1'
    if (n % 11 === 0) file.task_id = 'mock-task-1'
    out.push(file)
  }
  return out
}

const OUT = buildOutputs()
for (const o of OUT) CATALOG[o.id] = o

function outCounts(items: OutAtt[]): Record<OutKind, number> {
  const counts: Record<OutKind, number> = { image: 0, video: 0, audio: 0, document: 0, table: 0 }
  for (const o of items) counts[outKind(o.mime)]++
  return counts
}

const DEMO: Record<string, string[]> = {
  gambar: [A.img1.id],
  galeri: [A.img1.id, A.img2.id, A.img3.id, A.img4.id],
  video: [A.video.id],
  'video besar': [A.huge.id],
  suara: [A.audio.id],
  dokumen: [A.pdf.id, A.docx.id],
  tabel: [A.csv.id, A.xlsx.id],
  semua: [A.img1.id, A.img2.id, A.video.id, A.audio.id, A.csv.id, A.pdf.id],
  rusak: [A.broken.id],
  posting: [A.img1.id, A.img2.id, A.img3.id],
  'posting panjang': [A.img1.id, A.img2.id, A.img3.id],
}

const DEMO_TEXT: Record<string, string> = {
  gambar: 'Ini gambar yang Anda minta. Ukurannya 1080 × 1350 piksel, siap dipakai untuk postingan.',
  galeri: 'Empat gambar sudah siap. Ukurannya campur 1:1, 4:5, dan 16:9 untuk carousel.',
  video: 'Video pendeknya sudah jadi. Durasi 2 detik, ukuran 16:9.',
  'video besar': 'Video panjangnya sudah jadi (90 MB). Terlalu besar untuk diputar di sini, silakan unduh.',
  suara: 'Sapaan suaranya sudah siap. Durasi 2 detik.',
  dokumen: 'Katalog PDF dan dokumen SOP sudah siap. Keduanya bisa diunduh.',
  tabel: 'Tabel stoknya sudah siap. Ada 12 baris dan 5 kolom.',
  semua: 'Semua contoh hasil sudah siap: gambar, video, suara, tabel, dan dokumen.',
  rusak: 'Ini contoh berkas yang sudah tidak tersedia. Kartunya menjelaskan keadaannya.',
  posting: 'Draf postingan siap. Silakan setujui di kartu.',
  'posting panjang': 'Draf postingan siap. Silakan setujui di kartu.',
}

// ---- persisted demo sessions (so a reload can show the same conversation) ----
interface DemoSession {
  id: string
  run_id: string
  bot_id: string
  input: string
  output: string
  attachment_ids: string[]
  created_at: number
}

function demoStore(): { n: number; sessions: DemoSession[] } {
  try {
    const raw = JSON.parse(localStorage.getItem(DEMO_KEY) ?? '{}') as Partial<{ n: number; sessions: DemoSession[] }>
    return { n: asNum(raw.n), sessions: Array.isArray(raw.sessions) ? raw.sessions : [] }
  } catch {
    return { n: 0, sessions: [] }
  }
}

function saveDemo(store: { n: number; sessions: DemoSession[] }) {
  localStorage.setItem(DEMO_KEY, JSON.stringify({ n: store.n, sessions: store.sessions.slice(-20) }))
}

function demoSession(sid: string): DemoSession | undefined {
  return demoStore().sessions.find((s) => s.id === sid)
}

// ---- social approval demo ----
interface SocialDemo {
  caption: string
  ids: string[]
  bot_id: string
  session_id: string
  created_at: number
  approved_at: number
  rejected_at: number
}

function socialDemo(): SocialDemo | null {
  try {
    const x = JSON.parse(localStorage.getItem(SOCIAL_KEY) ?? 'null') as SocialDemo | null
    return x && Array.isArray(x.ids) ? x : null
  } catch {
    return null
  }
}
function saveSocial(x: SocialDemo | null) {
  if (x) localStorage.setItem(SOCIAL_KEY, JSON.stringify(x))
  else localStorage.removeItem(SOCIAL_KEY)
}

function captionShort(): string {
  const base = [
    'Rapi tanpa ribet, nyaman sepanjang hari. Koleksi terbaru Colorbox hadir dengan potongan yang jatuh pas di badan dan bahan yang adem dipakai dari pagi sampai malam.',
    'Padukan dengan sepatu favoritmu atau sendal kulit untuk gaya yang lebih santai. Tersedia dalam beberapa warna netral yang mudah dipadukan.',
    'Cek koleksinya di colorbox.co.id dan temukan padu padan yang cocok untukmu.',
  ]
  return base.join('\n\n')
}
function captionLong(): string {
  const one = captionShort()
  let out = ''
  while (out.length < 2340) out += (out ? '\n\n' : '') + one
  return out.slice(0, 2340)
}

// ---- handover (K3): five sample WhatsApp conversations; state and takeover survive a reload ----
interface HvSaved {
  state?: string
  reason?: string
  taken_by?: string
  resume_at?: number
  log?: { text: string; at: number }[]
}
type HvStore = Record<string, HvSaved>

function hvStore(): HvStore {
  try {
    const raw = JSON.parse(localStorage.getItem(HV_KEY) ?? '{}') as unknown
    return raw && typeof raw === 'object' ? (raw as HvStore) : {}
  } catch {
    return {}
  }
}

function saveHv(s: HvStore) {
  localStorage.setItem(HV_KEY, JSON.stringify(s))
}

function setConvState(id: string, patch: HvSaved) {
  const s = hvStore()
  s[id] = { ...s[id], ...patch }
  saveHv(s)
}

function pushConvLog(id: string, text: string) {
  const s = hvStore()
  s[id] = { ...s[id], log: [...(s[id]?.log ?? []), { text, at: Math.floor(Date.now() / 1000) }] }
  saveHv(s)
}

interface HvSeed {
  id: string
  customer: string
  phone: string
  state: string
  reason: string
  taken: string
  last: string
  age: number // seconds since the last message
  resume: number // seconds from now while a human has it
}
const HV_SEEDS: HvSeed[] = [
  { id: 'mock-conv-1', customer: 'Dewi Lestari', phone: '4821', state: 'needs_human', reason: 'asked_human', taken: '', last: 'Aku mau bicara dengan CS asli, bukan bot.', age: 8 * 60, resume: 0 },
  { id: 'mock-conv-2', customer: 'Budi Santoso', phone: '0937', state: 'human', reason: 'refund', taken: 'Anda', last: 'Baik kak, saya tunggu kabar refund-nya ya.', age: 2 * 3600, resume: 90 * 60 },
  { id: 'mock-conv-3', customer: 'Rina Wijaya', phone: '7710', state: 'bot', reason: '', taken: '', last: 'Kak, ukuran M untuk jaket ini masih ada?', age: 14 * 60, resume: 0 },
  { id: 'mock-conv-4', customer: 'Agus', phone: '1156', state: 'bot', reason: '', taken: '', last: 'Terima kasih, pesanan sudah sampai.', age: 3 * 3600, resume: 0 },
  { id: 'mock-conv-5', customer: 'Maya Putri', phone: '3302', state: 'needs_human', reason: 'complaint', taken: '', last: 'Barangnya cacat, jahitannya lepas semua.', age: 25 * 60, resume: 0 },
]
const HV_FROM = ['customer', 'bot', 'staff', 'system'] as const

// Message scripts: `off` = seconds before the conversation's last message.
const HV_SCRIPTS: Record<string, { from: (typeof HV_FROM)[number]; text: string; off: number }[]> = {
  'mock-conv-1': [
    { from: 'customer', text: 'Selamat sore.', off: 2400 },
    { from: 'bot', text: 'Selamat sore, Kak Dewi. Ada yang bisa saya bantu?', off: 2340 },
    { from: 'customer', text: 'Saya mau tanya soal retur jaket yang saya beli minggu lalu.', off: 1800 },
    { from: 'bot', text: 'Retur bisa dalam 7 hari setelah paket diterima, asal label belum dilepas. Mau saya bantu ajukan?', off: 1740 },
    { from: 'customer', text: 'Aku mau bicara dengan CS asli, bukan bot.', off: 0 },
    { from: 'system', text: 'Siti berhenti membalas. Menunggu manusia.', off: 0 },
  ],
  'mock-conv-2': [
    { from: 'customer', text: 'Halo kak, pesanan saya belum sampai.', off: 7200 },
    { from: 'bot', text: 'Halo Kak Budi. Nomor pesanan berapa?', off: 7140 },
    { from: 'customer', text: 'PSN-8871.', off: 6900 },
    { from: 'customer', text: 'Saya mau minta refund saja.', off: 6600 },
    { from: 'system', text: 'Pelanggan minta pengembalian uang.', off: 6580 },
    { from: 'staff', text: 'Halo kak Budi, saya Anda dari tim CS. Refund sedang kami proses.', off: 4200 },
    { from: 'staff', text: 'Dana akan masuk 3–5 hari kerja. Kami kabari lagi bila sudah selesai.', off: 1800 },
    { from: 'customer', text: 'Baik kak, saya tunggu kabar refund-nya ya.', off: 0 },
  ],
  'mock-conv-3': [
    { from: 'customer', text: 'Halo, saya lihat postingan jaketnya.', off: 5400 },
    { from: 'bot', text: 'Halo Kak Rina, terima kasih sudah mampir.', off: 5350 },
    { from: 'customer', text: 'Selamat pagi.', off: 4800 },
    { from: 'bot', text: 'Selamat pagi, Kak Rina.', off: 4740 },
    { from: 'customer', text: 'Jaket koleksi November masih ada?', off: 600 },
    { from: 'bot', text: 'Masih ada, Kak. Warnanya biru, hitam, dan krem.', off: 540 },
    { from: 'customer', text: 'Kak, ukuran M untuk jaket ini masih ada?', off: 0 },
  ],
  'mock-conv-4': [
    { from: 'customer', text: 'Sore, kak.', off: 7400 },
    { from: 'bot', text: 'Sore, Kak Agus.', off: 7350 },
    { from: 'customer', text: 'Halo, saya mau tanya pesanan saya.', off: 7200 },
    { from: 'bot', text: 'Halo Kak Agus. Nomor pesanan berapa?', off: 7150 },
    { from: 'customer', text: 'PSN-2231.', off: 7100 },
    { from: 'bot', text: 'Pesanan sudah dikirim kemarin dan diperkirakan tiba hari ini.', off: 7000 },
    { from: 'customer', text: 'Terima kasih, pesanan sudah sampai.', off: 0 },
  ],
  'mock-conv-5': [
    { from: 'customer', text: 'Halo, jaket yang saya terima cacat.', off: 3000 },
    { from: 'bot', text: 'Mohon maaf, Kak Maya. Boleh kirim foto bagian yang cacat?', off: 2940 },
    { from: 'customer', text: 'Sudah saya kirim ya.', off: 1800 },
    { from: 'bot', text: 'Terima kasih, fotonya sudah saya lihat. Saya teruskan ke tim layanan pelanggan untuk penukaran.', off: 1740 },
    { from: 'customer', text: 'Barangnya cacat, jahitannya lepas semua.', off: 0 },
    { from: 'system', text: 'Siti berhenti membalas. Menunggu manusia.', off: 0 },
  ],
}

function convMessages(id: string): Raw[] {
  const seed = HV_SEEDS.find((s) => s.id === id)
  if (!seed) return []
  const lastAt = Math.floor(Date.now() / 1000) - seed.age
  const saved = hvStore()[id] ?? {}
  const rows: Raw[] = (HV_SCRIPTS[id] ?? []).map((m, i) => ({
    id: `${id}-m${i + 1}`,
    from: m.from,
    bot_id: m.from === 'bot' ? 'siti' : '',
    text: m.text,
    at: new Date((lastAt - m.off) * 1000).toISOString(),
  }))
  for (const [k, entry] of (saved.log ?? []).entries()) {
    rows.push({ id: `${id}-log${k + 1}`, from: 'system', bot_id: '', text: entry.text, at: new Date(entry.at * 1000).toISOString() })
  }
  return rows.sort((a, b) => Date.parse(a.at) - Date.parse(b.at))
}

function convRows(): Raw[] {
  const saved = hvStore()
  const now = Math.floor(Date.now() / 1000)
  return HV_SEEDS.map((s) => {
    const o = saved[s.id] ?? {}
    const state = o.state ?? s.state
    const resume = o.resume_at != null ? o.resume_at : s.resume ? now + s.resume : 0
    const lastAt = now - s.age
    return {
      id: s.id,
      channel: 'whatsapp',
      customer: s.customer,
      phone_tail: s.phone,
      bot_id: 'siti',
      state,
      reason: o.reason ?? s.reason,
      taken_by: o.taken_by ?? s.taken,
      resume_at: resume ? new Date(resume * 1000).toISOString() : null,
      last_message: s.last,
      last_at: new Date(lastAt * 1000).toISOString(),
      message_count: convMessages(s.id).length,
      since: new Date(lastAt * 1000).toISOString(),
    }
  })
}

function conversationRow(id: string): Raw | undefined {
  return convRows().find((c) => c.id === id)
}

function convPage(state: string, botId: string, limit: number): Raw {
  const all = convRows()
  const counts = { needs_human: 0, human: 0, bot: 0 }
  for (const c of all) {
    if (c.state === 'needs_human') counts.needs_human++
    else if (c.state === 'human') counts.human++
    else counts.bot++
  }
  if (sc('handover') === 'empty') return { items: [], next: null, counts: { needs_human: 0, human: 0, bot: 0 } }
  const wanted = state === 'open' ? ['needs_human', 'human'] : state ? [state] : []
  const items = all
    .filter((c) => (!botId || c.bot_id === botId) && (!wanted.length || wanted.includes(c.state)))
    .sort((a, b) => (a.state === 'needs_human' ? 0 : 1) - (b.state === 'needs_human' ? 0 : 1) || Date.parse(b.last_at) - Date.parse(a.last_at))
  return { items: items.slice(0, limit), next: null, counts }
}

// ---- WhatsApp status (K2): scenario answers and the channels flag on agents ----
function waStatus(): Raw {
  const scenario = sc('whatsapp')
  const base: Raw = {
    channel: 'whatsapp',
    mode: 'business',
    webhook_url: '',
    webhook_verify_token_configured: true,
    api_token_configured: true,
    primary_agent: { id: 'siti', name: 'Siti', role: 'Frontline Support Specialist' },
    escalation_agent: { id: 'hendra', name: 'Hendra', role: 'CS Team Lead & Quality Auditor' },
    total_messages_processed: 128,
    last_activity: new Date(Date.now() - 12 * 60_000).toISOString(),
    eligible_bot_ids: ['siti', 'hendra'],
    agents: [
      { bot_id: 'siti', role: 'primary' },
      { bot_id: 'hendra', role: 'escalation' },
    ],
  }
  if (scenario === 'ready') {
    return { ...base, status: 'ready', number: '+62 812-3456-7890', webhook_url: 'https://contoh.pegawai.ai/bff/api/whatsapp/webhook' }
  }
  if (scenario === 'notconfigured') return { ...base, status: 'not_configured', api_token_configured: false }
  if (scenario === 'error') return { ...base, status: 'error', error: 'Nomor WhatsApp terputus. Hubungkan ulang di server.' }
  return base
}

// ---- onboarding (K5): templates and a fresh install kept in localStorage ----
const SAMPLE_TEMPLATES: Raw[] = [
  { id: 'rian', name: 'Rian', role: 'Copywriting Specialist', team: 'marketing', color: 'amber', description: 'Menulis naskah dan caption yang santai, jujur, dan enak dibaca di HP.' },
  { id: 'budi', name: 'Budi', role: 'Visual Designer & Art Director', team: 'marketing', color: 'indigo', description: 'Merancang arah visual dan menyiapkan gambar untuk konten.' },
  { id: 'diana', name: 'Diana', role: 'Creative Director & QC Auditor', team: 'marketing', color: 'teal', description: 'Menilai mutu naskah dan memberi skor serta catatan perbaikan.' },
  { id: 'siti', name: 'Siti', role: 'Frontline Support Specialist', team: 'customer_support', color: 'sky', description: 'Membalas pelanggan dengan empatik, jelas, dan sopan.' },
  { id: 'hendra', name: 'Hendra', role: 'CS Team Lead & Quality Auditor', team: 'customer_support', color: 'teal', description: 'Memimpin tim CS dan mengaudit mutu balasan sebelum dikirim.' },
]

interface FreshState {
  bots: Raw[]
  groups: Raw[]
  seq: number
}

// Skenario fresh hanya untuk menguji #/mulai; __mock.reset() mengembalikan.
function freshStore(): FreshState {
  try {
    const raw = JSON.parse(localStorage.getItem(FRESH_KEY) ?? '{}') as Partial<FreshState>
    return { bots: Array.isArray(raw.bots) ? raw.bots : [], groups: Array.isArray(raw.groups) ? raw.groups : [], seq: asNum(raw.seq) }
  } catch {
    return { bots: [], groups: [], seq: 0 }
  }
}

function saveFresh(f: FreshState) {
  localStorage.setItem(FRESH_KEY, JSON.stringify(f))
}

const isFresh = () => sc('onboarding') === 'fresh' || sc('onboarding') === 'limit'

// ---- events: the same handler map as the real /events stream, so a sample ping reaches toast and badge ----
let eventHandlers: Record<string, (d: Raw) => void> | null = null
let pingTimer = 0

function pingHandover() {
  const row = conversationRow('mock-conv-3')
  if (!row || row.state !== 'needs_human') {
    setConvState('mock-conv-3', { state: 'needs_human', reason: 'asked_human', taken_by: '', resume_at: 0 })
    pushConvLog('mock-conv-3', 'Siti berhenti membalas. Menunggu manusia.')
  }
  eventHandlers?.handover?.({
    conversation_id: 'mock-conv-3',
    state: 'needs_human',
    reason: 'asked_human',
    customer: 'Rina Wijaya',
    bot_id: 'siti',
    at: new Date().toISOString(),
  })
}

export function mockEvents(on: Record<string, (d: Raw) => void>): () => void {
  eventHandlers = on
  if (sc('handoverPing') === 'auto' && !pingTimer) {
    pingTimer = window.setTimeout(() => {
      pingTimer = 0
      pingHandover()
    }, 8000)
  }
  return () => {
    if (eventHandlers === on) eventHandlers = null
  }
}

// Agents the group decoration knows by id or first name (the ids the BFF can route to).
const A2A_NAMES: Record<string, string> = { rian: 'Rian', diana: 'Diana', budi: 'Budi', siti: 'Siti', hendra: 'Hendra', bimo: 'Bimo', meda: 'Meda', raka: 'Raka', bram: 'Bram', vina: 'Vina' }

function mentionedIds(text: string, author: string): string[] {
  return Object.entries(A2A_NAMES)
    .filter(([id, name]) => id !== author && new RegExp(`@(${id}|${name})\\b`, 'i').test(text))
    .map(([id]) => id)
}

// ---- connections demo ----
const disconnectedByUser = new Set<string>()

function connItem(provider: 'instagram' | 'canva'): Raw {
  const name = provider === 'instagram' ? 'Instagram' : 'Canva'
  const scenario = sc(provider)
  const base: Raw = { provider, name, status: 'disconnected', account: null, connected_at: null, redirect_uri: '', setup: [] }
  if (disconnectedByUser.has(provider)) return base
  if (scenario === 'notconfigured') return { ...base, status: 'not_configured' }
  if (scenario === 'connected' || scenario === 'personal') {
    return {
      ...base,
      status: scenario === 'personal' ? 'disconnected' : 'connected',
      account: provider === 'instagram' ? { username: 'colorbox.id', type: 'BUSINESS' } : 'colorbox.studio',
      connected_at: new Date(Date.now() - 14 * 86400_000).toISOString(),
    }
  }
  if (scenario === 'reconnect' || scenario === 'broken') {
    return {
      ...base,
      status: scenario,
      reason: scenario === 'reconnect' ? 'Izin akses sudah tidak berlaku. Hubungkan ulang agar bisa dipakai lagi.' : 'Sambungan terakhir ke penyedia gagal. Hubungkan ulang.',
      needs: 'reconnect',
    }
  }
  return base
}

// ---- skill files ----
interface SkillState {
  name: string
  description: string
  category: string
  content: string
  bytes: number
  updated_at: number
  scan: 'safe' | 'caution' | 'dangerous'
  scan_note: string
  enabled: boolean
  source: 'user' | 'template'
  versions: { id: string; content: string; created_at: number }[]
}

const SKILL_BASE: SkillState[] = [
  {
    name: 'balasan-pelanggan-colorbox',
    description: 'Dipakai saat membalas pesan pelanggan Colorbox tentang pesanan, pengiriman, ukuran, retur, atau keluhan.',
    category: 'customer_support',
    content: '---\nname: balasan-pelanggan-colorbox\ndescription: Dipakai saat membalas pesan pelanggan Colorbox.\n---\n\n# Balasan pelanggan\n\n## Kapan dipakai\nSetiap kali pelanggan menulis pesan.\n\n## Nada bicara\n- Ramah dan jelas.\n- Kalimat pendek.\n',
    bytes: 4200,
    updated_at: Math.floor(Date.now() / 1000) - 3600,
    scan: 'safe',
    scan_note: '',
    enabled: true,
    source: 'user',
    versions: [],
  },
  {
    name: 'caption-instagram-colorbox',
    description: 'Dipakai saat menulis caption atau naskah singkat untuk Instagram Colorbox.',
    category: 'marketing',
    content: '---\nname: caption-instagram-colorbox\ndescription: Dipakai saat menulis caption Instagram Colorbox.\n---\n\n# Caption Instagram\n\n## Gaya\nSantai dan ringkas.\n\n## Sebelum diposting\nSiapkan sebagai draf.\n',
    bytes: 3900,
    updated_at: Math.floor(Date.now() / 1000) - 86400,
    scan: 'caution',
    scan_note: 'Isinya memuat tautan atau perintah mengirim ke pihak luar. Periksa dulu sebelum diaktifkan.',
    enabled: false,
    source: 'template',
    versions: [],
  },
  {
    name: 'jadwal-konten-mingguan',
    description: 'Menyusun jadwal konten mingguan untuk tim konten.',
    category: 'khusus',
    content: '---\nname: jadwal-konten-mingguan\ndescription: Menyusun jadwal konten mingguan.\n---\n\n# Jadwal konten mingguan\n\nBuat tujuh ide konten, satu per hari.\n',
    bytes: 2400,
    updated_at: Math.floor(Date.now() / 1000) - 5 * 86400,
    scan: 'safe',
    scan_note: '',
    enabled: false,
    source: 'user',
    versions: [],
  },
]

let skillState: SkillState[] | null = null

function skills(): SkillState[] {
  if (!skillState) {
    const scenario = sc('skills')
    if (scenario === 'empty') skillState = []
    else if (scenario === 'full') {
      skillState = Array.from({ length: 30 }, (_, i) => ({
        ...SKILL_BASE[i % SKILL_BASE.length],
        name: `cara-kerja-${i + 1}`,
        description: `Cara kerja contoh nomor ${i + 1} untuk menguji daftar yang penuh.`,
        updated_at: Math.floor(Date.now() / 1000) - i * 3600,
        enabled: i % 3 !== 2,
      }))
    } else skillState = SKILL_BASE.map((s) => ({ ...s, versions: [{ id: `v-${s.name}-1`, content: s.content, created_at: s.updated_at - 600 }] }))
  }
  return skillState
}

function skillItem(s: SkillState): Raw {
  return {
    name: s.name,
    description: s.description,
    category: s.category,
    bytes: s.bytes,
    updated_at: s.updated_at,
    scan: s.scan,
    enabled: s.enabled,
    source: s.source,
    scan_note: s.scan_note,
  }
}

const DANGEROUS = /abaikan (semua )?(instruksi|perintah)|ignore (all )?previous|curl[^\n]*\|\s*(ba)?sh|\.env\b|api[_ -]?key|password|kata sandi/i
const CAUTION = /https?:\/\/|kirim ke/i
const XML_TAG = /<\/?[a-zA-Z][^>]*>/

// Prohibitions ("Jangan meminta ... kata sandi") are not instructions to open secrets. Without this, the
// sample skill itself would be rejected by its own scanner.
function scanText(content: string): string {
  return content.replace(/\b(jangan|tidak boleh|hindari|never|do not)\b[^\n.]*/gi, '')
}

function parseSkill(content: string): { name: string; description: string; category: string; body: string } | string {
  if (new TextEncoder().encode(content).length > 65536) return 'Berkas terlalu besar. Maksimal 64 KB.'
  const fm = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/.exec(content)
  if (!fm) return 'Bagian pembuka (name dan description) wajib diisi.'
  const field = (k: string) => new RegExp(`${k}:\\s*(.+)`).exec(fm[1])?.[1].trim() ?? ''
  const name = field('name')
  const description = field('description')
  const category = field('category') || 'khusus'
  const body = content.slice(fm[0].length)
  if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(name) || name.length > 64) return 'Nama cara kerja hanya boleh huruf kecil, angka, dan tanda hubung, maksimal 64 huruf.'
  if (!description || description.length > 1024) return 'Keterangan wajib diisi, maksimal 1.024 huruf.'
  if (XML_TAG.test(content)) return 'Isi tidak boleh memuat kode atau tag.'
  if (!body.trim()) return 'Isi cara kerja tidak boleh kosong.'
  if (DANGEROUS.test(scanText(content))) return 'Cara kerja ini ditolak: isinya menyuruh pegawai mengabaikan aturan atau membuka kunci rahasia.'
  return { name, description, category, body }
}

function upsertVersion(s: SkillState, content: string) {
  s.versions.unshift({ id: `v-${s.name}-${s.versions.length + 1}`, content: s.content, created_at: Math.floor(Date.now() / 1000) })
  s.content = content
  s.bytes = new TextEncoder().encode(content).length
  s.updated_at = Math.floor(Date.now() / 1000)
}

function applyScan(s: SkillState, content: string) {
  const text = scanText(content)
  if (CAUTION.test(text)) {
    s.scan = 'caution'
    s.scan_note = 'Isinya memuat tautan atau perintah mengirim ke pihak luar. Periksa dulu sebelum diaktifkan.'
    s.enabled = false
  } else {
    s.scan = 'safe'
    s.scan_note = ''
  }
}

// ---- AI accounts ----
const AI_NAMES: Record<string, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  gemini: 'Google Gemini',
  'opencode-zen': 'OpenCode Zen',
  'opencode-go': 'OpenCode Go',
  openrouter: 'OpenRouter',
}
const UNAVAILABLE: Raw[] = [
  { id: 'claude-subscription', available: false, reason: 'Anthropic tidak mengizinkan langganan pribadi dipakai di aplikasi lain. Pakai kunci akses Anthropic di atas.' },
  { id: 'chatgpt-subscription', available: false, reason: 'OpenAI mensyaratkan login ChatGPT disimpan di perangkat Anda sendiri, bukan di server aplikasi. Pakai kunci akses OpenAI di atas.' },
  { id: 'copilot', available: false, reason: 'GitHub Copilot belum menyediakan sambungan untuk aplikasi lain.' },
]

const KEY_PROVIDERS = ['anthropic', 'openai', 'gemini', 'opencode-zen', 'opencode-go']
const aiOverride: Record<string, { last4: string; status: 'ok' | 'invalid' }> = {}

function aiRows(): Raw[] {
  const scenario = sc('ai')
  const connected = scenario === 'ok'
  const rows: Raw[] = KEY_PROVIDERS.map((id) => {
    const o = aiOverride[id]
    const isOk = connected && (id === 'anthropic' || id === 'openai')
    return {
      id,
      connected: !!o || isOk,
      last4: o?.last4 ?? (isOk ? (id === 'anthropic' ? 'ab12' : 'wxyz') : undefined),
      status: o?.status ?? (isOk ? 'ok' : undefined),
      method: 'api_key',
      checked_at: o || isOk ? new Date().toISOString() : undefined,
    }
  })
  const or = aiOverride.openrouter
  rows.unshift({
    id: 'openrouter',
    connected: !!or || connected,
    last4: or?.last4 ?? (connected ? 'or42' : undefined),
    status: or?.status ?? (connected ? 'ok' : undefined),
    method: 'oauth',
    checked_at: or || connected ? new Date().toISOString() : undefined,
  })
  if (scenario === 'invalid') {
    const a = rows.find((r) => r.id === 'anthropic')
    if (a) Object.assign(a, { connected: true, status: 'invalid', last4: '1234' })
  }
  return rows
}

// ---- telegram ----
const tgState: { started: number; username: string; allowed: Raw[]; pending: Raw[] } = {
  started: 0,
  username: 'siti_colorbox_bot',
  allowed: [],
  pending: [],
}
const TG_LINK = 'https://t.me/newbot/pegawai_ai_bot/siti_colorbox_bot?name=Siti%20Colorbox'

function telegramStatus(): 'none' | 'pending' | 'connected' | 'error' {
  const base = sc('telegram')
  if (base === 'error') return 'error'
  if (base === 'connected') return 'connected'
  if (base === 'pending') {
    if (sc('telegramConfirm') === 'never') return 'pending'
    return tgState.started ? (Date.now() - tgState.started >= 10_000 ? 'connected' : 'pending') : 'pending'
  }
  if (!tgState.started) return 'none'
  if (sc('telegramConfirm') === 'never') return 'pending'
  return Date.now() - tgState.started >= 10_000 ? 'connected' : 'pending'
}

function pairing(): Raw {
  return {
    pairing_id: 'mock-pair-1',
    link: TG_LINK,
    qr_text: TG_LINK,
    expires_at: Math.floor(Date.now() / 1000) + Math.max(5, Number(sc('telegramExpiry')) || 600),
  }
}

function telegramInfo(): Raw {
  const status = telegramStatus()
  const allowed = status === 'connected' && !tgState.allowed.length ? [{ id: '111', name: 'Anda', owner: true }, { id: '222', name: 'Rina (staf)' }] : tgState.allowed
  const pending = status === 'pending' && !tgState.pending.length ? [{ id: '333', name: 'Dewi' }] : tgState.pending
  return {
    status,
    username: status === 'connected' ? tgState.username : undefined,
    allowed,
    pending,
    error: status === 'error' ? 'Bot tidak bisa dipakai lagi. Hubungkan ulang.' : undefined,
    pairing: status === 'pending' ? pairing() : undefined,
  }
}

// ---- social posts / action ----
function postRow(id: string, caption: string, ids: string[], status: string, extra: Raw = {}): Raw {
  const now = Math.floor(Date.now() / 1000)
  return { id, platform: 'instagram', caption, attachment_ids: ids, status, created_at: now - 5 * 86400, published_at: status === 'published' ? now - 4 * 86400 : 0, ...extra }
}

let publishingStart = 0

function socialPosts(): Raw[] {
  const scenario = sc('posts')
  const out: Raw[] = []
  const demo = socialDemo()
  if (demo && demo.approved_at) {
    const done = Date.now() - demo.approved_at >= 2000
    const failed = done && sc('publish') === 'fail'
    out.push(
      postRow('mock-post-demo', demo.caption, demo.ids, done ? (failed ? 'failed' : 'published') : 'publishing', {
        error: failed ? 'Instagram menolak gambar ini: ukurannya terlalu kecil.' : undefined,
        permalink: done && !failed ? 'https://www.instagram.com/p/CONTOHDEMO/' : undefined,
        published_at: done && !failed ? Math.floor(Date.now() / 1000) : 0,
      }),
    )
  }
  if (scenario === 'empty') return out
  if (scenario === 'publishing') {
    const started = publishingStart || (publishingStart = Date.now())
    const done = started > 0 && Date.now() - started >= 8000
    out.push(postRow('mock-post-pub', 'Koleksi terbaru sudah bisa dilihat di toko.', [A.img1.id], done ? 'published' : 'publishing', { permalink: done ? 'https://www.instagram.com/p/CONTOHPUB/' : undefined }))
    return out
  }
  out.push(
    postRow('mock-post-pub', 'Potongan nyaman untuk dipakai harian. Cek koleksinya di colorbox.co.id.', [A.img1.id], 'published', { permalink: 'https://www.instagram.com/p/CONTOH123/' }),
    postRow('mock-post-wait', 'Carousel tiga gaya untuk akhir pekan ini.', [A.img1.id, A.img3.id], 'awaiting_approval'),
    postRow('mock-post-fail', 'Foto produk baru, siap terbit sore ini.', [A.img2.id], 'failed', { error: 'Instagram menolak gambar ini: ukurannya terlalu kecil.' }),
  )
  return out
}

function socialAction(): Raw | null {
  const demo = socialDemo()
  if (!demo) return null
  let status = 'pending'
  let result: string | null = null
  let permalink: string | undefined
  let decided: string | null = null
  if (demo.rejected_at) {
    status = 'rejected'
    result = null
    decided = new Date(demo.rejected_at).toISOString()
  } else if (demo.approved_at) {
    const done = Date.now() - demo.approved_at >= 2000
    if (!done) {
      status = 'approved'
      decided = new Date(demo.approved_at).toISOString()
    } else if (sc('publish') === 'fail') {
      status = 'failed'
      result = 'Instagram menolak gambar ini: ukurannya terlalu kecil.'
      decided = new Date(demo.approved_at + 2000).toISOString()
    } else {
      status = 'done'
      result = 'Terbit di Instagram.'
      permalink = 'https://www.instagram.com/p/CONTOHDEMO/'
      decided = new Date(demo.approved_at + 2000).toISOString()
    }
  }
  return {
    id: 'mock-act-1',
    short_id: 'A1',
    kind: 'social_publish_post',
    summary: 'Posting ke Instagram',
    payload: {
      platform: 'instagram',
      kind: 'carousel',
      caption: demo.caption,
      attachment_ids: demo.ids,
      attachments: atts(demo.ids),
      draft_id: 'mock-draft-1',
      account: '@colorbox.id',
      permalink,
    },
    status,
    result,
    source: { bot_id: demo.bot_id, run_id: 'mock-run-1', session_id: demo.session_id },
    created_at: new Date(demo.created_at).toISOString(),
    decided_at: decided,
  }
}

// ---- demo runs ----
function demoName(input: string): string {
  const m = /^\/demo\s+(.+?)\s*$/i.exec(input.trim())
  const raw = (m?.[1] ?? '').toLowerCase()
  if (raw === 'posting panjang' || raw === 'video besar') return raw
  return Object.keys(DEMO_TEXT).find((k) => raw.startsWith(k)) ?? ''
}

function startDemoRun(botId: string, body: Raw): Raw {
  const input = asStr(body.input)
  const keyword = demoName(input)
  const store = demoStore()
  const n = store.n + 1
  const sid = asStr(body.session_id) || `mock-sess-${n}`
  const runId = `mock-run-${n}`
  const output = DEMO_TEXT[keyword] ?? 'Contoh hasil sudah siap.'
  const ids = keyword === 'posting panjang' || keyword === 'posting' ? DEMO.posting : DEMO[keyword] ?? []
  const session: DemoSession = {
    id: sid,
    run_id: runId,
    bot_id: botId,
    input,
    output,
    attachment_ids: ids,
    created_at: Date.now(),
  }
  store.n = n
  saveDemo({ n, sessions: [...store.sessions, session] })
  if (keyword === 'posting' || keyword === 'posting panjang') {
    saveSocial({
      caption: keyword === 'posting panjang' ? captionLong() : captionShort(),
      ids,
      bot_id: botId,
      session_id: sid,
      created_at: Date.now(),
      approved_at: 0,
      rejected_at: 0,
    })
  }
  return {
    run: {
      id: runId,
      bot_id: botId,
      bot_name: 'Siti',
      status: 'running',
      kind: 'chat',
      session_id: sid,
      started_at: new Date().toISOString(),
      origin: { type: 'chat' },
    },
    session_id: sid,
  }
}

export function mockSubscribe(path: string, on: Record<string, (d: Raw) => void>, onState?: (s: 'open' | 'retry') => void): () => void {
  const id = decodeURIComponent(path.replace(/^\/runs\//, '').replace(/\/stream$/, ''))
  const session = demoStore().sessions.find((s) => s.run_id === id)
  onState?.('open')
  const output = session?.output ?? 'Contoh hasil sudah siap.'
  const attachments = atts(session?.attachment_ids ?? [])
  const chunks = [output.slice(0, Math.ceil(output.length / 3)), output.slice(Math.ceil(output.length / 3), Math.ceil((2 * output.length) / 3)), output.slice(Math.ceil((2 * output.length) / 3))]
  let closed = false
  const timers: number[] = []
  const at = (ms: number, fn: () => void) => timers.push(window.setTimeout(() => void (closed || fn()), ms))
  at(0, () => on.snapshot?.({ output: '', tools: [] }))
  chunks.forEach((c, i) => at(300 * (i + 1), () => on.delta?.({ text: c })))
  at(1000, () =>
    on.done?.({
      status: 'completed',
      output,
      attachments,
      usage: { input_tokens: 1240, output_tokens: 320, total_tokens: 1560 },
    }),
  )
  return () => {
    closed = true
    for (const t of timers) window.clearTimeout(t)
  }
}

// ---- blob answers ----
export async function mockBlob(path: string): Promise<Blob> {
  const url = new URL(path, 'http://mock.local')
  const id = decodeURIComponent(url.pathname.replace('/artifacts/', ''))
  const thumb = url.searchParams.get('thumb') === '1'
  const a = attById(id)
  // mock-out-17 is always gone: the Output screen has to explain a missing file.
  if (!a || id === A.broken.id || id === 'mock-out-17' || sc('attachments') === 'gone') throw new ApiError('Berkas ini sudah tidak tersedia.', 404)
  if (sc('attachments') === 'slow') await wait(4000)
  try {
    if (a.mime.startsWith('video/')) {
      if (thumb) return await pngBlob(640, 360, 'Video contoh', 3)
      return await webmBlob(a.width ?? 1280, a.height ?? 720, 'Video contoh')
    }
    if (a.mime.startsWith('audio/')) return wavBlob(2)
    if (a.mime === 'application/pdf') return pdfBlob('Katalog Colorbox', ['Contoh katalog produk untuk mode contoh.', 'Ukuran, warna, dan harga di layar bukan data asli.', '', 'Dokumen ini dibuat di browser dan tidak disimpan.'])
    if (a.mime === 'text/csv') return csvBlob()
    if (a.mime.startsWith('image/')) return await pngBlob(a.width ?? 1080, a.height ?? 1080, `Contoh ${a.width ?? 1080}×${a.height ?? 1080}`, a.width === a.height ? 1 : a.width === 1080 ? 0 : 2)
    if (a.mime.startsWith('text/')) return textBlob('Contoh berkas teks dari mode contoh.')
    return zipLikeBlob(a.name.split('.').pop() ?? 'zip')
  } catch (e) {
    if (e instanceof MockAssetError) throw new ApiError(e.message, e.status)
    throw e
  }
}

// ---- call interception ----
async function answer<T>(value: unknown): Promise<T> {
  await wait()
  return value as T
}

function raw(body: unknown): Raw {
  return body && typeof body === 'object' ? (body as Raw) : {}
}

function parts(path: string): { p: string; q: URLSearchParams } {
  const i = path.indexOf('?')
  return { p: i < 0 ? path : path.slice(0, i), q: new URLSearchParams(i < 0 ? '' : path.slice(i + 1)) }
}

const notFound = () => new ApiError('Data tidak ditemukan. Mungkin sudah dihapus.', 404)

export async function mockIntercept<T>(method: string, path: string, body: unknown, real: () => Promise<T>): Promise<T> {
  const { p, q } = parts(path)
  const b = raw(body)
  const m = method.toUpperCase()
  const seg = p.split('/').filter(Boolean).map(decodeURIComponent)

  // R1 artifacts
  if (m === 'POST' && seg[0] === 'artifacts' && seg[2] === 'link') {
    if (sc('artifactLink') === 'off' || sc('attachments') === 'huge') throw new ApiError('Tautan berkas tidak tersedia.', 404)
    const id = seg[1]
    const blob = await mockBlob(`/artifacts/${id}`)
    return answer({ url: URL.createObjectURL(blob), expires_at: new Date(Date.now() + 300_000).toISOString() })
  }
  if (m === 'GET' && seg.length === 1 && seg[0] === 'artifacts') {
    const sid = q.get('session_id') ?? ''
    if (sid) {
      const session = demoSession(sid)
      let items: Att[] = []
      if (sc('attachments') !== 'empty') {
        if (session) items = atts(session.attachment_ids)
        else if (sc('attachments') === 'huge') items = [A.huge]
        else items = [A.img1, A.pdf]
      }
      return answer({ items })
    }
    // Output (K1): the same endpoint without session_id lists every file, filtered and paged.
    if (sc('output') === 'fail') throw new ApiError('Layanan belum bisa dihubungi. Coba lagi sebentar lagi.', 500)
    const botId = q.get('bot_id') ?? ''
    const type = q.get('type') ?? ''
    const scenario = sc('output')
    const limit = Math.min(100, Math.max(1, asNum(q.get('limit'), 24)))
    const start = scenario === 'few' || scenario === 'empty' ? 0 : Math.max(0, asNum(q.get('before'), 0))
    // The scenario decides the whole set: `few` and `empty` also drive the chip counts, not only the rows.
    const base = OUT.filter((o) => !botId || o.bot_id === botId)
    const scope = scenario === 'empty' ? [] : scenario === 'few' ? base.slice(0, 3) : base
    const rows = type ? scope.filter((o) => outKind(o.mime) === type) : scope
    const page = rows.slice(start, start + limit)
    await wait(scenario === 'slow' ? 3000 : latency())
    return {
      items: page,
      next: scenario === 'few' || scenario === 'empty' || start + limit >= rows.length ? null : String(start + limit),
      counts: outCounts(scope),
    } as T
  }

  // R5 skill files
  if (seg[0] === 'agents' && seg[2] === 'skill-files') {
    if (sc('skills') === 'fail') throw new ApiError('Layanan belum bisa dihubungi. Coba lagi sebentar lagi.', 500)
    if (m !== 'GET') await wait(sc('skills') === 'slowscan' ? 6000 : latency())
    const name = seg[3] ?? ''
    const action = seg[4] ?? ''
    const all = skills()
    if (m === 'GET' && !name) {
      return {
        items: all.map(skillItem),
        can_edit: sc('skills') !== 'staff',
      } as T
    }
    if (m === 'GET' && name) {
      const s = all.find((x) => x.name === name)
      if (!s) throw notFound()
      return { name: s.name, category: s.category, content: s.content, scan: s.scan, scan_note: s.scan_note, versions: s.versions.map((v) => ({ id: v.id, created_at: v.created_at })) } as T
    }
    if (m === 'POST' && !name) {
      const parsed = parseSkill(asStr(b.content))
      if (typeof parsed === 'string') throw new ApiError(parsed, 422)
      if (all.length >= 30) throw new ApiError('Batas 30 cara kerja tercapai. Hapus yang tidak dipakai.', 422)
      if (all.some((x) => x.name === parsed.name)) throw new ApiError('Nama ini sudah dipakai.', 409)
      const s: SkillState = {
        name: parsed.name,
        description: parsed.description,
        category: asStr(b.category) || parsed.category,
        content: asStr(b.content),
        bytes: new TextEncoder().encode(asStr(b.content)).length,
        updated_at: Math.floor(Date.now() / 1000),
        scan: 'safe',
        scan_note: '',
        enabled: true,
        source: 'user',
        versions: [],
      }
      applyScan(s, s.content)
      all.push(s)
      return skillItem(s) as T
    }
    const s = all.find((x) => x.name === name)
    if (!s) throw notFound()
    if (m === 'PUT' && !action) {
      const parsed = parseSkill(asStr(b.content))
      if (typeof parsed === 'string') throw new ApiError(parsed, 422)
      upsertVersion(s, asStr(b.content))
      applyScan(s, s.content)
      return skillItem(s) as T
    }
    if (m === 'PUT' && action === 'enabled') {
      s.enabled = b.enabled === true && s.scan !== 'dangerous'
      return skillItem(s) as T
    }
    if (m === 'POST' && action === 'restore') {
      const v = s.versions.find((x) => x.id === asStr(b.version_id))
      if (!v) throw notFound()
      upsertVersion(s, v.content)
      applyScan(s, s.content)
      return skillItem(s) as T
    }
    if (m === 'DELETE' && !action) {
      skillState = all.filter((x) => x.name !== name)
      return undefined as T
    }
    throw notFound()
  }

  // R4 AI accounts
  if (seg[0] === 'ai-accounts') {
    if (m === 'GET' && seg[1] === 'openrouter' && seg[2] === 'start') {
      // Stay inside the app: the real BFF sends the browser to OpenRouter, the sample mode pretends the person came back.
      await wait()
      aiOverride.openrouter = { last4: 'or42', status: 'ok' }
      return { url: '#/pengaturan/akun-ai?connect=ok' } as T
    }
    if (m === 'GET' && !seg[1]) {
      if (sc('ai') === 'fail') throw new ApiError('Layanan belum bisa dihubungi. Coba lagi sebentar lagi.', 500)
      return answer({ providers: [...aiRows(), ...UNAVAILABLE] })
    }
    const provider = seg[1] ?? ''
    const name = AI_NAMES[provider] ?? provider
    if (m === 'POST' && seg[2] === 'test') {
      await wait()
      const row = aiRows().find((r) => r.id === provider)
      return { status: row?.status === 'invalid' ? 'invalid' : 'ok' } as T
    }
    if (m === 'POST' && !seg[2]) {
      await wait()
      const key = asStr(b.api_key)
      if (sc('ai') === 'keyreject' || key.length < 20 || key.startsWith('sk-salah')) throw new ApiError(`Kunci tidak diterima oleh ${name}.`, 422)
      aiOverride[provider] = { last4: key.slice(-4), status: 'ok' }
      return { status: 'ok', last4: key.slice(-4) } as T
    }
    if (m === 'DELETE' && !seg[2]) {
      await wait()
      delete aiOverride[provider]
      return undefined as T
    }
    throw notFound()
  }

  // R3 Telegram
  if (seg[0] === 'agents' && seg[2] === 'telegram') {
    if (sc('telegram') === 'fail') throw new ApiError('Layanan belum bisa dihubungi. Coba lagi sebentar lagi.', 500)
    const action = seg[3] ?? ''
    if (m === 'GET' && !action) return answer(telegramInfo())
    if (m === 'POST' && action === 'start') {
      await wait()
      tgState.started = Date.now()
      tgState.allowed = []
      tgState.pending = []
      return answer(pairing())
    }
    if (m === 'POST' && action === 'token') {
      await wait()
      const token = asStr(b.token)
      if (!/^\d{6,12}:[A-Za-z0-9_-]{30,}$/.test(token)) throw new ApiError('Kunci bot tidak dikenali Telegram. Periksa lagi salinannya.', 422)
      tgState.started = Date.now() - 11_000
      tgState.allowed = [{ id: '111', name: 'Anda', owner: true }]
      return answer(telegramInfo())
    }
    if (m === 'PUT' && action === 'allowed') {
      await wait()
      const ids: unknown[] = Array.isArray(b.user_ids) ? b.user_ids : []
      tgState.allowed = ids.map((x, i) => ({ id: String(x), name: i === 0 ? 'Anda' : `Staf ${i}`, owner: i === 0 }))
      tgState.pending = []
      return answer(telegramInfo())
    }
    if (m === 'DELETE' && !action) {
      await wait()
      tgState.started = 0
      tgState.allowed = []
      tgState.pending = []
      return undefined as T
    }
    throw notFound()
  }

  // R2 posts + approval
  if (m === 'GET' && seg[0] === 'social' && seg[1] === 'posts') {
    const limit = asNum(q.get('limit'), 20)
    return answer({ items: socialPosts().slice(0, limit) })
  }
  if (seg[0] === 'actions' && seg[1] === 'mock-act-1' && (seg[2] === 'approve' || seg[2] === 'reject')) {
    const demo = socialDemo()
    if (!demo) throw notFound()
    await wait()
    if (seg[2] === 'approve') demo.approved_at = Date.now()
    else demo.rejected_at = Date.now()
    saveSocial(demo)
    return socialAction() as T
  }
  if (m === 'GET' && seg[0] === 'actions') {
    const list = await real()
    const rows = Array.isArray(list) ? list : Array.isArray((list as Raw)?.items) ? (list as Raw).items : []
    const mine = socialAction()
    return (mine ? [...rows, mine] : rows) as T
  }

  // K4: sessions started by another agent, and the turns inside them, before the demo-session branch.
  if (sc('a2a') === 'on' && m === 'GET' && seg[0] === 'bots' && seg[2] === 'sessions' && seg[3] === 'mock-sess-a2a-in' && seg[4] === 'messages') {
    await wait()
    return [
      { id: 'a1', role: 'user', from_bot_id: 'rian', content: 'Budi, tolong buatkan 3 gambar carousel untuk koleksi November. Warna utama biru.' },
      { id: 'a2', role: 'assistant', content: 'Siap. Saya buat tiga gambar 4:5 dengan warna biru. Saya kabari Rian setelah selesai.' },
      { id: 'a3', role: 'assistant', content: 'Tiga gambar sudah jadi.', attachments: atts([A.img1.id, A.img2.id, A.img3.id]) },
    ] as T
  }
  if (sc('a2a') === 'on' && m === 'GET' && seg[0] === 'bots' && seg[2] === 'sessions' && seg[3] === 'mock-sess-a2a-out' && seg[4] === 'messages') {
    await wait()
    return [
      { id: 'b1', role: 'user', content: 'Minta Budi membuat carousel koleksi November.' },
      { id: 'b2', role: 'assistant', content: 'Sudah saya teruskan ke Budi.', to_bots: [{ bot_id: 'budi', link: '/chat/budi/mock-sess-a2a-in' }] },
    ] as T
  }

  // K5 onboarding=fresh|limit: the only agent endpoints this scenario answers; the rest goes to the BFF.
  if (isFresh() && m === 'GET' && seg[0] === 'bots' && seg[2] === 'sessions' && seg[3] && seg[1].endsWith('-mock')) return [] as T
  if (isFresh() && m === 'GET' && seg[0] === 'bots' && seg.length === 2 && seg[1].endsWith('-mock')) {
    const bot = freshStore().bots.find((x) => x.id === seg[1])
    if (!bot) throw notFound()
    return bot as T
  }

  // R1 demo chat
  if (m === 'POST' && seg[0] === 'bots' && seg[2] === 'runs' && /^\/demo\b/i.test(asStr(b.input))) {
    await wait()
    return startDemoRun(seg[1], b) as T
  }
  if (m === 'GET' && seg[0] === 'bots' && seg[2] === 'sessions' && seg[3]?.startsWith('mock-sess')) {
    const sid = seg[3]
    const session = demoSession(sid)
    await wait()
    if (seg[4] === 'messages') {
      if (!session) {
        return [
          { id: 'mock-tg-1', role: 'user', content: 'Halo, ini pesan dari Telegram.' },
          { id: 'mock-tg-2', role: 'assistant', content: 'Halo! Pesan Anda sudah masuk ke riwayat pegawai.' },
        ] as T
      }
      return [
        { id: `${sid}-u`, role: 'user', content: session.input },
        { id: `${sid}-a`, role: 'assistant', content: session.output, attachments: atts(session.attachment_ids) },
      ] as T
    }
    return [] as T
  }
  if (m === 'GET' && seg[0] === 'bots' && seg[2] === 'sessions') {
    const rows = await real()
    const list = Array.isArray(rows) ? rows : []
    const now = Math.floor(Date.now() / 1000)
    const demoRows = demoStore()
      .sessions.filter((s) => s.bot_id === seg[1])
      .map((s) => ({ id: s.id, title: `Contoh: ${s.input.replace(/^\/demo\s*/i, '')}`, preview: s.output, message_count: 2, last_active: Math.floor(s.created_at / 1000), model: '' }))
    const a2aOn = sc('a2a') === 'on'
    const incoming =
      a2aOn && ['budi', 'diana', 'siti', 'hendra'].includes(seg[1])
        ? [{ id: 'mock-sess-a2a-in', title: 'Brief carousel dari Rian', preview: 'Budi, tolong buatkan 3 gambar carousel…', message_count: 3, last_active: now - 40 * 60, model: '', source: 'web', peer: { bot_id: 'rian', name: 'Rian', link: '/chat/rian/mock-sess-a2a-out' } }]
        : []
    const outgoing = a2aOn && seg[1] === 'rian' ? [{ id: 'mock-sess-a2a-out', title: 'Brief carousel untuk Budi', preview: 'Sudah saya teruskan ke Budi.', message_count: 2, last_active: now - 45 * 60, model: '', source: 'web', peer: null }] : []
    const tg = telegramStatus() === 'none' && sc('telegram') === 'none' ? [] : [{ id: 'mock-sess-tg', title: 'Pesan dari Telegram', preview: 'Halo, ini pesan dari Telegram.', message_count: 4, last_active: Math.floor(Date.now() / 1000) - 1800, model: '', source: 'telegram' }]
    return [...outgoing, ...incoming, ...demoRows, ...tg, ...list.filter((r) => !r?.id?.startsWith?.('mock-sess'))] as T
  }

  // R1 task files
  if (m === 'GET' && seg[0] === 'tasks' && seg.length === 2) {
    const t = (await real()) as Raw
    if (sc('attachments') !== 'empty' && asStr(t.result)) {
      return { ...t, attachments: sc('attachments') === 'huge' ? [A.huge] : [A.img1, A.pdf] } as T
    }
    return t as T
  }

  // K2: the WhatsApp eligibility flag on the agent list and one agent (only when the scenario is not real).
  if (m === 'GET' && seg[0] === 'bots' && seg.length === 1) {
    if (isFresh()) return freshStore().bots as T
    if (sc('whatsapp') === 'real') return real()
    const rows = (await real()) as unknown
    const arr = Array.isArray(rows) ? rows : []
    return arr.map((x: Raw) => ({ ...x, channels: { whatsapp: asStr(x.team) === 'customer_support' } })) as T
  }
  if (m === 'GET' && seg[0] === 'bots' && seg.length === 2 && !seg[1].endsWith('-mock')) {
    const row = (await real()) as Raw
    return (sc('whatsapp') === 'real' ? row : { ...row, channels: { whatsapp: asStr(row.team) === 'customer_support' } }) as T
  }
  // K5: creating agents and a team on a fresh install (one by one, as the screens do).
  if (m === 'GET' && seg[0] === 'groups' && seg.length === 1 && isFresh()) return freshStore().groups as T
  if (m === 'GET' && seg[0] === 'me' && isFresh()) {
    const me = (await real()) as Raw
    const f = freshStore()
    const limits = sc('onboarding') === 'limit' ? { ...(me.limits ?? {}), max_bots: 3 } : me.limits
    return { ...me, limits, usage: { ...(me.usage ?? {}), bots: f.bots.length, groups: f.groups.length } } as T
  }
  if (m === 'POST' && seg[0] === 'bots' && seg.length === 1 && isFresh()) {
    await wait(1200)
    const f = freshStore()
    const name = asStr(b.name).trim()
    if (f.bots.some((x) => asStr(x.name).toLowerCase() === name.toLowerCase())) throw new ApiError('Nama ini sudah dipakai.', 400)
    if (sc('onboarding') === 'limit' && f.bots.length >= 3)
      throw new ApiError('Batas jumlah pegawai di paket Anda tercapai. Hapus pegawai yang tidak dipakai, atau hubungi tim AITopTrends untuk menaikkan paket.', 402)
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'pegawai'
    const bot = {
      id: `${slug}-mock`,
      name,
      role: asStr(b.role),
      team: asStr(b.team),
      color: 'slate',
      builtin: false,
      status: 'idle',
      activity: '',
      about: '',
      created_at: new Date().toISOString(),
      model: null,
      provider: null,
      reasoning_effort: null,
    }
    f.bots.push(bot)
    saveFresh(f)
    return bot as T
  }
  if (m === 'POST' && seg[0] === 'groups' && seg.length === 1 && isFresh()) {
    await wait(600)
    const f = freshStore()
    const ids = Array.isArray(b.bot_ids) ? b.bot_ids.map((x: unknown) => asStr(x)) : []
    if (ids.length < 2 || ids.length > 6) throw new ApiError('Grup harus punya 2 sampai 6 anggota', 400)
    const group = { id: `mock-grp-${f.seq + 1}`, name: asStr(b.name), members: ids, running: false }
    f.seq += 1
    f.groups.push(group)
    saveFresh(f)
    return group as T
  }

  // K4: group messages carry who was handed the turn (`to_bot_ids`), same @name rule as the real routing.
  if (sc('a2a') === 'on' && m === 'GET' && seg[0] === 'groups' && seg[2] === 'messages') {
    const rows = (await real()) as unknown
    const arr = Array.isArray(rows) ? rows : []
    return arr.map((x: Raw) => {
      const text = asStr(x.text ?? x.content)
      const author = asStr(x.bot_id)
      const isBot = asStr(x.author ?? x.role) === 'bot'
      return { ...x, to_bot_ids: isBot ? mentionedIds(text, author) : [] }
    }) as T
  }

  // K3: conversations, takeover and return. Sample data lives in localStorage so a reload keeps the state.
  if (seg[0] === 'conversations') {
    if (sc('handover') === 'fail') throw new ApiError('Layanan belum bisa dihubungi. Coba lagi sebentar lagi.', 500)
    if (m === 'GET' && seg.length === 1) {
      await wait()
      return convPage(q.get('state') ?? '', q.get('bot_id') ?? '', Math.max(1, asNum(q.get('limit'), 30))) as T
    }
    if (m === 'GET' && seg.length === 2) {
      await wait()
      const row = conversationRow(seg[1])
      if (!row) throw notFound()
      return row as T
    }
    if (m === 'GET' && seg[2] === 'messages') {
      await wait()
      if (!conversationRow(seg[1])) throw notFound()
      return { items: convMessages(seg[1]), next: null } as T
    }
    if (m === 'POST' && seg[2] === 'takeover') {
      await wait(600)
      const row = conversationRow(seg[1])
      if (!row) throw notFound()
      if (!(row.state === 'human' && row.taken_by)) {
        setConvState(seg[1], { state: 'human', taken_by: 'Anda', resume_at: Math.floor(Date.now() / 1000) + 7200 })
        pushConvLog(seg[1], 'Percakapan diambil alih.')
      }
      return conversationRow(seg[1]) as T
    }
    if (m === 'POST' && seg[2] === 'return') {
      await wait(600)
      const row = conversationRow(seg[1])
      if (!row) throw notFound()
      if (row.state !== 'bot' || row.taken_by) {
        setConvState(seg[1], { state: 'bot', taken_by: '', resume_at: 0 })
        pushConvLog(seg[1], 'Dikembalikan ke Siti.')
      }
      return conversationRow(seg[1]) as T
    }
  }

  // K2: WhatsApp status scenarios (`real` decorates the BFF's own reply and never hides its errors).
  if (m === 'GET' && seg[0] === 'whatsapp' && seg[1] === 'status') {
    const scenario = sc('whatsapp')
    if (scenario === 'fail') throw new ApiError('Layanan belum bisa dihubungi. Coba lagi sebentar lagi.', 500)
    if (scenario === 'real') {
      const r = (await real()) as Raw
      return {
        ...r,
        eligible_bot_ids: Array.isArray(r.eligible_bot_ids) && r.eligible_bot_ids.length ? r.eligible_bot_ids : ['siti', 'hendra'],
        agents:
          Array.isArray(r.agents) && r.agents.length
            ? r.agents
            : [
                { bot_id: 'siti', role: 'primary' },
                { bot_id: 'hendra', role: 'escalation' },
              ],
        number: r.number || '+62 812-3456-7890',
      } as T
    }
    await wait()
    return waStatus() as T
  }

  // K5: the templates the BFF really has, or a fixed sample so #/mulai can be seen without a backend.
  if (m === 'GET' && seg[0] === 'templates') {
    const scenario = sc('templates')
    if (scenario === 'fail') throw new ApiError('Layanan belum bisa dihubungi. Coba lagi sebentar lagi.', 500)
    if (scenario !== 'real') {
      await wait()
      return (scenario === 'few' ? SAMPLE_TEMPLATES.filter((t) => t.id === 'siti') : SAMPLE_TEMPLATES) as T
    }
    return real()
  }

  // R2 connections
  if (m === 'POST' && seg[0] === 'connections' && (seg[1] === 'instagram' || seg[1] === 'canva') && seg[2] === 'start') {
    await wait()
    const provider = seg[1]
    const app = provider
    if (provider === 'instagram' && sc('instagram') === 'personal') return answer({ url: `#/aplikasi?connect=error&app=${app}&reason=personal` })
    return answer({ url: `#/aplikasi?connect=ok&app=${app}` })
  }
  if (m === 'DELETE' && seg[0] === 'connections' && (seg[1] === 'instagram' || seg[1] === 'canva')) {
    await wait()
    disconnectedByUser.add(seg[1])
    return undefined as T
  }
  if (m === 'GET' && seg[0] === 'connections') {
    const rows = await real()
    const list = Array.isArray(rows) ? rows : []
    const ours = ['instagram', 'canva'].map((p) => connItem(p as 'instagram' | 'canva'))
    return [...ours, ...list.filter((r) => !['instagram', 'canva'].includes(asStr(r?.provider)))] as T
  }

  // R4 model catalog decoration (own providers when keys are connected)
  if (m === 'GET' && seg[0] === 'models') {
    const cat = (await real()) as Raw
    const active = sc('ai') === 'ok' || Object.keys(aiOverride).length > 0
    if (!active || !Array.isArray(cat.providers)) return cat as T
    const extra = [
      {
        slug: 'openrouter',
        name: 'OpenRouter (akun Anda)',
        own: true,
        models: ['anthropic/claude-sonnet-4.5', 'openai/gpt-5-mini', 'google/gemini-3-flash'],
        models_info: [
          { id: 'anthropic/claude-sonnet-4.5', label: 'Claude Sonnet 4.5', tier: 'teliti' },
          { id: 'openai/gpt-5-mini', label: 'GPT-5 mini', tier: 'seimbang' },
          { id: 'google/gemini-3-flash', label: 'Gemini 3 Flash', tier: 'hemat' },
        ],
      },
      {
        slug: 'anthropic',
        name: 'Anthropic (kunci Anda)',
        own: true,
        models: ['claude-sonnet-4-5', 'claude-haiku-4-5'],
        models_info: [
          { id: 'claude-sonnet-4-5', label: 'Claude Sonnet 4.5', tier: 'teliti' },
          { id: 'claude-haiku-4-5', label: 'Claude Haiku 4.5', tier: 'hemat' },
        ],
      },
    ]
    const providers = [...cat.providers]
    for (const e of extra) {
      const i = providers.findIndex((x: Raw) => x.slug === e.slug || x.slug === (e.slug === 'anthropic' ? 'claude' : ''))
      if (i >= 0) providers[i] = { ...providers[i], ...e, models: [...new Set([...providers[i].models, ...e.models])] }
      else providers.push(e)
    }
    return { ...cat, providers } as T
  }

  return real()
}
