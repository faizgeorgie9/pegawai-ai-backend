import type { ReactNode } from 'react'
import {
  siAirtable, siAsana, siBetterstack, siBox, siCalendly, siClickhouse, siClickup, siCloudflare, siCoinbase,
  siConfluence, siDatadog, siDiscord, siInstagram, siIntercom, siJira, siLinear, siMetabase,
  siMintlify, siNeon, siNotion, siPosthog, siRailway, siResend, siSemrush, siSentry, siShopify, siStripe,
  siSupabase, siTodoist, siTurso, siVercel,
  type SimpleIcon,
} from 'simple-icons'
import { EXTRA_LOGOS } from './app-logos-extra'

// app id (Hermes catalog id or our own connection id) -> brand icon (simple-icons, CC0).
// gdrive/gmail keep their own multicolour marks in connections.tsx (single-colour simple-icons looked worse). Ids without an entry in either map (Ahrefs, SendGrid, ...) fall back to the initial avatar.
const LOGOS: Record<string, SimpleIcon> = {
  airtable: siAirtable,
  asana: siAsana,
  better_stack_mcp: siBetterstack,
  box: siBox,
  calendly: siCalendly,
  clickhouse_mcp: siClickhouse,
  clickup_mcp: siClickup,
  cloudflare_mcp: siCloudflare,
  coinbase_agents_mcp: siCoinbase,
  coinbase_wallet_mcp: siCoinbase,
  confluence: siConfluence,
  datadog_mcp: siDatadog,
  discordbot: siDiscord,
  intercom_mcp: siIntercom,
  instagram: siInstagram,
  jira: siJira,
  linear: siLinear,
  metabase: siMetabase,
  mintlify_mcp: siMintlify,
  neon_mcp: siNeon,
  notion: siNotion,
  posthog_mcp: siPosthog,
  railway: siRailway,
  resend_mcp: siResend,
  semrush: siSemrush,
  sentry_mcp: siSentry,
  shopify: siShopify,
  stripe_mcp: siStripe,
  supabase: siSupabase,
  todoist_mcp: siTodoist,
  turso: siTurso,
  vercel_mcp: siVercel,
}

export const hasLogo = (id: string) => id in LOGOS || id in EXTRA_LOGOS || id === 'canva'

// Brand colour on a neutral light tile in both themes, so dark brand colours stay visible. Decorative: the name is text next to it.
export function AppLogo({ id, size = 28, fallback = null }: { id: string; name?: string; size?: number; fallback?: ReactNode }) {
  const icon = LOGOS[id]
  // Our Canva connection reuses the official full-colour mark the old Hermes connector already carried.
  const extra = icon ? undefined : EXTRA_LOGOS[id] ?? (id === 'canva' ? EXTRA_LOGOS['canva_mcp'] : undefined)
  if (!icon && !extra) return <>{fallback}</>
  const px = Math.round(size * 0.64)
  return (
    <span className="app-logo" style={{ width: size, height: size }} aria-hidden="true">
      {icon ? (
        <svg viewBox="0 0 24 24" width={px} height={px} focusable="false">
          <path d={icon.path} fill={`#${icon.hex}`} />
        </svg>
      ) : (
        // Full-colour marks from app-logos-extra.ts (sanitized at generation time).
        <svg viewBox={extra!.vb} width={px} height={px} focusable="false" dangerouslySetInnerHTML={{ __html: extra!.body }} />
      )}
    </span>
  )
}
