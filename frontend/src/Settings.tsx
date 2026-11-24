import { useCallback, useEffect, useState } from 'react'
import { api, errText } from './bff'
import { useData } from './data'
import { ErrorLine, nf } from './ui'
import { Loading, PageHead, useLoad } from './ui-extra'

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
      <p className="quiet">Hanya untuk dilihat. Pembatasan ini dipasang tim backend di tiap agen.</p>
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
                      <span className="quiet">Belum terbaca dari Hermes</span>
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
function Knowledge() {
  const fn = useCallback(() => api.knowledge(), [])
  const k = useLoad(fn)
  return (
    <div className="set-sec">
      <h2>Knowledge base</h2>
      <p className="quiet">
        Instruksi CS v2.1 dan SOP resmi selalu dipakai lebih dulu. Unggahan di bawah hanya bukti tambahan untuk
        pertanyaan yang cocok.
      </p>
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
      <Uploads />
    </div>
  )
}

function Uploads() {
  const { flash } = useData()
  const fn = useCallback(() => api.knowledgeSources('all'), [])
  const list = useLoad(fn)
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [scope, setScope] = useState('cs')
  const [website, setWebsite] = useState('')
  const [websiteTitle, setWebsiteTitle] = useState('')
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const [query, setQuery] = useState('')
  const [matches, setMatches] = useState<{ title: string; text: string; score: number }[] | null>(null)
  const [searching, setSearching] = useState(false)

  const done = (message: string) => {
    flash(message)
    list.retry()
  }

  async function upload() {
    if (!file) {
      setProblem('Pilih berkas dulu.')
      return
    }
    setBusy(true)
    setProblem('')
    try {
      await api.addKnowledgeFile(file, title, scope)
      setFile(null)
      setTitle('')
      const input = document.getElementById('kb-file') as HTMLInputElement | null
      if (input) input.value = ''
      done('Dokumen ditambahkan')
    } catch (e) {
      setProblem(errText(e))
    }
    setBusy(false)
  }

  async function addSite() {
    if (!website.trim()) {
      setProblem('Isi alamat situs dulu.')
      return
    }
    setBusy(true)
    setProblem('')
    try {
      await api.addKnowledgeWebsite(website.trim(), websiteTitle, scope)
      setWebsite('')
      setWebsiteTitle('')
      done('Situs ditambahkan')
    } catch (e) {
      setProblem(errText(e))
    }
    setBusy(false)
  }

  async function remove(id: string) {
    setBusy(true)
    setProblem('')
    try {
      await api.deleteKnowledgeSource(id)
      done('Dokumen dihapus')
    } catch (e) {
      setProblem(errText(e))
    }
    setBusy(false)
  }

  async function search() {
    if (!query.trim()) return
    setSearching(true)
    setProblem('')
    try {
      setMatches((await api.searchKnowledge(query.trim(), scope)).map((m) => ({ title: m.title, text: m.text, score: m.score })))
    } catch (e) {
      setProblem(errText(e))
    }
    setSearching(false)
  }

  return (
    <>
      <h2 style={{ marginTop: 28 }}>Dokumen unggahan</h2>
      <p className="quiet small">PDF, DOCX, TXT, MD, CSV, atau JSON sampai 10 MB. Teks disimpan di server untuk pencarian.</p>
      <form
        className="set-inline"
        onSubmit={(e) => {
          e.preventDefault()
          void upload()
        }}
      >
        <input
          id="kb-file"
          type="file"
          accept=".pdf,.docx,.txt,.md,.csv,.json"
          aria-label="Berkas dokumen"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <input
          value={title}
          maxLength={160}
          placeholder="Judul (opsional)"
          aria-label="Judul dokumen"
          onChange={(e) => setTitle(e.target.value)}
        />
        <select value={scope} aria-label="Berlaku untuk" onChange={(e) => setScope(e.target.value)}>
          <option value="cs">CS</option>
          <option value="marketing">Marketing</option>
          <option value="all">CS dan Marketing</option>
        </select>
        <button type="submit" className="btn primary" disabled={busy || !file}>
          {busy ? 'Mengunggah...' : 'Unggah'}
        </button>
      </form>

      <form
        className="set-inline"
        onSubmit={(e) => {
          e.preventDefault()
          void addSite()
        }}
      >
        <input
          value={website}
          maxLength={2000}
          placeholder="https://contoh.com/kebijakan-retur"
          aria-label="Alamat situs"
          onChange={(e) => setWebsite(e.target.value)}
        />
        <input
          value={websiteTitle}
          maxLength={160}
          placeholder="Judul (opsional)"
          aria-label="Judul situs"
          onChange={(e) => setWebsiteTitle(e.target.value)}
        />
        <button type="submit" className="btn outline" disabled={busy || !website.trim()}>
          Tambah situs
        </button>
      </form>

      {problem && (
        <p className="problem-bar" role="alert">
          {problem}
        </p>
      )}

      {list.state === 'loading' && <Loading text="Memuat unggahan..." shape="lines" />}
      {list.state === 'error' && <ErrorLine text={list.error} onRetry={list.retry} />}
      {list.state === 'ok' && list.data?.length === 0 && <p className="quiet small">Belum ada dokumen atau situs yang diunggah.</p>}
      {list.state === 'ok' &&
        list.data?.map((s) => (
          <div key={s.id} className="set-doc">
            <div className="set-doc-head">
              <b>{s.title}</b>
              <span className="pill">{s.kind === 'website' ? 'Situs' : (s.filename?.split('.').pop() ?? 'Berkas').toUpperCase()}</span>
              <span className="pill">{s.scope === 'all' ? 'CS + Marketing' : s.scope === 'cs' ? 'CS' : 'Marketing'}</span>
            </div>
            <p className="quiet small">
              {s.url ? s.url : s.filename} · {new Date(s.created_at).toLocaleDateString('id-ID')}
            </p>
            <button type="button" className="btn outline" disabled={busy} onClick={() => void remove(s.id)}>
              Hapus
            </button>
          </div>
        ))}

      <h2 style={{ marginTop: 28 }}>Uji pencarian</h2>
      <p className="quiet small">Lihat potongan dokumen yang akan dipakai untuk sebuah pertanyaan.</p>
      <form
        className="set-inline"
        onSubmit={(e) => {
          e.preventDefault()
          void search()
        }}
      >
        <input
          value={query}
          maxLength={300}
          placeholder="Contoh: berapa lama batas retur?"
          aria-label="Pertanyaan uji"
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" className="btn outline" disabled={searching || !query.trim()}>
          {searching ? 'Mencari...' : 'Cari'}
        </button>
      </form>
      {matches && matches.length === 0 && <p className="quiet small">Tidak ada dokumen unggahan yang cocok.</p>}
      {matches?.map((m, i) => (
        <div key={`${m.title}-${i}`} className="set-doc">
          <div className="set-doc-head">
            <b>{m.title}</b>
            <span className="pill">{m.score} kata cocok</span>
          </div>
          <p className="quiet small">{m.text.slice(0, 320)}{m.text.length > 320 ? '…' : ''}</p>
        </div>
      ))}
    </>
  )
}

// ---------- Paket dan pemakaian ----------
function Plan() {
  const { me, loadState } = useData()
  if (!me) return <div className="set-sec">{loadState === 'loading' ? <Loading text="Memuat paket..." /> : <p className="quiet">Data paket belum terbaca.</p>}</div>
  const { limits: l, usage: u } = me
  const pct = l.monthly_tokens ? Math.min(100, Math.round((u.tokens_month / l.monthly_tokens) * 100)) : 0
  return (
    <div className="set-sec">
      <h2>Paket dan pemakaian</h2>
      <dl className="kv">
        <dt>Paket aktif</dt>
        <dd>{me.plan.name}</dd>
        <dt>Token bulan ini</dt>
        <dd>
          <span className="num">{nf.format(u.tokens_month)}</span>
          {l.monthly_tokens === null ? ' (tanpa batas)' : <> dari <span className="num">{nf.format(l.monthly_tokens)}</span> ({pct}%)</>}
          {l.monthly_tokens !== null && (
            <span className="set-meter" role="img" aria-label={`${pct} persen dari batas token bulan ini`}>
              <span style={{ width: `${pct}%` }} />
            </span>
          )}
        </dd>
        <dt>Agen</dt>
        <dd>
          <span className="num">{u.bots}</span> dari <span className="num">{l.max_bots}</span>
        </dd>
        <dt>Grup</dt>
        <dd>
          <span className="num">{u.groups}</span> dari <span className="num">{l.max_groups}</span>
        </dd>
        <dt>Tugas bersamaan</dt>
        <dd>
          <span className="num">{u.active_runs}</span> dari <span className="num">{l.max_concurrent_runs}</span>
        </dd>
      </dl>
    </div>
  )
}

// ---------- Data ----------
function DataSection() {
  const { flash } = useData()
  const fn = useCallback(() => api.knowledge(), [])
  const k = useLoad(fn)
  const connections = useLoad(useCallback(() => api.dataConnections(), []))
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
  const stock = connections.data?.connections.find((c) => c.kind === 'stock')
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

      <h2 style={{ marginTop: 28 }}>Spreadsheet Google Drive</h2>
      <p className="quiet small">
        Stok dan pesanan dibaca langsung dari spreadsheet. Tautan disimpan di server; isi spreadsheet tidak disalin.
      </p>
      {connections.state === 'loading' && <Loading text="Memeriksa koneksi..." shape="lines" />}
      {connections.state === 'error' && <ErrorLine text={connections.error} onRetry={connections.retry} />}
      {connections.state === 'ok' && connections.data && !connections.data.write_ready && (
        <p className="quiet small">
          Menulis pesanan butuh alamat aplikasi web spreadsheet (Apps Script) atau kredensial service account di server.
          Membaca spreadsheet yang dibagikan publik tetap bisa.
        </p>
      )}
      {connections.state === 'ok' && (
        <>
          <SheetConnect
            kind="stock"
            title="Spreadsheet stok"
            hint="Kolom yang dikenali: kode/SKU, nama, ukuran, warna, stok, harga."
            current={stock}
            onChanged={connections.retry}
          />
          <SheetConnect
            kind="orders"
            title="Spreadsheet pesanan"
            hint="Pesanan baru ditambahkan sebagai satu baris di sheet ini."
            current={connections.data?.connections.find((c) => c.kind === 'orders')}
            allowWebhook
            onChanged={connections.retry}
          />
          {stock?.status === 'verified' && <StockPeek />}
        </>
      )}
    </div>
  )
}

function SheetConnect({
  kind,
  title,
  hint,
  current,
  allowWebhook = false,
  onChanged,
}: {
  kind: 'stock' | 'orders'
  title: string
  hint: string
  current?: { url: string; status: string; detail: string | null; header: string[] | null; webhook_url?: string | null }
  allowWebhook?: boolean
  onChanged: () => void
}) {
  const { flash } = useData()
  const [url, setUrl] = useState('')
  const [webhook, setWebhook] = useState('')
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  useEffect(() => setUrl(current?.url ?? ''), [current?.url])
  useEffect(() => setWebhook(current?.webhook_url ?? ''), [current?.webhook_url])

  async function save() {
    setBusy(true)
    setProblem('')
    try {
      const saved = await api.saveDataConnection(kind, url.trim(), '', allowWebhook ? webhook.trim() : '')
      flash(saved.status === 'verified' ? 'Spreadsheet terhubung' : 'Tautan disimpan, tetapi belum bisa dibaca')
      onChanged()
    } catch (e) {
      setProblem(errText(e))
    }
    setBusy(false)
  }

  async function verify() {
    setBusy(true)
    setProblem('')
    try {
      const checked = await api.verifyDataConnection(kind)
      flash(checked.status === 'verified' ? 'Spreadsheet bisa dibaca' : 'Spreadsheet belum bisa dibaca')
      onChanged()
    } catch (e) {
      setProblem(errText(e))
    }
    setBusy(false)
  }

  const badge = current?.status === 'verified' ? 'Terhubung' : current?.status === 'error' ? 'Gagal' : 'Belum diperiksa'
  return (
    <div className="set-doc">
      <div className="set-doc-head">
        <b>{title}</b>
        {current && <span className="pill">{badge}</span>}
      </div>
      <p className="quiet small">{current?.detail || hint}</p>
      {current?.header && <p className="quiet small">Kolom: {current.header.slice(0, 8).join(', ')}{current.header.length > 8 ? '…' : ''}</p>}
      <form
        className="set-inline"
        onSubmit={(e) => {
          e.preventDefault()
          void save()
        }}
      >
        <input
          value={url}
          maxLength={2000}
          placeholder="https://docs.google.com/spreadsheets/d/…"
          aria-label={`Tautan ${title}`}
          onChange={(e) => setUrl(e.target.value)}
        />
        {allowWebhook && (
          <input
            value={webhook}
            maxLength={2000}
            placeholder="Alamat aplikasi web (…/exec) untuk menulis pesanan"
            aria-label={`Alamat aplikasi web ${title}`}
            onChange={(e) => setWebhook(e.target.value)}
          />
        )}
        <button type="submit" className="btn primary" disabled={busy || !url.trim()}>
          {busy ? 'Memeriksa...' : 'Simpan'}
        </button>
        {current && (
          <button type="button" className="btn outline" disabled={busy} onClick={() => void verify()}>
            Periksa
          </button>
        )}
      </form>
      {allowWebhook && (
        <p className="quiet small">
          {current?.webhook_url ? 'Menulis pesanan: aktif (aplikasi web).' : 'Menulis pesanan: belum aktif.'}
        </p>
      )}
      {problem && (
        <p className="problem-bar" role="alert">
          {problem}
        </p>
      )}
    </div>
  )
}

function StockPeek() {
  const [query, setQuery] = useState('')
  const [items, setItems] = useState<{ sku?: string; name?: string; stock?: string; price?: string }[] | null>(null)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  async function find() {
    if (!query.trim()) return
    setBusy(true)
    setProblem('')
    try {
      setItems((await api.stockLookup(query.trim())).items)
    } catch (e) {
      setProblem(errText(e))
    }
    setBusy(false)
  }
  return (
    <>
      <h2 style={{ marginTop: 28 }}>Cek stok</h2>
      <p className="quiet small">Membaca langsung dari spreadsheet stok yang terhubung.</p>
      <form
        className="set-inline"
        onSubmit={(e) => {
          e.preventDefault()
          void find()
        }}
      >
        <input
          value={query}
          maxLength={120}
          placeholder="SKU atau nama produk"
          aria-label="Cari stok"
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" className="btn outline" disabled={busy || !query.trim()}>
          {busy ? 'Mencari...' : 'Cari'}
        </button>
      </form>
      {problem && (
        <p className="problem-bar" role="alert">
          {problem}
        </p>
      )}
      {items && items.length === 0 && <p className="quiet small">Tidak ada baris yang cocok.</p>}
      {items?.map((item, i) => (
        <div key={i} className="set-doc">
          <div className="set-doc-head">
            <b>{item.name ?? item.sku ?? 'Baris'}</b>
            <span className="pill">{item.stock ? `stok ${item.stock}` : 'stok tidak terbaca'}</span>
          </div>
          <p className="quiet small">
            {item.sku ? `SKU ${item.sku}` : ''}
            {item.price ? ` · Rp ${item.price}` : ''}
          </p>
        </div>
      ))}
    </>
  )
}
