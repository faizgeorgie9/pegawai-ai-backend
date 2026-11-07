import { useCallback, useEffect, useRef, useState } from 'react'
import { api, asStr, errText, subscribe } from './bff'

// One agent run for the workspaces: start (optionally in an existing session), follow the stream, resolve with the final text.
// `reset()` and unmount drop the stream; a late answer is ignored by the ticket check, so nothing from another agent or an
// older request lands in the current view. The run itself keeps going on the server (same as leaving a chat).
export type RunStatus = 'idle' | 'running' | 'done' | 'stopped' | 'error'
export interface RunEnd {
  status: RunStatus
  text: string
  error: string
  runId: string
  sid: string
}

export function useRun(botId = '') {
  const [status, setStatus] = useState<RunStatus>('idle')
  const [text, setText] = useState('')
  const [error, setError] = useState('')
  const [runId, setRunId] = useState('')
  const ticket = useRef(0)
  const unstream = useRef<(() => void) | null>(null)
  const runRef = useRef('')

  const drop = useCallback(() => {
    unstream.current?.()
    unstream.current = null
  }, [])
  useEffect(() => drop, [drop])

  const reset = useCallback(() => {
    ticket.current++
    drop()
    runRef.current = ''
    setStatus('idle')
    setText('')
    setError('')
    setRunId('')
  }, [drop])

  const send = useCallback(
    (input: string, opt: { sid?: string; instructions?: string; botId?: string } = {}): Promise<RunEnd> => {
      const mine = ++ticket.current
      drop()
      setStatus('running')
      setText('')
      setError('')
      setRunId('')
      const fail = (e: string): RunEnd => ({ status: 'error', text: '', error: e, runId: runRef.current, sid: opt.sid ?? '' })
      return new Promise<RunEnd>((resolve) => {
        const end = (r: RunEnd) => {
          if (mine !== ticket.current) return resolve({ ...r, status: 'idle' }) // superseded: caller must ignore
          drop()
          setStatus(r.status)
          setError(r.error)
          if (r.text) setText(r.text)
          resolve(r)
        }
        api.startRun(opt.botId ?? botId, input, opt.sid, opt.instructions).then(
          (r) => {
            if (mine !== ticket.current) return end(fail(''))
            runRef.current = r.run.id
            setRunId(r.run.id)
            let acc = ''
            const sid = r.session_id || opt.sid || ''
            unstream.current = subscribe(`/runs/${encodeURIComponent(r.run.id)}/stream`, {
              snapshot: (d) => {
                acc = asStr(d.output) || acc
                if (mine === ticket.current) setText(acc)
              },
              delta: (d) => {
                acc += asStr(d.text)
                if (mine === ticket.current) setText(acc)
              },
              done: (d) => {
                const st = asStr(d.status).toLowerCase()
                const out = asStr(d.output) || acc
                const stopped = /stop|cancel|interrupt/.test(st)
                const failed = /fail|error/.test(st)
                end({ status: stopped ? 'stopped' : failed ? 'error' : 'done', text: out, error: failed ? asStr(d.error) || 'Agen belum berhasil menyelesaikan tugas ini.' : '', runId: r.run.id, sid })
              },
            })
          },
          (e) => end(fail(errText(e))),
        )
      })
    },
    [botId, drop],
  )

  const stop = useCallback(() => {
    if (runRef.current) void api.stopRun(runRef.current).catch(() => {})
  }, [])

  return { status, text, error, runId, send, stop, reset, busy: status === 'running' }
}
