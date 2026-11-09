import type { ReactNode } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { CLS_LABEL, RUBRIC } from './results'
import type { Cls, CsResult, MarketingResult } from './results'

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
          {origin === 'sample' ? <span className="pill sample">Contoh data</span> : <span className="pill origin">Hasil agen · belum divalidasi backend</span>}
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
