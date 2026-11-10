import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { errText } from './bff'
import { ErrorLine, I, Icon } from './ui'
import type { Bot } from './bff'

// Shared page pieces for the Sprint 3 pages.

// Status in words, from /api/bots. "Sedang berpikir" and "Menunggu izin" exist only in the run stream (open chat), not in the list.
export function statusText(b: Pick<Bot, 'status' | 'activity' | 'deleteError'>): string {
  if (b.deleteError) return 'Gagal dihapus. Coba hapus lagi.'
  if (b.status === 'working') return b.activity ? `Sedang bekerja: ${b.activity}` : 'Sedang bekerja'
  if (b.status === 'discussing') return b.activity ? `Berdiskusi di grup: ${b.activity}` : 'Berdiskusi di grup'
  return 'Siap'
}

// Marks an optional field label. Forms where most fields are required mark only the optional ones.
export const Opt = () => <em className="req">(opsional)</em>

export type Cap = 'ok' | 'mock' | 'none' | 'blocked' | 'unknown'
// Status words: Berfungsi / Simulasi / Nonaktif (the rest only when the state is truly not known).
const CAP_LABEL: Record<Cap, string> = { ok: 'Berfungsi', mock: 'Simulasi', none: 'Belum didukung', blocked: 'Nonaktif', unknown: 'Tidak diketahui' }
export function CapChip({ cap, label }: { cap: Cap; label?: string }) {
  return <span className={`pill cap-${cap}`}>{label ?? CAP_LABEL[cap]}</span>
}

// Every fixture carries this badge.
export const SampleBadge = () => <span className="pill sample" title="Isi buatan frontend untuk menunjukkan bentuk hasil. Bukan hasil agen.">Contoh data</span>

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

// Waiting mark: four dots in a 2x2 grid, one lit at a time going clockwise (opacity only, so nothing bounces).
export const Spinner = () => (
  <span className="spin4" aria-hidden="true">
    <i /><i /><i /><i />
  </span>
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
