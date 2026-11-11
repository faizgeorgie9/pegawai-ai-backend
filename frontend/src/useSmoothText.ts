import { useEffect, useRef, useState } from 'react'

export const reducedMotion = () => typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

// Deltas arrive in bursts. While `streaming`, reveal the buffered text at a steady pace and close any backlog fast
// (exponential catch-up, ~99% of it within 400 ms), so the shown text never trails the real text by more than that.
// When streaming ends the full text shows at once. Reduced motion: no smoothing, no caret.
// Commits to React at most every 50 ms (driven by requestAnimationFrame) so long answers do not re-render per frame.
const BASE = 90 // chars per second when there is almost no backlog
const TAU = 0.085 // seconds: backlog decays by e^(-dt/TAU)
const COMMIT_MS = 50

export function useSmoothText(target: string, streaming: boolean): { text: string; caret: boolean } {
  const [shown, setShown] = useState(0)
  const tgt = useRef(target)
  const pos = useRef(0)
  tgt.current = target
  const reduced = reducedMotion()
  const smooth = streaming && !reduced

  useEffect(() => {
    if (!smooth) return
    let raf = 0
    let last = performance.now()
    let committed = -1
    let lastCommit = 0
    const tick = (now: number) => {
      raf = requestAnimationFrame(tick)
      const dt = Math.min((now - last) / 1000, 0.1)
      last = now
      const len = tgt.current.length
      if (pos.current > len) pos.current = len // the text got shorter (a new attempt started)
      const back = len - pos.current
      if (back > 0) {
        const step = Math.max(Math.min(back, BASE * dt), back * (1 - Math.exp(-dt / TAU)))
        pos.current = Math.min(len, pos.current + Math.max(step, 1))
      }
      let p = Math.floor(pos.current)
      const c = tgt.current.charCodeAt(p - 1)
      if (c >= 0xd800 && c <= 0xdbff) p++ // do not cut a surrogate pair
      if (p !== committed && (now - lastCommit >= COMMIT_MS || p >= len)) {
        committed = p
        lastCommit = now
        setShown(p)
      }
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [smooth])

  if (!streaming) return { text: target, caret: false }
  if (reduced) return { text: target, caret: false }
  return { text: target.slice(0, Math.min(shown, target.length)), caret: true }
}
