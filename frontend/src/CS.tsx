import { useEffect, useRef, useState } from 'react'
import { useData } from './data'
import type { Bot } from './bff'
import { CS_EXAMPLE } from './fixtures'
import { Cs21Card, CsCard, PlainAnswer, Provenance, ValidationBadge } from './ResultCards'
import { parseCs } from './results'
import type { ContextRef, Cs21, CsResult, Validation } from './results'
import { useRun } from './useRun'
import { DataLegend, Empty, Loading, PageHead } from './ui-extra'
import { AgentSelect, ConfirmSwitch, OpenInChat, RunBar, Switch, hhmm, teamBots } from './ws-common'

interface Turn {
  id: number
  inquiry: string
  reply: string // raw answer of the agent
  cs: Cs21 | null // validated by the BFF
  legacy: CsResult | null // old kind:"cs" block, still readable
  validation: Validation | null
  refs: ContextRef[]
  sim: boolean
  runId: string
  at: Date
}
const CHIPS: { text: string; label: string; sim?: boolean }[] = [
  { label: 'Ukuran XL', text: 'Apakah kaos ini ada ukuran XL?' },
  { label: 'Rekomendasi', text: 'Aku cari kaos grafis buat hadiah teman cowok, ada rekomendasi?' },
  { label: 'Harga', text: 'Kaos grafis lengan pendek harganya berapa ya?' },
  { label: 'Pesanan terlambat', text: 'Pesananku sudah 10 hari belum sampai, tolong dicek.', sim: true },
  { label: 'Retur', text: 'Kaos yang kuterima kekecilan, bisa retur?', sim: true },
  { label: 'Refund', text: 'Aku mau refund pesanan kemarin, prosesnya bagaimana?', sim: true },
]

export default function CS() {
  const { bots } = useData()
  const team = teamBots(bots, 'customer_support')
  const [agent, setAgent] = useState('')
  const [pending, setPending] = useState('')
  const [gen, setGen] = useState(0)
  const dirty = useRef(false)
  const cur = team.find((b) => b.id === agent) ?? team.find((b) => b.id === 'siti') ?? team[0]

  return (
    <section className="page ws">
      <PageHead
        title="Customer Service"
        sub="Simulasikan pertanyaan pelanggan dan lihat draf jawaban terstruktur (CS v2.1)."
        hint={<>Untuk tanya bebas, pakai <a href="#/chat">Chat</a>.</>}
        actions={<AgentSelect label="Agen" bots={team} value={cur?.id ?? ''} onChange={(id) => (id === cur?.id ? null : dirty.current ? setPending(id) : setAgent(id))} />}
      />
      <p className="note-box">Mengikuti paket CS v2.1 (Mansi). Semua jawaban adalah draf internal: tidak ada pesan yang dikirim ke pelanggan, dan eskalasi hanya rekomendasi.</p>
      <DataLegend />
      {!cur ? <Loading text="Memuat agen CS..." /> : <Desk key={cur.id + ':' + gen} bot={cur} onDirty={(v) => (dirty.current = v)} onNew={() => { dirty.current = false; setGen((g) => g + 1) }} />}
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

function Desk({ bot, onDirty, onNew }: { bot: Bot; onDirty: (v: boolean) => void; onNew: () => void }) {
  const run = useRun(bot.id)
  const [simMode, setSimMode] = useState(false)
  const [sample, setSample] = useState(false)
  const [turns, setTurns] = useState<Turn[]>([])
  const [pendingQ, setPendingQ] = useState('')
  const [draft, setDraft] = useState('')
  const [sel, setSel] = useState(0)
  const [sid, setSid] = useState('')
  const sidRef = useRef('')
  const nRef = useRef(0)
  const [last, setLast] = useState<(() => void) | null>(null)
  const [tried, setTried] = useState(false)

  useEffect(() => {
    onDirty(turns.length > 0 || draft.trim() !== '')
  }, [turns.length, draft, onDirty])

  async function send(text: string) {
    setTried(true)
    if (!text.trim() || run.busy) return
    setLast(() => () => void send(text))
    setSample(false)
    setPendingQ(text.trim())
    setDraft('')
    const r = await run.send(text.trim(), { sid: sidRef.current || undefined, ctx: { workflow: 'cs', test_mode: simMode } })
    if (r.status === 'idle') return
    setPendingQ('')
    if (r.sid) {
      sidRef.current = r.sid
      setSid(r.sid)
    }
    if (r.status !== 'done') {
      setDraft(text.trim()) // keep the question so it can be sent again
      return
    }
    const { structured: cs, validation, refs } = r.result
    const t: Turn = { id: ++nRef.current, inquiry: text.trim(), reply: r.text.trim(), cs, legacy: cs ? null : parseCs(r.text).result, validation, refs, sim: simMode, runId: r.runId, at: new Date() }
    setTurns((cur) => [...cur, t])
    setSel(t.id)
  }

  const shown = turns.find((t) => t.id === sel) ?? turns[turns.length - 1]

  return (
    <>
      <div className="ws-bar">
        <Switch checked={simMode} onChange={setSimMode} label="Mode uji simulasi (SIM-*)" hint="Menyertakan data simulasi pesanan, retur, dan kebijakan palsu untuk pengujian. Hasilnya diberi label Simulasi. Bukan data pelanggan nyata." />
        <Switch checked={sample} onChange={setSample} label="Lihat contoh" />
        <OpenInChat botId={bot.id} sid={sid} />
        {turns.length > 0 && (
          <button className="btn soft" onClick={onNew} disabled={run.busy}>
            Percakapan baru
          </button>
        )}
      </div>

      <div className="cs-grid">
        <div className="cs-conv">
          <h2>Percakapan</h2>
          <div className="chip-row" aria-label="Skenario">
            {CHIPS.map((c) => (
              <button key={c.label} type="button" className="chip-btn" onClick={() => { setDraft(c.text); if (c.sim) setSimMode(true) }} disabled={run.busy}>
                {c.label}
                {c.sim && <span className="pill sim">Simulasi</span>}
              </button>
            ))}
          </div>
          <div className="turns" aria-live="polite">
            {turns.length === 0 && !pendingQ && <Empty title="Belum ada pertanyaan">Pilih skenario di atas atau tulis pertanyaan pelanggan.</Empty>}
            {turns.map((t) => (
              <div key={t.id} className="turn-pair">
                <p className="q">{t.inquiry}</p>
                <button type="button" className="a" aria-current={shown?.id === t.id ? 'true' : undefined} onClick={() => { setSel(t.id); setSample(false) }}>
                  <span className="quiet small">{bot.name} · {hhmm(t.at)}</span>
                  <span className="clamp3">{t.cs ? t.cs.reply : t.legacy ? t.legacy.draft : t.reply}</span>
                  <span className="quiet small">{t.cs ? 'Lihat hasil di kanan' : t.legacy ? 'Format lama, lihat di kanan' : 'Tidak lolos validasi, jawaban mentah'}{t.sim ? ' · simulasi' : ''}</span>
                </button>
              </div>
            ))}
            {pendingQ && (
              <div className="turn-pair">
                <p className="q">{pendingQ}</p>
                <div className="a live"><span className="quiet">{bot.name} {run.text ? 'sedang menyusun hasil terstruktur...' : 'sedang bekerja...'}</span></div>
              </div>
            )}
          </div>
          <RunBar busy={run.busy} text={`${bot.name} sedang menjawab...`} onStop={run.stop} status={run.status} error={run.error} onRetry={last ?? undefined} />
          <form
            className="ask"
            onSubmit={(e) => {
              e.preventDefault()
              void send(draft)
            }}
          >
            <label className="field">
              <span>Pertanyaan pelanggan</span>
              <textarea
                rows={2}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                aria-invalid={tried && !draft.trim() && turns.length === 0}
                placeholder="Tulis pertanyaan seperti dari pelanggan"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    void send(draft)
                  }
                }}
              />
              {tried && !draft.trim() && turns.length === 0 && !run.busy && <small className="err" role="alert">Tulis pertanyaan dulu.</small>}
            </label>
            <button className="btn primary" type="submit" disabled={run.busy || !draft.trim()}>
              Kirim
            </button>
          </form>
        </div>

        <div className="cs-result">
          <h2>Hasil</h2>
          {sample ? (
            <div className="sample-box">
              <header><span className="pill sample">Contoh data</span><b>Contoh hasil CS</b></header>
              <p>Ini contoh bentuk kartu, bukan output agen.</p>
              <Cs21Card r={CS_EXAMPLE} validation={null} origin="sample" meta="contoh" />
            </div>
          ) : shown ? (
            <>
              {shown.cs ? (
                <Cs21Card r={shown.cs} validation={shown.validation} origin="agent" meta={`Giliran ${shown.id} · ${hhmm(shown.at)}`} />
              ) : shown.legacy ? (
                <CsCard r={shown.legacy} origin="agent" meta={`Giliran ${shown.id} · ${hhmm(shown.at)}`} />
              ) : (
                <>
                  <PlainAnswer text={shown.reply} note={shown.validation?.status === 'invalid' ? 'Tidak lolos validasi skema v2.1' : 'Format terstruktur tidak ada'} />
                  <p className="quiet small"><ValidationBadge v={shown.validation} /> {shown.validation?.errors.length ? shown.validation.errors.join(' · ') : ''}</p>
                </>
              )}
              <Provenance refs={shown.refs} workflow="cs" />
            </>
          ) : (
            <Empty title="Belum ada hasil">Klasifikasi, sumber, draf balasan, ringkasan, prioritas, dan rekomendasi eskalasi muncul di sini setelah agen menjawab.</Empty>
          )}
        </div>
      </div>
    </>
  )
}
