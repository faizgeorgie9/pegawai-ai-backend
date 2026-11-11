import type { ReactNode } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { CLS_LABEL, INTENT_LABEL, RUBRIC } from './results'
import type { Cls, ContextRef, Cs21, CsResult, MarketingResult, Validation } from './results'
import { CopyButton } from './ui-extra'

export type Origin = 'agent' | 'sample'

export function ClassBadge({ c }: { c?: Cls }) {
  return c ? <span className={`pill cls cls-${c}`}>{CLS_LABEL[c]}</span> : null
}

function Frame({ title, meta, origin, flags, children }: { title: string; meta?: string; origin: Origin; flags?: ReactNode; children: ReactNode }) {
  return (
    <article className="rcard" data-origin={origin}>
      <header>
        <b>{title}</b>
        {meta && <span className="quiet small">{meta}</span>}
        <span className="rflags">
          {origin === 'sample' && <span className="pill sample" title="Isi buatan frontend untuk menunjukkan bentuk hasil. Bukan hasil agen.">Contoh data</span>}
          {flags}
        </span>
      </header>
      <div className="rbody">{children}</div>
    </article>
  )
}

const Block = ({ label, badge, children }: { label: string; badge?: ReactNode; children: ReactNode }) => (
  <section className="rblock">
    <h3>
      {label} {badge}
    </h3>
    {children}
  </section>
)
const List = ({ items }: { items: string[] }) => (
  <ul className="rlist">
    {items.map((t, i) => (
      <li key={i}>{t}</li>
    ))}
  </ul>
)
const Kv = ({ k, v }: { k: string; v: string }) => (v ? <><dt>{k}</dt><dd>{v}</dd></> : null)

// Word-level diff (LCS over words). Small texts only, so the O(n*m) table is fine.
export function diffWords(a: string, b: string): { t: string; k: 'same' | 'del' | 'ins' }[] {
  const x = a.split(/\s+/).filter(Boolean)
  const y = b.split(/\s+/).filter(Boolean)
  const L = Array.from({ length: x.length + 1 }, () => new Array<number>(y.length + 1).fill(0))
  for (let i = x.length - 1; i >= 0; i--) for (let j = y.length - 1; j >= 0; j--) L[i][j] = x[i] === y[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1])
  const out: { t: string; k: 'same' | 'del' | 'ins' }[] = []
  let i = 0
  let j = 0
  while (i < x.length || j < y.length) {
    if (i < x.length && j < y.length && x[i] === y[j]) out.push({ t: x[i++], k: 'same' }), j++
    else if (j < y.length && (i === x.length || L[i][j + 1] >= L[i + 1][j])) out.push({ t: y[j++], k: 'ins' })
    else out.push({ t: x[i++], k: 'del' })
  }
  return out
}

export function ScoreGrid({ scores }: { scores: Partial<Record<string, number>> }) {
  return (
    <div className="scores">
      {RUBRIC.map((d) => {
        const v = scores[d.key]
        return (
          <div key={d.key} className={v !== undefined && v < 4 ? 'low' : undefined}>
            <span>{d.label}</span>
            <b className="num">{v ?? '–'}</b>
          </div>
        )
      })}
    </div>
  )
}

export function MarketingCard({ r, origin, meta }: { r: MarketingResult; origin: Origin; meta?: string }) {
  switch (r.kind) {
    case 'brief':
      return (
        <Frame title="Brief terstruktur" meta={meta} origin={origin} flags={<span className={`pill ${r.ready ? 'ok' : 'warn'}`}>{r.ready ? 'Siap dikerjakan' : 'Belum siap'}</span>}>
          <dl className="kv2">{Object.entries(r.fields).map(([k, v]) => <Kv key={k} k={k.replace(/_/g, ' ')} v={v} />)}</dl>
          {r.assumptions.length > 0 && <Block label="Asumsi" badge={<span className="pill cls cls-assumptions">Assumptions</span>}><List items={r.assumptions} /></Block>}
          {r.questions.length > 0 && <Block label="Pertanyaan terbuka"><List items={r.questions} /></Block>}
        </Frame>
      )
    case 'plan':
      return (
        <Frame title="Rencana: ide dan kalender" meta={meta} origin={origin}>
          <Block label="Creative brief"><p>{r.creative_brief}</p></Block>
          <Block label="Ide dan konsep">
            <ol className="rlist num-list">
              {r.ideas.map((i, n) => (
                <li key={n}>
                  <b>{i.title}</b> {i.reason && <span className="quiet">· {i.reason}</span>} <ClassBadge c={i.classification} />
                </li>
              ))}
            </ol>
          </Block>
          <Block label="Kalender">
            <div className="table-wrap flat">
              <table className="plain">
                <thead><tr><th>Tanggal</th><th>Kanal</th><th>Tipe</th><th>Ide</th><th>Pesan</th><th>CTA</th></tr></thead>
                <tbody>{r.calendar.map((c, n) => <tr key={n}><td className="num" data-label="Tanggal">{c.date}</td><td data-label="Kanal">{c.channel}</td><td data-label="Tipe">{c.type}</td><td data-label="Ide">{c.idea}</td><td data-label="Pesan">{c.message}</td><td data-label="CTA">{c.cta}</td></tr>)}</tbody>
              </table>
            </div>
          </Block>
        </Frame>
      )
    case 'content':
      return (
        <Frame title={`Draf: ${r.type || 'konten'}`} meta={meta} origin={origin} flags={<span className="pill">Perlu review</span>}>
          {r.items.map((it, n) => (
            <Block key={n} label={r.items.length > 1 ? `Opsi ${n + 1}` : 'Teks'} badge={<ClassBadge c={it.classification} />}>
              <p className="draft-text">{it.text}</p>
              {it.alt_angle && <p className="quiet small">Sudut alternatif: {it.alt_angle}</p>}
            </Block>
          ))}
          {r.sources.length > 0 && <Block label="Sumber klaim"><List items={r.sources} /></Block>}
          {r.assumptions.length > 0 && <Block label="Asumsi kreatif" badge={<span className="pill cls cls-assumptions">Assumptions</span>}><List items={r.assumptions} /></Block>}
          {r.warnings.length > 0 && <ul className="warns">{r.warnings.map((w, i) => <li key={i}>Peringatan: {w}</li>)}</ul>}
        </Frame>
      )
    case 'review': {
      const vals = Object.values(r.scores)
      const low = RUBRIC.filter((d) => (r.scores[d.key] ?? 5) < 4).map((d) => d.label)
      return (
        <Frame title="Review brand dan konten" meta={meta} origin={origin} flags={<span className={`pill ${low.length ? 'warn' : 'ok'}`}>{low.length ? 'Perlu revisi' : 'Lolos ambang usulan'}</span>}>
          {r.findings.length > 0 && <Block label="Temuan"><List items={r.findings} /></Block>}
          {r.evidence.length > 0 && <Block label="Bukti"><List items={r.evidence} /></Block>}
          {r.recommendations.length > 0 && <Block label="Rekomendasi"><List items={r.recommendations} /></Block>}
          <ScoreGrid scores={r.scores} />
          <p className="quiet small">
            Rata-rata {(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1)}. Ambang usulan: minimal 4 di setiap dimensi.{low.length ? ` Di bawah ambang: ${low.join(', ')}.` : ''} Keputusan akhir ada pada reviewer.
          </p>
        </Frame>
      )
    }
    case 'revision': {
      const d = diffWords(r.before, r.after)
      return (
        <Frame title="Revisi dari feedback" meta={meta} origin={origin}>
          <div className="cmp">
            <section className="rblock old"><h3>Sebelum</h3><p>{d.filter((x) => x.k !== 'ins').map((x, i) => (x.k === 'del' ? <del key={i}>{x.t} </del> : x.t + ' '))}</p></section>
            <section className="rblock new"><h3>Sesudah</h3><p>{d.filter((x) => x.k !== 'del').map((x, i) => (x.k === 'ins' ? <ins key={i}>{x.t} </ins> : x.t + ' '))}</p></section>
          </div>
          {r.feedback_applied.length > 0 && <Block label="Feedback yang ditindaklanjuti"><List items={r.feedback_applied} /></Block>}
          {r.change_log.length > 0 && <Block label="Change log"><List items={r.change_log} /></Block>}
          {r.open_issues.length > 0 && <Block label="Masalah terbuka"><List items={r.open_issues} /></Block>}
        </Frame>
      )
    }
  }
}

export function CsCard({ r, origin, meta }: { r: CsResult; origin: Origin; meta?: string }) {
  return (
    <Frame title="Hasil CS" meta={meta} origin={origin} flags={r.simulated ? <span className="pill sim">Simulasi</span> : null}>
      <div className="cs-top">
        <span className="pill cls-class">{r.classification || 'Tanpa klasifikasi'}</span>
        <span className={`pill prio-${r.priority}`}>Prioritas {r.priority}</span>
        <span className={`pill ${r.escalate ? 'bad' : 'ok'}`}>{r.escalate ? 'Perlu eskalasi' : 'Tidak perlu eskalasi'}</span>
      </div>
      {r.inquiry && <Block label="Pertanyaan"><p>{r.inquiry}</p></Block>}
      <Block label="Draf balasan" badge={<span className="pill warn">Draf — perlu review manusia</span>}>
        <p className="draft-text">{r.draft}</p>
      </Block>
      <Block label="Sumber">
        {r.sources.length ? (
          <ul className="rlist">{r.sources.map((s, i) => <li key={i}><b>{s.ref}</b> {s.excerpt && <span className="quiet">· {s.excerpt}</span>} <ClassBadge c={s.classification} /></li>)}</ul>
        ) : (
          <p className="quiet">Tidak ada sumber disebut. Draf ini tidak berbasis sumber.</p>
        )}
      </Block>
      {r.summary && <Block label="Ringkasan tiket"><p>{r.summary}</p></Block>}
      {r.context_notes && <Block label="Konteks percakapan"><p>{r.context_notes}</p></Block>}
      {r.escalate && <Block label="Alasan eskalasi"><p>{r.escalation_reason || 'Tidak ada alasan ditulis.'}</p></Block>}
    </Frame>
  )
}

const http = (u: string) => /^https?:\/\//i.test(u)
const Link = ({ url }: { url: string }) => (http(url) ? <a href={url} target="_blank" rel="noopener noreferrer">{url.replace(/^https?:\/\//, '')}</a> : null)
const SubList = ({ label, items }: { label: string; items: string[] }) => (items.length ? <><h4>{label}</h4><List items={items} /></> : null)

const VALID_LABEL: Record<Validation['status'], string> = { valid: 'Valid (skema v2.1)', repaired: 'Diperbaiki otomatis (skema v2.1)', invalid: 'Tidak valid', not_applicable: 'Tidak diperiksa' }
export function ValidationBadge({ v }: { v: Validation | null }) {
  if (!v) return null
  return <span className={`pill ${v.status === 'valid' ? 'ok' : v.status === 'invalid' ? 'bad' : 'warn'}`} title={v.errors.join('\n') || undefined}>{VALID_LABEL[v.status]}</span>
}

// CS v2.1 result, validated by the BFF. Ordered by what the reader needs first: the reply draft, intent and priority, the escalation
// recommendation (a recommendation only: nothing is routed to anyone), the ticket summary, the sources, then the technical details, folded.
export function Cs21Card({ r, validation, origin, meta, raw, refs }: { r: Cs21; validation: Validation | null; origin: Origin; meta?: string; raw?: string; refs?: ContextRef[] }) {
  const s = r.summary
  const prio = { P0: 'Kritis', P1: 'Tinggi', P2: 'Sedang', P3: 'Rendah' }[r.priority]
  return (
    <Frame
      title="Hasil CS"
      meta={meta}
      origin={origin}
      flags={<>{r.simulation.simulated && <span className="pill sim" title="Tidak ada pesan yang dikirim ke pelanggan. Semuanya latihan.">Simulasi{r.simulation.ids.length ? ` · ${r.simulation.ids.join(', ')}` : ''}</span>}{validation && validation.status !== 'valid' && <ValidationBadge v={validation} />}</>}
    >
      <Block label="Draf balasan pelanggan" badge={<><span className="pill warn">Draf internal, perlu tinjauan manusia</span> <CopyButton text={r.reply} what="draf balasan" /></>}>
        <p className="draft-text">{r.reply}</p>
        {r.clarifying && <p className="quiet small">Pertanyaan klarifikasi: {r.clarifying}</p>}
      </Block>
      <Block label="Intent dan prioritas">
        <div className="cs-top">
          <span className="pill cls-class" title={r.primary_intent}>{INTENT_LABEL[r.primary_intent] ?? r.primary_intent}</span>
          <span className={`pill prio-${r.priority}`}>{r.priority} · {prio}</span>
        </div>
        {r.secondary_intents.length > 0 && <p className="quiet small">Intent tambahan: {r.secondary_intents.map((i) => INTENT_LABEL[i] ?? i).join(', ')}</p>}
      </Block>
      <Block label="Rekomendasi eskalasi" badge={<span className={`pill ${r.escalation.recommended ? 'bad' : 'ok'}`}>{r.escalation.recommended ? 'Direkomendasikan' : 'Tidak direkomendasikan'}</span>}>
        <p>{r.escalation.reason || (r.escalation.recommended ? 'Tidak ada alasan ditulis.' : 'Tidak ada alasan eskalasi. Draf tetap perlu ditinjau manusia.')}</p>
        <p className="quiet small">Hanya rekomendasi. Tidak ada yang dikirim ke siapa pun.</p>
      </Block>
      <Block label="Ringkasan tiket">
        {s.issue && <p>{s.issue}</p>}
        <SubList label="Dilaporkan pelanggan" items={s.reported} />
        <SubList label="Terverifikasi dari sumber publik" items={s.verified} />
        <SubList label="Belum diketahui" items={s.unknowns} />
        <SubList label="Referensi dari pelanggan" items={s.references} />
        {s.outcome && <><h4>Hasil yang diminta</h4><p>{s.outcome}</p></>}
        <SubList label="Konteks yang dipertahankan" items={s.context} />
      </Block>
      <Block label="Sumber">
        {r.refs.length ? (
          <ul className="rlist">
            {r.refs.map((k, i) => (
              <li key={i}>
                <b>{k.knowledge_id}</b> {k.source_ids.length > 0 && <span className="quiet">· {k.source_ids.join(', ')} (daftar sumber CS)</span>}
                {k.used_for && <div>{k.used_for}</div>}
                <div className="quiet small"><Link url={k.source_url} /> {k.accessed_date && <span className="num">· dicek {k.accessed_date}</span>}</div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="quiet">Tidak ada referensi knowledge disebut.</p>
        )}
        {refs && <Provenance refs={refs} workflow="cs" />}
      </Block>
      <details className="tech">
        <summary>Detail teknis</summary>
        <dl className="kv2">
          <dt>Keyakinan</dt>
          <dd className="num">{Math.round(r.confidence * 100)}%</dd>
          <dt>Validasi</dt>
          <dd>{validation ? <ValidationBadge v={validation} /> : 'Tidak diperiksa'}</dd>
          <dt>Intent utama</dt>
          <dd>{r.primary_intent}</dd>
        </dl>
        {raw && (
          <>
            <h4>Jawaban mentah agen</h4>
            <pre className="raw">{raw}</pre>
          </>
        )}
      </details>
    </Frame>
  )
}

// "Sumber jawaban": what the BFF put into the agent's context (not necessarily what the answer cites).
const REF_TYPE = { knowledge: 'Knowledge', product: 'Produk katalog', fixture: 'Fixture simulasi' } as const
const refCls = (c: string): Cls | undefined => (/^public/i.test(c) ? 'public_data' : /^research/i.test(c) ? 'research_findings' : /^assum/i.test(c) ? 'assumptions' : /^dummy|^simul/i.test(c) ? 'dummy' : undefined)
export function Provenance({ refs, workflow }: { refs: ContextRef[]; workflow: 'cs' | 'marketing' }) {
  if (!refs.length) return null
  const reg = workflow === 'cs' ? 'daftar sumber CS' : 'daftar sumber Hub'
  return (
    <details className="prov">
      <summary>Sumber jawaban <span className="quiet small">({refs.length})</span></summary>
      <p className="quiet small">Konteks yang diberikan ke agen untuk run ini, belum tentu semuanya dikutip di jawaban. ID SRC-xx hanya berlaku di {reg}.</p>
      {(['knowledge', 'product', 'fixture'] as const).map((t) => {
        const list = refs.filter((x) => x.type === t)
        if (!list.length) return null
        return (
          <section key={t} className="rblock">
            <h3>{REF_TYPE[t]} <span className="quiet small">({list.length})</span></h3>
            <ul className="rlist prov-list">
              {list.map((x, i) => (
                <li key={i}>
                  <b>{x.title || x.id}</b> {x.title && x.title !== x.id && <span className="quiet">· {x.id}</span>}{' '}
                  {refCls(x.classification) ? <ClassBadge c={refCls(x.classification)} /> : x.classification && <span className="pill plain cls">{x.classification}</span>}
                  <div className="quiet small">
                    {x.source_id && <span>{x.source_id} · {t === 'product' ? 'katalog' : reg} </span>}
                    <Link url={x.url} /> {x.accessed_date && <span className="num">· {x.accessed_date}</span>}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )
      })}
    </details>
  )
}

// Shown when the answer carried no readable block. Never fakes a card.
export function PlainAnswer({ text, note }: { text: string; note?: string }) {
  return (
    <article className="rcard plain-answer">
      <header>
        <b>Jawaban agen (teks)</b>
        {note && <span className="pill warn">{note}</span>}
      </header>
      <div className="rbody md">{text ? <Markdown remarkPlugins={[remarkGfm]}>{text}</Markdown> : <p className="quiet">Jawaban kosong.</p>}</div>
    </article>
  )
}

// The agent's ordinary text next to its cards (block already removed).
export function AnswerDetails({ text }: { text: string }) {
  return text ? (
    <details className="md-ans">
      <summary>Jawaban teks agen</summary>
      <div className="md">
        <Markdown remarkPlugins={[remarkGfm]}>{text}</Markdown>
      </div>
    </details>
  ) : null
}
