import { useSyncExternalStore } from 'react'

// "Mode admin" shows developer/QA screens and setup details. It only declutters the UI; it is not access control.
// shortcut: stored per browser in localStorage; move to a workspace setting in the BFF when login and roles exist.
const KEY = 'pegawai-ai.admin-mode'
const listeners = new Set<() => void>()

function read(): boolean {
  try {
    return localStorage.getItem(KEY) === '1'
  } catch {
    return false
  }
}

export function setAdminMode(on: boolean) {
  try {
    if (on) localStorage.setItem(KEY, '1')
    else localStorage.removeItem(KEY)
  } catch {
    // storage blocked: the toggle just does not persist
  }
  listeners.forEach((l) => l())
}

function subscribe(l: () => void) {
  listeners.add(l)
  return () => listeners.delete(l)
}

export function useAdminMode(): boolean {
  return useSyncExternalStore(subscribe, read, () => false)
}
