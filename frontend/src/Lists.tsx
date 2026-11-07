import { useData } from './data'
import type { Bot } from './bff'
import { botPath, groupPath } from './router'
import { BotAvatar, ErrorLine, botColor, teamLabel } from './ui'
import { Empty, Loading, PageHead, statusText } from './ui-extra'

// Agent card shared by Beranda and Chat. `last` is the optional "Terakhir aktif" line (Beranda only).
export function AgentCard({ b, last }: { b: Bot; last?: string }) {
  return (
    <a className="agent-card card-link" href={'#' + botPath(b.id)} style={{ ['--bot' as string]: botColor(b) }}>
      <span className="who">
        <BotAvatar bot={b} size={36} />
        <span className="bot-text">
          <b>{b.name}</b>
          <small>{b.role}</small>
        </span>
      </span>
      <span className="st-line">
        <span className="status-dot" data-s={b.status} aria-hidden="true" />
        {statusText(b)}
      </span>
      {last !== undefined && (
        <dl>
          <dt>Terakhir aktif</dt>
          <dd>{last}</dd>
        </dl>
      )}
    </a>
  )
}

// #/chat: pick one agent to ask freely.
export function ChatHome() {
  const { bots, loadState, error, reload } = useData()
  const teams = bots.reduce<Record<string, Bot[]>>((acc, b) => ((acc[b.team] ??= []).push(b), acc), {})
  return (
    <section className="page">
      <PageHead
        title="Chat"
        sub="Tanya bebas ke satu agen."
        actions={
          <a className="btn outline" href="#/agen/baru">
            Agen baru
          </a>
        }
      />
      {loadState === 'loading' && <Loading text="Memuat agen..." />}
      {loadState === 'error' && bots.length === 0 && <ErrorLine text={error} onRetry={reload} />}
      {loadState === 'ok' && bots.length === 0 && (
        <Empty title="Belum ada agen">
          <a className="btn link" href="#/agen/baru">
            Buat agen pertama
          </a>
        </Empty>
      )}
      {Object.entries(teams).map(([team, list]) => (
        <div key={team} className="block">
          <h2 className="team-title">{teamLabel(team)}</h2>
          <div className="agent-grid">
            {list.map((b) => (
              <AgentCard key={b.id} b={b} />
            ))}
          </div>
        </div>
      ))}
    </section>
  )
}

// #/grup: the groups, one card each.
export function GroupList() {
  const { bots, groups, loadState, error, reload, setDialog } = useData()
  return (
    <section className="page">
      <PageHead
        title="Grup"
        sub="Beberapa agen berdiskusi dalam satu percakapan."
        actions={
          <button className="btn primary" onClick={() => setDialog({ kind: 'group' })}>
            Grup baru
          </button>
        }
      />
      {loadState === 'loading' && <Loading text="Memuat grup..." />}
      {loadState === 'error' && groups.length === 0 && <ErrorLine text={error} onRetry={reload} />}
      {loadState === 'ok' && groups.length === 0 && <Empty title="Belum ada grup">Gabungkan 2 sampai 6 agen lewat tombol Grup baru.</Empty>}
      <div className="agent-grid">
        {groups.map((g) => {
          const ms = g.members.map((m) => bots.find((b) => b.id === m)).filter((b): b is Bot => !!b)
          return (
            <a key={g.id} className="agent-card card-link" href={'#' + groupPath(g.id)}>
              <span className="who">
                <span className="avatar-stack" aria-hidden="true">
                  {ms.slice(0, 3).map((b) => (
                    <BotAvatar key={b.id} bot={b} size={28} />
                  ))}
                </span>
                <span className="bot-text">
                  <b>{g.name}</b>
                  <small>{ms.map((b) => b.name).join(', ')}</small>
                </span>
              </span>
              <span className="st-line">
                {g.running && <span className="live-dot" aria-hidden="true" />}
                {g.running ? 'Diskusi berjalan' : `${g.members.length} anggota`}
              </span>
            </a>
          )
        })}
      </div>
    </section>
  )
}
