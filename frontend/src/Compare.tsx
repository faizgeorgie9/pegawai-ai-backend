import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useMemo, useState } from 'react'
import type { RunMeta } from './bff'
import { diffWords } from './ResultCards'
import { ProgressLine } from './ui-extra'

// Pieces of the Evaluasi page: side-by-side run columns (with a word-level diff against the first column) and the
// collapsible "Versi & konfigurasi" snapshot.

export interface Col {
  botId: string
  botName: string
  runId: string
  sid: string
  status: 'pending' | 'running' | 'done' | 'stopped' | 'error'
  text: string
  error: string
  tokens: number
  seconds: number | null
  startedAt: number // epoch seconds, 0 when unknown
  meta: Partial<RunMeta>
}

const DIFF_MAX_WORDS = 1500 // shortcut: the LCS diff is O(n*m); above this size the columns show without highlight
const clock = (t: number) => (t ? new Date(t * 1000).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '–')
const words = (s: string) => s.split(/\s+/).filter(Boolean).length

export function CompareColumns({ cols, live }: { cols: Col[]; live: string }) {
  const [diff, setDiff] = useState(true)
  const base = cols[0]?.status === 'done' ? cols[0].text : ''
  const tooBig = cols.some((c) => words(c.text) > DIFF_MAX_WORDS)
  const canDiff = !!base && !tooBig
  const diffs = useMemo(() => cols.map((c, i) => (i > 0 && c.status === 'done' && canDiff ? diffWords(base, c.text).filter((x) => x.k !== 'del') : null)), [cols, base, canDiff])
  return (
    <div className="cmp-wrap">
      {canDiff && cols.length > 1 && (
        <label className="ws-switch">
          <input type="checkbox" checked={diff} onChange={(e) => setDiff(e.target.checked)} />
          <span>Tandai kata yang beda dari kolom pertama</span>
        </label>
      )}
      <div className="cmp-cols" style={{ ['--n' as string]: cols.length }}>
        {cols.map((c, i) => (
          <article key={i} className={`rcard${c.status === 'running' ? ' live' : ''}`}>
            <header>
              <b>{c.botName}</b>
              <span className="pill plain">Run {i + 1}</span>
              {i === 0 && cols.length > 1 && <span className="pill origin">Acuan</span>}
            </header>
            <div className="rbody">
              <dl className="cmp-meta">
                <dt>Run ID</dt>
                <dd className="num" title={c.runId}>{c.runId ? c.runId.slice(0, 8) : '–'}</dd>
                <dt>Waktu</dt>
                <dd className="num">{clock(c.startedAt)}{c.seconds !== null ? ` · ${c.seconds < 10 ? c.seconds.toFixed(1) : Math.round(c.seconds)} dtk` : ''}</dd>
                <dt>Token</dt>
                <dd className="num">{c.status === 'done' ? c.tokens.toLocaleString('id-ID') : '–'}</dd>
              </dl>
              {c.status === 'pending' && <p className="quiet">Menunggu giliran.</p>}
              {c.status === 'running' && <p className="draft-text quiet">{live || <ProgressLine label="Agen sedang bekerja" />}</p>}
              {c.status === 'done' &&
                (diff && diffs[i] ? (
                  <p className="cmp-text">{diffs[i]!.map((x, j) => (x.k === 'ins' ? <mark key={j}>{x.t} </mark> : x.t + ' '))}</p>
                ) : diff && i === 0 && canDiff ? (
                  <p className="cmp-text">{c.text || '(kosong)'}</p>
                ) : (
                  <div className="md"><Markdown remarkPlugins={[remarkGfm]}>{c.text || '(kosong)'}</Markdown></div>
                ))}
              {(c.status === 'error' || c.status === 'stopped') && <p className="err-text">{c.status === 'stopped' ? 'Dihentikan.' : c.error || 'Agen belum berhasil menyelesaikan tugas ini.'}</p>}
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}

const MODE_LABEL: Record<string, string> = { plain: 'Biasa (plain)', terstruktur: 'Eksperimen terstruktur' }
const ROWS: { key: keyof RunMeta; label: string }[] = [
  { key: 'hermes_version', label: 'Versi Hermes' },
  { key: 'model', label: 'Model' },
  { key: 'provider', label: 'Penyedia' },
  { key: 'bot_id', label: 'Agen' },
  { key: 'soul_hash', label: 'Hash persona' },
  { key: 'toolsets', label: 'Toolset aktif' },
  { key: 'instructions_mode', label: 'Mode instruksi' },
  { key: 'bff_commit', label: 'Commit BFF' },
]
const UNKNOWN = 'tidak diketahui'

export function metaValue(m: Partial<RunMeta>, key: keyof RunMeta): string {
  const v = m[key]
  if (key === 'toolsets') return Array.isArray(v) ? v.join(', ') || 'tidak ada' : UNKNOWN
  if (key === 'instructions_mode') return typeof v === 'string' && v ? (MODE_LABEL[v] ?? v) : UNKNOWN
  return typeof v === 'string' && v ? v : UNKNOWN
}

export function Versions({ items, open }: { items: { label: string; meta: Partial<RunMeta> }[]; open?: boolean }) {
  const shown = ROWS.filter((r) => r.key !== 'bff_commit' || items.some((i) => i.meta.bff_commit))
  return (
    <details className="ver" open={open}>
      <summary>Versi &amp; konfigurasi</summary>
      <div className="ver-grid">
        {items.map((it, i) => (
          <dl key={i}>
            {items.length > 1 && <dt className="ver-head">{it.label}</dt>}
            {shown.map((r) => (
              <div key={r.key}>
                <dt>{r.label}</dt>
                <dd className="num">{metaValue(it.meta, r.key)}</dd>
              </div>
            ))}
          </dl>
        ))}
      </div>
    </details>
  )
}
