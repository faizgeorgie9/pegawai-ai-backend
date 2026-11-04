import { useMemo, useSyncExternalStore } from 'react'

// Hash router: #/bot/<id>/<session?>, #/grup/<id>, #/aktivitas. Refresh and back work because the hash is the state.
export type Route =
  | { name: 'home' }
  | { name: 'bot'; id: string; sid?: string }
  | { name: 'grup'; id: string }
  | { name: 'aktivitas' }

export function parse(hash: string): Route {
  const p = hash.replace(/^#\/?/, '').split('/').filter(Boolean).map(decodeURIComponent)
  if (p[0] === 'bot' && p[1]) return { name: 'bot', id: p[1], sid: p[2] }
  if (p[0] === 'grup' && p[1]) return { name: 'grup', id: p[1] }
  if (p[0] === 'aktivitas') return { name: 'aktivitas' }
  return { name: 'home' }
}

const subscribe = (fn: () => void) => {
  window.addEventListener('hashchange', fn)
  return () => window.removeEventListener('hashchange', fn)
}

export function useRoute(): Route {
  const hash = useSyncExternalStore(subscribe, () => location.hash)
  return useMemo(() => parse(hash), [hash])
}

export function go(path: string, replace = false) {
  const h = '#' + path
  if (replace) {
    history.replaceState(null, '', h)
    window.dispatchEvent(new HashChangeEvent('hashchange')) // replaceState fires nothing by itself
  } else location.hash = h
}

export const botPath = (id: string, sid?: string) => `/bot/${encodeURIComponent(id)}${sid ? '/' + encodeURIComponent(sid) : ''}`
export const groupPath = (id: string) => `/grup/${encodeURIComponent(id)}`
