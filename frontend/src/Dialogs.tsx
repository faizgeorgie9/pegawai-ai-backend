import { useEffect, useState } from 'react'
import { ApiError, api, errText } from './bff'
import type { Bot, BotDetail, ModelCatalog, Plan, Template } from './bff'
import { useData } from './data'
import { botPath, groupPath, go, parse } from './router'
import { BotAvatar, COLORS, Dialog, ErrorLine, botColor, colorLabel, roleLabel, teamLabel } from './ui'
import { Opt, modelKey, splitModel } from './ui-extra'
import { TIERS, tierOf, tiersFrom } from './modelTiers'
import type { TierId } from './modelTiers'
import { useAdminMode } from './adminMode'

type Problem = { text: string; upgrade: boolean } | null
const problemOf = (e: unknown): Problem => ({ text: errText(e), upgrade: e instanceof ApiError && e.upgrade })

// The plan dialog is no longer reachable from the UI, so a 402 shows as a plain error.
function ProblemLine({ p }: { p: Problem; onPlan?: () => void }) {
  if (!p) return null
  return (
    <p className="problem-bar" role="alert">
      {p.text}
    </p>
  )
}

export function Dialogs() {
  const { dialog, setDialog } = useData()
  const close = () => setDialog(null)
  if (!dialog) return null
  if (dialog.kind === 'bot') return <BotDialog onClose={close} />
  if (dialog.kind === 'group') return <GroupDialog id={dialog.id} onClose={close} />
  if (dialog.kind === 'plan') return <PlanDialog onClose={close} />
  if (dialog.kind === 'edit') return <EditBotDialog bot={dialog.bot} onClose={close} />
  return <DeleteBotDialog bot={dialog.bot} onClose={close} />
}

// ---------- Bot baru ----------
function BotDialog({ onClose }: { onClose: () => void }) {
  const { bots, refreshBots, refreshMe, setDialog, flash } = useData()
  const [tab, setTab] = useState<'template' | 'custom'>('template')
  const [tpls, setTpls] = useState<Template[]>([])
  const [tplState, setTplState] = useState<'loading' | 'ok' | 'error'>('loading')
  const [tplError, setTplError] = useState('')
  const [tpl, setTpl] = useState('')
  const [name, setName] = useState('')
  const [role, setRole] = useState('')
  const [team, setTeam] = useState('')
  const [newTeam, setNewTeam] = useState(false)
  const [color, setColor] = useState('rose')
  const [persona, setPersona] = useState('')
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<Problem>(null)
  const [tried, setTried] = useState(false)
  const teams = [...new Set(bots.map((b) => b.team))]
  const NEW = '__new'

  function loadTpls() {
    setTplState('loading')
    api.templates().then(
      (t) => {
        setTpls(t)
        setTplState('ok')
      },
      (e) => {
        setTplError(errText(e))
        setTplState('error')
      },
    )
  }
  useEffect(loadTpls, [])

  function pickTemplate(t: Template) {
    setTpl(t.id)
    setRole(t.role)
    setTeam(t.team)
    setNewTeam(false)
    setName('')
    setProblem(null)
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const body = { name: name.trim(), role: role.trim(), team: team.trim(), color: tab === 'custom' ? color : undefined }
    setTried(true)
    if (Object.keys(errs).length) return
    setBusy(true)
    setProblem(null)
    try {
      const b = await api.createBot(tab === 'template' ? { ...body, template: tpl } : { ...body, persona: persona.trim() })
      await refreshBots().catch(() => [])
      refreshMe()
      onClose()
      flash(`Pegawai ${b.name} dibuat`)
      go(botPath(b.id))
    } catch (err) {
      setProblem(problemOf(err))
      setBusy(false)
    }
  }

  const selected = tpls.find((t) => t.id === tpl)
  const errs: Record<string, string> = {}
  if (!name.trim()) errs.name = 'Nama wajib diisi.'
  if (!role.trim()) errs.role = 'Peran wajib diisi.'
  if (!team.trim()) errs.team = newTeam ? 'Nama tim wajib diisi.' : 'Pilih tim.'
  if (tab === 'custom' && !persona.trim()) errs.persona = 'Tulis tugas pegawai ini, supaya ia tahu cara bekerja.'
  const err = (k: string) => tried && errs[k] && <small className="err" role="alert">{errs[k]}</small>
  const form = (
    <div className="fields">
      <label className="field">
        <span>Nama</span>
        <input value={name} maxLength={40} onChange={(e) => setName(e.target.value)} placeholder="Nama pegawai baru" aria-invalid={tried && !!errs.name} />
        {err('name')}
      </label>
      <label className="field">
        <span>Peran</span>
        <input value={role} maxLength={40} onChange={(e) => setRole(e.target.value)} placeholder="Contoh: Analis data" aria-invalid={tried && !!errs.role} />
        {err('role')}
      </label>
      <label className="field">
        <span>Tim</span>
        <select aria-invalid={tried && !!errs.team} value={newTeam ? NEW : team} onChange={(e) => (e.target.value === NEW ? (setNewTeam(true), setTeam('')) : (setNewTeam(false), setTeam(e.target.value)))}>
          <option value="" disabled>
            Pilih tim
          </option>
          {teams.map((t) => (
            <option key={t} value={t}>
              {teamLabel(t)}
            </option>
          ))}
          <option value={NEW}>Tim baru…</option>
        </select>
        {newTeam && <input value={team} maxLength={40} onChange={(e) => setTeam(e.target.value)} placeholder="Nama tim baru" aria-label="Nama tim baru" aria-invalid={tried && !!errs.team} />}
        {err('team')}
      </label>
    </div>
  )

  return (
    <Dialog title="Pegawai baru" onClose={onClose} wide>
      <form onSubmit={(e) => void submit(e)} className="dlg-body" noValidate>
        <div className="seg" role="tablist" aria-label="Cara membuat pegawai">
          {(['template', 'custom'] as const).map((t) => (
            <button key={t} type="button" role="tab" aria-selected={tab === t} disabled={busy} onClick={() => { setTab(t); setProblem(null) }}>
              {t === 'template' ? 'Dari template' : 'Buat sendiri'}
            </button>
          ))}
        </div>

        {tab === 'template' ? (
          <>
            {tplState === 'loading' && <p className="quiet state">Memuat template...</p>}
            {tplState === 'error' && <ErrorLine text={tplError} onRetry={loadTpls} />}
            {tplState === 'ok' && tpls.length === 0 && <p className="quiet state">Belum ada template.</p>}
            <ul className="tpl-grid">
              {tpls.map((t) => (
                <li key={t.id}>
                  <button type="button" className="tpl" aria-pressed={t.id === tpl} disabled={busy} onClick={() => pickTemplate(t)} style={{ ['--bot' as string]: botColor(t) }}>
                    <BotAvatar bot={t} size={36} />
                    <b>{t.name}</b>
                    <span>{roleLabel(t.role)}</span>
                    <small>{t.description}</small>
                  </button>
                </li>
              ))}
            </ul>
            {selected && <fieldset disabled={busy}>{form}</fieldset>}
          </>
        ) : (
          <fieldset disabled={busy}>
            {form}
            <div className="field">
              <span id="color-l">Warna <Opt /></span>
              <div className="swatches" role="radiogroup" aria-labelledby="color-l">
                {Object.entries(COLORS).map(([c, hex]) => (
                  <button key={c} type="button" role="radio" aria-checked={c === color} aria-label={`Warna ${colorLabel(c)}`} className="swatch" style={{ background: hex }} onClick={() => setColor(c)} />
                ))}
              </div>
            </div>
            <label className="field">
              <span>Tugas dan gaya bicara</span>
              <textarea value={persona} maxLength={2000} rows={6} onChange={(e) => setPersona(e.target.value)} placeholder="Contoh: Kamu admin toko online saya. Jawab pelanggan dengan sopan dan singkat." aria-invalid={tried && !!errs.persona} />
              {err('persona')}
              <small className="counter num">{persona.length} / 2.000</small>
            </label>
          </fieldset>
        )}

        <ProblemLine p={problem} onPlan={() => setDialog({ kind: 'plan' })} />
        {busy && (
          <div className="progress" role="status">
            <span className="bar-ind" aria-hidden="true" />
            Membuat pegawai… bisa sampai 40 detik
          </div>
        )}
        <footer className="dlg-foot">
          <button type="button" className="btn quiet-btn" onClick={onClose} disabled={busy}>
            Batal
          </button>
          <button type="submit" className="btn primary" disabled={busy || (tab === 'template' && !selected)}>
            Buat pegawai
          </button>
        </footer>
      </form>
    </Dialog>
  )
}

// ---------- Grup baru / Atur anggota ----------
function GroupDialog({ id, onClose }: { id?: string; onClose: () => void }) {
  const { bots, groups, refreshGroups, refreshMe, setDialog } = useData()
  const existing = groups.find((g) => g.id === id)
  const [name, setName] = useState(existing?.name ?? '')
  const [picked, setPicked] = useState<string[]>(existing?.members ?? [])
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<Problem>(null)
  const [tried, setTried] = useState(false)
  const byTeam = bots.reduce<Record<string, Bot[]>>((acc, b) => ((acc[b.team] ??= []).push(b), acc), {})
  const teamsPicked = new Set(bots.filter((b) => picked.includes(b.id)).map((b) => b.team))
  const ok = name.trim().length > 0 && picked.length >= 2 && picked.length <= 6

  const toggle = (bid: string) => setPicked((p) => (p.includes(bid) ? p.filter((x) => x !== bid) : p.length < 6 ? [...p, bid] : p))

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setTried(true)
    if (!ok) return
    setBusy(true)
    setProblem(null)
    try {
      const g = id ? await api.patchGroup(id, { name: name.trim(), bot_ids: picked }) : await api.createGroup(name.trim(), picked)
      await refreshGroups().catch(() => [])
      refreshMe()
      onClose()
      go(groupPath(g.id || id || ''))
    } catch (err) {
      setProblem(problemOf(err))
      setBusy(false)
    }
  }

  return (
    <Dialog title={id ? 'Atur anggota' : 'Tim baru'} onClose={onClose}>
      <form onSubmit={(e) => void submit(e)} className="dlg-body" noValidate>
        <fieldset disabled={busy}>
          <label className="field">
            <span>Nama tim</span>
            <input value={name} maxLength={60} onChange={(e) => setName(e.target.value)} placeholder="Contoh: Kampanye Desember" aria-invalid={tried && !name.trim()} />
            {tried && !name.trim() && <small className="err" role="alert">Nama tim wajib diisi.</small>}
          </label>
          <div className="field">
            <span className="field-row">
              <span>Anggota</span>
              <small className="counter num" aria-live="polite">
                {picked.length} / 6 dipilih, minimal 2
              </small>
            </span>
            {bots.length === 0 && <p className="quiet state">Belum ada pegawai. Buat pegawai dulu.</p>}
            <div className="picker">
              {Object.entries(byTeam).map(([team, list]) => (
                <div key={team} className="picker-team">
                  <h3>{teamLabel(team)}</h3>
                  {list.map((b) => {
                    const on = picked.includes(b.id)
                    return (
                      <label key={b.id} className="pick-row" data-on={on || undefined}>
                        <input type="checkbox" checked={on} disabled={!on && picked.length >= 6} onChange={() => toggle(b.id)} />
                        <BotAvatar bot={b} size={28} />
                        <span className="bot-text">
                          <b>{b.name}</b>
                          <small>{roleLabel(b.role)}</small>
                        </span>
                      </label>
                    )
                  })}
                </div>
              ))}
            </div>
            {tried && picked.length < 2 && <small className="err" role="alert">Pilih minimal 2 anggota.</small>}
            {teamsPicked.size > 1 && <p className="note-line">Anggota dari beberapa tim</p>}
          </div>
        </fieldset>
        <ProblemLine p={problem} onPlan={() => setDialog({ kind: 'plan' })} />
        <footer className="dlg-foot">
          <button type="button" className="btn quiet-btn" onClick={onClose} disabled={busy}>
            Batal
          </button>
          <button type="submit" className="btn primary" disabled={busy}>
            {busy ? 'Menyimpan...' : id ? 'Simpan' : 'Buat tim'}
          </button>
        </footer>
      </form>
    </Dialog>
  )
}

// ---------- Paket ----------
function PlanDialog({ onClose }: { onClose: () => void }) {
  const { me, refreshMe } = useData()
  const [plans, setPlans] = useState<Plan[]>([])
  const [state, setState] = useState<'loading' | 'ok' | 'error'>('loading')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')
  const [problem, setProblem] = useState<Problem>(null)

  function load() {
    setState('loading')
    api.plans().then(
      (p) => {
        setPlans(p)
        setState('ok')
      },
      (e) => {
        setError(errText(e))
        setState('error')
      },
    )
  }
  useEffect(load, [])

  async function choose(p: Plan) {
    setBusy(p.id)
    setProblem(null)
    try {
      await api.setPlan(p.id)
      refreshMe()
    } catch (e) {
      setProblem(problemOf(e))
    } finally {
      setBusy('')
    }
  }

  return (
    <Dialog title="Paket" onClose={onClose} wide>
      <div className="dlg-body">
        <p className="quiet">Ganti paket untuk mencoba batasnya. Ini mode demo.</p>
        {state === 'loading' && <p className="quiet state">Memuat paket...</p>}
        {state === 'error' && <ErrorLine text={error} onRetry={load} />}
        {state === 'ok' && plans.length === 0 && <p className="quiet state">Belum ada paket.</p>}
        <ul className="plan-grid">
          {plans.map((p) => {
            const current = me?.plan.id === p.id
            return (
              <li key={p.id} className="plan" data-current={current || undefined}>
                <h3>{p.name}</h3>
                {p.price && <p className="plan-price">{p.price}</p>}
                <ul className="plan-limits num">
                  <li>{p.monthly_usd === null ? 'Biaya tanpa batas' : `Batas biaya ${p.monthly_usd.label} per bulan`}</li>
                  <li>{p.max_bots} pegawai</li>
                  <li>{p.max_groups} tim</li>
                  <li>{p.max_concurrent_runs} tugas berjalan bersamaan</li>
                </ul>
                {current ? (
                  <p className="pill ok">Paket Anda</p>
                ) : (
                  <button className="btn soft" disabled={!!busy} onClick={() => void choose(p)}>
                    {busy === p.id ? 'Mengganti...' : 'Coba paket ini'}
                  </button>
                )}
              </li>
            )
          })}
        </ul>
        <ProblemLine p={problem} onPlan={() => {}} />
        <p className="note-line">Pembayaran belum tersedia</p>
      </div>
    </Dialog>
  )
}

// ---------- Hapus bot ----------
function DeleteBotDialog({ bot, onClose }: { bot: Bot; onClose: () => void }) {
  const { refreshBots, refreshGroups, refreshMe, flash } = useData()
  const admin = useAdminMode()
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<Problem>(null)
  async function remove() {
    setBusy(true)
    setProblem(null)
    try {
      await api.deleteBot(bot.id)
      await Promise.all([refreshBots(), refreshGroups()]).catch(() => [])
      refreshMe()
      onClose()
      const r = parse(location.hash)
      flash(`Pegawai ${bot.name} dihapus`)
      if ((r.name === 'bot' || r.name === 'agen-detail' || r.name === 'agen-ubah') && r.id === bot.id) go(admin ? '/agen' : '/')
    } catch (e) {
      setProblem(problemOf(e))
      setBusy(false)
    }
  }
  return (
    <Dialog title={`Hapus ${bot.name}?`} onClose={onClose}>
      <div className="dlg-body">
        <p>
          {bot.name} dihapus dari daftar pegawai dan dari semua tim. Semua percakapan dengan {bot.name} ikut hilang. Dokumen di Pengetahuan tidak terhapus. Pegawai yang sedang bekerja tidak bisa dihapus; tunggu sampai selesai.
        </p>
        <ProblemLine p={problem} onPlan={() => {}} />
        <footer className="dlg-foot">
          <button className="btn quiet-btn" onClick={onClose} disabled={busy}>
            Batal
          </button>
          <button className="btn danger" onClick={() => void remove()} disabled={busy}>
            {busy ? 'Menghapus...' : 'Hapus pegawai'}
          </button>
        </footer>
      </div>
    </Dialog>
  )
}

// ---------- Atur agen (for users: name, task, model tier) ----------
function EditBotDialog({ bot, onClose }: { bot: Bot; onClose: () => void }) {
  const { refreshBots, setBot, flash } = useData()
  const admin = useAdminMode()
  const [d, setD] = useState<BotDetail | null>(null)
  const [cat, setCat] = useState<ModelCatalog | null>(null)
  const [catDone, setCatDone] = useState(false) // the catalog call finished, successfully or not
  const [loadErr, setLoadErr] = useState('')
  const [name, setName] = useState(bot.name)
  const [persona, setPersona] = useState('')
  const [color, setColor] = useState(bot.color || 'plain')
  const [model, setModel] = useState(modelKey(bot.provider, bot.model)) // '' = Ikuti bawaan
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const [tried, setTried] = useState(false)

  function load() {
    setLoadErr('')
    api.bot(bot.id).then(
      (x) => {
        setD(x)
        setPersona(x.persona)
        setColor(x.color || 'plain')
      },
      (e) => setLoadErr(errText(e)),
    )
    // without the list the tiers stay empty and the dialog says so, instead of promising a choice it cannot offer
    api.models().then(
      (x) => {
        setCat(x)
        setCatDone(true)
      },
      () => setCatDone(true),
    )
  }
  useEffect(load, [bot.id])

  const tiers = tiersFrom(cat)
  // FE-4: when the catalog offers no tier, the dialog must say that plainly instead of promising the choice.
  const tierOff = catDone && TIERS.every((t) => !tiers[t.id].length)
  const cur = bot.model ? tierOf(bot.model) : null
  const curTier = cur ? TIERS.find((t) => t.id === cur)?.label ?? '' : ''
  // Picking a tier keeps the current model when it already belongs to it, else takes the middle model of the tier.
  const pick = (t: TierId) => setModel(cur === t && modelKey(bot.provider, bot.model) ? modelKey(bot.provider, bot.model) : tiers[t][Math.floor(tiers[t].length / 2)] ?? '')
  const selTier = model ? tierOf(splitModel(model).model ?? '') : ''
  const nameErr = tried && !name.trim() ? 'Isi nama pegawai.' : ''

  async function save(e: React.FormEvent) {
    e.preventDefault()
    setTried(true)
    if (!d || !name.trim()) return
    const patch: Record<string, string | null> = {}
    // built-in agents: the BFF only accepts run settings (model), so name and task are not sent
    if (!bot.builtin && name.trim() !== d.name.trim()) patch.name = name.trim()
    if (!bot.builtin && persona.trim() !== d.persona.trim()) patch.persona = persona.trim()
    if (color !== (d.color || 'plain')) patch.color = color
    if (model !== modelKey(d.provider, d.model)) Object.assign(patch, splitModel(model))
    if (!Object.keys(patch).length) return onClose()
    setBusy(true)
    setProblem('')
    try {
      const saved = await api.updateBot(bot.id, patch)
      setBot(saved) // the detail view reads this list, so its card and avatar change without a reload
      await refreshBots().catch(() => [])
      flash(`${name.trim()} disimpan`)
      onClose()
    } catch (err) {
      setProblem(errText(err))
      setBusy(false)
    }
  }

  return (
    <Dialog title={`Atur ${bot.name}`} onClose={onClose}>
      <form className="dlg-body" onSubmit={(e) => void save(e)} noValidate>
        {loadErr && <ErrorLine text={loadErr} onRetry={load} />}
        {!d && !loadErr && <p className="quiet">Memuat...</p>}
        {d && (
          <fieldset disabled={busy} className="form-page">
            {bot.builtin && (
              <p className="quiet">
                Pegawai bawaan: nama dan tugasnya diatur sistem.
                {tierOff ? ' Anda bisa mengubah warnanya.' : ' Anda bisa mengubah warna dan tingkat ketelitiannya.'}
              </p>
            )}
            {!bot.builtin && <>
            <label className="field">
              <span>Nama</span>
              <input value={name} maxLength={40} aria-invalid={!!nameErr} onChange={(e) => setName(e.target.value)} />
              {nameErr && <small className="err" role="alert">{nameErr}</small>}
            </label>
            <label className="field">
              <span>Tugas dan gaya bicara</span>
              <textarea
                value={persona}
                rows={6}
                maxLength={2000}
                placeholder="Contoh: Kamu adalah admin toko online saya. Jawab pelanggan dengan sopan dan singkat, pakai bahasa Indonesia santai."
                onChange={(e) => setPersona(e.target.value)}
              />
              <small className="counter num">{persona.length} / 2.000</small>
            </label>
            </>}
            <div className="field">
              <span id="ec-l">Warna: {colorLabel(color)}</span>
              <div className="swatches" role="radiogroup" aria-labelledby="ec-l">
                {[['plain', 'var(--raised)'] as const, ...Object.entries(COLORS)].map(([c, hex]) => (
                  <button key={c} type="button" role="radio" aria-checked={c === color} aria-label={`Warna ${colorLabel(c)}`} className="swatch" style={{ background: hex }} onClick={() => setColor(c)} />
                ))}
              </div>
            </div>
            <div className="field" role={tierOff ? undefined : 'radiogroup'} aria-label={tierOff ? undefined : 'Tingkat ketelitian'}>
              <span>Tingkat ketelitian</span>
              {tierOff ? (
                <p className="quiet">
                  Pilihan tingkat ketelitian belum tersedia saat ini, jadi {bot.name} {curTier ? `tetap memakai ${curTier}.` : 'memakai pilihan standar sistem.'}
                </p>
              ) : (
                <>
                  <label className="radio-row">
                    <input type="radio" name="tier" checked={model === ''} onChange={() => setModel('')} />
                    <span>
                      <b>Ikuti bawaan</b>
                      <small className="quiet"> Memakai pilihan standar sistem.{admin && cat?.default.model ? ` (${cat.default.model})` : ''}</small>
                    </span>
                  </label>
                  {TIERS.map((t) => {
                    const off = !tiers[t.id].length && selTier !== t.id
                    return (
                      <label key={t.id} className="radio-row" aria-disabled={off || undefined}>
                        <input type="radio" name="tier" checked={selTier === t.id} disabled={off} onChange={() => pick(t.id)} />
                        <span>
                          <b>{t.label}</b>
                          <small className="quiet"> {t.hint}{admin && selTier === t.id ? ` Model: ${splitModel(model).model}` : ''}</small>
                        </span>
                      </label>
                    )
                  })}
                </>
              )}
            </div>
            <small className="quiet">Perubahan berlaku mulai tugas berikutnya. Percakapan lama tidak berubah.</small>
          </fieldset>
        )}
        {problem && <p className="problem-bar" role="alert">{problem}</p>}
        <footer className="dlg-foot">
          <button type="button" className="btn quiet-btn" onClick={onClose} disabled={busy}>
            Batal
          </button>
          <button type="submit" className="btn primary" disabled={busy || !d}>
            {busy ? 'Menyimpan...' : 'Simpan'}
          </button>
        </footer>
      </form>
    </Dialog>
  )
}
