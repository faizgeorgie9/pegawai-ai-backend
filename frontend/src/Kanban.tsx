import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, errText } from './bff'
import type { KanbanBoard, KanbanCard } from './bff'
import { useData } from './data'
import { BotAvatar, DOTS, Dialog, ErrorLine, Icon, botColor, stamp } from './ui'
import { Empty, Loading } from './ui-extra'

const SOURCE: Record<KanbanCard['source'], string> = { chat: 'Chat', group: 'Tim', schedule: 'Jadwal', sequence: 'Evaluasi', plan: 'Rencana', hermes: 'Tugas agen' }
const OUTCOME = { failed: 'Gagal', cancelled: 'Dibatalkan' } as const
const COLUMN_HINT: Record<string, string> = {
  todo: 'Akan dikerjakan sesuai jadwal',
  running: 'Agen sedang mengerjakan',
  blocked: 'Agen menunggu persetujuan atau jawaban Anda',
  done: 'Sudah dikerjakan',
}
const COLUMN_EMPTY: Record<string, string> = {
  todo: 'Belum ada yang menunggu. Buat jadwal baru untuk memulai.',
  running: 'Tidak ada yang sedang dikerjakan.',
  blocked: 'Tidak ada yang perlu Anda putuskan.',
  done: 'Belum ada pekerjaan yang selesai.',
}
const WEEK = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']
const PERIODS: [string, string][] = [['today', 'Hari ini'], ['7d', '7 hari terakhir'], ['30d', '30 hari terakhir']]

type Ask = (a: { text: string; ok: string; run: () => Promise<unknown> }) => void
interface Act {
  label: string
  run?: () => Promise<unknown> // an action; without it the button opens `c.link`
  confirm?: string
}

// What a card offers: at most one visible button (`main`), anything else in the small menu. Hermes' own tasks offer nothing.
function actionsOf(c: KanbanCard): { main?: Act; more: Act[] } {
  const r = c.ref
  const open = c.link ? { label: c.column === 'done' ? 'Buka obrolan' : 'Tinjau' } : undefined
  const remove: Act = { label: 'Hapus jadwal', confirm: `Hapus jadwal "${c.title}"? Tugas yang belum jalan tidak akan dikerjakan.`, run: () => api.deleteSchedule(r.schedule_id) }
  const stop = (run: () => Promise<unknown>): Act => ({ label: 'Hentikan', run, confirm: `Hentikan "${c.title}"? Pekerjaan yang sedang berjalan akan berhenti.` })
  if (c.source === 'hermes') return { more: [] }
  if (c.source === 'schedule') {
    if (r.occurrence_status === 'running') return c.column === 'blocked' ? { main: open, more: [] } : { main: stop(() => api.stopOccurrence(r.occurrence_id)), more: [] }
    if (r.occurrence_status === 'planned') return { main: r.paused ? { label: 'Lanjutkan', run: () => api.scheduleAction(r.schedule_id, 'resume') } : { label: 'Jeda', run: () => api.scheduleAction(r.schedule_id, 'pause') }, more: [remove] }
    if (r.occurrence_status === 'skipped') return { more: [remove] }
    return { main: c.column === 'done' ? open : undefined, more: [] }
  }
  if (c.source === 'sequence') return { main: c.column === 'todo' || c.column === 'running' ? stop(() => api.stopSequence(r.sequence_id)) : undefined, more: [] }
  if (c.source === 'plan') return { main: open, more: [] }
  // a chat or team run
  if (c.column === 'todo' || c.column === 'running') return { main: stop(() => (r.group_id ? api.stopGroup(r.group_id) : api.stopRun(r.run_id))), more: [] }
  return { main: open, more: [] }
}

function Card({ c, ask, act }: { c: KanbanCard; ask: Ask; act: (f: () => Promise<unknown>) => Promise<void> }) {
  const [menu, setMenu] = useState(false)
  useEffect(() => {
    if (!menu) return
    const off = () => setMenu(false)
    document.addEventListener('click', off)
    return () => document.removeEventListener('click', off)
  }, [menu])
  const { main, more } = actionsOf(c)
  const go = (a: Act) => {
    setMenu(false)
    if (a.confirm) ask({ text: a.confirm, ok: a.label, run: a.run! })
    else void act(a.run!)
  }
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
      <div className="kc-link">{body}</div>
      {(main || more.length > 0) && (
        <div className="kc-act">
          {main &&
            (main.run ? (
              <button type="button" className="btn soft sm" onClick={() => go(main)}>
                {main.label}
              </button>
            ) : (
              <a className="btn soft sm" href={'#' + c.link}>
                {main.label}
              </a>
            ))}
          {more.length > 0 && (
            <span className="row-menu kc-menu">
              <button
                type="button"
                className="icon-btn"
                aria-label="Pilihan lain"
                aria-expanded={menu}
                onClick={(e) => {
                  e.stopPropagation()
                  setMenu(!menu)
                }}
              >
                <Icon d={DOTS} />
              </button>
              {menu && (
                <div className="popmenu" role="menu">
                  {more.map((a) => (
                    <button key={a.label} type="button" role="menuitem" onClick={() => go(a)}>
                      {a.label}
                    </button>
                  ))}
                </div>
              )}
            </span>
          )}
        </div>
      )}
    </li>
  )
}

function Confirm({ a, onClose }: { a: { text: string; ok: string; run: () => Promise<unknown> }; onClose: (done: boolean) => void }) {
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  async function yes() {
    setBusy(true)
    try {
      await a.run()
      onClose(true)
    } catch (e) {
      setProblem(errText(e))
      setBusy(false)
    }
  }
  return (
    <Dialog title="Yakin?" onClose={() => onClose(false)}>
      <div className="dlg-body">
        <p>{a.text}</p>
        {problem && <ErrorLine text={problem} />}
        <div className="dlg-foot">
          <button type="button" className="btn outline" onClick={() => onClose(false)}>
            Batal
          </button>
          <button type="button" className="btn primary" disabled={busy} onClick={() => void yes()}>
            {a.ok}
          </button>
        </div>
      </div>
    </Dialog>
  )
}

function NewSchedule({ onClose }: { onClose: (created: boolean) => void }) {
  const { bots, groups } = useData()
  const [prompt, setPrompt] = useState('')
  const [target, setTarget] = useState('')
  const [time, setTime] = useState('09:00')
  const [repeat, setRepeat] = useState<'daily' | 'work' | 'pick'>('work')
  const [picked, setPicked] = useState<number[]>([])
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const days = repeat === 'daily' ? [0, 1, 2, 3, 4, 5, 6] : repeat === 'work' ? [0, 1, 2, 3, 4] : picked
  const ok = prompt.trim() && target && time && days.length > 0

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!ok || busy) return
    setBusy(true)
    setProblem('')
    try {
      const [kind, id] = target.split(':')
      const title = prompt.trim().split(/\s+/).slice(0, 6).join(' ').slice(0, 80) // the name is the first words of the task
      await api.createSchedule({ title, prompt: prompt.trim(), days, time, ...(kind === 'bot' ? { bot_id: id } : { group_id: id }) })
      onClose(true)
    } catch (err) {
      setProblem(errText(err))
      setBusy(false)
    }
  }
  return (
    <Dialog title="Jadwal baru" onClose={() => onClose(false)}>
      <form className="dlg-body" onSubmit={(e) => void submit(e)}>
        <label className="field">
          <span>Apa yang perlu dikerjakan?</span>
          <textarea rows={3} maxLength={4000} value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Contoh: Rangkum pesanan masuk hari ini" />
        </label>
        <label className="field">
          <span>Siapa yang mengerjakan?</span>
          <select value={target} onChange={(e) => setTarget(e.target.value)}>
            <option value="">Pilih agen atau tim</option>
            <optgroup label="Agen">
              {bots.map((b) => (
                <option key={b.id} value={`bot:${b.id}`}>
                  {b.name}
                </option>
              ))}
            </optgroup>
            {groups.length > 0 && (
              <optgroup label="Tim">
                {groups.map((g) => (
                  <option key={g.id} value={`group:${g.id}`}>
                    {g.name}
                  </option>
                ))}
              </optgroup>
            )}
          </select>
        </label>
        <label className="field">
          <span>Kapan?</span>
          <input type="time" value={time} onChange={(e) => setTime(e.target.value)} />
        </label>
        <label className="field">
          <span>Ulangi</span>
          <select value={repeat} onChange={(e) => setRepeat(e.target.value as typeof repeat)}>
            <option value="work">Hari kerja (Sen–Jum)</option>
            <option value="daily">Setiap hari</option>
            <option value="pick">Pilih hari</option>
          </select>
        </label>
        {repeat === 'pick' && (
          <div className="chip-row" role="group" aria-label="Pilih hari">
            {WEEK.map((d, i) => (
              <button key={d} type="button" className={`btn sm ${picked.includes(i) ? 'primary' : 'outline'}`} aria-pressed={picked.includes(i)} onClick={() => setPicked((cur) => (cur.includes(i) ? cur.filter((x) => x !== i) : [...cur, i].sort()))}>
                {d}
              </button>
            ))}
          </div>
        )}
        {problem && <ErrorLine text={problem} />}
        <div className="dlg-foot">
          <button type="button" className="btn outline" onClick={() => onClose(false)}>
            Batal
          </button>
          <button type="submit" className="btn primary" disabled={!ok || busy}>
            Buat jadwal
          </button>
        </div>
      </form>
    </Dialog>
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
  const [confirm, setConfirm] = useState<{ text: string; ok: string; run: () => Promise<unknown> } | null>(null)
  const [creating, setCreating] = useState(false)
  const [problem, setProblem] = useState('')

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

  async function act(f: () => Promise<unknown>) {
    setProblem('')
    try {
      await f()
    } catch (e) {
      setProblem(errText(e))
    }
    load(true)
  }

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
          <button type="button" className="btn primary" onClick={() => setCreating(true)}>
            Jadwal baru
          </button>
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
      {problem && <ErrorLine text={problem} />}
      {creating && (
        <NewSchedule
          onClose={(created) => {
            setCreating(false)
            if (created) load(true)
          }}
        />
      )}
      {confirm && (
        <Confirm
          a={confirm}
          onClose={(done) => {
            setConfirm(null)
            if (done) load(true)
          }}
        />
      )}

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
                <p className="quiet small kb-none">{COLUMN_EMPTY[c.id]}</p>
              ) : (
                <ul>
                  {c.cards.map((x) => (
                    <Card key={x.key} c={x} ask={setConfirm} act={act} />
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
