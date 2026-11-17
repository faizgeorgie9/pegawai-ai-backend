import { useCallback, useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { api, errText } from './bff'
import { useAdminMode } from './adminMode'
import type { ConnProvider, Connection } from './bff'
import { go } from './router'
import { SourcePicker } from './pick-ui'
import { ErrorLine } from './ui'
import { CapChip, Loading, PageHead, useLoad } from './ui-extra'

// Real per-user connections (BFF: bff/connections.py). The state comes from the BFF; nothing here pretends to be connected.
type AppDef = { name: string; enables: string; where: string }
const APPS: Record<ConnProvider, AppDef> = {
  gdrive: {
    name: 'Google Drive',
    enables: 'Agen membaca berkas Drive setelah Anda menambahkannya ke Pengetahuan; agen tidak membuka Drive sendiri.',
    where: 'Halaman Pengetahuan dan lampiran chat.',
  },
  gmail: {
    name: 'Gmail',
    enables: 'Simpan jawaban agen sebagai draf di Gmail Anda; email tidak pernah dikirim otomatis.',
    where: 'Tombol "Simpan sebagai draf Gmail" di bawah jawaban agen.',
  },
  notion: {
    name: 'Notion',
    enables: 'Simpan halaman Notion yang Anda bagikan ke Pengetahuan, seperti berkas biasa.',
    where: 'Halaman Pengetahuan.',
  },
}
const GROUPS: { id: string; title: string; note: string; apps: ConnProvider[] }[] = [
  { id: 'google', title: 'Google Workspace', note: 'Satu akun Google, dua izin terpisah.', apps: ['gdrive', 'gmail'] },
  { id: 'notion', title: 'Notion', note: 'Hanya halaman yang Anda bagikan yang bisa dibaca.', apps: ['notion'] },
]
const SOON = [
  { id: 'whatsapp', name: 'WhatsApp', text: 'Ngobrol dengan agen lewat WhatsApp.' },
  { id: 'telegram', name: 'Telegram', text: 'Ngobrol dengan agen lewat Telegram.' },
]

const WHY: Record<string, string> = {
  denied: 'Izin tidak diberikan, jadi akun belum tersambung.',
  state: 'Permintaan sambungan sudah kedaluwarsa atau tidak dikenal. Coba hubungkan lagi.',
  exchange: 'Sambungan tidak diterima. Coba lagi; jika terus gagal, hubungi admin Anda.',
  scope: 'Izin yang diperlukan tidak dicentang. Hubungkan lagi dan centang semua izin yang diminta.',
}

// The BFF sends the browser back to #/aplikasi?connect=ok|error&app=...&reason=... after the provider's consent page.
function readResult(): { ok: boolean; text: string } | null {
  const q = new URLSearchParams(location.hash.split('?')[1] ?? '')
  const c = q.get('connect')
  if (c !== 'ok' && c !== 'error') return null
  const app = APPS[q.get('app') as ConnProvider] as AppDef | undefined
  if (c === 'ok') return { ok: true, text: `${app?.name ?? 'Aplikasi'} tersambung.` }
  return { ok: false, text: `${app ? `${app.name} belum tersambung. ` : ''}${WHY[q.get('reason') ?? ''] ?? 'Sambungan gagal. Coba lagi.'}` }
}

// Old links (#/tools?connect=..., from before the Aplikasi page existed) are forwarded with their query.
export function forwardOldConnectLink() {
  const q = location.hash.split('?')[1]
  if (q && new URLSearchParams(q).has('connect')) go(`/aplikasi?${q}`, true)
}

export function useConnections() {
  const fn = useCallback(() => api.connections(), [])
  return useLoad(fn)
}

// Marks drawn here in each product's colours (simple shapes, not the official artwork).
function Mark({ id }: { id: string }) {
  const p = { width: 28, height: 28, viewBox: '0 0 32 32', 'aria-hidden': true } as const
  if (id === 'gdrive')
    return (
      <svg {...p}>
        <path d="M11 4h10l10 17H21z" fill="#f4b400" />
        <path d="M11 4 1 21l5 8 10-17z" fill="#0f9d58" />
        <path d="M6 29h20l5-8H11z" fill="#4285f4" />
      </svg>
    )
  if (id === 'gmail')
    return (
      <svg {...p}>
        <rect x="2" y="6" width="28" height="20" rx="3" fill="#fff" />
        <path d="M2 9v14a3 3 0 0 0 3 3h3V13zM30 9v14a3 3 0 0 1-3 3h-3V13z" fill="#4285f4" />
        <path d="m2 9 14 11L30 9l-1-2a3 3 0 0 0-3-1H6a3 3 0 0 0-3 1z" fill="#ea4335" />
        <path d="m8 13 8 6 8-6v-3l-8 6-8-6z" fill="#c5221f" />
      </svg>
    )
  if (id === 'notion')
    return (
      <svg {...p}>
        <rect x="4" y="3" width="24" height="26" rx="4" fill="#fff" stroke="#15171c" strokeWidth="1.8" />
        <path d="M11 22V10l10 12V10" fill="none" stroke="#15171c" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    )
  if (id === 'whatsapp')
    return (
      <svg {...p}>
        <path d="M16 3a13 13 0 0 0-11 19.7L3 29l6.5-2A13 13 0 1 0 16 3z" fill="#25d366" />
        <path d="M11.5 10c.5 4.8 4.2 8.5 9 9l1.8-2.2-2.8-1.4-1.2 1c-1.6-.6-3-2-3.6-3.6l1-1.2L13.3 8z" fill="#fff" />
      </svg>
    )
  return (
    <svg {...p}>
      <circle cx="16" cy="16" r="13" fill="#2aabee" />
      <path d="m7.5 15.5 15.500-6-2.600 12.500-4.400-3.200-2.300 2.200-.4-4.400 6.600-5.600-8.200 4.600z" fill="#fff" />
    </svg>
  )
}

// Only "filled or not" per value, from the BFF. Never a secret, never whether it is correct.
function AdminHint({ c }: { c: Connection }) {
  const missing = c.setup.filter((s) => !s.filled).length
  return (
    <details className="app-admin">
      <summary>Petunjuk untuk admin</summary>
      <div className="app-admin-in">
        <p>
          {missing > 0
            ? `${c.name} belum bisa disambungkan. Isi ${missing} nilai yang belum terisi di file bff/.env, lalu jalankan ulang BFF.`
            : `Semua nilai ${c.name} sudah terisi.`}
        </p>
        <ul className="app-setup">
          {c.setup.map((s) => (
            <li key={s.env} data-filled={s.filled}>
              <span>
                {s.label} <code>{s.env}</code>
              </span>
              <span className={`pill ${s.filled ? 'cap-ok' : 'cap-mock'}`}>{s.filled ? 'Terisi' : 'Belum diisi'}</span>
            </li>
          ))}
        </ul>
        <p>Daftarkan alamat ini sebagai redirect URI di layanan penyedia, ditempel persis:</p>
        <p>
          <code className="app-uri">{c.redirect_uri}</code>
        </p>
        <p className="quiet small">Langkah lengkapnya ada di panduan docs/sprint4/setup-koneksi.md. Nilai rahasia tidak pernah ditampilkan di sini.</p>
      </div>
    </details>
  )
}

export function AppsPage() {
  const conns = useConnections()
  const admin = useAdminMode()
  const [result] = useState(readResult)
  const [problem, setProblem] = useState('')
  const [busy, setBusy] = useState<ConnProvider | null>(null)
  const [asking, setAsking] = useState<ConnProvider | null>(null)
  const [picker, setPicker] = useState<'gdrive' | 'notion' | null>(null)
  const [saved, setSaved] = useState('')
  const [how, setHow] = useState(false)
  useEffect(() => {
    if (result) go('/aplikasi', true) // drop the flag so a refresh does not show the banner again
  }, [result])

  async function connect(p: ConnProvider) {
    setBusy(p)
    setProblem('')
    try {
      window.location.assign((await api.connectStart(p)).url)
    } catch (e) {
      setProblem(errText(e))
      setBusy(null)
    }
  }
  async function disconnect(p: ConnProvider) {
    setBusy(p)
    setProblem('')
    setAsking(null)
    try {
      await api.disconnect(p)
      conns.retry()
    } catch (e) {
      setProblem(errText(e))
    }
    setBusy(null)
  }

  async function recheck(id: ConnProvider) {
    setBusy(id)
    try {
      await api.connections(true) // bypass the 60 s cache, then reload the list (served from the fresh cache)
    } catch {
      /* the reload below shows the error */
    }
    conns.retry()
    setBusy(null)
  }

  const by = new Map<string, Connection>((conns.data ?? []).map((c) => [c.provider, c]))

  function row(id: ConnProvider) {
    const a = APPS[id]
    const c = by.get(id)
    if (!c) return null
    const status = c.status
    const soon = status === 'not_configured' && !admin // not set up by the admin: users only see "Segera hadir"
    const mustAsk = status === 'broken' && c.needs === 'admin'
    return (
      <li key={id} className="app-row" data-app={id} data-s={status}>
        <div className="app-mark">
          <Mark id={id} />
        </div>
        <div className="app-body">
          <div className="app-top">
            <h3>{a.name}</h3>
            {status === 'connected' && <CapChip cap="ok" label="Tersambung" />}
            {status === 'reconnect' && <CapChip cap="mock" label="Perlu disambungkan ulang" />}
            {status === 'broken' && <CapChip cap="mock" label="Perlu perbaikan" />}
            {status === 'disconnected' && <CapChip cap="unknown" label="Belum tersambung" />}
            {status === 'not_configured' && <CapChip cap="none" label={soon ? 'Segera hadir' : 'Belum diatur admin'} />}
          </div>
          <p>{a.enables}</p>
          <p className="quiet small">
            <b>Dipakai di:</b> {a.where}
          </p>
          {status === 'connected' && c.account && (
            <p className="connect-acct">
              Tersambung sebagai <b>{c.account}</b>
            </p>
          )}
          {status === 'reconnect' && <p className="connect-warn">Izin akses sudah tidak berlaku. Hubungkan ulang agar bisa dipakai lagi.</p>}
          {status === 'broken' && (
            <p className="connect-warn" role="status">
              {c.reason ?? `${a.name} sedang bermasalah.`}
            </p>
          )}
          {status === 'not_configured' && admin && (
            <p className="quiet small" id={`why-${id}`}>
              Administrator belum mengatur {a.name}, jadi belum bisa disambungkan.
            </p>
          )}
          {id === 'gmail' && how && (
            <p className="note-box" id="how-gmail">
              Di bawah setiap jawaban agen ada tombol &ldquo;Simpan sebagai draf Gmail&rdquo;. Anda bisa mengubah penerima, subjek, dan isinya dulu. Hasilnya hanya draf di Gmail Anda. Anda sendiri yang membuka dan mengirimnya.
            </p>
          )}
          {status === 'not_configured' && admin && <AdminHint c={c} />}
        </div>
        <div className="app-act">
          {asking === id ? (
            <span className="confirm-actions" role="alert">
              <span className="app-ask">Putuskan {a.name}?</span>
              <button type="button" className="btn danger" disabled={busy === id} onClick={() => void disconnect(id)}>
                Putuskan
              </button>
              <button type="button" className="btn quiet-btn" onClick={() => setAsking(null)}>
                Batal
              </button>
            </span>
          ) : (
            <>
              {status === 'connected' ? (
                <button type="button" className="btn soft" disabled={busy === id} onClick={() => setAsking(id)}>
                  Putuskan
                </button>
              ) : soon ? null : status === 'broken' && c.needs !== 'reconnect' ? (
                <button type="button" className="btn primary" disabled={busy === id} onClick={() => void recheck(id)}>
                  {mustAsk ? 'Sudah diaktifkan? Periksa lagi' : 'Periksa lagi'}
                </button>
              ) : (
                <button
                  type="button"
                  className={`btn ${status === 'reconnect' || status === 'broken' ? 'primary' : 'soft'}`}
                  disabled={status === 'not_configured' || busy === id}
                  aria-describedby={status === 'not_configured' ? `why-${id}` : undefined}
                  onClick={() => void connect(id)}
                >
                  {status === 'reconnect' || status === 'broken' ? 'Sambungkan ulang' : 'Hubungkan'}
                </button>
              )}
              {(status === 'reconnect' || status === 'broken') && (
                <button type="button" className="btn link" disabled={busy === id} onClick={() => setAsking(id)}>
                  Putuskan
                </button>
              )}
              {status === 'connected' && id !== 'gmail' && (
                <button type="button" className="btn outline" onClick={() => setPicker(id as 'gdrive' | 'notion')}>
                  {id === 'gdrive' ? 'Pilih dari Drive' : 'Pilih dari Notion'}
                </button>
              )}
              {id === 'gmail' && (
                <button type="button" className="btn link" aria-expanded={how} aria-controls="how-gmail" onClick={() => setHow((v) => !v)}>
                  {how ? 'Sembunyikan cara kerja' : 'Cara kerja tombol draf'}
                </button>
              )}
            </>
          )}
        </div>
      </li>
    )
  }

  return (
    <section className="page apps">
      <PageHead title="Aplikasi" sub="Sambungkan akun Anda agar agen bisa memakai berkas dan email Anda sendiri. Anda yang memegang kendali: izin sekecil mungkin, dan bisa diputus kapan saja." />
      {result && (
        <p className={result.ok ? 'note-box connect-ok' : 'problem-bar'} role={result.ok ? 'status' : 'alert'}>
          {result.text}
        </p>
      )}
      {saved && (
        <p className="note-box connect-ok" role="status">
          {saved} <a href="#/pengetahuan">Lihat di Pengetahuan</a>
        </p>
      )}
      {problem && (
        <p className="problem-bar" role="alert">
          {problem}
        </p>
      )}
      {conns.state === 'loading' && !conns.data && <Loading text="Memuat sambungan..." shape="ledger" />}
      {conns.state === 'error' && !conns.data && <ErrorLine text={conns.error} onRetry={conns.retry} />}
      {conns.data &&
        GROUPS.map((g) => (
          <section key={g.id} className="apps-group" aria-labelledby={`g-${g.id}`}>
            <header>
              <h2 id={`g-${g.id}`}>{g.title}</h2>
              <p className="quiet small">{g.note}</p>
            </header>
            <ul className="apps-list">{g.apps.map(row)}</ul>
          </section>
        ))}
      <section className="apps-group" aria-labelledby="g-soon">
        <header>
          <h2 id="g-soon">Segera hadir</h2>
          <p className="quiet small">Saluran yang direncanakan. Belum bisa dipakai.</p>
        </header>
        <ul className="apps-list">
          {SOON.map((s) => (
            <li key={s.id} className="app-row soon" data-app={s.id}>
              <div className="app-mark">
                <Mark id={s.id} />
              </div>
              <div className="app-body">
                <div className="app-top">
                  <h3>{s.name}</h3>
                  <CapChip cap="none" label="Belum tersedia" />
                </div>
                <p>{s.text}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>
      {picker && createPortal(<SourcePicker provider={picker} onClose={() => setPicker(null)} onDone={(ok) => setSaved(`${ok.length} item disimpan ke Pengetahuan.`)} />, document.body)}
    </section>
  )
}

// Compact pointer on Kemampuan > Alat.
export function AppsLink() {
  return (
    <p className="apps-link">
      Menyambungkan Google Drive, Gmail, atau Notion? Buka <a href="#/aplikasi">Aplikasi</a>.
    </p>
  )
}
