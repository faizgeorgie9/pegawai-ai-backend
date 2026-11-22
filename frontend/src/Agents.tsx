import { useCallback, useEffect, useState } from 'react'
import { api, errText } from './bff'
import type { Bot, BotDetail } from './bff'
import { useAdminMode } from './adminMode'
import { useData } from './data'
import { agenPath, botPath, go } from './router'
import { BotAvatar, COLORS, ErrorLine, Icon, I, LOCK, botColor, cleanTaskText, colorLabel, nf, roleLabel, stamp, teamLabel } from './ui'
import { AgentSkills } from './skills-ui'
import { TIERS, tierOf } from './modelTiers'
import { Empty, EffortSelect, Loading, ModelSelect, PageHead, Opt, defaultEffortLabel, defaultModelLabel, effortWord, modelKey, splitModel, statusText, useLoad } from './ui-extra'

// ---------- Daftar ----------
export function AgentList() {
  const { bots, loadState, error, reload } = useData()
  const [team, setTeam] = useState('')
  const [q, setQ] = useState('')
  const teams = [...new Set(bots.map((b) => b.team))]
  const shown = bots.filter(
    (b) => (!team || b.team === team) && `${b.name} ${b.role} ${roleLabel(b.role)}`.toLowerCase().includes(q.trim().toLowerCase()),
  )
  return (
    <section className="page">
      <PageHead
        title="Agen"
        sub="Semua agen, dengan konteks Colorbox."
        actions={
          <a className="btn primary" href="#/agen/baru">
            Pegawai baru
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
      {loadState === 'ok' && bots.length === 0 && <Empty title="Belum ada pegawai AI">Klik Pegawai baru untuk membuat yang pertama.</Empty>}
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
                      {b.builtin && <span className="pill plain">Sistem</span>}
                    </a>
                  </td>
                  <td data-label="Peran">{b.role}</td>
                  <td data-label="Tim"><span className="pill" data-team={b.team}>{teamLabel(b.team)}</span></td>
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
// Run statuses are English server values; show them as plain Indonesian (code issue #4).
const RUN_STATUS: Record<string, string> = {
  completed: 'Selesai',
  done: 'Selesai',
  finished: 'Selesai',
  failed: 'Gagal',
  error: 'Gagal',
  stopped: 'Dihentikan',
  interrupted: 'Dihentikan',
  cancelled: 'Dibatalkan',
  canceled: 'Dibatalkan',
  running: 'Berjalan',
  queued: 'Antre',
}
const RUN_PILL: Record<string, string> = {
  completed: 'ok',
  done: 'ok',
  finished: 'ok',
  failed: 'bad',
  error: 'bad',
  stopped: 'idle',
  interrupted: 'idle',
  cancelled: 'idle',
  canceled: 'idle',
  running: 'run',
  queued: 'wait',
}
const TABS = [
  ['ringkasan', 'Ringkasan'],
  ['pekerjaan', 'Pekerjaan'],
  ['keahlian', 'Keahlian'],
] as const
type TabId = (typeof TABS)[number][0]
export function AgentDetail({ id }: { id: string }) {
  const { setDialog } = useData()
  const admin = useAdminMode()
  const backHref = admin ? '#/agen' : '#/'
  const backLabel = admin ? 'Semua agen' : 'Beranda'
  const botFn = useCallback(() => api.bot(id), [id])
  const bot = useLoad(botFn)
  const extraFn = useCallback(
    () =>
      Promise.all([
        api.sessions(id),
        api.runs('recent', 8, id),
        api.usageBots('month'),
        api.usageBots('all'),
        api.models().catch(() => null),
      ]),
    [id],
  )
  const extra = useLoad(extraFn)
  const [tab, setTab] = useState<TabId>(() => {
    const t = new URLSearchParams(location.hash.split('?')[1] ?? '').get('tab')
    return TABS.some(([id]) => id === t) ? (t as TabId) : 'ringkasan'
  })
  const [allText, setAllText] = useState(false)
  const [wide] = useState(() => window.matchMedia('(min-width: 901px)').matches)

  function onTabKey(e: React.KeyboardEvent) {
    const i = TABS.findIndex(([id]) => id === tab)
    const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0
    const next = d ? TABS[(i + d + TABS.length) % TABS.length][0] : e.key === 'Home' ? TABS[0][0] : e.key === 'End' ? TABS[TABS.length - 1][0] : undefined
    if (!next) return
    e.preventDefault()
    setTab(next)
    document.getElementById('tab-' + next)?.focus()
  }

  if (bot.state === 'loading') return <section className="page"><Loading text="Memuat pegawai..." shape="page" /></section>
  if (bot.state === 'error')
    return (
      <section className="page">
        <a className="back" href={backHref}>
          {backLabel}
        </a>
        {/Tidak ditemukan|tidak ditemukan/.test(bot.error) ? <Empty title="Pegawai tidak ditemukan">Mungkin sudah dihapus.</Empty> : <ErrorLine text={bot.error} onRetry={bot.retry} />}
      </section>
    )
  const b = bot.data as BotDetail
  const [sessions, runs, um, ua, cat] = extra.data ?? [[], [], [], [], null]
  const month = um.find((x) => x.bot_id === id)
  const all = ua.find((x) => x.bot_id === id)
  const tier = b.model ? TIERS.find((t) => t.id === tierOf(b.model))?.label : undefined
  const persona = b.persona || (b.builtin ? 'Dikelola sistem.' : 'Belum ada petunjuk tugas. Klik Atur untuk menulisnya.')
  const long = (b.persona ?? '').length > 200

  return (
    <section className="page">
      <a className="back" href={backHref}>
        {backLabel}
      </a>
      <header className="page-head" style={{ ['--bot' as string]: botColor(b) }}>
        <div className="row" style={{ width: 'auto', padding: 0 }}>
          <BotAvatar bot={b} size={48} />
          <div>
            <h1>{b.name}</h1>
            <p className="quiet">
              {roleLabel(b.role)} · {teamLabel(b.team)} · {statusText(b)}
            </p>
          </div>
        </div>
        <div className="head-actions">
          <a className="btn primary" href={'#' + botPath(b.id)}>
            Ajak bicara
          </a>
          <button className="btn outline" onClick={() => setDialog({ kind: 'edit', bot: b })}>
            Atur
          </button>
          {!b.builtin && (
            <button className="btn danger" onClick={() => setDialog({ kind: 'delete', bot: b })}>
              Hapus
            </button>
          )}
        </div>
      </header>

      <div className="tabs" role="tablist" aria-label="Bagian detail pegawai" onKeyDown={onTabKey}>
        {TABS.map(([id, label]) => (
          <button
            key={id}
            id={'tab-' + id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            aria-controls={'panel-' + id}
            tabIndex={tab === id ? 0 : -1}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      <div id={'panel-' + tab} role="tabpanel" aria-labelledby={'tab-' + tab} className="tab-body">
        {tab === 'ringkasan' && (
          <>
            {extra.state === 'loading' && <Loading text="Memuat pemakaian..." shape="ledger" rows={1} />}
            {extra.state === 'error' && <ErrorLine text={extra.error} onRetry={extra.retry} />}
            {extra.state === 'ok' && (
              <dl className={admin ? 'kpis k4' : 'kpis k2'}>
                {(admin
                  ? [
                      { label: 'Percakapan', value: sessions.length },
                      { label: 'Pemakaian bulan ini (token)', value: month?.total ?? 0 },
                      { label: 'Pemakaian total (token)', value: all?.total ?? 0 },
                      { label: 'Tugas total', value: all?.runs ?? 0 },
                    ]
                  : [
                      { label: 'Percakapan', value: sessions.length },
                      { label: 'Tugas dikerjakan', value: all?.runs ?? 0 },
                    ]
                ).map((k) => (
                  <div key={k.label}>
                    <dt>{k.label}</dt>
                    <dd className="num">{nf.format(k.value)}</dd>
                  </div>
                ))}
              </dl>
            )}

      <div className="two perm-block">
        <section className="cbox perm-edit" aria-labelledby="perm-edit-h">
          <header className="perm-head">
            <h2 id="perm-edit-h">Bisa Anda ubah</h2>
            <button className="btn soft sm" onClick={() => setDialog({ kind: 'edit', bot: b })}>
              Atur
            </button>
          </header>
          <ul className="perm-list">
            {!b.builtin && (
              <>
                <li>
                  <b>Jenis</b>
                  <small className="quiet small">Dibuat oleh Anda</small>
                </li>
                <li>
                  <b>Nama</b>
                  <small className="quiet small">{b.name}</small>
                </li>
                <li>
                  <b>Tugas dan gaya bicara</b>
                  <small className="quiet small">Petunjuk yang mengatur cara {b.name} bekerja</small>
                </li>
              </>
            )}
            <li>
              <b>Warna</b>
              <small className="quiet small">
                <span className="swatch-chip" style={{ background: botColor(b) }} />
                {colorLabel(b.color || 'plain')}
              </small>
            </li>
            <li>
              <b>Tingkat ketelitian</b>
              <small className="quiet small">{tier ?? 'Ikuti bawaan'}</small>
            </li>
          </ul>
          <p className="quiet small">Perubahan berlaku mulai tugas berikutnya.</p>
        </section>
        <details className="cbox perm-locked" open={wide}>
          <summary>
            <h2 id="perm-locked-h">
              <Icon d={LOCK} size={16} /> Diatur sistem
            </h2>
            <Icon d={I.down} size={16} />
          </summary>
          <ul className="perm-list">
            {b.builtin && (
              <li>
                <b>Nama dan tugas</b>
                <small className="quiet small">Pegawai bawaan: dikelola tim AITopTrends.</small>
              </li>
            )}
            <li>
              <b>Aturan inti</b>
              <small className="quiet small">Cara dasar {b.name} bekerja dan menjaga data bisnis Anda.</small>
            </li>
            <li>
              <b>Izin keamanan</b>
              <small className="quiet small">Tindakan berisiko, misalnya menghapus berkas atau mengirim email, selalu menunggu izin Anda.</small>
            </li>
          </ul>
          <a className="btn link" href="#/pengaturan/keamanan">
            Lihat batasan keamanan
          </a>
        </details>
      </div>

      <div className="cbox">
        <h2>Tugas dan gaya bicara</h2>
        <p className={'persona' + (long && !allText ? ' persona-clamp' : '')}>{persona}</p>
        {long && (
          <button type="button" className="btn link small" aria-expanded={allText} onClick={() => setAllText((v) => !v)}>
            {allText ? 'Tampilkan lebih sedikit' : 'Baca selengkapnya'}
          </button>
        )}
      </div>

      {b.createdAt > 0 && <p className="quiet small">Dibuat {stamp(b.createdAt)}</p>}

      {admin && (
        <div className="cbox">
          <h2>Identitas</h2>
          <dl className="kv kv-wide">
            <dt>Warna</dt>
            <dd>
              <span className="swatch-chip" style={{ background: botColor(b) }} />
              {colorLabel(b.color || 'plain')}
            </dd>
            <dt>Model</dt>
            <dd>{b.model || defaultModelLabel(cat)}</dd>
            <dt>Tingkat berpikir</dt>
            <dd>{effortWord(b.effort) || defaultEffortLabel(cat)}</dd>
          </dl>
          <p className="quiet small">
            <a className="btn link" href={'#' + agenPath(b.id, 'ubah')}>
              Pengaturan lanjutan
            </a>
          </p>
        </div>
      )}
          </>
        )}

        {tab === 'pekerjaan' &&
          (extra.state === 'loading' ? (
            <Loading text="Memuat pekerjaan..." shape="table" />
          ) : extra.state === 'error' ? (
            <ErrorLine text={extra.error} onRetry={extra.retry} />
          ) : (
            <div className="block">
              <header>
                <h2>Tugas terakhir</h2>
              </header>
              {runs.length === 0 ? (
                <Empty title="Belum ada tugas">
                  <a className="btn primary" href={'#' + botPath(b.id)}>
                    Ajak {b.name} bicara
                  </a>
                </Empty>
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
                          <td data-label="Tugas">
                            <span className="clamp2">{cleanTaskText(r.input || '').split(/\s*\(id tugas:/)[0].trim() || '–'}</span>
                          </td>
                          <td data-label="Status">
                            <span className={`pill ${RUN_PILL[r.status] ?? 'idle'} run-status`}>{RUN_STATUS[r.status] ?? r.status}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}

        {tab === 'keahlian' && (
          <div className="cbox">
            <h2>Keahlian pegawai</h2>
            <AgentSkills slug={id} />
          </div>
        )}
      </div>
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
  const { bots, refreshBots, flash, setDialog } = useData()
  const admin = useAdminMode()
  const botFn = useCallback(() => api.bot(id), [id])
  const bot = useLoad(botFn)
  const [f, setF] = useState({ name: '', role: '', team: '', color: 'plain', persona: '', model: '', effort: '' })
  const [newTeam, setNewTeam] = useState(false)
  const [touched, setTouched] = useState(false)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const d = bot.data

  useEffect(() => {
    if (d) setF({ name: d.name, role: d.role, team: d.team, color: d.color || 'plain', persona: d.persona, model: modelKey(d.provider, d.model), effort: d.effort })
  }, [d])

  // The technical edit page is admin-only: everyone else gets the simple dialog over the detail page.
  useEffect(() => {
    if (admin || !d) return
    go(agenPath(id), true)
    setDialog({ kind: 'edit', bot: d })
  }, [admin, d, id, setDialog])

  if (!admin) return null
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
    const patch: Record<string, string | null> = {}
    if (!ro) for (const k of ['name', 'role', 'team', 'persona'] as const) if (f[k].trim() !== d![k].trim()) patch[k] = f[k].trim()
    if (f.color !== (d!.color || 'plain')) patch.color = f.color
    if (f.model !== modelKey(d!.provider, d!.model)) Object.assign(patch, splitModel(f.model))
    if (f.effort !== d!.effort) patch.reasoning_effort = f.effort || null
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
        {ro && <p className="note-box">Agen sistem: nama, peran, tim, dan persona dikelola tim AITopTrends. Warna, model, dan tingkat berpikir bisa diubah.</p>}
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
          <ModelSelect value={f.model} onChange={(v) => set('model', v)} />
          <EffortSelect value={f.effort} onChange={(v) => set('effort', v)} />
          <small className="quiet">Bawaan memakai model standar agen ini. Pilihan baru berlaku di tugas berikutnya.</small>
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
