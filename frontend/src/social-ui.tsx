// Instagram posting: the approval card the agent's publish request shows in every chat, the guide for
// turning a personal account into a business/creator one, and the post list inside the Instagram app card.
// Tokens and existing classes only; every string is written for a non-technical shop owner.

import { useCallback, useEffect, useRef, useState } from 'react'
import type { ReactElement } from 'react'
import { api, errText } from './bff'
import type { Attachment, PendingAction, SocialActionPayload, SocialPost } from './bff'
import { attachmentKind, AttachmentCard, useArtifactSrc } from './attachments'
import { ago, stamp, ErrorLine } from './ui'
import { Loading, ProgressLine, useLoad } from './ui-extra'
import { botPath } from './router'
import './social.css'

const CAPTION_LIMIT = 2200
const CAPTION_FOLD = 280
const CAROUSEL_LIMIT = 10

// The payload of a publish request. Absent fields fall back to the safe shape (no crash on old actions).
function payloadOf(a: PendingAction): SocialActionPayload {
  const p = a.payload
  const kind = p.kind === 'image' || p.kind === 'reel' ? p.kind : 'carousel'
  const rawIds: unknown[] = Array.isArray(p.attachment_ids) ? p.attachment_ids : []
  const ids = rawIds.filter((x): x is string => typeof x === 'string')
  const atts = Array.isArray(p.attachments) ? (p.attachments as Attachment[]) : undefined
  return {
    platform: 'instagram',
    kind,
    caption: typeof p.caption === 'string' ? p.caption : '',
    attachment_ids: ids,
    attachments: atts,
    draft_id: typeof p.draft_id === 'string' ? p.draft_id : '',
    account: typeof p.account === 'string' && p.account ? p.account : undefined,
    permalink: typeof p.permalink === 'string' && p.permalink ? p.permalink : undefined,
  }
}

// Instagram accepts 1:1 down to 4:5; anything more square is cropped by the app anyway.
const imageRatio = (a: Pick<Attachment, 'width' | 'height'>) =>
  a.width && a.height ? Math.min(1, Math.max(0.8, a.width / a.height)) : 1

function PostImage({ item, alt, thumb, className }: { item: Attachment; alt: string; thumb?: boolean; className?: string }) {
  const { src, state, retry } = useArtifactSrc(item, { thumb })
  if (state === 'ok' && src) {
    return <img className={className ?? 'post-img'} src={src} alt={alt} style={{ aspectRatio: String(imageRatio(item)) }} />
  }
  if (state === 'gone') return <p className="post-media-none">Berkas ini sudah tidak tersedia.</p>
  if (state === 'error') {
    return (
      <p className="post-media-none">
        Gambar tidak bisa dimuat.{' '}
        <button type="button" className="btn link small" onClick={retry}>
          Coba lagi
        </button>
      </p>
    )
  }
  return (
    <span className={`post-media-skel${className ? ` ${className}` : ''}`} role="status">
      <span className="sr">Memuat gambar</span>
      <i className="skel" aria-hidden="true" />
    </span>
  )
}

function PostVideo({ item, reel }: { item: Attachment; reel?: boolean }) {
  const { src, state, retry } = useArtifactSrc(item, { wantLink: true })
  if (state === 'ok' && src) return <video className={reel ? 'post-reel' : 'post-video'} controls preload="metadata" playsInline src={src} />
  if (state === 'gone') return <p className="post-media-none">Berkas ini sudah tidak tersedia.</p>
  if (state === 'error') {
    return (
      <p className="post-media-none">
        Video tidak bisa diputar di sini.{' '}
        <button type="button" className="btn link small" onClick={retry}>
          Coba lagi
        </button>
      </p>
    )
  }
  return (
    <span className="post-media-skel" role="status">
      <span className="sr">Memuat video</span>
      <i className="skel" aria-hidden="true" />
    </span>
  )
}

// Contract gap G9: an old action may carry only attachment ids. Fetch them once, read the type from the
// file itself, and show images/videos here; anything else becomes its normal attachment card.
type Fetched = { id: string; mime: string; bytes: number; src: string }

function useFetchedMedia(ids: string[]): { items: Fetched[]; state: 'idle' | 'loading' | 'ok' | 'error'; retry: () => void } {
  const key = ids.join('|')
  const [nonce, setNonce] = useState(0)
  const [state, setState] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle')
  const [items, setItems] = useState<Fetched[]>([])
  useEffect(() => {
    if (!ids.length) {
      setItems([])
      setState('idle')
      return
    }
    let dead = false
    const urls: string[] = []
    setState('loading')
    Promise.all(
      ids.map(async (id) => {
        const blob = await api.artifactBlob(id)
        // The card may have unmounted while this file was loading (slow file, navigation away). Creating its
        // URL after that would leave nobody to revoke it, so the effect's own cleanup wins.
        if (dead) throw new Error('unmounted')
        const src = URL.createObjectURL(blob)
        urls.push(src)
        return { id, mime: blob.type, bytes: blob.size, src }
      }),
    ).then(
      (rows) => {
        if (dead) return
        setItems(rows)
        setState('ok')
      },
      () => {
        if (!dead) setState('error')
      },
    )
    return () => {
      dead = true
      for (const url of urls) URL.revokeObjectURL(url)
    }
    // The ids are compared by their joined key: a new array with the same files must not refetch.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, nonce])
  return { items, state, retry: () => setNonce((n) => n + 1) }
}

function FetchedMedia({ ids, kind }: { ids: string[]; kind: SocialActionPayload['kind'] }): ReactElement | null {
  const { items, state, retry } = useFetchedMedia(ids)
  if (!ids.length) return null
  if (state === 'error') {
    return (
      <p className="post-media-none">
        Gambar tidak bisa dimuat.{' '}
        <button type="button" className="btn link small" onClick={retry}>
          Coba lagi
        </button>
      </p>
    )
  }
  if (state !== 'ok') {
    return (
      <span className="post-media-skel" role="status">
        <span className="sr">Memuat gambar</span>
        <i className="skel" aria-hidden="true" />
      </span>
    )
  }
  const images = items.filter((f) => /^image\//.test(f.mime))
  const videos = items.filter((f) => /^video\//.test(f.mime))
  const others = items.filter((f) => !/^(image|video)\//.test(f.mime))
  return (
    <>
      {kind === 'reel' && videos[0] ? (
        <video className="post-reel" controls preload="metadata" playsInline src={videos[0].src} />
      ) : kind !== 'carousel' && images[0] ? (
        <img className="post-img" src={images[0].src} alt="Gambar postingan" style={{ aspectRatio: '1' }} />
      ) : kind !== 'carousel' && videos[0] ? (
        <video className="post-video" controls preload="metadata" playsInline src={videos[0].src} />
      ) : images.length > 0 ? (
        <>
          <ul className="post-strip" tabIndex={0} role="region" aria-label="Gambar postingan">
            {images.map((f, i) => (
              <li key={f.id}>
                <img src={f.src} alt={`Gambar ${i + 1} dari ${images.length}`} />
              </li>
            ))}
          </ul>
          {images.length > 0 && <small className="quiet post-strip-note">{images.length} gambar</small>}
        </>
      ) : null}
      {kind === 'carousel' && videos.length > 0 && (
        <div className="post-files">
          {videos.map((f) => (
            <video key={f.id} className="post-video" controls preload="metadata" playsInline src={f.src} />
          ))}
        </div>
      )}
      {others.length > 0 && (
        <div className="post-files">
          {others.map((f) => (
            <AttachmentCard key={f.id} item={{ id: f.id, name: 'Lampiran postingan', mime: f.mime, bytes: f.bytes, url: '' }} compact />
          ))}
        </div>
      )}
    </>
  )
}

function PreviewMedia({ p }: { p: SocialActionPayload }) {
  const atts = p.attachments ?? []
  if (!atts.length) return <FetchedMedia ids={p.attachment_ids} kind={p.kind} />
  const images = atts.filter((a) => attachmentKind(a) === 'image')
  const videos = atts.filter((a) => attachmentKind(a) === 'video')
  const others = atts.filter((a) => !['image', 'video'].includes(attachmentKind(a)))
  return (
    <>
      {p.kind === 'reel' ? (
        videos[0] ? (
          <PostVideo item={videos[0]} reel />
        ) : images[0] ? (
          <PostImage item={images[0]} alt="Gambar postingan" />
        ) : null
      ) : p.kind === 'image' ? (
        images[0] ? (
          <PostImage item={images[0]} alt="Gambar postingan" />
        ) : videos[0] ? (
          <PostVideo item={videos[0]} />
        ) : null
      ) : images.length > 0 ? (
        <>
          <ul className="post-strip" tabIndex={0} role="region" aria-label="Gambar postingan">
            {images.map((a, i) => (
              <li key={a.id}>
                <PostImage item={a} alt={`Gambar ${i + 1} dari ${images.length}`} thumb className="post-strip-img" />
              </li>
            ))}
          </ul>
          {images.length > 0 && <small className="quiet post-strip-note">{images.length} gambar</small>}
        </>
      ) : null}
      {videos.length > 0 && p.kind === 'carousel' && (
        <div className="post-files">
          {videos.map((a) => (
            <PostVideo key={a.id} item={a} />
          ))}
        </div>
      )}
      {others.length > 0 && (
        <div className="post-files">
          {others.map((a) => (
            <AttachmentCard key={a.id} item={a} compact />
          ))}
        </div>
      )}
    </>
  )
}

// The same yellow approval wrapper as an email card. The agent only asks; nothing is published before Setujui.
export function PostApprovalCard({ action }: { action: PendingAction }) {
  const [local, setLocal] = useState<PendingAction | null>(null)
  const [busy, setBusy] = useState<'approve' | 'reject' | 'change' | null>(null)
  const [problem, setProblem] = useState('')
  const [editing, setEditing] = useState(false)
  const [request, setRequest] = useState('')
  const [edited, setEdited] = useState<{ chat?: string } | null>(null)
  const [expanded, setExpanded] = useState(false)

  // Our own click answers at once; the global stream then owns the card (approved → done/failed), and a final
  // status from either side always wins over a still-running one.
  const actionFinal = action.status === 'done' || action.status === 'failed' || action.status === 'rejected' || action.status === 'expired'
  const localFinal = local?.status === 'done' || local?.status === 'failed' || local?.status === 'rejected' || local?.status === 'expired'
  const a = actionFinal ? action : localFinal && local ? local : action.status === 'pending' ? local ?? action : action
  const p = payloadOf(a)
  const pending = a.status === 'pending'
  const tooLong = p.caption.length > CAPTION_LIMIT
  const tooMany = p.attachment_ids.length > CAROUSEL_LIMIT
  const longCaption = p.caption.length > CAPTION_FOLD

  async function decide(approve: boolean) {
    setBusy(approve ? 'approve' : 'reject')
    setProblem('')
    try {
      setLocal(await (approve ? api.approveAction(a.id) : api.rejectAction(a.id)))
    } catch (e) {
      setProblem(errText(e))
    } finally {
      setBusy(null)
    }
  }

  // The stream usually reports the upload result; if it does not (or the tab missed it), the card asks again
  // while the upload is running, so "Sedang diunggah…" can never stay on screen after it ended.
  const uploading = a.status === 'approved'
  const actionId = a.id
  useEffect(() => {
    if (!uploading) return
    const t = window.setInterval(() => {
      void api.actions().then(
        (rows) => {
          const next = rows.find((x) => x.id === actionId)
          if (next && next.status !== 'approved' && next.status !== 'pending') setLocal(next)
        },
        () => undefined,
      )
    }, 2000)
    return () => window.clearInterval(t)
  }, [uploading, actionId])

  async function sendChange() {
    const text = request.trim()
    if (!text) return
    setBusy('change')
    setProblem('')
    try {
      setLocal(await api.rejectAction(a.id)) // the old draft never publishes
      const botId = a.source?.bot_id
      if (botId) {
        const run = await api.startRun(botId, `Tolong ubah postingan Instagram tadi: ${text}`, a.source?.session_id ?? undefined)
        setEdited({ chat: `#${botPath(botId, run.session_id || a.source?.session_id || undefined)}` })
      } else {
        setEdited({})
      }
      setEditing(false)
    } catch (e) {
      setProblem(errText(e))
    } finally {
      setBusy(null)
    }
  }

  const account = p.account
  const initial = (account ?? 'Instagram').replace(/^@/, '').charAt(0).toUpperCase()
  const permalink = p.permalink ?? ''
  const title = account ? `Posting ke Instagram ${account}` : 'Posting ke Instagram'

  return (
    <div className="approval action-card post-approval" data-s={a.status} role="group" aria-label="Persetujuan posting Instagram">
      <p className="approval-title">{title}</p>
      {edited ? (
        edited.chat ? (
          <p className="plan-done">
            Permintaan dikirim. Pegawai akan menyiapkan versi baru.{' '}
            <a className="btn link" href={edited.chat}>
              Buka chat
            </a>
          </p>
        ) : (
          <p className="plan-done">Postingan ditolak. Ketik perubahan yang Anda mau di chat.</p>
        )
      ) : (
        <>
          {(pending || a.status === 'approved') && (
            <div className="post-prev">
              <div className="post-prev-head">
                <span className="post-avatar" aria-hidden="true">
                  {initial}
                </span>
                <span className="post-who">
                  <b>{account ?? 'Instagram'}</b>
                  <small className="quiet">Pratinjau</small>
                </span>
              </div>
              <PreviewMedia p={p} />
              {p.caption && <p className={`post-cap${longCaption && !expanded ? ' post-fold' : ''}`}>{p.caption}</p>}
              {longCaption && (
                <button type="button" className="btn link small post-more" aria-expanded={expanded} onClick={() => setExpanded((v) => !v)}>
                  {expanded ? 'Lebih sedikit' : 'Selengkapnya'}
                </button>
              )}
              <small className={`num post-count${tooLong ? ' err' : ''}`}>
                {p.caption.length.toLocaleString('id-ID')} / 2.200 huruf
              </small>
              {tooLong && <p className="post-limit err">Terlalu panjang untuk Instagram. Pilih Ubah untuk meminta versi lebih pendek.</p>}
            </div>
          )}
          {tooMany && <p className="note-box">Instagram hanya menerima 10 gambar per carousel.</p>}
          {pending ? (
            <>
              <p className="plan-note">Postingan ini belum terbit. Pegawai baru mengunggahnya setelah Anda setuju.</p>
              {editing ? (
                <div className="post-edit">
                  <label className="field">
                    <span>Apa yang ingin diubah?</span>
                    <textarea
                      rows={3}
                      maxLength={500}
                      value={request}
                      placeholder="Contoh: Buat lebih singkat dan tambahkan ajakan ke website."
                      onChange={(e) => setRequest(e.target.value)}
                    />
                  </label>
                  <div className="approval-actions">
                    <button type="button" className="btn primary" disabled={busy !== null || !request.trim()} onClick={() => void sendChange()}>
                      {busy === 'change' ? 'Mengirim…' : 'Kirim permintaan'}
                    </button>
                    <button type="button" className="btn quiet-btn" disabled={busy !== null} onClick={() => setEditing(false)}>
                      Batal
                    </button>
                  </div>
                </div>
              ) : (
                <div className="approval-actions">
                  <button type="button" className="btn primary" disabled={busy !== null || tooLong || tooMany} onClick={() => void decide(true)}>
                    {busy === 'approve' ? 'Menyetujui…' : 'Setujui'}
                  </button>
                  <button type="button" className="btn soft" disabled={busy !== null} onClick={() => setEditing(true)}>
                    Ubah
                  </button>
                  <button type="button" className="btn soft" disabled={busy !== null} onClick={() => void decide(false)}>
                    {busy === 'reject' ? 'Menolak…' : 'Tolak'}
                  </button>
                </div>
              )}
            </>
          ) : a.status === 'approved' ? (
            <>
              <p role="status">Sedang diunggah ke Instagram…</p>
              <span aria-hidden="true">
                <ProgressLine label="Sedang diunggah ke Instagram" />
              </span>
            </>
          ) : (
            <p className={a.status === 'done' ? 'plan-done' : 'action-result'} role="status">
              <b>{a.status === 'done' ? 'Terbit. ' : a.status === 'failed' ? 'Gagal. ' : a.status === 'rejected' ? 'Ditolak. ' : 'Kedaluwarsa. '}</b>
              {a.status === 'done' || a.status === 'failed' ? a.result : ''}
              {a.status === 'done' && permalink && (
                <>
                  {' '}
                  <a className="btn link" href={permalink} target="_blank" rel="noopener noreferrer">
                    Lihat di Instagram
                  </a>
                </>
              )}
            </p>
          )}
        </>
      )}
      {problem && (
        <p className="plan-problem" role="alert">
          {problem}
        </p>
      )}
    </div>
  )
}

// Shown inside the Instagram card, not in a dialog: five steps while the user still has Instagram open.
export function InstagramGuide({ onClose, autoFocus }: { onClose: () => void; autoFocus?: boolean }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (autoFocus) ref.current?.focus()
  }, [autoFocus])
  return (
    <div className="note-box ig-guide" id="ig-guide" ref={ref} tabIndex={-1}>
      <b>Instagram hanya bisa dihubungkan bila akunnya Bisnis atau Kreator. Ubahnya dulu, gratis dan tidak mengubah pengikut Anda.</b>
      <ol>
        <li>Buka aplikasi Instagram, masuk ke Profil.</li>
        <li>
          Ketuk menu (tiga garis) lalu <b>Pengaturan dan aktivitas</b>.
        </li>
        <li>
          Pilih <b>Jenis akun dan alat</b>, lalu <b>Beralih ke akun profesional</b>.
        </li>
        <li>
          Pilih <b>Bisnis</b> (untuk toko) atau <b>Kreator</b>, lalu ikuti langkahnya sampai selesai.
        </li>
        <li>
          Kembali ke sini dan tekan <b>Hubungkan</b> lagi.
        </li>
      </ol>
      <p className="quiet small">Nama menu bisa sedikit berbeda menurut versi aplikasi.</p>
      <button type="button" className="btn link" onClick={onClose}>
        Tutup panduan
      </button>
    </div>
  )
}

const STATUS: Record<SocialPost['status'], { cls: string; label: string }> = {
  draft: { cls: 'idle', label: 'Draf' },
  awaiting_approval: { cls: 'wait', label: 'Menunggu persetujuan Anda' },
  publishing: { cls: 'run', label: 'Sedang diunggah' },
  published: { cls: 'ok', label: 'Terbit' },
  failed: { cls: 'bad', label: 'Gagal' },
}

function PostThumb({ id }: { id?: string }) {
  const { src, state } = useArtifactSrc({ id: id ?? '', bytes: 0, mime: 'image/jpeg' }, { thumb: true, enabled: !!id })
  if (state === 'ok' && src) return <img className="sp-thumb" src={src} alt="" />
  return <span className="sp-thumb sp-thumb-empty" aria-hidden="true" />
}

// The list inside the connected Instagram card. Read-only: decisions happen on the approval card.
export function SocialPostList() {
  const [nonce, setNonce] = useState(0)
  const load = useCallback(() => api.socialPosts({ platform: 'instagram', limit: 20 }), [nonce])
  const d = useLoad(load)
  const items = d.data ?? []
  const publishing = items.some((p) => p.status === 'publishing')
  useEffect(() => {
    if (!publishing) return
    const t = window.setInterval(() => setNonce((n) => n + 1), 5000)
    return () => window.clearInterval(t)
  }, [publishing])

  return (
    <div id="ig-posts" className="social-posts">
      <h3>Posting Instagram{d.state === 'ok' ? ` · ${items.length}` : ''}</h3>
      {d.state === 'loading' ? (
        <Loading text="Memuat daftar posting…" shape="lines" rows={2} />
      ) : d.state === 'error' ? (
        <ErrorLine text="Daftar posting belum bisa dimuat. Coba lagi sebentar." onRetry={d.retry} />
      ) : items.length === 0 ? (
        <p className="quiet">Belum ada posting. Minta pegawai menyiapkan satu lewat chat.</p>
      ) : (
        <ul className="sp-list">
          {items.map((p) => {
            const s = STATUS[p.status] ?? { cls: 'idle', label: 'Status belum dikenal' }
            return (
              <li key={p.id} className="sp-row">
                <PostThumb id={p.attachment_ids[0]} />
                <div className="sp-main">
                  <p className="sp-cap clamp2">{p.caption || 'Tanpa keterangan'}</p>
                  <small className="quiet num">{p.status === 'published' ? `Terbit ${stamp(p.published_at)}` : `Dibuat ${ago(p.created_at)}`}</small>
                  {p.status === 'failed' && p.error && <small className="err">{p.error}</small>}
                </div>
                <div className="sp-status">
                  <span className={`pill ${s.cls}`}>{s.label}</span>
                  {p.status === 'published' && p.permalink && (
                    <a className="btn link small" href={p.permalink} target="_blank" rel="noopener noreferrer">
                      Lihat di Instagram
                    </a>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
