import { useCallback, useEffect, useRef, useState } from 'react'
import { api, errText } from './bff'
import type { Schedule, TaskAction, TaskBoard, TaskCard, TaskColumnId } from './bff'
import { useAdminMode } from './adminMode'
import { useData } from './data'
import TaskPanel from './TaskPanel'
import type { Ask } from './TaskPanel'
import { BotAvatar, DOTS, Dialog, ErrorLine, Icon, botColor } from './ui'
import { Empty, Loading } from './ui-extra'

const COLUMN_EMPTY: Record<string, string> = {
  queue: 'Belum ada yang antre.',
  running: 'Tidak ada yang sedang dikerjakan.',
  needs_you: 'Tidak ada yang perlu Anda putuskan.',
  done: 'Belum ada pekerjaan yang selesai.',
  archived: 'Arsip masih kosong.',
}
// The BFF's hint text still says "Agen"; the board speaks about pegawai.
const COLUMN_HINT: Record<string, string> = {
  running: 'Pegawai sedang mengerjakan',
  needs_you: 'Pegawai menunggu persetujuan atau jawaban Anda',
}
const WEEK = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']
const ZONE: Record<string, string> = { 'Asia/Jakarta': 'WIB', 'Asia/Makassar': 'WITA', 'Asia/Jayapura': 'WIT' }
// only these two moves can be dragged (Perlu Anda -> Antre, Selesai -> Antre); Dikerjakan is never a drop target
const DRAGGABLE = ['needs_you', 'done'] // a plan is never dragged: it is approved, revised or cancelled

type Open = (id: string, edit?: boolean) => void

// Four columns become four tabs under 1100 px (phones and narrow windows): one column at a time, the list scrolls itself.
function useNarrow() {
  const [on, setOn] = useState(() => window.matchMedia('(max-width: 1100px)').matches)
  useEffect(() => {
    const m = window.matchMedia('(max-width: 1100px)')
    const change = () => setOn(m.matches)
    m.addEventListener('change', change)
    return () => m.removeEventListener('change', change)
  }, [])
  return on
}

function Card({ c, ask, act, open }: { c: TaskCard; ask: Ask; act: (f: () => Promise<unknown>) => Promise<void>; open: Open }) {
  const admin = useAdminMode()
  const [menu, setMenu] = useState(false)
  const [pos, setPos] = useState<{ top?: number | 'auto'; bottom?: number | 'auto'; right: number } | null>(null)
  const moreBtn = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (!menu) return
    const off = () => setMenu(false)
    document.addEventListener('click', off)
    document.addEventListener('scroll', off, true) // a scrolling list would leave the fixed menu behind
    return () => {
      document.removeEventListener('click', off)
      document.removeEventListener('scroll', off, true)
    }
  }, [menu])
  const go = (a: TaskAction) => {
    setMenu(false)
    if (a.id === 'open') open(c.id)
    else if (a.id === 'edit') open(c.id, true)
    else if (a.id === 'chat') window.location.hash = c.link
    else if (a.confirm) ask({ text: a.confirm, ok: a.label, run: () => api.taskVerb(c.id, a.id) })
    else void act(() => api.taskVerb(c.id, a.id))
  }
  const tone = c.outcome === 'failed' ? 'bad' : 'plain'
  const drag = DRAGGABLE.includes(c.column) && c.kind !== 'plan'
  return (
    <li
      className="kcard"
      data-col={c.column}
      data-bad={c.outcome === 'failed' || undefined}
      draggable={drag}
      onDragStart={(e) => {
        e.dataTransfer.setData('text/plain', c.id)
        e.dataTransfer.effectAllowed = 'move'
      }}
      style={c.assignee ? ({ ['--kc' as string]: botColor(c.assignee) } as React.CSSProperties) : undefined}
    >
      <button type="button" className="kc-link" onClick={() => open(c.id)}>
        <span className="kc-title">{c.title}</span>
        {c.parent && <span className="kc-parent">Bagian dari: {c.parent.title}</span>}
        <span className="kc-meta">
          {c.assignee && (
            <span className="kc-who">
              <BotAvatar bot={c.assignee} size={18} />
              <span>{c.assignee.name}</span>
            </span>
          )}
        </span>
        <span className={`kc-note ${c.column === 'needs_you' ? 'wait' : ''}`}>{c.line.replace(/\bAgen\b/g, 'Pegawai')}</span>
        {(c.priority > 0 || c.outcome === 'failed' || c.outcome === 'cancelled' || admin) && (
          <span className="kc-foot">
            {c.priority > 0 && <span className="pill warn cls">Penting</span>}
            {c.outcome && c.outcome !== 'ok' && <span className={`pill ${tone} cls`}>{c.outcome === 'failed' ? 'Gagal' : 'Dibatalkan'}</span>}
            {admin && <span className="pill plain cls">{c.status}</span>}
          </span>
        )}
      </button>
      {(c.primary || c.more.length > 0 || c.cost) && (
        <div className="kc-act">
          {c.cost && (
            <span className="kc-cost num">
              {c.cost.label}
              {c.estimated ? ' (perkiraan)' : ''}
            </span>
          )}
          {c.primary && (
            <button type="button" className="btn soft sm" onClick={() => go(c.primary!)}>
              {c.primary.label}
            </button>
          )}
          {c.more.length > 0 && (
            <span
              className="row-menu kc-menu"
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  setMenu(false)
                  moreBtn.current?.focus()
                }
              }}
            >
              <button
                ref={moreBtn}
                type="button"
                className="icon-btn"
                aria-label="Pilihan lain"
                aria-haspopup="menu"
                aria-expanded={menu}
                onClick={(e) => {
                  e.stopPropagation()
                  if (menu) return setMenu(false)
                  const r = e.currentTarget.getBoundingClientRect()
                  const up = r.bottom + 4 + c.more.length * 40 + 8 > window.innerHeight
                  setPos(up ? { top: 'auto', bottom: window.innerHeight - r.top + 4, right: window.innerWidth - r.right } : { top: r.bottom + 4, bottom: 'auto', right: window.innerWidth - r.right })
                  setMenu(true)
                }}
              >
                <Icon d={DOTS} />
              </button>
              {menu && (
                <div className="popmenu" role="menu" style={pos ? { position: 'fixed', ...pos } : undefined}>
                  {c.more.map((a) => (
                    <button key={a.id} type="button" role="menuitem" data-danger={a.id === 'cancel' || undefined} onClick={() => go(a)}>
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

// The next full hour, as the value of <input type="datetime-local">: opening "Jadwalkan" starts from a real time,
// never from the browser's English mm/dd/yyyy placeholder.
const nextHour = () => {
  const d = new Date(Date.now() + 3_600_000)
  d.setMinutes(0, 0, 0)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
}

// Quick add on one line above the board: a title, who does it, an optional time. Enter saves.
function QuickAdd({ agent, onAdded }: { agent: string; onAdded: () => void }) {
  const { bots, groups } = useData()
  const [title, setTitle] = useState('')
  const [who, setWho] = useState('')
  const [at, setAt] = useState('')
  const [sched, setSched] = useState(false)
  const [opts, setOpts] = useState(false)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const titleRef = useRef<HTMLInputElement>(null)
  const target = who || (agent ? `bot:${agent}` : bots[0] ? `bot:${bots[0].id}` : '')
  const whoName = target.startsWith('bot:') ? bots.find((b) => `bot:${b.id}` === target)?.name : groups.find((g) => `group:${g.id}` === target)?.name
  const when = at ? new Date(at).toLocaleString('id-ID', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : ''
  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim() || !target || busy) return
    setBusy(true)
    setProblem('')
    try {
      const [kind, id] = target.split(':')
      await api.createTask({ title: title.trim(), ...(kind === 'bot' ? { assignee_bot: id } : { assignee_group: id }), ...(at ? { scheduled_at: new Date(at).toISOString() } : {}) })
      setTitle('')
      setAt('')
      setSched(false)
      onAdded()
      titleRef.current?.focus()
    } catch (err) {
      setProblem(errText(err))
    }
    setBusy(false)
  }
  return (
    <form className="tq-add tq-bar" onSubmit={(e) => void submit(e)}>
      <input ref={titleRef} className="tq-title" value={title} maxLength={120} onChange={(e) => setTitle(e.target.value)} placeholder="Tugas baru, lalu tekan Enter" aria-label="Judul tugas baru" />
      <button type="submit" className="btn primary tq-go" disabled={!title.trim() || !target || busy}>
        {busy ? 'Menambah...' : 'Tambah'}
      </button>
      <button type="button" className="btn link sm tq-toggle" aria-expanded={opts} aria-controls="tq-opts" onClick={() => setOpts((v) => !v)}>
        Untuk {whoName ?? 'pegawai'}{when ? ` · ${when}` : ''} · Ubah
      </button>
      <div id="tq-opts" className="tq-opts" data-open={opts || undefined}>
        <select className="tq-who" aria-label="Dikerjakan oleh" value={target} onChange={(e) => setWho(e.target.value)}>
          <optgroup label="Pegawai">
            {bots.map((b) => (
              <option key={b.id} value={`bot:${b.id}`}>
                {b.name}
              </option>
            ))}
          </optgroup>
          <optgroup label="Tim">
            {groups.map((g) => (
              <option key={g.id} value={`group:${g.id}`}>
                {g.name}
              </option>
            ))}
          </optgroup>
        </select>
        {sched ? (
          <>
            <input
              type="datetime-local"
              lang="id"
              value={at}
              aria-label="Mulai pada"
              onChange={(e) => setAt(e.target.value)}
            />
            <button
              type="button"
              className="btn link sm"
              onClick={() => {
                setSched(false)
                setAt('')
              }}
            >
              Hapus jadwal
            </button>
          </>
        ) : (
          <button
            type="button"
            className="btn outline"
            onClick={() => {
              setSched(true)
              setAt(nextHour())
            }}
          >
            Jadwalkan
          </button>
        )}
      </div>
      {problem && <ErrorLine text={problem} />}
    </form>
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
    <Dialog title="Tugas berulang" onClose={() => onClose(false)}>
      <form className="dlg-body" onSubmit={(e) => void submit(e)}>
        <label className="field">
          <span>Apa yang perlu dikerjakan?</span>
          <textarea rows={3} maxLength={4000} value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Contoh: Rangkum pesanan masuk hari ini" />
        </label>
        <label className="field">
          <span>Siapa yang mengerjakan?</span>
          <select value={target} onChange={(e) => setTarget(e.target.value)}>
            <option value="">Pilih pegawai atau tim</option>
            <optgroup label="Pegawai">
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
            Buat tugas berulang
          </button>
        </div>
      </form>
    </Dialog>
  )
}

const rhythm = (s: Schedule) => `${s.days.length === 7 ? 'Setiap hari' : s.days.join() === '0,1,2,3,4' ? 'Hari kerja' : s.days.map((d) => WEEK[d]).join(', ')}, ${s.time.replace(':', '.')} ${ZONE[s.timezone] ?? ''}`

// The templates behind Tugas berulang: each time they come up, a task appears in Antre. Pausing or deleting one archives the days not started.
// The list lives in a dialog opened from the header (the board never gains an extra row above it).
function RecurringList({ list, ask, act }: { list: Schedule[]; ask: Ask; act: (f: () => Promise<unknown>) => Promise<void> }) {
  return (
    <ul className="kb-rec-list">
      {list.map((s) => (
        <li key={s.id}>
          <span className="kb-rec-main">
            <b>{s.title}</b>
            <small className="quiet">
              {s.target} · {rhythm(s)}
              {s.status === 'paused' && ' · Dijeda'}
            </small>
          </span>
          <span className="sched-actions">
            {s.status === 'active' ? (
              <button type="button" className="btn soft sm" onClick={() => void act(() => api.scheduleAction(s.id, 'pause'))}>
                Jeda
              </button>
            ) : (
              <button type="button" className="btn soft sm" onClick={() => void act(() => api.scheduleAction(s.id, 'resume'))}>
                Lanjutkan
              </button>
            )}
            <button type="button" className="btn link sm" onClick={() => ask({ text: `Hapus tugas berulang "${s.title}"? Tugas yang belum dimulai ikut dihapus dari antrean.`, ok: 'Hapus', run: () => api.deleteSchedule(s.id) })}>
              Hapus
            </button>
          </span>
        </li>
      ))}
    </ul>
  )
}

export default function Kanban() {
  const { bots, groups, runs } = useData()
  const [agent, setAgent] = useState('')
  const [group, setGroup] = useState('')
  const [archived, setArchived] = useState(false)
  const [filterOpen, setFilterOpen] = useState(false)
  const [board, setBoard] = useState<TaskBoard | null>(null)
  const [rec, setRec] = useState<Schedule[]>([])
  const [state, setState] = useState<'loading' | 'ok' | 'error'>('loading')
  const [error, setError] = useState('')
  const epoch = useRef(0)
  const [confirm, setConfirm] = useState<{ text: string; ok: string; run: () => Promise<unknown> } | null>(null)
  const [creating, setCreating] = useState(false)
  const [recOpen, setRecOpen] = useState(false)
  const [opened, setOpened] = useState<{ id: string; edit: boolean } | null>(null)
  const [problem, setProblem] = useState('')
  const [notice, setNotice] = useState('')
  const [over, setOver] = useState(false)
  const narrow = useNarrow()
  const [tabCol, setTabCol] = useState<TaskColumnId>('queue')
  const picked = useRef(false)

  const load = useCallback(
    (quiet = false) => {
      const mine = ++epoch.current
      if (!quiet) setState((s) => (s === 'ok' ? s : 'loading'))
      api.schedules().then(setRec, () => undefined) // the list of Tugas berulang is a side note: the board loads without it
      api.tasksBoard({ agent, group, archived }).then(
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
    [agent, group, archived],
  )
  useEffect(() => load(), [load])

  // The first board chooses the tab: work waiting for the owner comes first when there is any.
  useEffect(() => {
    if (!board || picked.current) return
    if ((board.columns.find((c) => c.id === 'needs_you')?.total ?? 0) > 0) setTabCol('needs_you')
    picked.current = true
  }, [board])
  useEffect(() => {
    if (recOpen && rec.length === 0) setRecOpen(false)
  }, [rec.length, recOpen])

  async function act(f: () => Promise<unknown>) {
    setProblem('')
    try {
      await f()
    } catch (e) {
      setProblem(errText(e))
    }
    load(true)
  }

  // Same live pattern as the rest of the app: active runs tell us when to look again; while something is running we also poll lightly.
  const sig = runs.map((r) => r.id).join(',')
  const seen = useRef(sig)
  useEffect(() => {
    if (seen.current === sig) return
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

  const columns = board?.columns ?? []
  const total = columns.reduce((n, c) => n + c.total, 0)
  const filtered = !!(agent || group)
  const filters = [agent, group, archived].filter(Boolean).length
  const panel = narrow && !archived

  return (
    <section className="page kanban" aria-labelledby="kb-h">
      <header className="page-head head-inline">
        <div>
          <h1 id="kb-h">Jadwal &amp; tugas</h1>
          <p className="quiet">Beri tugas ke pegawai AI Anda dan pantau sampai selesai.</p>
        </div>
        <div className="filters">
          <button
            type="button"
            className="btn outline"
            aria-label={rec.length ? `Tugas berulang, ${rec.length}` : 'Tugas berulang'}
            onClick={() => (rec.length ? setRecOpen(true) : setCreating(true))}
          >
            <span><span className="hide-sm">Tugas </span>berulang</span>
            {rec.length > 0 && <b className="num count-pill hide-sm">{rec.length}</b>}
          </button>
          <button type="button" className="btn outline" aria-expanded={filterOpen} aria-controls="kb-filters" onClick={() => setFilterOpen(!filterOpen)}>
            Filter{filters ? ` (${filters})` : ''}
          </button>
        </div>
        <div className="filters kb-more" id="kb-filters" hidden={!filterOpen}>
          <label className="field inline">
            <span>Pegawai</span>
            <select value={agent} onChange={(e) => setAgent(e.target.value)}>
              <option value="">Semua pegawai</option>
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
            <span>Tampilkan</span>
            <select value={archived ? 'arsip' : 'papan'} onChange={(e) => setArchived(e.target.value === 'arsip')}>
              <option value="papan">Papan tugas</option>
              <option value="arsip">Arsip</option>
            </select>
          </label>
        </div>
      </header>
      {notice && (
        <p className="state ok" role="status">
          {notice}
        </p>
      )}
      {problem && <ErrorLine text={problem} />}
      {!archived && <QuickAdd agent={agent} onAdded={() => load(true)} />}
      {creating && (
        <NewSchedule
          onClose={(created) => {
            setCreating(false)
            if (created) {
              setNotice('Tugas berulang dibuat. Tugas untuk beberapa hari ke depan muncul di Antre.')
              load(true)
            }
          }}
        />
      )}
      {recOpen && (
        <Dialog title="Tugas berulang" onClose={() => setRecOpen(false)}>
          <div className="dlg-body">
            <RecurringList list={rec} ask={setConfirm} act={act} />
            <div className="dlg-foot">
              <button
                type="button"
                className="btn primary"
                onClick={() => {
                  setRecOpen(false)
                  setCreating(true)
                }}
              >
                Tugas berulang baru
              </button>
            </div>
          </div>
        </Dialog>
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
      {opened && <TaskPanel key={opened.id + String(opened.edit)} id={opened.id} edit={opened.edit} ask={setConfirm} onChanged={() => load(true)} onClose={() => setOpened(null)} />}

      {state === 'loading' && (
        <div className="kb-load">
          <Loading text="Memuat papan..." shape="ledger" rows={3} />
        </div>
      )}
      {state === 'error' && <ErrorLine text={error} onRetry={() => load()} />}
      {state === 'ok' && archived && total === 0 && <Empty title="Arsip kosong">Tugas yang diarsipkan atau dibatalkan muncul di sini.</Empty>}
      {state === 'ok' && narrow && !archived && (
        <div
          className="tabs kb-tabs"
          role="tablist"
          aria-label="Kolom tugas"
          onKeyDown={(e) => {
            const ids = columns.map((c) => c.id)
            const i = ids.indexOf(tabCol)
            const next =
              e.key === 'ArrowRight' ? (i + 1) % ids.length : e.key === 'ArrowLeft' ? (i - 1 + ids.length) % ids.length : e.key === 'Home' ? 0 : e.key === 'End' ? ids.length - 1 : -1
            if (next < 0) return
            e.preventDefault()
            picked.current = true
            setTabCol(ids[next])
            document.getElementById(`kbt-${ids[next]}`)?.focus()
          }}
        >
          {columns.map((c) => (
            <button
              key={c.id}
              id={`kbt-${c.id}`}
              type="button"
              role="tab"
              aria-selected={tabCol === c.id}
              aria-controls={`kb-${c.id}-body`}
              tabIndex={tabCol === c.id ? 0 : -1}
              onClick={() => {
                picked.current = true
                setTabCol(c.id)
              }}
            >
              {c.label} <b className={'num' + (c.id === 'needs_you' && c.total > 0 ? ' pill warn' : '')}>{c.total}</b>
            </button>
          ))}
        </div>
      )}
      {state === 'ok' && !(archived && total === 0) && (
        <div className="kb-grid" data-one={archived || undefined}>
          {columns.map((c) => (
            <section
              key={c.id}
              className="kb-col"
              id={`kb-${c.id}-body`}
              data-col={c.id}
              data-over={(c.id === 'queue' && over) || undefined}
              hidden={panel && tabCol !== c.id}
              role={panel ? 'tabpanel' : undefined}
              aria-labelledby={panel ? `kbt-${c.id}` : `kb-${c.id}`}
              onDragOver={(e) => {
                if (c.id !== 'queue') return
                e.preventDefault()
                setOver(true)
              }}
              onDragLeave={() => setOver(false)}
              onDrop={(e) => {
                setOver(false)
                if (c.id !== 'queue') return
                e.preventDefault()
                const id = e.dataTransfer.getData('text/plain')
                if (id) void act(() => api.taskVerb(id, 'move', { to: 'queue' }))
              }}
            >
              <header>
                <h2 id={`kb-${c.id}`} title={COLUMN_HINT[c.id] ?? c.hint}>
                  {c.label} <b className="num">{c.total}</b>
                </h2>
                <p className="sr kb-hint">{COLUMN_HINT[c.id] ?? c.hint}</p>
              </header>
              {c.cards.length === 0 ? (
                <p className="quiet small kb-none">
                  {filtered ? (
                    <>
                      Tidak ada yang cocok dengan filter.{' '}
                      <button
                        type="button"
                        className="btn link small"
                        onClick={() => {
                          setAgent('')
                          setGroup('')
                        }}
                      >
                        Hapus filter
                      </button>
                    </>
                  ) : (
                    (COLUMN_EMPTY[c.id] ?? c.hint)
                  )}
                </p>
              ) : (
                <ul className="kb-cards">
                  {c.cards.map((x) => (
                    <Card key={x.id} c={x} ask={setConfirm} act={act} open={(id, edit = false) => setOpened({ id, edit })} />
                  ))}
                </ul>
              )}
              {c.total > c.cards.length && <p className="quiet small kb-note">dan {c.total - c.cards.length} lainnya. Persempit dengan Filter.</p>}
            </section>
          ))}
        </div>
      )}
    </section>
  )
}
