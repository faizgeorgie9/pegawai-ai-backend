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
// `denied` stops the timer for an account the endpoint refuses or does not have; the entry point then relies
// on a CS employee.
// `generation` belongs to the session: logout bumps it, so a reply that started before logout can neither
// publish the previous account's customers nor set `denied` for the next account.
let generation = 0
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
  const gen = generation
  try {
    const page = await api.conversations({ state: 'needs_human', limit: 3 })
    if (gen !== generation) return
    publish({ ready: true, needs: page.items, counts: page.counts })
  } catch (e) {
    if (gen !== generation) return
    // 401/403: this account may not read the queue. 404: the BFF has no queue endpoint (yet). One probe per
    // session is enough; no error is shown and the caller falls back to the employee list.
    if (e instanceof ApiError && (e.status === 401 || e.status === 403 || e.status === 404)) {
      denied = true
      stopPolling()
    }
    /* selain itu diam: angka terakhir tetap tampil */
  } finally {
    // A reply from an ended session must not clear or restart the flags of the current one.
    if (gen === generation) {
      loading = false
      if (again) {
        again = false
        void load()
      }
    }
  }
}

// One timer and one event subscription for every caller that wants live numbers; both stop when the last of
// them leaves. `callers` is separate: it keeps the shared store alive (and does the session's first read) so a
// caller that only needs the entry decision still gets the numbers other pages fetch.
let callers = 0
let pollers = 0
let timer = 0
let offHandover: (() => void) | null = null

function stopPolling() {
  window.clearInterval(timer)
  timer = 0
  offHandover?.()
  offHandover = null
}

// `poll` asks for the repeating read. It is on by default; a caller that does not need live numbers (the
// Sidebar, when the Pelanggan entry is already on screen) can pass false and still read the queue once. Once
// the endpoint has answered, the timer also runs for that caller: the entry and its badge are then on screen,
// so fresh numbers matter again. A 404/401/403 stops it either way.
export function useHandoverQueue(poll = true): HandoverQueue & { refresh: () => void } {
  const { on } = useData()
  const snapshot = useSyncExternalStore(subscribe, getSnapshot, getSnapshot)

  // Every signed-in caller joins the session's queue: a staff member may not see the employee list, yet still
  // takes conversations over. One read happens when the first caller arrives; logout ends the session.
  useEffect(() => {
    callers++
    if (callers === 1) void load()
    return () => {
      callers--
      if (callers === 0) {
        stopPolling()
        // The shell unmounts on logout: end this session (a late reply is dropped), and let the next account
        // start with no counts, no request behind it, and a fresh chance to read the endpoint.
        generation++
        loading = false
        again = false
        denied = false
        publish({ ready: false, needs: [], counts: { needs_human: 0, human: 0, bot: 0 } })
      }
    }
  }, [])

  const live = poll || snapshot.ready
  useEffect(() => {
    if (!live || denied) return
    pollers++
    if (pollers === 1) {
      timer = window.setInterval(() => {
        if (document.visibilityState === 'visible') void load()
      }, 60_000)
      offHandover = on('handover', () => void load())
    }
    return () => {
      pollers--
      if (pollers === 0) stopPolling()
    }
  }, [on, live])

  const refresh = useCallback(() => void load(), [])
  return { ...snapshot, refresh }
}
