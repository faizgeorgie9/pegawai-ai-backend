import { useCallback, useEffect, useState } from 'react'
import { api } from './bff'
import { useData } from './data'
import { botPath } from './router'
import { ErrorLine, nf, stamp } from './ui'
import { CapChip, Empty, Loading, PageHead, useLoad } from './ui-extra'
import type { Cap } from './ui-extra'

const startOfToday = () => new Date().setHours(0, 0, 0, 0) / 1000
const TOOLS_WAIT = 8000 // ms before "Tools" stops saying it is loading

type Row = { href: string; name: string; detail: string; cap: Cap; label?: string }

// Beranda answers: what can I do here, and how is the system doing?
export default function Dashboard() {
  const { bots, runs, me, loadState, error, reload } = useData()
  const recentFn = useCallback(() => api.runs('recent', 100), [])
  const actFn = useCallback(() => api.activity({ limit: 5 }), [])
  const toolsFn = useCallback(() => api.tools(), [])
  const recent = useLoad(recentFn)
  const act = useLoad(actFn)
  const tools = useLoad(toolsFn)
  const [slow, setSlow] = useState(false)

  useEffect(() => {
    if (tools.state !== 'loading') return setSlow(false)
    const t = window.setTimeout(() => setSlow(true), TOOLS_WAIT)
    return () => window.clearTimeout(t)
  }, [tools.state])

  if (loadState === 'loading') return <section className="page"><Loading text="Memuat beranda..." shape="page" /></section>
  if (loadState === 'error') return <section className="page"><ErrorLine text={error} onRetry={reload} /></section>

  const day = startOfToday()
  const todayRuns = (recent.data ?? []).filter((r) => r.started_at >= day).length + runs.filter((r) => r.started_at >= day).length
  const capped = (recent.data?.length ?? 0) >= 100 && (recent.data ?? []).every((r) => r.started_at >= day)
  const toolsets = tools.data ? new Set(tools.data.bots.flatMap((b) => b.toolsets.filter((t) => t.enabled).map((t) => t.name))).size : 0
  const toolsOk = !!tools.data && tools.data.bots.some((b) => b.ok)
  const toolsRow: Row = toolsOk
    ? { href: '#/tools', name: 'Tools', detail: `${toolsets} toolset aktif`, cap: 'ok' }
    : tools.state === 'loading' && !slow
      ? { href: '#/tools', name: 'Tools', detail: 'Memeriksa ke Hermes...', cap: 'unknown', label: 'Memeriksa' }
      : { href: '#/tools', name: 'Tools', detail: 'Hermes belum menjawab. Buka Kemampuan untuk mencoba lagi.', cap: 'unknown', label: 'Belum terjawab' }
  const caps: Row[] = [
    { href: '#/agen', name: 'Agen', detail: 'Daftar, buat, ubah, hapus', cap: 'ok' },
    toolsRow,
    { href: '#/marketing', name: 'Marketing', detail: 'Memakai knowledge dan katalog Colorbox', cap: 'ok' },
    { href: '#/cs', name: 'Customer Service', detail: 'CS v2.1, perlu tinjauan manusia', cap: 'ok' },
    { href: '#/computer-use', name: 'Computer Use', detail: 'Belum dibuka', cap: 'blocked' },
    { href: '#/scheduler', name: 'Scheduler', detail: 'Belum dibuka', cap: 'blocked' },
  ]

  return (
    <section className="page">
      <PageHead title="Beranda" sub="Mulai dari tiga hal ini, dan lihat kondisi sistem." />

      <div className="actions">
        <article className="act-card">
          <h2>Chat dengan agen</h2>
          <p className="quiet">Tanya bebas ke satu agen.</p>
          <div className="act-btns">
            <a className="btn primary" href={bots[0] ? '#' + botPath(bots[0].id) : '#/chat'}>
              Buka Chat
            </a>
          </div>
        </article>
        <article className="act-card">
          <h2>Jalankan alur kerja</h2>
          <p className="quiet">Langkah demi langkah, dengan hasil terstruktur.</p>
          <div className="act-btns">
            <a className="btn outline" href="#/marketing">
              Marketing
            </a>
            <a className="btn outline" href="#/cs">
              Customer Service
            </a>
          </div>
        </article>
        <article className="act-card">
          <h2>Uji dan nilai</h2>
          <p className="quiet">Jalankan skenario uji, lalu beri nilai 1–5.</p>
          <div className="act-btns">
            <a className="btn outline" href="#/uji">
              Buka Evaluasi
            </a>
          </div>
        </article>
      </div>

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
          <dt>Token bulan ini</dt>
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
          {act.state === 'ok' && act.data!.length === 0 && <Empty title="Belum ada aktivitas">Saat agen memakai alat, catatannya muncul di sini.</Empty>}
          {act.state === 'ok' && act.data!.length > 0 && (
            <ul className="ledger">
              {act.data!.slice(0, 5).map((r) => (
                <li key={r.id} className="ledger-row">
                  <span className="ledger-main">
                    <b>{r.bot_name}</b>
                    <small>
                      {r.tool || '–'} · <span className="num">{stamp(r.time)}</span>
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
    </section>
  )
}
