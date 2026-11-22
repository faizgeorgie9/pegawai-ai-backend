import { asStr, newKey } from './bff'
import type { Raw, ToolChip } from './bff'

// Tool events from the run stream (`tool`: tool.started / tool.completed) folded into a list of steps.
const isEnd = (ev: string) => /complet|finish|done|end|result|error|fail/.test(ev)

export function applyTool(tools: ToolChip[], d: Raw): ToolChip[] {
  const tool = asStr(d.tool, 'tool')
  const ev = asStr(d.event).toLowerCase()
  const bad = Boolean(d.error) || /error|fail/.test(ev)
  const preview = asStr(d.preview) || undefined
  if (!isEnd(ev)) return [...tools, { id: newKey('t'), tool, preview, status: 'run' }]
  const i = tools.map((t) => t.tool === tool && t.status === 'run').lastIndexOf(true)
  const status = bad ? 'bad' : 'done'
  if (i < 0) return [...tools, { id: newKey('t'), tool, preview, status }]
  return tools.map((t, n) => (n === i ? { ...t, status, preview: preview ?? t.preview } : t))
}

export const toolsFrom = (x: unknown): ToolChip[] | undefined =>
  Array.isArray(x)
    ? (x as Raw[])
        .filter((r) => !r.type || String(r.type).startsWith('tool.')) // stored rows: {type, payload}; live ones are already flat
        .reduce<ToolChip[]>((acc, r) => applyTool(acc, r.type ? { ...(r.payload as Raw), event: r.type } : r), [])
    : undefined

// A run that ended: nothing is still "running".
export const settle = (tools: ToolChip[]): ToolChip[] => (tools.some((t) => t.status === 'run') ? tools.map((t) => (t.status === 'run' ? { ...t, status: 'done' as const } : t)) : tools)

// The one place that turns an engine tool name (session_search, read_file...) into words for the user.
// shortcut: pattern list, add a line when the engine ships a new tool; unknown names fall back to a readable form of the name.
const LABELS: [RegExp, string][] = [
  // Names the engine/MCP server ships as one flat word: list them before the generic families below.
  [/^kb_add_note/, 'Menyimpan catatan ke Pengetahuan'],
  [/^kb_/, 'Membaca Pengetahuan'],
  [/^knowledge/, 'Membaca Pengetahuan'],
  [/^task_complete/, 'Menyelesaikan tugas'],
  [/^task_cancel/, 'Membatalkan tugas'],
  [/^task_list/, 'Melihat daftar tugas'],
  [/^task_ask_user/, 'Bertanya kepada Anda'],
  [/^gmail_search/, 'Mencari email'],
  [/^gmail_create_draft/, 'Membuat draf email'],
  [/^gmail_send/, 'Mengirim email'],
  [/^drive_search/, 'Mencari di Drive'],
  [/^drive_read/, 'Membaca berkas Drive'],
  [/^drive_create/, 'Membuat berkas Drive'],
  [/^ping/, 'Memeriksa sambungan'],
  [/^tool_describe/, 'Membaca petunjuk alat'],
  [/^tool_search/, 'Mencari alat'],
  [/^tool_call/, 'Memakai alat'],
  [/^manage_connections/, 'Mengatur aplikasi tersambung'],
  [/^skills?_/, 'Membaca panduan'],
  [/^session_search/, 'Mencari percakapan lama'],
  [/^web/, 'Mencari di web'],
  [/^(browser|navigate)/, 'Membuka halaman web'],
  [/^(read_file|file_read|search_files|list_files|grep|glob)/, 'Membaca berkas'],
  [/^(write_file|patch|edit_file|file_write)/, 'Menulis berkas'],
  [/^(terminal|shell|bash|execute|process)/, 'Menjalankan perintah'],
  [/^(code_exec|python)/, 'Menjalankan kode'],
  [/^memory/, 'Memakai ingatan'],
  [/^vision/, 'Melihat gambar'],
  [/^image_gen/, 'Membuat gambar'],
  [/^todo/, 'Menyusun langkah'],
  [/^clarify/, 'Bertanya kepada Anda'],
  [/^(delegate|delegation)/, 'Membagi tugas'],
  [/^(cron|schedule)/, 'Mengatur jadwal'],
  [/^kanban/, 'Mengelola tugas'],
  [/^(drive|gdrive|gmail|notion|connection)/, 'Memakai aplikasi tersambung'],
]
export const toolLabel = (tool: string): string => {
  const t = tool.replace(/^mcp__[a-z0-9]+__/i, '') // mcp__pegawai__kb_add_note → kb_add_note
  const hit = LABELS.find(([re]) => re.test(t))?.[1]
  if (hit) return hit
  const words = t.replace(/[_.-]+/g, ' ').trim()
  return words ? words.charAt(0).toUpperCase() + words.slice(1) : 'Langkah kerja'
}
