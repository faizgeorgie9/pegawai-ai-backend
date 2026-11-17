import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, errText } from './bff'
import type { KanbanBoard, KanbanCard } from './bff'
import { useData } from './data'
import { BotAvatar, ErrorLine, botColor, stamp } from './ui'
import { Empty, Loading } from './ui-extra'

const SOURCE: Record<KanbanCard['source'], string> = { chat: 'Chat', group: 'Tim', schedule: 'Jadwal', sequence: 'Evaluasi', plan: 'Rencana', hermes: 'Tugas agen' }
const OUTCOME = { failed: 'Gagal', cancelled: 'Dibatalkan' } as const
const COLUMN_HINT: Record<string, string> = {
  todo: 'Menunggu giliran',
  running: 'Sedang dikerjakan',
  blocked: 'Butuh Anda',
  done: 'Sudah selesai',
}
const PERIODS: [string, string][] = [['today', 'Hari ini'], ['7d', '7 hari terakhir'], ['30d', '30 hari terakhir']]

function Card({ c }: { c: KanbanCard }) {
  const first = c.agents[0]
  const tone = c.outcome === 'failed' ? 'bad' : c.outcome === 'cancelled' ? 'plain' : ''
  const body = (
    <>
      <span className="kc-title">{c.title}</span>
      <span className="kc-meta">
        {c.agents.length > 0 && (
          <span className="kc-who">
            {c.agents.slice(0, 3).map((a) => (
              <BotAvatar key={a.id} bot={a} size={18} />
            ))}
            <span>{c.agents.map((a) => a.name).join(', ')}</span>
          </span>
        )}
        {c.group && <span className="kc-group">{c.group.name}</span>}
      </span>
      {c.note && <span className={`kc-note ${c.column === 'blocked' ? 'wait' : ''}`}>{c.note}</span>}
      <span className="kc-foot">
        <span className="pill plain cls">{SOURCE[c.source]}</span>
        {c.outcome && c.outcome !== 'ok' && <span className={`pill ${tone} cls`}>{OUTCOME[c.outcome]}</span>}
        <span className="kc-time num">{stamp(c.at)}</span>
        {c.cost && (
          <span className="kc-cost num">
            {c.cost.label}
            {c.estimated ? ' (perkiraan)' : ''}
          </span>
        )}
      </span>
    </>
  )
  return (
    <li className="kcard" data-col={c.column} data-bad={c.outcome === 'failed' || undefined} style={first ? ({ ['--kc' as string]: botColor(first) } as React.CSSProperties) : undefined}>
      {c.link ? (
        <a className="kc-link" href={'#' + c.link}>
          {body}
        </a>
      ) : (
        <div className="kc-link">{body}</div>
      )}
    </li>
  )
}

export default function Kanban() {
  const { bots, groups, runs } = useData()
  const [agent, setAgent] = useState('')
  const [group, setGroup] = useState('')
  const [period, setPeriod] = useState('7d')
  const [filterOpen, setFilterOpen] = useState(false)
  const [result, setResult] = useState('') // '' | 'ok' | 'bad': what the Selesai column shows
  const [board, setBoard] = useState<KanbanBoard | null>(null)
  const [state, setState] = useState<'loading' | 'ok' | 'error'>('loading')
  const [error, setError] = useState('')
  const epoch = useRef(0)

  const load = useCallback(
    (quiet = false) => {
      const mine = ++epoch.current
      if (!quiet) setState((s) => (s === 'ok' ? s : 'loading'))
      api.kanban({ agent, group, period }).then(
        (b) => {
          if (mine !== epoch.current) return
          setBoard(b)
          setState('ok')
        },
        (e) => {
          if (mine !== epoch.current) return
          setError(errText(e))
          if (!quiet) setState('error')
        },
      )
    },
    [agent, group, period],
  )
  useEffect(() => load(), [load])

  // Same live pattern as the rest of the app: the active runs (kept fresh by the global event stream) tell us when to look again,
  // and while something is on the board as running we also poll lightly (scheduler occurrences move without a page event).
  const sig = runs.map((r) => r.id).join(',')
  const seen = useRef(sig)
  useEffect(() => {
    if (seen.current === sig) return // nothing changed since the load above
    seen.current = sig
    const t = window.setTimeout(() => load(true), 600)
    return () => window.clearTimeout(t)
  }, [sig, load])
  const busy = runs.length > 0 || board?.columns.some((c) => c.id === 'running' && c.total > 0)
  useEffect(() => {
    if (!busy) return
    const id = window.setInterval(() => load(true), 8000)
    return () => window.clearInterval(id)
  }, [busy, load])

  const columns = useMemo(
    () =>
      (board?.columns ?? []).map((c) =>
        c.id === 'done' && result ? { ...c, cards: c.cards.filter((x) => (result === 'ok' ? x.outcome === 'ok' || x.source === 'hermes' : x.outcome === 'failed' || x.outcome === 'cancelled')) } : c,
      ),
    [board, result],
  )
  const total = columns.reduce((n, c) => n + c.total, 0)
  const filtered = !!(agent || group || result)

  return (
    <section className="page kanban" aria-labelledby="kb-h">
      <header className="page-head">
        <div>
          <h1 id="kb-h">Jadwal &amp; tugas</h1>
          <p className="quiet">Semua pekerjaan agen Anda dalam satu papan.</p>
        </div>
        <div className="filters">
          <label className="field inline">
            <span>Periode</span>
            <select value={period} onChange={(e) => setPeriod(e.target.value)}>
              {PERIODS.map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
          </label>
          <button type="button" className="btn outline" aria-expanded={filterOpen} aria-controls="kb-filters" onClick={() => setFilterOpen(!filterOpen)}>
            Filter{agent || group || result ? ` (${[agent, group, result].filter(Boolean).length})` : ''}
          </button>
        </div>
        <div className="filters kb-more" id="kb-filters" hidden={!filterOpen}>
          <label className="field inline">
            <span>Agen</span>
            <select value={agent} onChange={(e) => setAgent(e.target.value)}>
              <option value="">Semua agen</option>
              {bots.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field inline">
            <span>Tim</span>
            <select value={group} onChange={(e) => setGroup(e.target.value)}>
              <option value="">Semua tim</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field inline">
            <span>Hasil</span>
            <select value={result} onChange={(e) => setResult(e.target.value)}>
              <option value="">Semua hasil</option>
              <option value="ok">Berhasil</option>
              <option value="bad">Gagal atau dibatalkan</option>
            </select>
          </label>
        </div>
      </header>


      {state === 'loading' && <Loading text="Memuat papan..." shape="ledger" />}
      {state === 'error' && <ErrorLine text={error} onRetry={() => load()} />}
      {state === 'ok' && total === 0 && (
        <Empty title={filtered ? 'Tidak ada tugas yang cocok' : 'Belum ada tugas'}>
          {filtered ? 'Coba ubah filter.' : 'Pekerjaan agen muncul di sini.'}
        </Empty>
      )}
      {state === 'ok' && total > 0 && (
        <div className="kb-grid">
          {columns.map((c) => (
            <section key={c.id} className="kb-col" data-col={c.id} aria-labelledby={`kb-${c.id}`}>
              <header>
                <h2 id={`kb-${c.id}`}>
                  {c.label} <b className="num">{c.total}</b>
                </h2>
                <p className="quiet small">{COLUMN_HINT[c.id]}</p>
              </header>
              {c.cards.length === 0 ? (
                <p className="quiet small kb-none">Kosong</p>
              ) : (
                <ul>
                  {c.cards.map((x) => (
                    <Card key={x.key} c={x} />
                  ))}
                </ul>
              )}
              {c.total > c.cards.length && result === '' && <p className="quiet small">dan {c.total - c.cards.length} lainnya. Persempit dengan Filter.</p>}
            </section>
          ))}
        </div>
      )}
    </section>
  )
}
