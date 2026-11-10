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

const LABELS: [RegExp, string][] = [
  [/^skills?_/, 'Membaca panduan'],
  [/^session_search/, 'Mencari riwayat'],
  [/^web/, 'Mencari di web'],
  [/^memory/, 'Membuka memori'],
  [/^vision/, 'Melihat gambar'],
  [/^image_gen/, 'Membuat gambar'],
  [/^todo/, 'Menyusun langkah'],
]
export const toolLabel = (tool: string): string => LABELS.find(([re]) => re.test(tool))?.[1] ?? tool
