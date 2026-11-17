import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { ApiError, api, asStr, errText, subscribe } from './bff'
import type { Bot, GroupMsg, ToolChip } from './bff'
import { LiveSteps } from './LiveSteps'
import { applyTool, settle, toolsFrom } from './steps'
import { useSmoothText } from './useSmoothText'
import { MentionsCtx, Md } from './rich'
import { useData } from './data'
import { PlanCard, withoutPlanBlock } from './PlanCard'
import { PanelButtons, SidePanel, Split } from './Panel'
import { GmailDraftButton } from './gmail-ui'
import { RUNNING_HINT, STEER_KEY, STEER_TIP, isSteerKey } from './composerKeys'
import { KbAttach, KbLines, KbTrayView, asksToSave, useKbTray } from './kb-ui'
import { groupPath } from './router'
import { CopyButton } from './ui-extra'
import { BotAvatar, CLOSE, ErrorLine, PENCIL, Icon, ThinkingBlock, botColor, clock, teamLabel } from './ui'

const sameId = (a: string, b: string) => a === b
type Problem = { text: string; upgrade?: boolean } | null
// The bot turn being written right now: text and steps come from that run's own stream (the same one Chat follows).
interface Turn {
  bot: string
  run: string // empty until the run has started
  text: string
  tools: ToolChip[]
  reasoning: string
}

export default function GroupChat({ id, onRail }: { id: string; onRail: () => void }) {
  const { groups, bots, loadState, on, setDialog, setGroup, askNotify, viewing, reload } = useData()
  const group = groups.find((g) => g.id === id)
  const members = (group?.members ?? []).map((m) => bots.find((b) => b.id === m)).filter((b): b is Bot => !!b)
  const [msgs, setMsgs] = useState<GroupMsg[]>([])
  const [state, setState] = useState<'loading' | 'ok' | 'error'>('loading')
  const [error, setError] = useState('')
  const [hasMore, setHasMore] = useState(false)
  const [older, setOlder] = useState(false)
  const [turn, setTurn] = useState<Turn | null>(null)
  const [rv, setRv] = useState(0) // bumped when group_reasoning arrives
  const [thoughts, setThoughts] = useState<Record<string, { text: string; seconds?: number }>>({}) // run_id -> reasoning
  const [pv, setPv] = useState(0) // bumped whenever the side panel's data may have changed
  const [pending, setPending] = useState<string[]>([]) // ids of queued user messages
  const [kbBusy, setKbBusy] = useState(false) // the BFF is reading a link this message asked to save
  const [problem, setProblem] = useState<Problem>(null)
  const [draft, setDraft] = useState('')
  const kb = useKbTray(draft)
  const [mention, setMention] = useState<{ start: number; query: string } | null>(null)
  const [pick, setPick] = useState(0)
  const [renaming, setRenaming] = useState<string | null>(null)
  const scroller = useRef<HTMLDivElement>(null)
  const stick = useRef(true)
  const anchor = useRef<number | null>(null)
  const box = useRef<HTMLTextAreaElement>(null)
  const epoch = useRef(0)
  const running = !!group?.running

  useEffect(() => {
    if (!location.hash.includes('tulis=1')) return
    const t = window.setTimeout(() => box.current?.focus(), 150) // "Minta tim Anda" on Beranda: the message box is ready
    return () => window.clearTimeout(t)
  }, [id, state])

  useEffect(() => {
    viewing(groupPath(id))
    return () => viewing('')
  }, [id, viewing])

  function load() {
    const mine = ++epoch.current
    setState('loading')
    setMsgs([])
    setTurn(null)
    setPending([])
    setProblem(null)
    stick.current = true
    api.groupLive(id).then(
      (t) => mine === epoch.current && t && setTurn((cur) => cur ?? { bot: t.bot, run: t.run, text: '', tools: [], reasoning: '' }),
      () => {}, // a reload mid-turn recovers the live bubble; without it the final message still arrives
    )
    api.groupMessages(id).then(
      (m) => {
        if (mine !== epoch.current) return
        setMsgs(m)
        setHasMore(m.length >= 50)
        setState('ok')
      },
      (e) => {
        if (mine !== epoch.current) return
        setError(errText(e))
        setState('error')
      },
    )
  }
  useEffect(load, [id]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const add = (m: GroupMsg) => setMsgs((cur) => (cur.some((x) => sameId(x.id, m.id)) ? cur : [...cur, m]))
    const bump = () => setPv((n) => n + 1)
    const offs = [
      on('group_message', (d) => {
        if (asStr(d.group_id) === id) {
          add(d.message as GroupMsg)
          bump()
        }
      }),
      on('group_reasoning', (d) => {
        if (asStr(d.group_id) === id) {
          setRv((n) => n + 1)
          bump()
        }
      }),
      on('group_typing', (d) => {
        if (asStr(d.group_id) !== id) return
        const bot = asStr(d.bot_id)
        const run = asStr(d.run_id)
        setTurn((cur) => {
          if (!d.on) return cur?.bot === bot ? null : cur
          if (cur?.bot === bot) return run && !cur.run ? { ...cur, run } : cur
          return { bot, run, text: '', tools: [], reasoning: '' }
        })
        bump()
      }),
      on('group_send', (d) => {
        if (asStr(d.group_id) === id && /done|complet|finish|stop|fail|error|idle|cancel|limit/i.test(asStr(d.status))) {
          setPending([])
          setTurn(null)
          bump()
        }
      }),
    ]
    return () => offs.forEach((f) => f())
  }, [id, on])

  const run = turn?.run
  useEffect(() => {
    if (!run) return
    const upd = (f: (t: Turn) => Turn) => setTurn((cur) => (cur && cur.run === run ? f(cur) : cur))
    const off = subscribe(`/runs/${encodeURIComponent(run)}/stream`, {
      snapshot: (d) =>
        upd((t) => ({ ...t, text: asStr(d.output), tools: toolsFrom(d.events) ?? t.tools, reasoning: asStr(d.reasoning) || t.reasoning })),
      delta: (d) => upd((t) => ({ ...t, text: t.text + asStr(d.text) })),
      tool: (d) => upd((t) => ({ ...t, tools: applyTool(t.tools, d) })),
      reasoning: (d) => upd((t) => ({ ...t, reasoning: [t.reasoning, asStr(d.text)].filter(Boolean).join('\n\n') })),
      done: () => {
        off() // a finished run's stream ends; left open, EventSource would reconnect forever
        upd((t) => ({ ...t, tools: settle(t.tools) })) // the final message replaces this bubble
      },
    })
    return off
  }, [run])

  useEffect(() => {
    let live = true
    api.thinking({ group_id: id }).then(
      (t) => live && setThoughts(Object.fromEntries(t.map((x) => [x.run_id, { text: x.reasoning, seconds: x.seconds }]))),
      () => {}, // the inline block is optional; the side panel reports errors
    )
    return () => {
      live = false
    }
  }, [id, rv, msgs.length])

  useLayoutEffect(() => {
    const el = scroller.current
    if (!el) return
    if (anchor.current !== null) {
      el.scrollTop = el.scrollHeight - anchor.current // keep the reader's place after older messages are prepended
      anchor.current = null
    } else if (stick.current) el.scrollTop = el.scrollHeight
  }, [msgs, turn])
  useEffect(() => {
    const el = box.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }, [draft])

  async function loadOlder() {
    if (older || !hasMore || msgs.length === 0) return
    setOlder(true)
    const el = scroller.current
    try {
      const m = await api.groupMessages(id, msgs[0].id)
      anchor.current = el ? el.scrollHeight - el.scrollTop : null
      setMsgs((cur) => [...m.filter((x) => !cur.some((c) => sameId(c.id, x.id))), ...cur])
      setHasMore(m.length >= 50)
    } catch (e) {
      setProblem({ text: errText(e) })
    } finally {
      setOlder(false)
    }
  }

  async function send(mode: 'queue' | 'steer') {
    const text = draft.trim()
    if (!text) return
    setDraft('')
    setMention(null)
    setProblem(null)
    askNotify()
    stick.current = true
    const ids = kb.take()
    setKbBusy(asksToSave(text))
    try {
      const r = await api.sendGroup(id, text, mode, ids)
      if (r.message.id) {
        setMsgs((cur) => (cur.some((x) => sameId(x.id, r.message.id)) ? cur : [...cur, r.message]))
        if (r.queued) setPending((p) => [...p, r.message.id])
      }
    } catch (e) {
      setDraft((d) => d || text)
      setProblem({ text: errText(e), upgrade: e instanceof ApiError && e.upgrade })
    }
    setKbBusy(false)
  }

  // A queued message leaves the queue either way: delivered now, or removed. A 409 means the agent already picked it up.
  async function queuedAction(mid: string, act: 'steer' | 'cancel') {
    setProblem(null)
    try {
      await (act === 'steer' ? api.steerGroupMessage(id, mid) : api.cancelGroupMessage(id, mid))
      if (act === 'cancel') setMsgs((cur) => cur.filter((x) => x.id !== mid))
    } catch (e) {
      setProblem({ text: errText(e) })
    }
    setPending((p) => p.filter((x) => x !== mid))
  }

  async function stop() {
    try {
      await api.stopGroup(id)
    } catch (e) {
      setProblem({ text: errText(e) })
    }
  }

  async function rename(name: string) {
    setRenaming(null)
    const n = name.trim()
    if (!n || !group || n === group.name) return
    try {
      setGroup(await api.patchGroup(id, { name: n }))
    } catch (e) {
      setProblem({ text: errText(e) })
    }
  }

  function track(el: HTMLTextAreaElement) {
    const upto = el.value.slice(0, el.selectionStart)
    const m = /(^|\s)@([\p{L}\p{N}_]*)$/u.exec(upto)
    setMention(m ? { start: upto.length - m[2].length - 1, query: m[2].toLowerCase() } : null)
    setPick(0)
  }
  const options = mention ? members.filter((b) => b.name.toLowerCase().replace(/\s/g, '').startsWith(mention.query)) : []
  function choose(b: Bot) {
    if (!mention || !box.current) return
    const caret = box.current.selectionStart
    const name = '@' + b.name.replace(/\s/g, '') + ' '
    const next = draft.slice(0, mention.start) + name + draft.slice(caret)
    setDraft(next)
    setMention(null)
    const at = mention.start + name.length
    window.setTimeout(() => {
      box.current?.focus()
      box.current?.setSelectionRange(at, at)
    }, 0)
  }

  if (!group) {
    return (
      <section className="convo">
        <div className="page-state">
          {loadState === 'loading' ? <p className="quiet">Memuat tim...</p> : loadState === 'error' ? <ErrorLine text="Tim belum bisa dimuat." onRetry={reload} /> : <p className="quiet">Tim tidak ditemukan. Mungkin sudah dihapus.</p>}
        </div>
      </section>
    )
  }

  return (
    <Split panel={<SidePanel scope={{ group_id: id }} version={pv} group={group} members={members} />}>
    <section className="convo" aria-label={`Tim ${group.name}`}>
      <header className="convo-head">
        <button className="btn soft sm rail-open" onClick={onRail}>
          Daftar tim
        </button>
        <div className="convo-title">
          {renaming !== null ? (
            <input
              className="rename title-edit"
              autoFocus
              value={renaming}
              maxLength={60}
              aria-label="Nama tim"
              onChange={(e) => setRenaming(e.target.value)}
              onBlur={() => void rename(renaming)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') void rename(renaming)
                else if (e.key === 'Escape') setRenaming(null)
              }}
            />
          ) : (
            <h1>
              <button className="title-btn" onClick={() => setRenaming(group.name)} aria-label={`Ubah nama tim ${group.name}`}>
                {group.name}
                <Icon d={PENCIL} size={14} />
              </button>
            </h1>
          )}
          <p>
            {members.map((m) => m.name).join(', ') || 'Belum ada anggota'}
            {running ? ' · diskusi berjalan' : ''}
          </p>
        </div>
        <span className="avatar-stack" aria-hidden="true">
          {members.slice(0, 6).map((b) => (
            <BotAvatar key={b.id} bot={b} size={28} />
          ))}
        </span>
        <button className="btn soft sm" onClick={() => setDialog({ kind: 'group', id })}>
          Atur anggota
        </button>
        <PanelButtons />
      </header>

      <div
        className="scroll"
        ref={scroller}
        onScroll={(e) => {
          const el = e.currentTarget
          stick.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80
          if (el.scrollTop < 60) void loadOlder()
        }}
      >
        <MentionsCtx.Provider value={members}>
        <div className="thread group-thread" aria-live="polite">
          {state === 'loading' && <p className="quiet center">Memuat pesan...</p>}
          {state === 'error' && <ErrorLine text={error} onRetry={load} />}
          {state === 'ok' && hasMore && (
            <button className="btn link more" onClick={() => void loadOlder()} disabled={older}>
              {older ? 'Memuat...' : 'Muat pesan lama'}
            </button>
          )}
          {state === 'ok' && msgs.length === 0 && (
            <div className="empty">
              <span className="avatar-stack big">
                {members.slice(0, 4).map((b) => (
                  <BotAvatar key={b.id} bot={b} size={44} />
                ))}
              </span>
              <h2>Belum ada pesan</h2>
              <p>Tulis tugas untuk tim ini. Sebut @nama untuk bertanya ke satu anggota.</p>
            </div>
          )}
          {msgs.filter((m) => !pending.includes(m.id)).map((m) => (
            <GroupBubble key={m.id} m={m} bot={bots.find((b) => b.id === m.bot_id)} queued={pending.includes(m.id)} thought={thoughts[m.run_id ?? '']} onApproved={(sid) => setMsgs((cur) => cur.map((x) => (x.id === m.id && x.plan ? { ...x, plan: { ...x.plan, schedule_id: sid } } : x)))} />
          ))}
          {turn && <LiveBubble t={turn} bot={bots.find((b) => b.id === turn.bot)} />}
        </div>
        </MentionsCtx.Provider>
      </div>

      <div className="composer-wrap">
        {pending.length > 0 && (
          <ul className="queue-rows" aria-label="Pesan menunggu giliran">
            {pending.map((mid) => (
              <li key={mid} className="queue-row">
                <span className="queue-text">{msgs.find((m) => m.id === mid)?.text ?? 'Pesan Anda'}</span>
                <small>Menunggu giliran</small>
                <button type="button" className="btn link" onClick={() => void queuedAction(mid, 'steer')} title={STEER_TIP}>
                  Kirim sekarang
                </button>
                <button type="button" className="icon-btn tiny" aria-label="Hapus pesan ini dari antrean" onClick={() => void queuedAction(mid, 'cancel')}>
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
            void send('queue')
          }}
        >
          {options.length > 0 && (
            <ul className="mention" role="listbox" aria-label="Anggota tim">
              {options.map((b, i) => (
                <li key={b.id} role="option" aria-selected={i === pick}>
                  <button type="button" className="mention-row" data-on={i === pick || undefined} onMouseDown={(e) => e.preventDefault()} onClick={() => choose(b)}>
                    <BotAvatar bot={b} size={24} />
                    <b>{b.name}</b>
                    <small>{b.role}</small>
                  </button>
                </li>
              ))}
            </ul>
          )}
          <KbTrayView kb={kb} />
          {kbBusy && <KbLines busy />}
          <label className="sr" htmlFor="gmsg">
            Pesan untuk tim {group.name}
          </label>
          <textarea
            id="gmsg"
            ref={box}
            rows={1}
            value={draft}
            placeholder={running ? 'Agen sedang bekerja. Pesan Anda akan dikirim setelah selesai.' : 'Tulis pesan. Ketik @ untuk menyebut anggota.'}
            onChange={(e) => {
              setDraft(e.target.value)
              track(e.target)
            }}
            onKeyUp={(e) => {
              if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') track(e.currentTarget)
            }}
            onKeyDown={(e) => {
              if (options.length > 0) {
                if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                  e.preventDefault()
                  setPick((p) => (p + (e.key === 'ArrowDown' ? 1 : options.length - 1)) % options.length)
                  return
                }
                if (e.key === 'Enter' || e.key === 'Tab') {
                  e.preventDefault()
                  choose(options[pick])
                  return
                }
                if (e.key === 'Escape') return setMention(null)
              }
              if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault()
                void send(running && isSteerKey(e) ? 'steer' : 'queue')
              }
            }}
          />
          <div className="composer-actions">
            <KbAttach kb={kb} />
            {running && (
              <>
                <button type="button" className="btn stop" onClick={() => void stop()}>
                  <span className="square" aria-hidden="true" />
                  Berhenti
                </button>
                <button type="button" className="btn soft" onClick={() => void send('steer')} disabled={!draft.trim()} title={STEER_TIP}>
                  Kirim sekarang <kbd>{STEER_KEY}</kbd>
                </button>
              </>
            )}
            <button type="submit" className="btn primary" disabled={!draft.trim()}>
              {running ? <>Kirim setelah selesai <kbd>Enter</kbd></> : 'Kirim'}
            </button>
          </div>
        </form>
        <p className="composer-note">
          {running ? RUNNING_HINT : 'Enter untuk kirim, Shift+Enter untuk baris baru.'} <a href="#/marketing">Pakai formulir brief</a>
        </p>
      </div>
    </section>
    </Split>
  )
}

function GroupBubble({ m, bot, queued, thought, onApproved }: { m: GroupMsg; bot?: Bot; queued: boolean; thought?: { text: string; seconds?: number }; onApproved: (scheduleId: string) => void }) {
  if (m.role === 'system') return <p className="sys-msg">{m.text}</p>
  if (m.role === 'user') {
    return (
      <div className="msg user">
        <p>{m.text}</p>
        {queued && <span className="pending-tag">Menunggu giliran, dikirim setelah ronde selesai</span>}
      </div>
    )
  }
  return (
    <div className="msg bot gmsg" style={{ ['--bot' as string]: botColor(bot) }}>
      <BotAvatar bot={bot ?? { name: '?', color: '' }} size={32} />
      <div className="msg-body">
        <p className="gmsg-who">
          <b>{bot?.name ?? 'Agen'}</b>
          {bot?.role && <span>{bot.role}</span>}
          {bot?.team && <span className="team-tag" data-team={bot.team}>{teamLabel(bot.team)}</span>}
          <time>{clock(m.created_at)}</time>
        </p>
        {thought?.text && <ThinkingBlock text={thought.text} running={false} seconds={thought.seconds} />}
        <div className="bubble">
          <Md text={m.plan ? withoutPlanBlock(m.text) : m.text} />
        </div>
        {m.text.trim() && (
          <div className="msg-tools">
            <CopyButton text={m.plan ? withoutPlanBlock(m.text) : m.text} what="jawaban" />
            <GmailDraftButton text={m.plan ? withoutPlanBlock(m.text) : m.text} />
          </div>
        )}
        {m.plan && <PlanCard groupId={m.group_id} messageId={m.id} plan={m.plan} onApproved={onApproved} />}
      </div>
    </div>
  )
}

function LiveBubble({ t, bot }: { t: Turn; bot?: Bot }) {
  const sm = useSmoothText(t.text, true)
  const waiting = !t.text
  return (
    <div className="msg bot gmsg" style={{ ['--bot' as string]: botColor(bot) }}>
      <BotAvatar bot={bot ?? { name: '?', color: '' }} size={32} />
      <div className="msg-body">
        <p className="gmsg-who">
          <b>{bot?.name ?? 'Agen'}</b>
          {bot?.role && <span>{bot.role}</span>}
          {bot?.team && <span className="team-tag">{teamLabel(bot.team)}</span>}
        </p>
        <LiveSteps tools={t.tools} running writing={!waiting} />
        <ThinkingBlock text={t.reasoning} running={waiting} />
        {!waiting && (
          <div className="bubble">
            <Md text={sm.text} caret={sm.caret} />
          </div>
        )}
      </div>
    </div>
  )
}
