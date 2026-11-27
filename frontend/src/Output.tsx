// #/output — every non-text result the agents made: images, video, voice, documents and tables.
// The filter lives in the hash (#/output?pegawai=<id>&jenis=<jenis>), so refresh and shared links keep the view.
// Reading a thumbnail, previewing and downloading all go through attachments.tsx (the file never comes from a raw URL).
import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactElement } from 'react'
import { api, errText, OUTPUT_KINDS } from './bff'
import type { OutputItem, OutputKind } from './bff'
import { AttachmentCard, attachmentKind, downloadAttachment, KIND_LABEL, Lightbox, sizeText, useArtifactSrc } from './attachments'
import { ago, Dialog, ErrorLine, nf, stamp } from './ui'
import { Empty, PageHead } from './ui-extra'
import { go, outputPath } from './router'
import { useData } from './data'
import './output.css'

const PAGE = 24
const DELETED = 'Pegawai yang sudah dihapus'

// The extension label in the tile media area. Only the extensions the product actually shows; anything else is "FILE".
const EXTS: Record<string, true> = { PDF: true, DOCX: true, XLSX: true, CSV: true, WAV: true, MP3: true, MD: true, TXT: true, ZIP: true }
const extLabel = (name: string) => {
  const ext = (name.split('.').pop() ?? '').toUpperCase()
  return EXTS[ext] ? ext : 'FILE'
}

const dayKey = (epoch: number) => {
  const d = new Date(epoch * 1000)
  return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`
}

function dayTitle(epoch: number): string {
  const d = new Date(epoch * 1000)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const day = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  if (day === today) return 'Hari ini'
  if (day === new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1).getTime()) return 'Kemarin'
  return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
}

interface Filters {
  pegawai: string
  jenis: OutputKind | ''
}

const readFilters = (): Filters => {
  const s = new URLSearchParams(location.hash.split('?')[1] ?? '')
  const jenis = s.get('jenis') ?? ''
  return { pegawai: s.get('pegawai') ?? '', jenis: OUTPUT_KINDS.includes(jenis as OutputKind) ? (jenis as OutputKind) : '' }
}

// ---- one tile ----
// Images read their thumbnail once; a 404 leaves the tile honest ("Berkas ini sudah tidak tersedia.") with no Unduh.
function Tile({ item, botName, onOpen }: { item: OutputItem; botName: string; onOpen: () => void }): ReactElement {
  const kind = attachmentKind(item)
  const thumb = useArtifactSrc(item, { thumb: true, enabled: kind === 'image' })
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const gone = kind === 'image' && thumb.state === 'gone'

  const download = async () => {
    setBusy(true)
    setErr('')
    try {
      await downloadAttachment(item)
    } catch (e) {
      setErr(errText(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <li className="out-tile" id={`out-tile-${item.id}`}>
      <button type="button" className="out-media" tabIndex={-1} aria-hidden="true" onClick={onOpen}>
        {kind === 'image' ? (
          thumb.state === 'ok' ? (
            <img src={thumb.src} alt="" loading="lazy" decoding="async" />
          ) : thumb.state === 'loading' || thumb.state === 'idle' ? (
            <span className="skel-block out-skel" aria-hidden="true" />
          ) : (
            <span className="out-ext" aria-hidden="true">
              {extLabel(item.name)}
            </span>
          )
        ) : kind === 'video' ? (
          <span className="out-play" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M8 5v14l11-7z" />
            </svg>
          </span>
        ) : (
          <span className="out-ext" aria-hidden="true">
            {extLabel(item.name)}
          </span>
        )}
      </button>
      <div className="out-body">
        <span className="out-name clamp2">{item.name}</span>
        <span className="out-meta num">
          {KIND_LABEL[kind]} · {sizeText(item.bytes)}
        </span>
        <span className="out-who">
          {botName} · {ago(item.created_at)}
        </span>
      </div>
      {gone ? (
        <p className="out-gone quiet small">Berkas ini sudah tidak tersedia.</p>
      ) : (
        <div className={'out-foot' + (busy ? ' out-foot-busy' : '')}>
          <button type="button" className="btn soft sm out-preview" aria-label={`Lihat ${KIND_LABEL[kind]}: ${item.name}`} onClick={onOpen}>
            Lihat
          </button>
          <button type="button" className="btn outline sm" disabled={busy} onClick={download}>
            {busy ? 'Mengunduh…' : 'Unduh'}
          </button>
        </div>
      )}
      {err ? (
        <p className="out-err quiet small" role="alert">
          {err}
        </p>
      ) : null}
    </li>
  )
}

// ---- preview for everything that is not an image (the Lightbox handles those) ----
function Preview({ item, botName, onClose }: { item: OutputItem; botName: string; onClose: () => void }): ReactElement {
  const source = item.session_id
    ? { href: `#/chat/${encodeURIComponent(item.bot_id)}/${encodeURIComponent(item.session_id)}`, label: 'Buka percakapan' }
    : item.group_id
      ? { href: `#/grup/${encodeURIComponent(item.group_id)}`, label: 'Buka tim' }
      : item.task_id
        ? { href: '#/kanban', label: 'Lihat di Jadwal & tugas' }
        : null
  return (
    <Dialog title={item.name} wide onClose={onClose}>
      <div className="dlg-body">
        <AttachmentCard item={item} />
        <p className="quiet small">
          Dibuat oleh {botName} · {stamp(item.created_at)}
        </p>
        {source ? (
          <p className="out-src">
            <a className="btn link" href={source.href} onClick={onClose}>
              {source.label}
            </a>
          </p>
        ) : null}
        <footer className="dlg-foot">
          <button
            type="button"
            className="btn quiet-btn"
            onClick={(e) => {
              const d = e.currentTarget.closest('dialog')
              if (d instanceof HTMLDialogElement) d.close()
              else onClose()
            }}
          >
            Tutup
          </button>
        </footer>
      </div>
    </Dialog>
  )
}

export default function Output(): ReactElement {
  const { bots } = useData()
  const [filters, setFilters] = useState<Filters>(readFilters)
  const [items, setItems] = useState<OutputItem[]>([])
  const [next, setNext] = useState<string | null>(null)
  const [counts, setCounts] = useState<Record<OutputKind, number> | null>(null)
  const [state, setState] = useState<'loading' | 'ok' | 'error'>('loading')
  const [error, setError] = useState('')
  const [more, setMore] = useState<'idle' | 'loading' | 'error'>('idle')
  const [preview, setPreview] = useState<OutputItem | null>(null)
  const [lightbox, setLightbox] = useState<number | null>(null)
  const [focusId, setFocusId] = useState<string | null>(null)
  const req = useRef(0)
  const countsBot = useRef<string | null>(null)

  const nameOf = useCallback((id: string) => bots.find((b) => b.id === id)?.name ?? DELETED, [bots])

  // Page one: every filter change starts clean; a late answer from a filter that is already gone is dropped.
  const loadFirst = useCallback(() => {
    const n = ++req.current
    setState('loading')
    setError('')
    setItems([])
    setNext(null)
    setMore('idle')
    if (countsBot.current !== filters.pegawai) {
      countsBot.current = filters.pegawai
      setCounts(null)
    }
    api
      .outputs({ bot_id: filters.pegawai || undefined, type: filters.jenis || undefined, limit: PAGE })
      .then((page) => {
        if (n !== req.current) return
        setItems(page.items)
        setNext(page.next)
        setCounts(page.counts)
        setState('ok')
      })
      .catch((e: unknown) => {
        if (n !== req.current) return
        setError(errText(e))
        setState('error')
      })
  }, [filters.pegawai, filters.jenis])

  useEffect(() => {
    loadFirst()
  }, [loadFirst])

  // The hash is the source of truth: "Output" in the sidebar, Back, or a typed link re-reads the filters.
  // apply() dispatches hashchange itself; the values are equal then, so this bails out without a second load.
  useEffect(() => {
    const sync = () => {
      const f = readFilters()
      setFilters((cur) => (cur.pegawai === f.pegawai && cur.jenis === f.jenis ? cur : f))
    }
    window.addEventListener('hashchange', sync)
    return () => window.removeEventListener('hashchange', sync)
  }, [])

  const apply = (patch: Partial<Filters>) => {
    const f = { ...filters, ...patch }
    // Picking the filter that is already on is a refresh: the hash does not change, so sync() stays quiet and
    // only this explicit reload can replace the skeleton. Without it, apply() would clear the list and no
    // request would follow.
    if (f.pegawai === filters.pegawai && f.jenis === filters.jenis) {
      loadFirst()
      return
    }
    req.current += 1 // any answer still on its way belongs to the old filter
    setFilters(f)
    setState('loading')
    setError('')
    setItems([])
    setNext(null)
    setMore('idle')
    go(outputPath({ pegawai: f.pegawai || undefined, jenis: f.jenis || undefined }), true)
  }

  const loadMore = async () => {
    if (!next || more === 'loading') return
    const n = req.current
    setMore('loading')
    try {
      const page = await api.outputs({
        bot_id: filters.pegawai || undefined,
        type: filters.jenis || undefined,
        before: next,
        limit: PAGE,
      })
      if (n !== req.current) return
      const seen = new Set(items.map((i) => i.id))
      const add = page.items.filter((i) => !seen.has(i.id))
      setItems([...items, ...add])
      setNext(page.next)
      if (page.counts) setCounts(page.counts)
      setMore('idle')
      if (add[0]) setFocusId(add[0].id)
    } catch {
      if (n !== req.current) return
      setMore('error')
    }
  }

  // After "Muat lebih banyak" the keyboard lands on the first tile that arrived, so the list stays usable.
  useEffect(() => {
    if (!focusId) return
    setFocusId(null)
    document.getElementById(`out-tile-${focusId}`)?.querySelector<HTMLButtonElement>('button.out-preview')?.focus()
  }, [focusId])

  const images = useMemo(() => items.filter((i) => attachmentKind(i) === 'image'), [items])

  const days = useMemo(() => {
    const out: { key: string; title: string; items: OutputItem[] }[] = []
    for (const item of items) {
      const key = dayKey(item.created_at)
      const last = out[out.length - 1]
      if (last && last.key === key) last.items.push(item)
      else out.push({ key, title: dayTitle(item.created_at), items: [item] })
    }
    return out
  }, [items])

  const openItem = (item: OutputItem) => {
    if (attachmentKind(item) === 'image') {
      const i = images.findIndex((x) => x.id === item.id)
      setLightbox(i < 0 ? 0 : i)
    } else {
      setPreview(item)
    }
  }

  const hasFilter = !!filters.pegawai || !!filters.jenis
  const missing = filters.pegawai !== '' && !bots.some((b) => b.id === filters.pegawai)
  const total = counts
    ? filters.jenis
      ? counts[filters.jenis]
      : OUTPUT_KINDS.reduce((s, k) => s + counts[k], 0)
    : null
  const countText = `${nf.format(items.length)} hasil${total !== null && next ? ` dari ${nf.format(total)}` : ''}`
  const busy = state === 'loading' || more === 'loading'

  const chips: { key: OutputKind | ''; label: string; n: number | null }[] = [
    { key: '', label: 'Semua', n: counts ? OUTPUT_KINDS.reduce((s, k) => s + counts[k], 0) : null },
    ...OUTPUT_KINDS.map((k) => ({ key: k, label: KIND_LABEL[k], n: counts ? counts[k] : null })),
  ]

  return (
    <section className="page out-page">
      <PageHead title="Output" sub="Gambar, video, suara, dokumen, dan tabel yang sudah dibuat pegawai Anda." />

      <div className="out-main">
        <div className="out-bar">
          <label className="field">
            <span>Pegawai</span>
            <select value={filters.pegawai} onChange={(e) => apply({ pegawai: e.target.value })}>
              <option value="">Semua pegawai</option>
              {bots.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
              {missing ? <option value={filters.pegawai}>{DELETED}</option> : null}
            </select>
          </label>
          <div className="out-types" role="group" aria-label="Jenis hasil">
            {chips.map((c) => (
              <button
                key={c.key || 'all'}
                type="button"
                className="out-chip"
                aria-pressed={filters.jenis === c.key}
                aria-label={c.n !== null ? `${c.label}, ${nf.format(c.n)}` : c.label}
                onClick={() => apply({ jenis: c.key })}
              >
                {c.label}
                {c.n !== null ? <span className="num">{nf.format(c.n)}</span> : null}
              </button>
            ))}
          </div>
        </div>

        <div className="out-results" aria-busy={busy || undefined}>
          <p className="quiet small" role="status">
            {state === 'loading' ? 'Memuat hasil…' : state === 'ok' ? countText : ''}
          </p>

          {state === 'loading' ? (
            <div className="out-grid out-skel-grid" aria-hidden="true">
              {Array.from({ length: 8 }, (_, i) => (
                <div className="out-tile skel" key={i}>
                  <span className="skel-block out-skel" />
                  <div className="out-body">
                    <i className="skel-bar w70" />
                    <i className="skel-bar w40" />
                    <i className="skel-bar w60" />
                  </div>
                  <div className="out-foot out-skel-foot">
                    <span className="skel-block" />
                    <span className="skel-block" />
                  </div>
                </div>
              ))}
            </div>
          ) : null}

          {state === 'error' ? <ErrorLine text={error} onRetry={loadFirst} /> : null}

          {state === 'ok' && items.length === 0 ? (
            hasFilter ? (
              <Empty title="Tidak ada hasil untuk pilihan ini">
                <p>Tidak ada hasil untuk pegawai atau jenis yang dipilih.</p>
                <p className="out-empty-act">
                  <button type="button" className="btn link" onClick={() => apply({ pegawai: '', jenis: '' })}>
                    Hapus pilihan
                  </button>
                </p>
              </Empty>
            ) : (
              <Empty title="Belum ada hasil">
                <p>Hasil muncul di sini saat pegawai membuat gambar, video, suara, dokumen, atau tabel. Coba minta lewat Chat.</p>
                <p className="out-empty-act">
                  <a className="btn primary" href="#/chat">
                    Buka Chat
                  </a>
                </p>
              </Empty>
            )
          ) : null}

          {state === 'ok' && items.length > 0
            ? days.map((d) => (
                <Fragment key={d.key}>
                  <h2 className="out-day">{d.title}</h2>
                  <ul className="out-grid">
                    {d.items.map((item) => (
                      <Tile key={item.id} item={item} botName={nameOf(item.bot_id)} onOpen={() => openItem(item)} />
                    ))}
                  </ul>
                </Fragment>
              ))
            : null}

          {state === 'ok' && more === 'error' ? (
            <p className="problem-bar" role="alert">
              Hasil berikutnya belum bisa dimuat.
              <button type="button" className="btn link" onClick={loadMore}>
                Coba lagi
              </button>
            </p>
          ) : null}

          {state === 'ok' && next && more !== 'error' ? (
            <div className="out-more">
              <button type="button" className="btn soft" disabled={more === 'loading'} onClick={loadMore}>
                {more === 'loading' ? 'Memuat…' : 'Muat lebih banyak'}
              </button>
            </div>
          ) : null}
        </div>
      </div>

      {lightbox !== null && images.length > 0 ? (
        <Lightbox
          items={images}
          index={lightbox}
          onIndex={(i) => setLightbox(i)}
          onClose={() => setLightbox(null)}
        />
      ) : null}

      {preview ? <Preview item={preview} botName={nameOf(preview.bot_id)} onClose={() => setPreview(null)} /> : null}
    </section>
  )
}
