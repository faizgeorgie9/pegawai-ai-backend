import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import type { Bot } from './bff'

export const nf = new Intl.NumberFormat('id-ID')
const rtf = new Intl.RelativeTimeFormat('id', { numeric: 'auto' })
export function ago(epoch: number): string {
  if (!epoch) return ''
  const s = Math.round(epoch - Date.now() / 1000)
  const a = Math.abs(s)
  if (a < 60) return 'baru saja'
  if (a < 3600) return rtf.format(Math.round(s / 60), 'minute')
  if (a < 86400) return rtf.format(Math.round(s / 3600), 'hour')
  if (a < 86400 * 30) return rtf.format(Math.round(s / 86400), 'day')
  return rtf.format(Math.round(s / (86400 * 30)), 'month')
}
export const clock = (epoch: number) => new Date(epoch * 1000).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
export const stamp = (epoch: number) =>
  epoch ? new Date(epoch * 1000).toLocaleString('id-ID', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '–'
export const elapsed = (epoch: number, now: number) => {
  const s = Math.max(0, Math.round(now / 1000 - epoch))
  return s < 60 ? `${s} dtk` : `${Math.floor(s / 60)} mnt ${s % 60} dtk`
}

// A bot's colour arrives as a name (the BFF's palette) or a hex string; anything else falls back to the accent.
export const COLORS: Record<string, string> = {
  amber: '#d97706',
  teal: '#0d9488',
  indigo: '#3b82f6',
  sky: '#0ea5e9',
  rose: '#b8336a',
  green: '#059669',
  red: '#dc2626',
  slate: '#64748b',
}
export const botColor = (b?: Pick<Bot, 'color'>) => (b ? (COLORS[b.color.toLowerCase()] ?? (/^#[0-9a-f]{3,8}$/i.test(b.color) ? b.color : '#b8336a')) : '#b8336a')

// Team ids arrive as slugs ("customer_support"); show them as words.
const TEAM_LABELS: Record<string, string> = { marketing: 'Marketing', customer_support: 'Customer Service' }
export const teamLabel = (t: string) => TEAM_LABELS[t] ?? (t ? t.charAt(0).toUpperCase() + t.slice(1).replace(/_/g, ' ') : 'Tanpa tim')

export function BotAvatar({ bot, size = 32 }: { bot?: Pick<Bot, 'name' | 'color'>; size?: number }) {
  return (
    <span
      className="bot-avatar"
      style={{ ['--bot' as string]: botColor(bot), width: size, height: size, fontSize: Math.round(size * 0.45) }}
      aria-hidden="true"
    >
      {(bot?.name ?? '?').charAt(0)}
    </span>
  )
}

export const Icon = ({ d, size = 16 }: { d: string; size?: number }) => (
  <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d={d} />
  </svg>
)
export const PENCIL = 'M4 20h4L19 9l-4-4L4 16v4zM14 6l4 4'
export const TRASH = 'M5 7h14M10 7V4h4v3M7 7l1 13h8l1-13'
export const PLUS = 'M12 5v14M5 12h14'
export const MENU = 'M4 7h16M4 12h16M4 17h16'
export const CLOSE = 'M6 6l12 12M18 6L6 18'
export const DOTS = 'M12 6h.01M12 12h.01M12 18h.01'
export const CHEVRON = 'M9 6l6 6-6 6'

// Native <dialog>: focus trap, Esc and inert background come from the browser. Full screen under 640 px (CSS).
export function Dialog({ title, onClose, children, wide }: { title: string; onClose: () => void; children: ReactNode; wide?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const d = ref.current
    if (d && !d.open) d.showModal()
  }, [])
  return (
    <dialog ref={ref} className="dlg" data-wide={wide || undefined} onClose={onClose} onClick={(e) => e.target === ref.current && ref.current?.close()}>
      <div className="dlg-in">
        <header className="dlg-head">
          <h2>{title}</h2>
          <button className="icon-btn" aria-label="Tutup" onClick={() => ref.current?.close()}>
            <Icon d={CLOSE} />
          </button>
        </header>
        {children}
      </div>
    </dialog>
  )
}

export function ErrorLine({ text, onRetry }: { text: string; onRetry?: () => void }) {
  return (
    <div className="state error" role="alert">
      <p>{text}</p>
      {onRetry && (
        <button className="btn link" onClick={onRetry}>
          Coba lagi
        </button>
      )}
    </div>
  )
}

// Claude-style thinking block: one quiet summary line, expands to the steps (separated by blank lines).
function thinkSummary(text: string): string {
  const last = text.split(/\n\s*\n/).map((x) => x.trim()).filter(Boolean).pop() ?? ''
  const flat = last.replace(/[*_`#>]/g, '').replace(/\s+/g, ' ')
  const first = flat.match(/^.*?[.!?](?=\s|$)/)?.[0] ?? flat
  return first.length > 80 ? first.slice(0, 79).trimEnd() + '…' : first
}
const dur = (s: number) => (s >= 60 ? `${Math.floor(s / 60)} mnt ${s % 60} dtk` : `${s} dtk`)
export function ThinkingBlock({ text, running, seconds, defaultOpen }: { text: string; running: boolean; seconds?: number; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(!!defaultOpen)
  useEffect(() => setOpen(!!defaultOpen), [defaultOpen])
  const steps = text.split(/\n\s*\n/).map((x) => x.trim()).filter(Boolean)
  if (!steps.length && !running) return null
  const sum = thinkSummary(text)
  const title = seconds ? `Berpikir selama ${dur(seconds)}` : 'Proses berpikir'
  return (
    <div className="thinking" data-running={running || undefined}>
      <button type="button" className="thinking-head" aria-expanded={open} onClick={() => setOpen(!open)}>
        <span className="thinking-label">{running ? (sum ? `Sedang berpikir: ${sum}` : 'Sedang berpikir…') : sum || title}</span>
        <span className="thinking-chev" aria-hidden="true">
          <Icon d="M6 9l6 6 6-6" size={14} />
        </span>
      </button>
      {open && (
        <div className="thinking-box">
          <p className="thinking-title">{running ? 'Sedang berpikir…' : title}</p>
          {steps.map((t, i) => (
            <p key={i}>{t}</p>
          ))}
        </div>
      )}
    </div>
  )
}
