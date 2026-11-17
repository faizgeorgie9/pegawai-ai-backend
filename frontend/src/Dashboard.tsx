import { useCallback, useEffect, useState } from 'react'
import { ActionCard, useVisibleActions } from './ActionCard'
import { useAdminMode } from './adminMode'
import { api } from './bff'
import { useData } from './data'
import { Onboarding, hasName } from './Onboarding'
import type { Step } from './Onboarding'
import { groupPath } from './router'
import { toolLabel } from './steps'
import { ErrorLine, nf, stamp } from './ui'
import { CapChip, CostMeter, Empty, Loading, PageHead, useLoad } from './ui-extra'
import type { Cap } from './ui-extra'

const startOfToday = () => new Date().setHours(0, 0, 0, 0) / 1000
const TOOLS_WAIT = 8000 // ms before "Tools" stops saying it is loading

type Row = { href: string; name: string; detail: string; cap: Cap; label?: string }

// What waits for the user and what is next, from the task board: the Perlu Anda cards and the queue's scheduled tasks.
// shortcut: reads the board's first cards of each column (up to 40); a board that long needs its own endpoint.
async function loadWork() {
  const board = await api.tasksBoard({})
  const col = (id: string) => board.columns.find((c) => c.id === id)?.cards ?? []
  const plans = board.columns.flatMap((c) => c.cards).filter((c) => c.kind === 'plan')
  const upcoming = col('queue')
    .filter((c) => c.kind === 'task' && c.status === 'scheduled' && c.scheduled_at > 0)
    .sort((a, b) => a.scheduled_at - b.scheduled_at)
    .slice(0, 3)
  return { waiting: col('needs_you'), upcoming, anyPlan: plans.length > 0, approved: plans.some((c) => c.status !== 'review') }
}

// Beranda answers one question: what do I need to do today?
export default function Dashboard() {
  const { groups, runs, me, settings, loadState, error, reload } = useData()
  const admin = useAdminMode()
  const workFn = useCallback(() => loadWork(), [])
  const work = useLoad(workFn)
  const kbFn = useCallback(() => api.kbItems(), [])
  const kb = useLoad(kbFn)
  const connFn = useCallback(() => api.connections(), [])
  const conn = useLoad(connFn)
  const recentFn = useCallback(() => api.runs('recent', 100), [])
  const actFn = useCallback(() => api.activity({ limit: 5 }), [])
  const toolsFn = useCallback(() => api.tools(), [])
  const recent = useLoad(recentFn)
  const act = useLoad(actFn)
  const tools = useLoad(toolsFn)
  const [slow, setSlow] = useState(false)
  const approvals = useVisibleActions() // risky agent actions waiting for the user (and the ones just decided)

  useEffect(() => {
    if (tools.state !== 'loading') return setSlow(false)
    const t = window.setTimeout(() => setSlow(true), TOOLS_WAIT)
    return () => window.clearTimeout(t)
  }, [tools.state])

  if (loadState === 'loading') return <section className="page"><Loading text="Memuat beranda..." shape="page" /></section>
  if (loadState === 'error') return <section className="page"><ErrorLine text={error} onRetry={reload} /></section>

  const team = groups[0] // "Minta tim Anda" opens the first team (Marketing) with the message box ready
  const ask = team ? `#${groupPath(team.id)}?tulis=1` : '#/grup'
  const w = work.data
  const upcoming = w?.upcoming ?? []

  const steps: Step[] = [
    { id: 'name', title: 'Isi nama bisnis', hint: 'Nama bisnis Anda tampil di menu samping.', done: hasName(settings.company_name), href: '#/pengaturan/umum', action: 'Isi nama' },
    { id: 'kb', title: 'Tambahkan pengetahuan bisnis', hint: 'Unggah berkas atau link agar agen mengenal bisnis Anda.', done: (kb.data?.length ?? 0) > 0, href: '#/pengetahuan', action: 'Tambah' },
    { id: 'drive', title: 'Sambungkan Google Drive', hint: 'Ambil berkas langsung dari Drive.', done: !!conn.data?.some((c) => c.provider === 'gdrive' && (c.status === 'connected' || c.status === 'needs_scope')), href: '#/aplikasi', action: 'Sambungkan', optional: true },
    { id: 'plan', title: 'Minta rencana konten pertama', hint: 'Minta Tim Marketing menyusun rencana.', done: !!w?.anyPlan, href: ask, action: 'Minta tim' },
    { id: 'approve', title: 'Setujui rencana konten', hint: 'Tim mulai bekerja setelah Anda setuju.', done: !!w?.approved, href: w?.waiting.some((c) => c.kind === 'plan') ? '#/kanban' : ask, action: 'Tinjau' },
  ]
  // Wait for the data the steps are read from, so the card does not flash steps that are already done.
  const stepsReady = work.state !== 'loading' && kb.state !== 'loading' && conn.state !== 'loading'

  const day = startOfToday()
  const todayRuns = (recent.data ?? []).filter((r) => r.started_at >= day).length + runs.filter((r) => r.started_at >= day).length
  const capped = (recent.data?.length ?? 0) >= 100 && (recent.data ?? []).every((r) => r.started_at >= day)
  const toolsets = tools.data ? new Set(tools.data.bots.flatMap((b) => b.toolsets.filter((t) => t.enabled).map((t) => t.name))).size : 0
  const toolsOk = !!tools.data && tools.data.bots.some((b) => b.ok)
  const toolsRow: Row = toolsOk
    ? { href: '#/tools', name: 'Alat', detail: `${toolsets} alat aktif`, cap: 'ok' }
    : tools.state === 'loading' && !slow
      ? { href: '#/tools', name: 'Alat', detail: 'Memeriksa...', cap: 'unknown', label: 'Memeriksa' }
      : { href: '#/tools', name: 'Alat', detail: 'Belum terjawab. Buka Kemampuan untuk mencoba lagi.', cap: 'unknown', label: 'Belum terjawab' }
  const caps: Row[] = [
    { href: '#/agen', name: 'Agen', detail: 'Daftar, buat, ubah, hapus', cap: 'ok' },
    toolsRow,
    { href: '#/marketing', name: 'Marketing', detail: 'Memakai pengetahuan dan katalog Colorbox', cap: 'ok' },
    { href: '#/cs', name: 'Layanan pelanggan', detail: 'Jawaban perlu ditinjau manusia', cap: 'ok' },
    { href: '#/computer-use', name: 'Computer Use', detail: 'Belum dibuka', cap: 'blocked' },
    { href: '#/kanban', name: 'Jadwal & tugas', detail: 'Tugas berulang dan rencana konten', cap: 'ok' },
  ]

  return (
    <section className="page">
      <PageHead
        title="Beranda"
        sub="Yang perlu Anda lakukan hari ini."
        actions={
          <a className="btn primary" href={ask}>
            Minta tim Anda
          </a>
        }
      />

      {stepsReady && <Onboarding steps={steps} />}

      <div className="two">
        <section className="panel-card" aria-labelledby="need-h">
          <h2 id="need-h">Perlu persetujuan Anda</h2>
          {work.state === 'loading' && <Loading text="Memuat..." shape="ledger" rows={2} />}
          {work.state === 'error' && <ErrorLine text={work.error} onRetry={work.retry} />}
          {approvals.length > 0 && (
            <div className="action-list">
              {approvals.map((a) => (
                <ActionCard key={a.id} action={a} />
              ))}
            </div>
          )}
          {w && w.waiting.length === 0 && approvals.length === 0 && <p className="quiet state-note">Tidak ada yang menunggu.</p>}
          {w && w.waiting.length > 0 && (
            <ul className="ledger">
              {w.waiting.slice(0, 5).map((c) => (
                <li key={c.id} className="ledger-row">
                  <span className="ledger-main">
                    <b>{c.title}</b>
                    <small>{[c.assignee?.name, c.line].filter(Boolean).join(': ')}</small>
                  </span>
                  <a className="btn primary sm" href="#/kanban">
                    Tinjau
                  </a>
                </li>
              ))}
              {w.waiting.length > 5 && (
                <li>
                  <a className="ledger-row ledger-more" href="#/kanban">
                    Dan {w.waiting.length - 5} lainnya di papan tugas
                  </a>
                </li>
              )}
            </ul>
          )}
        </section>

        <section className="panel-card" aria-labelledby="next-h">
          <h2 id="next-h">Berikutnya</h2>
          {work.state === 'loading' && <Loading text="Memuat..." shape="ledger" rows={2} />}
          {w && upcoming.length === 0 && <p className="quiet state-note">Belum ada jadwal terdekat.</p>}
          {upcoming.length > 0 && (
            <ul className="ledger">
              {upcoming.map((u) => (
                <li key={u.id} className="ledger-row">
                  <span className="ledger-main">
                    <b>{u.title}</b>
                    <small>{u.assignee?.name}</small>
                  </span>
                  <span className="num quiet small">{stamp(u.scheduled_at)}</span>
                </li>
              ))}
              <li>
                <a className="ledger-row ledger-more" href="#/kanban">
                  Lihat jadwal &amp; tugas
                </a>
              </li>
            </ul>
          )}
        </section>
      </div>

      <section className="panel-card cost-card" aria-labelledby="cost-h">
        <h2 id="cost-h">Biaya bulan ini</h2>
        {me ? <CostMeter u={me.usage} /> : <p className="quiet state-note">Belum terbaca.</p>}
        {admin && me && (
          <p className="quiet small">
            Pemakaian: <span className="num">{nf.format(me.usage.tokens_month)}</span> token
          </p>
        )}
      </section>

      {admin && (
        <>
          <dl className="kpis">
            <div>
              <dt>Tugas aktif</dt>
              <dd className="num">{nf.format(runs.length)}</dd>
            </div>
            <div>
              <dt>Tugas hari ini</dt>
              <dd className="num">{recent.state === 'ok' ? `${nf.format(todayRuns)}${capped ? '+' : ''}` : '–'}</dd>
            </div>
            <div>
              <dt>Pemakaian bulan ini (token)</dt>
              <dd className="num">{me ? nf.format(me.usage.tokens_month) : '–'}</dd>
            </div>
          </dl>

          <div className="two">
            <section className="panel-card" aria-labelledby="cap-h">
              <h2 id="cap-h">Status kemampuan</h2>
              <ul className="ledger">
                {caps.map((c) => (
                  <li key={c.name}>
                    <a className="ledger-row" href={c.href}>
                      <span className="ledger-main">
                        <b>{c.name}</b>
                        <small>{c.detail}</small>
                      </span>
                      <CapChip cap={c.cap} label={c.label} />
                    </a>
                  </li>
                ))}
              </ul>
            </section>

            <section className="panel-card" aria-labelledby="act-h">
              <h2 id="act-h">Aktivitas terbaru</h2>
              {act.state === 'loading' && <Loading text="Memuat aktivitas..." shape="ledger" />}
              {act.state === 'error' && <ErrorLine text={act.error} onRetry={act.retry} />}
              {act.state === 'ok' && act.data!.length === 0 && <Empty title="Belum ada aktivitas">Catatan muncul di sini saat agen bekerja.</Empty>}
              {act.state === 'ok' && act.data!.length > 0 && (
                <ul className="ledger">
                  {act.data!.slice(0, 5).map((r) => (
                    <li key={r.id} className="ledger-row">
                      <span className="ledger-main">
                        <b>{r.bot_name}</b>
                        <small>
                          {r.tool ? toolLabel(r.tool) : '–'} · <span className="num">{stamp(r.time)}</span>
                        </small>
                      </span>
                      <span className={`pill ${r.status === 'ok' ? 'ok' : 'bad'}`}>{r.status === 'ok' ? 'Berhasil' : 'Gagal'}</span>
                    </li>
                  ))}
                  <li>
                    <a className="ledger-row ledger-more" href="#/aktivitas">
                      Lihat semua
                    </a>
                  </li>
                </ul>
              )}
            </section>
          </div>
        </>
      )}
    </section>
  )
}
