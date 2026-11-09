import { useEffect, useRef, useState } from 'react'
import { api, errText } from './bff'
import type { ActivityRow, Scope } from './bff'
import { useData } from './data'
import { ErrorLine, stamp } from './ui'

const PAGE = 100
const dur = (s: number) => (s <= 0 ? '–' : s < 1 ? `${Math.round(s * 1000)} md` : `${s.toFixed(1).replace('.', ',')} dtk`)

// scope: the same table inside the side panel, limited to one conversation (stacked rows, no page header).
export default function Activity({ scope, version }: { scope?: Scope; version?: number } = {}) {
  const { bots } = useData()
  const [rows, setRows] = useState<ActivityRow[]>([])
  const [state, setState] = useState<'loading' | 'ok' | 'error'>('loading')
  const [error, setError] = useState('')
  const [more, setMore] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [bot, setBot] = useState('')
  const [status, setStatus] = useState('')
  const [open, setOpen] = useState<string | null>(null)
  const epoch = useRef(0)

  function load() {
    const mine = ++epoch.current
    setState('loading')
    api.activity({ bot, status, ...scope }).then(
      (r) => {
        if (mine !== epoch.current) return
        setRows(r)
        setMore(r.length >= PAGE)
        setState('ok')
      },
      (e) => {
        if (mine !== epoch.current) return
        setError(errText(e))
        setState('error')
      },
    )
  }
  useEffect(load, [bot, status, scope?.session_id, scope?.group_id]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!scope || !version) return
    const t = window.setTimeout(load, 500) // a run finished: refresh quietly
    return () => window.clearTimeout(t)
  }, [version]) // eslint-disable-line react-hooks/exhaustive-deps

  async function loadMore() {
    const last = rows[rows.length - 1]
    if (!last) return
    setLoadingMore(true)
    try {
      const r = await api.activity({ bot, status, before: last.id, ...scope })
      setRows((cur) => [...cur, ...r.filter((x) => !cur.some((c) => c.id === x.id))])
      setMore(r.length >= PAGE)
    } catch (e) {
      setError(errText(e))
      setState('error')
    } finally {
      setLoadingMore(false)
    }
  }

  return (
    <section className={scope ? 'act-scope' : 'page'} aria-labelledby={scope ? undefined : 'act-h'}>
      {!scope && (
      <header className="page-head">
        <div>
          <h1 id="act-h">Aktivitas</h1>
          <p className="quiet">Bot tidak memiliki akses terminal. Data sensitif disensor otomatis.</p>
        </div>
        <div className="filters">
          <label className="field inline">
            <span>Bot</span>
            <select value={bot} onChange={(e) => setBot(e.target.value)}>
              <option value="">Semua bot</option>
              {bots.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field inline">
            <span>Status</span>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">Semua status</option>
              <option value="ok">Berhasil</option>
              <option value="error">Gagal</option>
            </select>
          </label>
        </div>
      </header>
      )}

      {state === 'loading' && <p className="quiet state">Memuat aktivitas...</p>}
      {state === 'error' && <ErrorLine text={error} onRetry={load} />}
      {state === 'ok' && rows.length === 0 && (
        <div className="state empty-box">
          <h2>Belum ada aktivitas</h2>
          <p className="quiet">{bot || status ? 'Tidak ada aktivitas yang cocok dengan filter ini.' : 'Saat bot memakai alat, catatannya muncul di sini.'}</p>
        </div>
      )}
      {rows.length > 0 && (
        <>
          <div className={scope ? 'table-wrap flat' : 'table-wrap'}>
            <table className={scope ? 'act stack' : 'act'}>
              <thead>
                <tr>
                  <th>Waktu</th>
                  <th>Bot</th>
                  <th>Alat</th>
                  <th>Status</th>
                  <th className="r">Durasi</th>
                  <th>Ringkasan</th>
                  {!scope && <th>Buka</th>}
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td data-label="Waktu" className="num">{stamp(r.time)}</td>
                    <td data-label="Bot">{r.bot_name}</td>
                    <td data-label="Alat">{r.tool || '–'}</td>
                    <td data-label="Status">
                      <span className={`pill ${r.status === 'ok' ? 'ok' : 'bad'}`}>{r.status === 'ok' ? 'Berhasil' : 'Gagal'}</span>
                    </td>
                    {(!scope || r.duration > 0) && <td data-label="Durasi" className="r num">{dur(r.duration)}</td>}
                    <td data-label="Ringkasan" className="sum">
                      {r.preview ? (
                        <button className="sum-btn" aria-expanded={open === r.id} onClick={() => setOpen(open === r.id ? null : r.id)}>
                          <span data-open={open === r.id || undefined}>{r.preview}</span>
                        </button>
                      ) : (
                        '–'
                      )}
                    </td>
                    {!scope && (
                      <td data-label="Buka">
                        {r.link ? (
                          <a className="btn link" href={'#' + r.link}>
                            {r.where || 'Buka'}
                          </a>
                        ) : (
                          '–'
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="quiet small num">{rows.length} catatan ditampilkan</p>
          {more && (
            <button className="btn soft" onClick={() => void loadMore()} disabled={loadingMore}>
              {loadingMore ? 'Memuat...' : 'Muat lagi'}
            </button>
          )}
        </>
      )}
    </section>
  )
}
