// Short-lived cache for read-only lists (connections, app catalog, skills, security).
// A screen the user returns to paints from memory instead of holding an empty skeleton again,
// and two mounts of the same screen (React StrictMode in dev) share one request.
// A failed read is never kept, so "Coba lagi" starts a real request.

const TTL_MS = 60_000
type Entry = { at: number; scope: string; p: Promise<unknown> }
const store = new Map<string, Entry>()

// The token is part of the entry: after another account signs in, old data cannot be shown to it.
function scope(): string {
  try {
    return localStorage.getItem('pegawai_ai_token') ?? ''
  } catch {
    return ''
  }
}

export function cachedRead<T>(key: string, load: () => Promise<T>): Promise<T> {
  const who = scope()
  const hit = store.get(key)
  if (hit && hit.scope === who && Date.now() - hit.at < TTL_MS) return hit.p as Promise<T>
  const entry: Entry = { at: Date.now(), scope: who, p: load() }
  store.set(key, entry)
  entry.p.catch(() => {
    if (store.get(key) === entry) store.delete(key)
  })
  return entry.p as Promise<T>
}

// Drops the entries a change made stale (connect, disconnect, a fresh=1 reload).
export function forgetReads(...keys: string[]): void {
  for (const k of keys) store.delete(k)
}

// Starts a slow read while the pointer or keyboard focus is still on the menu link, so the click
// lands on data instead of an empty page. Attached once per selector *and purpose* (the data attribute
// survives HMR): two purposes on the same link (warming the code chunk, warming the data) each need
// their own key, or the second registration is dropped and never fires.
export function onLinkIntent(selector: string, run: () => void, key = selector): void {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  const flag = `intent${key.replace(/\W/g, '')}`
  if (flag in root.dataset) return
  root.dataset[flag] = '1'
  const fire = (e: Event) => {
    const t = e.target
    if (t instanceof Element && t.closest(selector)) run()
  }
  document.addEventListener('pointerover', fire, { passive: true })
  document.addEventListener('focusin', fire)
  document.addEventListener('touchstart', fire, { passive: true })
}
