import { useCallback, useEffect, useState } from 'react'
import { api, errText, isSocialAction } from './bff'
import type { PendingAction } from './bff'
import { useData } from './data'
import { PostApprovalCard } from './social-ui'

// Approval cards for risky agent actions (delete a file, send an email): the agent only asks, the user decides here.
// One list for the whole app: the BFF announces every change on the global stream, so every card stays current.
export function useActions(): PendingAction[] {
  const { on } = useData()
  const [items, setItems] = useState<PendingAction[]>([])
  const load = useCallback(() => {
    api.actions().then(setItems, () => undefined) // a failed refresh keeps what is on screen
  }, [])
  useEffect(() => {
    load()
    return on('action', load)
  }, [load, on])
  return items
}

const RECENT = 60 * 60 * 1000 // a decided card stays visible for an hour so the result can be read
const isRecent = (a: PendingAction) => a.status === 'pending' || (!!a.decided_at && Date.now() - new Date(a.decided_at).getTime() < RECENT)

// What to show where: pending ones and just-decided ones. `match` narrows to one chat or team.
export function useVisibleActions(match?: (a: PendingAction) => boolean): PendingAction[] {
  return useActions().filter((a) => isRecent(a) && (!match || match(a)))
}

// An email card shows what is stored for sending (recipients, subject, full body), never the agent's own description of it.
function emailOf(a: PendingAction) {
  if (a.kind !== 'gmail_send' && a.kind !== 'gmail_send_draft') return null
  const p = a.payload
  const rt = p.reply_to as { from?: string; subject?: string } | undefined
  return {
    to: Array.isArray(p.to) ? p.to.join(', ') : String(p.to ?? ''),
    subject: String(p.subject ?? ''),
    body: String(p.body ?? ''),
    reply: rt ? [rt.subject, rt.from && `dari ${rt.from}`].filter(Boolean).join(' ') : '',
  }
}

// A publish request has its own preview and words; every other action keeps the card below.
export function ActionCard({ action }: { action: PendingAction }) {
  if (isSocialAction(action)) return <PostApprovalCard action={action} />
  return <GenericActionCard action={action} />
}

function GenericActionCard({ action }: { action: PendingAction }) {
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const [local, setLocal] = useState<PendingAction | null>(null) // the answer to our own click: final, so it stays
  const a = local ?? action

  async function decide(approve: boolean) {
    setBusy(true)
    setProblem('')
    try {
      setLocal(await (approve ? api.approveAction(a.id) : api.rejectAction(a.id)))
    } catch (e) {
      setProblem(errText(e))
    } finally {
      setBusy(false)
    }
  }

  const pending = a.status === 'pending'
  const mail = emailOf(a)
  const ok = a.status === 'done'
  return (
    <div className="approval action-card" data-s={a.status} role="group" aria-label="Persetujuan aksi agen">
      <p className="approval-title">{a.summary}</p>
      {a.payload.preview && <p className="action-preview">{a.payload.preview}</p>}
      {mail && (
        <div className="action-preview mail-preview" aria-label="Isi email yang akan dikirim">
          <div>
            <b>Kepada:</b> {mail.to}
          </div>
          <div>
            <b>Subjek:</b> {mail.subject || '(tanpa subjek)'}
          </div>
          {mail.reply && (
            <div>
              <b>Membalas:</b> {mail.reply}
            </div>
          )}
          <div className="mail-body">{mail.body}</div>
        </div>
      )}
      {a.payload.link && pending && (
        <a className="action-link" href={a.payload.link} target="_blank" rel="noreferrer">
          Lihat berkasnya
        </a>
      )}
      {pending ? (
        <>
          <p className="plan-note">Agen tidak melakukan apa-apa sebelum Anda setuju.</p>
          <div className="approval-actions">
            <button className="btn primary" disabled={busy} onClick={() => void decide(true)}>
              Setujui
            </button>
            <button className="btn soft" disabled={busy} onClick={() => void decide(false)}>
              Tolak
            </button>
          </div>
        </>
      ) : (
        <p className={ok ? 'plan-done' : 'action-result'} role="status">
          <b>{ok ? 'Selesai. ' : a.status === 'rejected' ? 'Ditolak. ' : a.status === 'expired' ? 'Kedaluwarsa. ' : 'Gagal. '}</b>
          {a.status === 'rejected' || a.status === 'expired' ? '' : a.result}
        </p>
      )}
      {problem && (
        <p className="plan-problem" role="alert">
          {problem}
        </p>
      )}
    </div>
  )
}
