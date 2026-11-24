import { useSyncExternalStore } from 'react'

// Admin screens are chosen by the account's role from /auth/me, not by this browser. "Mode admin" is only a
// declutter switch for admins: default on, never shown to members. It is not access control.
const KEY = 'pegawai-ai.admin-mode'
const ADMIN_ROLE = /^(owner|admin|super_?admin)$/i
const listeners = new Set<() => void>()
let role: string | null = null

export const isAdminRole = (value?: string | null) => ADMIN_ROLE.test((value ?? '').trim())

/** The signed-in account's role; App sets it on login/boot and clears it on logout. */
export function setAuthRole(next: string | null) {
  const value = next && next.trim() ? next.trim() : null
  if (value === role) return
  role = value
  listeners.forEach((l) => l())
}

function subscribe(l: () => void) {
  listeners.add(l)
  return () => listeners.delete(l)
}

// Unset means on: an admin gets the full workspace right after login, with no hidden switch to find.
function read(): boolean {
  try {
    return localStorage.getItem(KEY) !== '0'
  } catch {
    return true
  }
}

export function setAdminMode(on: boolean) {
  try {
    if (on) localStorage.setItem(KEY, '1')
    else localStorage.setItem(KEY, '0')
  } catch {
    // storage blocked: the toggle just does not persist
  }
  listeners.forEach((l) => l())
}

export function useIsAdmin(): boolean {
  return useSyncExternalStore(subscribe, () => isAdminRole(role), () => false)
}

export function useAdminMode(): boolean {
  const admin = useIsAdmin()
  const shown = useSyncExternalStore(subscribe, read, () => false)
  return admin && shown
}
