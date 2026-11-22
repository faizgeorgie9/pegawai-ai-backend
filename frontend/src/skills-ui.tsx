import { useCallback, useState } from 'react'
import { api, errText } from './bff'
import type { AgentSkills as AgentSkillsData, Skill } from './bff'
import { useAdminMode } from './adminMode'
import { Dialog, ErrorLine } from './ui'
import { Loading, toolsetText, useLoad } from './ui-extra'

const clean = (s: string) => s.replace(/^[^\p{L}\p{N}]+/u, '').trim()
export const skillText = (s: Pick<Skill, 'name' | 'label' | 'description'>) => toolsetText(s.name, clean(s.label), s.description)

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

// Agent detail: this agent's skills as switches.
export function AgentSkills({ slug }: { slug: string }) {
  const fn = useCallback(() => api.agentSkills(slug), [slug])
  const r = useLoad(fn)
  const [local, setLocal] = useState<Skill[] | null>(null)
  if (r.state === 'loading') return <Loading text="Memuat keahlian..." shape="lines" />
  if (r.state === 'error' || !r.data) return <ErrorLine text="Daftar keahlian belum bisa dimuat. Coba lagi sebentar." onRetry={r.retry} />
  return <SkillSwitches slug={slug} skills={local ?? r.data} onChange={setLocal} />
}

// Aplikasi page: "Keahlian pegawai". One card per skill, who uses it, and "Atur" for the per-agent switches.
export function SkillsSection({ q = '' }: { q?: string }) {
  const admin = useAdminMode()
  const fn = useCallback(() => api.skillsAll(), [])
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
        <h2 id="g-skills">Keahlian pegawai</h2>
        <p className="quiet small">Kemampuan bawaan yang bisa dinyalakan atau dimatikan untuk tiap pegawai.</p>
      </header>
      {r.state === 'loading' && !r.data && <Loading text="Memuat keahlian..." shape="ledger" />}
      {r.state === 'error' && !r.data && <ErrorLine text="Daftar keahlian belum bisa dimuat. Coba lagi sebentar." onRetry={r.retry} />}
      {names.size > 0 && (
        <ul className="app-grid">
          {[...names.values()].map((s) => {
            const [label, text] = skillText(s)
            const who = users(s.name)
            return (
              <li key={s.name} className="app-card skill-card" data-skill={s.name}>
                <div className="app-top">
                  <h3>{label}</h3>
                </div>
                <p>{text}</p>
                <p className="quiet small">{who.length ? `Dipakai: ${who.join(', ')}` : 'Belum dipakai pegawai mana pun.'}</p>
                <div className="app-card-act">
                  <button type="button" className="btn soft" onClick={() => setOpen(s.name)}>
                    Atur
                  </button>
                </div>
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
