import { useMemo, useSyncExternalStore } from 'react'

// Hash router. The hash is the state, so refresh and back work.
// #/ dashboard, #/chat/<id>/<sesi?> (old #/bot/... still read), #/grup/<id>, #/agen, #/agen/baru, #/agen/<id>, #/agen/<id>/ubah,
// #/tools, #/computer-use, #/scheduler, #/marketing, #/cs, #/aktivitas
export type Route =
  | { name: 'home' }
  | { name: 'bot'; id: string; sid?: string }
  | { name: 'grup'; id: string }
  | { name: 'aktivitas' }
  | { name: 'agen' }
  | { name: 'agen-baru' }
  | { name: 'agen-detail'; id: string }
  | { name: 'agen-ubah'; id: string }
  | { name: 'tools' }
  | { name: 'computer-use' }
  | { name: 'scheduler' }
  | { name: 'marketing' }
  | { name: 'cs' }

export function parse(hash: string): Route {
  const p = hash.replace(/^#\/?/, '').split('/').filter(Boolean).map(decodeURIComponent)
  if ((p[0] === 'chat' || p[0] === 'bot') && p[1]) return { name: 'bot', id: p[1], sid: p[2] }
  if (p[0] === 'grup' && p[1]) return { name: 'grup', id: p[1] }
  if (p[0] === 'agen') {
    if (p[1] === 'baru') return { name: 'agen-baru' }
    if (p[1] && p[2] === 'ubah') return { name: 'agen-ubah', id: p[1] }
    if (p[1]) return { name: 'agen-detail', id: p[1] }
    return { name: 'agen' }
  }
  if (p[0] === 'aktivitas') return { name: 'aktivitas' }
  if (p[0] === 'tools') return { name: 'tools' }
  if (p[0] === 'computer-use') return { name: 'computer-use' }
  if (p[0] === 'scheduler') return { name: 'scheduler' }
  if (p[0] === 'marketing') return { name: 'marketing' }
  if (p[0] === 'cs') return { name: 'cs' }
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

export const botPath = (id: string, sid?: string) => `/chat/${encodeURIComponent(id)}${sid ? '/' + encodeURIComponent(sid) : ''}`
export const groupPath = (id: string) => `/grup/${encodeURIComponent(id)}`
export const agenPath = (id: string, sub?: 'ubah') => `/agen/${encodeURIComponent(id)}${sub ? '/' + sub : ''}`
