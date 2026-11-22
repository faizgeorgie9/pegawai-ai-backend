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
  const left = steps.filter((s) => !s.done).length
  if (closed || left === 0) return null
  const next = steps.find((s) => !s.done && !s.optional) ?? steps.find((s) => !s.done)
  return (
    <section className="panel-card onboard" aria-labelledby="onb-h">
      <header className="onb-head">
        <div>
          <h2 id="onb-h">Mulai dari sini</h2>
          <p className="quiet small">
            <span className="num">{steps.length - left}</span> dari <span className="num">{steps.length}</span> langkah selesai.
          </p>
        </div>
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
      </header>
      <ol className="onb-list">
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
    </section>
  )
}
