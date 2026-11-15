import { useState } from 'react'
import { api, errText } from './bff'
import { useConnections } from './connections'
import { Dialog } from './ui'
import { Loading } from './ui-extra'

// "Simpan sebagai draf Gmail" under an agent message. The BFF only creates a draft (bff/integrations.py); nothing is ever sent.
const MAIL = 'M4 6h16v12H4zM4 7l8 6 8-6'
const firstLine = (text: string) => text.split('\n').map((l) => l.replace(/^[#>*\-\s]+|[*_`]/g, '').trim()).find(Boolean) ?? ''

export function GmailDraftButton({ text }: { text: string }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button type="button" className="copy-btn" onClick={() => setOpen(true)}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d={MAIL} />
        </svg>
        <span>Simpan sebagai draf Gmail</span>
      </button>
      {open && <DraftDialog text={text} onClose={() => setOpen(false)} />}
    </>
  )
}

function DraftDialog({ text, onClose }: { text: string; onClose: () => void }) {
  const conns = useConnections()
  const status = conns.data?.find((c) => c.provider === 'gmail')?.status
  const first = firstLine(text)
  const [to, setTo] = useState('')
  const [subject, setSubject] = useState(first.length <= 120 ? first : '')
  const [body, setBody] = useState(text)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const [done, setDone] = useState<{ url: string; account: string | null } | null>(null)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setProblem('')
    try {
      setDone(await api.gmailDraft({ to: to.trim(), subject: subject.trim(), body }))
    } catch (err) {
      setProblem(errText(err))
    }
    setBusy(false)
  }

  return (
    <Dialog title="Simpan sebagai draf Gmail" onClose={onClose}>
      {conns.state === 'loading' && !conns.data ? (
        <div className="dlg-body">
          <Loading text="Memeriksa sambungan..." shape="lines" />
        </div>
      ) : status !== 'connected' ? (
        <div className="dlg-body">
          <p>
            {status === 'not_configured' && 'Gmail belum diatur oleh administrator.'}
            {status === 'reconnect' && 'Sambungan Gmail perlu disambungkan ulang.'}
            {(status === 'disconnected' || !status) && 'Gmail belum tersambung.'}
          </p>
          <div className="dlg-foot">
            <button className="btn quiet-btn" type="button" onClick={onClose}>
              Tutup
            </button>
            {status !== 'not_configured' && (
              <a className="btn primary" href="#/aplikasi" onClick={onClose}>
                Buka Aplikasi
              </a>
            )}
          </div>
        </div>
      ) : done ? (
        <div className="dlg-body">
          <p role="status">Draf tersimpan di Gmail{done.account ? ` (${done.account})` : ''}. Email belum dikirim. Anda yang meninjau dan mengirimnya.</p>
          <div className="dlg-foot">
            <button className="btn quiet-btn" type="button" onClick={onClose}>
              Tutup
            </button>
            <a className="btn primary" href={done.url} target="_blank" rel="noopener noreferrer">
              Buka draf di Gmail
            </a>
          </div>
        </div>
      ) : (
        <form className="dlg-body" onSubmit={(e) => void submit(e)}>
          <fieldset disabled={busy}>
            <label className="field">
              <span>Kepada (boleh dikosongkan)</span>
              <input type="text" inputMode="email" autoComplete="off" value={to} onChange={(e) => setTo(e.target.value)} placeholder="nama@contoh.com, pisahkan dengan koma" />
            </label>
            <label className="field">
              <span>Subjek</span>
              <input value={subject} maxLength={300} onChange={(e) => setSubject(e.target.value)} />
            </label>
            <label className="field">
              <span>Isi</span>
              <textarea rows={9} value={body} onChange={(e) => setBody(e.target.value)} />
            </label>
          </fieldset>
          <p className="meta">Hanya dibuat sebagai draf di {conns.data?.find((c) => c.provider === 'gmail')?.account ?? 'akun Gmail Anda'}. Tidak ada email yang dikirim.</p>
          {problem && (
            <p className="problem-bar small" role="alert">
              {problem}
            </p>
          )}
          <div className="dlg-foot">
            <button className="btn quiet-btn" type="button" onClick={onClose}>
              Batal
            </button>
            <button className="btn primary" type="submit" disabled={busy || !body.trim()}>
              {busy ? 'Menyimpan...' : 'Simpan draf'}
            </button>
          </div>
        </form>
      )}
    </Dialog>
  )
}
