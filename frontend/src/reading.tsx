// Turns an agent's plain-text output into a reading layout. Display only: no word is changed.
// - ALL_CAPS_KEY: lines become headings, "KEY: value" lines become key-value rows
// - hard-wrapped lines are joined; intentional short lines and lines after a full stop keep their break
// - "1." / "-" lines become lists, #RRGGBB codes get a small swatch
// - a leading process note ("Konteks sudah saya baca...") is moved into a collapsed block, not removed
import type { ReactNode } from 'react'
import type { Agent } from './api'

type Block =
  | { t: 'h'; text: string }
  | { t: 'kv'; k: string; v: string }
  | { t: 'p'; text: string }
  | { t: 'list'; ordered: boolean; start: number; items: string[] }

const HEAD = /^[A-Z][A-Z0-9_]{2,}:$/
const KV = /^([A-Z][A-Z0-9_]{2,}):\s+(.+)$/
const LI = /^(\s*)(?:(\d+)[.)]|[-•*])\s+(.*)$/
const NOTE = /^(Konteks sudah saya baca|Tanggal acuan|Catatan proses)/i
const ACRONYM = /\b(qc|qa|aida|sop|cs|ai)\b/gi

export function humanize(key: string): string {
  const s = key.toLowerCase().replace(/_/g, ' ').replace(ACRONYM, (m) => m.toUpperCase())
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function keepBreak(prev: string, next: string): boolean {
  const p = prev.trim()
  return /[.!?:]$/.test(p) || p.length < 50 || /^[\p{L}][\p{L} ]{0,18}:\s/u.test(next)
}
function joinLines(lines: string[]): string {
  return lines.reduce((acc, line, i) => (i === 0 ? line : acc + (keepBreak(lines[i - 1], line) ? '\n' : ' ') + line), '')
}

export function parse(content: string): { note?: string; blocks: Block[] } {
  const blocks: Block[] = []
  let para: string[] = []
  let list: { ordered: boolean; start: number; items: string[] } | null = null
  const flushPara = () => {
    if (para.length) blocks.push({ t: 'p', text: joinLines(para) })
    para = []
  }
  const flushList = () => {
    if (list) blocks.push({ t: 'list', ...list })
    list = null
  }
  for (const raw of content.split('\n')) {
    const line = raw.replace(/\s+$/, '')
    if (!line.trim()) {
      flushPara()
      flushList()
      continue
    }
    const t = line.trim()
    const li = LI.exec(line)
    if (HEAD.test(t)) {
      flushPara()
      flushList()
      blocks.push({ t: 'h', text: humanize(t.slice(0, -1)) })
    } else if (KV.test(t)) {
      flushPara()
      flushList()
      const m = KV.exec(t)!
      blocks.push({ t: 'kv', k: humanize(m[1]), v: m[2] })
    } else if (li) {
      flushPara()
      const ordered = li[2] !== undefined
      if (!list || list.ordered !== ordered) {
        flushList()
        list = { ordered, start: ordered ? Number(li[2]) : 1, items: [] }
      }
      list.items.push(li[3])
    } else if (list && /^\s+/.test(line)) {
      list.items[list.items.length - 1] += ' ' + t
    } else {
      flushList()
      para.push(t)
    }
  }
  flushPara()
  flushList()
  let note: string | undefined
  if (blocks.length > 1 && blocks[0].t === 'p' && NOTE.test(blocks[0].text)) {
    note = blocks[0].text
    blocks.shift()
  }
  return { note, blocks }
}

const HEX = /(#[0-9A-Fa-f]{6})(?![0-9A-Za-z])/g
function Inline({ text }: { text: string }) {
  const parts: ReactNode[] = []
  let last = 0
  for (const m of text.matchAll(HEX)) {
    const at = m.index!
    parts.push(text.slice(last, at))
    parts.push(
      <span key={at} className="sw" style={{ background: m[1] }} role="img" aria-label={`warna ${m[1]}`} />,
      m[1],
    )
    last = at + m[0].length
  }
  parts.push(text.slice(last))
  return <>{parts}</>
}

export function Prose({ agent }: { agent: Agent }) {
  const { note, blocks } = parse(agent.content)
  return (
    <div className="prose">
      {note && (
        <details className="note">
          <summary>Catatan proses dari {agent.name}</summary>
          <p>{note}</p>
        </details>
      )}
      {blocks.map((b, i) => {
        switch (b.t) {
          case 'h':
            return <h3 key={i}>{b.text}</h3>
          case 'kv':
            return (
              <p key={i} className="kv">
                <span>{b.k}</span>
                <b>{/^[A-Z0-9_]+$/.test(b.v) ? humanize(b.v) : <Inline text={b.v} />}</b>
              </p>
            )
          case 'p':
            return (
              <p key={i}>
                <Inline text={b.text} />
              </p>
            )
          case 'list': {
            const Tag = b.ordered ? 'ol' : 'ul'
            return (
              <Tag key={i} start={b.ordered ? b.start : undefined}>
                {b.items.map((it, j) => (
                  <li key={j}>
                    <Inline text={it} />
                  </li>
                ))}
              </Tag>
            )
          }
        }
      })}
    </div>
  )
}

// The auditor's list of suggested fixes (the list under a SARAN / PERBAIKAN / REVISI heading), and which of them
// are marked WAJIB (a revision a human must apply before the draft is used).
export interface Advice {
  by: string
  index: number
  heading: string
  items: string[]
  required: string[]
}
export function findAdvice(agents: Agent[]): Advice | undefined {
  for (const [index, a] of agents.entries()) {
    const blocks = parse(a.content).blocks
    const h = blocks.findIndex((b) => b.t === 'h' && /saran|perbaikan|revisi/i.test(b.text))
    const list = h >= 0 ? blocks.slice(h + 1).find((b) => b.t === 'list') : undefined
    if (h >= 0 && list && list.t === 'list') {
      const heading = (blocks[h] as { text: string }).text
      return { by: a.name, index, heading, items: list.items, required: list.items.filter((it) => /^WAJIB\b/i.test(it)) }
    }
  }
  return undefined
}

// The scorer's own reason for the score ("Alasan skor: ..."), when the output has one.
export function findWhy(agent: Agent | undefined): string | undefined {
  if (!agent) return undefined
  for (const b of parse(agent.content).blocks)
    if (b.t === 'p' && /^Alasan skor:/i.test(b.text)) return b.text.replace(/^Alasan skor:\s*(.)/i, (_m, c: string) => c.toUpperCase())
  return undefined
}

export type Tone = 'ok' | 'watch' | 'alert' | 'neutral'
export interface Escalation {
  label: string
  tone: Tone
  reason?: string
  items: string[]
  by: string
}

// STATUS_ESKALASI: VALUE inside an agent's content (Hendra's, in Customer Service), plus the sentence after it.
export function findEscalation(agents: Agent[]): Escalation | undefined {
  for (const a of [...agents].reverse()) {
    const m = /^[ \t]*STATUS_ESKALASI:[ \t]*([A-Z0-9_]+)/m.exec(a.content)
    if (!m) continue
    const code = m[1]
    const rest = a.content.slice((m.index ?? 0) + m[0].length).split('\n').slice(1)
    const lines: string[] = []
    const items: string[] = []
    for (const l of rest) {
      if (!l.trim()) {
        if (lines.length || items.length) break
        continue
      }
      const li = LI.exec(l)
      if (li) items.push(li[3])
      else if (items.length && /^\s+/.test(l)) items[items.length - 1] += ' ' + l.trim()
      else if (items.length) break
      else lines.push(l.trim())
    }
    const tone: Tone = /^(TIDAK|AMAN|NORMAL|SELESAI)/.test(code)
      ? 'ok'
      : /MANAJEMEN|KRITIS|SEGERA|PERLU/.test(code)
        ? 'alert'
        : /MONITORING|PANTAU/.test(code)
          ? 'watch'
          : 'neutral'
    return { label: humanize(code), tone, reason: lines.length ? joinLines(lines) : undefined, items, by: a.name }
  }
  return undefined
}
