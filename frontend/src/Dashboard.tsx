import { useCallback, useState } from 'react'
import { api } from './bff'
import type { Bot } from './bff'
import { useData } from './data'
import { botPath } from './router'
import { AgentCard } from './Lists'
import { ErrorLine, I, Icon, ago, nf, stamp, teamLabel } from './ui'
import { CapChip, Empty, Loading, PageHead, useLoad } from './ui-extra'
import type { Cap } from './ui-extra'

const START_KEY = 'pa.start.dismissed'
const wasDismissed = () => {
  try {
    return localStorage.getItem(START_KEY) === '1'
  } catch {
    return false
  }
}

// "Mulai dari sini": three steps, one button each. Dismissal is remembered when storage works.
function StartCard() {
  const [open, setOpen] = useState(() => !wasDismissed())
  if (!open) return null
  const hide = () => {
    setOpen(false)
    try {
      localStorage.setItem(START_KEY, '1')
    } catch {
      /* storage blocked: the card simply returns on the next visit */
    }
  }
  const steps = [
    { icon: I.chat, title: 'Ngobrol dengan agen', text: 'Tanya bebas ke satu agen.', href: '#/chat', cta: 'Buka Chat' },
    { icon: I.marketing, title: 'Jalankan alur kerja', text: 'Marketing atau Customer Service, langkah demi langkah.', href: '#/marketing', cta: 'Buka Marketing', more: { href: '#/cs', label: 'atau Customer Service' } },
    { icon: I.test, title: 'Evaluasi hasil', text: 'Jalankan skenario uji dan beri nilai 1–5.', href: '#/uji', cta: 'Buka Evaluasi' },
  ]
  return (
    <section className="start card" aria-labelledby="start-h">
      <header>
        <h2 id="start-h">Mulai dari sini</h2>
        <button className="icon-btn" aria-label="Tutup Mulai dari sini" onClick={hide}>
          <Icon d="M6 6l12 12M18 6L6 18" />
        </button>
      </header>
      <ol>
        {steps.map((st, n) => (
          <li key={st.title}>
            <span className="step-ic" aria-hidden="true">
              <Icon d={st.icon} size={20} />
            </span>
            <div>
              <b>
                {n + 1}. {st.title}
              </b>
              <p className="quiet">{st.text}</p>
            </div>
            <span className="start-cta">
              <a className="btn outline" href={st.href}>
                {st.cta}
              </a>
              {st.more && (
                <a className="btn link" href={st.more.href}>
                  {st.more.label}
                </a>
              )}
            </span>
          </li>
        ))}
      </ol>
    </section>
  )
}

const startOfToday = () => new Date().setHours(0, 0, 0, 0) / 1000

export default function Dashboard() {
  const { bots, groups, runs, me, loadState, error, reload, setDialog } = useData()
  const recentFn = useCallback(() => api.runs('recent', 100), [])
  const actFn = useCallback(() => api.activity({ limit: 8 }), [])
  const toolsFn = useCallback(() => api.tools(), [])
  const recent = useLoad(recentFn)
  const act = useLoad(actFn)
  const tools = useLoad(toolsFn)

  if (loadState === 'loading') return <section className="page"><Loading text="Memuat beranda..." /></section>
  if (loadState === 'error') return <section className="page"><ErrorLine text={error} onRetry={reload} /></section>

  const day = startOfToday()
  const todayRuns = (recent.data ?? []).filter((r) => r.started_at >= day).length + runs.filter((r) => r.started_at >= day).length
  const capped = (recent.data?.length ?? 0) >= 100 && (recent.data ?? []).every((r) => r.started_at >= day)
  const lastActive = new Map<string, number>()
  for (const r of [...(recent.data ?? []), ...runs]) lastActive.set(r.bot_id, Math.max(lastActive.get(r.bot_id) ?? 0, r.started_at))
  const teams = bots.reduce<Record<string, Bot[]>>((acc, b) => ((acc[b.team] ??= []).push(b), acc), {})
  const activeToolsets = tools.data ? new Set(tools.data.bots.flatMap((b) => b.toolsets.filter((t) => t.enabled).map((t) => t.name))).size : 0
  const toolsCap: Cap = tools.state === 'error' ? 'unknown' : tools.data && tools.data.bots.some((b) => b.ok) ? 'ok' : 'unknown'

  return (
    <section className="page">
      <PageHead
        title="Beranda"
        sub="Siapa sedang mengerjakan apa."
        actions={
          <>
            <button className="btn primary" onClick={() => (location.hash = bots[0] ? '#' + botPath(bots[0].id) : '#/agen')} disabled={bots.length === 0}>
              Chat dengan agen
            </button>
            <button className="btn outline" onClick={() => setDialog({ kind: 'group' })}>
              Grup baru
            </button>
            <a className="btn outline" href="#/agen/baru">
              Agen baru
            </a>
          </>
        }
      />

      <StartCard />

      <div className="counters">
        <div className="counter-card">
          <span>Tugas aktif</span>
          <b>{nf.format(runs.length)}</b>
        </div>
        <div className="counter-card">
          <span>Tugas hari ini</span>
          <b>{recent.state === 'ok' ? `${nf.format(todayRuns)}${capped ? '+' : ''}` : '–'}</b>
        </div>
        <div className="counter-card">
          <span>Token bulan ini</span>
          <b>{me ? nf.format(me.usage.tokens_month) : '–'}</b>
        </div>
        <div className="counter-card">
          <span>Grup</span>
          <b>{nf.format(groups.length)}</b>
        </div>
      </div>

      <div className="block">
        <header>
          <h2>Agen</h2>
          <a href="#/agen">Semua agen</a>
        </header>
        {bots.length === 0 ? (
          <Empty title="Belum ada agen">
            <a className="btn link" href="#/agen/baru">
              Buat agen pertama
            </a>
          </Empty>
        ) : (
          Object.entries(teams).map(([team, list]) => (
            <div key={team}>
              <h3 className="team-title">{teamLabel(team)}</h3>
              <div className="agent-grid">
                {list.map((b) => (
                  <AgentCard key={b.id} b={b} last={recent.state === 'loading' ? 'Memuat...' : lastActive.get(b.id) ? ago(lastActive.get(b.id)!) : 'Belum ada tugas'} />
                ))}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="block">
        <header>
          <h2>Aktivitas terbaru</h2>
          <a href="#/aktivitas">Lihat semua</a>
        </header>
        {act.state === 'loading' && <Loading text="Memuat aktivitas..." />}
        {act.state === 'error' && <ErrorLine text={act.error} onRetry={act.retry} />}
        {act.state === 'ok' && act.data!.length === 0 && <Empty title="Belum ada aktivitas">Saat agen memakai alat, catatannya muncul di sini.</Empty>}
        {act.state === 'ok' && act.data!.length > 0 && (
          <div className="table-wrap">
            <table className="act">
              <thead>
                <tr>
                  <th>Waktu</th>
                  <th>Agen</th>
                  <th>Alat</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {act.data!.map((r) => (
                  <tr key={r.id}>
                    <td data-label="Waktu" className="num">{stamp(r.time)}</td>
                    <td data-label="Agen">{r.bot_name}</td>
                    <td data-label="Alat">{r.tool || '–'}</td>
                    <td data-label="Status">
                      <span className={`pill ${r.status === 'ok' ? 'ok' : 'bad'}`}>{r.status === 'ok' ? 'Berhasil' : 'Gagal'}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="block">
        <header>
          <h2>Status kemampuan</h2>
        </header>
        <div className="cap-grid">
          <a className="cap-item" href="#/agen">
            Agen: daftar, buat, ubah, hapus <CapChip cap="ok" />
          </a>
          <a className="cap-item" href="#/tools">
            Tools {tools.state === 'loading' ? <CapChip cap="unknown" label="Memuat..." /> : <CapChip cap={toolsCap} label={toolsCap === 'ok' ? `${activeToolsets} toolset aktif` : undefined} />}
          </a>
          <a className="cap-item" href="#/computer-use">
            Computer Use <CapChip cap="blocked" />
          </a>
          <a className="cap-item" href="#/scheduler">
            Scheduler <CapChip cap="blocked" />
          </a>
          <a className="cap-item" href="#/marketing">
            Marketing <CapChip cap="mock" label="Eksperimen, data contoh" />
          </a>
          <a className="cap-item" href="#/cs">
            Customer Service <CapChip cap="mock" label="Eksperimen, requirement belum final" />
          </a>
        </div>
      </div>
    </section>
  )
}
