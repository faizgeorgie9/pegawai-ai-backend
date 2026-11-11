import { useCallback, useEffect, useRef, useState } from 'react'
import { api, asStr, errText, subscribe } from './bff'
import type { RunCtx, ToolChip } from './bff'
import { applyTool, settle, toolsFrom } from './steps'
import { toRunResult } from './results'
import type { RunResult } from './results'

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
  result: RunResult // structured CS result, validation and context_refs from the `done` frame (empty without a workflow)
}
const NONE: RunResult = { structured: null, validation: null, refs: [] }

export function useRun(botId = '') {
  const [status, setStatus] = useState<RunStatus>('idle')
  const [text, setText] = useState('')
  const [error, setError] = useState('')
  const [runId, setRunId] = useState('')
  const [tools, setTools] = useState<ToolChip[]>([]) // live steps: one per tool event, kept after the run for the folded line
  const [startedAt, setStartedAt] = useState(0)
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
    setTools([])
  }, [drop])

  const send = useCallback(
    (input: string, opt: { sid?: string; instructions?: string; botId?: string; ctx?: RunCtx } = {}): Promise<RunEnd> => {
      const mine = ++ticket.current
      drop()
      setStatus('running')
      setText('')
      setError('')
      setRunId('')
      setTools([])
      setStartedAt(Date.now())
      const fail = (e: string): RunEnd => ({ status: 'error', text: '', error: e, runId: runRef.current, sid: opt.sid ?? '', result: NONE })
      return new Promise<RunEnd>((resolve) => {
        const end = (r: RunEnd) => {
          if (mine !== ticket.current) return resolve({ ...r, status: 'idle' }) // superseded: caller must ignore
          drop()
          setStatus(r.status)
          setError(r.error)
          setTools(settle)
          if (r.text) setText(r.text)
          resolve(r)
        }
        api.startRun(opt.botId ?? botId, input, opt.sid, opt.instructions, opt.ctx).then(
          (r) => {
            if (mine !== ticket.current) return end(fail(''))
            runRef.current = r.run.id
            setRunId(r.run.id)
            let acc = ''
            const sid = r.session_id || opt.sid || ''
            unstream.current = subscribe(`/runs/${encodeURIComponent(r.run.id)}/stream`, {
              snapshot: (d) => {
                acc = asStr(d.output) || acc
                if (mine !== ticket.current) return
                setText(acc)
                const t = toolsFrom(d.tools ?? d.tool_events ?? d.events)
                if (t) setTools(t)
              },
              tool: (d) => {
                if (mine === ticket.current) setTools((cur) => applyTool(cur, d))
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
                end({ status: stopped ? 'stopped' : failed ? 'error' : 'done', text: out, error: failed ? asStr(d.error) || 'Agen belum berhasil menyelesaikan tugas ini.' : '', runId: r.run.id, sid, result: toRunResult(d) })
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

  return { status, text, error, runId, tools, startedAt, send, stop, reset, busy: status === 'running' }
}

// Follow a run that something else started (a server-side sequence): live text from its stream, nothing else.
// An empty id follows nothing. The stream is dropped on its `done` and when the id changes or the page unmounts.
export function useFollow(runId: string): string {
  const [text, setText] = useState('')
  useEffect(() => {
    setText('')
    if (!runId) return
    let acc = ''
    const off = subscribe(`/runs/${encodeURIComponent(runId)}/stream`, {
      snapshot: (d) => {
        acc = asStr(d.output) || acc
        setText(acc)
      },
      delta: (d) => {
        acc += asStr(d.text)
        setText(acc)
      },
      done: () => off(),
    })
    return off
  }, [runId])
  return text
}
