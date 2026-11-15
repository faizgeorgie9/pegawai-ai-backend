import { useRef, useState } from 'react'
import { api, errText } from './bff'
import type { KbItem } from './bff'
import { CLOSE, Icon } from './ui'

// Knowledge Base in the composer (shared by Chat and Group): an attachment icon for files, a chip under a pasted link,
// and an inline status line per item. The BFF does the work (bff/kb.py); this file only shows it.

export const KB_ACCEPT = '.txt,.md,.csv,.pdf,.docx'
export const KB_TYPES_TEXT = 'TXT, MD, CSV, PDF, DOCX (maksimal 10 MB)'
const PAPERCLIP = 'm21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48'
const URL_RE = /https?:\/\/[^\s<>"'`]+/gi
// Same words as INTENT_RE in bff/kb.py: the BFF decides, this only shows "memproses" while it reads the link.
const INTENT_RE = /\b(simpan\w*|simpen\w*|pelajari\w*|baca\w*|bacain|jadikan|jadiin|masukkan|masukin|tambahkan|tambahin|hafal\w*|ingat\w*|serap|save|read|learn|study|memorize|remember|store|ingest|index|knowledge)\b|\badd\b.{0,30}\b(knowledge|kb)\b/i

export function urlsIn(text: string): string[] {
  const out: string[] = []
  for (const m of text.match(URL_RE) ?? []) {
    const u = m.replace(/[.,;:!?)\]}>]+$/, '')
    if (!out.includes(u)) out.push(u)
  }
  return out
}
export const asksToSave = (text: string) => urlsIn(text).length > 0 && INTENT_RE.test(text.replace(URL_RE, ' '))

export const KB_KIND: Record<KbItem['kind'], string> = { file: 'Berkas', url: 'Website', gdrive: 'Google Drive' }
export function bytes(n: number | null): string {
  if (n == null) return '–'
  return n < 1024 ? `${n} B` : n < 1024 * 1024 ? `${Math.round(n / 1024)} KB` : `${(n / 1024 / 1024).toFixed(1)} MB`
}

interface TrayItem {
  key: string
  label: string
  url?: string
  state: 'processing' | 'ready' | 'failed'
  id?: string
  error?: string
}

export function useKbTray(draft: string) {
  const [tray, setTray] = useState<TrayItem[]>([])
  const [skipped, setSkipped] = useState<string[]>([])
  const n = useRef(0)
  const patch = (key: string, p: Partial<TrayItem>) => setTray((cur) => cur.map((t) => (t.key === key ? { ...t, ...p } : t)))
  function track(label: string, work: Promise<KbItem>, url?: string) {
    const key = `kb${++n.current}`
    setTray((cur) => [...cur, { key, label, url, state: 'processing' }])
    work.then(
      (i) => patch(key, i.status === 'ready' ? { state: 'ready', id: i.id ?? undefined } : { state: 'failed', error: i.error ?? 'Gagal diproses.' }),
      (e) => patch(key, { state: 'failed', error: errText(e) }),
    )
  }
  return {
    tray,
    addFiles: (files: FileList | File[]) => Array.from(files).forEach((f) => track(f.name, api.kbUpload(f))),
    saveLink: (url: string) => track(url.replace(/^https?:\/\//, ''), api.kbAddLink(url), url),
    // detected links that were neither saved from here nor dismissed
    links: urlsIn(draft).slice(0, 3).filter((u) => !skipped.includes(u) && !tray.some((t) => t.url === u)),
    skip: (url: string) => setSkipped((s) => [...s, url]),
    remove: (key: string) => setTray((cur) => cur.filter((t) => t.key !== key)),
    // ids to attach to the message being sent; the tray is emptied except for items still being read
    take: () => {
      const ids = tray.filter((t) => t.state === 'ready' && t.id).map((t) => t.id as string)
      setTray((cur) => cur.filter((t) => t.state === 'processing'))
      return ids
    },
  }
}
export type KbTray = ReturnType<typeof useKbTray>

export function KbAttach({ kb }: { kb: KbTray }) {
  const input = useRef<HTMLInputElement>(null)
  return (
    <>
      <input
        ref={input}
        type="file"
        multiple
        hidden
        accept={KB_ACCEPT}
        aria-label="Pilih berkas untuk Knowledge Base"
        onChange={(e) => {
          if (e.target.files?.length) kb.addFiles(e.target.files)
          e.target.value = ''
        }}
      />
      <button type="button" className="icon-btn kb-attach" aria-label="Lampirkan berkas ke Knowledge Base" title={`Lampirkan berkas: ${KB_TYPES_TEXT}`} onClick={() => input.current?.click()}>
        <Icon d={PAPERCLIP} size={18} />
      </button>
    </>
  )
}

// The BFF's "needs Drive" failure (kb.py DRIVE_NEEDS_CONNECT) links to the draft connection cards in Kemampuan > Tools.
export const needsDrive = (e?: string | null) => !!e && e.includes('Google Drive') && e.includes('tanpa login')
export const DriveLink = () => (
  <>
    {' '}
    <a className="kb-drive-link" href="#/tools">Lihat Hubungkan aplikasi</a>
  </>
)
const STATE_TEXT = { processing: 'memproses…', ready: 'tersimpan', failed: 'gagal' } as const

export function KbTrayView({ kb }: { kb: KbTray }) {
  if (!kb.tray.length && !kb.links.length) return null
  return (
    <ul className="kb-tray" aria-label="Knowledge Base">
      {kb.tray.map((t) => (
        <li key={t.key} className="kb-chip" data-s={t.state} role={t.state === 'failed' ? 'alert' : undefined}>
          <span className="kb-dot" aria-hidden="true" />
          <span className="kb-name">{t.label}</span>
          <span className="kb-state">
            {STATE_TEXT[t.state]}
            {t.state === 'failed' && t.error ? `: ${t.error}` : ''}
            {t.state === 'failed' && needsDrive(t.error) && <DriveLink />}
          </span>
          <button type="button" className="icon-btn tiny" aria-label={`Lepas ${t.label}`} onClick={() => kb.remove(t.key)}>
            <Icon d={CLOSE} size={12} />
          </button>
        </li>
      ))}
      {kb.links.map((u) => (
        <li key={u} className="kb-chip" data-s="link">
          <span className="kb-name">{u.replace(/^https?:\/\//, '')}</span>
          <button type="button" className="btn link sm" onClick={() => kb.saveLink(u)}>
            Simpan ke Knowledge Base
          </button>
          <button type="button" className="icon-btn tiny" aria-label="Sembunyikan" onClick={() => kb.skip(u)}>
            <Icon d={CLOSE} size={12} />
          </button>
        </li>
      ))}
    </ul>
  )
}

// Status lines under a user message: what happened to the links it asked to save.
export function KbLines({ items, busy }: { items?: KbItem[]; busy?: boolean }) {
  if (!items?.length && !busy) return null
  return (
    <div className="kb-lines">
      {busy && <p className="kb-line" data-s="processing">Knowledge Base: memproses link…</p>}
      {items?.map((i, n) => (
        <p key={n} className="kb-line" data-s={i.status} role={i.status === 'failed' ? 'alert' : undefined}>
          Knowledge Base: {i.status === 'ready' ? `tersimpan, ${i.name}` : `gagal menyimpan ${i.source ?? i.name}. ${i.error ?? ''}`}
          {i.status === 'failed' && needsDrive(i.error) && <DriveLink />}
        </p>
      ))}
    </div>
  )
}
