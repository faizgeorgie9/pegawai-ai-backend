import { useCallback } from 'react'
import { api } from './bff'
import { ErrorLine } from './ui'
import { BlockedBanner, CapChip, Empty, Loading, PageHead, SampleBadge, useLoad } from './ui-extra'

const DENY_REASON = 'dimatikan demi keamanan prototipe'
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
    <section className="page">
      <PageHead title="Tools / Plugins" sub="Toolset yang dilayani Hermes untuk setiap agen, dibaca langsung saat halaman dibuka." />
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
                  <td>
                    <b>{r.label}</b>
                    <div className="quiet small">{r.name}</div>
                  </td>
                  <td><div className="clamp2" title={r.description}>{r.description || '–'}</div></td>
                  <td className="st-col">
                    {r.users.length ? (
                      <CapChip cap="ok" label="Aktif" />
                    ) : deny.has(r.name) ? (
                      <>
                        <CapChip cap="blocked" label="Diblokir" />
                        <div className="quiet small">{DENY_REASON}</div>
                      </>
                    ) : (
                      <CapChip cap="none" label="Nonaktif" />
                    )}
                  </td>
                  <td>{!r.users.length ? '–' : r.users.length === answered.length && answered.length > 1 ? `Semua agen (${answered.length})` : r.users.join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

// ---------- Computer Use ----------
export function ComputerUse() {
  return (
    <section className="page">
      <PageHead title="Computer Use" sub="Tugas komputer untuk agen: tugas, status, dan aktivitas." />
      <BlockedBanner title="Computer Use belum dibuka" reason="Toolset computer_use dimatikan demi keamanan prototipe. Backend yang memutuskan kapan dibuka. Sampai itu, tidak ada tugas yang bisa dijalankan." />
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
        <Empty title="Belum ada tugas">Tidak ada tugas Computer Use selama fitur ini diblokir.</Empty>
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
                <td>Buka halaman produk dan catat harganya</td>
                <td>Selesai</td>
                <td>Mencatat 3 harga</td>
              </tr>
              <tr>
                <td>Bandingkan dua daftar harga</td>
                <td>Berjalan</td>
                <td>Membuka daftar kedua</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

// ---------- Scheduler ----------
export function Scheduler() {
  return (
    <section className="page">
      <PageHead title="Scheduler" sub="Job terjadwal untuk agen." />
      <BlockedBanner title="Scheduler belum dibuka" reason="Toolset cronjob dimatikan demi keamanan prototipe, supaya tidak ada job yang terus berjalan setelah dihentikan. Backend yang memutuskan kapan dibuka." />
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
        <Empty title="Belum ada job">Tidak ada job terjadwal selama fitur ini diblokir.</Empty>
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
                <td>Rangkuman harian tim</td>
                <td>Setiap hari, 08.00</td>
                <td>Aktif</td>
              </tr>
              <tr>
                <td>Cek draf mingguan</td>
                <td>Setiap Senin, 09.00</td>
                <td>Dijeda</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

// ---------- Workspace (routes only; built next) ----------
export function Building({ title }: { title: string }) {
  return (
    <section className="page">
      <PageHead title={title} />
      <Empty title="Sedang dibangun">Halaman ini belum tersedia.</Empty>
    </section>
  )
}
