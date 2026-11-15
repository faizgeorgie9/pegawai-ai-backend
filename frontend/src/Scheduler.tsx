import { useCallback, useEffect, useState } from 'react'
import { api, errText } from './bff'
import type { OccStatus, Occurrence, Schedule } from './bff'
import { useData } from './data'
import { ErrorLine } from './ui'
import { Empty, Loading, useLoad } from './ui-extra'

const DAYS = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
const ZONE: Record<string, string> = { 'Asia/Jakarta': 'WIB', 'Asia/Makassar': 'WITA', 'Asia/Jayapura': 'WIT' }
const OCC: Record<OccStatus, [string, string]> = {
  planned: ['Terjadwal', 'plain'],
  running: ['Berjalan', 'run'],
  done: ['Selesai', 'ok'],
  skipped: ['Dilewati', 'warn'],
  failed: ['Gagal', 'bad'],
  cancelled: ['Dibatalkan', 'plain'],
}
const SCHED: Record<Schedule['status'], [string, string]> = { active: ['Aktif', 'ok'], paused: ['Dijeda', 'warn'], cancelled: ['Dibatalkan', 'plain'] }

const when = (epoch: number, tz: string) =>
  epoch ? new Date(epoch * 1000).toLocaleString('id-ID', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: tz }) + ' ' + (ZONE[tz] ?? '') : '–'

function rhythm(s: Schedule) {
  if (s.kind === 'plan') return `Rencana konten, ${s.occurrences.length} hari`
  const names = s.days.length === 7 ? 'Setiap hari' : 'Setiap ' + s.days.map((d) => DAYS[d]).join(', ')
  return `${names}, ${s.time.replace(':', '.')} ${ZONE[s.timezone] ?? ''}`
}

function OccRow({ o, tz, onStop }: { o: Occurrence; tz: string; onStop: () => void }) {
  const [label, tone] = OCC[o.status]
  return (
    <tr>
      <td data-label="Kapan">{when(o.planned_at, tz)}</td>
      <td data-label="Agen">{o.agents.length ? o.agents.join(', ') : 'Sesuai jadwal'}</td>
      <td data-label="Tugas" className="rich">
        {o.title && o.title !== o.brief && <b>{o.title}</b>}
        <div className="clamp2" title={o.brief}>{o.brief}</div>
      </td>
      <td className="st-col rich" data-label="Status">
        <span className={`pill ${tone}`}>{label}</span>
        {o.skip_reason && <div className="quiet small">{o.skip_reason}</div>}
      </td>
      <td data-label="Biaya">{o.cost ? `${o.cost.label}${o.estimated ? ' (perkiraan)' : ''}` : '–'}</td>
      <td data-label="">
        {o.status === 'running' && (
          <button className="btn soft sm" onClick={onStop}>
            Hentikan
          </button>
        )}
      </td>
    </tr>
  )
}

function ScheduleCard({ s, act }: { s: Schedule; act: (f: () => Promise<unknown>) => Promise<void> }) {
  const [confirm, setConfirm] = useState(false)
  const [label, tone] = SCHED[s.status]
  return (
    <article className="cbox sched">
      <header className="sched-head">
        <div>
          <h3>{s.title}</h3>
          <p className="quiet small">
            {s.target} · {rhythm(s)}
          </p>
        </div>
        <span className={`pill ${tone}`}>{label}</span>
      </header>
      {s.status === 'active' && <p className="small">Berikutnya: {when(s.next_at, s.timezone)}</p>}
      <div className="sched-actions">
        {s.status === 'active' && (
          <button className="btn soft sm" onClick={() => void act(() => api.scheduleAction(s.id, 'pause'))}>
            Jeda
          </button>
        )}
        {s.status === 'paused' && (
          <button className="btn soft sm" onClick={() => void act(() => api.scheduleAction(s.id, 'resume'))}>
            Lanjutkan
          </button>
        )}
        {s.status !== 'cancelled' && (
          <button className="btn soft sm" onClick={() => void act(() => api.scheduleAction(s.id, 'cancel'))}>
            Batalkan
          </button>
        )}
        {confirm ? (
          <>
            <button className="btn stop sm" onClick={() => void act(() => api.deleteSchedule(s.id))}>
              Ya, hapus
            </button>
            <button className="btn link sm" onClick={() => setConfirm(false)}>
              Tidak
            </button>
          </>
        ) : (
          <button className="btn link sm" onClick={() => setConfirm(true)}>
            Hapus
          </button>
        )}
      </div>
      {s.occurrences.length === 0 ? (
        <p className="quiet small">Belum ada waktu yang tercatat.</p>
      ) : (
        <div className="table-wrap">
          <table className="plain">
            <thead>
              <tr>
                <th>Kapan</th>
                <th>Agen</th>
                <th>Tugas</th>
                <th>Status</th>
                <th>Biaya</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {s.occurrences.map((o) => (
                <OccRow key={o.id} o={o} tz={s.timezone} onStop={() => void act(() => api.stopOccurrence(o.id))} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </article>
  )
}

function NewSchedule({ onDone }: { onDone: () => void }) {
  const { bots, groups } = useData()
  const [title, setTitle] = useState('')
  const [target, setTarget] = useState('')
  const [prompt, setPrompt] = useState('')
  const [days, setDays] = useState<number[]>([0, 1, 2, 3, 4])
  const [time, setTime] = useState('09:00')
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const ok = title.trim() && target && prompt.trim() && days.length > 0 && time

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!ok || busy) return
    setBusy(true)
    setProblem('')
    try {
      const [kind, id] = target.split(':')
      await api.createSchedule({ title: title.trim(), prompt: prompt.trim(), days, time, ...(kind === 'bot' ? { bot_id: id } : { group_id: id }) })
      onDone()
    } catch (err) {
      setProblem(errText(err))
    } finally {
      setBusy(false)
    }
  }
  return (
    <form className="cbox sched-form" onSubmit={(e) => void submit(e)}>
      <h2>Jadwal baru</h2>
      <label className="field">
        <span>Nama jadwal</span>
        <input value={title} maxLength={80} onChange={(e) => setTitle(e.target.value)} placeholder="Contoh: Rangkuman harian" />
      </label>
      <label className="field">
        <span>Dijalankan oleh</span>
        <select value={target} onChange={(e) => setTarget(e.target.value)}>
          <option value="">Pilih agen atau grup</option>
          <optgroup label="Agen">
            {bots.map((b) => (
              <option key={b.id} value={`bot:${b.id}`}>
                {b.name}
              </option>
            ))}
          </optgroup>
          {groups.length > 0 && (
            <optgroup label="Grup">
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
        <span>Perintah</span>
        <textarea rows={3} maxLength={4000} value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Apa yang harus dikerjakan setiap kali jadwal ini jalan?" />
      </label>
      <fieldset className="field days">
        <legend>Hari</legend>
        <div className="day-row">
          {DAYS.map((d, i) => (
            <label key={d} className="chk">
              <input type="checkbox" checked={days.includes(i)} onChange={() => setDays((cur) => (cur.includes(i) ? cur.filter((x) => x !== i) : [...cur, i].sort()))} />
              {d.slice(0, 3)}
            </label>
          ))}
        </div>
      </fieldset>
      <label className="field">
        <span>Jam</span>
        <input type="time" value={time} onChange={(e) => setTime(e.target.value)} />
      </label>
      <p className="quiet small">Memakai zona waktu di Pengaturan. Pemakaian dihitung seperti chat biasa dan ikut batas biaya bulanan.</p>
      {problem && <ErrorLine text={problem} />}
      <div className="sched-actions">
        <button className="btn primary" type="submit" disabled={!ok || busy}>
          Buat jadwal
        </button>
        <button className="btn link" type="button" onClick={onDone}>
          Batal
        </button>
      </div>
    </form>
  )
}

export function Scheduler() {
  const fn = useCallback(() => api.schedules(), [])
  const t = useLoad(fn)
  const [creating, setCreating] = useState(false)
  const [problem, setProblem] = useState('')
  const { retry } = t
  useEffect(() => {
    const id = window.setInterval(retry, 30000) // statuses change while the page is open
    return () => window.clearInterval(id)
  }, [retry])

  async function act(f: () => Promise<unknown>) {
    setProblem('')
    try {
      await f()
    } catch (e) {
      setProblem(errText(e))
    }
    retry()
  }

  return (
    <div className="tab-body">
      <p className="note-box">Jadwal dijalankan oleh server kami sendiri, bukan oleh Hermes. Setiap jalan tercatat sebagai run biasa. Rencana konten dibuat dari kartu persetujuan di chat grup.</p>
      <div className="sched-bar">
        <h2>Jadwal</h2>
        {!creating && (
          <button className="btn primary" onClick={() => setCreating(true)}>
            Jadwal baru
          </button>
        )}
      </div>
      {creating && (
        <NewSchedule
          onDone={() => {
            setCreating(false)
            retry()
          }}
        />
      )}
      {problem && <ErrorLine text={problem} />}
      {t.state === 'loading' && <Loading text="Memuat jadwal..." shape="ledger" />}
      {t.state === 'error' && <ErrorLine text={t.error} onRetry={t.retry} />}
      {t.state === 'ok' && t.data?.length === 0 && !creating && (
        <Empty title="Belum ada jadwal">Buat jadwal berulang di sini, atau setujui rencana konten di chat grup Marketing.</Empty>
      )}
      {t.state === 'ok' && t.data?.map((s) => <ScheduleCard key={s.id} s={s} act={act} />)}
    </div>
  )
}
