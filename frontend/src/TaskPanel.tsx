import { useEffect, useRef, useState } from 'react'
import { api, errText } from './bff'
import type { TaskAction, TaskDetail } from './bff'
import { useAdminMode } from './adminMode'
import { useData } from './data'
import { Md } from './rich'
import { BotAvatar, Dialog, ErrorLine, Icon, stamp } from './ui'
import { Loading } from './ui-extra'

export type Ask = (a: { text: string; ok: string; run: () => Promise<unknown>; danger?: boolean }) => void

const EVENT_TEXT: Record<string, string> = {
  created: 'Tugas dibuat',
  start: 'Diminta dikerjakan',
  stop: 'Anda menghentikan tugas',
  reply: 'Anda menjawab',
  request_changes: 'Anda meminta revisi',
  approve: 'Anda menyetujui hasil',
  cancel: 'Dibatalkan',
  retry: 'Diulangi',
  archive: 'Diarsipkan',
  restore: 'Dipulihkan',
  edit: 'Diubah',
  claim: 'Pegawai mulai bekerja',
  due: 'Waktunya tiba, masuk giliran',
  run_done: 'Pegawai selesai, hasil siap ditinjau',
  run_failed: 'Percobaan gagal',
  done: 'Selesai',
  ask_user: 'Pegawai menanyakan sesuatu',
  auto_retry: 'Mencoba lagi otomatis',
  failed: 'Gagal setelah dua percobaan',
  skipped: 'Tidak bisa dijalankan',
  late: 'Terlewat',
  recover: 'Dilanjutkan setelah sistem dimulai ulang',
  replaced: 'Diganti rencana yang lebih baru',
  children: 'Mengikuti hari-harinya',
  schedule_paused: 'Tugas berulang dijeda',
  schedule_deleted: 'Tugas berulang dihapus',
}
const QUEUE = ['todo', 'scheduled', 'ready']

// epoch seconds -> value of <input type="datetime-local"> in the browser's own time
const toLocalInput = (e: number) => {
  if (!e) return ''
  const d = new Date(e * 1000)
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

function Edit({ t, onSaved, onCancel }: { t: TaskDetail; onSaved: (d: TaskDetail) => void; onCancel: () => void }) {
  const { bots, groups } = useData()
  const [title, setTitle] = useState(t.title)
  const [body, setBody] = useState(t.body)
  const [who, setWho] = useState(t.assignee ? `${t.assignee.kind}:${t.assignee.id}` : '')
  const first = toLocalInput(t.scheduled_at)
  const [at, setAt] = useState(first)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const queued = QUEUE.includes(t.status)
  async function save(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setProblem('')
    try {
      const [kind, id] = who.split(':')
      // the time is only sent when changed: an old time that has passed would be refused
      onSaved(await api.editTask(t.id, { title, body, ...(kind === 'bot' ? { assignee_bot: id } : { assignee_group: id }), ...(queued && at !== first ? { scheduled_at: at ? new Date(at).toISOString() : null } : {}) }))
    } catch (err) {
      setProblem(errText(err))
      setBusy(false)
    }
  }
  return (
    <form className="tp-edit" onSubmit={(e) => void save(e)}>
      <label className="field">
        <span>Judul</span>
        <input value={title} maxLength={120} onChange={(e) => setTitle(e.target.value)} />
      </label>
      <label className="field">
        <span>Instruksi</span>
        <textarea rows={4} maxLength={4000} value={body} onChange={(e) => setBody(e.target.value)} />
      </label>
      <label className="field">
        <span>Siapa yang mengerjakan?</span>
        <select value={who} onChange={(e) => setWho(e.target.value)}>
          {bots.map((b) => (
            <option key={b.id} value={`bot:${b.id}`}>
              {b.name}
            </option>
          ))}
          {groups.map((g) => (
            <option key={g.id} value={`group:${g.id}`}>
              Tim {g.name}
            </option>
          ))}
        </select>
      </label>
      {queued && (
        <label className="field">
          <span>Jadwal (kosongkan bila tidak perlu)</span>
          <input type="datetime-local" lang="id" value={at} onChange={(e) => setAt(e.target.value)} />
        </label>
      )}
      {problem && <ErrorLine text={problem} />}
      <div className="dlg-foot">
        <button type="button" className="btn outline" onClick={onCancel}>
          Batal
        </button>
        <button type="submit" className="btn primary" disabled={busy || !title.trim() || !who}>
          Simpan
        </button>
      </div>
    </form>
  )
}

export default function TaskPanel({ id, edit, ask, onChanged, onClose }: { id: string; edit: boolean; ask: Ask; onChanged: () => void; onClose: () => void }) {
  const { bots } = useData()
  const admin = useAdminMode()
  const [t, setT] = useState<TaskDetail | null>(null)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(edit)
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [hist, setHist] = useState(false)

  useEffect(() => {
    api.task(id).then(setT, (e) => setError(errText(e)))
  }, [id])
  // The agent works on its own: while the task waits for its turn or runs, look again every few seconds (and tell the board).
  const live = !editing && (t?.status === 'ready' || t?.status === 'running')
  const changed = useRef(onChanged)
  changed.current = onChanged
  useEffect(() => {
    if (!live) return
    const timer = window.setInterval(() => {
      api.task(id).then((d) => {
        setT(d)
        changed.current()
      }, () => undefined)
    }, 4000)
    return () => window.clearInterval(timer)
  }, [live, id])

  // every change answers with the fresh task; the board behind is told to reload
  async function run(f: () => Promise<TaskDetail>, clear = false) {
    setBusy(true)
    setError('')
    try {
      setT(await f())
      if (clear) setText('')
      onChanged()
    } catch (e) {
      setError(errText(e))
    }
    setBusy(false)
  }
  const verb = (a: TaskAction) => {
    if (!t) return
    if (a.confirm) ask({ text: a.confirm, ok: a.label, danger: a.id === 'cancel', run: async () => { setT(await api.taskVerb(t.id, a.id)); onChanged() } })
    else void run(() => api.taskVerb(t.id, a.id))
  }

  const who = (c: TaskDetail['comments'][number]) => (c.author === 'user' ? 'Anda' : c.author === 'bot' ? (bots.find((b) => b.id === c.bot_id)?.name ?? 'Pegawai') : 'Sistem')
  const actions = t ? [t.primary, ...t.more].filter((a): a is TaskAction => !!a && !['open', 'edit', 'chat'].includes(a.id)) : []
  const send = t?.status === 'blocked' ? { label: 'Kirim jawaban', go: () => api.taskVerb(t.id, 'reply', { text }) } : t?.status === 'review' ? { label: 'Minta revisi', go: () => api.taskVerb(t.id, 'request_changes', { note: text }) } : { label: 'Kirim catatan', go: () => api.commentTask(t!.id, text) }
  const worker = t?.assignee?.name ?? 'pegawai'
  const placeholder = t?.status === 'blocked' ? `Tulis jawaban untuk ${worker}…` : t?.status === 'review' ? 'Tulis catatan revisi…' : `Tulis catatan untuk ${worker}…`
  // The result often repeats the one-line summary above: showing both reads as two different things.
  const resultEchoesLine = !!t && t.result.trim() !== '' && t.result.trim().replace(/\s+/g, ' ') === t.line.trim().replace(/\s+/g, ' ')
  const reply =
    t && t.status !== 'archived' ? (
      <form
        className="tp-reply"
        onSubmit={(e) => {
          e.preventDefault()
          if (text.trim()) void run(send.go, true)
        }}
      >
        <textarea rows={2} maxLength={4000} value={text} onChange={(e) => setText(e.target.value)} placeholder={placeholder} aria-label={placeholder.replace(/…$/, '')} />
        <button type="submit" className="btn soft" disabled={busy || !text.trim()}>
          {send.label}
        </button>
      </form>
    ) : null

  return (
    <Dialog title={t?.title ?? 'Tugas'} onClose={onClose} wide>
      <div className="dlg-body tp">
        {!t && !error && <Loading text="Memuat tugas..." />}
        {error && <ErrorLine text={error} />}
        {t && (
          <>
            <p className="tp-who">
              {t.assignee && <BotAvatar bot={t.assignee} size={20} />}
              <span>{t.assignee?.name ?? 'Belum ada pengerja'}</span>
              {t.parent && <span className="quiet">· Bagian dari: {t.parent.title}</span>}
              {admin && <span className="pill plain cls">{t.status}</span>}
              {admin && <small className="quiet num">{t.id.slice(0, 8)}</small>}
            </p>
            <p className={`tp-line ${t.column === 'needs_you' ? 'wait' : ''}`}>{t.line.replace(/\bAgen\b/g, 'Pegawai')}</p>

            {editing && t.editable ? (
              <Edit t={t} onCancel={() => setEditing(false)} onSaved={(d) => { setT(d); setEditing(false); onChanged() }} />
            ) : (
              <section className="tp-sec">
                <h3>Instruksi</h3>
                <p className="tp-body">{t.body || 'Tidak ada instruksi tambahan.'}</p>
                {t.editable && (
                  <button type="button" className="btn link" onClick={() => setEditing(true)}>
                    Ubah
                  </button>
                )}
              </section>
            )}

            {t.result && !resultEchoesLine && (
              <section className="tp-sec">
                <h3>Hasil terakhir</h3>
                <div className="tp-result">
                  <Md text={t.result} />
                </div>
              </section>
            )}

            {t.children.length > 0 && (
              <section className="tp-sec">
                <h3>Bagian-bagiannya</h3>
                <ul className="tp-kids">
                  {t.children.map((k) => (
                    <li key={k.id}>
                      <b>{k.title}</b>
                      <span className="quiet small">{k.line.replace(/\bAgen\b/g, 'Pegawai')}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {t.comments.length > 0 ? (
              <section className="tp-sec">
                <h3>Percakapan</h3>
                <ul className="tp-thread">
                  {t.comments.map((c) => (
                    <li key={c.id} data-me={c.author === 'user' || undefined}>
                      <span className="quiet small">
                        {who(c)} · {stamp(c.at)}
                      </span>
                      <span className="tp-text">{c.text}</span>
                    </li>
                  ))}
                </ul>
                {reply}
              </section>
            ) : (
              // Nothing to reply to yet: keep the note box without an empty "Percakapan" heading.
              reply && <section className="tp-sec">{reply}</section>
            )}

            <section className="tp-sec">
              <button type="button" className="btn link" aria-expanded={hist} onClick={() => setHist(!hist)}>
                Riwayat
                <span className="thinking-chev" aria-hidden="true" style={hist ? { transform: 'rotate(180deg)' } : undefined}>
                  <Icon d="M6 9l6 6 6-6" size={14} />
                </span>
              </button>
              {hist && (
                <ul className="tp-hist">
                  {t.events.map((e, i) => (
                    <li key={i}>
                      <span>{EVENT_TEXT[e.kind] ?? e.kind}</span>
                      {admin && e.from && <span className="quiet small"> ({e.from} → {e.to})</span>}
                      <span className="quiet small num"> · {stamp(e.at)}</span>
                    </li>
                  ))}
                  {t.runs.map((r) => (
                    <li key={r.id}>
                      <span>Pengerjaan pegawai{r.cost ? ` · ${r.cost.label}` : ''}</span>
                      {admin && <span className="quiet small"> ({r.status} {r.id.slice(0, 8)})</span>}
                      <span className="quiet small num"> · {stamp(r.at)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {actions.length > 0 && (
              <div className="dlg-foot tp-acts">
                {t.link && t.status === 'running' && (
                  <a className="btn outline" href={'#' + t.link} onClick={onClose}>
                    Buka obrolan
                  </a>
                )}
                {[...actions].reverse().map((a, i, all) => (
                  <button key={a.id} type="button" className={`btn ${i === all.length - 1 && a === t.primary ? 'primary' : 'outline'}`} disabled={busy} onClick={() => verb(a)}>
                    {a.label}
                  </button>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </Dialog>
  )
}

// "Jadikan tugas" under a user message: the message becomes a task for that agent or team (title = its first words).
export function MakeTaskButton({ text, bot, group }: { text: string; bot?: string; group?: string }) {
  const { flash } = useData()
  const [st, setSt] = useState<'idle' | 'busy' | 'ok'>('idle')
  async function make() {
    setSt('busy')
    try {
      const words = text.trim().split(/\s+/)
      const title = words.slice(0, 8).join(' ') + (words.length > 8 ? '…' : '')
      await api.createTask({ title, body: text.trim(), ...(group ? { assignee_group: group } : { assignee_bot: bot }) })
      setSt('ok')
      flash('Tugas dibuat. Lihat di papan.', '/kanban')
    } catch (e) {
      setSt('idle')
      flash(errText(e))
    }
  }
  return (
    <button type="button" className="copy-btn make-task" disabled={st !== 'idle'} onClick={() => void make()}>
      {st === 'ok' ? 'Tugas dibuat' : 'Jadikan tugas'}
    </button>
  )
}
