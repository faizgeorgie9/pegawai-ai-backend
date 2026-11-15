import { useEffect, useState } from 'react'
import { api, errText } from './bff'
import type { ConnProvider, ImportResult, PickItem } from './bff'
import { useConnections } from './connections'
import { Dialog, ErrorLine } from './ui'
import { Loading } from './ui-extra'

// One picker for Google Drive files and Notion pages: search, tick, import into the Knowledge Base (BFF does the reading).
const COPY = {
  gdrive: { name: 'Google Drive', title: 'Pilih dari Drive', search: 'Cari nama berkas', what: 'berkas' },
  notion: { name: 'Notion', title: 'Pilih dari Notion', search: 'Cari judul halaman', what: 'halaman' },
} as const

const day = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' }) : '')
const size = (n: number | null) => (n == null ? '' : n < 1024 * 1024 ? `${Math.max(1, Math.round(n / 1024))} KB` : `${(n / 1024 / 1024).toFixed(1)} MB`)

export function SourcePicker({ provider, onClose, onDone }: { provider: Extract<ConnProvider, 'gdrive' | 'notion'>; onClose: () => void; onDone: (ok: ImportResult[]) => void }) {
  const t = COPY[provider]
  const conns = useConnections()
  const status = conns.data?.find((c) => c.provider === provider)?.status
  const [q, setQ] = useState('')
  const [term, setTerm] = useState('')
  const [items, setItems] = useState<PickItem[]>([])
  const [next, setNext] = useState<string | null>(null)
  const [load, setLoad] = useState<'idle' | 'loading' | 'error'>('idle')
  const [error, setError] = useState('')
  const [pick, setPick] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [failed, setFailed] = useState<ImportResult[]>([])

  async function fetchPage(search: string, cursor: string | null) {
    setLoad('loading')
    setError('')
    try {
      const r = await (provider === 'gdrive' ? api.driveFiles(search, cursor) : api.notionPages(search, cursor))
      setItems((cur) => (cursor ? [...cur, ...r.items] : r.items))
      setNext(r.next)
      setLoad('idle')
    } catch (e) {
      setError(errText(e))
      setLoad('error')
    }
  }
  useEffect(() => {
    if (status === 'connected') void fetchPage(term, null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, term])

  async function doImport() {
    setBusy(true)
    setFailed([])
    try {
      const res = await (provider === 'gdrive' ? api.driveImport(pick) : api.notionImport(pick))
      const bad = res.filter((r) => r.status === 'failed')
      const ok = res.filter((r) => r.status === 'ready')
      if (ok.length) onDone(ok)
      if (bad.length) {
        setFailed(bad.map((b) => ({ ...b, name: items.find((x) => x.id === b.name)?.name ?? b.name }))) // failed results carry the source id
        setPick([])
      } else onClose()
    } catch (e) {
      setError(errText(e))
      setLoad('error')
    }
    setBusy(false)
  }
  const toggle = (id: string) => setPick((cur) => (cur.includes(id) ? cur.filter((x) => x !== id) : cur.length >= 10 ? cur : [...cur, id]))

  return (
    <Dialog title={t.title} onClose={onClose} wide>
      <div className="dlg-body src-picker">
        {conns.state === 'loading' && !conns.data && <Loading text="Memeriksa sambungan..." shape="lines" />}
        {conns.state === 'error' && !conns.data && <ErrorLine text={conns.error} onRetry={conns.retry} />}
        {status && status !== 'connected' && (
          <div className="state" role="status">
            <p>
              {status === 'not_configured' && `${t.name} belum diatur oleh administrator.`}
              {status === 'disconnected' && `${t.name} belum tersambung.`}
              {status === 'reconnect' && `Sambungan ${t.name} perlu disambungkan ulang.`}
            </p>
            {status !== 'not_configured' && (
              <a className="btn soft" href="#/tools">
                Buka Hubungkan aplikasi
              </a>
            )}
          </div>
        )}
        {status === 'connected' && (
          <>
            <form
              className="set-inline"
              role="search"
              onSubmit={(e) => {
                e.preventDefault()
                setTerm(q.trim())
                setPick([])
              }}
            >
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t.search} aria-label={t.search} />
              <button className="btn outline" type="submit" disabled={load === 'loading'}>
                Cari
              </button>
            </form>
            {load === 'error' && <ErrorLine text={error} onRetry={() => void fetchPage(term, null)} />}
            {load === 'loading' && !items.length && <Loading text={`Memuat ${t.what}...`} shape="lines" />}
            {load !== 'loading' && load !== 'error' && !items.length && (
              <p className="quiet">
                {term ? `Tidak ada ${t.what} yang cocok dengan "${term}".` : provider === 'notion' ? 'Belum ada halaman yang dibagikan ke aplikasi ini. Di Notion, buka halaman lalu pilih Hubungkan ke aplikasi ini.' : 'Belum ada berkas yang bisa dipilih.'}
              </p>
            )}
            {items.length > 0 && (
              <ul className="src-list" aria-label={`Daftar ${t.what}`}>
                {items.map((i) => (
                  <li key={i.id}>
                    <label className="src-row">
                      <input type="checkbox" checked={pick.includes(i.id)} onChange={() => toggle(i.id)} disabled={busy} />
                      <span className="src-text">
                        <b className="src-name">{i.name}</b>
                        <span className="meta">{[i.type, size(i.size), day(i.modified) && `diubah ${day(i.modified)}`].filter(Boolean).join(' · ')}</span>
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            )}
            {next && (
              <button className="btn soft" type="button" disabled={load === 'loading'} onClick={() => void fetchPage(term, next)}>
                {load === 'loading' ? 'Memuat...' : 'Tampilkan lebih banyak'}
              </button>
            )}
          </>
        )}
        {failed.length > 0 && (
          <div className="problem-bar small" role="alert">
            {failed.map((f, n) => (
              <p key={n}>
                {f.name}: {f.error ?? 'gagal disimpan.'}
              </p>
            ))}
          </div>
        )}
        <div className="dlg-foot">
          <button className="btn quiet-btn" type="button" onClick={onClose}>
            Tutup
          </button>
          {status === 'connected' && (
            <button className="btn primary" type="button" disabled={!pick.length || busy} onClick={() => void doImport()}>
              {busy ? 'Menyimpan...' : pick.length ? `Simpan ${pick.length} ke Knowledge Base` : 'Simpan ke Knowledge Base'}
            </button>
          )}
        </div>
        {status === 'connected' && <p className="meta">Maksimal 10 item sekali simpan. Ukuran dan jenis berkas sama seperti unggahan biasa.</p>}
      </div>
    </Dialog>
  )
}
