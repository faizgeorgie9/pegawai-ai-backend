import { useEffect, useMemo, useRef, useState } from 'react'
import { ApiError, api, asStr, errText, isAbort, newKey, subscribe, toClarify, usageOf } from './bff'
import type { Bot, ChatMessage, Session, SseState } from './bff'
import { ActionCard, useVisibleActions } from './ActionCard'
import { useAdminMode } from './adminMode'
import { useData } from './data'
import { Cs21Card } from './ResultCards'
import { partialReplyDraft, toCs21 } from './results'
import { applyTool, settle, toolsFrom } from './steps'
import { LiveDraft, LiveSteps } from './LiveSteps'
import { useSmoothText } from './useSmoothText'
import { Md } from './rich'
import type { Cs21 } from './results'
import { go, botPath } from './router'
import { GmailDraftButton } from './gmail-ui'
import { KbAttach, KbLines, KbTrayView, asksToSave, useKbTray } from './kb-ui'
import { RUNNING_HINT, RUNNING_PLACEHOLDER, STEER_KEY, STEER_TIP, isSteerKey } from './composerKeys'
import { ClarifyCard, CopyButton, RunProgress, statusText } from './ui-extra'
import { PanelButtons, SidePanel, Split } from './Panel'
import { MakeTaskButton } from './TaskPanel'
import { BotAvatar, CLOSE, Icon, ThinkingBlock, botColor, cleanTaskText, isTaskPrompt, nf, roleLabel } from './ui'

const THINK_KEY = 'pegawai.showThinking'
function readThink(): boolean {
  try {
    return localStorage.getItem(THINK_KEY) === '1'
  } catch {
    return false
  }
}

type Problem = { text: string; upgrade?: boolean } | null

export default function Chat({ bot, sid, sessions, onSessions, onRail, onHistory }: { bot: Bot; sid?: string; sessions: Session[]; onSessions: () => void; onRail: () => void; onHistory: () => void }) {
  const [pv, setPv] = useState(0) // bumped whenever the side panel's data may have changed
  const bump = () => setPv((n) => n + 1)
  const admin = useAdminMode()
  const { setDialog, askNotify, refreshMe, viewing, runs } = useData()
  const attached = useRef('') // last run this view followed, so a run is never attached twice
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [run, setRun] = useState<{ id: string } | null>(null) // id '' while the POST is in flight
  const [conn, setConn] = useState<SseState>('open')
  const [queue, setQueue] = useState<{ text: string; kb: string[] }[]>([])
  const [problem, setProblem] = useState<Problem>(null)
  const [draft, setDraft] = useState('')
  const kb = useKbTray(draft)
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
      () => {}, // optional: the block falls back to "Tampilkan langkah kerja"
    )
  }

  function attach(runId: string, key: string) {
    attached.current = runId
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
            clarify: toClarify(d.clarify) ?? m.clarify,
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
        clarify: (d) => edit(key, (m) => ({ ...m, clarify: toClarify(d) })),
        clarify_done: () => edit(key, (m) => ({ ...m, clarify: undefined })),
        done: (d) => {
          const status = asStr(d.status).toLowerCase()
          const usage = d.usage ? usageOf(d.usage) : undefined
          edit(key, (m) => ({
            ...m,
            clarify: undefined,
            content: asStr(d.output) || m.content,
            reasoning: asStr(d.reasoning) || m.reasoning,
            tokens: usage,
            approval: undefined,
            tools: settle(m.tools),
            stopped: /stop|cancel|interrupt/.test(status) || undefined,
            error: /fail|error/.test(status) ? asStr(d.error) || 'Pegawai belum berhasil menyelesaikan tugas ini.' : undefined,
          }))
          finish()
        },
      },
      setConn,
    )
    unstream.current = stop
  }

  async function startRun(text: string, kbIds: string[] = []) {
    setRun({ id: '' })
    setProblem(null)
    stick.current = true
    const u: ChatMessage = { key: newKey('u'), role: 'user', content: text, reasoning: '', tools: [], kbBusy: asksToSave(text) || undefined }
    const a: ChatMessage = { key: newKey('a'), role: 'assistant', content: '', reasoning: '', tools: [] }
    setMessages((cur) => [...cur, u, a])
    try {
      const r = await api.startRun(bot.id, text, sidRef.current, undefined, undefined, kbIds)
      setMessages((cur) => cur.map((m) => (m.key === u.key ? { ...m, kbBusy: undefined, kb: r.kb } : m)))
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

  // A run that starts in this session while the view is open and idle (the next turn of an evaluation sequence run
  // by the server): reload the messages, so the finished turn shows, and follow the new run live.
  useEffect(() => {
    if (!sid || run || loading) return
    const r = runs.find((x) => x.bot_id === bot.id && x.session_id === sid && x.kind !== 'group') // runs holds only active runs
    if (!r || r.id === attached.current) return
    const mine = epoch.current
    void (async () => {
      const msgs = await api.messages(bot.id, sid).catch(() => null)
      if (!msgs || mine !== epoch.current || attached.current === r.id) return
      const lastUser = [...msgs].reverse().find((m) => m.role === 'user')
      const a: ChatMessage = { key: newKey('a'), role: 'assistant', content: '', reasoning: '', tools: [] }
      const extra: ChatMessage[] = []
      if (r.input && lastUser?.content.trim() !== r.input.trim()) extra.push({ key: newKey('u'), role: 'user', content: r.input, reasoning: '', tools: [] })
      setMessages([...msgs, ...extra, a])
      setRun({ id: r.id })
      stick.current = true
      attach(r.id, a.key)
    })()
    // attach is stable enough here; this must re-run only when the active runs or this view's state change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runs, sid, run, loading, bot.id])

  // Queued messages go out one at a time as soon as the run ends.
  useEffect(() => {
    if (!run && queue.length) {
      const [next, ...rest] = queue
      setQueue(rest)
      void startRun(next.text, next.kb)
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
    const ids = kb.take()
    if (run) setQueue((q) => [...q, { text, kb: ids }])
    else void startRun(text, ids)
  }

  // Sends text to the running agent now. From the composer (no argument) it uses the draft; from a queued chip it uses that chip's text.
  async function steer(queuedAt?: number) {
    const fromQueue = queuedAt !== undefined
    const text = fromQueue ? queue[queuedAt]?.text : draft.trim()
    if (!text || !run) return
    if (fromQueue) setQueue((q) => q.filter((_, n) => n !== queuedAt))
    else setDraft('')
    if (!run.id) return setQueue((q) => [...q, { text, kb: [] }])
    try {
      await api.steerRun(run.id, text)
      edit(live.current, (m) => ({ ...m, notes: [...(m.notes ?? []), text] }))
    } catch (e) {
      // 409: the bot already finished, so the message goes out as a new one.
      if (e instanceof ApiError && e.status === 409) setQueue((q) => [...q, { text, kb: [] }])
      else {
        setProblem({ text: errText(e) })
        if (fromQueue) setQueue((q) => [{ text, kb: [] }, ...q])
        else setDraft(text)
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

  async function answer(m: ChatMessage, text: string) {
    const c = m.clarify
    if (!c || !run?.id) return
    try {
      await api.clarify(run.id, text)
      edit(m.key, (x) => ({ ...x, clarify: undefined }))
    } catch (e) {
      setProblem({ text: errText(e) })
    }
  }

  const running = !!run
  const asked = useVisibleActions((a) => !!sid && a.source?.session_id === sid) // cards for what this agent asked in this chat

  return (
    <Split panel={<SidePanel scope={sid ? { session_id: sid } : null} version={pv} bot={bot} />}>
    <section className="convo" aria-label={`Percakapan dengan ${bot.name}`}>
      <header className="convo-head" style={{ ['--bot' as string]: botColor(bot) }}>
        <button className="btn soft sm rail-open" onClick={onRail}>
          Riwayat
        </button>
        <BotAvatar bot={bot} size={36} />
        <div className="convo-title">
          <h1>{bot.name}</h1>
          <p>
            {roleLabel(bot.role)} · {statusText(bot)}
            {admin && active?.model && active.messageCount !== -1 ? ` · ${active.model}` : ''}
          </p>
        </div>
        <button className="btn soft sm" onClick={() => setDialog({ kind: 'edit', bot })}>
          Atur pegawai
        </button>
        <button className="btn soft sm convo-new" title="Mulai percakapan baru, riwayat lama tetap ada" onClick={() => go(botPath(bot.id))}>
          Topik baru
        </button>
        <button className="switch" role="switch" aria-checked={showThink} onClick={toggleThink}>
          <span className="knob" aria-hidden="true" />
          Tampilkan langkah kerja
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
                {roleLabel(bot.role)}. Tulis pesan di bawah; {bot.name} melanjutkan topik yang sama sampai Anda memilih Topik baru.
              </p>
              {sessions.length > 0 && (
                <p className="quiet small">
                  Ada {sessions.length} topik lain dengan {bot.name}.{' '}
                  <button type="button" className="btn link" onClick={onHistory}>
                    Buka riwayat
                  </button>
                </p>
              )}
              {admin && bot.team === 'marketing' && (
                <a className="empty-link" href="#/marketing">
                  Butuh alur brief → konten? Buka Marketing
                </a>
              )}
              {admin && bot.team === 'customer_support' && (
                <a className="empty-link" href="#/cs">
                  Butuh simulasi pelanggan? Buka Customer Service
                </a>
              )}
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
              onAnswer={(t) => answer(m, t)}
            />
          ))}
          {asked.map((a) => (
            <ActionCard key={a.id} action={a} />
          ))}
        </div>
      </div>

      <div className="composer-wrap">
        {queue.length > 0 && (
          <ul className="queue-rows" aria-label="Pesan menunggu giliran">
            {queue.map((t, i) => (
              <li key={i} className="queue-row">
                <span className="queue-text">{t.text}</span>
                <small>Menunggu giliran</small>
                <button type="button" className="btn link" disabled={!run?.id} onClick={() => void steer(i)} title={STEER_TIP}>
                  Kirim sekarang
                </button>
                <button type="button" className="icon-btn tiny" aria-label="Hapus pesan ini dari antrean" onClick={() => setQueue((q) => q.filter((_, n) => n !== i))}>
                  <Icon d={CLOSE} size={12} />
                </button>
              </li>
            ))}
          </ul>
        )}
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
          <KbTrayView kb={kb} />
          <label className="sr" htmlFor="msg">
            Pesan untuk {bot.name}
          </label>
          <textarea
            id="msg"
            ref={box}
            rows={1}
            value={draft}
            placeholder={running ? RUNNING_PLACEHOLDER : `Tulis pesan untuk ${bot.name}`}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault()
                if (running && isSteerKey(e)) void steer()
                else send()
              }
            }}
          />
          <div className="composer-actions">
            <KbAttach kb={kb} />
            {running && (
              <>
                <button type="button" className="btn stop" onClick={() => void stopRun()} disabled={!run?.id}>
                  <span className="square" aria-hidden="true" />
                  Berhenti
                </button>
                <button type="button" className="btn soft" onClick={() => void steer()} disabled={!draft.trim()} title={STEER_TIP}>
                  Kirim sekarang <kbd>{STEER_KEY}</kbd>
                </button>
              </>
            )}
            <button type="submit" className="btn primary" disabled={!draft.trim()}>
              {running ? <>Kirim setelah selesai <kbd>Enter</kbd></> : 'Kirim'}
            </button>
          </div>
        </form>
        <p className="composer-note">{running ? RUNNING_HINT : 'Enter untuk kirim, Shift+Enter untuk baris baru.'}</p>
      </div>
    </section>
    </Split>
  )
}

const JSON_START = /^\s*(```(?:json)?\s*)?\{/i

// A CS agent answers in JSON (CS v2.1). The chat shows the reply draft; the card with everything else opens from "Lihat detail".
function csFromText(text: string): Cs21 | null {
  const t = text.trim().replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/, '')
  if (!t.startsWith('{')) return null
  try {
    return toCs21(JSON.parse(t))
  } catch {
    return null
  }
}

function Message(p: {
  m: ChatMessage
  bot: Bot
  model?: string
  showThink: boolean
  live: boolean
  reconnecting: boolean
  onApprove: (deny: boolean) => void
  onAnswer: (text: string) => Promise<void>
}) {
  const { m, bot, live } = p
  const admin = useAdminMode() // model names and token counts are admin detail
  const cs = useMemo(() => (m.role === 'assistant' ? csFromText(m.content) : null), [m.role, m.content])
  const draft = useMemo(() => (live && m.role === 'assistant' ? partialReplyDraft(m.content) : null), [live, m.role, m.content]) // CS reply while its JSON is still open
  const sm = useSmoothText(m.content, live && m.role === 'assistant')
  // A task's prompt reaches the BFF with the agent's instruction appended; the owner sees only what they asked.
  const clean = m.role === 'user' ? cleanTaskText(m.content) : m.content
  if (m.role === 'user') {
    return (
      <div className="msg user">
        <p>{clean}</p>
        <KbLines items={m.kb} busy={m.kbBusy} />
        {clean.trim() && !isTaskPrompt(m.content) && (
          <div className="msg-tools user-tools">
            <MakeTaskButton text={clean} bot={bot.id} />
          </div>
        )}
      </div>
    )
  }
  const waiting = live && !m.content && !m.approval && !m.clarify
  return (
    <div className="msg bot" style={{ ['--bot' as string]: botColor(bot) }}>
      <BotAvatar bot={bot} size={28} />
      <div className="msg-body">
        {live && !m.approval && !m.clarify && <RunProgress />}
        <LiveSteps tools={m.tools} running={live && !m.approval && !m.clarify} writing={!!m.content} seconds={m.seconds} />
        <ThinkingBlock text={m.reasoning} running={waiting} seconds={m.seconds} defaultOpen={p.showThink} />
        {cs ? (
          <div className="cs-msg">
            <p className="quiet small">Draf balasan pelanggan · draf internal, perlu tinjauan manusia</p>
            <p className="draft-text">{cs.reply}</p>
            <details className="cs-detail">
              <summary>Lihat detail</summary>
              <Cs21Card r={cs} validation={null} origin="agent" raw={m.content} />
            </details>
          </div>
        ) : draft ? (
          <LiveDraft text={draft} label="Draf balasan · sedang ditulis" />
        ) : live && JSON_START.test(m.content) ? (
          <p className="quiet">Menyusun draf balasan…</p>
        ) : m.content ? (
          <Md text={sm.text} caret={sm.caret} />
        ) : null}
        {!live && (cs?.reply || m.content) && (
          <div className="msg-tools">
            <CopyButton text={cs ? cs.reply : m.content} what={cs ? 'draf balasan' : 'jawaban'} />
            <GmailDraftButton text={cs ? cs.reply : m.content} />
          </div>
        )}
        {m.approval && (
          <div className="approval" role="group" aria-label="Butuh izin">
            <p className="approval-title">Pegawai meminta izin</p>
            <p>{m.approval.description || 'Pegawai ingin menjalankan satu tindakan.'}</p>
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
        {m.clarify && <ClarifyCard key={m.clarify.request_id} c={m.clarify} onAnswer={p.onAnswer} />}
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
        {admin && m.tokens && !live && (
          <p className="meta num">
            {[p.model, `${nf.format(m.tokens.input)} masuk, ${nf.format(m.tokens.output)} keluar`].filter(Boolean).join(' · ')}
          </p>
        )}
      </div>
    </div>
  )
}
