// Composer shortcuts while an agent works: Enter queues the message, Ctrl+Enter (Cmd+Enter on Mac) sends it right away.
export const MAC = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/i.test(navigator.platform || navigator.userAgent)
export const STEER_KEY = MAC ? '⌘+Enter' : 'Ctrl+Enter'
export const STEER_TIP = 'Pegawai langsung membaca pesan ini sambil bekerja.'
export const RUNNING_HINT = `Enter: kirim setelah selesai · ${STEER_KEY}: kirim sekarang`
export const RUNNING_PLACEHOLDER = 'Pegawai sedang bekerja. Pesan Anda dikirim setelah selesai.'
export const isSteerKey = (e: { ctrlKey: boolean; metaKey: boolean }) => e.ctrlKey || e.metaKey
