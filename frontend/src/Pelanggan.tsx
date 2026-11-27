// #/pelanggan and #/pelanggan/<id>: WhatsApp conversations where a customer waits for a human. The left column is
// the queue (filtered by state), the right column one conversation. "Ambil alih" stops the AI employee and marks the
// conversation taken over; the staff member replies from their own WhatsApp, so there is no reply box here.
import { useCallback, useEffect, useRef, useState } from 'react'
import { useIsAdmin } from './adminMode'
import { ApiError, api, canWhatsApp, errText } from './bff'
import type { Conversation, ConversationCounts, ConversationMessage, WhatsAppStatus } from './bff'
import { useData } from './data'
import { HANDOVER_LABEL, HANDOVER_REASON, useHandoverQueue } from './handover'
import { agenPath, pelangganPath } from './router'
import { ErrorLine, ago, clock } from './ui'
import { Empty, Loading, PageHead } from './ui-extra'
import './handover.css'

type Filter = 'needs_human' | 'human' | 'all'
const FILTERS: { id: Filter; label: string }[] = [
  { id: 'needs_human', label: 'Perlu manusia' },
  { id: 'human', label: 'Diambil alih' },
  { id: 'all', label: 'Semua' },
]
interface Feed {
  state: 'loading' | 'ok' | 'error'
  items: Conversation[]
  next: string | null
  counts: ConversationCounts | null
  error: string
}
const FEED_START: Feed = { state: 'loading', items: [], next: null, counts: null, error: '' }

interface Thread {
  id: string
  items: ConversationMessage[]
  next: string | null
}
const THREAD_START: Thread = { id: '', items: [], next: null }

// Old pages and a 20-second refresh overlap; keep one row per message, newest text wins.
function mergeMessages(old: ConversationMessage[], next: ConversationMessage[]): ConversationMessage[] {
  const byId = new Map<string, ConversationMessage>()
  for (const m of old) byId.set(m.id, m)
  for (const m of next) byId.set(m.id, m)
  return [...byId.values()].sort((a, b) => a.at - b.at)
}

export default function Pelanggan({ id }: { id?: string }) {
  const { bots, on, flash } = useData()
  const admin = useIsAdmin()
  const { refresh: refreshQueue } = useHandoverQueue()
  const [filter, setFilter] = useState<Filter>('needs_human')
  const [feed, setFeed] = useState<Feed>(FEED_START)
  const [wa, setWa] = useState<WhatsAppStatus | null>(null)
  const [conv, setConv] = useState<Conversation | null>(null)
  const [detail, setDetail] = useState<{ state: 'idle' | 'loading' | 'ok' | 'error' | 'missing'; error: string }>({ state: id ? 'loading' : 'idle', error: '' })
  const [thread, setThread] = useState<Thread>(THREAD_START)
  const [busy, setBusy] = useState<'take' | 'back' | 'messages' | ''>('')
  const [problem, setProblem] = useState('')
  const [confirmBack, setConfirmBack] = useState(false)
  const [nonce, setNonce] = useState(0)
  const picked = useRef(false) // the user chose a filter; the automatic first choice must not override it
  const listSeq = useRef(0)
  // The conversation the reader is looking at now. An action that started on another one compares against
  // this before writing, so its reply cannot replace what the reader opened meanwhile.
  const openId = useRef(id)
  openId.current = id
  const actionRef = useRef<HTMLButtonElement>(null)
  const confirmRef = useRef<HTMLButtonElement>(null)
  const focusAction = useRef(false)
  const confirmWasOpen = useRef(false)

  const loadList = useCallback(async (f: Filter, opts: { before?: string; quiet?: boolean } = {}) => {
    const { before, quiet } = opts
    const seq = ++listSeq.current
    if (!before && !quiet) setFeed((s) => ({ ...s, state: 'loading', error: '' }))
    try {
      const page = await api.conversations({ state: f === 'all' ? undefined : f, before, limit: 30 })
      if (seq !== listSeq.current) return
      setFeed((s) => ({
        state: 'ok',
        items: before ? [...s.items, ...page.items] : page.items,
        next: page.next,
        counts: page.counts,
        error: '',
      }))
      // Nothing waits for a human: start on "Semua", matching the first honest view of the queue.
      if (!picked.current && f === 'needs_human' && page.counts.needs_human === 0) setFilter('all')
    } catch (e) {
      if (seq !== listSeq.current) return
      setFeed((s) => ({ ...s, state: 'error', error: errText(e) }))
    }
  }, [])

  useEffect(() => {
    void loadList(filter)
  }, [filter, loadList])

  useEffect(() => {
    let live = true
    api.whatsappStatus().then(
      (s) => live && setWa(s),
      () => undefined, // the list's own state is enough; no second error line
    )
    return () => {
      live = false
    }
  }, [])

  // One conversation: the header row and its messages load together.
  useEffect(() => {
    setConfirmBack(false)
    setProblem('')
    if (!id) {
      setConv(null)
      setThread(THREAD_START)
      setDetail({ state: 'idle', error: '' })
      return
    }
    let live = true
    setDetail({ state: 'loading', error: '' })
    setConv(null)
    setThread(THREAD_START)
    Promise.all([api.conversation(id), api.conversationMessages(id)]).then(
      ([c, m]) => {
        if (!live) return
        setConv(c)
        setThread({ id: c.id, items: m.items, next: m.next })
        setDetail({ state: 'ok', error: '' })
      },
      (e) => {
        if (!live) return
        setDetail({ state: e instanceof ApiError && e.status === 404 ? 'missing' : 'error', error: errText(e) })
      },
    )
    return () => {
      live = false
    }
  }, [id, nonce])

  // Soft refresh: keeps the current thread on screen and only reports a conversation that is gone. A reply
  // for a conversation the reader has left is dropped.
  const refreshOpen = useCallback(async () => {
    const cid = id
    if (!cid) return
    try {
      const [c, m] = await Promise.all([api.conversation(cid), api.conversationMessages(cid)])
      if (openId.current !== cid) return
      setConv(c)
      // The refresh reads the newest page only; the older-messages cursor stays where the reader left it.
      setThread((t) => (t.id === c.id ? { id: c.id, items: mergeMessages(t.items, m.items), next: t.next } : t))
      setDetail((d) => (d.state === 'missing' ? d : { state: 'ok', error: '' }))
    } catch (e) {
      if (openId.current !== cid) return
      if (e instanceof ApiError && e.status === 404) setDetail({ state: 'missing', error: errText(e) })
    }
  }, [id])

  // New messages arrive on their own while the conversation is open and the tab is visible.
  useEffect(() => {
    if (!id || detail.state !== 'ok') return
    const cid = id
    const t = window.setInterval(() => {
      if (document.visibilityState !== 'visible') return
      api.conversationMessages(cid).then(
        (m) => setThread((x) => (x.id === cid ? { id: cid, items: mergeMessages(x.items, m.items), next: x.next } : x)),
        () => undefined, // a quiet refresh never replaces the thread with an error
      )
    }, 20_000)
    return () => window.clearInterval(t)
  }, [id, detail.state])

  // A customer asking for a human changes the queue and, when open, the conversation itself.
  useEffect(
    () =>
      on('handover', () => {
        void loadList(filter, { quiet: true })
        void refreshOpen()
      }),
    [on, filter, loadList, refreshOpen],
  )

  const csBot = bots.find(canWhatsApp)
  const counts = feed.counts
  const total = counts ? counts.needs_human + counts.human + counts.bot : 0
  const current = conv && conv.id === id ? conv : null
  const actBusy = busy === 'take' || busy === 'back'
  const botName = (current && bots.find((b) => b.id === current.bot_id)?.name) || 'Pegawai AI'
  const shownThread = thread.id === id ? thread : THREAD_START
  const listHasRows = feed.state === 'ok' && feed.items.length > 0 && wa?.status !== 'not_configured'
  const showDetail = !!id || listHasRows
  const openOutside = !!current && listHasRows && !feed.items.some((c) => c.id === current.id)

  // A replaced button must not drop keyboard focus on <body>: the confirm row takes it when it opens,
  // Batal gives it back to the button that opened it, and a finished action lands on the new action.
  useEffect(() => {
    if (confirmBack) {
      confirmWasOpen.current = true
      confirmRef.current?.focus()
    } else if (confirmWasOpen.current) {
      confirmWasOpen.current = false
      if (!focusAction.current) actionRef.current?.focus()
    }
  }, [confirmBack])

  useEffect(() => {
    if (busy || !focusAction.current) return
    focusAction.current = false
    ;(confirmBack ? confirmRef.current : actionRef.current)?.focus()
  }, [busy, confirmBack, current?.state])

  function pick(f: Filter) {
    picked.current = true
    setFilter(f)
  }

  async function take() {
    if (!current || busy) return
    const cid = current.id
    setBusy('take')
    setProblem('')
    focusAction.current = true
    try {
      const next = await api.takeOver(cid)
      if (openId.current !== cid) return
      setConv(next)
      await refreshOpen()
      void loadList(filter, { quiet: true })
      refreshQueue()
      flash('Percakapan diambil alih. Balas lewat WhatsApp Anda.')
    } catch (e) {
      if (openId.current === cid) setProblem(errText(e))
    } finally {
      setBusy('')
    }
  }

  async function giveBack() {
    if (!current || busy) return
    const cid = current.id
    setBusy('back')
    setProblem('')
    focusAction.current = true
    try {
      const next = await api.handBack(cid)
      if (openId.current !== cid) return
      setConv(next)
      await refreshOpen()
      void loadList(filter, { quiet: true })
      refreshQueue()
      setConfirmBack(false)
      flash(`Dikembalikan ke ${botName}`)
    } catch (e) {
      if (openId.current === cid) setProblem(errText(e))
    } finally {
      setBusy('')
    }
  }

  async function moreMessages() {
    if (!id || !shownThread.next || busy) return
    setBusy('messages')
    setProblem('')
    try {
      const m = await api.conversationMessages(id, shownThread.next)
      setThread((t) => (t.id === id ? { id, items: mergeMessages(t.items, m.items), next: m.next } : t))
    } catch (e) {
      setProblem(errText(e))
    } finally {
      setBusy('')
    }
  }

  // One row, used by the list and by the pinned row that keeps the open conversation visible while a
  // different filter is active.
  function convRow(c: Conversation, note?: string) {
    const name = c.customer || 'Pelanggan'
    return (
      <li key={c.id} className="hv-row" data-state={c.state}>
        <a
          href={'#' + pelangganPath(c.id)}
          aria-current={c.id === id ? 'true' : undefined}
          aria-label={`${name}, ${HANDOVER_LABEL[c.state].toLowerCase()}, ${note ?? ago(c.last_at)}`}
        >
          <span className="hv-row-top">
            <b className="clamp2">{name}</b>
            {c.state !== 'bot' && <span className={`pill ${c.state === 'needs_human' ? 'wait' : 'run'}`}>{HANDOVER_LABEL[c.state]}</span>}
          </span>
          <small className="quiet num">WhatsApp …{c.phone_tail} · {note ?? ago(c.last_at)}</small>
          <small className="hv-last clamp2">{c.last_message}</small>
        </a>
      </li>
    )
  }

  const listBody = () => {
    if (feed.state === 'loading') return <Loading shape="ledger" text="Memuat percakapan..." />
    if (feed.state === 'error') return <ErrorLine text={feed.error} onRetry={() => void loadList(filter)} />
    if (feed.items.length > 0) {
      return (
        <>
          <ul className="hv-rows">
            {openOutside && current && convRow(current, 'Di luar saringan ini')}
            {feed.items.map((c) => convRow(c))}
          </ul>
          {feed.next && (
            <button type="button" className="btn soft hv-more-list" onClick={() => void loadList(filter, { before: feed.next ?? undefined })}>
              Muat lebih banyak
            </button>
          )}
        </>
      )
    }
    if (wa?.status === 'not_configured') {
      return (
        <Empty title="WhatsApp belum tersambung">
          {admin ? (
            <>
              <p>Sambungkan dulu di pengaturan pegawai layanan pelanggan.</p>
              {csBot && (
                <a className="btn soft hv-empty-act" href={`#${agenPath(csBot.id)}?tab=whatsapp`}>
                  Buka pengaturan WhatsApp
                </a>
              )}
            </>
          ) : (
            <p>Minta pemilik akun menyambungkan WhatsApp.</p>
          )}
        </Empty>
      )
    }
    if (filter === 'all') {
      return <Empty title="Belum ada percakapan pelanggan">Percakapan muncul di sini saat pelanggan mengirim pesan ke WhatsApp bisnis Anda.</Empty>
    }
    return (
      <Empty title="Tidak ada percakapan di sini.">
        <button type="button" className="btn link" onClick={() => pick('all')}>
          Lihat semua
        </button>
      </Empty>
    )
  }

  const detailBody = () => {
    if (!id) return <Empty title="Pilih percakapan">Pilih satu percakapan di kiri untuk melihat isinya.</Empty>
    if (detail.state === 'missing') {
      return (
        <Empty title="Percakapan tidak ditemukan">
          <p>Mungkin sudah dihapus.</p>
          <a className="back" href="#/pelanggan">
            ← Semua pelanggan
          </a>
        </Empty>
      )
    }
    if (detail.state === 'error') return <ErrorLine text={detail.error} onRetry={() => setNonce((n) => n + 1)} />
    if (detail.state !== 'ok' || !current) return <Loading shape="ledger" text="Memuat percakapan..." />
    return (
      <>
        <h2 id="hv-detail-h" className="clamp2">
          {current.customer || 'Pelanggan'}
        </h2>
        <p className="quiet small num">
          WhatsApp …{current.phone_tail} · dijawab oleh {botName}
        </p>
        {current.phone_tail && current.state !== 'bot' && (
          <p className="quiet small hv-find">Cari nama atau nomor pelanggan berakhiran {current.phone_tail} di WhatsApp Anda.</p>
        )}

        {current.state === 'needs_human' && (
          <div className="note-box hv-banner" role="status">
            <b>Pelanggan ini meminta bantuan manusia.</b>
            <p>
              {HANDOVER_REASON[current.reason]}. {botName} sudah berhenti membalas.
            </p>
          </div>
        )}
        {current.state === 'human' && (
          <div className="hv-human" role="status">
            <b>Diambil alih oleh {current.taken_by || 'staf'}.</b>
            <p>
              Balas pelanggan lewat WhatsApp Anda. {botName} tidak membalas sampai dikembalikan.
              {current.resume_at ? ` Kembali otomatis pukul ${clock(current.resume_at)}.` : ''}
            </p>
          </div>
        )}
        {current.state === 'bot' && <p className="quiet small hv-bot">Dijawab oleh {botName}.</p>}

        <div className="hv-actions">
          {problem && (
            <p className="problem-bar" role="alert">
              {problem}
            </p>
          )}
          {current.state === 'needs_human' && !confirmBack && <p className="quiet small hv-take-hint">Pegawai AI berhenti membalas. Anda membalas dari WhatsApp Anda.</p>}
          {confirmBack ? (
            <div className="confirm-actions" role="alert">
              <p>{botName} akan mulai membalas pelanggan ini lagi. Lanjut?</p>
              <button ref={confirmRef} type="button" className="btn primary" disabled={busy === 'back'} onClick={() => void giveBack()}>
                {busy === 'back' ? 'Mengembalikan…' : 'Kembalikan'}
              </button>
              <button type="button" className="btn quiet-btn" disabled={busy === 'back'} onClick={() => setConfirmBack(false)}>
                Batal
              </button>
            </div>
          ) : current.state === 'needs_human' ? (
            <>
              <button ref={actionRef} type="button" className="btn primary" disabled={actBusy} onClick={() => void take()}>
                {busy === 'take' ? 'Mengambil alih…' : 'Ambil alih'}
              </button>
              <button
                type="button"
                className="btn outline"
                disabled={actBusy}
                onClick={() => {
                  setConfirmBack(true)
                  setProblem('')
                }}
              >
                Kembalikan ke pegawai
              </button>
            </>
          ) : current.state === 'human' ? (
            <button
              ref={actionRef}
              type="button"
              className="btn primary"
              disabled={actBusy}
              onClick={() => {
                setConfirmBack(true)
                setProblem('')
              }}
            >
              Kembalikan ke pegawai
            </button>
          ) : (
            <button ref={actionRef} type="button" className="btn soft" disabled={actBusy} onClick={() => void take()}>
              {busy === 'take' ? 'Mengambil alih…' : 'Ambil alih'}
            </button>
          )}
        </div>

        <h3>Percakapan</h3>
        {shownThread.next && (
          <button type="button" className="btn link hv-more" disabled={busy === 'messages'} onClick={() => void moreMessages()}>
            {busy === 'messages' ? 'Memuat pesan…' : 'Muat pesan sebelumnya'}
          </button>
        )}
        <ul className="hv-thread">
          {shownThread.items.map((m) => (
            <li key={m.id} className="hv-msg" data-from={m.from}>
              {m.from !== 'system' && (
                <span className="hv-who">
                  {m.from === 'customer' ? 'Pelanggan' : m.from === 'staff' ? 'Staf' : botName}
                  {m.from === 'bot' && <small className="quiet"> Pegawai AI</small>}
                </span>
              )}
              <p>{m.text}</p>
              {m.at > 0 && (
                <time className="num" dateTime={new Date(m.at * 1000).toISOString()}>
                  {clock(m.at)}
                </time>
              )}
            </li>
          ))}
        </ul>
      </>
    )
  }

  return (
    <section className="page">
      <PageHead title="Pelanggan" sub="Percakapan pelanggan lewat WhatsApp. Pegawai AI menjawab sendiri; Anda mengambil alih bila perlu." />
      {id && (
        <a className="back hv-back" href="#/pelanggan">
          ← Semua pelanggan
        </a>
      )}
      <div className="hv" data-detail={id ? '' : undefined}>
        <section className="panel-card hv-list" aria-label="Daftar percakapan">
          <div className="seg" role="group" aria-label="Saring percakapan">
            {FILTERS.map((f) => {
              const n = f.id === 'needs_human' ? counts?.needs_human : f.id === 'human' ? counts?.human : counts ? total : undefined
              return (
                <button key={f.id} type="button" aria-pressed={filter === f.id} onClick={() => pick(f.id)}>
                  {n === undefined ? f.label : `${f.label} (${n})`}
                </button>
              )
            })}
          </div>
          {listBody()}
        </section>
        {showDetail && (
          <section className="panel-card hv-detail" aria-labelledby={current ? 'hv-detail-h' : undefined}>
            {detailBody()}
          </section>
        )}
      </div>
    </section>
  )
}
