import { useCallback } from 'react'
import { api } from './bff'
import { ErrorLine } from './ui'
import { BlockedBanner, CapChip, Empty, Loading, OFF_WHY, PageHead, SampleBadge, useLoad } from './ui-extra'
import { go } from './router'
import type { Route } from './router'

const clean = (s: string) => s.replace(/^[^\p{L}\p{N}]+/u, '').trim()

// ---------- Tools / Plugins ----------
export function Tools() {
  const fn = useCallback(() => api.tools(), [])
  const t = useLoad(fn)

  type Row = { name: string; label: string; description: string; users: string[]; seen: number }
  const rows = new Map<string, Row>()
  const deny = new Set(t.data?.deny ?? [])
  const answered = t.data?.bots.filter((b) => b.ok) ?? []
  const failed = t.data?.bots.filter((b) => !b.ok) ?? []
  for (const b of answered)
    for (const ts of b.toolsets) {
      const r = rows.get(ts.name) ?? { name: ts.name, label: clean(ts.label), description: ts.description, users: [], seen: 0 }
      r.seen++
      if (ts.enabled) r.users.push(b.name)
      rows.set(ts.name, r)
    }
  const order = (r: Row) => (r.users.length ? 0 : deny.has(r.name) ? 2 : 1)
  const list = [...rows.values()].sort((a, b) => order(a) - order(b) || a.name.localeCompare(b.name))

  return (
    <div className="tab-body">
      <p className="note-box">Pengaturan per agen: perlu disepakati dengan backend. Halaman ini hanya untuk melihat.</p>
      {t.state === 'loading' && <Loading text="Memuat toolset dari Hermes..." />}
      {t.state === 'error' && <ErrorLine text={t.error} onRetry={t.retry} />}
      {t.state === 'ok' && failed.length > 0 && (
        <div className="state error" role="alert">
          <p>Hermes tidak menjawab untuk: {failed.map((b) => b.name).join(', ')}. Status toolset agen itu tidak diketahui.</p>
          <button className="btn link" onClick={t.retry}>
            Coba lagi
          </button>
        </div>
      )}
      {t.state === 'ok' && list.length === 0 && failed.length === 0 && <Empty title="Belum ada toolset">Belum ada agen yang bisa ditanya.</Empty>}
      {t.state === 'ok' && list.length === 0 && failed.length > 0 && (
        <p>
          <CapChip cap="unknown" /> Tidak ada data toolset yang bisa ditampilkan.
        </p>
      )}
      <div className="table-wrap">
        <table className="plain">
          <thead><tr><th>Kemampuan platform</th><th>Isi</th><th>Status</th></tr></thead>
          <tbody>
            <tr>
              <td data-label="Kemampuan platform" className="rich"><b>Pencarian katalog dan knowledge (BFF)</b></td>
              <td data-label="Isi"><div className="clamp2">BFF mencari 1.206 produk katalog dan knowledge Colorbox sebelum agen menjawab, lalu mencatat sumbernya per run.</div></td>
              <td className="st-col" data-label="Status"><CapChip cap="ok" label="Berfungsi" /></td>
            </tr>
          </tbody>
        </table>
      </div>
      {list.length > 0 && (
        <div className="table-wrap">
          <table className="plain">
            <thead>
              <tr>
                <th>Toolset</th>
                <th>Isi</th>
                <th>Status</th>
                <th>Dipakai agen</th>
              </tr>
            </thead>
            <tbody>
              {list.map((r) => (
                <tr key={r.name}>
                  <td data-label="Toolset" className="rich">
                    <b>{r.label}</b>
                    <div className="quiet small">{r.name}</div>
                  </td>
                  <td data-label="Isi"><div className="clamp2" title={r.description}>{r.description || '–'}</div></td>
                  <td className="st-col rich" data-label="Status">
                    {r.users.length ? (
                      <CapChip cap="ok" label="Aktif" />
                    ) : deny.has(r.name) ? (
                      <>
                        <CapChip cap="blocked" />
                        <div className="quiet small">{OFF_WHY}</div>
                      </>
                    ) : (
                      <CapChip cap="none" label="Tidak dipakai" />
                    )}
                  </td>
                  <td data-label="Dipakai agen">{!r.users.length ? '–' : r.users.length === answered.length && answered.length > 1 ? `Semua agen (${answered.length})` : r.users.join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ---------- Computer Use ----------
export function ComputerUse() {
  return (
    <div className="tab-body">
      <BlockedBanner title="Computer Use belum dibuka" reason="Sampai dibuka, tidak ada tugas Computer Use yang bisa dijalankan." />
      <div className="cbox">
        <h2>Yang akan tampil di sini</h2>
        <ul className="plain">
          <li>Tugas: apa yang diminta dan oleh siapa.</li>
          <li>Status: menunggu, berjalan, selesai, atau dihentikan.</li>
          <li>Aktivitas: langkah yang dilakukan agen.</li>
        </ul>
      </div>
      <div className="block">
        <header>
          <h2>Daftar tugas</h2>
        </header>
        <Empty title="Belum ada tugas">Tidak ada tugas Computer Use selama fitur ini nonaktif.</Empty>
      </div>
      <div className="sample-box">
        <header>
          <SampleBadge />
          <b>Contoh tampilan</b>
        </header>
        <p>Dua baris contoh agar bentuk halaman terlihat. Bukan tugas nyata.</p>
        <div className="table-wrap">
          <table className="plain">
            <thead>
              <tr>
                <th>Tugas</th>
                <th>Status</th>
                <th>Aktivitas terakhir</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td data-label="Tugas">Buka halaman produk dan catat harganya</td>
                <td data-label="Status">Selesai</td>
                <td data-label="Aktivitas terakhir">Mencatat 3 harga</td>
              </tr>
              <tr>
                <td data-label="Tugas">Bandingkan dua daftar harga</td>
                <td data-label="Status">Berjalan</td>
                <td data-label="Aktivitas terakhir">Membuka daftar kedua</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ---------- Scheduler ----------
export function Scheduler() {
  return (
    <div className="tab-body">
      <BlockedBanner title="Scheduler belum dibuka" reason="Sampai dibuka, tidak ada job terjadwal yang bisa dijalankan." />
      <div className="cbox">
        <h2>Yang akan tampil di sini</h2>
        <ul className="plain">
          <li>Daftar job: nama, jadwal, dan agen yang menjalankan.</li>
          <li>Status tiap job: aktif, dijeda, atau gagal.</li>
        </ul>
      </div>
      <div className="block">
        <header>
          <h2>Daftar job</h2>
        </header>
        <Empty title="Belum ada job">Tidak ada job terjadwal selama fitur ini nonaktif.</Empty>
      </div>
      <div className="sample-box">
        <header>
          <SampleBadge />
          <b>Contoh tampilan</b>
        </header>
        <p>Dua baris contoh agar bentuk halaman terlihat. Bukan job nyata.</p>
        <div className="table-wrap">
          <table className="plain">
            <thead>
              <tr>
                <th>Job</th>
                <th>Jadwal</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td data-label="Job">Rangkuman harian tim</td>
                <td data-label="Jadwal">Setiap hari, 08.00</td>
                <td data-label="Status">Aktif</td>
              </tr>
              <tr>
                <td data-label="Job">Cek draf mingguan</td>
                <td data-label="Jadwal">Setiap Senin, 09.00</td>
                <td data-label="Status">Dijeda</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ---------- Kemampuan: one page, three tabs ----------
const TABS = [
  { name: 'tools', label: 'Tools', path: '/tools' },
  { name: 'computer-use', label: 'Computer Use', path: '/computer-use' },
  { name: 'scheduler', label: 'Scheduler', path: '/scheduler' },
] as const

export function Kemampuan({ tab }: { tab: Extract<Route['name'], 'tools' | 'computer-use' | 'scheduler'> }) {
  const i = TABS.findIndex((t) => t.name === tab)
  function onKey(e: React.KeyboardEvent) {
    const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0
    if (!d) return
    e.preventDefault()
    const n = TABS[(i + d + TABS.length) % TABS.length]
    go(n.path, true)
    document.getElementById('tab-' + n.name)?.focus()
  }
  return (
    <section className="page">
      <PageHead title="Kemampuan" sub="Apa yang bisa dan belum bisa dipakai agen." />
      <div className="tabs" role="tablist" aria-label="Kemampuan" onKeyDown={onKey}>
        {TABS.map((t) => (
          <a key={t.name} id={'tab-' + t.name} role="tab" href={'#' + t.path} aria-selected={t.name === tab} aria-controls="tabpanel" tabIndex={t.name === tab ? 0 : -1}>
            {t.label}
            {t.name !== 'tools' && <span className="tab-tag">Nonaktif</span>}
          </a>
        ))}
      </div>
      <div id="tabpanel" role="tabpanel" aria-labelledby={'tab-' + tab}>
        {tab === 'tools' && <Tools />}
        {tab === 'computer-use' && <ComputerUse />}
        {tab === 'scheduler' && <Scheduler />}
      </div>
    </section>
  )
}
