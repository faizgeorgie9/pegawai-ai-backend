import { useCallback, useState } from 'react'
import type { ReactNode } from 'react'
import { api, errText } from './bff'
import type { Money, MonthUsage } from './bff'
import { setAdminMode, useAdminMode } from './adminMode'
import { useData } from './data'
import { markNamed } from './Onboarding'
import { toolsetText } from './ui-extra'
import { ErrorLine, nf } from './ui'
import { CostMeter, Loading, PageHead, Perkiraan, useLoad } from './ui-extra'

// #/pengaturan/<bagian>. Left: the sections (a scrolling row on small screens). Right: the section, one sentence per option.
const SECTIONS = [
  { id: 'umum', label: 'Umum' },
  { id: 'notifikasi', label: 'Notifikasi' },
  { id: 'keamanan', label: 'Keamanan' },
  { id: 'knowledge', label: 'Pengetahuan' },
  { id: 'paket', label: 'Paket dan biaya' },
  { id: 'data', label: 'Data' },
] as const

const ZONES: [string, string][] = [['Asia/Jakarta', 'WIB (Asia/Jakarta)'], ['Asia/Makassar', 'WITA (Asia/Makassar)'], ['Asia/Jayapura', 'WIT (Asia/Jayapura)']]

export default function Settings({ section }: { section?: string }) {
  const cur = SECTIONS.find((s) => s.id === section)?.id ?? 'umum'
  return (
    <section className="page">
      <PageHead title="Pengaturan" sub="Atur ruang kerja Anda." />
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
          {cur === 'knowledge' && <KnowledgeLink />}
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
  const admin = useAdminMode()
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
      <Row title="Nama bisnis" hint="Tampil di menu samping.">
        <form
          className="set-inline"
          onSubmit={(e) => {
            e.preventDefault()
            if (dirty) {
              markNamed()
              void save({ company_name: name.trim() })
            }
          }}
        >
          <input value={name} maxLength={40} aria-label="Nama bisnis" onChange={(e) => setName(e.target.value)} />
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
      <Row title="Zona waktu" hint="Dipakai untuk jadwal.">
        <select value={settings.timezone} aria-label="Zona waktu" onChange={(e) => void save({ timezone: e.target.value })}>
          {ZONES.map(([v, l]) => (
            <option key={v} value={v}>
              {l}
            </option>
          ))}
        </select>
      </Row>
      <Row title="Tema" hint="Terang atau gelap.">
        <div className="seg" role="group" aria-label="Tema">
          <button type="button" aria-pressed={!dark} onClick={() => setTheme(false)}>
            Terang
          </button>
          <button type="button" aria-pressed={dark} onClick={() => setTheme(true)}>
            Gelap
          </button>
        </div>
      </Row>
      <Row title="Mode admin" hint="Tampilkan halaman dan rincian teknis untuk admin.">
        <label className="set-check">
          <input type="checkbox" checked={admin} onChange={(e) => setAdminMode(e.target.checked)} />
          <span>{admin ? 'Nyala' : 'Mati'}</span>
        </label>
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
    ['input', 'Butuh izin atau jawaban', 'Kabar saat agen menunggu Anda.'],
    ['failed', 'Tugas gagal', 'Kabar saat tugas berhenti.'],
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
      <p className="quiet">Pembatasan ini dipasang tim AITopTrends di tiap agen.</p>
      {s.state === 'loading' && <Loading text="Memuat pembatasan..." shape="table" />}
      {s.state === 'error' && <ErrorLine text={s.error} onRetry={s.retry} />}
      {s.state === 'ok' && s.data && (
        <div className="table-wrap">
          <table className="plain">
            <thead>
              <tr>
                <th>Agen</th>
                <th>Kemampuan yang dimatikan</th>
                <th>Persetujuan</th>
              </tr>
            </thead>
            <tbody>
              {s.data.bots.map((b) => (
                <tr key={b.bot_id}>
                  <td data-label="Agen">{b.name}</td>
                  <td data-label="Kemampuan yang dimatikan">
                    {!b.ok ? (
                      <span className="quiet">Belum terbaca</span>
                    ) : b.blocked.length === 0 ? (
                      <span className="pill warn">Tidak ada</span>
                    ) : (
                      <div className="chip-row">
                        {b.blocked.map((t) => (
                          <span key={t} className="pill">
                            {toolsetText(t, t, '')[0]}
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

// ---------- Pengetahuan: moved to its own page ----------
function KnowledgeLink() {
  return (
    <div className="set-sec">
      <h2>Pengetahuan</h2>
      <p className="quiet">Berkas dan link untuk agen kini ada di halaman sendiri.</p>
      <p>
        <a className="btn primary" href="#/pengetahuan">
          Buka Pengetahuan
        </a>
      </p>
    </div>
  )
}

// ---------- Paket dan pemakaian ----------
const dayText = (d: string) => new Date(`${d}T00:00:00`).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })

function Split({ title, rows, tokens }: { title: string; tokens: boolean; rows: { key: string; name: ReactNode; cost: Money; tokens: number; est: boolean }[] }) {
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
            {tokens && <small className="quiet num">{nf.format(r.tokens)} token</small>}
          </li>
        ))}
      </ul>
    </div>
  )
}

function UsageDetail({ u, admin }: { u: MonthUsage; admin: boolean }) {
  if (u.tokens.runs === 0) return <p className="quiet">Belum ada pemakaian bulan ini. Biaya muncul di sini setelah agen mengerjakan tugas.</p>
  const days = Math.max(...u.by_day.map((d) => Number(d.cost.usd)), 0)
  return (
    <>
      <div className="usage-split">
        <Split title="Per agen" tokens={admin} rows={u.by_agent.map((a) => ({ key: a.bot_id, name: a.name, cost: a.cost, tokens: a.tokens, est: a.estimated }))} />
        {admin && <Split
          title="Per model"
          tokens
          rows={u.by_model.map((m) => ({ key: `${m.provider}/${m.model}`, name: m.priced ? m.model : `${m.model} (belum ada harga)`, cost: m.cost, tokens: m.tokens, est: m.estimated }))}
        />}
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
      {admin && u.unpriced_tokens > 0 && <p className="note-box">{nf.format(u.unpriced_tokens)} token belum dihitung karena modelnya belum punya harga.</p>}
    </>
  )
}

function Plan() {
  const admin = useAdminMode()
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
        {admin && (
          <>
            <dt>Pemakaian bulan ini (token)</dt>
            <dd>
              <span className="num">{nf.format(u.tokens_month)}</span>
            </dd>
          </>
        )}
        <dt>Agen</dt>
        <dd>
          <span className="num">{u.bots}</span> dari <span className="num">{me.limits.max_bots}</span>
        </dd>
        <dt>Tim</dt>
        <dd>
          <span className="num">{u.groups}</span> dari <span className="num">{me.limits.max_groups}</span>
        </dd>
        <dt>Tugas sekaligus</dt>
        <dd>
          <span className="num">{u.active_runs}</span> dari <span className="num">{me.limits.max_concurrent_runs}</span>
        </dd>
      </dl>
      <h2>Rincian biaya</h2>
      {d && !admin && <p className="quiet small">Dihitung dari pemakaian agen bulan ini.</p>}
      {d && admin && (
        <p className="quiet small">
          {new Date(d.period.start).toLocaleDateString('id-ID', { month: 'long', year: 'numeric', timeZone: d.period.timezone })} ({d.period.timezone}), diperbarui{' '}
          {new Date(d.updated_at).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', timeZone: d.period.timezone })}. Dihitung dari token yang benar-benar terpakai (teks masuk, teks keluar, dan teks yang diingat ulang) dikali harga model per 1 juta token. Token adalah potongan kecil teks yang dibaca dan ditulis model. {d.basis === 'estimated' ? 'Angka berlabel "perkiraan" memakai harga yang belum diverifikasi.' : 'Semua harga sudah diverifikasi dari halaman resmi penyedia.'}
        </p>
      )}
      {m.state === 'loading' && !d && <Loading text="Memuat rincian..." />}
      {m.state === 'error' && !d && <ErrorLine text={m.error} onRetry={m.retry} />}
      {d && <UsageDetail u={d} admin={admin} />}
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
      <Row title="Lama simpan log aktivitas" hint="Catatan aktivitas dihapus otomatis setelah masa ini.">
        <span className="num">{k.data ? `${k.data.retention_days} hari` : '90 hari'}</span>
      </Row>
      <Row title="Ekspor riwayat chat" hint="Semua chat dan tim dalam satu berkas.">
        <button className="btn outline" disabled={busy} onClick={() => void exportAll()}>
          {busy ? 'Menyiapkan...' : 'Unduh'}
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
