// Shared attachment cards (R1: chat, tasks, Marketing; R2: post preview). One place decides how a file is
// shown, downloaded, and previewed, so every screen reads the same. Nothing here uses attachment.url directly:
// files always come through the API with the session token.

import { useCallback, useEffect, useRef, useState } from 'react'
import type { ReactElement } from 'react'
import { ApiError, api, errText } from './bff'
import type { Attachment } from './bff'
import { CLOSE, Icon } from './ui'
import { ProgressLine } from './ui-extra'
import './attachments.css'

type Kind = 'image' | 'video' | 'audio' | 'table' | 'document'

const EXT_KIND: Record<string, Kind> = {
  png: 'image',
  jpg: 'image',
  jpeg: 'image',
  webp: 'image',
  gif: 'image',
  mp4: 'video',
  webm: 'video',
  mp3: 'audio',
  ogg: 'audio',
  wav: 'audio',
  csv: 'table',
  xlsx: 'table',
}
const extOf = (name: string) => (name.split('.').pop() ?? '').toLowerCase()

// Unknown types become documents: nothing is ever put into <img> unless the type says it is an image.
export function attachmentKind(a: Pick<Attachment, 'mime' | 'name'>): Kind {
  const mime = (a.mime || '').toLowerCase()
  if (/^image\/(png|jpeg|webp|gif)$/.test(mime)) return 'image'
  if (/^video\/(mp4|webm)$/.test(mime)) return 'video'
  if (/^audio\/(mpeg|ogg|wav|x-wav)$/.test(mime)) return 'audio'
  if (mime === 'text/csv' || /spreadsheetml\.sheet/.test(mime)) return 'table'
  return EXT_KIND[extOf(a.name)] ?? 'document'
}

export const KIND_LABEL: Record<Kind, string> = { image: 'Gambar', video: 'Video', audio: 'Suara', table: 'Tabel', document: 'Dokumen' }

export const sizeText = (bytes: number): string => {
  if (bytes >= 1_048_576) return `${(bytes / 1_048_576).toLocaleString('id-ID', { maximumFractionDigits: 1 })} MB`
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`
  return `${Math.max(0, Math.round(bytes))} B`
}

const clock = (ms?: number) => {
  if (!ms || ms < 0) return ''
  const total = Math.round(ms / 1000)
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`
}

// ---- file cache ----
// One request per file (and per thumbnail) shared by every card on screen; failed promises are dropped so
// "Coba lagi" really retries.
const blobCache = new Map<string, Promise<Blob>>()

function blobFor(id: string, thumb: boolean): Promise<Blob> {
  const key = `${id}|${thumb ? 't' : 'o'}`
  const hit = blobCache.get(key)
  if (hit) return hit
  const p = api.artifactBlob(id, thumb)
  blobCache.set(key, p)
  p.catch(() => blobCache.delete(key))
  return p
}

const MAX_PLAY = 50 * 1024 * 1024 // above this a video/audio is downloaded, not streamed

export function useArtifactSrc(
  a: Pick<Attachment, 'id' | 'bytes' | 'mime'>,
  opt?: { thumb?: boolean; wantLink?: boolean; enabled?: boolean },
): { src: string; state: 'idle' | 'loading' | 'ok' | 'gone' | 'error'; retry: () => void } {
  const thumb = opt?.thumb === true
  const wantLink = opt?.wantLink === true
  const enabled = opt?.enabled !== false
  const [nonce, setNonce] = useState(0)
  const [src, setSrc] = useState('')
  const [state, setState] = useState<'idle' | 'loading' | 'ok' | 'gone' | 'error'>('idle')
  const retry = useCallback(() => {
    blobCache.delete(`${a.id}|${thumb ? 't' : 'o'}`)
    setNonce((n) => n + 1)
  }, [a.id, thumb])

  useEffect(() => {
    if (!enabled) {
      setState('idle')
      setSrc('')
      return
    }
    let dead = false
    let url = ''
    setState('loading')
    setSrc('')
    const av = /^(video|audio)\//.test(a.mime)
    const run = async () => {
      if (av && wantLink) {
        try {
          const link = await api.artifactLink(a.id)
          if (dead) return
          url = link.url
          setSrc(link.url)
          setState('ok')
          return
        } catch {
          if (a.bytes > MAX_PLAY) {
            if (!dead) setState('error')
            return
          }
        }
      }
      try {
        const blob = await blobFor(a.id, thumb)
        if (dead) return
        url = URL.createObjectURL(blob)
        setSrc(url)
        setState('ok')
      } catch (e) {
        if (dead) return
        setState(e instanceof ApiError && e.status === 404 ? 'gone' : 'error')
      }
    }
    void run()
    return () => {
      dead = true
      if (url.startsWith('blob:')) URL.revokeObjectURL(url)
    }
  }, [a.id, a.mime, a.bytes, thumb, wantLink, enabled, nonce])

  return { src, state, retry }
}

function safeName(name: string): string {
  const clean = name
    .replace(/[\\/:*?"<>|]/g, '')
    .replace(/[\u0000-\u001f\u007f]/g, '')
    .trim()
  return clean || 'berkas'
}

export async function downloadAttachment(a: Attachment): Promise<void> {
  const blob = await api.artifactBlob(a.id)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = safeName(a.name)
  document.body.append(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 4000)
}

// ---- small shared pieces ----
const DOWN = 'M12 4v10M8 11l4 4 4-4M5 19h14'
const SOUND = 'M11 5 6 9H3v6h3l5 4zM16 9a4 4 0 0 1 0 6M19 6a8 8 0 0 1 0 12'

function DownloadButton({ item, compact, onError }: { item: Attachment; compact?: boolean; onError?: (message: string) => void }) {
  const [busy, setBusy] = useState(false)
  const go = async () => {
    setBusy(true)
    onError?.('')
    try {
      await downloadAttachment(item)
    } catch (e) {
      onError?.(errText(e))
    } finally {
      setBusy(false)
    }
  }
  return compact ? (
    <button type="button" className="icon-btn att-dl" aria-label={`Unduh ${item.name}`} title="Unduh" disabled={busy} onClick={go}>
      <Icon d={DOWN} />
    </button>
  ) : (
    <button type="button" className="btn soft att-dl-text" disabled={busy} onClick={go} aria-label={`Unduh ${item.name}`}>
      {busy ? 'Mengunduh…' : 'Unduh'}
    </button>
  )
}

function FootDownload({ item }: { item: Attachment }) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const go = async () => {
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
    <>
      <button type="button" className="icon-btn att-dl" aria-label={`Unduh ${item.name}`} disabled={busy} onClick={go}>
        <Icon d={DOWN} />
      </button>
      {err ? (
        <p className="small err att-err" role="alert">
          {err}
        </p>
      ) : null}
    </>
  )
}

const ratioOf = (a: Pick<Attachment, 'width' | 'height'>) => {
  if (!a.width || !a.height) return 4 / 3
  return Math.min(1.8, Math.max(0.6, a.width / a.height))
}

// ---- image ----
function Photo({ item, onOpen, compact }: { item: Attachment; onOpen?: () => void; compact?: boolean }) {
  const { src, state, retry } = useArtifactSrc(item)
  const ratio = ratioOf(item)
  return (
    <figure className={`att-card att-photo${compact ? ' att-compact' : ''}`}>
      {state === 'ok' ? (
        <button type="button" className="att-media att-img" style={{ aspectRatio: String(ratio) }} aria-label={`Perbesar gambar: ${item.name}`} onClick={onOpen}>
          <img src={src} alt={item.name} loading="lazy" decoding="async" />
        </button>
      ) : state === 'gone' ? (
        <div className="att-state att-img" style={{ aspectRatio: String(ratio) }}>
          <span>Berkas ini sudah tidak tersedia.</span>
        </div>
      ) : state === 'error' ? (
        <div className="att-state att-img" style={{ aspectRatio: String(ratio) }} role="alert">
          <span>Gambar tidak bisa dimuat.</span>
          <button type="button" className="btn link" onClick={retry}>
            Coba lagi
          </button>
        </div>
      ) : (
        <div className="att-img att-skel-wrap" style={{ aspectRatio: String(ratio) }} role="status">
          <span className="skel-block att-skel" />
          <span className="sr">Memuat gambar</span>
        </div>
      )}
      {!compact && (
        <figcaption className="att-foot">
          <span className="att-foot-text">
            <span className="att-name clamp2">{item.name}</span>
            <span className="att-meta num">
              {KIND_LABEL.image} · {sizeText(item.bytes)}
            </span>
          </span>
          {state !== 'gone' && <FootDownload item={item} />}
        </figcaption>
      )}
    </figure>
  )
}

// ---- video ----
function Video({ item }: { item: Attachment }) {
  const [playing, setPlaying] = useState(false)
  const poster = useArtifactSrc(item, { thumb: true })
  const media = useArtifactSrc(item, { wantLink: true, enabled: playing })
  const ref = useRef<HTMLVideoElement>(null)
  const ratio = Math.min(1.78, Math.max(0.56, item.width && item.height ? item.width / item.height : 16 / 9))

  useEffect(() => {
    if (media.state === 'ok' && playing) void ref.current?.play().catch(() => undefined)
  }, [media.state, playing])

  const tooBig = item.bytes > MAX_PLAY && media.state === 'error'
  const gone = media.state === 'gone' || (!playing && poster.state === 'gone')
  return (
    <figure className="att-card att-video">
      <div className="att-video-box" style={{ aspectRatio: String(ratio) }}>
        {gone ? (
          <div className="att-state">
            <span>Berkas ini sudah tidak tersedia.</span>
          </div>
        ) : playing && media.state === 'ok' ? (
          <video ref={ref} className="att-video-el" controls playsInline preload="metadata" poster={poster.src || undefined} src={media.src} />
        ) : playing && media.state === 'error' ? (
          <div className="att-state" role="alert">
            <span>{tooBig ? 'Video terlalu besar untuk diputar di sini. Unduh untuk menontonnya.' : 'Video tidak bisa dimuat.'}</span>
            {!tooBig && (
              <button type="button" className="btn link" onClick={media.retry}>
                Coba lagi
              </button>
            )}
          </div>
        ) : playing && media.state === 'gone' ? (
          <div className="att-state">
            <span>Berkas ini sudah tidak tersedia.</span>
          </div>
        ) : playing ? (
          <div className="att-state">
            <ProgressLine label="Menyiapkan video…" />
          </div>
        ) : (
          <>
            {poster.state === 'ok' ? <img className="att-video-poster" src={poster.src} alt="" /> : <span className="att-video-poster" />}
            <button type="button" className="btn primary att-play" aria-label={`Putar video: ${item.name}`} onClick={() => setPlaying(true)}>
              <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
                <path d="M8 5v14l11-7z" fill="currentColor" />
              </svg>
            </button>
          </>
        )}
      </div>
      <figcaption className="att-foot">
        <span className="att-foot-text">
          <span className="att-name clamp2">{item.name}</span>
          <span className="att-meta num">
            {KIND_LABEL.video}
            {clock(item.duration_ms) ? ` · ${clock(item.duration_ms)}` : ''} · {sizeText(item.bytes)}
          </span>
        </span>
        {!gone && <FootDownload item={item} />}
      </figcaption>
    </figure>
  )
}

// ---- audio ----
function Audio({ item }: { item: Attachment }) {
  const auto = item.bytes <= 10 * 1024 * 1024 // a small file may load with the card
  const [armed, setArmed] = useState(auto)
  const { src, state, retry } = useArtifactSrc(item, { wantLink: true, enabled: armed })
  return (
    <figure className="att-card att-audio-card">
      <div className="att-audio">
        <span className="att-audio-icon" aria-hidden="true">
          <Icon d={SOUND} size={20} />
        </span>
        <span className="att-foot-text">
          <span className="att-name clamp2">{item.name}</span>
          <span className="att-meta num">
            {KIND_LABEL.audio}
            {clock(item.duration_ms) ? ` · ${clock(item.duration_ms)}` : ''} · {sizeText(item.bytes)}
          </span>
        </span>
      </div>
      <div className="att-audio-player">
        {!armed ? (
          <button type="button" className="btn soft" onClick={() => setArmed(true)}>
            Putar
          </button>
        ) : state === 'ok' ? (
          <audio controls preload="none" src={src} style={{ width: '100%' }} />
        ) : state === 'gone' ? (
          <span className="small muted">Berkas ini sudah tidak tersedia.</span>
        ) : state === 'error' ? (
          <span className="small err" role="alert">
            Suara tidak bisa dimuat.{' '}
            <button type="button" className="btn link" onClick={retry}>
              Coba lagi
            </button>
          </span>
        ) : (
          <span className="small muted" role="status">
            Memuat suara…
          </span>
        )}
      </div>
      {state !== 'gone' && (
        <figcaption className="att-foot att-foot-actions">
          <FootDownload item={item} />
        </figcaption>
      )}
    </figure>
  )
}

// ---- documents ----
function extLabel(name: string): string {
  const ext = extOf(name)
  if (['pdf', 'docx', 'xlsx', 'pptx', 'md', 'txt', 'zip', 'csv'].includes(ext)) return ext.toUpperCase()
  if (ext === 'doc') return 'DOC'
  if (ext === 'ppt') return 'PPT'
  return 'FILE'
}

function Doc({ item, compact }: { item: Attachment; compact?: boolean }) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const isPdf = extOf(item.name) === 'pdf' || item.mime === 'application/pdf'
  const kind = attachmentKind(item)
  // The file is read once when the card appears: that is how a deleted file is shown as gone before a click.
  const probe = useArtifactSrc(item, { enabled: !compact })

  // A tab must be opened during the click; it is filled once the file arrives (the token never goes into a URL).
  const open = async () => {
    const tab = window.open('', '_blank')
    if (!tab) {
      setErr('Pop-up diblokir. Gunakan Unduh.')
      return
    }
    setBusy(true)
    setErr('')
    try {
      const blob = await api.artifactBlob(item.id)
      const url = URL.createObjectURL(blob)
      tab.location.href = url
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
    } catch (e) {
      tab.close()
      setErr(errText(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <figure className={`att-card${compact ? ' att-compact' : ''}`}>
      <div className="att-doc">
        <span className="att-ext" aria-hidden="true">
          {extLabel(item.name)}
        </span>
        <span className="att-foot-text">
          <span className="att-name att-name-doc clamp2">{item.name}</span>
          <span className="att-meta num">
            {KIND_LABEL[kind]} · {extLabel(item.name)} · {sizeText(item.bytes)}
          </span>
        </span>
        <span className="att-act">
          {probe.state === 'gone' ? null : compact ? (
            <DownloadButton item={item} compact onError={setErr} />
          ) : (
            <>
              {isPdf && (
                <button type="button" className="btn soft" disabled={busy} onClick={open}>
                  {busy ? 'Membuka…' : 'Buka'}
                </button>
              )}
              <DownloadButton item={item} onError={setErr} />
            </>
          )}
        </span>
      </div>
      {probe.state === 'gone' ? (
        <p className="small muted att-note">Berkas ini sudah tidak tersedia.</p>
      ) : probe.state === 'error' ? (
        <p className="small err att-note" role="alert">
          {KIND_LABEL[kind]} tidak bisa dimuat.{' '}
          <button type="button" className="btn link" onClick={probe.retry}>
            Coba lagi
          </button>
        </p>
      ) : probe.state === 'loading' ? (
        <p className="small muted att-note" role="status">
          Memuat {KIND_LABEL[kind].toLowerCase()}…
        </p>
      ) : null}
      {err ? (
        <p className="small err att-err" role="alert">
          {err}
        </p>
      ) : null}
    </figure>
  )
}

// ---- CSV preview ----
// Small RFC 4180 reader: quotes keep separators and newlines, doubled quotes mean one quote.
function parseCsv(text: string, delim: string): string[][] {
  const rows: string[][] = []
  let row: string[] = []
  let cell = ''
  let quoted = false
  for (let i = 0; i < text.length; i++) {
    const c = text[i]
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') {
        cell += '"'
        i++
      } else if (c === '"') quoted = false
      else cell += c
    } else if (c === '"') quoted = true
    else if (c === delim) {
      row.push(cell)
      cell = ''
    } else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++
      row.push(cell)
      rows.push(row)
      row = []
      cell = ''
    } else cell += c
  }
  if (cell || row.length) {
    row.push(cell)
    rows.push(row)
  }
  return rows.filter((r) => r.some((x) => x.trim() !== ''))
}

function Table({ item, compact }: { item: Attachment; compact?: boolean }) {
  const [rows, setRows] = useState<string[][] | null>(null)
  const [state, setState] = useState<'loading' | 'ok' | 'error' | 'gone'>('loading')
  const [nonce, setNonce] = useState(0)
  const [dlErr, setDlErr] = useState('')

  useEffect(() => {
    if (compact || extOf(item.name) === 'xlsx') return
    let dead = false
    setState('loading')
    blobFor(item.id, false)
      .then((blob) => blob.slice(0, 262_144).text())
      .then((text) => {
        if (dead) return
        const head = text.split(/\r?\n/, 1)[0] ?? ''
        const delim = (head.match(/;/g)?.length ?? 0) > (head.match(/,/g)?.length ?? 0) ? ';' : ','
        setRows(parseCsv(text, delim))
        setState('ok')
      })
      .catch((e) => {
        if (!dead) setState(e instanceof ApiError && e.status === 404 ? 'gone' : 'error')
      })
    return () => {
      dead = true
    }
  }, [item.id, item.name, compact, nonce])

  const preview = !compact && extOf(item.name) !== 'xlsx'
  const shown = rows?.slice(0, 7) ?? []
  const width = Math.min(8, Math.max(0, ...shown.map((r) => r.length)))
  const total = rows?.length ?? 0
  return (
    <figure className={`att-card att-table-card${compact ? ' att-compact' : ''}`}>
      <div className="att-doc">
        <span className="att-ext" aria-hidden="true">
          {extLabel(item.name)}
        </span>
        <span className="att-foot-text">
          <span className="att-name att-name-doc clamp2">{item.name}</span>
          <span className="att-meta num">
            {KIND_LABEL.table} · {extLabel(item.name)} · {sizeText(item.bytes)}
          </span>
        </span>
        <span className="att-act">
          {state === 'gone' ? null : compact ? <DownloadButton item={item} compact onError={setDlErr} /> : <DownloadButton item={item} onError={setDlErr} />}
        </span>
      </div>
      {dlErr ? (
        <p className="small err att-err" role="alert">
          {dlErr}
        </p>
      ) : null}
      {preview && (
        <div className="att-table" role="region" tabIndex={0} aria-label={`Pratinjau tabel: ${item.name}`}>
          {state === 'loading' ? (
            <p className="small muted att-table-note" role="status">
              Memuat tabel…
            </p>
          ) : state === 'gone' ? (
            <p className="small muted att-table-note">Berkas ini sudah tidak tersedia.</p>
          ) : state === 'error' ? (
            <p className="small err att-table-note" role="alert">
              Tabel tidak bisa dimuat.{' '}
              <button type="button" className="btn link" onClick={() => setNonce((n) => n + 1)}>
                Coba lagi
              </button>
            </p>
          ) : shown.length === 0 ? (
            <p className="small muted att-table-note">Tabel ini kosong.</p>
          ) : (
            <>
              <table className="plain">
                <thead>
                  <tr>
                    {shown[0].slice(0, width).map((h, i) => (
                      <th key={i}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {shown.slice(1).map((r, ri) => (
                    <tr key={ri}>
                      {Array.from({ length: width }, (_, i) => (
                        <td key={i}>{r[i] ?? ''}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {total > 7 && (
                <p className="small muted att-table-note">
                  Menampilkan 6 dari {total - 1} baris. Unduh untuk melihat semuanya.
                </p>
              )}
            </>
          )}
        </div>
      )}
    </figure>
  )
}

// ---- public card ----
export function AttachmentCard({ item, onOpenImage, compact }: { item: Attachment; onOpenImage?: () => void; compact?: boolean }): ReactElement {
  const kind = attachmentKind(item)
  if (kind === 'image') return <Photo item={item} onOpen={onOpenImage} compact={compact} />
  if (kind === 'video') return <Video item={item} />
  if (kind === 'audio') return <Audio item={item} />
  if (kind === 'table') return <Table item={item} compact={compact} />
  return <Doc item={item} compact={compact} />
}

export function AttachmentList({ items, compact }: { items: Attachment[]; compact?: boolean }): ReactElement | null {
  const [open, setOpen] = useState<number | null>(null)
  if (!items.length) return null
  const images = items.filter((a) => attachmentKind(a) === 'image')
  const rest = items.filter((a) => attachmentKind(a) !== 'image')
  return (
    <div className={`att-list${compact ? ' att-compact-list' : ''}`}>
      {images.length === 1 && !compact ? (
        <Photo item={images[0]} onOpen={() => setOpen(0)} />
      ) : images.length > 0 ? (
        <div className="att-grid">
          {images.map((a, i) => (
            <Photo key={a.id} item={a} onOpen={() => setOpen(i)} compact />
          ))}
        </div>
      ) : null}
      {rest.map((a) => (
        <AttachmentCard key={a.id} item={a} compact={compact} />
      ))}
      {open !== null && images.length > 0 && <Lightbox items={images} index={open} onIndex={setOpen} onClose={() => setOpen(null)} />}
    </div>
  )
}

// ---- lightbox ----
export function Lightbox({ items, index, onIndex, onClose }: { items: Attachment[]; index: number; onIndex: (i: number) => void; onClose: () => void }): ReactElement {
  const ref = useRef<HTMLDialogElement>(null)
  const opener = useRef<Element | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const i = Math.min(Math.max(0, index), items.length - 1)
  const item = items[i]
  const { src, state, retry } = useArtifactSrc(item)

  useEffect(() => {
    opener.current = document.activeElement
    const d = ref.current
    if (d && !d.open) d.showModal()
    return () => {
      if (opener.current instanceof HTMLElement && opener.current.isConnected) opener.current.focus()
    }
  }, [])

  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft' && i > 0) onIndex(i - 1)
      if (e.key === 'ArrowRight' && i < items.length - 1) onIndex(i + 1)
    }
    window.addEventListener('keydown', key)
    return () => window.removeEventListener('keydown', key)
  }, [i, items.length, onIndex])

  const save = async () => {
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
    <dialog
      ref={ref}
      className="lb"
      aria-label={`Pratinjau gambar: ${item.name}`}
      onClose={onClose}
      onClick={(e) => {
        if (e.target === ref.current) ref.current?.close()
      }}
    >
      <div className="lb-in">
        <button type="button" className="icon-btn lb-close" aria-label="Tutup" onClick={() => ref.current?.close()}>
          <Icon d={CLOSE} size={20} />
        </button>
        {i > 0 && (
          <button type="button" className="icon-btn lb-nav lb-prev" aria-label="Gambar sebelumnya" onClick={() => onIndex(i - 1)}>
            <Icon d="M15 6l-6 6 6 6" size={22} />
          </button>
        )}
        {i < items.length - 1 && (
          <button type="button" className="icon-btn lb-nav lb-next" aria-label="Gambar berikutnya" onClick={() => onIndex(i + 1)}>
            <Icon d="M9 6l6 6-6 6" size={22} />
          </button>
        )}
        {state === 'ok' ? (
          <img className="lb-img" src={src} alt={item.name} />
        ) : state === 'gone' ? (
          <p className="lb-note">Berkas ini sudah tidak tersedia.</p>
        ) : state === 'error' ? (
          <p className="lb-note" role="alert">
            Gambar tidak bisa dimuat.{' '}
            <button type="button" className="btn link lb-link" onClick={retry}>
              Coba lagi
            </button>
          </p>
        ) : (
          <p className="lb-note" role="status">
            Memuat gambar…
          </p>
        )}
        <div className="lb-bar">
          <span className="lb-name clamp2">{item.name}</span>
          <span className="num lb-count">
            {i + 1} / {items.length}
          </span>
          <button type="button" className="btn soft lb-dl" disabled={busy} onClick={save}>
            {busy ? 'Mengunduh…' : 'Unduh'}
          </button>
        </div>
        {err ? (
          <p className="small err lb-err" role="alert">
            {err}
          </p>
        ) : null}
      </div>
    </dialog>
  )
}
