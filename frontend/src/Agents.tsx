import { useCallback, useEffect, useState } from 'react'
import { api, errText } from './bff'
import type { Bot, BotDetail } from './bff'
import { useData } from './data'
import { agenPath, botPath, go } from './router'
import { BotAvatar, COLORS, ErrorLine, botColor, nf, stamp, teamLabel } from './ui'
import { CapChip, Empty, Loading, PageHead, Opt, statusText, useLoad } from './ui-extra'

// ---------- Daftar ----------
export function AgentList() {
  const { bots, loadState, error, reload } = useData()
  const [team, setTeam] = useState('')
  const [q, setQ] = useState('')
  const teams = [...new Set(bots.map((b) => b.team))]
  const shown = bots.filter(
    (b) => (!team || b.team === team) && `${b.name} ${b.role}`.toLowerCase().includes(q.trim().toLowerCase()),
  )
  return (
    <section className="page">
      <PageHead
        title="Agen"
        sub="Semua agen, dengan konteks Colorbox."
        actions={
          <a className="btn primary" href="#/agen/baru">
            Agen baru
          </a>
        }
      />
      <div className="toolbar">
        <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari nama atau peran" aria-label="Cari agen" />
        <label className="field inline">
          <span>Tim</span>
          <select value={team} onChange={(e) => setTeam(e.target.value)}>
            <option value="">Semua tim</option>
            {teams.map((t) => (
              <option key={t} value={t}>
                {teamLabel(t)}
              </option>
            ))}
          </select>
        </label>
      </div>
      {loadState === 'loading' && <Loading text="Memuat agen..." shape="table" />}
      {loadState === 'error' && bots.length === 0 && <ErrorLine text={error} onRetry={reload} />}
      {loadState === 'ok' && bots.length === 0 && <Empty title="Belum ada agen">Buat agen pertama lewat tombol Agen baru.</Empty>}
      {loadState === 'ok' && bots.length > 0 && shown.length === 0 && <Empty title="Tidak ada yang cocok">Ubah kata cari atau pilihan tim.</Empty>}
      {shown.length > 0 && (
        <div className="table-wrap">
          <table className="plain">
            <thead>
              <tr>
                <th>Agen</th>
                <th>Peran</th>
                <th>Tim</th>
                <th>Status</th>
                <th>Aksi</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((b) => (
                <tr key={b.id}>
                  <td data-label="Agen">
                    <a className="row" href={'#' + agenPath(b.id)} style={{ ['--bot' as string]: botColor(b), padding: 0 }}>
                      <BotAvatar bot={b} size={28} />
                      <b>{b.name}</b>
                      {b.builtin && <span className="pill plain">Bawaan</span>}
                    </a>
                  </td>
                  <td data-label="Peran">{b.role}</td>
                  <td data-label="Tim">{teamLabel(b.team)}</td>
                  <td data-label="Status">{statusText(b)}</td>
                  <td data-label="Aksi">
                    <span className="head-actions">
                      <a className="btn link" href={'#' + botPath(b.id)}>
                        Chat
                      </a>
                      <a className="btn link" href={'#' + agenPath(b.id)}>
                        Detail
                      </a>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

// ---------- Detail ----------
const RUN_STATUS: Record<string, string> = { completed: 'Selesai', failed: 'Gagal', stopped: 'Dihentikan', running: 'Berjalan', queued: 'Antre' }
export function AgentDetail({ id }: { id: string }) {
  const { setDialog } = useData()
  const botFn = useCallback(() => api.bot(id), [id])
  const bot = useLoad(botFn)
  const extraFn = useCallback(
    () =>
      Promise.all([
        api.sessions(id),
        api.runs('recent', 8, id),
        api.usageBots('month'),
        api.usageBots('all'),
        api.tools(id).then(
          (t) => t.bots[0] ?? null,
          () => null,
        ),
      ]),
    [id],
  )
  const extra = useLoad(extraFn)

  if (bot.state === 'loading') return <section className="page"><Loading text="Memuat agen..." shape="page" /></section>
  if (bot.state === 'error')
    return (
      <section className="page">
        <a className="back" href="#/agen">
          Semua agen
        </a>
        {/Tidak ditemukan|tidak ditemukan/.test(bot.error) ? <Empty title="Agen tidak ditemukan">Mungkin sudah dihapus.</Empty> : <ErrorLine text={bot.error} onRetry={bot.retry} />}
      </section>
    )
  const b = bot.data as BotDetail
  const [sessions, runs, um, ua, tools] = extra.data ?? [[], [], [], [], null]
  const month = um.find((x) => x.bot_id === id)
  const all = ua.find((x) => x.bot_id === id)

  return (
    <section className="page">
      <a className="back" href="#/agen">
        Semua agen
      </a>
      <header className="page-head" style={{ ['--bot' as string]: botColor(b) }}>
        <div className="row" style={{ width: 'auto', padding: 0 }}>
          <BotAvatar bot={b} size={48} />
          <div>
            <h1>{b.name}</h1>
            <p className="quiet">
              {b.role} · {teamLabel(b.team)} · {statusText(b)}
            </p>
          </div>
        </div>
        <div className="head-actions">
          <a className="btn primary" href={'#' + botPath(b.id)}>
            Chat
          </a>
          <a className="btn outline" href={'#' + agenPath(b.id, 'ubah')}>
            Ubah
          </a>
          {!b.builtin && (
            <button className="btn danger" onClick={() => setDialog({ kind: 'delete', bot: b })}>
              Hapus
            </button>
          )}
        </div>
      </header>

      <div className="cbox">
        <h2>Identitas</h2>
        <dl className="kv">
          <dt>Peran</dt>
          <dd>{b.role}</dd>
          <dt>Tim</dt>
          <dd>{teamLabel(b.team)}</dd>
          <dt>Warna</dt>
          <dd>
            <span className="swatch-chip" style={{ background: botColor(b) }} />
            {b.color || 'plain'}
          </dd>
          <dt>Jenis</dt>
          <dd>{b.builtin ? 'Bawaan (tidak bisa dihapus)' : 'Buatan pengguna'}</dd>
          <dt>Dibuat</dt>
          <dd>{b.createdAt ? stamp(b.createdAt) : '–'}</dd>
        </dl>
      </div>

      <div className="cbox">
        <h2>Persona</h2>
        <p className="persona">{b.persona || 'Belum ada persona.'}</p>
      </div>

      {extra.state === 'loading' && <Loading text="Memuat pemakaian..." shape="ledger" rows={2} />}
      {extra.state === 'error' && <ErrorLine text={extra.error} onRetry={extra.retry} />}
      {extra.state === 'ok' && (
        <>
          <dl className="kpis k4">
            <div>
              <dt>Percakapan</dt>
              <dd className="num">{nf.format(sessions.length)}</dd>
            </div>
            <div>
              <dt>Token bulan ini</dt>
              <dd className="num">{nf.format(month?.total ?? 0)}</dd>
            </div>
            <div>
              <dt>Token total</dt>
              <dd className="num">{nf.format(all?.total ?? 0)}</dd>
            </div>
            <div>
              <dt>Tugas total</dt>
              <dd className="num">{nf.format(all?.runs ?? 0)}</dd>
            </div>
          </dl>

          <div className="cbox">
            <h2>Toolset aktif</h2>
            {!tools || !tools.ok ? (
              <p className="quiet">
                <CapChip cap="unknown" /> Daftar toolset belum bisa dimuat dari Hermes.
              </p>
            ) : (
              <div className="chip-row">
                {tools.toolsets.filter((t) => t.enabled).map((t) => (
                  <span key={t.name} className="chip" title={t.description}>
                    {t.name}
                  </span>
                ))}
                {tools.toolsets.every((t) => !t.enabled) && <span className="quiet">Tidak ada toolset aktif.</span>}
              </div>
            )}
          </div>

          <div className="block">
            <header>
              <h2>Tugas terakhir</h2>
            </header>
            {runs.length === 0 ? (
              <Empty title="Belum ada tugas">Kirim pesan lewat Chat untuk memulai.</Empty>
            ) : (
              <div className="table-wrap">
                <table className="plain">
                  <thead>
                    <tr>
                      <th>Waktu</th>
                      <th>Tugas</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.map((r) => (
                      <tr key={r.id}>
                        <td className="num" data-label="Waktu">{stamp(r.started_at)}</td>
                        <td data-label="Tugas">{r.input || '–'}</td>
                        <td data-label="Status">
                          <span className={`pill ${r.status === 'completed' ? 'ok' : r.status === 'failed' ? 'bad' : ''}`}>{RUN_STATUS[r.status] ?? r.status}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </section>
  )
}

// ---------- Ubah ----------
// Same limits as the create dialog and the BFF: name/role/team 1-40 chars, persona 1-2000.
function check(f: { name: string; role: string; team: string; persona: string }) {
  const e: Partial<Record<'name' | 'role' | 'team' | 'persona', string>> = {}
  for (const [k, label] of [['name', 'Nama'], ['role', 'Peran'], ['team', 'Tim']] as const) {
    const v = f[k].trim()
    if (!v) e[k] = `${label} wajib diisi.`
    else if (v.length > 40) e[k] = `${label} maksimal 40 karakter.`
  }
  if (!e.name && !/[a-z0-9]/i.test(f.name.normalize('NFKD'))) e.name = 'Nama harus memuat huruf atau angka.'
  if (!f.persona.trim()) e.persona = 'Persona wajib diisi.'
  else if (f.persona.length > 2000) e.persona = 'Persona maksimal 2.000 karakter.'
  return e
}

export function AgentEdit({ id }: { id: string }) {
  const { bots, refreshBots, flash } = useData()
  const botFn = useCallback(() => api.bot(id), [id])
  const bot = useLoad(botFn)
  const [f, setF] = useState({ name: '', role: '', team: '', color: 'plain', persona: '' })
  const [newTeam, setNewTeam] = useState(false)
  const [touched, setTouched] = useState(false)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const d = bot.data

  useEffect(() => {
    if (d) setF({ name: d.name, role: d.role, team: d.team, color: d.color || 'plain', persona: d.persona })
  }, [d])

  if (bot.state === 'loading') return <section className="page"><Loading text="Memuat agen..." /></section>
  if (bot.state === 'error' || !d)
    return (
      <section className="page">
        <a className="back" href="#/agen">
          Semua agen
        </a>
        <ErrorLine text={bot.error} onRetry={bot.retry} />
      </section>
    )

  const ro = d.builtin // builtin: only the colour (the BFF enforces the same)
  const errs = ro ? {} : check(f)
  const teams = [...new Set(bots.map((b) => b.team))]
  const set = (k: keyof typeof f, v: string) => setF((x) => ({ ...x, [k]: v }))

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setTouched(true)
    if (Object.keys(errs).length) return
    const patch: Record<string, string> = {}
    if (ro) {
      if (f.color !== (d!.color || 'plain')) patch.color = f.color
    } else {
      for (const k of ['name', 'role', 'team', 'persona'] as const) if (f[k].trim() !== d![k].trim()) patch[k] = f[k].trim()
      if (f.color !== (d!.color || 'plain')) patch.color = f.color
    }
    if (!Object.keys(patch).length) return setProblem('Belum ada yang diubah.')
    setBusy(true)
    setProblem('')
    try {
      await api.updateBot(id, patch)
      await refreshBots().catch(() => [])
      flash(`Agen ${f.name.trim()} disimpan`)
      go(agenPath(id))
    } catch (err) {
      setProblem(errText(err))
      setBusy(false)
    }
  }

  const fe = (k: 'name' | 'role' | 'team' | 'persona') => (touched || f[k] !== d[k]) && errs[k]
  return (
    <section className="page">
      <a className="back" href={'#' + agenPath(id)}>
        {d.name}
      </a>
      <PageHead title={`Ubah ${d.name}`} />
      <form className="form-page" onSubmit={(e) => void submit(e)} noValidate>
        {ro && <p className="note-box">Agen bawaan: nama, peran, tim, dan persona dikelola tim backend. Hanya warna yang bisa diubah.</p>}
        <fieldset disabled={busy} className="form-page">
          <label className="field">
            <span>Nama</span>
            <input value={f.name} maxLength={40} disabled={ro} aria-invalid={!!fe('name')} onChange={(e) => set('name', e.target.value)} />
            {fe('name') && <small className="err" role="alert">{errs.name}</small>}
          </label>
          <label className="field">
            <span>Peran</span>
            <input value={f.role} maxLength={40} disabled={ro} aria-invalid={!!fe('role')} onChange={(e) => set('role', e.target.value)} />
            {fe('role') && <small className="err" role="alert">{errs.role}</small>}
          </label>
          <label className="field">
            <span>Tim</span>
            <select
              value={newTeam ? '__new' : f.team}
              disabled={ro}
              onChange={(e) => (e.target.value === '__new' ? (setNewTeam(true), set('team', '')) : (setNewTeam(false), set('team', e.target.value)))}
            >
              {teams.map((t) => (
                <option key={t} value={t}>
                  {teamLabel(t)}
                </option>
              ))}
              <option value="__new">Tim baru…</option>
            </select>
            {newTeam && <input value={f.team} maxLength={40} placeholder="Nama tim baru" aria-label="Nama tim baru" aria-invalid={!!fe('team')} onChange={(e) => set('team', e.target.value)} />}
            {fe('team') && <small className="err" role="alert">{errs.team}</small>}
          </label>
          <div className="field">
            <span id="clr">Warna <Opt /></span>
            <div className="swatches" role="radiogroup" aria-labelledby="clr">
              {Object.entries(COLORS).map(([c, hex]) => (
                <button key={c} type="button" role="radio" aria-checked={c === f.color} aria-label={`Warna ${c}`} className="swatch" style={{ background: hex }} onClick={() => set('color', c)} />
              ))}
            </div>
          </div>
          <label className="field">
            <span>Persona</span>
            <textarea value={f.persona} rows={8} maxLength={2000} disabled={ro} aria-invalid={!!fe('persona')} onChange={(e) => set('persona', e.target.value)} />
            {fe('persona') && <small className="err" role="alert">{errs.persona}</small>}
            <small className="counter num">{f.persona.length} / 2.000</small>
            {!ro && d.template && <small className="quiet">Agen ini dibuat dari template. Menyimpan persona baru menggantikan teks template.</small>}
          </label>
        </fieldset>
        {problem && (
          <p className="problem-bar" role="alert">
            {problem}
          </p>
        )}
        <div className="form-actions">
          <button type="submit" className="btn primary" disabled={busy}>
            {busy ? 'Menyimpan...' : 'Simpan'}
          </button>
          <a className="btn quiet-btn" href={'#' + agenPath(id)}>
            Batal
          </a>
        </div>
      </form>
    </section>
  )
}

// #/agen/baru: the create dialog is reused; this route only opens it over the list.
export function AgentNew() {
  const { setDialog } = useData()
  useEffect(() => {
    go('/agen', true)
    setDialog({ kind: 'bot' })
  }, [setDialog])
  return null
}

export type { Bot }
