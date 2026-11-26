import { useCallback, useState } from 'react'
import { api, canWhatsApp, errText } from './bff'
import type { Bot, WhatsAppSimulateResult, WhatsAppStatus } from './bff'
import { useAdminMode } from './adminMode'
import { useData } from './data'
import { useHandoverQueue } from './handover'
import { agenPath } from './router'
import { CHEVRON, ErrorLine, Icon, nf } from './ui'
import { CapChip, Loading, useLoad } from './ui-extra'
import './whatsapp.css'

// Item 2: only customer-service employees answer WhatsApp. The tab, the Ringkasan row and the Aplikasi
// card all read the one BFF status; nothing here pretends a channel is connected before the BFF says so.

// "Connected" means the channel works: ready plus either a number or a registered token (K2, P4).
const isConnected = (s: WhatsAppStatus) => s.status === 'ready' && (!!s.number || s.api_token_configured)

// The simulate answer repeats an English server status; admins read the plain Indonesian word.
const SIM_STATUS: Record<string, string> = {
  replied: 'Sudah dijawab pegawai AI',
  needs_human: 'Diteruskan ke manusia',
  escalated: 'Diteruskan ke pegawai senior',
}

// WhatsApp mark, the same shape as the one in connections.tsx (that one is private to the page).
function WhatsAppMark() {
  return (
    <svg width={28} height={28} viewBox="0 0 32 32" aria-hidden="true">
      <path d="M16 3a13 13 0 0 0-11 19.7L3 29l6.5-2A13 13 0 1 0 16 3z" fill="#25d366" />
      <path d="M11.5 10c.5 4.8 4.2 8.5 9 9l1.8-2.2-2.8-1.4-1.2 1c-1.6-.6-3-2-3.6-3.6l1-1.2L13.3 8z" fill="#fff" />
    </svg>
  )
}

// The Ringkasan row: a live status line that opens the WhatsApp tab. Only customer-service employees
// get the control; everyone else gets one honest sentence and no button.
export function WhatsAppRow({ bot, onOpen }: { bot: Bot; onOpen: () => void }) {
  if (!canWhatsApp(bot))
    return (
      <li>
        <b>WhatsApp</b>
        <small className="quiet small">Hanya untuk pegawai layanan pelanggan. {bot.name} tidak menjawab pelanggan di WhatsApp.</small>
      </li>
    )
  return <WhatsAppRowButton onOpen={onOpen} />
}

function WhatsAppRowButton({ onOpen }: { onOpen: () => void }) {
  const fn = useCallback(() => api.whatsappStatus(), [])
  const wa = useLoad(fn)
  const st = wa.state === 'ok' ? wa.data : undefined
  const value = !st
    ? wa.state === 'error'
      ? 'Belum diketahui'
      : 'Memeriksa…'
    : isConnected(st)
      ? 'Siap'
      : st.status === 'error'
        ? 'Bermasalah'
        : 'Belum tersambung'
  return (
    <li>
      <button type="button" className="wa-row" onClick={onOpen}>
        <b>WhatsApp</b>
        <span className="quiet small">{value}</span>
        <span className="wa-row-chev" aria-hidden="true">
          <Icon d={CHEVRON} size={14} />
        </span>
      </button>
    </li>
  )
}

// The tab itself: status, who answers, where the hard questions go, and (admin only) the address the
// provider has to call plus one test message. No per-agent role switch in v1: this screen only reads.
export function WhatsAppTab({ bot }: { bot: Bot }) {
  const { bots } = useData()
  const admin = useAdminMode()
  const hv = useHandoverQueue()
  const fn = useCallback(() => api.whatsappStatus(), [])
  const wa = useLoad(fn)
  const st = wa.state === 'ok' ? wa.data : undefined
  const connected = st ? isConnected(st) : false
  const agents = st?.agents ?? []
  const listed = agents.some((a) => a.bot_id === bot.id)

  return (
    <div className="cbox wa">
      <div className="wa-head">
        <h2>WhatsApp</h2>
        {st && (
          <span className={`pill ${connected ? 'ok' : st.status === 'error' ? 'bad' : 'idle'}`}>
            {connected ? 'Siap menerima pesan' : st.status === 'error' ? 'Bermasalah' : 'Belum tersambung'}
          </span>
        )}
      </div>

      {wa.state === 'loading' && <Loading text="Memuat WhatsApp..." shape="lines" />}
      {wa.state === 'error' && <ErrorLine text={wa.error} onRetry={wa.retry} />}

      {st && (
        <>
          {connected ? (
            <p>
              Pelanggan yang mengirim pesan {st.number ? `ke nomor ${st.number} ` : ''}dijawab oleh pegawai layanan pelanggan. Pertanyaan yang sulit diteruskan ke manusia.
            </p>
          ) : st.status === 'error' ? (
            <div className="problem-bar" role="alert">
              <p>WhatsApp terputus. Hubungi tim teknis Anda untuk menyambungkan ulang.</p>
              <button type="button" className="btn link" onClick={wa.retry}>
                Coba lagi
              </button>
            </div>
          ) : (
            <p>
              {admin
                ? 'WhatsApp belum tersambung. Lihat Petunjuk untuk admin di bawah untuk menyambungkannya.'
                : 'WhatsApp belum tersambung. Minta pemilik akun menyambungkannya.'}
            </p>
          )}

          <h3>Tugas {bot.name} di WhatsApp</h3>
          {agents.length > 0 && listed ? (
            <ul className="perm-list">
              {agents.map((a) => {
                const name = bots.find((x) => x.id === a.bot_id)?.name || a.bot_id
                return (
                  <li key={`${a.role}:${a.bot_id}`}>
                    <span>
                      {a.role === 'primary' ? 'Penjawab pertama: ' : 'Menangani kasus sulit: '}
                      {a.bot_id === bot.id ? <b>{name}</b> : name}
                    </span>
                  </li>
                )
              })}
            </ul>
          ) : (
            <p className="quiet small">{bot.name} belum ditugaskan menjawab di WhatsApp.</p>
          )}

          <div className="note-box">
            <p>Bila pelanggan minta bicara dengan manusia, pegawai AI berhenti menjawab dan Anda diberi tahu. Anda bisa mengambil alih, lalu mengembalikannya.</p>
          </div>
          {hv.ready && (
            <p className="quiet small num">
              {nf.format(hv.counts.needs_human)} perlu manusia · {nf.format(hv.counts.human)} diambil alih
            </p>
          )}
          <a className="btn soft" href="#/pelanggan">
            Buka Pelanggan
          </a>

          {admin && <AdminHint status={st} bot={bot} />}
        </>
      )}
    </div>
  )
}

// Admin only: the address the WhatsApp provider has to be pointed at, and one example message to prove
// the routing works. Errors from the BFF (e.g. this employee may not answer WhatsApp) are shown as sent.
function AdminHint({ status, bot }: { status: WhatsAppStatus; bot: Bot }) {
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const [result, setResult] = useState<WhatsAppSimulateResult | null>(null)

  async function send(e: React.FormEvent) {
    e.preventDefault()
    if (!message.trim() || busy) return
    setBusy(true)
    setProblem('')
    setResult(null)
    try {
      setResult(await api.whatsappSimulate({ message: message.trim(), bot_id: bot.id }))
    } catch (err) {
      setProblem(errText(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <details className="app-admin">
      <summary>Petunjuk untuk admin</summary>
      <div className="app-admin-in">
        <p>Alamat penerima pesan WhatsApp (daftarkan persis di layanan penyedia):</p>
        <p>
          <code className="app-uri">{status.webhook_url || 'Belum tersedia'}</code>
        </p>
        <form className="wa-test" onSubmit={(e) => void send(e)}>
          <label className="field">
            <span>Pesan pelanggan contoh</span>
            <textarea rows={3} maxLength={500} value={message} disabled={busy} onChange={(e) => setMessage(e.target.value)} />
          </label>
          <button type="submit" className="btn outline" disabled={busy || !message.trim()}>
            {busy ? 'Mengirim…' : 'Kirim pesan uji'}
          </button>
          {problem && (
            <p className="problem-bar" role="alert">
              {problem}
            </p>
          )}
        </form>
        {result && (
          <div className="note-box">
            <p>
              Balasan {result.bot_name}: {result.reply}
            </p>
            <p>
              <small>Status: {SIM_STATUS[result.status] ?? result.status}</small>
            </p>
          </div>
        )}
      </div>
    </details>
  )
}

// The Aplikasi card: one card for the whole account, only while a customer-service employee exists.
// It neither connects nor disconnects; it points an owner at the employee that answers WhatsApp.
export function WhatsAppAppCard() {
  const { bots } = useData()
  const admin = useAdminMode()
  const fn = useCallback(() => api.whatsappStatus(), [])
  const wa = useLoad(fn)
  const first = bots.find(canWhatsApp)
  if (!first) return null
  const st = wa.state === 'ok' ? wa.data : undefined
  const connected = st ? isConnected(st) : false
  return (
    <li className="app-card app-mini" data-app="whatsapp" data-s={st ? (connected ? 'connected' : 'disconnected') : 'unknown'}>
      <div className="app-card-head">
        <div className="app-mark">
          <WhatsAppMark />
        </div>
        <div className="app-top">
          <h3>WhatsApp</h3>
          {st && (connected ? <CapChip cap="ok" label="Siap" /> : st.status === 'error' ? <CapChip cap="mock" label="Perlu perbaikan" /> : <CapChip cap="none" label="Belum tersambung" />)}
        </div>
      </div>
      <p>Pelanggan chat ke nomor bisnis Anda dan dijawab oleh pegawai layanan pelanggan.</p>
      {admin ? (
        <div className="app-card-act">
          <a className="btn soft" href={'#' + agenPath(first.id) + '?tab=whatsapp'}>
            Atur di {first.name}
          </a>
        </div>
      ) : (
        <p className="quiet small">Diatur oleh pemilik akun.</p>
      )}
    </li>
  )
}
