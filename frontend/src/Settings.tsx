import { useCallback, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { api, errText } from './bff'
import type { Money, MonthUsage, Security as SecurityData } from './bff'
import { setAdminMode, useAdminMode, useIsAdmin } from './adminMode'
import { useData } from './data'
import { markNamed } from './Onboarding'
import { toolsetText } from './ui-extra'
import { ErrorLine, nf } from './ui'
import { CostMeter, Loading, PageHead, Perkiraan, useLoad } from './ui-extra'
import { cachedRead, onLinkIntent } from './session-cache'
import { Switch } from './ws-common'
import { AiAccounts } from './ai-accounts'

// #/pengaturan/<bagian>. Left: the sections (a scrolling row on small screens). Right: the section, one sentence per option.
const SECTIONS = [
  { id: 'umum', label: 'Umum' },
  { id: 'notifikasi', label: 'Notifikasi' },
  { id: 'akun-ai', label: 'Akun AI' },
  { id: 'keamanan', label: 'Keamanan' },
  { id: 'paket', label: 'Paket dan biaya' },
  { id: 'data', label: 'Data' },
] as const

const ZONES: [string, string][] = [['Asia/Jakarta', 'WIB (Asia/Jakarta)'], ['Asia/Makassar', 'WITA (Asia/Makassar)'], ['Asia/Jayapura', 'WIT (Asia/Jayapura)']]

export default function Settings({ section }: { section?: string }) {
  const cur = SECTIONS.find((s) => s.id === section)?.id ?? 'umum'
  const nav = useRef<HTMLElement>(null)
  // On a phone the tab row scrolls sideways; keep the open section's tab out from under the edge fade.
  useEffect(() => {
    const box = nav.current
    const a = box?.querySelector<HTMLElement>('[aria-current="page"]')
    if (!box || !a || box.scrollWidth <= box.clientWidth) return
    const r = a.getBoundingClientRect(), b = box.getBoundingClientRect()
    box.scrollLeft += r.left - b.left - (b.width - r.width) / 2
  }, [cur])
  return (
    <section className="page set-page">
      <PageHead title="Pengaturan" sub="Atur ruang kerja Anda." />
      <div className="set-layout">
        <nav ref={nav} className="set-nav" aria-label="Bagian pengaturan">
          {SECTIONS.map((s) => (
            <a key={s.id} href={`#/pengaturan/${s.id}`} aria-current={s.id === cur ? 'page' : undefined} aria-label={s.label}>
              {s.id === 'paket' ? (
                <>
                  Paket<span className="hide-sm"> dan biaya</span>
                </>
              ) : (
                s.label
              )}
            </a>
          ))}
        </nav>
        <div className="set-body">
          {cur === 'umum' && <General />}
          {cur === 'notifikasi' && <Notifications />}
          {cur === 'akun-ai' && <AiAccounts />}
          {cur === 'keamanan' && <Security />}
          {cur === 'paket' && <Plan />}
          {cur === 'data' && <DataSection />}
        </div>
      </div>
    </section>
  )
}

function Row({ title, hint, children, stack }: { title: string; hint: string; children: React.ReactNode; stack?: boolean }) {
  return (
    <div className={'set-row' + (stack ? ' set-row-stack' : '')}>
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
  const isAdmin = useIsAdmin()
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
      <h2 className="set-h">Umum</h2>
      <Row title="Nama bisnis" hint="Tampil di menu samping." stack>
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
      {isAdmin && (
        <Row title="Tampilan admin" hint="Tampilkan menu Admin dan rincian teknis. Matikan untuk melihat tampilan yang sama dengan staf.">
          <Switch checked={admin} label={admin ? 'Nyala' : 'Mati'} onChange={setAdminMode} />
        </Row>
      )}
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
    ['done', 'Tugas selesai', 'Kabar saat pegawai selesai bekerja.'],
    ['input', 'Butuh izin atau jawaban', 'Kabar saat pegawai menunggu Anda.'],
    ['failed', 'Tugas gagal', 'Kabar saat tugas berhenti.'],
  ]
  const browserHint =
    perm === 'granted'
      ? ''
      : perm === 'denied'
        ? 'Diblokir di peramban. Ubah izin situs di peramban Anda.'
        : perm === 'unsupported'
          ? 'Peramban ini tidak mendukung notifikasi.'
          : 'Belum aktif. Klik Izinkan, lalu pilih Izinkan di jendela peramban.'
  return (
    <div className="set-sec">
      <h2 className="set-h">Notifikasi</h2>
      <Row title="Notifikasi di peramban" hint={browserHint}>
        {perm === 'default' && (
          <button className="btn outline" onClick={() => void Notification.requestPermission().then(setPerm)}>
            Izinkan
          </button>
        )}
        {perm === 'granted' && <span className="pill ok">Aktif</span>}
      </Row>
      {items.map(([k, t, h]) => (
        <Row key={k} title={t} hint={h}>
          <Switch checked={settings.notify[k]} label={settings.notify[k] ? 'Nyala' : 'Mati'} onChange={(v) => void save({ notify: { ...settings.notify, [k]: v } })} />
        </Row>
      ))}
      {problem}
    </div>
  )
}

// ---------- Keamanan dan izin (hanya baca) ----------
type SecBot = SecurityData['bots'][number]

function BlockedChips({ bot }: { bot: SecBot }) {
  if (!bot.ok) return <span className="quiet">Belum terbaca</span>
  if (bot.blocked.length === 0) return <span className="pill warn">Tidak ada</span>
  return (
    <div className="chip-row">
      {bot.blocked.map((t) => (
        <span key={t} className="pill">
          {toolsetText(t, t, '')[0]}
        </span>
      ))}
    </div>
  )
}

// The real table head plus one placeholder row: the common "same policy for everyone" result has this
// exact shape, so only the row's text changes when the answer arrives.
function SecuritySkeleton() {
  const chips = [148, 128, 114, 106, 172, 144, 132]
  return (
    <div className="table-wrap skel skel-sec" role="status" aria-busy="true">
      <span className="sr">Memuat pengaturan keamanan…</span>
      <table className="plain" aria-hidden="true">
        <thead>
          <tr>
            <th>Pegawai</th>
            <th>Dimatikan</th>
            <th>Persetujuan</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td data-label="Pegawai">
              <div className="skel-body">
                <span className="slow-note skel-sec-note">Memuat…</span>
                <i className="skel-bar w60" />
              </div>
            </td>
            <td data-label="Dimatikan">
              <div className="skel-body">
                <span className="skel-chips">
                  {chips.map((w, i) => (
                    <i key={i} className="skel-chip" style={{ width: w }} />
                  ))}
                </span>
              </div>
            </td>
            <td data-label="Persetujuan">
              <div className="skel-body">
                <i className="skel-bar w70" />
                <i className="skel-bar w40 thin" />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

function Security() {
  const fn = useCallback(() => cachedRead('security', () => api.security()), [])
  const s = useLoad(fn)
  const bots = s.data?.bots ?? []
  // One shared policy reads as one row; per-employee rows only when a rule actually differs.
  const first = bots[0]
  const same =
    bots.length > 0 &&
    bots.every(
      (b) =>
        (b.ok ? b.blocked.slice().sort().join('|') : '!') === (first.ok ? first.blocked.slice().sort().join('|') : '!') &&
        b.approvals === first.approvals,
    )
  const rows = same ? [{ key: 'all', name: 'Semua pegawai', bot: first }] : bots.map((b) => ({ key: b.bot_id, name: b.name, bot: b }))
  return (
    <div className="set-sec">
      <h2 className="set-h">Keamanan dan izin</h2>
      <p className="quiet">Demi keamanan, kemampuan di bawah ini dimatikan untuk semua pegawai, dan tindakan berisiko seperti menghapus berkas atau mengirim email selalu menunggu izin Anda.</p>
      {s.state === 'loading' && !s.data && <SecuritySkeleton />}
      {s.state === 'error' && <ErrorLine text={s.error} onRetry={s.retry} />}
      {s.state === 'ok' && s.data && (
        <div className="table-wrap">
          <table className="plain">
            <thead>
              <tr>
                <th>Pegawai</th>
                <th>Dimatikan</th>
                <th>Persetujuan</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.key}>
                  <td data-label="Pegawai">{r.name}</td>
                  <td data-label="Dimatikan">
                    <BlockedChips bot={r.bot} />
                  </td>
                  <td data-label="Persetujuan">{r.bot.approvals === 'manual' ? 'Selalu menunggu izin Anda' : r.bot.approvals ?? 'Tidak diketahui'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// Starts the per-employee toolset read while the pointer or focus is still on "Keamanan" in the section nav.
onLinkIntent('a[href="#/pengaturan/keamanan"]', () => {
  void cachedRead('security', () => api.security()).catch(() => {})
})

// ---------- Paket dan pemakaian ----------
const dayText = (d: string) => new Date(`${d}T00:00:00`).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })

function Split({ title, rows, tokens }: { title: string; tokens: boolean; rows: { key: string; name: ReactNode; cost: Money; tokens: number; unpriced: boolean }[] }) {
  const top = Math.max(...rows.map((r) => Number(r.cost.usd)), 0)
  const [all, setAll] = useState(false)
  return (
    <div>
      <h3>{title}</h3>
      <ul className="usage-list" data-clamp={!all && rows.length > 5 ? true : undefined}>
        {rows.map((r) => (
          <li key={r.key}>
            <span className="row-top">
              <span>
                {r.name} {r.unpriced && <Perkiraan />}
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
      {rows.length > 5 && (
        <button type="button" className="btn link small usage-more" aria-expanded={all} onClick={() => setAll((v) => !v)}>
          {all ? 'Tampilkan lebih sedikit' : `Lihat semua ${rows.length}`}
        </button>
      )}
    </div>
  )
}

function UsageDetail({ u, admin }: { u: MonthUsage; admin: boolean }) {
  const [wide] = useState(() => window.matchMedia('(min-width: 641px)').matches)
  if (u.tokens.runs === 0) return <p className="quiet">Belum ada pemakaian bulan ini. Biaya muncul di sini setelah pegawai mengerjakan tugas.</p>
  const days = Math.max(...u.by_day.map((d) => Number(d.cost.usd)), 0)
  const perDay = (
    <details className="usage-days" open={wide}>
      <summary>
        <h3>Per hari</h3>
      </summary>
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
    </details>
  )
  return (
    <>
      <div className="usage-split">
        <Split title="Per pegawai" tokens={admin} rows={u.by_agent.map((a) => ({ key: a.bot_id, name: a.name, cost: a.cost, tokens: a.tokens, unpriced: false }))} />
        {admin ? (
          <Split
            title="Per model"
            tokens
            rows={u.by_model.map((m) => ({ key: `${m.provider}/${m.model}`, name: m.priced ? m.model : `${m.model} (belum ada harga)`, cost: m.cost, tokens: m.tokens, unpriced: !m.priced }))}
          />
        ) : (
          perDay
        )}
      </div>
      {admin && perDay}
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
      <h2 className="set-h">Paket dan pemakaian</h2>
      <p className="quiet small">Biaya ditampilkan dalam dolar AS (USD), bukan rupiah.</p>
      <dl className="kv kv-wide plan-sum">
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
        <dt>Pegawai</dt>
        <dd>
          <span className="num">{u.bots}</span> dari <span className="num">{me.limits.max_bots}</span>
        </dd>
        <dt>Tim</dt>
        <dd>
          <span className="num">{u.groups}</span> dari <span className="num">{me.limits.max_groups}</span>
        </dd>
        <dt>Tugas berjalan bersamaan</dt>
        <dd>
          <span className="num">{u.active_runs}</span> dari <span className="num">{me.limits.max_concurrent_runs}</span>
        </dd>
      </dl>
      <h2>Rincian biaya</h2>
      {d && !admin && <p className="quiet small">Dihitung dari pekerjaan pegawai AI bulan ini.</p>}
      {d && admin && (
        <p className="quiet small">
          {new Date(d.period.start).toLocaleDateString('id-ID', { month: 'long', year: 'numeric', timeZone: d.period.timezone })} ({d.period.timezone}), diperbarui{' '}
          {new Date(d.updated_at).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', timeZone: d.period.timezone })}. Dihitung dari token yang benar-benar terpakai (teks masuk, teks keluar, dan teks yang diingat ulang) dikali harga model per 1 juta token. Token adalah potongan kecil teks yang dibaca dan ditulis model. {d.basis === 'estimated' ? 'Angka berlabel "perkiraan" memakai harga yang belum diverifikasi.' : 'Semua harga sudah diverifikasi dari halaman resmi penyedia.'}
        </p>
      )}
      {m.state === 'loading' && !d && <Loading text="Memuat rincian..." />}
      {m.state === 'error' && !d && <ErrorLine text={m.error} onRetry={m.retry} />}
      {d && (
        <>
          {d.tokens.runs > 0 && <p className="quiet small">Semua angka biaya di bawah ini perkiraan.</p>}
          <UsageDetail u={d} admin={admin} />
        </>
      )}
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
      <h2 className="set-h">Data</h2>
      <Row title="Lama simpan catatan aktivitas" hint="Catatan aktivitas dihapus otomatis setelah masa ini.">
        <span className="num">{k.data ? `${k.data.retention_days} hari` : '90 hari'}</span>
        <br />
        <small className="quiet small">Tidak bisa diubah</small>
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
