import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { ApiError, api, asStr, errText } from './bff'
import type { Bot, GroupMsg } from './bff'
import { Md } from './Chat'
import { useData } from './data'
import { PanelButtons, SidePanel, Split } from './Panel'
import { groupPath } from './router'
import { BotAvatar, ErrorLine, PENCIL, Icon, ThinkingBlock, botColor, clock, teamLabel } from './ui'

const sameId = (a: string, b: string) => a === b
type Problem = { text: string; upgrade?: boolean } | null

export default function GroupChat({ id }: { id: string }) {
  const { groups, bots, loadState, on, setDialog, setGroup, askNotify, viewing, reload } = useData()
  const group = groups.find((g) => g.id === id)
  const members = (group?.members ?? []).map((m) => bots.find((b) => b.id === m)).filter((b): b is Bot => !!b)
  const [msgs, setMsgs] = useState<GroupMsg[]>([])
  const [state, setState] = useState<'loading' | 'ok' | 'error'>('loading')
  const [error, setError] = useState('')
  const [hasMore, setHasMore] = useState(false)
  const [older, setOlder] = useState(false)
  const [typing, setTyping] = useState<Record<string, 'thinking' | 'writing'>>({})
  const [rv, setRv] = useState(0) // bumped when group_reasoning arrives
  const [thoughts, setThoughts] = useState<Record<string, { text: string; seconds?: number }>>({}) // run_id -> reasoning
  const [pv, setPv] = useState(0) // bumped whenever the side panel's data may have changed
  const [pending, setPending] = useState<string[]>([]) // ids of queued user messages
  const [problem, setProblem] = useState<Problem>(null)
  const [draft, setDraft] = useState('')
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
    viewing(groupPath(id))
    return () => viewing('')
  }, [id, viewing])

  function load() {
    const mine = ++epoch.current
    setState('loading')
    setMsgs([])
    setTyping({})
    setPending([])
    setProblem(null)
    stick.current = true
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
        const b = asStr(d.bot_id)
        // phase "thinking" until the first words arrive, then "writing"
        setTyping((cur) => {
          if (!d.on) {
            const { [b]: _gone, ...rest } = cur
            return rest
          }
          return { ...cur, [b]: d.phase === 'writing' ? 'writing' : (cur[b] ?? 'thinking') }
        })
        bump()
      }),
      on('group_send', (d) => {
        if (asStr(d.group_id) === id && /done|complet|finish|stop|fail|error|idle|cancel|limit/i.test(asStr(d.status))) {
          setPending([])
          setTyping({})
          bump()
        }
      }),
    ]
    return () => offs.forEach((f) => f())
  }, [id, on])

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
  }, [msgs, typing])
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
    try {
      const r = await api.sendGroup(id, text, mode)
      if (r.message.id) {
        setMsgs((cur) => (cur.some((x) => sameId(x.id, r.message.id)) ? cur : [...cur, r.message]))
        if (r.queued) setPending((p) => [...p, r.message.id])
      }
    } catch (e) {
      setDraft((d) => d || text)
      setProblem({ text: errText(e), upgrade: e instanceof ApiError && e.upgrade })
    }
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
          {loadState === 'loading' ? <p className="quiet">Memuat grup...</p> : loadState === 'error' ? <ErrorLine text="Grup belum bisa dimuat." onRetry={reload} /> : <p className="quiet">Grup tidak ditemukan. Mungkin sudah dihapus.</p>}
        </div>
      </section>
    )
  }

  const typingBots = Object.keys(typing).map((t) => bots.find((b) => b.id === t)).filter((b): b is Bot => !!b)

  return (
    <Split panel={<SidePanel scope={{ group_id: id }} version={pv} group={group} members={members} />}>
    <section className="convo" aria-label={`Grup ${group.name}`}>
      <header className="convo-head">
        <div className="convo-title">
          {renaming !== null ? (
            <input
              className="rename title-edit"
              autoFocus
              value={renaming}
              maxLength={60}
              aria-label="Nama grup"
              onChange={(e) => setRenaming(e.target.value)}
              onBlur={() => void rename(renaming)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') void rename(renaming)
                else if (e.key === 'Escape') setRenaming(null)
              }}
            />
          ) : (
            <h1>
              <button className="title-btn" onClick={() => setRenaming(group.name)} aria-label={`Ubah nama grup ${group.name}`}>
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
        <button className="btn soft" onClick={() => setDialog({ kind: 'group', id })}>
          Atur anggota
        </button>
        <PanelButtons group />
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
              <p>Tulis tugas untuk grup ini. Sebut @nama untuk bertanya ke satu anggota; tanpa itu semua anggota ikut menjawab.</p>
            </div>
          )}
          {msgs.map((m) => (
            <GroupBubble key={m.id} m={m} bot={bots.find((b) => b.id === m.bot_id)} queued={pending.includes(m.id)} thought={thoughts[m.run_id ?? '']} />
          ))}
          {typingBots.length > 0 && (
            <div className="typing" style={{ ['--bot' as string]: botColor(typingBots[0]) }}>
              <span className="typing-dots" aria-hidden="true">
                <i />
                <i />
                <i />
              </span>
              {typingBots.map((b) => `${b.name} sedang ${typing[b.id] === 'writing' ? 'mengetik' : 'berpikir'}…`).join(' · ')}
            </div>
          )}
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
            void send('queue')
          }}
        >
          {options.length > 0 && (
            <ul className="mention" role="listbox" aria-label="Anggota grup">
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
          <label className="sr" htmlFor="gmsg">
            Pesan untuk grup {group.name}
          </label>
          <textarea
            id="gmsg"
            ref={box}
            rows={1}
            value={draft}
            placeholder={running ? 'Diskusi berjalan. Pesan baru masuk antrean.' : 'Tulis pesan. Ketik @ untuk menyebut anggota.'}
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
                void send('queue')
              }
            }}
          />
          <div className="composer-actions">
            {running && (
              <>
                <button type="button" className="btn stop" onClick={() => void stop()}>
                  <span className="square" aria-hidden="true" />
                  Berhenti
                </button>
                <button type="button" className="btn soft" onClick={() => void send('steer')} disabled={!draft.trim()}>
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

function GroupBubble({ m, bot, queued, thought }: { m: GroupMsg; bot?: Bot; queued: boolean; thought?: { text: string; seconds?: number } }) {
  if (m.role === 'system') return <p className="sys-msg">{m.text}</p>
  if (m.role === 'user') {
    return (
      <div className="msg user">
        <p>{m.text}</p>
        {queued && <span className="pending-tag">Antre, dikirim setelah ronde selesai</span>}
      </div>
    )
  }
  return (
    <div className="msg bot gmsg" style={{ ['--bot' as string]: botColor(bot) }}>
      <BotAvatar bot={bot ?? { name: '?', color: '' }} size={32} />
      <div className="msg-body">
        <p className="gmsg-who">
          <b>{bot?.name ?? 'Bot'}</b>
          {bot?.role && <span>{bot.role}</span>}
          {bot?.team && <span className="team-tag">{teamLabel(bot.team)}</span>}
          <time>{clock(m.created_at)}</time>
        </p>
        {thought?.text && <ThinkingBlock text={thought.text} running={false} seconds={thought.seconds} />}
        <div className="bubble">
          <Md text={m.text} />
        </div>
      </div>
    </div>
  )
}
