import { useEffect, useRef, useState } from 'react'
import { useData } from './data'
import type { Bot } from './bff'
import { MARKETING_EXAMPLES } from './fixtures'
import { AnswerDetails, MarketingCard, PlainAnswer, Provenance } from './ResultCards'
import { instructionsFor, parseMarketing, stripBlock } from './results'
import { LiveDraft } from './LiveSteps'
import type { ContextRef, MarketingKind, MarketingResult, Parsed } from './results'
import { useRun } from './useRun'
import { I, Icon } from './ui'
import { Empty, Loading, Opt, PageHead } from './ui-extra'
import { AgentSelect, ConfirmSwitch, OpenInChat, RunBar, Switch, hhmm, teamBots } from './ws-common'

const STAGES = ['Brief', 'Rencana', 'Konten', 'Review', 'Revisi'] as const
const KIND: MarketingKind[] = ['brief', 'plan', 'content', 'review', 'revision']
const CHANNELS = ['Instagram', 'TikTok', 'WhatsApp', 'Website / marketplace']
const CONTENT_TYPES = ['Caption Instagram', 'Copy promosi', 'Headline', 'Deskripsi produk', 'Skrip', 'Alternatif copy', 'Repurposing']

interface Output {
  id: string
  stage: number
  n: number // version within the stage
  label: string
  parsed: Parsed<MarketingResult>
  structured: boolean
  refs: ContextRef[]
  runId: string
  at: Date
}
const blankForm = { objective: '', product: '', channel: '', contentType: '', count: '', audience: '', tone: '', keyMessage: '', cta: '', period: '', promoFacts: '', forbidden: '', unknowns: '' }
type Form = typeof blankForm
const DUMMY: Form = {
  objective: 'Memperkenalkan kaos grafis baru ke pengikut Instagram',
  product: 'Colorbox Regular Fit Short Sleeve Graphic T-Shirt (Public Data · 9 Nov 2026)',
  channel: 'Instagram',
  contentType: 'Caption Instagram',
  count: '3',
  audience: 'Anak muda 18 sampai 25 tahun (Assumptions)',
  tone: 'Santai, jelas, ringkas',
  keyMessage: 'Kaos dengan grafis yang bikin orang bertanya',
  cta: 'Lihat katalog',
  period: '1 sampai 14 Desember 2026',
  promoFacts: '',
  forbidden: 'Jangan menyebut harga atau diskon. Jangan klaim "terlaris" atau "terbaik".',
  unknowns: '',
}
const FIELDS: [keyof Form, string][] = [
  ['audience', 'Audiens dan dasarnya'],
  ['tone', 'Bahasa dan nada'],
  ['keyMessage', 'Pesan kunci'],
  ['cta', 'CTA'],
  ['period', 'Periode'],
  ['promoFacts', 'Fakta promo'],
  ['forbidden', 'Klaim terlarang'],
  ['unknowns', 'Hal yang belum diketahui'],
]

function validate(f: Form): Partial<Record<keyof Form, string>> {
  const e: Partial<Record<keyof Form, string>> = {}
  if (!f.objective.trim()) e.objective = 'Tujuan wajib diisi.'
  if (!f.product.trim()) e.product = 'Produk atau topik wajib diisi.'
  if (!f.channel) e.channel = 'Pilih kanal.'
  if (!f.contentType) e.contentType = 'Pilih tipe konten.'
  const n = Number(f.count)
  if (!f.count.trim()) e.count = 'Jumlah output wajib diisi.'
  else if (!Number.isInteger(n) || n < 1 || n > 10) e.count = 'Isi angka bulat 1 sampai 10.'
  return e
}
function briefPrompt(f: Form): string {
  const row = (k: string, v: string) => (v.trim() ? `${k}: ${v.trim()}\n` : '')
  return (
    'Ini brief dari saya untuk konten Colorbox.\n\n' +
    row('Tujuan', f.objective) + row('Produk/topik', f.product) + row('Kanal', f.channel) + row('Tipe konten', f.contentType) + row('Jumlah output', f.count) +
    FIELDS.map(([k, l]) => row(l, f[k])).join('') +
    '\nTolong rapikan menjadi brief terstruktur. Tulis asumsi, pertanyaan yang masih terbuka, dan nyatakan siap atau belum siap dikerjakan. Jangan menulis konten dulu.'
  )
}
function draftText(o: Output): string {
  const r = o.parsed.result
  if (r?.kind === 'content') return r.items.map((i, n) => (r.items.length > 1 ? `Opsi ${n + 1}: ` : '') + i.text).join('\n\n')
  if (r?.kind === 'revision') return r.after
  return o.parsed.text
}

export default function Marketing() {
  const { bots } = useData()
  const team = teamBots(bots, 'marketing')
  const [agent, setAgent] = useState('')
  const [pending, setPending] = useState('')
  const dirty = useRef(false)
  const cur = team.find((b) => b.id === agent) ?? team.find((b) => b.id === 'rian') ?? team[0]

  return (
    <section className="page ws">
      <PageHead
        title="Marketing"
        sub="Satu alur, lima tahap: brief, rencana, konten, review, revisi."
        actions={<AgentSelect label="Agen" bots={team} value={cur?.id ?? ''} onChange={(id) => (id === cur?.id ? null : dirty.current ? setPending(id) : setAgent(id))} />}
      />
      {!cur ? <Loading text="Memuat agen Marketing..." /> : <Workspace key={cur.id} bot={cur} onDirty={(v) => (dirty.current = v)} />}
      {pending && (
        <ConfirmSwitch
          onYes={() => {
            dirty.current = false
            setAgent(pending)
            setPending('')
          }}
          onNo={() => setPending('')}
        />
      )}
    </section>
  )
}

function Workspace({ bot, onDirty }: { bot: Bot; onDirty: (v: boolean) => void }) {
  const run = useRun(bot.id)
  const [structured, setStructured] = useState(true)
  const [sample, setSample] = useState(false)
  const [stage, setStage] = useState(0)
  const [form, setForm] = useState<Form>(blankForm)
  const [tried, setTried] = useState(false)
  const [outs, setOuts] = useState<Output[]>([])
  const [view, setView] = useState('')
  const [sid, setSid] = useState('')
  const sidRef = useRef('')
  const counts = useRef<Record<number, number>>({})
  const [ctype, setCtype] = useState('')
  const [draftId, setDraftId] = useState('')
  const [feedback, setFeedback] = useState('')
  const [keep, setKeep] = useState('')
  const [fbTried, setFbTried] = useState(false)
  const [last, setLast] = useState<(() => void) | null>(null)

  const errs = validate(form)
  const hasWork = outs.length > 0 || JSON.stringify(form) !== JSON.stringify(blankForm) || feedback !== '' || keep !== ''
  useEffect(() => {
    onDirty(hasWork)
  }, [hasWork, onDirty])

  const drafts = outs.filter((o) => o.stage === 2 || o.stage === 4)
  const draft = drafts.find((o) => o.id === draftId) ?? drafts[drafts.length - 1]
  const hasBrief = outs.some((o) => o.stage === 0)
  const hasPlan = outs.some((o) => o.stage === 1)

  async function go(st: number, prompt: string, label: string) {
    setLast(() => () => void go(st, prompt, label))
    setSample(false)
    const kind = KIND[st]
    const r = await run.send(prompt, { sid: sidRef.current || undefined, instructions: structured ? instructionsFor(kind) : undefined, ctx: { workflow: 'marketing', stage: STAGES[st].toLowerCase() } })
    if (r.status === 'idle') return // superseded or reset: ignore
    if (r.sid) {
      sidRef.current = r.sid
      setSid(r.sid)
    }
    if (r.status !== 'done') return
    const parsed: Parsed<MarketingResult> = structured ? parseMarketing(r.text, kind) : { text: r.text.trim(), result: null, state: 'none', raw: '' }
    const n = (counts.current[st] = (counts.current[st] ?? 0) + 1)
    const o: Output = { id: `${st}-${n}`, stage: st, n, label, parsed, structured, refs: r.result.refs, runId: r.runId, at: new Date() }
    setOuts((cur) => [...cur, o])
    setView(o.id)
    setStage(st)
  }

  function submitBrief(e: React.FormEvent) {
    e.preventDefault()
    setTried(true)
    if (Object.keys(errs).length || run.busy) return
    void go(0, briefPrompt(form), 'Brief')
  }
  function makePlan() {
    void go(1, 'Berdasarkan brief tadi, buat creative brief, ide atau konsep bernomor, dan kalender konten (tanggal, kanal, tipe, ide, pesan, CTA). Jangan menulis draf lengkap dulu.', 'Rencana')
  }
  function makeContent() {
    const t = ctype || form.contentType || CONTENT_TYPES[0]
    const n = Number(form.count) >= 1 ? Number(form.count) : 3
    let p = `Tulis ${t} sebanyak ${n} opsi sesuai brief${hasPlan ? ' dan rencana' : ''} tadi. Sebut sumber klaim, asumsi kreatif, dan peringatan.`
    if (/Repurposing|Alternatif/.test(t) && draft) p += `\n\nDraf sumber:\n${draftText(draft)}`
    void go(2, p, t)
  }
  function makeReview() {
    if (!draft) return
    void go(3, `Review draf ini terhadap brief dan brand (nilai 9 dimensi dengan skor 1 sampai 5):\n\n${draftText(draft)}`, `Review ${draft.label}`)
  }
  function makeRevision(e: React.FormEvent) {
    e.preventDefault()
    setFbTried(true)
    if (!draft || !feedback.trim() || run.busy) return
    const base = draftText(draft)
    void go(4, `Revisi draf ini berdasarkan feedback.\n\nDraf:\n${base}\n\nFeedback: ${feedback.trim()}\n${keep.trim() ? `Bagian yang wajib dipertahankan: ${keep.trim()}\n` : ''}\nIsi "before" dengan draf di atas dan "after" dengan draf revisi lengkap.`, 'Revisi')
  }

  const inStage = outs.filter((o) => o.stage === stage)
  const shown = outs.find((o) => o.id === view && o.stage === stage) ?? inStage[inStage.length - 1]
  const needs = (ok: boolean, msg: string) => !ok && <p className="note-box">{msg}</p>
  const stageDone = (i: number) => outs.some((o) => o.stage === i)
  const revCount = (o: Output) => (o.stage === 4 ? `v${o.n} → v${o.n + 1}` : `v${o.n}`)
  const meta = (o: Output) => `BR-0001 · ${revCount(o)} · ${hhmm(o.at)}`

  return (
    <>
      {sid && (
        <div className="ws-bar">
          <OpenInChat botId={bot.id} sid={sid} />
          <span className="quiet small ws-sess">Semua tahap memakai percakapan yang sama.</span>
        </div>
      )}

      <ol className="stepper" aria-label="Tahap kerja">
        {STAGES.map((s, i) => (
          <li key={s} data-link={i > 0 && stageDone(i - 1) ? 'done' : undefined}>
            <button type="button" aria-current={stage === i ? 'step' : undefined} onClick={() => setStage(i)} data-done={stageDone(i) || undefined}>
              <span className="step-n" aria-hidden="true">{stageDone(i) ? <Icon d={I.check} size={14} /> : i + 1}</span>
              <span>{s}{stageDone(i) && <span className="sr">, selesai</span>}</span>
            </button>
          </li>
        ))}
      </ol>

      <div className="ws-grid" data-solo={outs.length === 0 || undefined}>
        <div className="ws-main">
          {stage === 0 && (
            <form className="ws-form" onSubmit={submitBrief} noValidate>
              <div className="ws-form-head">
                <h2>Brief</h2>
                <button type="button" className="btn soft" onClick={() => setForm(DUMMY)}>
                  Isi contoh Colorbox
                </button>
              </div>
              <div className="fgrid">
                <Field label="Tujuan" err={tried ? errs.objective : ''}>
                  <input value={form.objective} onChange={(e) => setForm({ ...form, objective: e.target.value })} aria-invalid={tried && !!errs.objective} />
                </Field>
                <Field label="Produk atau topik" err={tried ? errs.product : ''}>
                  <input value={form.product} onChange={(e) => setForm({ ...form, product: e.target.value })} aria-invalid={tried && !!errs.product} />
                </Field>
                <Field label="Kanal" err={tried ? errs.channel : ''}>
                  <select value={form.channel} onChange={(e) => setForm({ ...form, channel: e.target.value })} aria-invalid={tried && !!errs.channel}>
                    <option value="">Pilih kanal</option>
                    {CHANNELS.map((c) => <option key={c}>{c}</option>)}
                  </select>
                </Field>
                <Field label="Tipe konten" err={tried ? errs.contentType : ''}>
                  <select value={form.contentType} onChange={(e) => setForm({ ...form, contentType: e.target.value })} aria-invalid={tried && !!errs.contentType}>
                    <option value="">Pilih tipe</option>
                    {CONTENT_TYPES.map((c) => <option key={c}>{c}</option>)}
                  </select>
                </Field>
                <Field label="Jumlah output" err={tried ? errs.count : ''}>
                  <input inputMode="numeric" value={form.count} onChange={(e) => setForm({ ...form, count: e.target.value })} aria-invalid={tried && !!errs.count} />
                </Field>
              </div>
              <details className="opts" open={FIELDS.some(([k]) => form[k].trim() !== '') || undefined}>
                <summary>Tambahan (opsional)</summary>
                <div className="fgrid opts-body">
                  {FIELDS.map(([k, l]) => (
                    <Field key={k} label={l}>
                      <input value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} />
                    </Field>
                  ))}
                </div>
              </details>
              {tried && Object.keys(errs).length > 0 && <p className="field-err" role="alert">Lengkapi {Object.keys(errs).length} kolom wajib di atas.</p>}
              <div className="form-actions">
                <button className="btn primary" type="submit" disabled={run.busy}>
                  Kirim brief
                </button>
              </div>
            </form>
          )}
          {stage === 1 && (
            <div className="ws-act">
              <h2>Rencana</h2>
              <p className="quiet">Minta creative brief, ide, dan kalender dari brief yang sudah dikirim.</p>
              {needs(hasBrief, 'Kirim brief dulu di tahap Brief.')}
              <button className="btn primary" disabled={run.busy || !hasBrief} onClick={makePlan}>Buat rencana</button>
            </div>
          )}
          {stage === 2 && (
            <div className="ws-act">
              <h2>Konten</h2>
              <p className="quiet">Pilih tipe konten, lalu minta draf.</p>
              {needs(hasBrief, 'Kirim brief dulu di tahap Brief.')}
              <label className="field">
                <span>Tipe konten</span>
                <select value={ctype || form.contentType || CONTENT_TYPES[0]} onChange={(e) => setCtype(e.target.value)}>
                  {CONTENT_TYPES.map((c) => <option key={c}>{c}</option>)}
                </select>
              </label>
              <button className="btn primary" disabled={run.busy || !hasBrief} onClick={makeContent}>Buat konten</button>
            </div>
          )}
          {stage === 3 && (
            <div className="ws-act">
              <h2>Review</h2>
              <p className="quiet">Minta review brand dan konten untuk satu draf. Hasilnya skor 1 sampai 5 per dimensi.</p>
              {needs(!!draft, 'Belum ada draf. Buat konten dulu di tahap Konten.')}
              {draft && <DraftPick drafts={drafts} value={draft.id} onChange={setDraftId} />}
              <button className="btn primary" disabled={run.busy || !draft} onClick={makeReview}>Minta review</button>
            </div>
          )}
          {stage === 4 && (
            <form className="ws-act" onSubmit={makeRevision} noValidate>
              <h2>Revisi</h2>
              <p className="quiet">Tulis feedback, lalu minta revisi. Hasil dibandingkan dengan draf sebelumnya.</p>
              {needs(!!draft, 'Belum ada draf. Buat konten dulu di tahap Konten.')}
              {draft && <DraftPick drafts={drafts} value={draft.id} onChange={setDraftId} />}
              <Field label="Feedback" err={fbTried && !feedback.trim() ? 'Tulis feedback untuk revisi.' : ''}>
                <textarea rows={3} value={feedback} onChange={(e) => setFeedback(e.target.value)} aria-invalid={fbTried && !feedback.trim()} />
              </Field>
              <Field label="Bagian yang wajib dipertahankan" opt>
                <textarea rows={2} value={keep} onChange={(e) => setKeep(e.target.value)} placeholder="Contoh: nama produk dan nada santai" />
              </Field>
              <button className="btn primary" type="submit" disabled={run.busy || !draft}>Minta revisi</button>
            </form>
          )}

          <RunBar busy={run.busy} tools={run.tools} writing={!!run.text} since={run.startedAt} onStop={run.stop} status={run.status} error={run.error} onRetry={last ?? undefined} />
          {run.busy && run.text && <article className="rcard live"><div className="rbody"><LiveDraft text={stripBlock(run.text)} /></div></article>}

          {sample ? (
            <div className="sample-box">
              <header><span className="pill sample">Contoh data</span><b>Contoh dari requirement (E-01 sampai E-05)</b></header>
              <p>Ini rancangan, bukan output agen. Tidak tercampur dengan hasil nyata.</p>
              {MARKETING_EXAMPLES.map((e) => <MarketingCard key={e.id} r={e.result} origin="sample" meta={`contoh ${e.id}`} />)}
            </div>
          ) : (
            !run.busy && (shown ? <OutputView o={shown} meta={meta(shown)} /> : stage > 0 || !run.error ? <Empty title="Belum ada hasil di tahap ini">{stage === 0 ? 'Isi brief lalu kirim. Kartu brief muncul di sini.' : 'Hasil tahap ini muncul di sini.'}</Empty> : null)
          )}
        </div>

        {outs.length > 0 && (
        <aside className="ws-hist" aria-label="Riwayat hasil">
          <h2>Riwayat hasil</h2>
            <ul>
              {[...outs].reverse().map((o) => (
                <li key={o.id}>
                  <button type="button" aria-current={shown?.id === o.id ? 'true' : undefined} onClick={() => { setStage(o.stage); setView(o.id) }}>
                    <b>{STAGES[o.stage]} {revCount(o)}</b>
                    <span className="quiet small">{o.label} · {hhmm(o.at)} · {o.parsed.state === 'ok' ? 'kartu' : o.structured ? 'teks' : 'teks (mode biasa)'}</span>
                  </button>
                </li>
              ))}
            </ul>
        </aside>
        )}
      </div>

      <details className="opts">
        <summary>Opsi lanjutan</summary>
        <div className="opts-body">
          <Switch checked={structured} onChange={setStructured} label="Hasil terstruktur (eksperimen)" hint="Agen diminta menutup jawaban dengan satu blok JSON untuk kartu hasil. Skema ini usulan frontend dan belum divalidasi backend." />
          <p className="quiet small">Jika blok tidak terbaca, jawaban teks tetap ditampilkan.</p>
          <Switch checked={sample} onChange={setSample} label="Tampilkan contoh hasil" hint="Contoh bentuk kartu dari requirement. Bukan output agen." />
        </div>
      </details>
    </>
  )
}

function OutputView({ o, meta }: { o: Output; meta: string }) {
  if (o.parsed.result)
    return (
      <>
        <MarketingCard r={o.parsed.result} origin="agent" meta={meta} />
        <AnswerDetails text={o.parsed.text} />
        <Provenance refs={o.refs} workflow="marketing" />
      </>
    )
  return (
    <>
      <PlainAnswer text={o.parsed.text} note={o.structured ? 'Format terstruktur tidak terbaca' : undefined} />
      <Provenance refs={o.refs} workflow="marketing" />
    </>
  )
}

function Field({ label, err, opt, children }: { label: string; err?: string; opt?: boolean; children: React.ReactNode }) {
  return (
    <label className="field">
      <span>{label}{opt && <> <Opt /></>}</span>
      {children}
      {err && <small className="err" role="alert">{err}</small>}
    </label>
  )
}

function DraftPick({ drafts, value, onChange }: { drafts: Output[]; value: string; onChange: (id: string) => void }) {
  return (
    <label className="field">
      <span>Draf yang dipakai</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {drafts.map((d) => (
          <option key={d.id} value={d.id}>
            {STAGES[d.stage]} v{d.n} · {d.label}
          </option>
        ))}
      </select>
    </label>
  )
}
