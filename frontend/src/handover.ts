// Antrean "Perlu manusia" di WhatsApp: satu penyimpanan modul, bukan konteks React, supaya Sidebar,
// Beranda, tab WhatsApp, dan halaman Pelanggan membaca angka yang sama tanpa banyak permintaan.
// Galat dibiarkan diam: angka terakhir tetap tampil, dan `ready` hanya menjadi true setelah ambilan pertama sukses.

import { useCallback, useEffect, useSyncExternalStore } from 'react'
import { api, ApiError } from './bff'
import type { Conversation, ConversationCounts, HandoverReason, HandoverState } from './bff'
import { useData } from './data'

export const HANDOVER_LABEL: Record<HandoverState, string> = { bot: 'Dijawab pegawai', needs_human: 'Perlu manusia', human: 'Diambil alih' }
export const HANDOVER_REASON: Record<HandoverReason | '', string> = {
  asked_human: 'Pelanggan minta bicara dengan manusia',
  complaint: 'Pelanggan komplain barang rusak atau cacat',
  refund: 'Pelanggan minta pengembalian uang',
  bot_unsure: 'Pegawai AI tidak yakin dengan jawabannya',
  other: 'Perlu ditangani manusia',
  '': 'Perlu ditangani manusia',
}
export interface HandoverQueue {
  ready: boolean
  needs: Conversation[]
  counts: ConversationCounts
}

let store: HandoverQueue = { ready: false, needs: [], counts: { needs_human: 0, human: 0, bot: 0 } }
const listeners = new Set<() => void>()
const getSnapshot = () => store
const subscribe = (fn: () => void) => {
  listeners.add(fn)
  return () => {
    listeners.delete(fn)
  }
}
function publish(next: HandoverQueue) {
  store = next
  listeners.forEach((fn) => fn())
}

// One fetch at a time; a request asked for while one is running waits for the next round.
// `denied` stops the timer for an account the endpoint refuses; the entry point then relies on a CS employee.
let loading = false
let again = false
let denied = false
async function load() {
  if (denied) return
  if (loading) {
    again = true
    return
  }
  loading = true
  try {
    const page = await api.conversations({ state: 'needs_human', limit: 3 })
    publish({ ready: true, needs: page.items, counts: page.counts })
  } catch (e) {
    if (e instanceof ApiError && (e.status === 401 || e.status === 403)) denied = true
    /* selain itu diam: angka terakhir tetap tampil */
  } finally {
    loading = false
    if (again) {
      again = false
      void load()
    }
  }
}

// One timer and one event subscription for every caller; both stop when the last caller leaves.
let callers = 0
let timer = 0
let offHandover: (() => void) | null = null

export function useHandoverQueue(): HandoverQueue & { refresh: () => void } {
  const { on } = useData()
  const snapshot = useSyncExternalStore(subscribe, getSnapshot, getSnapshot)

  // Every signed-in user reads the queue once: a staff member may not see the employee list, yet still
  // takes conversations over. A 403 stops the timer; the caller falls back to the employee list.
  useEffect(() => {
    callers++
    if (callers === 1) {
      void load()
      timer = window.setInterval(() => {
        if (document.visibilityState === 'visible') void load()
      }, 60_000)
      offHandover = on('handover', () => void load())
    }
    return () => {
      callers--
      if (callers === 0) {
        window.clearInterval(timer)
        timer = 0
        offHandover?.()
        offHandover = null
        // The shell unmounts on logout: the next account starts with no counts and may try the endpoint again.
        denied = false
        publish({ ready: false, needs: [], counts: { needs_human: 0, human: 0, bot: 0 } })
      }
    }
  }, [on])

  const refresh = useCallback(() => void load(), [])
  return { ...snapshot, refresh }
}
