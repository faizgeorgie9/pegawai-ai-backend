import type { ModelCatalog } from './bff'
import { modelKey } from './ui-extra'

// Friendly model choice for non-technical users: models grouped by price into 3 tiers.
// shortcut: output USD per 1M tokens copied from bff/migrations/009_usage_costs.sql (the catalog API has no prices); unknown models count as "Seimbang". Upgrade: expose price in GET /models.
const OUT: Record<string, number> = {
  'deepseek-v4.1-flash': 1.2, 'deepseek-v4-pro': 3.96, 'glm-5.3-flash': 0.5, 'glm-5.3': 4.4, 'glm-5.2': 4.4, 'glm-5.1': 4.4, 'glm-5': 3.2,
  'kimi-k3.1-pro': 10, 'kimi-k3': 15, 'kimi-k2.7-code': 4, 'kimi-k2.6': 4, 'kimi-k2.5': 3, 'longcat-2.0': 1.2, 'step-5-preview': 2.7,
  'mimo-v2.6-flash': 0.28, 'mimo-v2.6-pro': 0.87, 'mimo-v2.5': 0.28, 'mimo-v2.5-pro': 0.87, 'minimax-m3.1-flash': 0.6, 'minimax-m3': 1.2,
  'minimax-m2.7': 1.2, 'minimax-m2.5': 1.2, 'muse-spark-1.3-contributor': 0.2, 'muse-spark-1.2-contributor': 0.2, 'qwen3.8-max': 6,
  'qwen3.8-flash': 0.47, 'qwen3.7-plus': 1.6, 'qwen3.6-plus': 3, 'qwen3.5-plus': 1.2, hy4: 2.5, 'hy4-preview': 2.5, hy3: 0.58, 'grok-4.7': 6,
  'gpt-6-luna': 0.5, 'gpt-5.6-luna': 1.2, 'claude-haiku-5-5': 0.5, 'gemini-4-argon': 10, 'beam-free': 0, 'iceman-contributor-free': 0, 'longcat-2.5-free': 0,
}

export const TIERS = [
  { id: 'hemat', label: 'Hemat & cepat', hint: 'Biaya paling rendah. Cocok untuk tugas harian yang ringan.' },
  { id: 'seimbang', label: 'Seimbang', hint: 'Biaya sedang. Pilihan aman untuk kebanyakan tugas.' },
  { id: 'teliti', label: 'Paling teliti', hint: 'Biaya paling tinggi. Untuk tugas rumit yang butuh ketelitian.' },
] as const
export type TierId = (typeof TIERS)[number]['id']

const price = (m: string) => OUT[m] ?? 3
export const tierOf = (m: string): TierId => (price(m) <= 1.5 ? 'hemat' : price(m) <= 6 ? 'seimbang' : 'teliti')

// GET /models does not always name the default route the same way as the provider list: production returned
// default.provider "opencode" while the only listed provider was "opencode-zen" (live test, 24 Nov 2026), so a plain
// `slug === default.provider` kept no provider, every tier came out empty and the three "Tingkat ketelitian"
// choices in the Atur dialog were all disabled (FE-2). Compare normalized names and accept a shared prefix.
const sameRoute = (a: string, b: string) => {
  const x = a.toLowerCase().replace(/[^a-z0-9]/g, '')
  const y = b.toLowerCase().replace(/[^a-z0-9]/g, '')
  return !!x && !!y && (x.startsWith(y) || y.startsWith(x))
}

// Only the default provider: it is the one with working credentials; other listed providers may not be signed in.
// The catalog is still the only source of models, so a tier can never offer something the server does not list.
// Ranked by evidence: a slug on the same route (opencode / OpenCode / opencode-zen) beats merely listing the default
// model; the model match breaks ties between two routes that look alike.
function defaultProviders(cat: ModelCatalog | null): ModelCatalog['providers'] {
  const all = cat?.providers ?? []
  const def = cat?.default
  if (!def?.provider && !def?.model) return []
  const rank = (p: ModelCatalog['providers'][number]) =>
    (def.provider && sameRoute(p.slug, def.provider) ? 2 : 0) + (def.model && p.models.includes(def.model) ? 1 : 0)
  const best = Math.max(0, ...all.map(rank))
  return best > 0 ? all.filter((p) => rank(p) === best) : []
}

// tier -> available "provider|model" keys, cheapest first
export function tiersFrom(cat: ModelCatalog | null): Record<TierId, string[]> {
  const out: Record<TierId, { k: string; m: string }[]> = { hemat: [], seimbang: [], teliti: [] }
  for (const p of defaultProviders(cat)) for (const m of p.models) out[tierOf(m)].push({ k: modelKey(p.slug, m), m })
  const r = {} as Record<TierId, string[]>
  for (const t of TIERS) r[t.id] = out[t.id].sort((a, b) => price(a.m) - price(b.m)).map((x) => x.k)
  return r
}
