import { CapChip } from './ui-extra'

// DRAFT: the connection cards only show what connecting will enable. There is no OAuth yet, so no button works and nothing is "connected".
const APPS = [
  {
    id: 'gdrive',
    name: 'Google Drive',
    enables: 'Berkas pribadi di Drive (dokumen, spreadsheet, slide) bisa dipakai sebagai sumber Knowledge Base, tanpa harus dibagikan ke publik.',
    where: 'Pengaturan > Knowledge base (sumber Google Drive), dan saat Anda menempel link Drive pribadi di chat.',
  },
  {
    id: 'gmail',
    name: 'Gmail',
    enables: 'Agen bisa membaca email yang Anda pilih dan menyiapkan draf balasan. Draf tetap Anda tinjau sendiri.',
    where: 'Daftar toolset agen di tab Tools ini, dan draf balasan di chat agen.',
  },
  {
    id: 'notion',
    name: 'Notion',
    enables: 'Halaman Notion bisa dipakai sebagai pengetahuan agen, seperti berkas di Knowledge Base.',
    where: 'Pengaturan > Knowledge base (sumber Notion).',
  },
]

export function ConnectApps() {
  return (
    <section className="connect" id="hubungkan-aplikasi" aria-labelledby="connect-h">
      <header className="connect-head">
        <h2 id="connect-h">Hubungkan aplikasi</h2>
        <CapChip cap="mock" label="Draft" />
      </header>
      <p className="note-box">Ini rancangan tampilan. Sambungan OAuth belum dibuat, jadi belum ada akun yang bisa disambungkan dan belum ada yang tersambung.</p>
      <ul className="connect-grid">
        {APPS.map((a) => (
          <li key={a.id} className="connect-card" data-app={a.id}>
            <div className="connect-top">
              <b>{a.name}</b>
              <CapChip cap="none" label="Belum tersedia · draft" />
            </div>
            <p>{a.enables}</p>
            <p className="quiet small">
              <b>Akan muncul di:</b> {a.where}
            </p>
            <div className="connect-act">
              <button type="button" className="btn soft" disabled aria-describedby={`why-${a.id}`}>
                Hubungkan
              </button>
              <span id={`why-${a.id}`} className="quiet small">
                Belum bisa: sambungan OAuth belum dibangun.
              </span>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
