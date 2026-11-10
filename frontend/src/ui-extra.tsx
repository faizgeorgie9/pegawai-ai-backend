import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { errText } from './bff'
import { ErrorLine } from './ui'
import type { Bot } from './bff'

// Shared page pieces for the Sprint 3 pages.

// Status in words, from /api/bots. "Sedang berpikir" and "Menunggu izin" exist only in the run stream (open chat), not in the list.
export function statusText(b: Pick<Bot, 'status' | 'activity' | 'deleteError'>): string {
  if (b.deleteError) return 'Gagal dihapus. Coba hapus lagi.'
  if (b.status === 'working') return b.activity ? `Sedang bekerja: ${b.activity}` : 'Sedang bekerja'
  if (b.status === 'discussing') return b.activity ? `Berdiskusi di grup: ${b.activity}` : 'Berdiskusi di grup'
  return 'Siap'
}

// Marks a required field label.
export const Req = () => <em className="req">wajib</em>

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

export const Loading = ({ text = 'Memuat...' }: { text?: string }) => (
  <p className="quiet state" role="status">
    {text}
  </p>
)

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
