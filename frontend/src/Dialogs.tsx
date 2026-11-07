import { useEffect, useState } from 'react'
import { ApiError, api, errText } from './bff'
import type { Bot, Plan, Template } from './bff'
import { useData } from './data'
import { botPath, groupPath, go, parse } from './router'
import { BotAvatar, COLORS, Dialog, ErrorLine, botColor, nf, teamLabel } from './ui'
import { Req } from './ui-extra'

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
      flash(`Agen ${b.name} dibuat`)
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
  if (tab === 'custom' && !persona.trim()) errs.persona = 'Persona wajib diisi, supaya agen tahu cara bekerja.'
  const err = (k: string) => tried && errs[k] && <small className="err" role="alert">{errs[k]}</small>
  const form = (
    <div className="fields">
      <label className="field">
        <span>Nama <Req /></span>
        <input value={name} maxLength={40} onChange={(e) => setName(e.target.value)} placeholder="Nama agen baru" aria-invalid={tried && !!errs.name} />
        {err('name')}
      </label>
      <label className="field">
        <span>Peran <Req /></span>
        <input value={role} maxLength={40} onChange={(e) => setRole(e.target.value)} placeholder="Contoh: Analis data" aria-invalid={tried && !!errs.role} />
        {err('role')}
      </label>
      <label className="field">
        <span>Tim <Req /></span>
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
    <Dialog title="Agen baru" onClose={onClose} wide>
      <form onSubmit={(e) => void submit(e)} className="dlg-body" noValidate>
        <div className="seg" role="tablist" aria-label="Cara membuat agen">
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
                    <span>{t.role}</span>
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
              <span id="color-l">Warna</span>
              <div className="swatches" role="radiogroup" aria-labelledby="color-l">
                {Object.entries(COLORS).map(([c, hex]) => (
                  <button key={c} type="button" role="radio" aria-checked={c === color} aria-label={`Warna ${c}`} className="swatch" style={{ background: hex }} onClick={() => setColor(c)} />
                ))}
              </div>
            </div>
            <label className="field">
              <span>Persona <Req /></span>
              <textarea value={persona} maxLength={2000} rows={6} onChange={(e) => setPersona(e.target.value)} placeholder="Jelaskan cara agen bekerja, gaya bahasanya, dan batasannya." aria-invalid={tried && !!errs.persona} />
              <small className="counter num">{persona.length} / 2.000</small>
              {err('persona')}
            </label>
          </fieldset>
        )}

        <ProblemLine p={problem} onPlan={() => setDialog({ kind: 'plan' })} />
        {busy && (
          <div className="progress" role="status">
            <span className="bar-ind" aria-hidden="true" />
            Membuat agen… bisa sampai 40 detik
          </div>
        )}
        <footer className="dlg-foot">
          <button type="button" className="btn quiet-btn" onClick={onClose} disabled={busy}>
            Batal
          </button>
          <button type="submit" className="btn primary" disabled={busy || (tab === 'template' && !selected)}>
            Buat agen
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
    <Dialog title={id ? 'Atur anggota' : 'Grup baru'} onClose={onClose}>
      <form onSubmit={(e) => void submit(e)} className="dlg-body" noValidate>
        <fieldset disabled={busy}>
          <label className="field">
            <span>Nama grup <Req /></span>
            <input value={name} maxLength={60} onChange={(e) => setName(e.target.value)} placeholder="Contoh: Kampanye Desember" aria-invalid={tried && !name.trim()} />
            {tried && !name.trim() && <small className="err" role="alert">Nama grup wajib diisi.</small>}
          </label>
          <div className="field">
            <span className="field-row">
              <span>Anggota <Req /></span>
              <small className="counter num" aria-live="polite">
                {picked.length} / 6 dipilih, minimal 2
              </small>
            </span>
            {bots.length === 0 && <p className="quiet state">Belum ada bot. Buat bot dulu.</p>}
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
                          <small>{b.role}</small>
                        </span>
                      </label>
                    )
                  })}
                </div>
              ))}
            </div>
            {tried && picked.length < 2 && <small className="err" role="alert">Pilih minimal 2 anggota.</small>}
            {teamsPicked.size > 1 && <p className="note-line">Grup lintas tim</p>}
          </div>
        </fieldset>
        <ProblemLine p={problem} onPlan={() => setDialog({ kind: 'plan' })} />
        <footer className="dlg-foot">
          <button type="button" className="btn quiet-btn" onClick={onClose} disabled={busy}>
            Batal
          </button>
          <button type="submit" className="btn primary" disabled={busy}>
            {busy ? 'Menyimpan...' : id ? 'Simpan' : 'Buat grup'}
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
                  <li>{p.monthly_tokens === null ? 'Token tanpa batas' : `${nf.format(p.monthly_tokens)} token per bulan`}</li>
                  <li>{p.max_bots} bot</li>
                  <li>{p.max_groups} grup</li>
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
      flash(`Agen ${bot.name} dihapus`)
      if ((r.name === 'bot' || r.name === 'agen-detail' || r.name === 'agen-ubah') && r.id === bot.id) go('/agen')
    } catch (e) {
      setProblem(problemOf(e))
      setBusy(false)
    }
  }
  return (
    <Dialog title={`Hapus ${bot.name}?`} onClose={onClose}>
      <div className="dlg-body">
        <p>
          {bot.name} dihapus dari daftar agen dan dari semua grup. Riwayat chat dengan {bot.name} tidak bisa dibuka lagi. Agen yang sedang bekerja tidak bisa dihapus.
        </p>
        <ProblemLine p={problem} onPlan={() => {}} />
        <footer className="dlg-foot">
          <button className="btn quiet-btn" onClick={onClose} disabled={busy}>
            Batal
          </button>
          <button className="btn danger" onClick={() => void remove()} disabled={busy}>
            {busy ? 'Menghapus...' : 'Hapus agen'}
          </button>
        </footer>
      </div>
    </Dialog>
  )
}
