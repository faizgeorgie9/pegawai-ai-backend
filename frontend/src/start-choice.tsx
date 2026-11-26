import { useData } from './data'
import './start.css'

// Beranda, new install: two ways to get the first AI employees, before the guide card (which needs employees).
export function StartChoice() {
  const { setDialog } = useData()
  return (
    <section className="panel-card start-card" aria-labelledby="start-h">
      <h2 id="start-h">Mulai dari mana?</h2>
      <p className="quiet">Pegawai AI bekerja seperti staf Anda. Pilih cara termudah untuk menyiapkan tim.</p>
      <div className="start-options">
        <div className="start-opt">
          <div className="start-opt-head">
            <h3>Pilih jenis usaha</h3>
            <span className="pill plain">Disarankan</span>
          </div>
          <p>Kami siapkan pegawai yang cocok untuk usaha Anda. Anda tinggal memilih dan mengubahnya.</p>
          <a className="btn primary" href="#/mulai">
            Pilih jenis usaha
          </a>
        </div>
        <div className="start-opt">
          <h3>Tambah satu per satu</h3>
          <p>Pilih pegawai sendiri dari daftar atau buat dari nol.</p>
          <button type="button" className="btn soft" onClick={() => setDialog({ kind: 'bot' })}>
            Tambah satu per satu
          </button>
        </div>
      </div>
    </section>
  )
}
