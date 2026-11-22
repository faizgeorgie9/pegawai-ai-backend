import { Children, Fragment, createContext, createElement, isValidElement, useContext, useMemo } from 'react'
import type { ReactNode } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Bot } from './bff'
import { botColor, nf } from './ui'
import { CopyButton } from './ui-extra'

// The shared renderer for agent text (chat, group chat). On top of Markdown it understands, generically from the text:
//  - fenced code and box-drawing wireframes (monospace block, scrolls inside, copy button),
//  - @handle mentions of the group's members (agent chips),
//  - Bimo's "[DISPATCH TASK-02] -> @agent" and "[BIMO REJECTION - ...]" lines (compact callout),
//  - product references (`products_referenced`, or /products/search rows) in a json block (product cards).
// Nothing here knows an agent by name: members are matched by name, id or role words.

export const MentionsCtx = createContext<Bot[]>([])

// ---------- mentions ----------
const squash = (s: string) => s.toLowerCase().replace(/[^\p{L}\p{N}]/gu, '')
// "marketingstrategist" matches the role "Marketing & Fashion Strategist": the handle is made of the role's words in order.
const roleMatch = (role: string, h: string) => {
  let pos = 0
  for (const w of role.toLowerCase().split(/[^\p{L}\p{N}]+/u).filter(Boolean)) if (h.startsWith(w, pos)) pos += w.length
  return pos === h.length
}
export function botFor(handle: string, bots: Bot[]): Bot | undefined {
  const h = squash(handle)
  if (!h) return undefined
  return bots.find((b) => squash(b.name) === h || squash(b.id) === h) ?? (h.length >= 4 ? bots.find((b) => roleMatch(b.role, h)) : undefined)
}

const MENTION = /(^|[^\p{L}\p{N}_@])@([\p{L}\p{N}_]+)/gu
export function mentionize(node: ReactNode, bots: Bot[]): ReactNode {
  if (typeof node === 'string') {
    if (!bots.length || !node.includes('@')) return node
    const out: ReactNode[] = []
    let last = 0
    for (const m of node.matchAll(MENTION)) {
      const bot = botFor(m[2], bots)
      if (!bot) continue
      const at = m.index + m[1].length
      if (at > last) out.push(node.slice(last, at))
      out.push(
        <span key={at} className="mention-chip" style={{ ['--bot' as string]: botColor(bot) }} title={`@${m[2]}`}>
          {bot.name}
        </span>,
      )
      last = at + m[2].length + 1
    }
    if (!out.length) return node
    if (last < node.length) out.push(node.slice(last))
    return out
  }
  if (Array.isArray(node)) return node.map((n, i) => (typeof n === 'string' ? <Fragment key={i}>{mentionize(n, bots)}</Fragment> : n))
  return node
}

// ---------- products ----------
export interface ProductRef { name: string; price?: number; original?: number; discount?: number; color: string; url: string; image: string }
const isObj = (x: unknown): x is Record<string, unknown> => typeof x === 'object' && x !== null && !Array.isArray(x)
const num = (x: unknown) => (typeof x === 'number' && Number.isFinite(x) ? x : typeof x === 'string' && /\d/.test(x) ? Number(x.replace(/\D/g, '')) : undefined)
const web = (x: unknown) => (typeof x === 'string' && /^https?:\/\//i.test(x.trim()) ? x.trim() : '')
// Bundled BFF photos come as /api/product-images/<file>; the browser reaches the BFF under /bff.
const photo = (x: unknown) => (typeof x === 'string' && /^\/api\/product-images\/[\w.-]+$/.test(x.trim()) ? `/bff${x.trim()}` : web(x))

// Accepts the handoff contract (price, original_price, discount_percent, color, url) and our /products/search rows (price_original, colors[]).
export function toProducts(x: unknown): ProductRef[] {
  const list = Array.isArray(x) ? x : []
  return list.filter(isObj).flatMap((o) => {
    const name = typeof o.name === 'string' ? o.name.trim() : ''
    if (!name) return []
    const price = num(o.price)
    const original = num(o.original_price ?? o.price_original)
    const discount = num(o.discount_percent) ?? (price && original && original > price ? Math.round((1 - price / original) * 100) : undefined)
    const color = typeof o.color === 'string' ? o.color : Array.isArray(o.colors) ? o.colors.filter((c) => typeof c === 'string').join(', ') : ''
    // Images only from a URL the data carries; nothing is fetched or guessed.
    return [{ name, price, original: original && price && original > price ? original : undefined, discount: discount && discount > 0 ? discount : undefined, color, url: web(o.url), image: photo(o.image_url ?? o.image) }]
  })
}

function productsFrom(body: string): ProductRef[] | null {
  let j: unknown
  try {
    j = JSON.parse(body)
  } catch {
    return null
  }
  const items = toProducts(isObj(j) ? j.products_referenced : j)
  return items.length ? items : null
}

const rp = (n: number) => `Rp ${nf.format(n)}`

export function ProductCards({ items }: { items: ProductRef[] }) {
  return (
    <ul className="pcards" aria-label="Produk yang disebut">
      {items.map((p, i) => (
        <li key={i} className="pcard">
          {p.image && <img src={p.image} alt="" loading="lazy" referrerPolicy="no-referrer" onError={(e) => { e.currentTarget.hidden = true }} />}
          <div className="pcard-main">
            <b className="pcard-name">{p.name}</b>
            {p.color && <span className="quiet small">Warna: {p.color}</span>}
            <span className="pcard-price num">
              {p.price !== undefined ? <strong>{rp(p.price)}</strong> : <span className="quiet">Harga tidak tersedia</span>}
              {p.original !== undefined && <s className="quiet">{rp(p.original)}</s>}
              {p.discount !== undefined && <span className="pill ok">-{p.discount}%</span>}
            </span>
            {p.url && (
              <a className="pcard-link" href={p.url} target="_blank" rel="noopener noreferrer">
                Lihat produk
              </a>
            )}
          </div>
        </li>
      ))}
    </ul>
  )
}

// ---------- segments ----------
type Call = { k: 'call'; kind: 'dispatch' | 'reject'; tag: string; head: string; body: string }
type Seg = { k: 'md'; text: string } | Call | { k: 'products'; items: ProductRef[] }

const BOX = /[─-╿▀-▟]/
const CALL = /^\s*[^\p{L}\p{N}[@]*\[(DISPATCH[^\]]*|BIMO REJECTION[^\]]*)\]\s*(?:->|-->|→)?\s*(.*)$/u
const FENCE = /^\s*(```+|~~~+)\s*([\w-]*)/
const sentence = (s: string) => (s === s.toUpperCase() ? s.charAt(0) + s.slice(1).toLowerCase() : s)

function callOf(m: RegExpExecArray, body: string): Call {
  const label = m[1]
  if (/^DISPATCH/i.test(label)) {
    const id = /TASK-?\s*(\w+)/i.exec(label)?.[1]
    return { k: 'call', kind: 'dispatch', tag: id ? `Tugas ${id}` : 'Tugas', head: m[2].startsWith('@') ? `Dikirim ke ${m[2]}` : m[2], body }
  }
  const reason = label.replace(/^BIMO REJECTION\s*[-:–]?\s*/i, '').trim()
  return { k: 'call', kind: 'reject', tag: 'Ditolak', head: [reason && sentence(reason), m[2]].filter(Boolean).join('. '), body }
}

export function segments(text: string): Seg[] {
  const t = text.trim()
  if (t.startsWith('{')) {
    // A whole backend payload: its markdown plus the products it references.
    try {
      const j: unknown = JSON.parse(t)
      const items = isObj(j) ? toProducts(j.products_referenced) : []
      if (isObj(j) && items.length) return [...(typeof j.output_markdown === 'string' ? segments(j.output_markdown) : []), { k: 'products', items }]
    } catch {
      /* ordinary text */
    }
  }
  const lines = text.split('\n')
  const out: Seg[] = []
  let md: string[] = []
  const flush = () => {
    if (md.join('\n').trim()) out.push({ k: 'md', text: md.join('\n') })
    md = []
  }
  for (let i = 0; i < lines.length; ) {
    const line = lines[i]
    const f = FENCE.exec(line)
    if (f) {
      let j = i + 1
      while (j < lines.length && !lines[j].trim().startsWith(f[1])) j++
      const closed = j < lines.length // streaming: an open fence runs to the end
      const items = closed && /^(json)?$/i.test(f[2]) ? productsFrom(lines.slice(i + 1, j).join('\n')) : null
      if (items) {
        flush()
        out.push({ k: 'products', items })
      } else md.push(...lines.slice(i, closed ? j + 1 : j))
      i = j + 1
      continue
    }
    const c = CALL.exec(line)
    if (c) {
      flush()
      let j = i + 1
      while (j < lines.length && lines[j].trim() && !CALL.test(lines[j]) && !FENCE.test(lines[j])) j++
      out.push(callOf(c, lines.slice(i + 1, j).join('\n')))
      i = j
      continue
    }
    if (BOX.test(line)) {
      // box-drawing lines outside a fence: wrap a run of 3+ so the characters line up
      let j = i
      while (j < lines.length && BOX.test(lines[j])) j++
      if (j - i >= 3) md.push('', '```', ...lines.slice(i, j), '```', '')
      else md.push(...lines.slice(i, j))
      i = j
      continue
    }
    md.push(line)
    i++
  }
  flush()
  return out
}

// ---------- markdown components ----------
const textOf = (n: ReactNode): string => (typeof n === 'string' ? n : Array.isArray(n) ? n.map(textOf).join('') : isValidElement<{ children?: ReactNode }>(n) ? textOf(n.props.children) : '')

// Fenced code: monospace, never wraps, scrolls inside the block only. Box-drawing content is labelled as a wireframe.
function Pre({ children }: { children?: ReactNode }) {
  const el = Children.toArray(children)[0]
  const code = isValidElement<{ className?: string; children?: ReactNode }>(el) ? el : null
  const text = textOf(code?.props.children).replace(/\n$/, '')
  const lang = /language-([\w-]+)/.exec(code?.props.className ?? '')?.[1]
  const wire = BOX.test(text)
  return (
    <div className="codeblock" data-wire={wire || undefined}>
      <div className="codeblock-bar">
        <span>{wire ? 'Wireframe' : lang && lang !== 'text' ? lang : 'Teks'}</span>
        <CopyButton text={text} what={wire ? 'wireframe' : 'blok teks'} />
      </div>
      <pre tabIndex={0} aria-label={wire ? 'Wireframe, bisa digeser ke samping' : 'Blok teks, bisa digeser ke samping'}>
        <code>{text}</code>
      </pre>
    </div>
  )
}

const withMentions = (tag: string) =>
  function Wrapped({ children }: { children?: ReactNode }) {
    return createElement(tag, null, mentionize(children, useContext(MentionsCtx)))
  }

const mdComponents = {
  a: ({ href, children }: { href?: string; children?: ReactNode }) => (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  ),
  img: () => null, // no remote images from model output
  pre: Pre,
  ...Object.fromEntries(['p', 'li', 'td', 'th', 'strong', 'em', 'h1', 'h2', 'h3', 'h4'].map((t) => [t, withMentions(t)])),
}

function Callout({ s }: { s: Call }) {
  const bots = useContext(MentionsCtx)
  return (
    <aside className="callout" data-k={s.kind}>
      <p className="callout-head">
        <span className="callout-tag">{s.tag}</span>
        <span>{mentionize(s.head, bots)}</span>
      </p>
      {s.body.trim() && (
        <div className="callout-body">
          <Markdown remarkPlugins={[remarkGfm]} components={mdComponents}>
            {s.body}
          </Markdown>
        </div>
      )}
    </aside>
  )
}

export function Md({ text, caret }: { text: string; caret?: boolean }) {
  const segs = useMemo(() => segments(text), [text])
  return (
    <div className="md" data-caret={caret || undefined}>
      {segs.map((s, i) =>
        s.k === 'md' ? (
          <Markdown key={i} remarkPlugins={[remarkGfm]} components={mdComponents}>
            {s.text}
          </Markdown>
        ) : s.k === 'call' ? (
          <Callout key={i} s={s} />
        ) : (
          <ProductCards key={i} items={s.items} />
        ),
      )}
    </div>
  )
}
