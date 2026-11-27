import { useCallback, useEffect, useRef, useState } from 'react'
import { api, errText } from './bff'
import type { Bot, Template } from './bff'
import { useData } from './data'
import { INDUSTRIES, industryById } from './industry-catalog'
import type { CatalogDivision, CatalogEmployee } from './industry-catalog'
import { BotAvatar, ErrorLine, roleLabel } from './ui'
import { Empty, Loading, PageHead, useLoad } from './ui-extra'
import './start.css'

// Onboarding by business type (#/mulai, owner only): pick the kind of business, tick the suggested employees,
// then the page creates them one by one and puts each division's team together. Non-technical language only.

type Step = 'usaha' | 'pilih' | 'proses' | 'selesai'
type PickState = { on: boolean; name: string }
type RunStatus = 'wait' | 'doing' | 'done' | 'error'

interface RunRow {
  key: string
  name: string
  title: string
  role: string
  team: string
  templateId: string
  divisionId: string
  division: string
  status: RunStatus
  error: string
  bot: Bot | null
}

interface TeamRow {
  id: string // division id
  name: string
  status: 'doing' | 'done' | 'error'
  error: string
}

interface Choice {
  key: string
  div: CatalogDivision
  emp: CatalogEmployee
  tpl: Template
}

const pickKey = (div: CatalogDivision, emp: CatalogEmployee) => `${div.id}:${emp.template}`
const nameFieldId = (div: CatalogDivision, emp: CatalogEmployee) => `nm-${div.id}-${emp.template}`

const STATUS_PILL: Record<RunStatus, string> = { wait: 'idle', doing: 'run', done: 'ok', error: 'bad' }
const STATUS_TEXT: Record<RunStatus, string> = { wait: 'Menunggu', doing: 'Membuat…', done: 'Selesai', error: 'Gagal' }

export default function Mulai() {
  const { bots, me, setDialog, flash, refreshBots, refreshGroups, refreshMe } = useData()
  const [step, setStep] = useState<Step>('usaha')
  const [industryId, setIndustryId] = useState('')
  const [picked, setPicked] = useState<Record<string, PickState>>({})
  const [rows, setRows] = useState<RunRow[]>([])
  const [teams, setTeams] = useState<TeamRow[]>([])
  const [progress, setProgress] = useState(0)
  const [problem, setProblem] = useState('')
  const [fieldErr, setFieldErr] = useState<Record<string, string>>({})
  const rowsRef = useRef<RunRow[]>([])
  const teamsRef = useRef<TeamRow[]>([])
  const started = useRef(false)
  const headRef = useRef<HTMLHeadingElement>(null)
  const fieldRefs = useRef<Record<string, HTMLInputElement | null>>({})
  const prevStep = useRef<Step>(step)
  const [focusKey, setFocusKey] = useState('')

  const tplFn = useCallback(() => api.templates(), [])
  const tpls = useLoad(tplFn)
  const byId = new Map((tpls.data ?? []).map((t) => [t.id, t]))
  const industry = industryById(industryId)

  const ready = (emp: CatalogEmployee) => emp.status === 'ready' && emp.template !== '' && byId.has(emp.template)

  // A tick and a name per employee. Until the owner touches a row, the suggestion in the catalog decides:
  // preselected names stay ticked, and the name starts as the one the BFF gives that employee ("Siti").
  const entry = (div: CatalogDivision, emp: CatalogEmployee): PickState => {
    const saved = picked[pickKey(div, emp)]
    if (saved) return saved
    return { on: emp.preselect && ready(emp), name: byId.get(emp.template)?.name ?? '' }
  }

  const setEntry = (div: CatalogDivision, emp: CatalogEmployee, patch: Partial<PickState>) => {
    const key = pickKey(div, emp)
    setPicked((p) => ({ ...p, [key]: { ...entry(div, emp), ...patch } }))
  }

  const selected: Choice[] = []
  if (industry) {
    for (const div of industry.divisions) {
      for (const emp of div.employees) {
        if (!ready(emp)) continue
        if (entry(div, emp).on) selected.push({ key: pickKey(div, emp), div, emp, tpl: byId.get(emp.template)! })
      }
    }
  }
  const n = selected.length
  const anyReady = !!industry && industry.divisions.some((d) => d.employees.some(ready))

  const syncRows = (next: RunRow[]) => {
    rowsRef.current = next
    setRows(next)
  }
  const syncTeams = (next: TeamRow[]) => {
    teamsRef.current = next
    setTeams(next)
  }
  const patchRow = (i: number, patch: Partial<RunRow>) => {
    const next = rowsRef.current.map((r, j) => (j === i ? { ...r, ...patch } : r))
    syncRows(next)
  }

  // Name checks run on "Buat", so the owner is not interrupted while typing. Duplicates count both the list
  // being created and the employees that already work here.
  const validate = (): boolean => {
    const errs: Record<string, string> = {}
    const seen = new Map<string, number>()
    for (const c of selected) {
      const name = entry(c.div, c.emp).name.trim().toLowerCase()
      if (name) seen.set(name, (seen.get(name) ?? 0) + 1)
    }
    const existing = new Set(bots.map((b) => b.name.trim().toLowerCase()))
    for (const c of selected) {
      const name = entry(c.div, c.emp).name.trim()
      const low = name.toLowerCase()
      if (!name) errs[c.key] = 'Nama wajib diisi.'
      else if (existing.has(low) || (seen.get(low) ?? 0) > 1) errs[c.key] = 'Nama ini dipakai dua pegawai.'
    }
    setFieldErr(errs)
    const firstBad = selected.find((c) => errs[c.key])
    if (firstBad) setFocusKey(firstBad.key)

    const over = me ? Math.max(0, bots.length + n - me.limits.max_bots) : 0
    const next = over > 0 ? `Paket Anda memuat ${me!.limits.max_bots} pegawai. Kurangi ${over} pilihan.` : Object.keys(errs).length ? 'Periksa nama pegawai yang ditandai.' : ''
    setProblem(next)
    return next === ''
  }

  const create = () => {
    if (!industry || !validate()) return
    const list: RunRow[] = selected.map((c) => ({
      key: c.key,
      name: entry(c.div, c.emp).name.trim(),
      title: c.emp.title,
      role: c.tpl.role,
      team: c.tpl.team,
      templateId: c.tpl.id,
      divisionId: c.div.id,
      division: c.div.label,
      status: 'wait',
      error: '',
      bot: null,
    }))
    syncRows(list)
    syncTeams([])
    setProgress(1)
    setStep('proses')
  }

  // Sequential on purpose: the BFF has no bulk-create, and each employee can take up to 40 seconds. Teams are
  // made after the people, one per division with at least two members (at most six). A team that fails never
  // undoes an employee.
  async function runAll() {
    const successes: { divisionId: string; division: string; botId: string }[] = []
    for (const r of rowsRef.current) {
      if (r.status === 'done' && r.bot) successes.push({ divisionId: r.divisionId, division: r.division, botId: r.bot.id })
    }
    let attempted = successes.length
    setProgress(Math.max(1, attempted))

    for (let i = 0; i < rowsRef.current.length; i++) {
      if (rowsRef.current[i].status === 'done') continue
      const row = rowsRef.current[i]
      attempted += 1
      setProgress(attempted)
      patchRow(i, { status: 'doing', error: '' })
      try {
        const bot = await api.createBot({ name: row.name, role: row.role, team: row.team, template: row.templateId })
        patchRow(i, { status: 'done', bot })
        successes.push({ divisionId: row.divisionId, division: row.division, botId: bot.id })
      } catch (e) {
        patchRow(i, { status: 'error', error: errText(e) })
      }
    }

    const groups = new Map<string, { label: string; ids: string[] }>()
    for (const s of successes) {
      const g = groups.get(s.divisionId) ?? { label: s.division, ids: [] }
      g.ids.push(s.botId)
      groups.set(s.divisionId, g)
    }
    for (const [id, g] of groups) {
      if (g.ids.length < 2) continue
      const prev = teamsRef.current.find((t) => t.id === id)
      if (prev?.status === 'done') continue
      const name = `Tim ${g.label}`
      const keep = (t: TeamRow) => syncTeams([...teamsRef.current.filter((x) => x.id !== id), t])
      keep({ id, name, status: 'doing', error: '' })
      try {
        const group = await api.createGroup(name, g.ids.slice(0, 6))
        keep({ id, name: group.name.trim() || name, status: 'done', error: '' })
      } catch (e) {
        keep({ id, name, status: 'error', error: errText(e) })
      }
    }

    const finalRows = rowsRef.current
    const done = finalRows.filter((r) => r.status === 'done').length
    if (done > 0 && done === finalRows.length) flash(`${done} pegawai siap bekerja`)
    refreshMe()
    // A failed final read must not hide the result: the employees were created and this screen reads the
    // rows made so far, while the next page load re-reads the lists. Without this the run stops silently on
    // the progress step with every row saying "Selesai" and no button left.
    await Promise.all([refreshBots(), refreshGroups()]).catch(() => [])
    setStep('selesai')
  }

  // StrictMode runs the effect twice in development; the guard keeps one pass (each pass creates employees).
  useEffect(() => {
    if (step !== 'proses' || started.current) return
    started.current = true
    void runAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step])

  // A new step moves focus to its heading, so a keyboard or screen-reader user lands on the new question.
  // The first step is already on screen at a direct load, so it must not take focus or show a focus ring;
  // comparing against the previous step also survives StrictMode's double effect run in development.
  useEffect(() => {
    if (prevStep.current === step) return
    prevStep.current = step
    headRef.current?.focus()
  }, [step])

  // After a failed check, the first input with a message gets focus and is scrolled into view; the owner
  // otherwise only sees the summary line while the field itself is off-screen.
  useEffect(() => {
    if (!focusKey) return
    const el = fieldRefs.current[focusKey]
    setFocusKey('')
    if (!el) return
    el.focus({ preventScroll: true })
    el.scrollIntoView({ block: 'center', inline: 'nearest' })
  }, [focusKey])

  const retry = () => {
    const next = rowsRef.current.map((r) => (r.status === 'error' ? { ...r, status: 'wait' as RunStatus, error: '' } : r))
    syncRows(next)
    setProgress(next.filter((r) => r.status === 'done').length)
    setStep('proses')
    void runAll()
  }

  const sub = step === 'usaha' ? 'Langkah 1 dari 2: pilih jenis usaha.' : step === 'pilih' ? 'Langkah 2 dari 2: pilih pegawai.' : undefined
  const failed = rows.filter((r) => r.status === 'error')
  const allDone = rows.length > 0 && failed.length === 0
  const allFailed = rows.length > 0 && failed.length === rows.length
  const madeTeams = teams.filter((t) => t.status === 'done')
  const teamFailed = teams.some((t) => t.status === 'error')

  return (
    <section className="page" data-step={step}>
      <a className="back" href="#/">
        ← Beranda
      </a>
      <PageHead title="Siapkan pegawai AI Anda" sub={sub} />

      {step === 'usaha' && (
        <div className="start-step">
          {bots.length > 0 && (
            <p className="note-box">Anda sudah punya {bots.length} pegawai. Pilihan di sini ditambahkan, tidak mengganti yang ada.</p>
          )}
          <h2 ref={headRef} tabIndex={-1}>
            Usaha Anda bergerak di bidang apa?
          </h2>
          <ul className="tpl-grid">
            {INDUSTRIES.map((ind) => (
              <li key={ind.id}>
                <button type="button" className="tpl" aria-pressed={industryId === ind.id} onClick={() => setIndustryId(ind.id)}>
                  <b>{ind.label}</b>
                  <small>{ind.examples}</small>
                </button>
              </li>
            ))}
          </ul>
          <div className="start-foot start-foot-sticky">
            <a className="btn quiet-btn" href="#/">
              Batal
            </a>
            <button type="button" className="btn primary" disabled={!industryId} onClick={() => setStep('pilih')}>
              Lanjut
            </button>
          </div>
        </div>
      )}

      {step === 'pilih' && (
        <div className="start-step">
          <h2 ref={headRef} tabIndex={-1}>
            Pegawai yang kami sarankan untuk {industry?.label}
          </h2>
          <p className="quiet">Centang yang Anda mau. Nama bisa diubah.</p>

          {tpls.state === 'loading' && (
            <>
              <p className="quiet">Memeriksa pegawai yang tersedia…</p>
              <Loading text="Memeriksa pegawai yang tersedia" shape="lines" rows={2} />
            </>
          )}

          {tpls.state === 'error' && (
            <div className="start-step">
              <ErrorLine text={tpls.error} onRetry={tpls.retry} />
              <button type="button" className="btn soft" onClick={() => setDialog({ kind: 'bot' })}>
                Tambah satu per satu
              </button>
            </div>
          )}

          {tpls.state === 'ok' && industry && anyReady && (
            <>
              {industry.divisions.map((div) => {
                const chosen = div.employees.filter((emp) => ready(emp) && entry(div, emp).on).length
                return (
                  <section key={div.id} className="panel-card start-div" aria-labelledby={`dir-${div.id}`}>
                    <h2 id={`dir-${div.id}`}>{div.label}</h2>
                    <p className="quiet">{div.blurb}</p>
                    <ul className="ledger">
                      {div.employees.map((emp) => {
                        const key = pickKey(div, emp)
                        if (!ready(emp)) {
                          return (
                            <li key={key} className="start-emp is-planned">
                              <span className="start-pick-text">
                                <b>{emp.title}</b>
                                <small className="quiet small">{emp.why}</small>
                              </span>
                              <span className="pill plain">{emp.status === 'planned' ? 'Segera hadir' : 'Belum tersedia'}</span>
                            </li>
                          )
                        }
                        const e = entry(div, emp)
                        const err = fieldErr[key]
                        return (
                          <li key={key} className="start-emp">
                            <label className="start-pick">
                              <input type="checkbox" checked={e.on} onChange={(ev) => setEntry(div, emp, { on: ev.target.checked })} />
                              <span className="start-pick-text">
                                <b>{emp.title}</b>
                                <small className="quiet small">{emp.why}</small>
                              </span>
                            </label>
                            {e.on && (
                              <label className="field start-name">
                                <span className="sr">Nama untuk {emp.title}</span>
                                <input
                                  ref={(el) => {
                                    fieldRefs.current[key] = el
                                  }}
                                  value={e.name}
                                  maxLength={40}
                                  autoComplete="off"
                                  aria-invalid={err ? true : undefined}
                                  aria-describedby={err ? `${nameFieldId(div, emp)}-err` : undefined}
                                  onChange={(ev) => setEntry(div, emp, { name: ev.target.value })}
                                />
                                {err && (
                                  <small className="err" role="alert" id={`${nameFieldId(div, emp)}-err`}>
                                    {err}
                                  </small>
                                )}
                              </label>
                            )}
                          </li>
                        )
                      })}
                    </ul>
                    {chosen >= 2 && (
                      <p className="quiet small">
                        Kami juga membuat Tim {div.label} supaya mereka bisa bekerja bersama.
                        {chosen > 6 ? ' Tim hanya memuat 6 pegawai pertama.' : ''}
                      </p>
                    )}
                  </section>
                )
              })}
            </>
          )}

          {tpls.state === 'ok' && industry && !anyReady && (
            <Empty title="Belum ada pegawai siap untuk jenis usaha ini">
              <button type="button" className="btn soft" onClick={() => setDialog({ kind: 'bot' })}>
                Tambah satu per satu
              </button>
            </Empty>
          )}

          {problem && (
            <div className="problem-bar" role="alert">
              {problem}
            </div>
          )}

          <div className="start-foot">
            <p id="start-sum" className="quiet" role="status">
              {n} pegawai dipilih
            </p>
            <button
              type="button"
              className="btn quiet-btn"
              onClick={() => {
                setProblem('')
                setFieldErr({})
                setStep('usaha')
              }}
            >
              Kembali
            </button>
            {n > 0 && (
              <button type="button" className="btn primary" onClick={create}>
                Buat {n} pegawai
              </button>
            )}
          </div>
        </div>
      )}

      {step === 'proses' && (
        <div className="start-step">
          <h2 ref={headRef} tabIndex={-1}>
            Menyiapkan pegawai Anda
          </h2>
          <p role="status" className="quiet">
            Membuat {progress} dari {rows.length}… Tiap pegawai bisa sampai 40 detik. Jangan tutup halaman ini.
          </p>
          <ul className="ledger">
            {rows.map((r) => (
              <li key={r.key} className="start-run">
                <div className="ledger-row">
                  <span className="ledger-main">
                    <b>{r.name}</b>
                    <small>{r.title}</small>
                  </span>
                  <span className={`pill ${STATUS_PILL[r.status]}`}>{STATUS_TEXT[r.status]}</span>
                </div>
                {r.status === 'error' && <small className="err">{r.error}</small>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {step === 'selesai' && (
        <div className="start-step">
          {allDone ? (
            <>
              <h2 ref={headRef} tabIndex={-1}>
                Tim Anda siap
              </h2>
              <p>
                {rows.length} pegawai sudah bekerja untuk {industry?.label}.
              </p>
              <ul className="ledger">
                {rows.map((r) => (
                  <li key={r.key} className="start-done">
                    <BotAvatar bot={r.bot ?? undefined} size={28} />
                    <span className="ledger-main">
                      <b>{r.name}</b>
                      <small>{roleLabel(r.role)}</small>
                    </span>
                  </li>
                ))}
              </ul>
              {madeTeams.length > 0 && <p className="quiet">Tim: {madeTeams.map((t) => t.name).join(', ')}.</p>}
              {teamFailed && <p className="note-box">Tim belum bisa dibuat. Anda bisa membuatnya nanti di halaman Tim.</p>}
            </>
          ) : (
            <>
              <h2 ref={headRef} tabIndex={-1}>
                {allFailed ? 'Pegawai belum bisa dibuat' : 'Sebagian pegawai belum jadi'}
              </h2>
              {allFailed && <p className="quiet">Periksa pesan di tiap baris, lalu coba lagi.</p>}
              <ul className="ledger">
                {rows.map((r) => (
                  <li key={r.key} className="start-run">
                    <div className="ledger-row">
                      <span className="ledger-main">
                        <b>{r.name}</b>
                        <small>{r.title}</small>
                      </span>
                      <span className={`pill ${r.status === 'done' ? 'ok' : 'bad'}`}>{r.status === 'done' ? 'Selesai' : 'Gagal'}</span>
                    </div>
                    {r.status === 'error' && <small className="err">{r.error}</small>}
                  </li>
                ))}
              </ul>
              {madeTeams.length > 0 && <p className="quiet">Tim: {madeTeams.map((t) => t.name).join(', ')}.</p>}
            </>
          )}

          <div className="start-actions">
            {failed.length > 0 && (
              <button type="button" className="btn soft" onClick={retry}>
                Coba lagi ({failed.length})
              </button>
            )}
            {allDone ? (
              <>
                <a className="btn primary" href="#/pengetahuan">
                  Isi pengetahuan bisnis
                </a>
                <a className="btn soft" href="#/">
                  Ke Beranda
                </a>
              </>
            ) : (
              <a className="btn quiet-btn" href="#/">
                Ke Beranda
              </a>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
