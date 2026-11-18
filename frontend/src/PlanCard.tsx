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

type PlanState = Pick<ContentPlan, 'task_id' | 'state'>

// Approval card inside the group chat: one decision for the whole bundle. After approval the Writer and Visual run on their days.
// The state is the plan's real state on the board; it refreshes with the chat (shortcut: a change made on the board shows after a reload).
export function PlanCard({ groupId, messageId, plan, onState }: { groupId: string; messageId: string; plan: ContentPlan; onState: (s: PlanState) => void }) {
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const [revising, setRevising] = useState(false)
  const [feedback, setFeedback] = useState('')
  const [revised, setRevised] = useState(false)
  const [cancelling, setCancelling] = useState(false)

  async function approve() {
    setBusy(true)
    setProblem('')
    try {
      onState(await api.approvePlan(groupId, messageId))
    } catch (e) {
      setProblem(errText(e))
    } finally {
      setBusy(false)
    }
  }
  async function cancel() {
    setBusy(true)
    setProblem('')
    try {
      onState(await api.cancelPlan(groupId, messageId))
      setCancelling(false)
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

  const closed = plan.state === 'cancelled' || plan.state === 'replaced'
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
      {closed ? (
        <p className="plan-done">
          <b>{plan.state === 'replaced' ? 'Sudah diganti rencana yang lebih baru.' : 'Rencana dibatalkan.'}</b>
        </p>
      ) : plan.state === 'approved' ? (
        <p className="plan-done">
          <b>Disetujui · terjadwal.</b> <a href="#/kanban">Lihat di papan tugas</a>
        </p>
      ) : revised ? (
        <p className="plan-done">Catatan revisi terkirim ke tim. Rencana baru akan muncul di sini.</p>
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
            {!revising && (
              <button className="btn link" disabled={busy} onClick={() => setCancelling(true)}>
                Batalkan
              </button>
            )}
          </div>
        </>
      )}
      {!closed && plan.state === 'approved' && !cancelling && (
        <div className="approval-actions">
          <button className="btn link" disabled={busy} onClick={() => setCancelling(true)}>
            Batalkan rencana
          </button>
        </div>
      )}
      {cancelling && !closed && (
        <div className="approval-actions">
          <span className="small">Batalkan rencana ini? Hari yang belum selesai tidak akan dikerjakan.</span>
          <button className="btn stop sm" disabled={busy} onClick={() => void cancel()}>
            Ya, batalkan
          </button>
          <button className="btn link sm" disabled={busy} onClick={() => setCancelling(false)}>
            Tidak
          </button>
        </div>
      )}
      {problem && (
        <p className="plan-problem" role="alert">
          {problem}
        </p>
      )}
    </div>
  )
}
