// Composer shortcuts while an agent works: Enter queues the message, Ctrl+Enter (Cmd+Enter on Mac) sends it right away.
export const MAC = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/i.test(navigator.platform || navigator.userAgent)
export const STEER_KEY = MAC ? '⌘+Enter' : 'Ctrl+Enter'
export const STEER_TIP = 'Agen langsung membaca pesan ini di tengah pekerjaannya.'
export const RUNNING_HINT = `Enter: kirim setelah selesai · ${STEER_KEY}: kirim sekarang`
export const RUNNING_PLACEHOLDER = 'Agen sedang bekerja. Pesan Anda akan dikirim setelah selesai.'
export const isSteerKey = (e: { ctrlKey: boolean; metaKey: boolean }) => e.ctrlKey || e.metaKey
