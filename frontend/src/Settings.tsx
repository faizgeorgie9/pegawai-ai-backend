import { useCallback, useState } from 'react'
import { api, errText } from './bff'
import { useData } from './data'
import { ErrorLine, nf } from './ui'
import { EffortSelect, Loading, ModelSelect, PageHead, modelKey, splitModel, useLoad } from './ui-extra'

// #/pengaturan/<bagian>. Left: the sections (a scrolling row on small screens). Right: the section, one sentence per option.
const SECTIONS = [
  { id: 'umum', label: 'Umum' },
  { id: 'model', label: 'Model AI' },
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
          <a href="#/tools" className="set-out">
            Kemampuan
          </a>
        </nav>
        <div className="set-body">
          {cur === 'umum' && <General />}
          {cur === 'model' && <ModelAI />}
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

// ---------- Model AI ----------
function ModelAI() {
  const { settings } = useData()
  const { save, problem } = useSave()
  return (
    <div className="set-sec">
      <h2>Model AI</h2>
      <p className="quiet">Berlaku untuk agen yang tidak punya pilihan sendiri. Pilihan per agen ada di halaman ubah agen.</p>
      <Row title="Model bawaan" hint="Dipakai di tugas berikutnya.">
        <ModelSelect label="Model" value={modelKey(settings.provider, settings.model)} onChange={(v) => void save(splitModel(v))} />
      </Row>
      <Row title="Tingkat berpikir bawaan" hint="Makin tinggi, makin teliti tetapi makin lambat dan boros token.">
        <EffortSelect value={settings.reasoning_effort ?? ''} onChange={(v) => void save({ reasoning_effort: v || null })} />
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

// ---------- Knowledge base (hanya baca) ----------
function Knowledge() {
  const fn = useCallback(() => api.knowledge(), [])
  const k = useLoad(fn)
  return (
    <div className="set-sec">
      <h2>Knowledge base</h2>
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
