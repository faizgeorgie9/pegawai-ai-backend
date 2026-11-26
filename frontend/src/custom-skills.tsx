// R5 · Cara kerja khusus: the section under the existing skill switches on a pegawai's Keahlian tab.
// Plain-language screen for owners and staff. The BFF decides what is safe; this file never guesses "safe".

import { useCallback, useEffect, useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import { api, errText } from './bff'
import type { SkillFile, SkillFileDetail, SkillFileList, SkillScan } from './bff'
import { useAdminMode } from './adminMode'
import { useData } from './data'
import { ago, Dialog, ErrorLine, stamp } from './ui'
import { Empty, Loading, ProgressLine } from './ui-extra'
import { sizeText } from './attachments'
import { forgetReads } from './session-cache'
import { TEMPLATES } from './skill-templates'
import './custom-skills.css'

const MAX_ITEMS = 30
const MAX_BYTES = 65536
const TEXT_EXT = /\.(md|markdown|txt)$/i
const UPLOAD_WHY = 'Cara kerja dari luar bisa menyuruh pegawai melakukan hal yang tidak Anda minta. Periksa dulu isinya.'
const SKELETON = `---
name: nama-cara-kerja
description: Jelaskan kapan pegawai memakai cara kerja ini.
---

# Judul

Tulis langkah-langkahnya di sini.`

const SCAN: Record<SkillScan, { cls: string; text: string }> = {
  safe: { cls: 'ok', text: 'Sudah diperiksa' },
  caution: { cls: 'warn', text: 'Perlu Anda periksa' },
  dangerous: { cls: 'bad', text: 'Ditolak: tidak aman' },
}

const humanName = (name: string) => {
  const words = name.replace(/-/g, ' ')
  return words ? words.charAt(0).toUpperCase() + words.slice(1) : ''
}

type Picked =
  | { kind: 'add' }
  | { kind: 'templates' }
  | { kind: 'editor'; mode: 'new' | 'edit' | 'view'; item?: SkillFile; content?: string; fromUpload?: boolean }

export function CustomSkills({ slug, canEdit }: { slug: string; canEdit: boolean }) {
  const admin = useAdminMode()
  const { flash } = useData()
  const [list, setList] = useState<SkillFileList | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tick, setTick] = useState(0)
  const [busy, setBusy] = useState<{ name: string; what: 'toggle' | 'delete' } | null>(null)
  const [rowErr, setRowErr] = useState<Record<string, string>>({})
  const [askDelete, setAskDelete] = useState('')
  const [confirmOn, setConfirmOn] = useState('')
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [newName, setNewName] = useState('')
  const [picked, setPicked] = useState<Picked | null>(null)

  // First load and Retry. A new slug starts from a clean slate so the old agent's list never flashes.
  useEffect(() => {
    let live = true
    setList(null)
    setLoading(true)
    setError('')
    setBusy(null)
    setAskDelete('')
    setConfirmOn('')
    setNotes({})
    setNewName('')
    setRowErr({})
    api.skillFiles(slug).then(
      (r) => {
        if (!live) return
        setList(r)
        setError('')
        setLoading(false)
      },
      (e) => {
        if (!live) return
        setError(errText(e))
        setLoading(false)
      },
    )
    return () => {
      live = false
    }
  }, [slug, tick])

  // After every change the BFF's list is fetched again; the screen never trusts the click.
  const refresh = useCallback(async () => {
    try {
      const r = await api.skillFiles(slug)
      setList(r)
      setError('')
    } catch (e) {
      setError(errText(e))
    }
  }, [slug])

  const items = [...(list?.items ?? [])].sort((a, b) => Number(b.enabled) - Number(a.enabled) || b.updated_at - a.updated_at)
  const allowed = canEdit && (list?.can_edit ?? true)
  const full = items.length >= MAX_ITEMS

  const clearRowErr = (name: string) => setRowErr((m) => ({ ...m, [name]: '' }))

  async function changeEnabled(s: SkillFile, on: boolean) {
    setConfirmOn('')
    setBusy({ name: s.name, what: 'toggle' })
    clearRowErr(s.name)
    try {
      await api.setSkillFileEnabled(slug, s.name, on)
      forgetReads('skills')
      await refresh()
    } catch (e) {
      setRowErr((m) => ({ ...m, [s.name]: errText(e) }))
    } finally {
      setBusy(null)
    }
  }

  async function toggle(s: SkillFile, on: boolean) {
    setAskDelete('')
    clearRowErr(s.name)
    if (on && s.scan === 'caution') {
      setConfirmOn(s.name)
      if (notes[s.name] === undefined) {
        try {
          const detail = await api.skillFile(slug, s.name)
          setNotes((m) => ({ ...m, [s.name]: detail.scan_note }))
        } catch {
          setNotes((m) => ({ ...m, [s.name]: '' }))
        }
      }
      return
    }
    await changeEnabled(s, on)
  }

  async function remove(s: SkillFile) {
    setBusy({ name: s.name, what: 'delete' })
    clearRowErr(s.name)
    try {
      await api.deleteSkillFile(slug, s.name)
      forgetReads('skills')
      setAskDelete('')
      if (newName === s.name) setNewName('')
      await refresh()
    } catch (e) {
      setRowErr((m) => ({ ...m, [s.name]: errText(e) }))
    } finally {
      setBusy(null)
    }
  }

  function onSaved(saved: SkillFile) {
    setPicked(null)
    setNewName(saved.scan === 'caution' ? saved.name : '')
    if (saved.scan === 'caution') {
      flash('Tersimpan, tapi belum aktif. Ada bagian yang perlu Anda periksa. Aktifkan dari daftar bila sudah yakin.')
    } else {
      flash(`Cara kerja “${humanName(saved.name)}” tersimpan`)
    }
    forgetReads('skills')
    void refresh()
  }

  return (
    <section className="cs-sec" aria-labelledby="cs-h">
      <header className="cs-head">
        <h3 id="cs-h">Cara kerja khusus</h3>
        {allowed && (
          <button type="button" className="btn primary" disabled={full || loading} onClick={() => setPicked({ kind: 'add' })}>
            Tambah cara kerja
          </button>
        )}
      </header>
      <p className="quiet cs-intro">Tulis atau unggah petunjuk langkah demi langkah. Pegawai langsung memakainya di percakapan berikutnya.</p>
      {!allowed && <p className="note-box cs-note">Hanya pemilik yang bisa mengubah cara kerja khusus. Anda bisa melihat isinya.</p>}
      {allowed && full && <p className="quiet cs-limit">Batas 30 cara kerja tercapai. Hapus yang tidak dipakai.</p>}

      {loading && !list && <Loading text="Memuat cara kerja khusus..." shape="lines" rows={3} />}
      {error && !list && (
        <ErrorLine
          text="Cara kerja khusus belum bisa dimuat. Coba lagi sebentar."
          onRetry={() => {
            setLoading(true)
            setTick((n) => n + 1)
          }}
        />
      )}
      {error && list && (
        <p className="problem-bar" role="alert">
          {error}
        </p>
      )}

      {list && items.length === 0 && allowed && (
        <Empty title="Belum ada cara kerja khusus">
          Cara kerja khusus adalah petunjuk tertulis yang dipakai pegawai ini setiap kali tugasnya cocok. Mulai dari contoh, atau tulis sendiri.
          <span className="cs-empty-act">
            <button type="button" className="btn primary" onClick={() => setPicked({ kind: 'templates' })}>
              Buat dari contoh
            </button>
            <button type="button" className="btn soft" onClick={() => setPicked({ kind: 'editor', mode: 'new', content: SKELETON })}>
              Tulis sendiri
            </button>
          </span>
        </Empty>
      )}
      {list && items.length === 0 && !allowed && <Empty title="Belum ada cara kerja khusus">Belum ada.</Empty>}

      {items.length > 0 && (
        <ul className="cs-list">
          {items.map((s) => {
            const title = humanName(s.name)
            const busyRow = busy?.name === s.name
            const scanning = SCAN[s.scan]
            return (
              <li
                key={s.name}
                className="cs-row"
                data-new={newName === s.name ? '' : undefined}
                onClick={() => {
                  if (newName === s.name) setNewName('')
                }}
              >
                {askDelete === s.name ? (
                  <div className="cs-confirm" role="alert">
                    <p>Hapus “{title}”? Pegawai tidak akan memakainya lagi.</p>
                    <span className="confirm-actions">
                      <button type="button" className="btn danger" disabled={busyRow} onClick={() => void remove(s)}>
                        {busyRow && busy?.what === 'delete' ? 'Menghapus…' : 'Hapus'}
                      </button>
                      <button type="button" className="btn quiet-btn" disabled={busyRow} onClick={() => setAskDelete('')}>
                        Batal
                      </button>
                    </span>
                  </div>
                ) : confirmOn === s.name ? (
                  <div className="cs-confirm note-box" role="alert">
                    <p>
                      Ada bagian yang perlu Anda periksa: {notes[s.name]?.replace(/[.!?]+$/, '') || 'isinya memuat hal yang tidak biasa'}. Aktifkan tetap?
                    </p>
                    <span className="confirm-actions">
                      <button type="button" className="btn primary" disabled={busyRow} onClick={() => void changeEnabled(s, true)}>
                        {busyRow ? 'Mengaktifkan…' : 'Aktifkan'}
                      </button>
                      <button type="button" className="btn quiet-btn" disabled={busyRow} onClick={() => setConfirmOn('')}>
                        Batal
                      </button>
                    </span>
                  </div>
                ) : (
                  <>
                    {allowed ? (
                      <label
                        className="ws-switch cs-sw"
                        title={s.scan === 'dangerous' ? 'Cara kerja ini tidak bisa diaktifkan.' : undefined}
                      >
                        <input
                          type="checkbox"
                          role="switch"
                          className="tgl"
                          checked={s.enabled}
                          disabled={busyRow || s.scan === 'dangerous'}
                          aria-label={`Aktifkan ${title}`}
                          onChange={(e) => void toggle(s, e.target.checked)}
                        />
                        <span className="sr">{s.enabled ? 'Aktif' : 'Mati'}</span>
                      </label>
                    ) : (
                      <span className={`pill ${s.enabled ? 'ok' : 'idle'}`}>{s.enabled ? 'Aktif' : 'Mati'}</span>
                    )}

                    <div className="cs-txt">
                      <p className="cs-title">{title}</p>
                      {s.description && <p className="cs-desc clamp2">{s.description}</p>}
                      <p className="cs-meta">
                        <span>
                          Diubah {ago(s.updated_at)} · {sizeText(s.bytes)}
                        </span>
                        <span className={`pill ${scanning.cls}`}>{scanning.text}</span>
                        {s.source === 'template' && <span className="pill plain">Dari contoh</span>}
                        {s.scan === 'dangerous' && <span className="cs-helpwarn">Cara kerja ini tidak bisa diaktifkan.</span>}
                        {admin && <span className="admin-tag">{s.name}</span>}
                        {admin && <span className="admin-tag">{s.category}</span>}
                      </p>
                    </div>

                    <div className="cs-acts">
                      <button
                        type="button"
                        className="btn soft"
                        disabled={busyRow}
                        onClick={() => setPicked({ kind: 'editor', mode: allowed ? 'edit' : 'view', item: s })}
                      >
                        {allowed ? 'Ubah' : 'Lihat'}
                      </button>
                      {allowed && (
                        <button
                          type="button"
                          className="btn link"
                          disabled={busyRow}
                          onClick={() => {
                            setConfirmOn('')
                            setAskDelete(s.name)
                          }}
                        >
                          Hapus
                        </button>
                      )}
                    </div>

                    {rowErr[s.name] && (
                      <p className="small err cs-row-err" role="alert">
                        {rowErr[s.name]}
                      </p>
                    )}
                  </>
                )}
              </li>
            )
          })}
        </ul>
      )}

      {picked?.kind === 'add' && (
        <AddDialog
          onClose={() => setPicked(null)}
          onTemplates={() => setPicked({ kind: 'templates' })}
          onWrite={() => setPicked({ kind: 'editor', mode: 'new', content: SKELETON })}
          onUpload={(content) => setPicked({ kind: 'editor', mode: 'new', content, fromUpload: true })}
        />
      )}
      {picked?.kind === 'templates' && (
        <TemplateDialog
          used={new Set(items.map((s) => s.name))}
          onClose={() => setPicked(null)}
          onBack={() => setPicked({ kind: 'add' })}
          onPick={(content) => setPicked({ kind: 'editor', mode: 'new', content })}
        />
      )}
      {picked?.kind === 'editor' && (
        <EditorDialog
          slug={slug}
          mode={picked.mode}
          item={picked.item}
          initialContent={picked.content}
          fromUpload={picked.fromUpload}
          onClose={() => setPicked(null)}
          onSaved={onSaved}
          onChanged={() => void refresh()}
        />
      )}
    </section>
  )
}

function AddDialog({
  onClose,
  onTemplates,
  onWrite,
  onUpload,
}: {
  onClose: () => void
  onTemplates: () => void
  onWrite: () => void
  onUpload: (content: string) => void
}) {
  const file = useRef<HTMLInputElement>(null)
  const [problem, setProblem] = useState('')

  async function picked(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    e.target.value = ''
    if (!f) return
    setProblem('')
    if (f.size > MAX_BYTES) {
      setProblem('Berkas terlalu besar. Maksimal 64 KB.')
      return
    }
    if (!TEXT_EXT.test(f.name)) {
      setProblem('Hanya berkas teks yang bisa diunggah.')
      return
    }
    let text = ''
    try {
      text = await f.text()
    } catch {
      setProblem('Berkas tidak bisa dibaca. Coba pilih berkas lain.')
      return
    }
    if (text.includes('\u0000')) {
      setProblem('Hanya berkas teks yang bisa diunggah.')
      return
    }
    onUpload(text)
  }

  return (
    <Dialog title="Tambah cara kerja" onClose={onClose}>
      <div className="dlg-body">
        <div className="cs-opts">
          <button type="button" className="cs-opt" onClick={onTemplates}>
            <b>Buat dari contoh</b>
            <span>Pilih contoh siap pakai untuk Colorbox, lalu sesuaikan.</span>
          </button>
          <button type="button" className="cs-opt" onClick={onWrite}>
            <b>Tulis sendiri</b>
            <span>Mulai dari lembar kosong dengan kerangka.</span>
          </button>
          <button type="button" className="cs-opt" onClick={() => file.current?.click()}>
            <b>Unggah berkas .md</b>
            <span>Pilih berkas teks dari komputer Anda. Anda bisa memeriksa isinya dulu sebelum menyimpan.</span>
          </button>
          <input ref={file} type="file" accept=".md,.markdown,text/markdown,text/plain" hidden onChange={(e) => void picked(e)} />
        </div>
        {problem && (
          <p className="problem-bar" role="alert">
            {problem}
          </p>
        )}
        <footer className="dlg-foot">
          <button type="button" className="btn quiet-btn" onClick={onClose}>
            Batal
          </button>
        </footer>
      </div>
    </Dialog>
  )
}

function TemplateDialog({
  used,
  onClose,
  onBack,
  onPick,
}: {
  used: Set<string>
  onClose: () => void
  onBack: () => void
  onPick: (content: string) => void
}) {
  const [selected, setSelected] = useState('')
  const chosen = TEMPLATES.find((t) => t.id === selected)

  function choose() {
    if (!chosen) return
    let content = chosen.content
    const found = /^name:\s*(.+)$/m.exec(content)
    if (found) {
      const base = found[1].trim()
      if (used.has(base)) {
        let n = 2
        while (used.has(`${base}-${n}`)) n += 1
        content = content.replace(/^name:\s*.+$/m, `name: ${base}-${n}`)
      }
    }
    onPick(content)
  }

  return (
    <Dialog title="Buat dari contoh" onClose={onClose} wide>
      <div className="dlg-body">
        <p>Ini contoh awal untuk Colorbox. Anda bisa mengubahnya sebelum disimpan.</p>
        <div className="cs-tpls" role="radiogroup" aria-label="Pilih contoh">
          {TEMPLATES.map((t) => (
            <label key={t.id} className="radio-row cs-tpl">
              <input type="radio" name="cs-template" checked={selected === t.id} onChange={() => setSelected(t.id)} />
              <span className="cs-tpl-body">
                <b>{t.title}</b>
                <small className="quiet">Cocok untuk {t.fit}</small>
                <span className="cs-tpl-prev">
                  {t.content
                    .replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/, '')
                    .split(/\r?\n/)
                    .map((line) => line.replace(/^#{1,6}\s*/, '').trim())
                    .filter(Boolean)
                    .slice(0, 3)
                    .join('\n')}
                </span>
              </span>
            </label>
          ))}
        </div>
        <footer className="dlg-foot">
          <button type="button" className="btn quiet-btn" onClick={onBack}>
            Kembali
          </button>
          <button type="button" className="btn primary" disabled={!chosen} onClick={choose}>
            Lanjut
          </button>
        </footer>
      </div>
    </Dialog>
  )
}

function EditorDialog({
  slug,
  mode,
  item,
  initialContent,
  fromUpload,
  onClose,
  onSaved,
  onChanged,
}: {
  slug: string
  mode: 'new' | 'edit' | 'view'
  item?: SkillFile
  initialContent?: string
  fromUpload?: boolean
  onClose: () => void
  onSaved: (saved: SkillFile) => void
  onChanged: () => void
}) {
  const admin = useAdminMode()
  const { flash } = useData()
  const name = item?.name ?? ''
  const [state, setState] = useState<'loading' | 'ok' | 'error'>(mode === 'new' ? 'ok' : 'loading')
  const [loadErr, setLoadErr] = useState('')
  const [detail, setDetail] = useState<SkillFileDetail | null>(null)
  const [content, setContent] = useState(initialContent ?? '')
  const [loaded, setLoaded] = useState(initialContent ?? '')
  const [category, setCategory] = useState('')
  const [problem, setProblem] = useState('')
  const [saving, setSaving] = useState(false)
  const [tick, setTick] = useState(0)
  const [askDiscard, setAskDiscard] = useState(false)
  const [askRestore, setAskRestore] = useState('')
  const [restoring, setRestoring] = useState('')
  const savingRef = useRef(false)
  const dialogRef = useRef<HTMLDialogElement | null>(null)
  const wrapRef = useRef<HTMLFormElement>(null)
  const dirtyRef = useRef(false)
  const dirty = mode !== 'view' && content !== loaded

  useEffect(() => {
    dirtyRef.current = dirty
  }, [dirty])

  useEffect(() => {
    if (mode === 'new' || !name) return
    let live = true
    setState('loading')
    setLoadErr('')
    api.skillFile(slug, name).then(
      (d) => {
        if (!live) return
        setDetail(d)
        setContent(d.content)
        setLoaded(d.content)
        setCategory(d.category)
        setState('ok')
      },
      (e) => {
        if (!live) return
        setLoadErr(errText(e))
        setState('error')
      },
    )
    return () => {
      live = false
    }
  }, [slug, name, mode, tick])

  // Keep the dialog open while a save runs, and ask before throwing away edits: Esc is cancelled, and
  // clicks on the header close button or the backdrop are stopped before the native dialog can close.
  useEffect(() => {
    const d = wrapRef.current?.closest<HTMLDialogElement>('dialog') ?? null
    dialogRef.current = d
    if (!d) return
    const cancel = (e: Event) => {
      if (savingRef.current || dirtyRef.current) {
        e.preventDefault()
        if (!savingRef.current) setAskDiscard(true)
      }
    }
    const click = (e: MouseEvent) => {
      if (!savingRef.current && !dirtyRef.current) return
      const target = e.target as HTMLElement
      if (target !== d && !target.closest('.dlg-head .icon-btn')) return
      e.preventDefault()
      e.stopPropagation()
      if (!savingRef.current) setAskDiscard(true)
    }
    d.addEventListener('cancel', cancel)
    d.addEventListener('click', click, true)
    return () => {
      d.removeEventListener('cancel', cancel)
      d.removeEventListener('click', click, true)
    }
  }, [])

  useEffect(() => {
    const d = dialogRef.current
    if (!d) return
    if (saving) d.setAttribute('data-cs-busy', '')
    else d.removeAttribute('data-cs-busy')
    return () => d.removeAttribute('data-cs-busy')
  }, [saving])

  const bytes = new TextEncoder().encode(content).length
  const tooBig = bytes > MAX_BYTES
  const title = mode === 'new' ? 'Cara kerja baru' : `${mode === 'edit' ? 'Ubah: ' : ''}${humanName(name)}`

  function requestClose() {
    if (savingRef.current) return
    if (dirty) {
      setAskDiscard(true)
      return
    }
    onClose()
  }

  async function save() {
    if (saving || mode === 'view' || state !== 'ok' || tooBig || !content.trim()) return
    setSaving(true)
    savingRef.current = true
    setProblem('')
    try {
      const saved =
        mode === 'new'
          ? await api.createSkillFile(slug, {
              content,
              ...(admin && category.trim() ? { category: category.trim() } : {}),
            })
          : await api.saveSkillFile(slug, name, content)
      onSaved(saved)
    } catch (e) {
      setProblem(errText(e))
    } finally {
      savingRef.current = false
      setSaving(false)
    }
  }

  async function restore(versionId: string) {
    if (!item) return
    const when = stamp(detail?.versions.find((v) => v.id === versionId)?.created_at ?? 0)
    setRestoring(versionId)
    setProblem('')
    try {
      await api.restoreSkillFile(slug, item.name, versionId)
      const d = await api.skillFile(slug, item.name)
      setDetail(d)
      setContent(d.content)
      setLoaded(d.content)
      setAskRestore('')
      setAskDiscard(false)
      forgetReads('skills')
      onChanged()
      flash(`Dikembalikan ke versi ${when}`)
    } catch (e) {
      setProblem(errText(e))
    } finally {
      setRestoring('')
    }
  }

  const banners: string[] = []
  if (mode === 'new' && fromUpload) banners.push(UPLOAD_WHY)
  if (mode === 'edit' && detail?.scan === 'caution' && detail.scan_note) banners.push(detail.scan_note)
  if (mode === 'edit' && dirty) banners.push(UPLOAD_WHY)

  return (
    <Dialog title={title} onClose={requestClose} wide>
      <form
        ref={wrapRef}
        className="dlg-body cs-editor"
        noValidate
        onSubmit={(e) => {
          e.preventDefault()
          void save()
        }}
      >
          <fieldset disabled={saving}>
            {banners.map((text, i) => (
              <p key={i} className="note-box" role="note">
                {text}
              </p>
            ))}

            {state === 'loading' && <Loading text="Memuat cara kerja..." shape="lines" rows={4} />}
            {state === 'error' && <ErrorLine text={loadErr || 'Cara kerja ini belum bisa dimuat. Coba lagi sebentar.'} onRetry={() => setTick((n) => n + 1)} />}

            {state === 'ok' && (
              <>
                {admin && mode === 'new' && (
                  <label className="field cs-cat">
                    <span>Kategori</span>
                    <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="khusus" />
                  </label>
                )}
                <label className="field cs-field">
                  <span>Isi cara kerja</span>
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    rows={16}
                    spellCheck={false}
                    readOnly={mode === 'view'}
                    data-autofocus
                    aria-describedby="cs-help cs-count"
                    aria-invalid={tooBig || undefined}
                  />
                </label>
                <div className="cs-help-row">
                  <p className="quiet small" id="cs-help">
                    Dua baris pertama (di antara tanda ---) berisi nama dan deskripsi singkat. Sisanya adalah petunjuknya.
                  </p>
                  <span id="cs-count" className={`counter num${tooBig ? ' err' : ''}`}>
                    {new Intl.NumberFormat('id-ID', { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(bytes / 1024)} / 64 KB
                  </span>
                </div>

                {mode === 'edit' && detail && (
                  <details className="cs-vers">
                    <summary>Versi sebelumnya ({detail.versions.length})</summary>
                    {detail.versions.length === 0 ? (
                      <p className="quiet small cs-vers-none">Belum ada versi sebelumnya.</p>
                    ) : (
                      <ul>
                        {detail.versions.map((v) => (
                          <li key={v.id}>
                            {askRestore === v.id ? (
                              <span className="cs-vers-confirm" role="alert">
                                <span>Kembalikan ke versi ini? Isi sekarang akan disimpan sebagai versi lama.</span>
                                <span className="confirm-actions">
                                  <button type="button" className="btn primary" disabled={!!restoring} onClick={() => void restore(v.id)}>
                                    {restoring === v.id ? 'Mengembalikan…' : 'Kembalikan'}
                                  </button>
                                  <button type="button" className="btn quiet-btn" disabled={!!restoring} onClick={() => setAskRestore('')}>
                                    Batal
                                  </button>
                                </span>
                              </span>
                            ) : (
                              <>
                                <span>{stamp(v.created_at)}</span>
                                <button type="button" className="btn link" disabled={!!restoring} onClick={() => setAskRestore(v.id)}>
                                  Kembalikan
                                </button>
                              </>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </details>
                )}

                {problem && (
                  <p className="problem-bar" role="alert">
                    {problem}
                  </p>
                )}
              </>
            )}
          </fieldset>

          <footer className="dlg-foot">
            {askDiscard ? (
              <span className="cs-discard" role="alert">
                <span>Buang perubahan?</span>
                <span className="confirm-actions">
                  <button type="button" className="btn danger" onClick={onClose}>
                    Buang
                  </button>
                  <button type="button" className="btn quiet-btn" onClick={() => setAskDiscard(false)}>
                    Lanjut menulis
                  </button>
                </span>
              </span>
            ) : mode === 'view' ? (
              <button type="button" className="btn primary" onClick={onClose}>
                Tutup
              </button>
            ) : (
              <>
                <button type="button" className="btn quiet-btn" disabled={saving} onClick={requestClose}>
                  Batal
                </button>
                <button type="submit" className="btn primary" disabled={saving || state !== 'ok' || tooBig || !content.trim()}>
                  {saving ? 'Memeriksa dan menyimpan…' : 'Simpan'}
                </button>
                {saving && <ProgressLine label="Memeriksa dan menyimpan cara kerja" />}
              </>
            )}
          </footer>
      </form>
    </Dialog>
  )
}
