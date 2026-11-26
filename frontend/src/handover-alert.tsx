// Beranda: one card that says which WhatsApp customers wait for a human. It reads the shared queue so the
// Sidebar badge, this card, and the Pelanggan page always show the same numbers. No close button: it leaves
// on its own once every customer is answered.
import type { ReactElement } from 'react'
import { HANDOVER_REASON, useHandoverQueue } from './handover'
import { pelangganPath } from './router'
import { ago } from './ui'
import './handover.css'

export function HandoverAlert(): ReactElement | null {
  const { ready, needs, counts } = useHandoverQueue()
  if (!ready || counts.needs_human === 0) return null
  const n = counts.needs_human
  return (
    <section className="panel-card hv-alert" aria-labelledby="hv-alert-h" aria-live="polite">
      <h2 id="hv-alert-h">
        Pelanggan butuh manusia
        <span className="pill wait count-pill">{n}</span>
      </h2>
      <ul className="ledger">
        {needs.slice(0, 3).map((c) => {
          const name = c.customer || 'Pelanggan'
          return (
            <li key={c.id} className="ledger-row">
              <span className="ledger-main">
                <b>{name}</b>
                <small>{[HANDOVER_REASON[c.reason], ago(c.since)].filter(Boolean).join(' · ')}</small>
              </span>
              <a className="btn primary sm" href={'#' + pelangganPath(c.id)} aria-label={`Buka percakapan ${name}`}>
                Buka
              </a>
            </li>
          )
        })}
        {n > 3 && (
          <li>
            <a className="ledger-row ledger-more" href="#/pelanggan">
              Dan {n - 3} lainnya di Pelanggan
            </a>
          </li>
        )}
      </ul>
    </section>
  )
}
