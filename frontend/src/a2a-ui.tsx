import type { ReactElement } from 'react'
import type { Bot, PeerLink, PeerRef } from './bff'
import { BotAvatar, Icon } from './ui'
import './a2a.css'

// R5 · Pegawai ke pegawai. Small, text-first marks: who handed work over, who started a conversation,
// and where a forwarded turn went. No new colours or buttons: the same pill, avatar and link styles.
export function AgentPill(): ReactElement {
  return (
    <span className="pill plain a2a-pill">
      <Icon d="M5 12h14M13 6l6 6-6 6" size={12} />
      Antar pegawai
    </span>
  )
}

export function PeerBanner({ peer }: { peer: PeerRef }): ReactElement {
  const name = peer.name || 'pegawai lain'
  return (
    <div className="a2a-banner" role="note">
      <p>
        Percakapan ini dimulai oleh <b>{name}</b>, bukan oleh Anda.
      </p>
      {peer.link && (
        <a className="btn link" href={'#' + peer.link}>
          Lihat percakapan asal
        </a>
      )}
    </div>
  )
}

export function ForwardedTo({ to, bots }: { to: PeerLink[]; bots: Bot[] }): ReactElement | null {
  if (!to.length) return null
  const rows = to.map((t) => {
    const bot = bots.find((b) => b.id === t.bot_id)
    const name = bot?.name || 'Pegawai lain'
    return { ...t, bot, name, first: bot?.name ? bot.name.split(' ')[0] : name }
  })
  return (
    <p className="delegates" aria-label={`Diteruskan ke ${rows.map((r) => r.name).join(', ')}`}>
      Diteruskan ke →
      {rows.map((r, i) =>
        r.link ? (
          <a key={`${r.bot_id}-${i}`} className="delegate a2a-link" href={'#' + r.link}>
            <BotAvatar bot={r.bot} size={16} />
            {r.first}
          </a>
        ) : (
          <span key={`${r.bot_id}-${i}`} className="delegate">
            <BotAvatar bot={r.bot} size={16} />
            {r.first}
          </span>
        ),
      )}
    </p>
  )
}
