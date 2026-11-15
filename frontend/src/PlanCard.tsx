import { useState } from 'react'
import { api, errText } from './bff'
import type { ContentPlan } from './bff'

// The plan block the project manager ends a message with is validated by the BFF; the card replaces it in the chat.
const FENCE = /```(?:json)?\s*\{[\s\S]*?\}\s*```/g
export const withoutPlanBlock = (text: string) => text.replace(FENCE, '').trim()

const dayLabel = (iso: string) => {
  const d = new Date(iso + 'T00:00:00')
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'long' })
}

// Approval card inside the group chat: one decision for the whole bundle. After approval the Writer and Visual run on their days.
export function PlanCard({ groupId, messageId, plan, onApproved }: { groupId: string; messageId: string; plan: ContentPlan; onApproved: (scheduleId: string) => void }) {
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const [revising, setRevising] = useState(false)
  const [feedback, setFeedback] = useState('')
  const [revised, setRevised] = useState(false)

  async function approve() {
    setBusy(true)
    setProblem('')
    try {
      onApproved((await api.approvePlan(groupId, messageId)).id)
    } catch (e) {
      setProblem(errText(e))
    } finally {
      setBusy(false)
    }
  }
  async function revise() {
    const text = feedback.trim()
    if (!text) return
    setBusy(true)
    setProblem('')
    try {
      await api.revisePlan(groupId, messageId, text)
      setRevised(true)
      setRevising(false)
      setFeedback('')
    } catch (e) {
      setProblem(errText(e))
    } finally {
      setBusy(false)
    }
  }

  const approved = plan.schedule_id !== null
  return (
    <div className="approval plan-card" role="group" aria-label="Persetujuan rencana konten">
      <p className="approval-title">
        Rencana konten, {plan.days.length} hari{plan.title ? `: ${plan.title}` : ''}
      </p>
      <ol className="plan-days">
        {plan.days.map((d) => (
          <li key={d.date}>
            <p className="plan-when">
              {dayLabel(d.date)}, {d.time}
            </p>
            <p className="plan-theme">{d.theme}</p>
            {d.products.length > 0 && <p className="plan-products">Produk: {d.products.join(', ')}</p>}
            <p className="plan-brief">{d.brief}</p>
          </li>
        ))}
      </ol>
      {approved ? (
        <p className="plan-done">
          <b>Disetujui · terjadwal.</b> <a href="#/scheduler">Lihat jadwal</a>
        </p>
      ) : revised ? (
        <p className="plan-done">Catatan revisi terkirim ke grup. Rencana baru akan muncul di sini.</p>
      ) : (
        <>
          <p className="plan-note">Setelah disetujui, hanya Writer dan Visual yang bekerja, satu hari satu kali sesuai jadwal.</p>
          {revising && (
            <div className="plan-revise">
              <label className="sr" htmlFor={`rev-${messageId}`}>
                Catatan revisi
              </label>
              <textarea id={`rev-${messageId}`} rows={3} maxLength={3000} value={feedback} onChange={(e) => setFeedback(e.target.value)} placeholder="Apa yang perlu diubah dari rencana ini?" disabled={busy} />
            </div>
          )}
          <div className="approval-actions">
            <button className="btn primary" disabled={busy} onClick={() => void approve()}>
              Setujui rencana
            </button>
            {revising ? (
              <>
                <button className="btn soft" disabled={busy || !feedback.trim()} onClick={() => void revise()}>
                  Kirim revisi
                </button>
                <button className="btn link" disabled={busy} onClick={() => setRevising(false)}>
                  Batal
                </button>
              </>
            ) : (
              <button className="btn soft" disabled={busy} onClick={() => setRevising(true)}>
                Minta revisi
              </button>
            )}
          </div>
        </>
      )}
      {problem && (
        <p className="plan-problem" role="alert">
          {problem}
        </p>
      )}
    </div>
  )
}
