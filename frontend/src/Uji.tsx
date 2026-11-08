import { Fragment, useCallback, useMemo, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api, errText } from './bff'
import type { EvalInput, Evaluation, EvalSummary, RunMeta } from './bff'
import { CompareColumns, Versions, metaValue } from './Compare'
import type { Col } from './Compare'
import Summary from './Summary'
import { useData } from './data'
import { RUBRIC } from './results'
import { SCENARIOS } from './scenarios'
import type { Scenario } from './scenarios'
import { ErrorLine } from './ui'
import { Empty, Loading, PageHead, Req, useLoad } from './ui-extra'
import { useRun } from './useRun'
import { OpenInChat, RunBar } from './ws-common'

const ROUTE = 'UI → BFF → Hermes'
const VERDICT_LABEL = { pass: 'Lulus', fail: 'Gagal', blocked: 'Nonaktif' } as const
type Verdict = keyof typeof VERDICT_LABEL
type Sc = { v: string; reason: string } // v: '' | '1'..'5' | 'na'
const VER_KEYS = ['hermes_version', 'model', 'provider', 'bot_id', 'soul_hash', 'toolsets', 'instructions_mode', 'bff_commit'] as const
const VER_ROW = 'ev-row'
const today = () => new Date().toISOString().slice(0, 10)
const blankScores = (): Record<string, Sc> => Object.fromEntries(RUBRIC.map((d) => [d.key, { v: '', reason: '' }]))

export function suggest(scores: Record<string, Sc>, critical: boolean): { verdict: Verdict; why: string } {
  const rel = Object.values(scores).filter((s) => /^[1-5]$/.test(s.v))
  if (critical) return { verdict: 'fail', why: 'Ada kegagalan kritis.' }
  if (!rel.length) return { verdict: 'fail', why: 'Belum ada skor.' }
  const low = rel.filter((s) => Number(s.v) < 4).length
  return low ? { verdict: 'fail', why: `${low} dimensi di bawah 4.` } : { verdict: 'pass', why: 'Semua skor relevan minimal 4 dan tidak ada kegagalan kritis.' }
}
export const avgOf = (e: Pick<Evaluation, 'scores'>): number | null => {
  const v = Object.values(e.scores).map((s) => s.score).filter((x): x is number => typeof x === 'number')
  return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null
}

type Snap = { text: string; runId: string; status: string; error: string }
type CmpState = { kind: 'repeat' | 'agents'; cols: Col[]; status: 'running' | 'done' | 'incomplete' }
const emptyCol = (botId: string, botName: string): Col => ({ botId, botName, runId: '', sid: '', status: 'pending', text: '', error: '', tokens: 0, seconds: null, startedAt: 0, meta: {} })

export default function Uji() {
  const { bots } = useData()
  const [group, setGroup] = useState<'all' | 'marketing' | 'cs'>('all')
  const [sc, setSc] = useState<Scenario | null>(null)
  const [override, setOverride] = useState('')
  const [botId, setBotId] = useState('')
  const [runKey, setRunKey] = useState(0) // new evaluation form per run
  const [sid, setSid] = useState('')
  const [runSnap, setRunSnap] = useState<Snap | null>(null)
  const [runMeta, setRunMeta] = useState<Partial<RunMeta>>({})
  const [compare, setCompare] = useState(false)
  const [kind, setKind] = useState<'repeat' | 'agents'>('repeat')
  const [times, setTimes] = useState<2 | 3>(2)
  const [botB, setBotB] = useState('')
  const [cmp, setCmp] = useState<CmpState | null>(null)
  const [problem, setProblem] = useState('')
  const cancelled = useRef(false)
  const fn = useCallback(() => api.evaluations(), [])
  const log = useLoad(fn)
  const sumFn = useCallback((): Promise<EvalSummary> => api.evaluationSummary(), [])
  const summary = useLoad(sumFn)
  const panel = useRef<HTMLDivElement>(null)

  const defaultBot = (s: Scenario) => bots.find((b) => b.id === (s.group === 'cs' ? 'siti' : 'rian'))?.id ?? bots[0]?.id ?? ''
  const effective = (s: Scenario) => override || defaultBot(s)
  const run = useRun()
  const busy = run.busy || cmp?.status === 'running'
  const nameOf = (id: string) => bots.find((b) => b.id === id)?.name ?? id
  const teamOf = (id: string) => bots.find((b) => b.id === id)?.team
  const saved = () => {
    log.retry()
    summary.retry()
  }
  // Agent B: another agent of the same team as agent A (when A is "Otomatis", it is checked when the scenario starts).
  const peerOpts = override ? bots.filter((b) => b.id !== override && b.team === teamOf(override)) : bots

  function begin(s: Scenario, bid: string) {
    setSc(s)
    setBotId(bid)
    setRunSnap(null)
    setRunMeta({})
    setCmp(null)
    setSid('')
    setProblem('')
    setRunKey((k) => k + 1)
    window.setTimeout(() => panel.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
  }

  async function start(s: Scenario) {
    if (busy) return
    const bid = effective(s)
    if (!bid) return
    if (compare) return void startCompare(s, bid)
    begin(s, bid)
    const r = await run.send(s.prompt, { botId: bid })
    if (r.status === 'idle') return
    setSid(r.sid)
    setRunSnap({ text: r.text, runId: r.runId, status: r.status, error: r.error })
    if (r.runId) void api.run(r.runId).then((d) => setRunMeta(d.meta), () => {})
  }

  // Each run goes in its own new session (no session id) and runs one after the other, so the concurrency cap is never hit.
  async function startCompare(s: Scenario, bid: string) {
    if (kind === 'agents' && (!botB || botB === bid || teamOf(botB) !== teamOf(bid))) {
      setProblem('Agen kedua harus agen lain dari tim yang sama.')
      return
    }
    const ids = kind === 'repeat' ? Array<string>(times).fill(bid) : [bid, botB]
    begin(s, bid)
    cancelled.current = false
    let cols = ids.map((x) => emptyCol(x, nameOf(x)))
    const put = (i: number, p: Partial<Col>) => {
      cols = cols.map((c, j) => (j === i ? { ...c, ...p } : c))
      setCmp({ kind, cols, status: 'running' })
    }
    setCmp({ kind, cols, status: 'running' })
    for (let i = 0; i < ids.length; i++) {
      put(i, { status: 'running' })
      const r = await run.send(s.prompt, { botId: ids[i] })
      if (r.status === 'idle') return
      const info = r.runId ? await api.run(r.runId).catch(() => null) : null
      const ok = r.status === 'done'
      put(i, { status: ok ? 'done' : r.status === 'stopped' ? 'stopped' : 'error', text: r.text, error: r.error, runId: r.runId, sid: r.sid, tokens: info?.tokens ?? 0, seconds: info?.seconds ?? null, startedAt: info?.started_at ?? 0, meta: info?.meta ?? {} })
      if (!ok || cancelled.current) {
        setCmp({ kind, cols, status: 'incomplete' })
        return
      }
    }
    setCmp({ kind, cols, status: 'done' })
  }
  const stop = () => {
    cancelled.current = true
    run.stop()
  }

  const shownRows = SCENARIOS.filter((s) => group === 'all' || s.group === group)
  const liveIdx = cmp ? Math.max(0, cmp.cols.findIndex((c) => c.status === 'running')) : 0

  return (
    <section className="page ws">
      <PageHead title="Evaluasi" sub="Jalankan skenario uji, bandingkan hasil, dan beri nilai 1–5." />
      <p className="note-box">Kasus Marketing TC-01 sampai TC-11 mengikuti test matrix requirement v1.1; kalimat prompt disusun frontend dari contoh E-01 sampai E-05, produk contoh berlabel dummy. Kasus CS berlabel draf sampai requirement Mansi final.</p>

      {summary.state === 'ok' && summary.data && <Summary data={summary.data} />}
      {summary.state === 'error' && <ErrorLine text={summary.error} onRetry={summary.retry} />}

      <div className="toolbar">
        <div className="seg" role="tablist" aria-label="Kelompok skenario">
          {(['all', 'marketing', 'cs'] as const).map((g) => (
            <button key={g} role="tab" aria-selected={group === g} onClick={() => setGroup(g)}>
              {g === 'all' ? 'Semua' : g === 'marketing' ? 'Marketing' : 'CS'}
            </button>
          ))}
        </div>
        <label className="field inline ws-agent">
          <span>Agen</span>
          <select value={override} disabled={busy} onChange={(e) => { setOverride(e.target.value); setBotB('') }}>
            <option value="">Otomatis (Rian untuk Marketing, Siti untuk CS)</option>
            {bots.map((b) => (
              <option key={b.id} value={b.id}>{b.name} · {b.role}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="cmp-opts">
        <label className="ws-switch">
          <input type="checkbox" checked={compare} disabled={busy} onChange={(e) => setCompare(e.target.checked)} />
          <span>Mode Bandingkan</span>
        </label>
        {compare && (
          <>
            <div className="seg" role="tablist" aria-label="Cara membandingkan">
              <button role="tab" aria-selected={kind === 'repeat'} disabled={busy} onClick={() => setKind('repeat')}>Ulang N kali</button>
              <button role="tab" aria-selected={kind === 'agents'} disabled={busy} onClick={() => setKind('agents')}>Dua agen</button>
            </div>
            {kind === 'repeat' ? (
              <label className="field inline">
                <span>Jumlah run</span>
                <select value={times} disabled={busy} onChange={(e) => setTimes(Number(e.target.value) === 3 ? 3 : 2)}>
                  <option value={2}>2 kali</option>
                  <option value={3}>3 kali</option>
                </select>
              </label>
            ) : (
              <label className="field inline">
                <span>Agen kedua</span>
                <select value={botB} disabled={busy} onChange={(e) => setBotB(e.target.value)}>
                  <option value="">Pilih agen satu tim</option>
                  {peerOpts.map((b) => <option key={b.id} value={b.id}>{b.name} · {b.role}</option>)}
                </select>
              </label>
            )}
            <span className="quiet small">Tiap run memakai sesi baru, dijalankan satu per satu.</span>
          </>
        )}
      </div>
      {problem && <ErrorLine text={problem} />}

      <div className="table-wrap">
        <table className="plain sc-table">
          <thead><tr><th>Kasus</th><th>Skenario</th><th>Prompt</th><th></th></tr></thead>
          <tbody>
            {shownRows.map((s) => (
              <tr key={s.id} data-on={sc?.id === s.id || undefined}>
                <td className="num" data-label="Kasus" style={{ whiteSpace: 'nowrap' }}><b>{s.id}</b></td>
                <td data-label="Skenario" className="rich">
                  <b>{s.title}</b>
                  <div className="quiet small">{s.capability}</div>
                  <span className={`pill ${s.group === 'cs' ? 'warn' : 'sample'}`}>{s.tag}</span>
                </td>
                <td data-label="Prompt"><div className="clamp2" title={s.prompt}>{s.prompt}</div></td>
                <td className="act-cell">
                  <button className="btn primary" disabled={busy} onClick={() => void start(s)} aria-label={`${compare ? 'Bandingkan' : 'Jalankan'} ${s.id}`}>{compare ? 'Bandingkan' : 'Jalankan'}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div ref={panel} className="uji-run">
        {!sc && <Empty title="Belum ada yang dijalankan">Pilih skenario lalu tekan Jalankan. Setiap run memakai sesi baru.</Empty>}
        {sc && (
          <>
            <header className="ws-form-head">
              <h2>{sc.id}: {sc.title}</h2>
              <span className="quiet small">
                {cmp ? (cmp.kind === 'repeat' ? `Ulang ${cmp.cols.length} kali · ${nameOf(botId)}` : `Dua agen: ${cmp.cols.map((c) => c.botName).join(' dan ')}`) : `Agen: ${nameOf(botId)}`} · {ROUTE}
              </span>
              {!cmp && <OpenInChat botId={botId} sid={sid} />}
            </header>
            <RunBar
              busy={busy}
              text={cmp ? `Run ${liveIdx + 1} dari ${cmp.cols.length}: ${cmp.cols[liveIdx].botName} sedang bekerja...` : 'Agen sedang bekerja...'}
              onStop={stop}
              status={run.status}
              error={run.error}
              onRetry={() => void start(sc)}
              stoppedNote={cmp ? 'Dihentikan. Perbandingan yang belum lengkap tidak bisa disimpan.' : 'Dihentikan. Anda masih bisa menyimpan evaluasi dengan hasil Nonaktif.'}
            />
            {cmp && <CompareColumns cols={cmp.cols} live={run.text} />}
            {cmp?.status === 'incomplete' && <p className="note-box">Perbandingan belum lengkap, jadi belum bisa dinilai. Jalankan lagi.</p>}
            {!cmp && run.busy && run.text && <article className="rcard live"><div className="rbody"><p className="draft-text">{run.text}</p></div></article>}
            {!cmp && runSnap && runSnap.status === 'done' && (
              <article className="rcard">
                <header><b>Output aktual</b><span className="pill origin">Jawaban agen, teks asli</span></header>
                <div className="rbody md"><Markdown remarkPlugins={[remarkGfm]}>{runSnap.text || '(kosong)'}</Markdown></div>
              </article>
            )}
            {!cmp && runSnap && runSnap.status !== 'running' && <EvalForm key={runKey} sc={sc} botId={botId} sid={sid} snap={runSnap} meta={runMeta} onSaved={saved} />}
            {cmp?.status === 'done' && <EvalForm key={runKey} sc={sc} botId={botId} sid={cmp.cols[0].sid} snap={{ text: '', runId: cmp.cols[0].runId, status: 'done', error: '' }} meta={cmp.cols[0].meta} cmp={cmp} onSaved={saved} />}
          </>
        )}
      </div>

      <div className="block">
        <header><h2>Log eksperimen</h2></header>
        {log.state === 'loading' && <Loading />}
        {log.state === 'error' && <ErrorLine text={log.error} onRetry={log.retry} />}
        {log.state === 'ok' && <LogTable rows={log.data ?? []} />}
      </div>
    </section>
  )
}

function EvalForm({ sc, botId, sid, snap, meta, cmp, onSaved }: { sc: Scenario; botId: string; sid: string; snap: Snap; meta: Partial<RunMeta>; cmp?: CmpState; onSaved: () => void }) {
  const [consistency, setConsistency] = useState<'konsisten' | 'tidak_konsisten' | ''>('')
  const [consNote, setConsNote] = useState('')
  const [expected, setExpected] = useState(sc.expected)
  const [scores, setScores] = useState<Record<string, Sc>>(blankScores)
  const [critical, setCritical] = useState(false)
  const [verdict, setVerdict] = useState<Verdict | ''>(snap.status === 'done' ? '' : 'blocked')
  const [errors, setErrors] = useState('')
  const [improve, setImprove] = useState('')
  const [reviewer, setReviewer] = useState('')
  const [date, setDate] = useState(today())
  const [tried, setTried] = useState(false)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const [savedId, setSavedId] = useState('')
  const actual = cmp
    ? cmp.cols.map((c, i) => `[Run ${i + 1} · ${c.botName}]\n${c.text}`).join('\n\n').slice(0, 40000)
    : snap.status === 'done' ? snap.text : `[${snap.status === 'error' ? 'Error' : 'Dihentikan'}] ${snap.error}`.trim()
  const sug = suggest(scores, critical)

  const bad: Record<string, string> = {}
  for (const d of RUBRIC) {
    const s = scores[d.key]
    if (!s.v) bad[d.key] = 'Pilih skor 1 sampai 5 atau N/A.'
    else if (s.v === 'na' && !s.reason.trim()) bad[d.key] = 'N/A wajib diberi alasan.'
  }
  const missing = [...(cmp && !consistency ? ['Pilih Konsisten atau Tidak konsisten.'] : []), ...(verdict ? [] : ['Pilih hasil: Lulus, Gagal, atau Nonaktif.']), ...(reviewer.trim() ? [] : ['Nama reviewer wajib diisi.']), ...(Object.keys(bad).length ? [`${Object.keys(bad).length} dimensi rubrik belum lengkap.`] : [])]

  async function save(e: React.FormEvent) {
    e.preventDefault()
    setTried(true)
    if (missing.length || busy || !verdict) return
    const body: EvalInput = {
      case_id: sc.id,
      bot_id: botId,
      session_id: sid || null,
      run_id: snap.runId || null,
      ...(cmp && consistency
        ? {
            comparison: {
              mode: cmp.kind,
              consistency,
              note: consNote.trim(),
              runs: cmp.cols.map((c) => ({ run_id: c.runId, session_id: c.sid || null, bot_id: c.botId, output: c.text, tokens: c.tokens, duration: c.seconds, meta: c.meta })),
            },
          }
        : {}),
      prompt: sc.prompt,
      expected,
      actual,
      scores: Object.fromEntries(RUBRIC.map((d) => [d.key, { score: scores[d.key].v === 'na' ? null : Number(scores[d.key].v), reason: scores[d.key].reason.trim() }])),
      verdict,
      notes: { errors, improvements: improve, critical, reviewed_on: date },
      reviewer: reviewer.trim(),
    }
    setBusy(true)
    setProblem('')
    try {
      const r = await api.saveEvaluation(body, savedId || undefined)
      setSavedId(r.id)
      onSaved()
    } catch (err) {
      setProblem(errText(err))
    } finally {
      setBusy(false)
    }
  }
  const set = (k: string, p: Partial<Sc>) => setScores((cur) => ({ ...cur, [k]: { ...cur[k], ...p } }))

  return (
    <form className="ws-form eval" onSubmit={save} noValidate>
      <h2>Evaluasi</h2>
      <label className="field">
        <span>Output yang diharapkan (dari skenario, boleh diubah)</span>
        <textarea rows={3} value={expected} onChange={(e) => setExpected(e.target.value)} />
      </label>
      {cmp ? (
        <fieldset className="verdicts">
          <legend>Konsistensi antar run <Req /></legend>
          {([['konsisten', 'Konsisten'], ['tidak_konsisten', 'Tidak konsisten']] as const).map(([v, l]) => (
            <label key={v} className="ws-switch">
              <input type="radio" name="consistency" checked={consistency === v} onChange={() => setConsistency(v)} />
              <span>{l}</span>
            </label>
          ))}
          {tried && !consistency && <small className="err" role="alert">Pilih Konsisten atau Tidak konsisten.</small>}
        </fieldset>
      ) : (
        <label className="field">
          <span>Output aktual (otomatis)</span>
          <textarea rows={3} value={actual} readOnly />
        </label>
      )}
      {cmp && <label className="field"><span>Catatan konsistensi</span><textarea rows={2} value={consNote} maxLength={2000} onChange={(e) => setConsNote(e.target.value)} /></label>}
      <Versions items={cmp ? cmp.cols.map((c, i) => ({ label: `Run ${i + 1} · ${c.botName}`, meta: c.meta })) : [{ label: 'Run', meta }]} />
      <p className="quiet small">Versi dicatat otomatis oleh BFF saat run dimulai.</p>
      <fieldset className="rubric">
        <legend>Rubrik, skor 1 sampai 5</legend>
        {RUBRIC.map((d) => {
          const s = scores[d.key]
          return (
            <div key={d.key} className="rub-row">
              <label htmlFor={`sc-${d.key}`}>{d.label}</label>
              <select id={`sc-${d.key}`} value={s.v} onChange={(e) => set(d.key, { v: e.target.value })} aria-invalid={tried && !!bad[d.key]}>
                <option value="">Pilih</option>
                {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}</option>)}
                <option value="na">N/A</option>
              </select>
              {s.v === 'na' && <input aria-label={`Alasan N/A ${d.label}`} placeholder="Alasan N/A (wajib)" value={s.reason} onChange={(e) => set(d.key, { reason: e.target.value })} aria-invalid={tried && !!bad[d.key]} />}
              {tried && bad[d.key] && <small className="err" role="alert">{bad[d.key]}</small>}
            </div>
          )
        })}
      </fieldset>
      <label className="ws-switch">
        <input type="checkbox" checked={critical} onChange={(e) => setCritical(e.target.checked)} />
        <span>Ada kegagalan kritis</span>
      </label>
      <p className="suggest" role="status">
        Saran otomatis: <b>{VERDICT_LABEL[sug.verdict]}</b>. {sug.why} Reviewer yang memutuskan.
      </p>
      <fieldset className="verdicts">
        <legend>Hasil</legend>
        {(['pass', 'fail', 'blocked'] as const).map((v) => (
          <label key={v} className="ws-switch">
            <input type="radio" name="verdict" checked={verdict === v} onChange={() => setVerdict(v)} />
            <span>{VERDICT_LABEL[v]}</span>
          </label>
        ))}
      </fieldset>
      <label className="field"><span>Error dan kekurangan</span><textarea rows={2} value={errors} onChange={(e) => setErrors(e.target.value)} /></label>
      <label className="field"><span>Saran perbaikan</span><textarea rows={2} value={improve} onChange={(e) => setImprove(e.target.value)} /></label>
      <div className="fgrid">
        <label className="field"><span>Nama reviewer <Req /></span><input value={reviewer} maxLength={80} onChange={(e) => setReviewer(e.target.value)} aria-invalid={tried && !reviewer.trim()} />{tried && !reviewer.trim() && <small className="err" role="alert">Nama reviewer wajib diisi.</small>}</label>
        <label className="field"><span>Tanggal</span><input type="date" value={date} onChange={(e) => setDate(e.target.value)} /></label>
      </div>
      {tried && missing.length > 0 && <ul className="field-err" role="alert">{missing.map((m) => <li key={m}>{m}</li>)}</ul>}
      {problem && <ErrorLine text={problem} />}
      {savedId && <p className="ok-line" role="status">Tersimpan di log eksperimen. Simpan lagi untuk memperbarui.</p>}
      <div className="form-actions"><button className="btn primary" type="submit" disabled={busy}>{savedId ? 'Perbarui evaluasi' : 'Simpan evaluasi'}</button></div>
    </form>
  )
}

function csvCell(v: unknown): string {
  const s = v === null || v === undefined ? '' : String(v)
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}
function download(name: string, mime: string, body: string) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([body], { type: mime }))
  a.download = name
  a.click()
  URL.revokeObjectURL(a.href)
}

function LogTable({ rows }: { rows: Evaluation[] }) {
  const { bots } = useData()
  const [text, setText] = useState('')
  const [verdict, setVerdict] = useState('')
  const [agent, setAgent] = useState('')
  const name = (id: string) => bots.find((b) => b.id === id)?.name ?? id
  const list = useMemo(
    () => rows.filter((r) => (!text || r.case_id.toLowerCase().includes(text.toLowerCase())) && (!verdict || r.verdict === verdict) && (!agent || r.bot_id === agent)),
    [rows, text, verdict, agent],
  )
  const flat = (e: Evaluation) => ({
    case_id: e.case_id, agent: name(e.bot_id), date: new Date(e.created_at * 1000).toISOString(), status: VERDICT_LABEL[e.verdict], average_score: avgOf(e)?.toFixed(2) ?? '', route: ROUTE,
    run_id: e.run_id ?? '', session_id: e.session_id ?? '', reviewer: e.reviewer, critical_failure: e.notes.critical, errors: e.notes.errors, improvements: e.notes.improvements,
    prompt: e.prompt, expected: e.expected, actual: e.actual, ...Object.fromEntries(RUBRIC.map((d) => [`score_${d.key}`, e.scores[d.key]?.score ?? 'N/A'])),
    comparison_mode: e.comparison ? (e.comparison.mode === 'repeat' ? 'Ulang N kali' : 'Dua agen') : '',
    comparison_run_ids: e.comparison ? e.comparison.runs.map((r) => r.run_id).join(' | ') : '',
    comparison_consistency: e.comparison ? (e.comparison.consistency === 'konsisten' ? 'Konsisten' : 'Tidak konsisten') : '',
    comparison_note: e.comparison?.note ?? '',
    ...Object.fromEntries(VER_KEYS.map((k) => [`version_${k}`, metaValue(e.meta, k)])),
  })
  function csv() {
    const f = list.map(flat)
    if (!f.length) return
    const head = Object.keys(f[0])
    download('log-eksperimen.csv', 'text/csv;charset=utf-8', '﻿' + [head.join(','), ...f.map((r) => head.map((h) => csvCell((r as Record<string, unknown>)[h])).join(','))].join('\r\n'))
  }
  function json() {
    download('log-eksperimen.json', 'application/json', JSON.stringify(list.map((e) => ({ ...flat(e), scores: e.scores, meta: e.meta, comparison: e.comparison })), null, 2))
  }

  if (!rows.length) return <Empty title="Log masih kosong">Evaluasi yang disimpan muncul di sini.</Empty>
  return (
    <>
      <div className="toolbar">
        <input type="search" placeholder="Cari ID kasus" aria-label="Cari ID kasus" value={text} onChange={(e) => setText(e.target.value)} />
        <select aria-label="Filter hasil" value={verdict} onChange={(e) => setVerdict(e.target.value)}>
          <option value="">Semua hasil</option>
          {(Object.keys(VERDICT_LABEL) as Verdict[]).map((v) => <option key={v} value={v}>{VERDICT_LABEL[v]}</option>)}
        </select>
        <select aria-label="Filter agen" value={agent} onChange={(e) => setAgent(e.target.value)}>
          <option value="">Semua agen</option>
          {[...new Set(rows.map((r) => r.bot_id))].map((id) => <option key={id} value={id}>{name(id)}</option>)}
        </select>
        <button className="btn outline" onClick={csv} disabled={!list.length}>Unduh CSV</button>
        <button className="btn outline" onClick={json} disabled={!list.length}>Unduh JSON</button>
      </div>
      <div className="table-wrap">
        <table className="plain">
          <thead><tr><th>Kasus</th><th>Agen</th><th>Tanggal</th><th>Status</th><th>Skor rata-rata</th><th>Rute</th><th>Reviewer</th></tr></thead>
          <tbody>
            {list.map((e) => (
              <Fragment key={e.id}>
              <tr className={VER_ROW}>
                <td className="num" data-label="Kasus"><b>{e.case_id}</b>{e.comparison && <span className="pill origin tag">Bandingkan</span>}</td>
                <td data-label="Agen">{name(e.bot_id)}</td>
                <td className="num" data-label="Tanggal">{new Date(e.created_at * 1000).toLocaleString('id-ID', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</td>
                <td data-label="Status"><span className={`pill ${e.verdict === 'pass' ? 'ok' : e.verdict === 'fail' ? 'bad' : 'warn'}`}>{VERDICT_LABEL[e.verdict]}</span></td>
                <td className="num" data-label="Skor rata-rata">{avgOf(e)?.toFixed(1) ?? '–'}</td>
                <td data-label="Rute">{ROUTE}</td>
                <td data-label="Reviewer">{e.reviewer || '–'}</td>
              </tr>
              <tr className="sub-row">
                <td colSpan={7}>
                  <Versions items={e.comparison ? e.comparison.runs.map((r, i) => ({ label: `Run ${i + 1} · ${name(r.bot_id)}`, meta: r.meta })) : [{ label: 'Run', meta: e.meta }]} />
                  {e.comparison && (
                    <p className="quiet small cmp-sum">
                      {e.comparison.mode === 'repeat' ? 'Ulang N kali' : 'Dua agen'}: <b>{e.comparison.consistency === 'konsisten' ? 'Konsisten' : 'Tidak konsisten'}</b>. Run: {e.comparison.runs.map((r) => r.run_id.slice(0, 8)).join(', ')}.{e.comparison.note ? ` ${e.comparison.note}` : ''}
                    </p>
                  )}
                </td>
              </tr>
              </Fragment>
            ))}
            {list.length === 0 && <tr><td colSpan={7} className="quiet">Tidak ada baris yang cocok dengan filter.</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  )
}
