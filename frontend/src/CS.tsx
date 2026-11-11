import { useEffect, useRef, useState } from 'react'
import { useData } from './data'
import type { Bot } from './bff'
import { Cs21Card, CsCard, PlainAnswer, Provenance, ValidationBadge } from './ResultCards'
import { parseCs, partialReplyDraft } from './results'
import { LiveDraft } from './LiveSteps'
import type { ContextRef, Cs21, CsResult, Validation } from './results'
import { SCENARIOS } from './scenarios'
import { useRun } from './useRun'
import { Empty, Loading, PageHead } from './ui-extra'
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

// "Contoh pertanyaan": the official demo cases and the V cases the demo does not repeat (V01 to V03 are the same texts as DEMO-A to C).
const EXAMPLE_GROUPS: { label: string; ids: string[] }[] = [
  { label: 'Demo CS v2.1', ids: ['DEMO-A', 'DEMO-B', 'DEMO-C'] },
  { label: 'Kasus uji', ids: ['V04', 'V05', 'V06'] },
]
const EXAMPLES = Object.fromEntries(SCENARIOS.filter((s) => s.group === 'cs').map((s) => [s.id, s]))

export default function CS() {
  const { bots } = useData()
  const team = teamBots(bots, 'customer_support')
  const [agent, setAgent] = useState('')
  const [pending, setPending] = useState('')
  const [gen, setGen] = useState(0)
  const dirty = useRef(false)
  const cur = team.find((b) => b.id === agent) ?? team.find((b) => b.id === 'siti') ?? team[0]

  return (
    <section className="page ws" data-team="customer_support">
      <PageHead title="Customer Service" sub="Simulasikan pertanyaan pelanggan. Jawaban berupa draf internal: tidak ada pesan yang dikirim." />
      {!cur ? <Loading text="Memuat agen CS..." /> : <Desk key={cur.id + ':' + gen} bot={cur} agentSelect={<AgentSelect label="Agen" bots={team} value={cur.id} onChange={(id) => (id === cur.id ? null : dirty.current ? setPending(id) : setAgent(id))} />} onDirty={(v) => (dirty.current = v)} onNew={() => { dirty.current = false; setGen((g) => g + 1) }} />}
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

function Desk({ bot, agentSelect, onDirty, onNew }: { bot: Bot; agentSelect: React.ReactNode; onDirty: (v: boolean) => void; onNew: () => void }) {
  const run = useRun(bot.id)
  const [simMode, setSimMode] = useState(false)
  const [turns, setTurns] = useState<Turn[]>([])
  const [pendingQ, setPendingQ] = useState('')
  const [draft, setDraft] = useState('')
  const [scn, setScn] = useState<{ id: string; i: number } | null>(null) // an example in progress: the next turn is filled in for you
  const [sel, setSel] = useState(0)
  const [sid, setSid] = useState('')
  const sidRef = useRef('')
  const nRef = useRef(0)
  const [last, setLast] = useState<(() => void) | null>(null)
  const [tried, setTried] = useState(false)

  useEffect(() => {
    onDirty(turns.length > 0 || draft.trim() !== '')
  }, [turns.length, draft, onDirty])

  function pick(id: string) {
    const s = EXAMPLES[id]
    if (!s) return
    setDraft(s.turns[0])
    setSimMode(s.simulate)
    setScn(s.turns.length > 1 ? { id, i: 0 } : null)
  }

  async function send(text: string) {
    setTried(true)
    if (!text.trim() || run.busy) return
    setLast(() => () => void send(text))
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
    // A multi-turn example: put the next customer message in the box.
    const s = scn ? EXAMPLES[scn.id] : null
    if (scn && s && scn.i + 1 < s.turns.length) {
      setDraft(s.turns[scn.i + 1])
      setScn({ id: scn.id, i: scn.i + 1 })
    } else setScn(null)
  }

  const streamDraft = run.busy ? partialReplyDraft(run.text) : null // the reply draft as it is being written, from the still-open JSON
  const shown = turns.find((t) => t.id === sel) ?? turns[turns.length - 1]
  const total = scn ? (EXAMPLES[scn.id]?.turns.length ?? 0) : 0

  return (
    <>
      <div className="ws-bar">
        {agentSelect}
        <Switch checked={simMode} onChange={setSimMode} label="Mode uji simulasi" hint="Menyertakan data simulasi pesanan, retur, dan kebijakan palsu (SIM-*) untuk pengujian. Hasilnya diberi label Simulasi. Bukan data pelanggan nyata." />
        <OpenInChat botId={bot.id} sid={sid} />
        {turns.length > 0 && (
          <button className="btn soft" onClick={onNew} disabled={run.busy}>
            Percakapan baru
          </button>
        )}
      </div>

      <div className="cs-grid">
        <div className="cs-conv">
          <form
            className="ask"
            onSubmit={(e) => {
              e.preventDefault()
              void send(draft)
            }}
          >
            <h2>Pertanyaan</h2>
            <label className="field">
              <span>Contoh pertanyaan</span>
              <select value="" onChange={(e) => pick(e.target.value)} disabled={run.busy}>
                <option value="">Pilih contoh...</option>
                {EXAMPLE_GROUPS.map((g) => (
                  <optgroup key={g.label} label={g.label}>
                    {g.ids.map((id) => EXAMPLES[id] && <option key={id} value={id}>{id} · {EXAMPLES[id].title.replace(/^Demo [A-C]: /, '')}</option>)}
                  </optgroup>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Pertanyaan pelanggan</span>
              <textarea
                rows={4}
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
            {scn && <p className="quiet small">Giliran {scn.i + 1} dari {total} sudah diisi. Kirim untuk melanjutkan.</p>}
            <button className="btn primary" type="submit" disabled={run.busy || !draft.trim()}>
              Kirim
            </button>
          </form>
          <RunBar busy={run.busy} tools={run.tools} writing={!!run.text} since={run.startedAt} clarify={run.clarify} onAnswer={run.answer} onStop={run.stop} status={run.status} error={run.error} onRetry={last ?? undefined} />
          {(turns.length > 0 || pendingQ) && (
            <section className="turns" aria-live="polite" aria-label="Percakapan">
              <h2>Percakapan</h2>
              {turns.map((t) => (
                <div key={t.id} className="turn-pair">
                  <p className="q">{t.inquiry}</p>
                  <button type="button" className="a" aria-current={shown?.id === t.id ? 'true' : undefined} onClick={() => setSel(t.id)}>
                    <span className="quiet small">{bot.name} · {hhmm(t.at)}{t.sim ? ' · simulasi' : ''}</span>
                    <span className="clamp3">{t.cs ? t.cs.reply : t.legacy ? t.legacy.draft : t.reply}</span>
                    <span className="quiet small">{t.cs ? 'Lihat hasil lengkap' : t.legacy ? 'Format lama, lihat hasil' : 'Tidak lolos validasi, jawaban mentah'}</span>
                  </button>
                </div>
              ))}
              {pendingQ && (
                <div className="turn-pair">
                  <p className="q">{pendingQ}</p>
                  <div className="a live">{streamDraft ? <LiveDraft text={streamDraft} label="Draf balasan · sedang ditulis" /> : <span className="quiet">{run.text ? 'Menyusun hasil terstruktur' : 'Menunggu jawaban'}</span>}</div>
                </div>
              )}
            </section>
          )}
        </div>

        <div className="cs-result" data-empty={shown ? undefined : ''}>
          <h2 className="sr">Hasil</h2>
          {shown ? (
            <>
              {shown.cs ? (
                <Cs21Card r={shown.cs} validation={shown.validation} origin="agent" meta={`Giliran ${shown.id} · ${hhmm(shown.at)}`} raw={shown.reply} refs={shown.refs} />
              ) : shown.legacy ? (
                <>
                  <CsCard r={shown.legacy} origin="agent" meta={`Giliran ${shown.id} · ${hhmm(shown.at)}`} />
                  <Provenance refs={shown.refs} workflow="cs" />
                </>
              ) : (
                <>
                  <PlainAnswer text={shown.reply} note={shown.validation?.status === 'invalid' ? 'Tidak lolos validasi skema v2.1' : 'Format terstruktur tidak ada'} />
                  <p className="quiet small"><ValidationBadge v={shown.validation} /> {shown.validation?.errors.length ? shown.validation.errors.join(' · ') : ''}</p>
                  <Provenance refs={shown.refs} workflow="cs" />
                </>
              )}
            </>
          ) : (
            <Empty title="Belum ada hasil">
              Setelah agen menjawab, hasilnya tampil berurutan:
              <ol className="rlist num-list">
                <li>Draf balasan pelanggan</li>
                <li>Intent dan prioritas</li>
                <li>Rekomendasi eskalasi</li>
                <li>Ringkasan tiket</li>
                <li>Sumber</li>
              </ol>
            </Empty>
          )}
        </div>
      </div>
    </>
  )
}
