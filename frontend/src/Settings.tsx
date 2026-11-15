import { useCallback, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { api, errText } from './bff'
import type { KbItem, Money, MonthUsage } from './bff'
import { useData } from './data'
import { SourcePicker } from './pick-ui'
import { DriveLink, KB_ACCEPT, KB_KIND, KB_TYPES_TEXT, bytes, needsDrive } from './kb-ui'
import { ErrorLine, nf } from './ui'
import { CostMeter, Loading, PageHead, Perkiraan, useLoad } from './ui-extra'

// #/pengaturan/<bagian>. Left: the sections (a scrolling row on small screens). Right: the section, one sentence per option.
const SECTIONS = [
  { id: 'umum', label: 'Umum' },
  { id: 'notifikasi', label: 'Notifikasi' },
  { id: 'keamanan', label: 'Keamanan dan izin' },
  { id: 'knowledge', label: 'Knowledge base' },
  { id: 'paket', label: 'Paket dan pemakaian' },
  { id: 'data', label: 'Data' },
] as const

const ZONES: [string, string][] = [['Asia/Jakarta', 'WIB (Asia/Jakarta)'], ['Asia/Makassar', 'WITA (Asia/Makassar)'], ['Asia/Jayapura', 'WIT (Asia/Jayapura)']]

export default function Settings({ section }: { section?: string }) {
  const cur = SECTIONS.find((s) => s.id === section)?.id ?? 'umum'
  return (
    <section className="page">
      <PageHead title="Pengaturan" sub="Pilihan untuk seluruh ruang kerja." />
      <div className="set-layout">
        <nav className="set-nav" aria-label="Bagian pengaturan">
          {SECTIONS.map((s) => (
            <a key={s.id} href={`#/pengaturan/${s.id}`} aria-current={s.id === cur ? 'page' : undefined}>
              {s.label}
            </a>
          ))}
        </nav>
        <div className="set-body">
          {cur === 'umum' && <General />}
          {cur === 'notifikasi' && <Notifications />}
          {cur === 'keamanan' && <Security />}
          {cur === 'knowledge' && <Knowledge />}
          {cur === 'paket' && <Plan />}
          {cur === 'data' && <DataSection />}
        </div>
      </div>
    </section>
  )
}

function Row({ title, hint, children }: { title: string; hint: string; children: React.ReactNode }) {
  return (
    <div className="set-row">
      <div className="set-text">
        <b>{title}</b>
        <small className="quiet">{hint}</small>
      </div>
      <div className="set-ctl">{children}</div>
    </div>
  )
}

// Saves one change now and says so; shows the BFF's message when it refuses.
function useSave() {
  const { saveSettings, flash } = useData()
  const [problem, setProblem] = useState('')
  const save = async (p: Parameters<typeof saveSettings>[0], ok = 'Disimpan') => {
    setProblem('')
    try {
      await saveSettings(p)
      flash(ok)
    } catch (e) {
      setProblem(errText(e))
    }
  }
  return { save, problem: problem && <p className="problem-bar" role="alert">{problem}</p> }
}

// ---------- Umum ----------
function General() {
  const { settings } = useData()
  const { save, problem } = useSave()
  const [name, setName] = useState(settings.company_name)
  const [dark, setDark] = useState(() => document.documentElement.dataset.theme === 'dark')
  const setTheme = (v: boolean) => {
    setDark(v)
    if (v) document.documentElement.dataset.theme = 'dark'
    else delete document.documentElement.dataset.theme
    try {
      localStorage.setItem('pa.theme', v ? 'dark' : 'light')
    } catch {
      /* not remembered */
    }
  }
  const dirty = name.trim() !== settings.company_name
  return (
    <div className="set-sec">
      <h2>Umum</h2>
      <Row title="Nama perusahaan" hint="Tampil di menu samping.">
        <form
          className="set-inline"
          onSubmit={(e) => {
            e.preventDefault()
            if (dirty) void save({ company_name: name.trim() })
          }}
        >
          <input value={name} maxLength={40} aria-label="Nama perusahaan" onChange={(e) => setName(e.target.value)} />
          <button type="submit" className="btn primary" disabled={!dirty || !name.trim()}>
            Simpan
          </button>
        </form>
      </Row>
      <Row title="Bahasa" hint="Bahasa lain belum tersedia.">
        <select value="id" disabled aria-label="Bahasa">
          <option value="id">Bahasa Indonesia</option>
        </select>
      </Row>
      <Row title="Zona waktu" hint="Disimpan untuk jadwal dan tampilan waktu. Tampilan waktu belum mengikutinya.">
        <select value={settings.timezone} aria-label="Zona waktu" onChange={(e) => void save({ timezone: e.target.value })}>
          {ZONES.map(([v, l]) => (
            <option key={v} value={v}>
              {l}
            </option>
          ))}
        </select>
      </Row>
      <Row title="Tema" hint="Terang atau gelap. Diingat di peramban ini.">
        <div className="seg" role="group" aria-label="Tema">
          <button type="button" aria-pressed={!dark} onClick={() => setTheme(false)}>
            Terang
          </button>
          <button type="button" aria-pressed={dark} onClick={() => setTheme(true)}>
            Gelap
          </button>
        </div>
      </Row>
      {problem}
    </div>
  )
}

// ---------- Notifikasi ----------
function Notifications() {
  const { settings } = useData()
  const { save, problem } = useSave()
  const [perm, setPerm] = useState(() => ('Notification' in window ? Notification.permission : 'unsupported'))
  const items: [keyof typeof settings.notify, string, string][] = [
    ['done', 'Tugas selesai', 'Kabar saat agen selesai bekerja.'],
    ['input', 'Butuh izin atau jawaban', 'Kabar saat agen menunggu persetujuan atau menjawab pertanyaan Anda.'],
    ['failed', 'Tugas gagal', 'Kabar saat tugas berhenti karena galat.'],
  ]
  return (
    <div className="set-sec">
      <h2>Notifikasi</h2>
      <Row
        title="Notifikasi browser"
        hint={perm === 'granted' ? 'Diizinkan. Muncul saat tab ini tidak dibuka.' : perm === 'denied' ? 'Diblokir di peramban. Ubah izin situs di peramban Anda.' : perm === 'unsupported' ? 'Peramban ini tidak mendukung notifikasi.' : 'Belum diizinkan.'}
      >
        {perm === 'default' && (
          <button className="btn outline" onClick={() => void Notification.requestPermission().then(setPerm)}>
            Izinkan
          </button>
        )}
        {perm === 'granted' && <span className="pill ok">Aktif</span>}
      </Row>
      {items.map(([k, t, h]) => (
        <Row key={k} title={t} hint={h}>
          <label className="set-check">
            <input type="checkbox" checked={settings.notify[k]} onChange={(e) => void save({ notify: { ...settings.notify, [k]: e.target.checked } })} />
            <span>{settings.notify[k] ? 'Nyala' : 'Mati'}</span>
          </label>
        </Row>
      ))}
      {problem}
    </div>
  )
}

// ---------- Keamanan dan izin (hanya baca) ----------
function Security() {
  const fn = useCallback(() => api.security(), [])
  const s = useLoad(fn)
  return (
    <div className="set-sec">
      <h2>Keamanan dan izin</h2>
      <p className="quiet">Hanya untuk dilihat. Pembatasan ini dipasang tim AITopTrends di tiap agen.</p>
      {s.state === 'loading' && <Loading text="Memuat pembatasan..." shape="table" />}
      {s.state === 'error' && <ErrorLine text={s.error} onRetry={s.retry} />}
      {s.state === 'ok' && s.data && (
        <div className="table-wrap">
          <table className="plain">
            <thead>
              <tr>
                <th>Agen</th>
                <th>Alat yang dimatikan</th>
                <th>Persetujuan</th>
              </tr>
            </thead>
            <tbody>
              {s.data.bots.map((b) => (
                <tr key={b.bot_id}>
                  <td data-label="Agen">{b.name}</td>
                  <td data-label="Alat yang dimatikan">
                    {!b.ok ? (
                      <span className="quiet">Belum terbaca</span>
                    ) : b.blocked.length === 0 ? (
                      <span className="pill warn">Tidak ada</span>
                    ) : (
                      <div className="chip-row">
                        {b.blocked.map((t) => (
                          <span key={t} className="pill">
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </td>
                  <td data-label="Persetujuan">{b.approvals === 'manual' ? 'Manual: perlu izin Anda' : b.approvals ?? 'Tidak diketahui'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ---------- Knowledge base ----------
const STATUS_TEXT = { processing: 'Memproses', ready: 'Tersimpan', failed: 'Gagal' } as const
const dayOf = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' }) : '–')

// The user's own sources (files and links added here or from the chat). The BFF keeps them per user and gives the best
// matching excerpts to every agent, citing the source name.
function MySources() {
  const [n, setN] = useState(0)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const fn = useCallback(() => api.kbItems(), [n])
  const items = useLoad(fn)
  const file = useRef<HTMLInputElement>(null)
  const [url, setUrl] = useState('')
  const [busy, setBusy] = useState('')
  const [problem, setProblem] = useState('')
  const [asking, setAsking] = useState<string | null>(null)
  const [picker, setPicker] = useState<'gdrive' | 'notion' | null>(null)
  const [refreshing, setRefreshing] = useState<string | null>(null)
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
      <h3>Sumber milik Anda</h3>
      <p className="quiet">
        Berkas dan link yang Anda simpan. Semua agen Anda bisa memakainya dan menyebut nama sumbernya. Bisa juga ditambah langsung dari chat: klik ikon klip, atau tempel link dan tulis &ldquo;simpan&rdquo;. Pencarian memakai kata kunci.
      </p>
      <div className="kb-add">
        <input
          ref={file}
          type="file"
          hidden
          accept={KB_ACCEPT}
          aria-label="Pilih berkas"
          onChange={(e) => {
            const f = e.target.files?.[0]
            e.target.value = ''
            if (f) void add(f.name, () => api.kbUpload(f))
          }}
        />
        <button className="btn outline" disabled={!!busy} onClick={() => file.current?.click()}>
          Unggah berkas
        </button>
        <button className="btn outline" disabled={!!busy} onClick={() => setPicker('gdrive')}>
          Pilih dari Drive
        </button>
        <button className="btn outline" disabled={!!busy} onClick={() => setPicker('notion')}>
          Pilih dari Notion
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
      <p className="meta">Berkas: {KB_TYPES_TEXT}. Link Google Drive tanpa login hanya untuk dokumen yang dibagikan ke &ldquo;siapa saja yang memiliki link&rdquo;. Untuk Drive pribadi atau Notion, hubungkan akun lebih dulu di Kemampuan &gt; Alat.</p>
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
          <b>Belum ada sumber.</b>
          <p className="quiet">Unggah berkas atau tempel link di atas, atau tambahkan dari chat.</p>
        </div>
      )}
      <ul className="kb-list">
        {items.data?.map((i) => (
          <li key={i.id} className="kb-row" data-s={i.status}>
            <span className="pill">{KB_KIND[i.kind]}</span>
            <div className="kb-rtext">
              <b className="kb-rname">{i.name}</b>
              {i.source && <span className="meta kb-src">{i.source}</span>}
              <span className="meta">
                {[i.size_bytes != null && bytes(i.size_bytes), dayOf(i.created_at)].filter(Boolean).join(' · ')}
              </span>
              {i.status === 'failed' && <span className="meta bad kb-why">{i.error}</span>}
            </div>
            <span className={`pill ${i.status === 'ready' ? 'cap-ok' : i.status === 'failed' ? 'cap-blocked' : 'cap-mock'}`}>{STATUS_TEXT[i.status]}</span>
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
      {picker && <SourcePicker provider={picker} onClose={() => setPicker(null)} onDone={() => setN((x) => x + 1)} />}
    </div>
  )
}

function Knowledge() {
  const fn = useCallback(() => api.knowledge(), [])
  const k = useLoad(fn)
  return (
    <div className="set-sec">
      <h2>Knowledge base</h2>
      <MySources />
      <h3>Dokumen bawaan</h3>
      <p className="quiet">Dokumen yang dimuat ke tugas Marketing dan CS. Mengganti dokumen belum bisa dari sini.</p>
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

// ---------- Paket dan pemakaian ----------
const dayText = (d: string) => new Date(`${d}T00:00:00`).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })

function Split({ title, rows }: { title: string; rows: { key: string; name: ReactNode; cost: Money; tokens: number; est: boolean }[] }) {
  const top = Math.max(...rows.map((r) => Number(r.cost.usd)), 0)
  return (
    <div>
      <h3>{title}</h3>
      <ul className="usage-list">
        {rows.map((r) => (
          <li key={r.key}>
            <span className="row-top">
              <span>
                {r.name} {r.est && <Perkiraan />}
              </span>
              <b className="num">{r.cost.label}</b>
            </span>
            <span className="bar-sm" aria-hidden="true">
              <span style={{ width: `${top > 0 ? Math.max(2, (Number(r.cost.usd) / top) * 100) : 2}%` }} />
            </span>
            <small className="quiet num">{nf.format(r.tokens)} token</small>
          </li>
        ))}
      </ul>
    </div>
  )
}

function UsageDetail({ u }: { u: MonthUsage }) {
  if (u.tokens.runs === 0) return <p className="quiet">Belum ada pemakaian bulan ini. Biaya muncul di sini setelah agen mengerjakan tugas.</p>
  const days = Math.max(...u.by_day.map((d) => Number(d.cost.usd)), 0)
  return (
    <>
      <div className="usage-split">
        <Split title="Per agen" rows={u.by_agent.map((a) => ({ key: a.bot_id, name: a.name, cost: a.cost, tokens: a.tokens, est: a.estimated }))} />
        <Split
          title="Per model"
          rows={u.by_model.map((m) => ({ key: `${m.provider}/${m.model}`, name: m.priced ? m.model : `${m.model} (belum ada harga)`, cost: m.cost, tokens: m.tokens, est: m.estimated }))}
        />
      </div>
      <div className="usage-days">
        <h3>Per hari</h3>
        <ul className="usage-list">
          {u.by_day.map((d) => (
            <li key={d.day}>
              <span className="day num">{dayText(d.day)}</span>
              <span className="bar-sm" aria-hidden="true">
                <span style={{ width: `${days > 0 ? Math.max(2, (Number(d.cost.usd) / days) * 100) : 2}%` }} />
              </span>
              <b className="amt num">{d.cost.label}</b>
            </li>
          ))}
        </ul>
      </div>
      {u.unpriced_tokens > 0 && <p className="note-box">{nf.format(u.unpriced_tokens)} token belum dihitung karena modelnya belum punya harga.</p>}
    </>
  )
}

function Plan() {
  const { me, loadState } = useData()
  const spent = me?.usage.cost.usd // refetch the breakdown when the month's cost changes
  const fn = useCallback(() => api.usageMonth(), [spent])
  const m = useLoad(fn)
  if (!me) return <div className="set-sec">{loadState === 'loading' ? <Loading text="Memuat paket..." /> : <p className="quiet">Data paket belum terbaca.</p>}</div>
  const { usage: u } = me
  const d = m.data
  return (
    <div className="set-sec">
      <h2>Paket dan pemakaian</h2>
      <dl className="kv">
        <dt>Paket aktif</dt>
        <dd>{me.plan.name}</dd>
        <dt>Biaya bulan ini</dt>
        <dd>
          <CostMeter u={u} reasons={d?.estimate_reasons} />
        </dd>
        <dt>Pemakaian bulan ini (token)</dt>
        <dd>
          <span className="num">{nf.format(u.tokens_month)}</span>
        </dd>
        <dt>Agen</dt>
        <dd>
          <span className="num">{u.bots}</span> dari <span className="num">{me.limits.max_bots}</span>
        </dd>
        <dt>Grup</dt>
        <dd>
          <span className="num">{u.groups}</span> dari <span className="num">{me.limits.max_groups}</span>
        </dd>
        <dt>Tugas bersamaan</dt>
        <dd>
          <span className="num">{u.active_runs}</span> dari <span className="num">{me.limits.max_concurrent_runs}</span>
        </dd>
      </dl>
      <h2>Rincian biaya</h2>
      {d && (
        <p className="quiet small">
          {new Date(d.period.start).toLocaleDateString('id-ID', { month: 'long', year: 'numeric', timeZone: d.period.timezone })} ({d.period.timezone}), diperbarui{' '}
          {new Date(d.updated_at).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', timeZone: d.period.timezone })}. Dihitung dari token yang benar-benar terpakai (teks masuk, teks keluar, dan teks yang diingat ulang) dikali harga model per 1 juta token. Token adalah potongan kecil teks yang dibaca dan ditulis model. {d.basis === 'estimated' ? 'Angka berlabel "perkiraan" memakai harga yang belum diverifikasi.' : 'Semua harga sudah diverifikasi dari halaman resmi penyedia.'}
        </p>
      )}
      {m.state === 'loading' && !d && <Loading text="Memuat rincian..." />}
      {m.state === 'error' && !d && <ErrorLine text={m.error} onRetry={m.retry} />}
      {d && <UsageDetail u={d} />}
    </div>
  )
}

// ---------- Data ----------
function DataSection() {
  const { flash } = useData()
  const fn = useCallback(() => api.knowledge(), [])
  const k = useLoad(fn)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  async function exportAll() {
    setBusy(true)
    setProblem('')
    try {
      const blob = await api.exportHistory()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `riwayat-chat-${new Date().toISOString().slice(0, 10)}.json`
      document.body.append(a)
      a.click()
      a.remove()
      window.setTimeout(() => URL.revokeObjectURL(a.href), 4000)
      flash('Riwayat chat diekspor')
    } catch (e) {
      setProblem(errText(e))
    }
    setBusy(false)
  }
  return (
    <div className="set-sec">
      <h2>Data</h2>
      <Row title="Lama simpan log aktivitas" hint="Log pemakaian alat dihapus otomatis setelah masa ini. Hanya untuk dilihat.">
        <span className="num">{k.data ? `${k.data.retention_days} hari` : '90 hari'}</span>
      </Row>
      <Row title="Ekspor riwayat chat" hint="Semua chat dan grup dalam satu berkas JSON. Bisa memakan beberapa detik.">
        <button className="btn outline" disabled={busy} onClick={() => void exportAll()}>
          {busy ? 'Menyiapkan...' : 'Unduh JSON'}
        </button>
      </Row>
      {problem && (
        <p className="problem-bar" role="alert">
          {problem}
        </p>
      )}
    </div>
  )
}
