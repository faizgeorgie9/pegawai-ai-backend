import { useCallback, useRef, useState } from 'react'
import { api, errText } from './bff'
import type { KbItem } from './bff'
import { useAdminMode } from './adminMode'
import { SourcePicker } from './pick-ui'
import { DriveLink, KB_ACCEPT, KB_KIND, KB_TYPES_TEXT, KbPreview, bytes, needsDrive } from './kb-ui'
import { ErrorLine } from './ui'
import { Loading, PageHead, useLoad } from './ui-extra'

// #/pengetahuan: what the business teaches its agents (files and links). Same list the chat attachment feeds.
const STATUS_TEXT = { processing: 'Memproses', ready: 'Tersimpan', failed: 'Gagal' } as const
const dayOf = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' }) : '–')

// The user's own sources (files and links added here or from the chat). The BFF keeps them per user and gives the best
// matching excerpts to every agent, citing the source name.
export function MySources() {
  const [n, setN] = useState(0)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const fn = useCallback(() => api.kbItems(), [n])
  const items = useLoad(fn)
  const file = useRef<HTMLInputElement>(null)
  const [url, setUrl] = useState('')
  const [busy, setBusy] = useState('')
  const [problem, setProblem] = useState('')
  const [asking, setAsking] = useState<string | null>(null)
  const [picker, setPicker] = useState<'gdrive' | null>(null)
  const [refreshing, setRefreshing] = useState<string | null>(null)
  const [viewing, setViewing] = useState<KbItem | null>(null)
  async function add(label: string, work: () => Promise<KbItem>) {
    setBusy(label)
    setProblem('')
    try {
      const i = await work()
      if (i.status === 'failed') setProblem(`${i.source ?? i.name}: ${i.error ?? 'gagal diproses.'}`)
      else if (i.kind !== 'file') setUrl('')
    } catch (e) {
      setProblem(errText(e))
    }
    setBusy('')
    setN((x) => x + 1)
  }
  // One file after another (keeps server load low); every failure is listed, the rest still upload.
  async function addMany(files: File[]) {
    setProblem('')
    const bad: string[] = []
    for (const [i, f] of files.entries()) {
      setBusy(files.length > 1 ? `${f.name} (${i + 1} dari ${files.length})` : f.name)
      try {
        const r = await api.kbUpload(f)
        if (r.status === 'failed') bad.push(`${f.name}: ${r.error ?? 'gagal diproses.'}`)
      } catch (e) {
        bad.push(`${f.name}: ${errText(e)}`)
      }
      setN((x) => x + 1)
    }
    setBusy('')
    setProblem(bad.join(' · '))
  }
  async function refresh(id: string) {
    setRefreshing(id)
    setProblem('')
    try {
      await api.kbRefresh(id)
    } catch (e) {
      setProblem(errText(e))
    }
    setRefreshing(null)
    setN((x) => x + 1)
  }
  async function remove(id: string) {
    try {
      await api.kbDelete(id)
    } catch (e) {
      setProblem(errText(e))
    }
    setAsking(null)
    setN((x) => x + 1)
  }
  return (
    <div className="kb-sec">
      <h2>Sumber milik Anda</h2>
      <p className="quiet">Semua agen Anda memakai berkas dan link ini, dan menyebut sumbernya.</p>
      <div className="kb-add">
        <input
          ref={file}
          type="file"
          hidden
          multiple
          accept={KB_ACCEPT}
          aria-label="Pilih berkas"
          onChange={(e) => {
            const fs = Array.from(e.target.files ?? [])
            e.target.value = ''
            if (fs.length) void addMany(fs)
          }}
        />
        <button className="btn outline" disabled={!!busy} onClick={() => file.current?.click()}>
          Unggah berkas
        </button>
        <button className="btn outline" disabled={!!busy} onClick={() => setPicker('gdrive')}>
          Pilih dari Drive
        </button>
        <form
          className="set-inline"
          onSubmit={(e) => {
            e.preventDefault()
            if (url.trim()) void add(url.trim(), () => api.kbAddLink(url.trim()))
          }}
        >
          <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://… (website atau Google Drive)" aria-label="Alamat web atau link Google Drive" inputMode="url" />
          <button className="btn outline" type="submit" disabled={!!busy || !url.trim()}>
            Tambah link
          </button>
        </form>
      </div>
      <p className="meta">
        Berkas: {KB_TYPES_TEXT}. Drive pribadi perlu disambungkan dulu di <a href="#/aplikasi">Aplikasi</a>.
      </p>
      {problem && (
        <p className="problem-bar small" role="alert">
          {problem}
          {needsDrive(problem) && <DriveLink />}
        </p>
      )}
      {items.state === 'loading' && !items.data && <Loading text="Memuat sumber..." shape="lines" />}
      {items.state === 'error' && !items.data && <ErrorLine text={items.error} onRetry={items.retry} />}
      {busy && (
        <div className="kb-row" data-s="processing" aria-live="polite">
          <span className="pill cap-mock">Memproses</span>
          <b className="kb-rname">{busy}</b>
        </div>
      )}
      {items.data?.length === 0 && !busy && (
        <div className="kb-empty">
          <b>Belum ada pengetahuan.</b>
          <p className="quiet">Unggah berkas atau tempel link di atas.</p>
        </div>
      )}
      <ul className="kb-list">
        {items.data?.map((i) => (
          <li key={i.id} className="kb-row" data-s={i.status}>
            <span className="pill">{KB_KIND[i.kind]}</span>
            <div className="kb-rtext">
              {i.status === 'ready' && i.id ? (
                <button className="kb-rname kb-open" onClick={() => setViewing(i)}>
                  {i.name}
                </button>
              ) : (
                <b className="kb-rname">{i.name}</b>
              )}
              {i.source && <span className="meta kb-src">{i.source}</span>}
              <span className="meta">
                {[i.size_bytes != null && bytes(i.size_bytes), dayOf(i.created_at)].filter(Boolean).join(' · ')}
              </span>
              {i.status === 'failed' && <span className="meta bad kb-why">{i.error}</span>}
            </div>
            <span className={`pill ${i.status === 'ready' ? 'cap-ok' : i.status === 'failed' ? 'cap-blocked' : 'cap-mock'}`}>{STATUS_TEXT[i.status]}</span>
            {i.status === 'ready' && i.id && (
              <button className="btn quiet-btn sm" aria-label={`Lihat ${i.name}`} onClick={() => setViewing(i)}>
                Lihat
              </button>
            )}
            {i.refreshable && asking !== i.id && (
              <button className="btn quiet-btn sm" disabled={refreshing === i.id} aria-label={`Perbarui ${i.name} dari ${KB_KIND[i.kind]}`} onClick={() => void refresh(i.id as string)}>
                {refreshing === i.id ? 'Memperbarui...' : 'Perbarui'}
              </button>
            )}
            {asking === i.id ? (
              <span className="confirm-actions" role="alert">
                <button className="btn danger sm" onClick={() => void remove(i.id as string)}>
                  Hapus
                </button>
                <button className="btn quiet-btn sm" onClick={() => setAsking(null)}>
                  Batal
                </button>
              </span>
            ) : (
              <button className="btn quiet-btn danger-text sm" aria-label={`Hapus ${i.name}`} onClick={() => setAsking(i.id)}>
                Hapus
              </button>
            )}
          </li>
        ))}
      </ul>
      {viewing && <KbPreview item={viewing} onClose={() => setViewing(null)} />}
      {picker && <SourcePicker provider={picker} onClose={() => setPicker(null)} onDone={() => setN((x) => x + 1)} />}
    </div>
  )
}

// Built-in documents of the Marketing and CS workflows: setup detail, admin mode only.
function BuiltinDocs() {
  const fn = useCallback(() => api.knowledge(), [])
  const k = useLoad(fn)
  return (
    <div className="set-sec">
      <h2>Dokumen bawaan</h2>
      <p className="quiet">Dimuat ke tugas Marketing dan layanan pelanggan.</p>
      {k.state === 'loading' && <Loading text="Memuat dokumen..." shape="lines" />}
      {k.state === 'error' && <ErrorLine text={k.error} onRetry={k.retry} />}
      {k.state === 'ok' &&
        k.data?.docs.map((d) => (
          <div key={d.id} className="set-doc">
            <div className="set-doc-head">
              <b>{d.title}</b>
              <span className="pill">{d.workflow === 'cs' ? 'CS' : 'Marketing'}</span>
            </div>
            <p className="quiet small">
              {d.version ? `Versi ${d.version}` : 'Tanpa nomor versi'} · {d.date ? `data per ${d.date}` : 'tanggal tidak diketahui'}
            </p>
            <ul className="set-files">
              {d.files.map((f) => (
                <li key={f.name}>{f.title}</li>
              ))}
            </ul>
          </div>
        ))}
    </div>
  )
}

export default function Pengetahuan() {
  const admin = useAdminMode()
  return (
    <section className="page">
      <PageHead title="Pengetahuan" sub="Ajari agen tentang bisnis Anda lewat berkas dan link." />
      <MySources />
      {admin && <BuiltinDocs />}
    </section>
  )
}
