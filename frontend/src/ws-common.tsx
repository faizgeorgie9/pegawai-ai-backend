import { useData } from './data'
import type { Bot } from './bff'
import { botPath } from './router'
import { Dialog, ErrorLine } from './ui'
import type { RunStatus } from './useRun'

// Pieces shared by the Marketing and CS workspaces and the test page.

export function teamBots(bots: Bot[], team: string): Bot[] {
  return bots.filter((b) => b.team === team)
}

export function AgentSelect({ label, bots, value, onChange, disabled }: { label: string; bots: Bot[]; value: string; onChange: (id: string) => void; disabled?: boolean }) {
  return (
    <label className="field inline ws-agent">
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled || bots.length === 0}>
        {bots.length === 0 && <option value="">Belum ada agen</option>}
        {bots.map((b) => (
          <option key={b.id} value={b.id}>
            {b.name} · {b.role}
          </option>
        ))}
      </select>
    </label>
  )
}

export function Switch({ checked, onChange, label, hint }: { checked: boolean; onChange: (v: boolean) => void; label: string; hint?: string }) {
  return (
    <label className="ws-switch" title={hint}>
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span>{label}</span>
    </label>
  )
}

export function ConfirmSwitch({ onYes, onNo }: { onYes: () => void; onNo: () => void }) {
  return (
    <Dialog title="Ganti agen?" onClose={onNo}>
      <div className="dlg-body">
        <p>Ada pekerjaan yang belum disimpan di workspace ini. Jika agen diganti, sesi baru dimulai dan semua tahap serta hasil di layar ini dikosongkan. Riwayat chat agen lama tetap ada.</p>
        <div className="dlg-foot">
          <button className="btn soft" onClick={onNo}>
            Tetap di agen ini
          </button>
          <button
            className="btn primary"
            onClick={() => {
              onYes()
            }}
          >
            Ganti dan kosongkan
          </button>
        </div>
      </div>
    </Dialog>
  )
}

export function RunBar({ busy, text, onStop, status, error, onRetry, stoppedNote }: { busy: boolean; text: string; onStop: () => void; status: RunStatus; error: string; onRetry?: () => void; stoppedNote?: string }) {
  return (
    <>
      {busy && (
        <div className="runbar" role="status">
          <span className="dots" aria-hidden="true" />
          <span>{text}</span>
          <button className="btn soft" onClick={onStop}>
            Hentikan
          </button>
        </div>
      )}
      {status === 'error' && error && <ErrorLine text={error} onRetry={onRetry} />}
      {status === 'stopped' && <p className="note-box">{stoppedNote ?? 'Dihentikan. Tidak ada hasil yang disimpan.'}</p>}
    </>
  )
}

export const OpenInChat = ({ botId, sid }: { botId: string; sid: string }) =>
  sid ? (
    <a className="btn outline" href={'#' + botPath(botId, sid)}>
      Buka di chat
    </a>
  ) : null

export function useBots() {
  return useData().bots
}

export const hhmm = (d: Date) => d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
