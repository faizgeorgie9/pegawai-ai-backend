import { useEffect, useRef, useState } from 'react'
import { MAX_PROMPT, MIN_PROMPT, RunError, USE_MOCK, runTask, sampleResult } from './api'
import type { Agent, Department, RunResult } from './api'
import { Prose, findAdvice, findEscalation, findWhy } from './reading'
import type { Escalation } from './reading'
import { EXAMPLES, MIN_SCORE, TEAMS, hueOf } from './team'

type View =
  | { step: 'task' }
  | { step: 'running' }
  | { step: 'result'; result: RunResult }
  | { step: 'error'; error: RunError }

const STEPS = ['Tugas', 'Proses', 'Hasil']
const DEPARTMENT_IDS = Object.keys(TEAMS) as Department[]
const nf1 = new Intl.NumberFormat('id-ID', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
const nf0 = new Intl.NumberFormat('id-ID')

// Sample mode only: #proses, #proses-cs, #hasil, #hasil-cs and #galat open that screen directly, for review.
// #proses-75 starts the timer at 75 s.
function previewFromHash(): { view: View; department: Department; prompt: string; from: number } | null {
  if (!USE_MOCK) return null
  const m = /^#(proses|hasil|galat)(-cs)?(?:-([0-9]+))?$/.exec(location.hash)
  if (!m) return null
  const department: Department = m[2] ? 'customer_support' : 'marketing'
  const prompt = EXAMPLES[department][m[1] === 'galat' ? 1 : 0].text
  const view: View =
    m[1] === 'hasil'
      ? { step: 'result', result: sampleResult(department) }
      : m[1] === 'galat'
        ? { step: 'error', error: new RunError('server', 'Layanan sedang bermasalah. Coba lagi sebentar lagi.', 'INTERNAL_SERVER_ERROR') }
        : { step: 'running' }
  return { view, department, prompt, from: Number(m[3] ?? 0) }
}

export default function App() {
  const [preview] = useState(previewFromHash)
  const [view, setView] = useState<View>(preview?.view ?? { step: 'task' })
  const [department, setDepartment] = useState<Department>(preview?.department ?? 'marketing')
  const [prompt, setPrompt] = useState(preview?.prompt ?? '')
  const abort = useRef<AbortController | null>(null)

  useEffect(() => () => abort.current?.abort(), [])

  async function send() {
    abort.current?.abort()
    const ctl = new AbortController()
    abort.current = ctl
    setView({ step: 'running' })
    try {
      const result = await runTask(department, prompt.trim(), ctl.signal)
      setView({ step: 'result', result })
    } catch (e) {
      if (ctl.signal.aborted) return
      setView({
        step: 'error',
        error: e instanceof RunError ? e : new RunError('server', 'Terjadi kesalahan yang tidak dikenal.'),
      })
    }
  }

  function reset() {
    setPrompt('')
    setView({ step: 'task' })
  }

  const at = view.step === 'task' ? 0 : view.step === 'result' ? 2 : 1
  return (
    <div className="shell">
      <header className="bar">
        <div className="bar-in">
          <span className="brand">
            <Mark />
            Pegawai AI
          </span>
          <ol className="steps" aria-label="Langkah">
            {STEPS.map((s, i) => (
              <li
                key={s}
                aria-current={i === at ? 'step' : undefined}
                data-state={i === at && view.step === 'error' ? 'failed' : i < at ? 'done' : undefined}
              >
                {s}
              </li>
            ))}
          </ol>
          <span className="scope">
            <span className="scope-name">PT AI Top Trends</span>
            {USE_MOCK && <span className="pill warn">Data contoh</span>}
          </span>
        </div>
      </header>
      <main>
        {view.step === 'task' && (
          <TaskStep
            department={department}
            setDepartment={setDepartment}
            prompt={prompt}
            setPrompt={setPrompt}
            onSend={send}
          />
        )}
        {view.step === 'running' && <Processing department={department} prompt={prompt} from={preview?.from ?? 0} />}
        {view.step === 'result' && <ResultStep department={department} result={view.result} onNew={reset} />}
        {view.step === 'error' && (
          <ErrorStep
            department={department}
            error={view.error}
            prompt={prompt}
            onRetry={send}
            onBack={() => setView({ step: 'task' })}
          />
        )}
      </main>
    </div>
  )
}

function Mark() {
  return (
    <svg className="mark" viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
      <circle cx="21.5" cy="11.5" r="4.5" fill="var(--accent-track)" />
      <path d="M13.5 28c.4-4.700 3.600-8 8-8s7.600 3.300 8 8z" fill="var(--accent-track)" />
      <circle cx="12" cy="10.500" r="5.500" fill="var(--accent)" />
      <path d="M2.500 28c0-5.500 4.300-9.500 9.500-9.500s9.500 4 9.500 9.500z" fill="var(--accent)" />
    </svg>
  )
}

function Avatar({ name, color, size = 40 }: { name: string; color?: string; size?: number }) {
  return (
    <span className="avatar" data-hue={hueOf(color)} style={{ width: size, height: size }} aria-hidden="true">
      {name.charAt(0)}
    </span>
  )
}

function TaskStep(p: {
  department: Department
  setDepartment: (d: Department) => void
  prompt: string
  setPrompt: (s: string) => void
  onSend: () => void
}) {
  const [problem, setProblem] = useState('')
  const box = useRef<HTMLTextAreaElement>(null)
  const team = TEAMS[p.department]
  const length = p.prompt.trim().length

  function submit(e: React.FormEvent) {
    e.preventDefault()
    if (length === 0) return setProblem('Tugas belum diisi. Tulis apa yang perlu dikerjakan tim.')
    if (length < MIN_PROMPT) return setProblem(`Tugas terlalu pendek. Tulis minimal ${MIN_PROMPT} karakter.`)
    if (p.prompt.length > MAX_PROMPT) return setProblem(`Tugas terlalu panjang. Maksimal ${MAX_PROMPT} karakter.`)
    setProblem('')
    p.onSend()
  }
  function useExample(text: string) {
    p.setPrompt(text)
    setProblem('')
    box.current?.focus()
  }

  return (
    <form className="step task" onSubmit={submit} noValidate>
      <header className="title rise">
        <h1>Beri tugas ke tim</h1>
        <p className="sub">
          Pilih departemen dan tulis tugasnya. Tim mengerjakan satu draf, biasanya dalam 1 sampai 2 menit.
        </p>
      </header>

      <fieldset className="teams">
        <legend className="sr">Departemen</legend>
        {DEPARTMENT_IDS.map((id, n) => {
          const t = TEAMS[id]
          return (
            <label key={id} className="team-card rise" style={{ ['--i' as string]: n + 1 }}>
              <input
                className="sr"
                type="radio"
                name="dept"
                value={id}
                aria-label={`${t.label}, ${t.members.length} pegawai`}
                checked={id === p.department}
                onChange={() => p.setDepartment(id)}
              />
              <span className="team-head">
                <span className="team-name">{t.label}</span>
                <span className="team-count">{t.members.length} pegawai</span>
                <span className="radio" aria-hidden="true" />
              </span>
              <span className="team-blurb">{t.blurb}</span>
              <RosterTiles department={id} />
            </label>
          )
        })}
      </fieldset>

      <div className="compose rise" style={{ ['--i' as string]: 3 }}>
        <div className="compose-main">
          <label className="field-label" htmlFor="task">
            Tugas untuk tim {team.label}
          </label>
          <textarea
            id="task"
            ref={box}
            value={p.prompt}
            maxLength={MAX_PROMPT}
            placeholder={`Tulis tugas untuk ${team.members.map((m) => m.name).join(', ')}.`}
            aria-describedby={p.department === 'customer_support' ? 'task-hint task-sensitive' : 'task-hint'}
            aria-invalid={problem ? true : undefined}
            onChange={(e) => {
              p.setPrompt(e.target.value)
              if (problem) setProblem('')
            }}
          />
          <div className="hint" id="task-hint">
            <span>Minimal {MIN_PROMPT} karakter.</span>
            <span className="num">
              {p.prompt.length} / {MAX_PROMPT}
            </span>
          </div>
          {p.department === 'customer_support' && (
            <p className="muted small" id="task-sensitive">
              Jangan tempel kata sandi, token, atau data rekening pelanggan di sini.
            </p>
          )}
          {problem && (
            <p className="problem" role="alert">
              {problem}
            </p>
          )}
          <button className="btn primary big" type="submit">
            Kirim ke tim {team.label}
          </button>
        </div>

        <aside className="examples" aria-labelledby="ex-h">
          <h2 id="ex-h">Contoh tugas</h2>
          <ul>
            {EXAMPLES[p.department].map((e) => (
              <li key={e.title}>
                <button
                  type="button"
                  className="example"
                  aria-pressed={p.prompt === e.text}
                  onClick={() => useExample(e.text)}
                >
                  <span className="example-title">{e.title}</span>
                  <span className="example-text">{e.text}</span>
                </button>
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </form>
  )
}


function RosterTiles({ department, stack }: { department: Department; stack?: boolean }) {
  return (
    <span className={`roster${stack ? ' stack' : ''}`}>
      {TEAMS[department].members.map((m) => (
        <span className="member" data-hue={hueOf(m.color)} key={m.name}>
          <span className="member-top">
            <Avatar name={m.name} color={m.color} size={44} />
            <span className="member-name">{m.name}</span>
          </span>
          <span className="member-role">{m.role}</span>
          <span className="member-makes">{m.makes}</span>
        </span>
      ))}
    </span>
  )
}

const EXPECTED_SECONDS = 120 // real runs took 62 to 101 s; the service stops at 180 s
const RING = 2 * Math.PI * 88
function Processing({ department, prompt, from }: { department: Department; prompt: string; from: number }) {
  const [secs, setSecs] = useState(from)
  useEffect(() => {
    const t = setInterval(() => setSecs((s) => s + 1), 1000)
    return () => clearInterval(t)
  }, [])
  const mmss = `${String(Math.floor(secs / 60)).padStart(2, '0')}:${String(secs % 60).padStart(2, '0')}` // taste-skill-ignore: a clock, not index numbering
  const team = TEAMS[department]
  const names = team.members.map((m) => m.name)
  const done = Math.min(secs / EXPECTED_SECONDS, 1)
  return (
    <section className="step process">
      <header className="title rise">
        <h1 role="status">Tim {team.label} sedang bekerja</h1>
        <p className="sub">
          {names.slice(0, -1).join(', ')} dan {names[names.length - 1]} mengerjakan tugas Anda. Hasilnya muncul
          sekaligus setelah semuanya selesai.
        </p>
      </header>

      <div className="process-grid">
        <div className="clock rise" style={{ ['--i' as string]: 1 }}>
          <div className="ring" aria-hidden="true">
            <svg viewBox="0 0 200 200">
              <circle className="ring-track" cx="100" cy="100" r="88" />
              <circle
                className="ring-fill"
                cx="100"
                cy="100"
                r="88"
                strokeDasharray={RING}
                strokeDashoffset={RING * (1 - done)}
              />
            </svg>
            <div className="ring-in">
              <span className="timer num">{mmss}</span>
              <span className="clock-label">
                <span className="live" />
                Waktu berjalan
              </span>
            </div>
          </div>
          <p className="clock-note">
            {secs < EXPECTED_SECONDS
              ? 'Biasanya 1 sampai 2 menit. Mohon tetap di halaman ini.'
              : 'Sudah lewat 2 menit, tim masih bekerja. Layanan berhenti menunggu di menit ke-3. Mohon tetap di halaman ini.'}
          </p>
        </div>
        <div className="process-side">
          <section className="rise" style={{ ['--i' as string]: 2 }} aria-labelledby="who">
            <h2 id="who" className="side-h">
              Tim yang mengerjakan
            </h2>
            <RosterTiles department={department} />
          </section>
          <section className="card rise" style={{ ['--i' as string]: 3 }} aria-labelledby="what">
            <h2 id="what">Tugas Anda</h2>
            <p className="quote">{prompt.trim()}</p>
          </section>
        </div>
      </div>
    </section>
  )
}

function Gate({
  department,
  score,
  scorer,
  extra,
}: {
  department: Department
  score?: number
  scorer?: Agent
  extra?: React.ReactNode
}) {
  const min = MIN_SCORE[department]
  const pass = score !== undefined && min !== undefined ? score >= min : undefined
  const title = department === 'marketing' ? 'Gerbang QC' : 'Audit mutu'
  const gap = score !== undefined && min !== undefined ? score - min : undefined
  return (
    <section className="card gate" aria-labelledby="gate-h">
      <div className="gate-head">
        <h2 id="gate-h">{title}</h2>
        {pass !== undefined ? (
          <span className={`pill ${pass ? 'ok' : 'bad'}`}>{pass ? 'Lulus' : 'Belum lulus'}</span>
        ) : (
          <span className="pill plain">{score === undefined ? 'Tanpa skor' : 'Tanpa ambang'}</span>
        )}
      </div>
      <p className="gate-figure">
        <span className="score num">{score ?? '–'}</span>
        <span className="of">dari 100{scorer ? `, dinilai ${scorer.name}` : ''}</span>
      </p>
      <div>
        <div className="track gate-track" aria-hidden="true">
          {score !== undefined && (
            <div className="fill grow" style={{ transform: `scaleX(${Math.max(0, Math.min(score, 100)) / 100})` }} />
          )}
          {min !== undefined && <span className="mark-line" style={{ left: `${min}%` }} />}
        </div>
        <div className="track-labels num" aria-hidden="true">
          <span>0</span>
          {min !== undefined && (
            <span className="at" style={{ left: `${min}%` }}>
              Ambang SOP {min}
            </span>
          )}
          <span style={{ left: '100%' }}>100</span>
        </div>
      </div>
      <p className="gate-note">
        {score === undefined
          ? 'Skor tidak ditemukan dalam hasil tim.'
          : min !== undefined && gap !== undefined
            ? gap >= 0
              ? `${scorer?.name ?? 'QC'} memberi ${score}. Ambang minimum SOP Marketing ${min}, selisih ${gap > 0 ? '+' : ''}${gap}.`
              : `${scorer?.name ?? 'QC'} memberi ${score}. Ambang minimum SOP Marketing ${min}, kurang ${-gap} poin.`
            : 'Ambang skor untuk Customer Service belum ditetapkan, jadi angka ini belum menentukan lulus atau tidak.'}
      </p>
      {extra}
    </section>
  )
}

function EscalationCard({ esc }: { esc?: Escalation }) {
  return (
    <section className="card esc" aria-labelledby="esc-h">
      <h2 id="esc-h">Rekomendasi eskalasi</h2>
      {esc ? (
        <>
          <p className={`pill big ${esc.tone}`}>{esc.label}</p>
          {esc.reason && <p className="esc-reason">{esc.reason}</p>}
          {esc.items.length > 0 && (
            <ul className="esc-items">
              {esc.items.map((it) => (
                <li key={it}>{it}</li>
              ))}
            </ul>
          )}
          <p className="muted small">Rekomendasi dari {esc.by} dalam catatan audit. Belum ada tindakan yang dijalankan.</p>
        </>
      ) : (
        <p className="muted">Rekomendasi eskalasi tidak ditemukan dalam catatan tim.</p>
      )}
    </section>
  )
}

function Banner({ agent }: { agent: Agent }) {
  const [size, setSize] = useState('')
  const [failed, setFailed] = useState(false)
  return (
    <section className="card banner" aria-labelledby="banner-h">
      <h2 id="banner-h">Banner dari {agent.name}</h2>
      {failed ? (
        <p className="muted">Gambar banner belum bisa dimuat.</p>
      ) : (
        <a href={agent.imageUrl} target="_blank" rel="noopener noreferrer" aria-label="Buka banner ukuran penuh di tab baru">
          <img
            src={agent.imageUrl}
            alt={`Banner promosi buatan ${agent.name} untuk tugas ini`}
            onLoad={(e) => setSize(`${e.currentTarget.naturalWidth} x ${e.currentTarget.naturalHeight} piksel`)}
            onError={() => setFailed(true)}
          />
        </a>
      )}
      {size && <p className="muted small">{size}. Ketuk gambar untuk membukanya penuh.</p>}
    </section>
  )
}

function ResultStep({
  department,
  result,
  onNew,
}: {
  department: Department
  result: RunResult
  onNew: () => void
}) {
  const [active, setActive] = useState(0)
  const agent = result.agents[active]
  const scorer = result.agents.find((a) => a.score !== undefined)
  const banner = result.agents.find((a) => a.imageUrl)
  const esc = department === 'customer_support' ? findEscalation(result.agents) : undefined
  const advice = findAdvice(result.agents)
  const why = findWhy(scorer)
  const min = MIN_SCORE[department]
  const tabs = useRef<(HTMLButtonElement | null)[]>([])
  const label = TEAMS[department].label

  function onKey(e: React.KeyboardEvent) {
    const n = result.agents.length
    const fwd = e.key === 'ArrowRight' || e.key === 'ArrowDown'
    const back = e.key === 'ArrowLeft' || e.key === 'ArrowUp'
    if (fwd || back) {
      const next = fwd ? (active + 1) % n : (active + n - 1) % n
      e.preventDefault()
      setActive(next)
      tabs.current[next]?.focus()
    }
  }

  const finding =
    result.score === undefined || !scorer
      ? 'Skor mutu tidak ditemukan dalam hasil. Periksa drafnya dengan teliti.'
      : min !== undefined
        ? result.score >= min
          ? `${scorer.name} memberi ${result.score} dari 100, di atas ambang SOP ${min}.`
          : `${scorer.name} memberi ${result.score} dari 100, di bawah ambang SOP ${min}. Draf perlu diperbaiki sebelum dipakai.`
        : `${scorer.name} memberi ${result.score} dari 100.${esc ? ` Rekomendasi eskalasi: ${esc.label.toLowerCase()}.` : ''}`

  const more = (n: number, by: string, index: number) => (
    <p className="gate-more">
      {n === 1 ? 'Ada 1 saran lain' : `Ada ${n} saran lain`} di catatan {by}.{' '}
      <button type="button" className="btn link" onClick={() => setActive(index)}>
        Buka catatan {by}
      </button>
    </p>
  )
  const extra =
    advice && advice.required.length ? (
      <div className="gate-extra">
        <h3>
          {advice.required.length === 1 ? 'Satu revisi wajib' : `${advice.required.length} revisi wajib`} dari {advice.by}
        </h3>
        <ul>
          {advice.required.map((it) => (
            <li key={it}>{it}</li>
          ))}
        </ul>
        {advice.items.length > advice.required.length && more(advice.items.length - advice.required.length, advice.by, advice.index)}
      </div>
    ) : why ? (
      <div className="gate-extra">
        <h3>Alasan skor dari {scorer?.name}</h3>
        <p>{why}</p>
      </div>
    ) : advice ? (
      <div className="gate-extra">
        <h3>
          {advice.heading} dari {advice.by}
        </h3>
        <ul>
          {advice.items.slice(0, 3).map((it) => (
            <li key={it}>{it}</li>
          ))}
        </ul>
        {advice.items.length > 3 && more(advice.items.length - 3, advice.by, advice.index)}
      </div>
    ) : undefined

  return (
    <section className="step result">
      <header className="title title-row rise">
        <div>
          <h1>Hasil tim {label}</h1>
          <p className="sub">{finding}</p>
        </div>
        <button className="btn primary" onClick={onNew}>
          Tugas baru
        </button>
      </header>

      <p className="draft rise" style={{ ['--i' as string]: 1 }}>
        Ini draf. Mohon ditinjau manusia sebelum dipakai.
      </p>

      <div className={`lead-row rise${department === 'customer_support' ? ' cs' : ''}`} style={{ ['--i' as string]: 2 }}>
        <Gate department={department} score={result.score} scorer={scorer} extra={extra} />
        {department === 'customer_support' ? <EscalationCard esc={esc} /> : banner ? <Banner agent={banner} /> : null}
      </div>

      <section className="card reading rise" style={{ ['--i' as string]: 3 }} aria-label="Hasil per anggota tim">
        <div className="tabs" role="tablist" aria-label="Hasil per anggota tim" aria-orientation="vertical" onKeyDown={onKey}>
          {result.agents.map((a, i) => (
            <button
              key={a.id}
              ref={(el) => {
                tabs.current[i] = el
              }}
              role="tab"
              id={`tab-${a.id}`}
              aria-selected={i === active}
              aria-controls="panel"
              tabIndex={i === active ? 0 : -1}
              onClick={() => setActive(i)}
            >
              <Avatar name={a.name} color={a.color} size={40} />
              <span className="tab-text">
                <b>{a.name}</b>
                <small>{a.role}</small>
                {a.badge && <small className="tab-badge">{a.badge}</small>}
              </span>
            </button>
          ))}
        </div>
        <article id="panel" role="tabpanel" aria-labelledby={`tab-${agent.id}`} tabIndex={0}>
          <header className="agent-head">
            <Avatar name={agent.name} color={agent.color} size={48} />
            <div>
              <h2>{agent.name}</h2>
              <p className="muted">
                {agent.role}
                {agent.badge ? ` · ${agent.badge}` : ''}
              </p>
            </div>
          </header>
          <Prose agent={agent} />
        </article>
      </section>

      <details className="card detail rise" style={{ ['--i' as string]: 4 }}>
        <summary>Detail</summary>
        <dl>
          <div>
            <dt>Durasi</dt>
            <dd className="num">{nf1.format(result.seconds)} detik</dd>
          </div>
          <div>
            <dt>Token</dt>
            <dd className="num">{nf0.format(result.tokens)}</dd>
          </div>
          <div>
            <dt>Model</dt>
            <dd>
              {result.model} ({result.provider}){result.fallback ? ', model cadangan' : ''}
            </dd>
          </div>
          <div>
            <dt>Sesi</dt>
            <dd className="num">{result.session}</dd>
          </div>
        </dl>
      </details>
    </section>
  )
}

const ERROR_TITLE: Record<RunError['kind'], string> = {
  network: 'Layanan tidak terjangkau',
  invalid: 'Tugas ditolak',
  server: 'Layanan bermasalah',
  timeout: 'Waktu habis',
  suspicious: 'Hasil tidak dipercaya',
}

function ErrorStep({
  department,
  error,
  prompt,
  onRetry,
  onBack,
}: {
  department: Department
  error: RunError
  prompt: string
  onRetry: () => void
  onBack: () => void
}) {
  return (
    <section className="step fail">
      <header className="title rise">
        <h1>Belum berhasil</h1>
        <p className="sub">Tugas Anda tersimpan di halaman ini, jadi tidak perlu menulis ulang.</p>
      </header>
      <div className="fail-grid">
        <div className="fail-main">
          <section className="card err rise" style={{ ['--i' as string]: 1 }} aria-labelledby="err-h">
            <h2 id="err-h" className="pill bad big">
              {ERROR_TITLE[error.kind]}
            </h2>
            <p className="lead" role="alert">
              {error.message}
            </p>
            {error.detail && <p className="muted small">Keterangan teknis: {error.detail}</p>}
          </section>
          <section className="card rise" style={{ ['--i' as string]: 2 }} aria-labelledby="mine">
            <h2 id="mine">Tugas Anda</h2>
            <p className="quote">{prompt.trim()}</p>
          </section>
          <div className="actions rise" style={{ ['--i' as string]: 3 }}>
            <button className="btn primary big" onClick={onRetry}>
              Coba lagi
            </button>
            <button className="btn link" onClick={onBack}>
              Ubah tugas
            </button>
          </div>
        </div>
        <section className="rise" style={{ ['--i' as string]: 2 }} aria-labelledby="team-h">
          <h2 id="team-h" className="side-h">
            Tim {TEAMS[department].label}
          </h2>
          <RosterTiles department={department} stack />
        </section>
      </div>
    </section>
  )
}
