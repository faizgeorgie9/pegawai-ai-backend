import { useState } from 'react'
import { useData } from './data'
import { agenPath, botPath } from './router'
import { BotAvatar, botColor, roleLabel } from './ui'
import { Empty, statusText } from './ui-extra'

// Beranda's employee list: who works for this business, what they are doing, and the two things a user does with them.
export function TimAnda() {
  const { bots, loadState, setDialog } = useData()
  const [showAll, setShowAll] = useState(false)

  if (loadState === 'error' && bots.length === 0) return null

  // Working first, then the main contact (Project Manager), then the server's own order.
  const rank = (b: (typeof bots)[number]) => (b.status !== 'idle' ? 0 : /project manager/i.test(b.role) ? 1 : 2)
  const sorted = [...bots].sort((a, b) => rank(a) - rank(b))
  const shown = showAll ? sorted : sorted.slice(0, 6)
  const working = bots.filter((b) => b.status !== 'idle').length

  return (
    <section className="panel-card team-card" data-collapsed={!showAll || undefined} aria-labelledby="team-h">
      <header className="team-head">
        <h2 id="team-h">Pegawai AI Anda</h2>
        <span className="quiet small">
          {bots.length} pegawai · {working}
          <span className="hide-sm"> sedang</span> bekerja
        </span>
      </header>
      {bots.length === 0 ? (
        <Empty title="Belum ada pegawai AI">
          <p className="team-empty">Buat pegawai pertama Anda untuk mulai mendelegasikan pekerjaan.</p>
          <a className="btn primary" href="#/agen/baru">
            Pegawai baru
          </a>
        </Empty>
      ) : (
        <>
          <ul className="ledger team-grid">
            {shown.map((b) => {
              const still = b.status === 'idle' && !b.deleteError
              const line = still ? `Siap · ${roleLabel(b.role)}` : statusText(b)
              return (
                <li key={b.id} className="team-row" style={{ ['--bot' as string]: botColor(b) }}>
                  <BotAvatar bot={b} size={36} />
                  <span className="ledger-main">
                    <a className="team-name" href={'#' + agenPath(b.id)}>
                      <b>{b.name}</b>
                    </a>
                    <small className="team-status">
                      <span
                        className="status-dot"
                        data-s={b.status}
                        role="img"
                        aria-label={b.status === 'idle' ? 'Siap' : b.status === 'working' ? 'Bekerja' : 'Berdiskusi'}
                      />
                      <span className="team-status-text" title={line}>
                        {line}
                      </span>
                    </small>
                  </span>
                  <span className="team-actions">
                    <a className="btn soft sm" href={'#' + botPath(b.id)} aria-label={`Ajak ${b.name} bicara`}>
                      Ajak bicara
                    </a>
                    <button type="button" className="btn outline sm" aria-label={`Atur ${b.name}`} onClick={() => setDialog({ kind: 'edit', bot: b })}>
                      Atur
                    </button>
                  </span>
                </li>
              )
            })}
          </ul>
          {sorted.length > 3 && (
            <button
              type="button"
              className="btn link team-more"
              data-few={sorted.length <= 6 || undefined}
              aria-expanded={showAll}
              onClick={() => setShowAll((v) => !v)}
            >
              {showAll ? 'Tampilkan lebih sedikit' : `Lihat semua ${sorted.length} pegawai`}
            </button>
          )}
        </>
      )}
    </section>
  )
}
