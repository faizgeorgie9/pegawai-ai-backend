import { useCallback, useState } from 'react'
import { api, errText } from './bff'
import type { AgentSkills as AgentSkillsData, Skill } from './bff'
import { useAdminMode, useIsAdmin } from './adminMode'
import { Dialog, ErrorLine } from './ui'
import { Loading, toolsetText, useLoad } from './ui-extra'
import { cachedRead, forgetReads } from './session-cache'
import { CustomSkills } from './custom-skills'

const clean = (s: string) => s.replace(/^[^\p{L}\p{N}]+/u, '').trim()
export const skillText = (s: Pick<Skill, 'name' | 'label' | 'description'>) => toolsetText(s.name, clean(s.label), s.description)

// The BFF asks the gateway for every agent's toolsets, which takes seconds. The tab reads it through
// `cachedRead('skills')` (one read per minute, shared with the agent screens), so switching back and forth
// never fetches twice. This starts that same read while the pointer or keyboard focus is still on the tab.
export const primeSkills = () => void cachedRead('skills', () => api.skillsAll()).catch(() => {})

// One switch per skill of one agent. The BFF answers with the real state after each change (it never trusts the click).
export function SkillSwitches({ slug, skills, onChange }: { slug: string; skills: Skill[]; onChange: (s: Skill[]) => void }) {
  const admin = useAdminMode()
  const [busy, setBusy] = useState('')
  const [problem, setProblem] = useState('')
  async function flip(s: Skill, on: boolean) {
    setBusy(s.name)
    setProblem('')
    try {
      onChange(await api.setSkill(slug, s.name, on))
      forgetReads('skills') // a reopened Keahlian tab asks the BFF again instead of showing the old switches
    } catch (e) {
      setProblem(errText(e))
    }
    setBusy('')
  }
  const shown = skills.filter((s) => admin || !s.technical)
  return (
    <div className="skill-sw">
      {problem && (
        <p className="problem-bar" role="alert">
          {problem}
        </p>
      )}
      <ul className="skill-list">
        {shown.map((s) => {
          const [label, text] = skillText(s)
          return (
            <li key={s.name}>
              <label className="skill-row">
                <span className="skill-txt">
                  <b>{label}</b>
                  <span className="quiet small">{text}</span>
                  {admin && <code className="small">{s.name}</code>}
                </span>
                <input type="checkbox" role="switch" className="tgl" checked={s.enabled} disabled={busy === s.name} onChange={(e) => void flip(s, e.target.checked)} aria-label={label} />
              </label>
              {s.name === 'memory' && !s.enabled && <p className="quiet small skill-note">Ingatan dimatikan. Hal yang sudah diingat tetap tersimpan.</p>}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

// Agent detail: this agent's skills as switches, then the owner's own written instructions.
export function AgentSkills({ slug }: { slug: string }) {
  const canEdit = useIsAdmin()
  const fn = useCallback(() => api.agentSkills(slug), [slug])
  const r = useLoad(fn)
  const [local, setLocal] = useState<Skill[] | null>(null)
  if (r.state === 'loading') return <Loading text="Memuat keahlian..." shape="lines" />
  if (r.state === 'error' || !r.data) return <ErrorLine text="Daftar keahlian belum bisa dimuat. Coba lagi sebentar." onRetry={r.retry} />
  return (
    <>
      <SkillSwitches slug={slug} skills={local ?? r.data} onChange={setLocal} />
      <CustomSkills slug={slug} canEdit={canEdit} />
    </>
  )
}

// Card shapes of the loaded grid; the third line is the "Dipakai" line, so the grid height does not jump.
function SkillsSkeleton() {
  return (
    <div className="skel skel-skills" role="status" aria-busy="true">
      <span className="sr">Memuat keahlian pegawai…</span>
      <div className="skel-body" aria-hidden="true">
        <ul className="app-grid app-mini-grid">
          {Array.from({ length: 12 }, (_, i) => (
            <li key={i} className="app-card app-mini skel-skill-card">
              <span className="skel-head">
                <i className="skel-bar w40" />
              </span>
              <i className="skel-btn sm" />
              <span className="skel-desc">
                <i className="skel-bar w70 thin" />
                <i className="skel-bar w40 thin" />
              </span>
              <span className="skel-who">
                <i className="skel-bar w60 thin" />
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

// Aplikasi page: "Keahlian pegawai". One card per skill, who uses it, and "Atur" for the per-agent switches.
export function SkillsSection({ q = '' }: { q?: string }) {
  const admin = useAdminMode()
  const fn = useCallback(() => cachedRead('skills', () => api.skillsAll()), [])
  const r = useLoad(fn)
  const [agents, setAgents] = useState<AgentSkillsData[] | null>(null)
  const [open, setOpen] = useState<string | null>(null)
  const data = agents ?? r.data?.agents ?? []
  const names = new Map<string, Skill>()
  for (const a of data) for (const s of a.skills) if ((admin || !s.technical) && skillText(s).join(' ').toLowerCase().includes(q.trim().toLowerCase())) names.set(s.name, s)
  const users = (name: string) => data.filter((a) => a.skills.some((s) => s.name === name && s.enabled)).map((a) => a.name)
  const current = open ? names.get(open) : undefined

  return (
    <section className="apps-group" aria-labelledby="g-skills">
      <header>
        <h2 id="g-skills" className="sr">
          Keahlian pegawai
        </h2>
        <p className="quiet small">
          Kemampuan bawaan yang bisa dinyalakan atau dimatikan untuk tiap pegawai.
          {r.state === 'loading' && !r.data && (
            <span className="slow-note" aria-hidden="true">
              {' '}
              Sedang memuat daftar keahlian…
            </span>
          )}
        </p>
      </header>
      {r.state === 'loading' && !r.data && <SkillsSkeleton />}
      {r.state === 'error' && !r.data && <ErrorLine text="Daftar keahlian belum bisa dimuat. Coba lagi sebentar." onRetry={r.retry} />}
      {names.size > 0 && (
        <ul className="app-grid app-mini-grid">
          {[...names.values()].map((s) => {
            const [label, text] = skillText(s)
            const who = users(s.name)
            return (
              <li key={s.name} className="app-card skill-card app-mini" data-skill={s.name}>
                <div className="app-card-head">
                  <div className="app-top">
                    <h3>{label}</h3>
                  </div>
                </div>
                <div className="app-card-act">
                  <button type="button" className="btn soft sm" onClick={() => setOpen(s.name)} aria-label={`Atur ${label}`}>
                    Atur
                  </button>
                </div>
                <p>{text}</p>
                <p className="quiet small" title={who.join(', ')}>
                  {who.length ? `Dipakai: ${who.slice(0, 2).join(', ')}${who.length > 2 ? ` +${who.length - 2}` : ''}` : 'Belum dipakai pegawai mana pun.'}
                </p>
              </li>
            )
          })}
        </ul>
      )}
      {r.data && names.size === 0 && <p className="quiet">Tidak ada keahlian yang cocok dengan pencarian Anda.</p>}
      {current && (
        <Dialog title={skillText(current)[0]} onClose={() => setOpen(null)}>
         <div className="dlg-body">
          <p className="quiet">{skillText(current)[1]} Pilih pegawai yang boleh memakainya.</p>
          {current.name === 'memory' && data.every((a) => a.skills.find((s) => s.name === 'memory')?.enabled === false) && (
            <p className="quiet small skill-note">Ingatan dimatikan. Hal yang sudah diingat tetap tersimpan.</p>
          )}
          <ul className="skill-list">
            {data.map((a) => (
              <AgentRow key={a.id} agent={a} name={current.name} label={skillText(current)[0]} onChange={(skills) => setAgents(data.map((x) => (x.id === a.id ? { ...x, skills } : x)))} />
            ))}
          </ul>
         </div>
        </Dialog>
      )}
    </section>
  )
}

function AgentRow({ agent, name, label, onChange }: { agent: AgentSkillsData; name: string; label: string; onChange: (s: Skill[]) => void }) {
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const on = agent.skills.find((s) => s.name === name)?.enabled === true
  async function flip(v: boolean) {
    setBusy(true)
    setProblem('')
    try {
      onChange(await api.setSkill(agent.id, name, v))
    } catch (e) {
      setProblem(errText(e))
    }
    setBusy(false)
  }
  return (
    <li>
      <label className="skill-row">
        <span className="skill-txt">
          <b>{agent.name}</b>
          {!agent.ok && <span className="quiet small">Pegawai belum bisa dihubungi.</span>}
          {problem && <span className="connect-warn small">{problem}</span>}
        </span>
        <input type="checkbox" role="switch" className="tgl" checked={on} disabled={busy || !agent.ok} onChange={(e) => void flip(e.target.checked)} aria-label={`${label} untuk ${agent.name}`} />
      </label>
    </li>
  )
}
