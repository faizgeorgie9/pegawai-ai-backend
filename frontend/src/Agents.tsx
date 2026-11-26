import { useCallback, useEffect, useRef, useState } from 'react'
import { api, canWhatsApp, errText } from './bff'
import type { Bot, BotDetail, MemoryItem } from './bff'
import { useAdminMode } from './adminMode'
import { useData } from './data'
import { agenPath, botPath, go } from './router'
import { BotAvatar, CHEVRON, COLORS, ErrorLine, Icon, I, LOCK, botColor, cleanTaskText, colorLabel, nf, roleLabel, stamp, teamLabel } from './ui'
import { AgentSkills } from './skills-ui'
import { TelegramRow, TelegramTab } from './telegram-ui'
import { WhatsAppRow, WhatsAppTab } from './whatsapp-ui'
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
  ['telegram', 'Telegram'],
  ['whatsapp', 'WhatsApp'],
  ['ingatan', 'Ingatan'],
] as const
type TabId = (typeof TABS)[number][0]

// A row that opens the Atur dialog, so the card stays the one place to change colour and precision without a second button.
function SettingRow({ label, value, onClick }: { label: string; value: React.ReactNode; onClick: () => void }) {
  return (
    <li>
      <button
        type="button"
        onClick={onClick}
        style={{ display: 'flex', alignItems: 'center', gap: 12, width: '100%', minHeight: 44, padding: '4px 0', border: 0, background: 'transparent', textAlign: 'left', cursor: 'pointer' }}
      >
        <b>{label}</b>
        <span className="quiet small" style={{ marginLeft: 'auto', textAlign: 'right' }}>
          {value}
        </span>
        <span aria-hidden="true" style={{ flex: 'none', color: 'var(--muted)' }}>
          <Icon d={CHEVRON} size={14} />
        </span>
      </button>
    </li>
  )
}

export function AgentDetail({ id }: { id: string }) {
  const { bots, setDialog } = useData()
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
  const tablist = useRef<HTMLDivElement>(null)

  // The WhatsApp tab exists only for an employee that may answer WhatsApp (K2). A link that asks for it
  // on anybody else falls back to Ringkasan instead of opening a tab that is not there.
  const loaded = bot.state === 'ok' ? (bots.find((x) => x.id === id) ?? (bot.data as BotDetail)) : undefined
  const allowWhatsApp = !!loaded && canWhatsApp(loaded)
  useEffect(() => {
    if (loaded && tab === 'whatsapp' && !allowWhatsApp) setTab('ringkasan')
  }, [loaded, allowWhatsApp, tab])

  // A narrow screen shows only part of the tab row; keep the selected tab centred without moving the page.
  useEffect(() => {
    const box = tablist.current
    const a = box?.querySelector<HTMLElement>('[aria-selected="true"]')
    if (!box || !a || box.scrollWidth <= box.clientWidth) return
    const r = a.getBoundingClientRect(), b = box.getBoundingClientRect()
    box.scrollLeft += r.left - b.left - (b.width - r.width) / 2
  }, [tab, bot.state, allowWhatsApp])

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
  // FE-3: the Atur dialog puts the saved bot into the shared list, so the card, avatar and values here follow at once
  // instead of waiting for a page reload. The detail snapshot still supplies what the list does not carry (persona).
  const live = bots.find((x) => x.id === id)
  const b = live ? { ...(bot.data as BotDetail), ...live } : (bot.data as BotDetail)
  const tabs = TABS.filter(([tid]) => tid !== 'whatsapp' || canWhatsApp(b))

  function onTabKey(e: React.KeyboardEvent) {
    const i = tabs.findIndex(([tid]) => tid === tab)
    const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0
    const next = d ? tabs[(i + d + tabs.length) % tabs.length][0] : e.key === 'Home' ? tabs[0][0] : e.key === 'End' ? tabs[tabs.length - 1][0] : undefined
    if (!next) return
    e.preventDefault()
    setTab(next)
    document.getElementById('tab-' + next)?.focus()
  }
  const [sessions, runs, um, ua, cat] = extra.data ?? [[], [], [], [], null]
  const month = um.find((x) => x.bot_id === id)
  const all = ua.find((x) => x.bot_id === id)
  const tier = b.model ? TIERS.find((t) => t.id === tierOf(b.model))?.label : undefined
  const persona = b.persona || (b.builtin ? 'Dikelola sistem.' : 'Belum ada petunjuk tugas. Klik Atur untuk menulisnya.')
  const long = (b.persona ?? '').length > 200
  const kpis = admin
    ? [
        { label: 'Percakapan', value: sessions.length },
        { label: 'Pemakaian bulan ini (token)', value: month?.total ?? 0 },
        ...((all?.total ?? 0) === (month?.total ?? 0) ? [] : [{ label: 'Pemakaian total (token)', value: all?.total ?? 0 }]),
        { label: 'Tugas total', value: all?.runs ?? 0 },
      ]
    : [
        { label: 'Percakapan', value: sessions.length },
        { label: 'Tugas dikerjakan', value: all?.runs ?? 0 },
      ]

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

      <div ref={tablist} className="tabs" role="tablist" aria-label="Bagian detail pegawai" onKeyDown={onTabKey}>
        {tabs.map(([tid, label]) => (
          <button
            key={tid}
            id={'tab-' + tid}
            type="button"
            role="tab"
            aria-selected={tab === tid}
            aria-controls={'panel-' + tid}
            tabIndex={tab === tid ? 0 : -1}
            onClick={() => setTab(tid)}
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
              <dl className={admin ? (kpis.length === 4 ? 'kpis k4' : 'kpis') : 'kpis k2'}>
                {kpis.map((k) => (
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
            <h2 id="perm-edit-h">Pengaturan pegawai</h2>
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
            <SettingRow
              label="Warna"
              value={
                <>
                  <span className="swatch-chip" style={{ background: botColor(b) }} />
                  {colorLabel(b.color || 'plain')}
                </>
              }
              onClick={() => setDialog({ kind: 'edit', bot: b })}
            />
            <SettingRow label="Tingkat ketelitian" value={tier ?? 'Ikuti bawaan'} onClick={() => setDialog({ kind: 'edit', bot: b })} />
            <TelegramRow bot={b} onOpen={() => setTab('telegram')} />
            <WhatsAppRow bot={b} onOpen={() => setTab('whatsapp')} />
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

        {tab === 'telegram' && <TelegramTab bot={b} />}

        {tab === 'whatsapp' && canWhatsApp(b) && <WhatsAppTab bot={b} />}

        {tab === 'ingatan' && <AgentMemory bot={b} />}
      </div>
    </section>
  )
}

// ---------- Ingatan ----------
// Plain-language view of what Hermes stores long-term for this profile (MEMORY.md + USER.md).
// Deletes are confirmed in place; a 409 means the entry changed since the list was loaded.
function AgentMemory({ bot }: { bot: Bot }) {
  const memFn = useCallback(() => api.memory(bot.id), [bot.id])
  const mem = useLoad(memFn)
  const [asking, setAsking] = useState('')
  const [clearAsk, setClearAsk] = useState(false)
  const [busy, setBusy] = useState('')
  const [problem, setProblem] = useState('')

  async function remove(item: MemoryItem) {
    setBusy(item.id)
    setProblem('')
    try {
      await api.deleteMemoryItem(bot.id, item.id)
      setAsking('')
      mem.retry()
    } catch (e) {
      setProblem(errText(e))
    } finally {
      setBusy('')
    }
  }
  async function clear() {
    setBusy('all')
    setProblem('')
    try {
      await api.clearMemory(bot.id)
      setClearAsk(false)
      mem.retry()
    } catch (e) {
      setProblem(errText(e))
    } finally {
      setBusy('')
    }
  }

  const d = mem.state === 'ok' ? mem.data : undefined
  const total = d ? d.items.length + d.aboutYou.length : 0
  const pct = d && d.limit.max > 0 ? Math.min(100, Math.round((d.limit.used / d.limit.max) * 100)) : 0
  const meterState = pct >= 100 ? 'exceeded' : pct >= 80 ? 'warning' : undefined

  return (
    <div className="cbox">
      <h2>Ingatan {bot.name}</h2>
      <p className="quiet">Hal yang diingat {bot.name} dari percakapan sebelumnya. Hapus kalau sudah tidak benar.</p>
      <p className="quiet small">
        Ingatan ini dipakai bersama oleh semua orang yang memakai {bot.name}. Menghapus ingatan tidak menghapus riwayat percakapan.
      </p>

      {problem && (
        <p className="problem-bar small" role="alert">
          {problem}
        </p>
      )}
      {mem.state === 'loading' && <Loading text={`Memuat ingatan ${bot.name}...`} shape="lines" rows={3} />}
      {mem.state === 'error' && <ErrorLine text={mem.error} onRetry={mem.retry} />}

      {d && (
        <>
          {total === 0 ? (
            <Empty title="Belum ada yang diingat">
              Pegawai mencatat hal penting dari percakapan, misalnya saat Anda menulis "Tolong ingat: …".
            </Empty>
          ) : (
            <>
              <div className="cost-meter mem-meter" data-state={meterState}>
                <span className="quiet small">
                  {nf.format(d.limit.used)} dari {nf.format(d.limit.max)} karakter terpakai
                </span>
                <span className="set-meter">
                  <span style={{ width: `${pct}%` }} />
                </span>
              </div>

              <h3 className="mem-head">Yang diingat {bot.name}</h3>
              {d.items.length === 0 ? (
                <p className="quiet small">Belum ada catatan dari percakapan.</p>
              ) : (
                <ul className="mem-list">
                  {d.items.map((item) => (
                    <MemRow key={item.id} item={item} asking={asking === item.id} busy={busy === item.id} anyBusy={!!busy} onAsk={() => setAsking(item.id)} onCancel={() => setAsking('')} onDelete={() => void remove(item)} />
                  ))}
                </ul>
              )}

              {d.aboutYou.length > 0 && (
                <>
                  <h3 className="mem-head">Tentang Anda</h3>
                  <p className="quiet small">Catatan yang {bot.name} simpan tentang Anda dari percakapan sebelumnya.</p>
                  <ul className="mem-list">
                    {d.aboutYou.map((item) => (
                      <MemRow key={item.id} item={item} asking={asking === item.id} busy={busy === item.id} anyBusy={!!busy} onAsk={() => setAsking(item.id)} onCancel={() => setAsking('')} onDelete={() => void remove(item)} />
                    ))}
                  </ul>
                </>
              )}

              {!clearAsk ? (
                <button className="btn quiet-btn danger-text mem-clear" onClick={() => setClearAsk(true)} disabled={!!busy}>
                  Hapus semua ingatan
                </button>
              ) : (
                <div className="mem-confirm" role="alert">
                  <p>
                    Hapus semua yang diingat {bot.name}? Catatan tentang Anda juga ikut terhapus. Riwayat percakapan dan dokumen di Pengetahuan tidak berubah. Tindakan ini tidak bisa dibatalkan.
                  </p>
                  <div className="confirm-actions">
                    <button className="btn danger" disabled={busy === 'all'} onClick={() => void clear()}>
                      {busy === 'all' ? 'Menghapus...' : 'Ya, hapus semua'}
                    </button>
                    <button className="btn quiet-btn" disabled={busy === 'all'} onClick={() => setClearAsk(false)}>
                      Batal
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}

function MemRow(p: { item: MemoryItem; asking: boolean; busy: boolean; anyBusy: boolean; onAsk: () => void; onCancel: () => void; onDelete: () => void }) {
  return (
    <li className="mem-item">
      <p className="mem-text">{p.item.text}</p>
      {p.asking ? (
        <span className="confirm-actions" role="alert">
          <button className="btn danger sm" disabled={p.busy} onClick={p.onDelete}>
            {p.busy ? 'Menghapus...' : 'Hapus'}
          </button>
          <button className="btn quiet-btn sm" disabled={p.busy} onClick={p.onCancel}>
            Batal
          </button>
        </span>
      ) : (
        <button className="btn quiet-btn danger-text sm" aria-label={`Hapus ingatan: ${p.item.text.slice(0, 60)}`} disabled={p.anyBusy} onClick={p.onAsk}>
          Hapus
        </button>
      )}
    </li>
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
