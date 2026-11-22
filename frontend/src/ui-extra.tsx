import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { api, errText } from './bff'
import { ErrorLine, I, Icon } from './ui'
import type { Bot, Clarify, EstimateReason, LimitInfo } from './bff'

// Shared page pieces for the Sprint 3 pages.

// Status in words, from /api/bots. "Sedang berpikir" and "Menunggu izin" exist only in the run stream (open chat), not in the list.
export function statusText(b: Pick<Bot, 'status' | 'activity' | 'deleteError'>): string {
  if (b.deleteError) return 'Gagal dihapus. Coba hapus lagi.'
  if (b.status === 'working') return b.activity ? `Sedang bekerja: ${b.activity}` : 'Sedang bekerja'
  if (b.status === 'discussing') return b.activity ? `Berdiskusi di grup: ${b.activity}` : 'Berdiskusi di grup'
  return 'Siap'
}

// Model and thinking-level dropdowns, used by the agent edit page. A model value is "provider|model"; '' = Default.
export const modelKey = (provider: string | null | undefined, model: string | null | undefined) => (provider && model ? `${provider}|${model}` : '')
export const splitModel = (v: string): { provider: string | null; model: string | null } => {
  const i = v.indexOf('|')
  return i < 0 ? { provider: null, model: null } : { provider: v.slice(0, i), model: v.slice(i + 1) }
}

export function ModelSelect({ value, onChange, disabled, label = 'Model' }: { value: string; onChange: (v: string) => void; disabled?: boolean; label?: string }) {
  const [cat, setCat] = useState<Awaited<ReturnType<typeof api.models>> | null>(null)
  const [err, setErr] = useState('')
  useEffect(() => {
    let live = true
    api.models().then(
      (c) => live && setCat(c),
      (e) => live && setErr(errText(e)),
    )
    return () => {
      live = false
    }
  }, [])
  const known = !value || !!cat?.providers.some((p) => p.models.some((m) => modelKey(p.slug, m) === value))
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)}>
        <option value="">{defaultModelLabel(cat)}</option>
        {!known && <option value={value}>{splitModel(value).model}</option>}
        {cat?.providers.map((p) => (
          <optgroup key={p.slug} label={p.name}>
            {p.models.map((m) => (
              <option key={m} value={modelKey(p.slug, m)}>
                {m}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
      {err && <small className="err" role="alert">{err}</small>}
    </label>
  )
}

const EFFORT_WORD: Record<string, string> = { none: 'Tidak berpikir', minimal: 'Minimal', low: 'Rendah', medium: 'Sedang', high: 'Tinggi', xhigh: 'Sangat tinggi', max: 'Maksimal', ultra: 'Ultra' }
export const effortWord = (v: string | null | undefined) => (v ? EFFORT_WORD[v] ?? v : '')

// Plain Indonesian names for the agent tools (Hermes toolsets). Unknown ones fall back to the engine's own label.
// shortcut: fixed list of known toolsets, add a line here when Hermes ships a new one.
const TOOLSET_TEXT: Record<string, [string, string]> = {
  web: ['Cari di internet', 'Mencari informasi dan membaca halaman web.'],
  browser: ['Mengendalikan browser sendiri', 'Membuka halaman web, mengklik, dan mengetik.'],
  terminal: ['Menjalankan perintah di komputer', 'Menjalankan perintah di komputer server.'],
  file: ['Mengubah berkas di komputer', 'Membaca dan menulis berkas di komputer ini, terpisah dari Google Drive.'],
  code_execution: ['Menjalankan program', 'Menjalankan program kecil, misalnya untuk menghitung.'],
  vision: ['Baca gambar', 'Memahami isi gambar atau foto.'],
  video: ['Baca video', 'Memahami isi video.'],
  image_gen: ['Buat gambar', 'Membuat gambar dari deskripsi.'],
  video_gen: ['Buat video', 'Membuat video dari deskripsi.'],
  x_search: ['Pencarian X (Twitter)', 'Mencari kiriman di X.'],
  tts: ['Ubah teks jadi suara', 'Membacakan teks dengan suara.'],
  stt: ['Ubah suara jadi teks', 'Menulis ulang pesan suara.'],
  skills: ['Keahlian tambahan', 'Panduan kerja khusus yang bisa dipakai pegawai.'],
  todo: ['Rencana tugas', 'Menyusun langkah kerja sebelum mengerjakan.'],
  kanban: ['Papan tugas', 'Mengelola tugas di papan Kanban.'],
  memory: ['Ingatan', 'Mengizinkan pegawai mengingat hal penting antar percakapan. Saklar ini hanya menyalakan atau mematikan kemampuan itu; yang sudah diingat tidak dihapus.'],
  context_engine: ['Pengelola konteks', 'Menjaga isi percakapan panjang tetap muat.'],
  session_search: ['Cari percakapan lama', 'Mencari isi percakapan sebelumnya.'],
  connections: ['Pakai aplikasi tersambung', 'Memakai aplikasi yang sudah Anda hubungkan.'],
  clarify: ['Pertanyaan balik', 'Bertanya kepada Anda saat informasi kurang.'],
  delegation: ['Membagi tugas ke pegawai lain', 'Menyerahkan sub-tugas ke pegawai lain.'],
  cronjob: ['Tugas terjadwal', 'Membuat dan mengatur tugas berulang.'],
  discord: ['Discord', 'Membaca dan ikut percakapan di Discord.'],
  discord_admin: ['Admin Discord', 'Mengatur kanal dan peran di server Discord.'],
  computer_use: ['Kontrol komputer', 'Mengendalikan komputer secara otomatis.'],
  a2a: ['Pegawai ke pegawai', 'Berkomunikasi dengan pegawai dari sistem lain.'],
}
export const toolsetText = (name: string, label: string, description: string): [string, string] => TOOLSET_TEXT[name] ?? [label || name, description]
// What "Default" resolves to, shown next to the word everywhere: the profile's own value, else "ikut bawaan penyedia" (value unknown).
export const defaultEffortLabel = (cat?: { default: { reasoning_effort?: string | null } } | null) => `Bawaan (${effortWord(cat?.default.reasoning_effort) || 'ikut bawaan penyedia'})`
export const defaultModelLabel = (cat?: { default: { model: string | null } } | null) => `Bawaan${cat?.default.model ? ` (${cat.default.model})` : ''}`
const EFFORT_MAIN: [string, string][] = [['low', 'Rendah'], ['medium', 'Sedang'], ['high', 'Tinggi']]
const EFFORT_ADV: [string, string][] = [['none', 'Tidak berpikir'], ['minimal', 'Minimal'], ['xhigh', 'Sangat tinggi']]
export function EffortSelect({ value, onChange, disabled }: { value: string; onChange: (v: string) => void; disabled?: boolean }) {
  const [cat, setCat] = useState<Awaited<ReturnType<typeof api.models>> | null>(null)
  useEffect(() => {
    let live = true
    api.models().then((c) => live && setCat(c), () => {}) // the label then says "ikut provider"; ModelSelect shows the error
    return () => {
      live = false
    }
  }, [])
  return (
    <label className="field">
      <span>Tingkat berpikir</span>
      <select value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)}>
        <option value="">{defaultEffortLabel(cat)}</option>
        {EFFORT_MAIN.map(([v, l]) => (
          <option key={v} value={v}>
            {l}
          </option>
        ))}
        {EFFORT_ADV.some(([v]) => v === value) && (
          <optgroup label="Lanjutan">
            {EFFORT_ADV.map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </optgroup>
        )}
      </select>
    </label>
  )
}

// Marks an optional field label. Forms where most fields are required mark only the optional ones.
// USD usage. Amounts come formatted from the BFF (Money.label: "$0" / "< $0.01" / rounded to cents). A cost with unverified or
// missing prices is an estimate and is always labeled "perkiraan"; the reasons are the hover text.
const REASON: Record<EstimateReason['code'], (m: string) => string> = {
  unverified_price: (m) => `Harga ${m} belum diverifikasi dari halaman resmi penyedia.`,
  model_not_recorded: () => 'Sebagian tugas tidak mencatat modelnya, jadi dihitung dengan model bawaan pegawai.',
  no_price: (m) => `Belum ada harga untuk ${m}, jadi belum dihitung.`,
}
export const reasonText = (r: EstimateReason[] = []) => r.map((x) => REASON[x.code](x.models.join(', '))).join(' ')

export function Perkiraan({ reasons, why }: { reasons?: EstimateReason[]; why?: string }) {
  return (
    <span className="pill warn est" title={why ?? (reasonText(reasons) || 'Biaya ini perkiraan.')}>
      perkiraan
    </span>
  )
}

const STATE_TEXT = { normal: 'Aman', warning: 'Hampir habis', exceeded: 'Batas tercapai' } as const

// Spent / limit / remaining with the three states: normal, warning (>= 80%), exceeded (new tasks are refused).
export function CostMeter({ u, reasons, plan }: { u: LimitInfo; reasons?: EstimateReason[]; plan?: string }) {
  const pct = u.percent ?? 0
  return (
    <div className="cost-meter" data-state={u.limit ? u.state : 'none'}>
      <div className="cost-head">
        <span className="cost-spent num">{u.cost.label}</span>
        <span className="quiet">{u.limit ? `dari ${u.limit.label} bulan ini${plan ? ` (paket ${plan})` : ''}` : 'bulan ini, tanpa batas biaya'}</span>
        {u.basis === 'estimated' && <Perkiraan reasons={reasons} />}
        {u.limit && <span className={`pill ${u.state === 'normal' ? 'ok' : u.state === 'warning' ? 'warn' : 'bad'}`}>{STATE_TEXT[u.state]}</span>}
      </div>
      {u.limit && (
        <span className="set-meter" role="img" aria-label={`${pct} persen dari batas biaya bulan ini`}>
          <span style={{ width: `${Math.min(100, pct)}%` }} />
        </span>
      )}
      {u.limit && u.remaining && (
        <small className="quiet">
          {u.state === 'exceeded'
            ? 'Tugas baru ditolak sampai bulan depan atau paket dinaikkan.'
            : u.state === 'warning'
              ? `Sisa ${u.remaining.label}. Naikkan paket sebelum tugas mulai ditolak.`
              : `Sisa ${u.remaining.label}.`}
        </small>
      )}
    </div>
  )
}

export const Opt = () => <em className="req">(opsional)</em>

export type Cap = 'ok' | 'mock' | 'none' | 'blocked' | 'unknown'
// Status words: Berfungsi / Simulasi / Nonaktif (the rest only when the state is truly not known).
const CAP_LABEL: Record<Cap, string> = { ok: 'Berfungsi', mock: 'Simulasi', none: 'Belum didukung', blocked: 'Nonaktif', unknown: 'Tidak diketahui' }
export function CapChip({ cap, label }: { cap: Cap; label?: string }) {
  return <span className={`pill cap-${cap}`}>{label ?? CAP_LABEL[cap]}</span>
}

// Every fixture carries this badge.
export const SampleBadge = () => <span className="pill sample" title="Isi buatan frontend untuk menunjukkan bentuk hasil. Bukan hasil pegawai.">Contoh data</span>

export function PageHead({ title, sub, actions }: { title: string; sub?: string; actions?: ReactNode }) {
  return (
    <header className="page-head">
      <div>
        <h1>{title}</h1>
        {sub && <p className="quiet">{sub}</p>}
      </div>
      {actions && <div className="head-actions">{actions}</div>}
    </header>
  )
}

// Skeleton loader: flat blocks shaped like the content, a slow opacity pulse (static under reduced motion). The words stay for screen readers.
const SK = { lines: 3, ledger: 4, table: 5, page: 0 }
export function Loading({ text = 'Memuat...', shape = 'lines', rows }: { text?: string; shape?: 'lines' | 'ledger' | 'table' | 'page'; rows?: number }) {
  const n = rows ?? SK[shape]
  return (
    <div className={`skel skel-${shape}`} role="status" aria-busy="true">
      <span className="sr">{text}</span>
      <div aria-hidden="true" className="skel-body">
        {shape === 'page' ? (
          <>
            <i className="skel-bar w40 tall" />
            <i className="skel-block" />
            <div className="skel-two"><i className="skel-block" /><i className="skel-block" /></div>
          </>
        ) : (
          Array.from({ length: n }, (_, i) =>
            shape === 'lines' ? (
              <i key={i} className={`skel-bar${i === n - 1 ? ' w60' : ''}`} />
            ) : (
              <div key={i} className="skel-row">
                <span className="skel-main"><i className="skel-bar w40" /><i className="skel-bar w70 thin" /></span>
                {shape === 'table' && <i className="skel-bar w15 hide-sm" />}
                <i className="skel-bar w15" />
              </div>
            ),
          )
        )}
      </div>
    </div>
  )
}

// Thin indeterminate line in the accent (a static line under reduced motion).
export const ProgressLine = ({ label }: { label: string }) => (
  <span className="pline" role="status">
    <span className="sr">{label}</span>
  </span>
)

// "Bekerja · 12 dtk": the line plus elapsed seconds. Mount it when a run starts, unmount when it ends.
export function RunProgress({ detail }: { detail?: string }) {
  const [t0] = useState(Date.now)
  const [now, setNow] = useState(t0)
  useEffect(() => {
    const t = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(t)
  }, [])
  const s = Math.floor((now - t0) / 1000)
  return (
    <span className="runprog">
      <span className="sr" role="status">Bekerja{detail ? `, ${detail}` : ''}</span>
      <span className="runprog-row" aria-hidden="true">
        <Spinner />
        <span className="num">Bekerja · {detail ? `${detail} · ` : ''}{s} dtk</span>
      </span>
    </span>
  )
}

// Waiting mark: a thin ring with one accent arc turning at a steady speed (rotation only, nothing pulses or bounces).
export const Spinner = () => (
  <svg className="spin-arc" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
    <circle cx="8" cy="8" r="6" fill="none" strokeWidth="2" className="spin-track" />
    <circle cx="8" cy="8" r="6" fill="none" strokeWidth="2" strokeLinecap="round" strokeDasharray="10 28" className="spin-head" />
  </svg>
)

const COPY = 'M9 9h10a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V10a1 1 0 0 1 1-1zM5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1'
// Copy to clipboard; the icon turns into a check and the label into "Disalin" for 1.5 s. No clipboard (or refused): "Gagal menyalin".
export function CopyButton({ text, what }: { text: string; what: string }) {
  const [st, setSt] = useState<'idle' | 'ok' | 'fail'>('idle')
  const timer = useRef(0)
  useEffect(() => () => window.clearTimeout(timer.current), [])
  async function copy() {
    let ok = false
    try {
      await navigator.clipboard.writeText(text)
      ok = true
    } catch {
      /* no clipboard permission or insecure context */
    }
    setSt(ok ? 'ok' : 'fail')
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => setSt('idle'), 1500)
  }
  return (
    <span className="copy">
      <button type="button" className="copy-btn" data-s={st} aria-label={`Salin ${what}`} onClick={() => void copy()}>
        <Icon d={st === 'ok' ? I.check : COPY} size={14} />
        <span aria-hidden="true">{st === 'ok' ? 'Disalin' : st === 'fail' ? 'Gagal menyalin' : 'Salin'}</span>
      </button>
      <span className="sr" role="status">{st === 'ok' ? 'Disalin' : st === 'fail' ? 'Gagal menyalin' : ''}</span>
    </span>
  )
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="state empty-box">
      <h2>{title}</h2>
      {children && <div className="quiet">{children}</div>}
    </div>
  )
}

// One sentence, used wherever "Nonaktif" needs explaining.
export const OFF_WHY = 'Dimatikan sementara demi keamanan prototipe. Backend yang memutuskan kapan dibuka.'

export function BlockedBanner({ title, reason }: { title: string; reason: string }) {
  return (
    <div className="blocked" role="note">
      <CapChip cap="blocked" />
      <h2>{title}</h2>
      <p>{reason}</p>
      <p>{OFF_WHY}</p>
    </div>
  )
}

// Whole-page state for a route whose object is loading, failed or gone.
export function PageState({ what, loadState, error, reload }: { what: string; loadState: string; error: string; reload: () => void }) {
  return (
    <section className="page center-page">
      {loadState === 'loading' ? <p className="quiet">Memuat...</p> : loadState === 'error' ? <ErrorLine text={error} onRetry={reload} /> : <p className="quiet">{what} tidak ditemukan. Mungkin sudah dihapus.</p>}
    </section>
  )
}

// One fetch with loading / error / retry. `fn` must be stable (wrap in useCallback) or the fetch repeats.
export function useLoad<T>(fn: () => Promise<T>) {
  const [s, setS] = useState<{ state: 'loading' | 'ok' | 'error'; data?: T; error: string }>({ state: 'loading', error: '' })
  const [n, setN] = useState(0)
  useEffect(() => {
    let live = true
    setS((x) => (x.state === 'ok' ? x : { state: 'loading', error: '' }))
    fn().then(
      (data) => live && setS({ state: 'ok', data, error: '' }),
      (e) => live && setS({ state: 'error', error: errText(e) }),
    )
    return () => {
      live = false
    }
  }, [fn, n])
  return { ...s, retry: () => setN((x) => x + 1) }
}

// The model asked the user a question (tool clarify): the question, a button per choice, a free answer and Kirim. Same card as the approval.
export function ClarifyCard({ c, onAnswer }: { c: Clarify; onAnswer: (text: string) => Promise<void> }) {
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const send = async (a: string) => {
    if (!a.trim() || busy) return
    setBusy(true)
    try {
      await onAnswer(a.trim())
    } finally {
      setBusy(false)
    }
  }
  return (
    <form className="approval clarify" role="group" aria-label="Pegawai bertanya" onSubmit={(e) => { e.preventDefault(); void send(text) }}>
      <p className="approval-title">Pegawai bertanya</p>
      <p>{c.question}</p>
      {c.choices.length > 0 && (
        <div className="approval-actions">
          {c.choices.map((ch) => (
            <button key={ch} type="button" className="btn soft" disabled={busy} onClick={() => void send(ch)}>
              {ch}
            </button>
          ))}
        </div>
      )}
      <div className="clarify-row">
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Tulis jawaban Anda" aria-label="Jawaban Anda" maxLength={4000} disabled={busy} />
        <button className="btn primary" type="submit" disabled={busy || !text.trim()}>
          Kirim
        </button>
      </div>
    </form>
  )
}
