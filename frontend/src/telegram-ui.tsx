import { useCallback, useEffect, useRef, useState } from 'react'
import { api, errText } from './bff'
import type { Bot, TelegramInfo, TelegramPairing, TelegramPerson, TelegramState } from './bff'
import { useAdminMode } from './adminMode'
import { useData } from './data'
import { CHEVRON, ErrorLine, Icon, useMedia } from './ui'
import { CopyButton, Loading, Spinner } from './ui-extra'
import './telegram.css'

// R3: connect the employee's own Telegram bot from its page. The bot is created in Telegram itself,
// so the screen only shows a link, a QR for a phone camera, and who may talk to it.

const mmss = (left: number) => `${String(Math.floor(left / 60)).padStart(2, '0')}:${String(left % 60).padStart(2, '0')}`

// Seconds left until an epoch time; ticks only while mounted.
function useLeft(until?: number): number {
  const calc = () => (until ? Math.max(0, until - Math.floor(Date.now() / 1000)) : 0)
  const [left, setLeft] = useState(calc)
  useEffect(() => {
    setLeft(calc())
    if (!until) return
    const t = window.setInterval(() => setLeft(calc()), 1000)
    return () => window.clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- calc reads `until`, listed below
  }, [until])
  return left
}

function Countdown({ until }: { until: number }) {
  const left = useLeft(until)
  return (
    <span className="num" aria-hidden="true">
      {mmss(left)}
    </span>
  )
}

// QR from the uqr package, encoded in the browser. One <path> keeps the DOM small; it is never innerHTML.
function QrCode({ text, size }: { text: string; size: number }) {
  const [qr, setQr] = useState<{ d: string; size: number } | null>(null)
  useEffect(() => {
    let live = true
    setQr(null)
    void import('uqr').then(
      ({ encode }) => {
        if (!live) return
        const { data, size: modules } = encode(text, { ecc: 'M', border: 1 })
        let d = ''
        for (let y = 0; y < data.length; y++) {
          const row = data[y]
          let x = 0
          while (x < row.length) {
            if (!row[x]) {
              x++
              continue
            }
            let n = 1
            while (x + n < row.length && row[x + n]) n++
            d += `M${x} ${y}h${n}v1h-${n}z`
            x += n
          }
        }
        setQr({ d, size: modules })
      },
      () => {
        /* no QR: the link below it is the alternative */
      },
    )
    return () => {
      live = false
    }
  }, [text])
  if (!qr)
    return (
      <span className="skel-block tg-qr-skel" role="status">
        <span className="sr">Menyiapkan kode QR</span>
      </span>
    )
  return (
    <svg viewBox={`0 0 ${qr.size} ${qr.size}`} width={size} height={size} role="img" aria-label="Kode QR untuk membuat bot Telegram" shapeRendering="crispEdges">
      <path d={qr.d} fill="#15171c" />
    </svg>
  )
}

// The Ringkasan row: label, live status and a way into the Telegram tab.
export function TelegramRow({ bot, onOpen }: { bot: Bot; onOpen: () => void }) {
  const [value, setValue] = useState('…')
  useEffect(() => {
    let live = true
    api.telegram(bot.id).then(
      (info) => {
        if (!live) return
        setValue(
          info.status === 'connected'
            ? info.username
              ? `@${info.username}`
              : 'Tersambung'
            : info.status === 'error'
              ? 'Perlu dihubungkan ulang'
              : 'Belum tersambung',
        )
      },
      () => live && setValue('Belum diketahui'),
    )
    return () => {
      live = false
    }
  }, [bot.id])
  return (
    <li>
      <button type="button" className="tg-row" onClick={onOpen}>
        <b>Telegram</b>
        <span className="quiet small">{value}</span>
        <span className="tg-row-chev" aria-hidden="true">
          <Icon d={CHEVRON} size={14} />
        </span>
      </button>
    </li>
  )
}

// "Siapa yang boleh memakai bot ini": owner, staff, people asking for permission, and (admin only)
// the numeric-ID fallback the current contract offers for adding somebody.
function PeopleSection({
  slug,
  allowed,
  pending,
  admin,
  onChanged,
}: {
  slug: string
  allowed: TelegramPerson[]
  pending: TelegramPerson[]
  admin: boolean
  onChanged: () => Promise<void>
}) {
  const [askRemove, setAskRemove] = useState('')
  const [hiddenPending, setHiddenPending] = useState<string[]>([])
  const [busy, setBusy] = useState('')
  const [problem, setProblem] = useState('')
  const [newId, setNewId] = useState('')
  const ids = allowed.map((p) => p.id)
  const ownerMarked = allowed.some((p) => p.owner)
  const shownPending = pending.filter((p) => !hiddenPending.includes(p.id))
  const cleanId = newId.trim()
  const idOk = /^[0-9]{5,15}$/.test(cleanId)

  async function save(next: string[], key: string): Promise<boolean> {
    setBusy(key)
    setProblem('')
    try {
      await api.telegramAllowed(slug, next)
      setAskRemove('')
      await onChanged()
      return true
    } catch (e) {
      setProblem(errText(e))
      return false
    } finally {
      setBusy('')
    }
  }

  async function add(e: React.FormEvent) {
    e.preventDefault()
    if (!idOk || busy) return
    if (await save([...ids, cleanId], 'add')) setNewId('')
  }

  return (
    <>
      <section aria-labelledby="tg-people-h">
        <h3 id="tg-people-h">Siapa yang boleh memakai bot ini · {allowed.length}</h3>
        {allowed.length === 0 ? (
          <p className="quiet small">Belum ada orang yang diizinkan.</p>
        ) : (
          <ul className="tg-people">
            {allowed.map((p, i) => {
              const owner = p.owner === true || (!ownerMarked && i === 0)
              if (askRemove === p.id)
                return (
                  <li key={p.id} className="tg-person-confirm" role="alert">
                    <p>Hapus akses {p.name}? Orang ini tidak bisa lagi mengobrol dengan bot.</p>
                    <span className="confirm-actions">
                      <button className="btn danger" disabled={busy === 'rm:' + p.id} onClick={() => void save(ids.filter((id) => id !== p.id), 'rm:' + p.id)}>
                        {busy === 'rm:' + p.id ? 'Menghapus…' : 'Hapus'}
                      </button>
                      <button className="btn quiet-btn" onClick={() => setAskRemove('')}>
                        Batal
                      </button>
                    </span>
                  </li>
                )
              return (
                <li key={p.id} className="tg-person">
                  <span className="tg-avatar" aria-hidden="true">
                    {(p.name.trim().charAt(0) || '?').toUpperCase()}
                  </span>
                  <span className="tg-person-txt">
                    <span className="tg-person-name clamp2">{p.name}</span>
                    {owner && <span className="pill plain">Pemilik</span>}
                  </span>
                  {!owner && (
                    <button className="btn link" onClick={() => setAskRemove(p.id)}>
                      Hapus akses
                    </button>
                  )}
                </li>
              )
            })}
          </ul>
        )}
        {problem && (
          <p className="problem-bar small" role="alert">
            {problem}
          </p>
        )}
      </section>

      {shownPending.length > 0 && (
        <section className="tg-pending" aria-labelledby="tg-pending-h">
          <h3 id="tg-pending-h">Meminta izin · {shownPending.length}</h3>
          <ul className="tg-people">
            {shownPending.map((p) => (
              <li key={p.id} className="tg-person">
                <span className="tg-avatar" aria-hidden="true">
                  {(p.name.trim().charAt(0) || '?').toUpperCase()}
                </span>
                <span className="tg-person-txt">
                  <span className="tg-person-name clamp2">{p.name}</span>
                </span>
                <span className="confirm-actions">
                  <button className="btn soft" disabled={busy === 'ok:' + p.id} onClick={() => void save([...ids, p.id], 'ok:' + p.id)}>
                    {busy === 'ok:' + p.id ? 'Mengizinkan…' : 'Izinkan'}
                  </button>
                  <button className="btn link" onClick={() => setHiddenPending((h) => [...h, p.id])}>
                    Tolak
                  </button>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="quiet small tg-quiet-add">Untuk menambah orang lain, minta mereka membuka bot ini di Telegram. Menambah lewat undangan: Belum tersedia.</p>
      {admin && (
        <form className="tg-add" onSubmit={(e) => void add(e)}>
          <label className="field">
            <span>ID Telegram (angka)</span>
            <input inputMode="numeric" pattern="[0-9]{5,15}" value={newId} onChange={(e) => setNewId(e.target.value)} required />
          </label>
          <button className="btn soft" type="submit" disabled={!idOk || !!busy}>
            {busy === 'add' ? 'Menambah…' : 'Tambah'}
          </button>
        </form>
      )}
    </>
  )
}

// Fallback for an admin who already has a bot from BotFather. The key is sent once and not kept.
function TokenForm({ slug, onDone }: { slug: string; onDone: () => Promise<void> }) {
  const { flash } = useData()
  const [token, setToken] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const t = token.trim()
    if (!t || busy) return
    setBusy(true)
    setError('')
    try {
      await api.telegramToken(slug, t)
      setToken('')
      await onDone()
      flash('Telegram tersambung')
    } catch (e) {
      setError(errText(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <details className="tg-alt">
      <summary>Sudah punya bot dari BotFather?</summary>
      <form className="tg-token" onSubmit={(e) => void submit(e)}>
        <label className="field">
          <span>Kunci bot dari @BotFather</span>
          <input type="password" autoComplete="off" spellCheck={false} inputMode="text" value={token} onChange={(e) => setToken(e.target.value)} required />
        </label>
        <p className="quiet small">Salin dari pesan @BotFather. Bentuknya angka, titik dua, lalu huruf dan angka.</p>
        {error && (
          <small className="err" role="alert">
            {error}
          </small>
        )}
        <button className="btn soft" type="submit" disabled={busy || !token.trim()}>
          {busy ? 'Memeriksa…' : 'Sambungkan'}
        </button>
      </form>
    </details>
  )
}

export function TelegramTab({ bot }: { bot: Bot }) {
  const { flash } = useData()
  const admin = useAdminMode()
  const wide = useMedia('(min-width: 641px)')
  const [qrOpen, setQrOpen] = useState(wide)
  const [info, setInfo] = useState<TelegramInfo | null>(null)
  const [state, setState] = useState<'loading' | 'ok' | 'error'>('loading')
  const [pairing, setPairing] = useState<TelegramPairing | null>(null)
  const [busy, setBusy] = useState<'start' | 'disconnect' | ''>('')
  const [problem, setProblem] = useState('')
  const [askDisconnect, setAskDisconnect] = useState(false)
  const req = useRef(0)
  const previous = useRef<TelegramState | null>(null)

  // A stopped bot (or a reloaded tab) always gets a fresh read; `quiet` keeps a background poll from
  // replacing the page with an error when one request fails.
  const fetchInfo = useCallback(
    async (quiet = false) => {
      const n = ++req.current
      try {
        const next = await api.telegram(bot.id)
        if (n !== req.current) return
        setInfo(next)
        setState('ok')
      } catch {
        if (n !== req.current) return
        if (!quiet) setState('error')
      }
    },
    [bot.id],
  )

  useEffect(() => {
    setInfo(null)
    setState('loading')
    setPairing(null)
    setProblem('')
    setAskDisconnect(false)
    setQrOpen(wide)
    void fetchInfo()
    return () => {
      req.current++
    }
    // wide only seeds the open state at mount; later changes are handled below
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchInfo])

  useEffect(() => {
    setQrOpen(wide)
  }, [wide])

  const status: TelegramState = info?.status === 'connected' ? 'connected' : info?.status === 'error' ? 'error' : info?.status === 'pending' || pairing ? 'pending' : 'none'

  // Keep the first link shown (start response or the first read), so the countdown does not restart on
  // every background poll and can actually reach zero.
  useEffect(() => {
    if (state !== 'ok' || !info) return
    if (info.status === 'pending' && info.pairing) setPairing((p) => p ?? info.pairing!)
    if (info.status === 'none' || info.status === 'connected') setPairing(null)
  }, [state, info])

  useEffect(() => {
    if (state !== 'ok') return
    if (previous.current === 'pending' && status === 'connected') flash('Telegram tersambung')
    previous.current = status
  }, [state, status, flash])

  // While waiting, read the status every 3 s; pause in a hidden tab and read once when it returns.
  useEffect(() => {
    if (state !== 'ok' || status !== 'pending') return
    const tick = () => {
      if (!document.hidden) void fetchInfo(true)
    }
    const timer = window.setInterval(tick, 3000)
    const onVisible = () => {
      if (!document.hidden) void fetchInfo(true)
    }
    document.addEventListener('visibilitychange', onVisible)
    return () => {
      window.clearInterval(timer)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [state, status, fetchInfo])

  async function start() {
    setBusy('start')
    setProblem('')
    try {
      const p = await api.telegramStart(bot.id)
      setPairing(p)
      setInfo((cur) => ({
        status: 'pending',
        allowed: cur?.allowed ?? [],
        pending: cur?.pending ?? [],
        pairing: p,
      }))
      previous.current = 'pending'
    } catch (e) {
      setProblem(errText(e))
    } finally {
      setBusy('')
    }
  }

  async function disconnect() {
    setBusy('disconnect')
    setProblem('')
    try {
      await api.telegramDisconnect(bot.id)
      setPairing(null)
      setAskDisconnect(false)
      setInfo({ status: 'none', allowed: [], pending: [] })
      previous.current = 'none'
      await fetchInfo(true)
    } catch (e) {
      setProblem(errText(e))
    } finally {
      setBusy('')
    }
  }

  // A pairing without a link has no usable control: treat it as "waiting, link lost".
  const waitLink = pairing && pairing.link ? pairing : null
  const left = useLeft(waitLink?.expires_at)
  const heading = state === 'ok' && (status === 'none' || status === 'pending') ? 'Hubungkan Telegram' : 'Telegram'
  const retry = () => {
    setState('loading')
    void fetchInfo()
  }

  return (
    <div className="cbox tg">
      <h2>{heading}</h2>

      {state === 'loading' && <Loading text="Memuat Telegram..." shape="lines" rows={3} />}
      {state === 'error' && <ErrorLine text="Status Telegram belum bisa dimuat. Coba lagi sebentar." onRetry={retry} />}

      {state === 'ok' && status === 'none' && (
        <>
          <p>
            Dengan Telegram, Anda dan tim bisa mengobrol dengan {bot.name} dari ponsel. {bot.name} akan punya bot Telegram sendiri.
          </p>
          <button className="btn primary tg-start" type="button" disabled={busy === 'start'} onClick={() => void start()}>
            {busy === 'start' ? 'Menyiapkan…' : 'Hubungkan Telegram'}
          </button>
          {problem && (
            <p className="problem-bar" role="alert">
              {problem}
            </p>
          )}
          {admin && <TokenForm slug={bot.id} onDone={async () => await fetchInfo(true)} />}
        </>
      )}

      {state === 'ok' && status === 'pending' && waitLink && left <= 0 && (
        <>
          <p className="note-box" role="alert">
            Tautan sudah kedaluwarsa.
          </p>
          <button className="btn primary tg-start" type="button" disabled={busy === 'start'} onClick={() => void start()}>
            {busy === 'start' ? 'Menyiapkan…' : 'Buat tautan baru'}
          </button>
          {problem && (
            <p className="problem-bar" role="alert">
              {problem}
            </p>
          )}
        </>
      )}

      {state === 'ok' && status === 'pending' && waitLink && left > 0 && (
        <>
          <div className="tg-wait">
            <div className="tg-wait-main">
              <ol className="tg-steps">
                <li>Di ponsel, arahkan kamera ke kode ini. Di komputer ini, klik tombol di bawah.</li>
                <li>Telegram menampilkan nama bot untuk {bot.name}. Tekan <b>Buat</b>.</li>
                <li>Kembali ke sini. Halaman ini terbarui sendiri.</li>
              </ol>
              <div className="tg-wait-actions">
                <a className="btn primary" href={waitLink.link} target="_blank" rel="noopener noreferrer">
                  Buka Telegram
                </a>
                <CopyButton text={waitLink.link} what="tautan" />
              </div>
              <div className="tg-wait-state">
                <p className="tg-waiting" role="status">
                  <Spinner />
                  Menunggu konfirmasi di Telegram…
                </p>
                <small className="quiet num" aria-hidden="true">
                  Tautan berlaku <Countdown until={waitLink.expires_at} /> lagi
                </small>
              </div>
            </div>
            <details
              className="tg-qr-wrap"
              open={qrOpen}
              onToggle={(e) => {
                if (!wide) setQrOpen(e.currentTarget.open)
              }}
            >
              <summary>Tampilkan kode QR (untuk dipindai dari ponsel lain)</summary>
              <div className="tg-qr">
                <QrCode text={waitLink.qr_text || waitLink.link} size={168} />
              </div>
              <a className="btn link tg-qr-link" href={waitLink.link} target="_blank" rel="noopener noreferrer">
                Buka tautan Telegram
              </a>
            </details>
          </div>
          {problem && (
            <p className="problem-bar" role="alert">
              {problem}
            </p>
          )}
        </>
      )}

      {state === 'ok' && status === 'pending' && !waitLink && (
        <>
          <p role="status">Menunggu konfirmasi di Telegram…</p>
          <button className="btn soft tg-start" type="button" disabled={busy === 'start'} onClick={() => void start()}>
            {busy === 'start' ? 'Menyiapkan…' : 'Buat tautan baru'}
          </button>
          {problem && (
            <p className="problem-bar" role="alert">
              {problem}
            </p>
          )}
        </>
      )}

      {state === 'ok' && status === 'connected' && info && (
        <>
          <div className="tg-head">
            <span className="tg-mark" aria-hidden="true">
              T
            </span>
            <div className="tg-head-line">
              <span className="pill ok">Tersambung</span>
              <p>{info.username ? <>Tersambung sebagai <b>@{info.username}</b></> : 'Tersambung'}</p>
            </div>
          </div>
          {info.username && (
            <a className="btn primary tg-start" href={`https://t.me/${info.username}`} target="_blank" rel="noopener noreferrer">
              Buka di Telegram
            </a>
          )}
          <p>Kirim pesan ke bot ini dan {bot.name} akan menjawab. Percakapannya juga muncul di Riwayat chat {bot.name}, ditandai Telegram.</p>
          <PeopleSection slug={bot.id} allowed={info.allowed} pending={info.pending} admin={admin} onChanged={async () => await fetchInfo(true)} />
          <hr className="tg-rule" />
          {askDisconnect ? (
            <div className="tg-disconnect" role="alert">
              <p>Putuskan Telegram dari {bot.name}? Bot-nya tetap ada di Telegram, tetapi berhenti menjawab.</p>
              <span className="confirm-actions">
                <button className="btn danger" disabled={busy === 'disconnect'} onClick={() => void disconnect()}>
                  {busy === 'disconnect' ? 'Memutuskan…' : 'Putuskan'}
                </button>
                <button className="btn quiet-btn" onClick={() => setAskDisconnect(false)}>
                  Batal
                </button>
              </span>
            </div>
          ) : (
            <button className="btn soft tg-start" type="button" onClick={() => setAskDisconnect(true)}>
              Putuskan Telegram
            </button>
          )}
          {problem && (
            <p className="problem-bar" role="alert">
              {problem}
            </p>
          )}
        </>
      )}

      {state === 'ok' && status === 'error' && (
        <>
          <p className="problem-bar" role="alert">
            {info?.error || 'Bot tidak bisa dipakai lagi. Hubungkan ulang.'}
          </p>
          <div className="tg-actions">
            <button className="btn primary" type="button" disabled={busy === 'start'} onClick={() => void start()}>
              {busy === 'start' ? 'Menyiapkan…' : 'Hubungkan ulang'}
            </button>
            {!askDisconnect && (
              <button className="btn link" type="button" onClick={() => setAskDisconnect(true)}>
                Putuskan
              </button>
            )}
          </div>
          {askDisconnect && (
            <div className="tg-disconnect" role="alert">
              <p>Putuskan Telegram dari {bot.name}? Bot-nya tetap ada di Telegram, tetapi berhenti menjawab.</p>
              <span className="confirm-actions">
                <button className="btn danger" disabled={busy === 'disconnect'} onClick={() => void disconnect()}>
                  {busy === 'disconnect' ? 'Memutuskan…' : 'Putuskan'}
                </button>
                <button className="btn quiet-btn" onClick={() => setAskDisconnect(false)}>
                  Batal
                </button>
              </span>
            </div>
          )}
          {problem && (
            <p className="problem-bar" role="alert">
              {problem}
            </p>
          )}
        </>
      )}
    </div>
  )
}
