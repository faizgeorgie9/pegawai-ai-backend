import { useState } from 'react'
import { CLOSE, Icon, I } from './ui'

// Checklist card on Beranda until every step is done or the user closes it ("ditutup" is remembered in this browser).
const CLOSED = 'pa.onboarding.closed'
const NAMED = 'pa.onboarding.named'
export const DEFAULT_NAME = 'Colorbox'

const read = (k: string) => {
  try {
    return localStorage.getItem(k) === '1'
  } catch {
    return false
  }
}
const write = (k: string) => {
  try {
    localStorage.setItem(k, '1')
  } catch {
    /* not remembered */
  }
}

// shortcut: the server starts every workspace as "Colorbox", so that name counts as "not filled" unless the user saved it once here;
// upgrade when the BFF tells whether the name was ever set.
export const markNamed = () => write(NAMED)
export const hasName = (name: string) => (name.trim() !== '' && name.trim() !== DEFAULT_NAME) || read(NAMED)
// The page draws a same-height stand-in while the steps are still loading, unless the user closed the guide.
export const onboardingClosed = () => read(CLOSED)

export interface Step {
  id: string
  title: string
  hint: string
  done: boolean
  href: string
  action: string
  optional?: boolean
}

export function Onboarding({ steps }: { steps: Step[] }) {
  const [closed, setClosed] = useState(() => read(CLOSED))
  const [open, setOpen] = useState(false)
  const left = steps.filter((s) => !s.done).length
  if (closed || left === 0) return null
  const done = steps.length - left
  const next = steps.find((s) => !s.done && !s.optional) ?? steps.find((s) => !s.done)!
  return (
    <section className="panel-card onboard onboard-row" aria-labelledby="onb-h">
      <div className="onb-bar">
        <span className="onb-ring num" aria-hidden="true">
          {done}/{steps.length}
        </span>
        <div className="onb-text">
          <h2 id="onb-h" className="onb-kicker">
            Mulai dari sini · {done} dari {steps.length} langkah selesai
          </h2>
          <b>{next.title}</b>
        </div>
        <span className="onb-ctrl">
          {!open && (
            <a className="btn sm primary" href={next.href}>
              {next.action}
            </a>
          )}
          <button type="button" className="btn link small" aria-expanded={open} aria-controls="onb-list" onClick={() => setOpen((v) => !v)}>
            {open ? 'Sembunyikan langkah' : 'Semua langkah'}
          </button>
          <button
            className="icon-btn"
            aria-label="Tutup panduan awal"
            onClick={() => {
              write(CLOSED)
              setClosed(true)
            }}
          >
            <Icon d={CLOSE} size={16} />
          </button>
        </span>
      </div>
      {open && (
        <ol id="onb-list" className="onb-list">
          {steps.map((s) => (
            <li key={s.id} className="onb-step" data-done={s.done || undefined}>
              <span className="onb-mark" aria-hidden="true">
                {s.done && <Icon d={I.check} size={14} />}
              </span>
              <span className="onb-text">
                <b>
                  {s.title}
                  {s.optional && <em className="req"> (opsional)</em>}
                </b>
                <small>{s.hint}</small>
              </span>
              {s.done ? (
                <span className="sr">Selesai</span>
              ) : (
                <a className={`btn sm ${s === next ? 'primary' : 'outline'}`} href={s.href}>
                  {s.action}
                </a>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
