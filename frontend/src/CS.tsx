import { useEffect, useRef, useState } from 'react'
import { useData } from './data'
import type { Bot } from './bff'
import { CS_EXAMPLE } from './fixtures'
import { AnswerDetails, CsCard, PlainAnswer } from './ResultCards'
import { instructionsFor, parseCs, stripBlock } from './results'
import type { CsResult, Parsed } from './results'
import { useRun } from './useRun'
import { Empty, Loading, PageHead } from './ui-extra'
import { AgentSelect, ConfirmSwitch, OpenInChat, RunBar, Switch, hhmm, teamBots } from './ws-common'

interface Turn {
  id: number
  inquiry: string
  reply: string
  parsed: Parsed<CsResult>
  structured: boolean
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
        title="Workspace CS"
        sub="Pertanyaan pelanggan sampai rekomendasi eskalasi. Tidak ada pesan yang dikirim ke pelanggan."
        actions={<AgentSelect label="Agen" bots={team} value={cur?.id ?? ''} onChange={(id) => (id === cur?.id ? null : dirty.current ? setPending(id) : setAgent(id))} />}
      />
      <p className="note-box">Requirement CS (Mansi) belum final — struktur bisa berubah.</p>
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
  const [structured, setStructured] = useState(true)
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
    const r = await run.send(text.trim(), { sid: sidRef.current || undefined, instructions: structured ? instructionsFor('cs') : undefined })
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
    const parsed: Parsed<CsResult> = structured ? parseCs(r.text) : { text: r.text.trim(), result: null, state: 'none', raw: '' }
    const t: Turn = { id: ++nRef.current, inquiry: text.trim(), reply: parsed.text, parsed, structured, at: new Date() }
    setTurns((cur) => [...cur, t])
    setSel(t.id)
  }

  const shown = turns.find((t) => t.id === sel) ?? turns[turns.length - 1]

  return (
    <>
      <div className="ws-bar">
        <Switch checked={structured} onChange={setStructured} label="Mode terstruktur (eksperimen)" hint="Agen diminta menambahkan satu blok JSON untuk kartu hasil. Format ini usulan frontend dan belum divalidasi backend." />
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
              <button key={c.label} type="button" className="chip-btn" onClick={() => setDraft(c.text)} disabled={run.busy}>
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
                  <span className="clamp3">{t.reply || (t.parsed.result ? t.parsed.result.draft : '')}</span>
                  <span className="quiet small">{t.parsed.state === 'ok' ? 'Lihat hasil di kanan' : t.structured ? 'Format terstruktur tidak terbaca' : 'Teks'}</span>
                </button>
              </div>
            ))}
            {pendingQ && (
              <div className="turn-pair">
                <p className="q">{pendingQ}</p>
                <div className="a live">{run.text ? <span className="clamp3">{stripBlock(run.text)}</span> : <span className="quiet">{bot.name} sedang bekerja...</span>}</div>
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
              <CsCard r={CS_EXAMPLE} origin="sample" meta="contoh" />
            </div>
          ) : shown ? (
            shown.parsed.result ? (
              <CsCard r={shown.parsed.result} origin="agent" meta={`Giliran ${shown.id} · ${hhmm(shown.at)}`} />
            ) : (
              <PlainAnswer text={shown.reply} note={shown.structured ? 'Format terstruktur tidak terbaca' : undefined} />
            )
          ) : (
            <Empty title="Belum ada hasil">Klasifikasi, sumber, draf balasan, ringkasan, prioritas, dan rekomendasi eskalasi muncul di sini setelah agen menjawab.</Empty>
          )}
          {shown && !sample && shown.parsed.result && <AnswerDetails text={shown.reply} />}
        </div>
      </div>
    </>
  )
}
