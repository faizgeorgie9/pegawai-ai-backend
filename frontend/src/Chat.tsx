import { useEffect, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ApiError, api, asStr, errText, isAbort, newKey, subscribe, usageOf } from './bff'
import type { Bot, ChatMessage, Raw, Session, SseState, ToolChip } from './bff'
import { useData } from './data'
import { go, botPath } from './router'
import { PanelButtons, SidePanel, Split } from './Panel'
import { BotAvatar, CLOSE, Icon, ThinkingBlock, nf } from './ui'

const THINK_KEY = 'pegawai.showThinking'
function readThink(): boolean {
  try {
    return localStorage.getItem(THINK_KEY) === '1'
  } catch {
    return false
  }
}

const isEnd = (ev: string) => /complet|finish|done|end|result|error|fail/.test(ev)
function applyTool(tools: ToolChip[], d: Raw): ToolChip[] {
  const tool = asStr(d.tool, 'tool')
  const ev = asStr(d.event).toLowerCase()
  const bad = Boolean(d.error) || /error|fail/.test(ev)
  const preview = asStr(d.preview) || undefined
  if (!isEnd(ev)) return [...tools, { id: newKey('t'), tool, preview, status: 'run' }]
  const i = tools.map((t) => t.tool === tool && t.status === 'run').lastIndexOf(true)
  const status = bad ? 'bad' : 'done'
  if (i < 0) return [...tools, { id: newKey('t'), tool, preview, status }]
  return tools.map((t, n) => (n === i ? { ...t, status, preview: preview ?? t.preview } : t))
}
const toolsFrom = (x: unknown): ToolChip[] | undefined =>
  Array.isArray(x)
    ? (x as Raw[])
        .filter((r) => !r.type || String(r.type).startsWith('tool.')) // stored rows: {type, payload}; live ones are already flat
        .reduce<ToolChip[]>((acc, r) => applyTool(acc, r.type ? { ...(r.payload as Raw), event: r.type } : r), [])
    : undefined

type Problem = { text: string; upgrade?: boolean } | null

export default function Chat({ bot, sid, sessions, onSessions }: { bot: Bot; sid?: string; sessions: Session[]; onSessions: () => void }) {
  const [pv, setPv] = useState(0) // bumped whenever the side panel's data may have changed
  const bump = () => setPv((n) => n + 1)
  const { setDialog, askNotify, refreshMe, viewing } = useData()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [run, setRun] = useState<{ id: string } | null>(null) // id '' while the POST is in flight
  const [conn, setConn] = useState<SseState>('open')
  const [queue, setQueue] = useState<string[]>([])
  const [problem, setProblem] = useState<Problem>(null)
  const [draft, setDraft] = useState('')
  const [showThink, setShowThink] = useState(readThink)
  const sidRef = useRef(sid)
  const ownSid = useRef<string | undefined>(undefined) // a session this view created itself: already on screen, do not reload
  const live = useRef('') // key of the assistant message being filled
  const unstream = useRef<(() => void) | null>(null)
  const epoch = useRef(0)
  const scroller = useRef<HTMLDivElement>(null)
  const stick = useRef(true)
  const box = useRef<HTMLTextAreaElement>(null)
  const active = sessions.find((s) => s.id === sid)

  useEffect(() => {
    viewing(botPath(bot.id, sid))
    return () => viewing('')
  }, [bot.id, sid, viewing])

  const edit = (key: string, fn: (m: ChatMessage) => ChatMessage) => setMessages((cur) => cur.map((m) => (m.key === key ? fn(m) : m)))

  // Durations come from /thinking; a message only gets one when its reasoning text matches exactly one run.
  function loadTimes(forSid: string | undefined) {
    if (!forSid) return
    api.thinking({ session_id: forSid }).then(
      (t) => {
        if (sidRef.current !== forSid) return
        const seen = new Map<string, number | undefined>()
        const dup = new Set<string>()
        for (const x of t) {
          const k = x.reasoning.trim()
          if (!k) continue
          if (seen.has(k)) dup.add(k)
          seen.set(k, x.seconds)
        }
        setMessages((cur) =>
          cur.map((m) => {
            const k = m.reasoning.trim()
            const sec = m.role === 'assistant' && k && !dup.has(k) ? seen.get(k) : undefined
            return sec === undefined || sec === m.seconds ? m : { ...m, seconds: sec }
          }),
        )
      },
      () => {}, // optional: the block falls back to "Proses berpikir"
    )
  }

  function attach(runId: string, key: string) {
    live.current = key
    const finish = () => {
      unstream.current?.()
      unstream.current = null
      setRun(null)
      setConn('open')
      refreshMe()
      bump()
      onSessions()
      loadTimes(sidRef.current)
      window.setTimeout(onSessions, 6000) // Hermes names the topic a few seconds later
    }
    const stop = subscribe(
      `/runs/${encodeURIComponent(runId)}/stream`,
      {
        snapshot: (d) =>
          edit(key, (m) => ({
            ...m,
            content: asStr(d.output) || m.content,
            reasoning: asStr(d.reasoning) || m.reasoning,
            tools: toolsFrom(d.tools ?? d.tool_events ?? d.events) ?? m.tools,
          })),
        delta: (d) => edit(key, (m) => ({ ...m, content: m.content + asStr(d.text), approval: undefined })),
        reasoning: (d) => {
          const t = asStr(d.text)
          if (t) edit(key, (m) => ({ ...m, reasoning: m.reasoning ? m.reasoning + '\n\n' + t : t }))
          bump()
        },
        tool: (d) => edit(key, (m) => ({ ...m, tools: applyTool(m.tools, d) })),
        approval: (d) =>
          edit(key, (m) => ({
            ...m,
            approval: { request_id: asStr(d.request_id), description: asStr(d.description), choices: Array.isArray(d.choices) ? d.choices.map((c: unknown) => asStr(c)) : [] },
          })),
        done: (d) => {
          const status = asStr(d.status).toLowerCase()
          const usage = d.usage ? usageOf(d.usage) : undefined
          edit(key, (m) => ({
            ...m,
            content: asStr(d.output) || m.content,
            reasoning: asStr(d.reasoning) || m.reasoning,
            tokens: usage,
            approval: undefined,
            tools: m.tools.map((t) => (t.status === 'run' ? { ...t, status: 'done' } : t)),
            stopped: /stop|cancel|interrupt/.test(status) || undefined,
            error: /fail|error/.test(status) ? asStr(d.error) || 'Bot belum berhasil menyelesaikan tugas ini.' : undefined,
          }))
          finish()
        },
      },
      setConn,
    )
    unstream.current = stop
  }

  async function startRun(text: string) {
    setRun({ id: '' })
    setProblem(null)
    stick.current = true
    const u: ChatMessage = { key: newKey('u'), role: 'user', content: text, reasoning: '', tools: [] }
    const a: ChatMessage = { key: newKey('a'), role: 'assistant', content: '', reasoning: '', tools: [] }
    setMessages((cur) => [...cur, u, a])
    try {
      const r = await api.startRun(bot.id, text, sidRef.current)
      if (!sidRef.current && r.session_id) {
        sidRef.current = r.session_id
        ownSid.current = r.session_id
        go(botPath(bot.id, r.session_id), true)
      }
      setRun({ id: r.run.id })
      bump()
      onSessions()
      attach(r.run.id, a.key)
    } catch (e) {
      setRun(null)
      setMessages((cur) => cur.filter((m) => m.key !== u.key && m.key !== a.key))
      setProblem({ text: errText(e), upgrade: e instanceof ApiError && e.upgrade })
      setDraft((d) => d || text)
    }
  }

  // The route's session changed (or first mount): load it, and reattach to a run that is still going.
  useEffect(() => {
    if (sid && sid === ownSid.current) return
    ownSid.current = undefined
    sidRef.current = sid
    const mine = ++epoch.current
    unstream.current?.()
    unstream.current = null
    setRun(null)
    setConn('open')
    setQueue([])
    setMessages([])
    setProblem(null)
    setLoading(!!sid)
    stick.current = true
    if (!sid) return
    void (async () => {
      try {
        const msgs = await api.messages(bot.id, sid)
        if (mine !== epoch.current) return
        const active = await api.runs('active').catch(() => [])
        if (mine !== epoch.current) return
        const r = active.find((x) => x.bot_id === bot.id && x.session_id === sid && x.kind !== 'group')
        if (r) {
          const lastUser = [...msgs].reverse().find((m) => m.role === 'user')
          const a: ChatMessage = { key: newKey('a'), role: 'assistant', content: '', reasoning: '', tools: [] }
          const extra: ChatMessage[] = []
          if (r.input && lastUser?.content.trim() !== r.input.trim()) extra.push({ key: newKey('u'), role: 'user', content: r.input, reasoning: '', tools: [] })
          setMessages([...msgs, ...extra, a])
          setRun({ id: r.id })
          attach(r.id, a.key)
        } else setMessages(msgs)
        loadTimes(sid)
      } catch (e) {
        if (mine === epoch.current && !isAbort(e)) setProblem({ text: errText(e) })
      } finally {
        if (mine === epoch.current) setLoading(false)
      }
    })()
    // attach/onSessions are stable enough for this effect: it must only re-run when the session changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sid, bot.id])
  useEffect(() => () => unstream.current?.(), [])

  // Queued messages go out one at a time as soon as the run ends.
  useEffect(() => {
    if (!run && queue.length) {
      const [next, ...rest] = queue
      setQueue(rest)
      void startRun(next)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run, queue])

  useEffect(() => {
    const el = scroller.current
    if (el && stick.current) el.scrollTop = el.scrollHeight
  }, [messages, queue])
  useEffect(() => {
    const el = box.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 200) + 'px'
  }, [draft])

  function toggleThink() {
    const v = !showThink
    setShowThink(v)
    try {
      localStorage.setItem(THINK_KEY, v ? '1' : '0')
    } catch {
      /* private mode: the toggle still works for this visit */
    }
  }

  function send() {
    const text = draft.trim()
    if (!text) return
    setDraft('')
    askNotify()
    if (run) setQueue((q) => [...q, text])
    else void startRun(text)
  }

  async function steer() {
    const text = draft.trim()
    if (!text || !run) return
    setDraft('')
    if (!run.id) return setQueue((q) => [...q, text])
    try {
      await api.steerRun(run.id, text)
      edit(live.current, (m) => ({ ...m, notes: [...(m.notes ?? []), text] }))
    } catch (e) {
      // 409: the bot already finished, so the message goes out as a new one.
      if (e instanceof ApiError && e.status === 409) setQueue((q) => [...q, text])
      else {
        setProblem({ text: errText(e) })
        setDraft(text)
      }
    }
  }

  async function stopRun() {
    if (!run?.id) return
    try {
      await api.stopRun(run.id)
    } catch (e) {
      setProblem({ text: errText(e) })
    }
  }

  async function approve(m: ChatMessage, deny: boolean) {
    const a = m.approval
    if (!a || !run?.id) return
    const choice = deny
      ? (a.choices.find((c) => /deny|tolak|reject|no/i.test(c)) ?? 'deny')
      : (a.choices.find((c) => /once|allow|izin|approve|yes/i.test(c)) ?? a.choices[0] ?? 'once')
    edit(m.key, (x) => ({ ...x, approval: undefined }))
    try {
      await api.approve(run.id, choice)
    } catch (e) {
      edit(m.key, (x) => ({ ...x, approval: a }))
      setProblem({ text: errText(e) })
    }
  }

  const running = !!run

  return (
    <Split panel={<SidePanel scope={sid ? { session_id: sid } : null} version={pv} bot={bot} />}>
    <section className="convo" aria-label={`Percakapan dengan ${bot.name}`}>
      <header className="convo-head">
        <BotAvatar bot={bot} size={36} />
        <div className="convo-title">
          <h1>{bot.name}</h1>
          <p>
            {bot.role}
            {active?.model && active.messageCount !== -1 ? ` · ${active.model}` : ''}
          </p>
        </div>
        <button className="switch" role="switch" aria-checked={showThink} onClick={toggleThink}>
          <span className="knob" aria-hidden="true" />
          Proses berpikir
        </button>
        <PanelButtons />
      </header>

      <div
        className="scroll"
        ref={scroller}
        onScroll={(e) => {
          const el = e.currentTarget
          stick.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80
        }}
      >
        <div className="thread" aria-live="polite" aria-busy={running}>
          {loading && <p className="quiet center">Memuat percakapan...</p>}
          {!loading && messages.length === 0 && (
            <div className="empty">
              <BotAvatar bot={bot} size={56} />
              <h2>{sid && !problem ? 'Percakapan kosong' : `Mulai topik baru dengan ${bot.name}`}</h2>
              <p>
                {bot.role}. Tulis pesan di bawah; {bot.name} melanjutkan topik yang sama sampai Anda memilih Topik baru.
              </p>
            </div>
          )}
          {messages.map((m, i) => (
            <Message
              key={m.key}
              m={m}
              bot={bot}
              model={active?.model}
              showThink={showThink}
              live={running && i === messages.length - 1 && m.role === 'assistant'}
              reconnecting={conn === 'retry' && running && i === messages.length - 1}
              onApprove={(deny) => void approve(m, deny)}
            />
          ))}
          {queue.map((t, i) => (
            <div key={i} className="msg user pending">
              <p>{t}</p>
              <span className="pending-tag">
                Antre
                <button className="icon-btn tiny" aria-label="Batalkan pesan antre" onClick={() => setQueue((q) => q.filter((_, n) => n !== i))}>
                  <Icon d={CLOSE} size={12} />
                </button>
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="composer-wrap">
        {problem && (
          <p className="problem-bar" role="alert">
            {problem.text}
            {problem.upgrade && (
              <button className="btn link" onClick={() => setDialog({ kind: 'plan' })}>
                Lihat paket
              </button>
            )}
          </p>
        )}
        <form
          className="composer"
          onSubmit={(e) => {
            e.preventDefault()
            send()
          }}
        >
          <label className="sr" htmlFor="msg">
            Pesan untuk {bot.name}
          </label>
          <textarea
            id="msg"
            ref={box}
            rows={1}
            value={draft}
            placeholder={running ? `Bot sedang bekerja. Pesan baru masuk antrean.` : `Tulis pesan untuk ${bot.name}`}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault()
                send()
              }
            }}
          />
          <div className="composer-actions">
            {running && (
              <>
                <button type="button" className="btn stop" onClick={() => void stopRun()} disabled={!run?.id}>
                  <span className="square" aria-hidden="true" />
                  Berhenti
                </button>
                <button type="button" className="btn soft" onClick={() => void steer()} disabled={!draft.trim()}>
                  Arahkan sekarang
                </button>
              </>
            )}
            <button type="submit" className="btn primary" disabled={!draft.trim()}>
              {running ? 'Antre' : 'Kirim'}
            </button>
          </div>
        </form>
        <p className="composer-note">Enter untuk kirim, Shift+Enter untuk baris baru.</p>
      </div>
    </section>
    </Split>
  )
}

const mdComponents = {
  a: ({ href, children }: { href?: string; children?: React.ReactNode }) => (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  ),
  img: () => null, // no remote images from model output
}

export function Md({ text }: { text: string }) {
  return (
    <div className="md">
      <Markdown remarkPlugins={[remarkGfm]} components={mdComponents}>
        {text}
      </Markdown>
    </div>
  )
}

function Message(p: {
  m: ChatMessage
  bot: Bot
  model?: string
  showThink: boolean
  live: boolean
  reconnecting: boolean
  onApprove: (deny: boolean) => void
}) {
  const { m, bot, live } = p
  if (m.role === 'user') {
    return (
      <div className="msg user">
        <p>{m.content}</p>
      </div>
    )
  }
  const waiting = live && !m.content && !m.approval
  return (
    <div className="msg bot">
      <BotAvatar bot={bot} size={28} />
      <div className="msg-body">
        {m.tools.length > 0 && (
          <ul className="chips" aria-label="Aktivitas">
            {m.tools.map((t) => (
              <li key={t.id} className="chip" data-status={t.status} title={t.preview}>
                <span className="dot" aria-hidden="true" />
                {t.tool}
              </li>
            ))}
          </ul>
        )}
        <ThinkingBlock text={m.reasoning} running={waiting && !m.tools.length} seconds={m.seconds} defaultOpen={p.showThink} />
        {m.content ? (
          <Md text={m.content} />
        ) : waiting && m.tools.length > 0 ? (
          <p className="quiet working">
            <span className="dots" aria-hidden="true" />
            Bot sedang bekerja…
          </p>
        ) : null}
        {m.approval && (
          <div className="approval" role="group" aria-label="Butuh izin">
            <p className="approval-title">Bot meminta izin</p>
            <p>{m.approval.description || 'Bot ingin menjalankan satu tindakan.'}</p>
            <div className="approval-actions">
              <button className="btn primary" onClick={() => p.onApprove(false)}>
                Izinkan sekali
              </button>
              <button className="btn soft" onClick={() => p.onApprove(true)}>
                Tolak
              </button>
            </div>
          </div>
        )}
        {m.notes?.map((n, i) => (
          <p key={i} className="meta">
            Anda mengarahkan: {n}
          </p>
        ))}
        {p.reconnecting && <p className="meta reconnect">Menyambung ulang…</p>}
        {m.error && (
          <p className="meta bad" role="alert">
            {m.error}
          </p>
        )}
        {m.stopped && <p className="meta">Dihentikan.</p>}
        {m.tokens && !live && (
          <p className="meta num">
            {[p.model, `${nf.format(m.tokens.input)} masuk, ${nf.format(m.tokens.output)} keluar`].filter(Boolean).join(' · ')}
          </p>
        )}
      </div>
    </div>
  )
}
