import { useCallback, useEffect, useState } from 'react'
import { api, errText } from './bff'
import type { ConnProvider, Connection } from './bff'
import { go } from './router'
import { ErrorLine } from './ui'
import { CapChip, Loading, useLoad } from './ui-extra'

// Real per-user connections (BFF: bff/connections.py). The card state comes from the BFF; nothing here pretends to be connected.
const APPS: { id: ConnProvider; name: string; enables: string; where: string }[] = [
  {
    id: 'gdrive',
    name: 'Google Drive',
    enables: 'Pilih dokumen, spreadsheet, slide, atau PDF dari Drive Anda dan simpan ke Knowledge Base, tanpa harus dibagikan ke publik. Anda hanya memberi izin membaca.',
    where: 'Pengaturan > Knowledge base (Pilih dari Drive), menu lampiran di chat, dan link Drive pribadi yang Anda tempel di chat.',
  },
  {
    id: 'gmail',
    name: 'Gmail',
    enables: 'Simpan jawaban agen sebagai draf di Gmail Anda. Anda memberi izin membuat draf saja. Email tidak pernah dikirim otomatis.',
    where: 'Tombol "Simpan sebagai draf Gmail" di bawah jawaban agen, di chat dan di grup.',
  },
  {
    id: 'notion',
    name: 'Notion',
    enables: 'Pilih halaman Notion yang Anda bagikan ke aplikasi ini dan simpan ke Knowledge Base, seperti berkas biasa.',
    where: 'Pengaturan > Knowledge base (Pilih dari Notion).',
  },
]

const WHY: Record<string, string> = {
  denied: 'Izin tidak diberikan, jadi akun belum tersambung.',
  state: 'Permintaan sambungan sudah kedaluwarsa atau tidak dikenal. Coba hubungkan lagi.',
  exchange: 'Aplikasi tidak menerima sambungan ini. Coba lagi. Jika terus gagal, hubungi administrator.',
  scope: 'Izin yang diperlukan tidak dicentang. Hubungkan lagi dan centang semua izin yang diminta.',
}

// The BFF sends the browser back to #/tools?connect=ok|error&app=…&reason=… after the provider's consent page.
function readResult(): { ok: boolean; text: string } | null {
  const q = new URLSearchParams(location.hash.split('?')[1] ?? '')
  const c = q.get('connect')
  if (c !== 'ok' && c !== 'error') return null
  const app = APPS.find((a) => a.id === q.get('app'))
  if (c === 'ok') return { ok: true, text: `${app?.name ?? 'Aplikasi'} tersambung.` }
  return { ok: false, text: `${app ? `${app.name} belum tersambung. ` : ''}${WHY[q.get('reason') ?? ''] ?? 'Sambungan gagal. Coba lagi.'}` }
}

export function useConnections() {
  const fn = useCallback(() => api.connections(), [])
  return useLoad(fn)
}

export function ConnectApps() {
  const conns = useConnections()
  const [result] = useState(readResult)
  const [problem, setProblem] = useState('')
  const [busy, setBusy] = useState<ConnProvider | null>(null)
  useEffect(() => {
    if (result) go('/tools', true) // drop the flag so a refresh does not show the banner again
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
    try {
      await api.disconnect(p)
      conns.retry()
    } catch (e) {
      setProblem(errText(e))
    }
    setBusy(null)
  }

  const by = new Map<string, Connection>((conns.data ?? []).map((c) => [c.provider, c]))
  return (
    <section className="connect" id="hubungkan-aplikasi" aria-labelledby="connect-h">
      <header className="connect-head">
        <h2 id="connect-h">Hubungkan aplikasi</h2>
      </header>
      {result && (
        <p className={result.ok ? 'note-box connect-ok' : 'problem-bar'} role={result.ok ? 'status' : 'alert'}>
          {result.text}
        </p>
      )}
      {problem && (
        <p className="problem-bar" role="alert">
          {problem}
        </p>
      )}
      {conns.state === 'loading' && !conns.data && <Loading text="Memuat sambungan..." shape="lines" />}
      {conns.state === 'error' && !conns.data && <ErrorLine text={conns.error} onRetry={conns.retry} />}
      {conns.data && (
        <ul className="connect-grid">
          {APPS.map((a) => {
            const c = by.get(a.id)
            const status = c?.status ?? 'disconnected'
            return (
              <li key={a.id} className="connect-card" data-app={a.id} data-s={status}>
                <div className="connect-top">
                  <b>{a.name}</b>
                  {status === 'connected' && <CapChip cap="ok" label="Tersambung" />}
                  {status === 'reconnect' && <CapChip cap="blocked" label="Perlu disambungkan ulang" />}
                  {status === 'disconnected' && <CapChip cap="unknown" label="Belum tersambung" />}
                  {status === 'not_configured' && <CapChip cap="none" label="Belum diatur admin" />}
                </div>
                <p>{a.enables}</p>
                <p className="quiet small">
                  <b>Dipakai di:</b> {a.where}
                </p>
                {status === 'connected' && c?.account && (
                  <p className="connect-acct">
                    Tersambung sebagai <b>{c.account}</b>
                  </p>
                )}
                {status === 'reconnect' && <p className="connect-warn">Izin akses sudah tidak berlaku. Hubungkan ulang agar bisa dipakai lagi.</p>}
                {status === 'not_configured' && (
                  <p className="quiet small" id={`why-${a.id}`}>
                    Administrator belum mengatur {a.name}, jadi belum bisa disambungkan.
                  </p>
                )}
                <div className="connect-act">
                  {status === 'connected' ? (
                    <button type="button" className="btn soft" disabled={busy === a.id} onClick={() => void disconnect(a.id)}>
                      Putuskan
                    </button>
                  ) : (
                    <button
                      type="button"
                      className={`btn ${status === 'reconnect' ? 'primary' : 'soft'}`}
                      disabled={status === 'not_configured' || busy === a.id}
                      aria-describedby={status === 'not_configured' ? `why-${a.id}` : undefined}
                      onClick={() => void connect(a.id)}
                    >
                      {status === 'reconnect' ? 'Hubungkan ulang' : 'Hubungkan'}
                    </button>
                  )}
                  {status === 'reconnect' && (
                    <button type="button" className="btn link" disabled={busy === a.id} onClick={() => void disconnect(a.id)}>
                      Putuskan
                    </button>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
