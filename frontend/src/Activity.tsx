import './admin.css'
import { useEffect, useRef, useState } from 'react'
import { api, errText } from './bff'
import type { ActivityRow, Scope } from './bff'
import { useData } from './data'
import { toolLabel } from './steps'
import { ErrorLine, cleanTaskText, stamp } from './ui'
import { Loading } from './ui-extra'

const PAGE = 20
const dur = (s: number) => (s <= 0 ? '–' : s < 1 ? `${Math.round(s * 1000)} md` : `${s.toFixed(1).replace('.', ',')} dtk`)

// Admin rows keep the tool's own English summary in the database; the table shows plain Indonesian.
function idSummary(text: string): string {
  const reading = text.match(/^Reading tool details(?:\s*·\s*(\d+)\s+tools?)?$/i)
  if (reading) return `Membaca petunjuk alat${reading[1] ? ` (${reading[1]})` : ''}`
  const searching = text.match(/^Searching tools(?:\s*·\s*(.*))?$/i)
  if (searching) return `Mencari alat${searching[1] ? `: ${searching[1]}` : ''}`
  const mcp = text.match(/^(.+?)\s+Mcp\s*·\s*(.*)$/i)
  if (mcp) return `${mcp[1]}: ${mcp[2]}`
  return text
}

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
    api.activity({ bot, status, limit: PAGE, ...scope }).then(
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
      const r = await api.activity({ bot, status, before: last.id, limit: PAGE, ...scope })
      setRows((cur) => [...cur, ...r.filter((x) => !cur.some((c) => c.id === x.id))])
      setMore(r.length >= PAGE)
    } catch (e) {
      setError(errText(e))
      setState('error')
    } finally {
      setLoadingMore(false)
    }
  }

  // A column with only "–" is noise: show it only when at least one row has a value.
  const hasDuration = rows.some((r) => r.duration > 0)
  const hasLink = rows.some((r) => !!r.link)

  return (
    <section className={scope ? 'act-scope' : 'page act-page'} aria-labelledby={scope ? undefined : 'act-h'}>
      {!scope && (
      <header className="page-head">
        <div>
          <h1 id="act-h">Catatan aktivitas</h1>
          <p className="quiet">Apa yang dikerjakan pegawai AI, dari yang terbaru.</p>
        </div>
        <div className="filters">
          <label className="field inline">
            <span>Pegawai</span>
            <select value={bot} onChange={(e) => setBot(e.target.value)}>
              <option value="">Semua pegawai</option>
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

      {state === 'loading' && <Loading text="Memuat aktivitas..." shape="table" />}
      {state === 'error' && <ErrorLine text={error} onRetry={load} />}
      {state === 'ok' && rows.length === 0 && (
        <div className="state empty-box">
          <h2>Belum ada aktivitas</h2>
          <p className="quiet">{bot || status ? 'Tidak ada aktivitas yang cocok dengan filter ini.' : 'Saat pegawai bekerja, catatannya muncul di sini.'}</p>
        </div>
      )}
      {rows.length > 0 && (
        <>
          <div className={scope ? 'table-wrap flat' : 'table-wrap'}>
            <table className={scope ? 'act stack' : 'act'}>
              <thead>
                <tr>
                  <th>Waktu</th>
                  <th>Pegawai</th>
                  <th>Kegiatan</th>
                  <th>Status</th>
                  {hasDuration && <th className="r">Durasi</th>}
                  <th>Ringkasan</th>
                  {!scope && hasLink && <th>Buka</th>}
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td data-label="Waktu" className="num act-time">{stamp(r.time)}</td>
                    <td data-label="Pegawai" className="act-who">{r.bot_name}</td>
                    <td data-label="Kegiatan" className="act-what">{r.tool ? toolLabel(r.tool) : '–'}</td>
                    <td data-label="Status" className="act-status">
                      <span className={`pill ${r.status === 'ok' ? 'ok' : 'bad'}`}>{r.status === 'ok' ? 'Berhasil' : 'Gagal'}</span>
                    </td>
                    {hasDuration && <td data-label="Durasi" className={r.duration > 0 ? 'r num act-dur' : 'r num none act-dur'}>{dur(r.duration)}</td>}
                    <td data-label="Ringkasan" className="sum">
                      {r.preview ? (
                        <button className="sum-btn" aria-expanded={open === r.id} onClick={() => setOpen(open === r.id ? null : r.id)}>
                          <span data-open={open === r.id || undefined}>{idSummary(cleanTaskText(r.preview))}</span>
                        </button>
                      ) : (
                        '–'
                      )}
                    </td>
                    {!scope && hasLink && (
                      <td data-label="Buka" className={r.link ? 'act-open' : 'act-open none'}>
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
