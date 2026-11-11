import { useEffect, useState } from 'react'
import type { ToolChip } from './bff'
import { toolLabel } from './steps'
import { useSmoothText } from './useSmoothText'
import { I, Icon } from './ui'

// Live step list while a run works: one step per tool event, "Berpikir" while nothing else is running, "Menulis jawaban" once
// text arrives. When the run ends it folds into one quiet line ("3 langkah · 14 dtk") that expands again.
// `since`: run start (ms); without it the clock starts when this mounts.
export function LiveSteps({ tools, running, writing, since, seconds }: { tools: ToolChip[]; running: boolean; writing: boolean; since?: number; seconds?: number }) {
  const [t0] = useState(() => since ?? Date.now())
  const [end, setEnd] = useState<number | null>(null)
  const [open, setOpen] = useState(false)
  const [ran] = useState(running)
  useEffect(() => {
    if (!running) setEnd((e) => e ?? Date.now())
    else setEnd(null)
  }, [running])

  const toolBusy = tools.some((t) => t.status === 'run')
  const rows: { id: string; label: string; s: 'run' | 'done' | 'bad'; title?: string }[] = tools.map((t) => ({ id: t.id, label: toolLabel(t.tool), s: t.status, title: t.preview }))
  if (running && writing) rows.push({ id: 'write', label: 'Menulis jawaban', s: 'run' })
  else if (running && !toolBusy) rows.push({ id: 'think', label: 'Berpikir', s: 'run' })

  if (running) {
    if (!rows.length) return null
    return (
      <ul className="steps" aria-label="Langkah agen">
        {rows.map((r) => (
          <Step key={r.id} {...r} />
        ))}
      </ul>
    )
  }
  if (!tools.length) return null
  const sec = seconds ?? (ran && end !== null ? Math.round((end - t0) / 1000) : undefined) // only a run watched live has a duration
  const head = `${tools.length} langkah${sec !== undefined ? ` · ${sec} dtk` : ''}`
  return (
    <div className="steps-done">
      <button type="button" className="steps-toggle" aria-expanded={open} onClick={() => setOpen(!open)}>
        <span className="num">{head}</span>
        <span className="thinking-chev" aria-hidden="true">
          <Icon d="M6 9l6 6 6-6" size={14} />
        </span>
      </button>
      {open && (
        <ul className="steps" aria-label="Langkah agen">
          {rows.map((r) => (
            <Step key={r.id} {...r} />
          ))}
        </ul>
      )}
    </div>
  )
}

function Step({ label, s, title }: { label: string; s: 'run' | 'done' | 'bad'; title?: string }) {
  return (
    <li className="step" data-s={s} title={title}>
      <span className="step-mark" aria-hidden="true">
        {s === 'done' ? <Icon d={I.check} size={12} /> : <span className="dot" />}
      </span>
      <span className="step-label">{label}</span>
      {s === 'bad' && <span className="step-note">gagal</span>}
      <span className="sr">{s === 'run' ? ', berjalan' : s === 'bad' ? ', gagal' : ', selesai'}</span>
    </li>
  )
}

// A draft that is still being written: revealed smoothly, with a caret. `label` is the small line above it.
export function LiveDraft({ text, label }: { text: string; label?: string }) {
  const { text: shown, caret } = useSmoothText(text, true)
  return (
    <div className="cs-msg">
      {label && <p className="quiet small">{label}</p>}
      <p className="draft-text" data-caret={caret || undefined}>{shown}</p>
    </div>
  )
}
