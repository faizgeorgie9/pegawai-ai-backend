import { useEffect, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useData } from './data'
import type { Bot } from './bff'
import { AnswerDetails, MarketingCard, Provenance } from './ResultCards'
import { instructionsFor, parseMarketing, stripBlock } from './results'
import { LiveDraft } from './LiveSteps'
import type { ContextRef, MarketingKind, MarketingResult, Parsed } from './results'
import { useRun } from './useRun'
import { I, Icon } from './ui'
import { Empty, Loading, Opt, PageHead } from './ui-extra'
import { ConfirmSwitch, OpenInChat, RunBar, Switch, hhmm, teamBots } from './ws-common'

const STAGES = [
  '1. Brief & PM',
  '2. Strategi & Konsep',
  '3. Riset Katalog',
  '4. Naskah & Prompt',
  '5. Aset Gambar',
  '6. Review Manusia',
] as const

const KIND: MarketingKind[] = ['brief', 'plan', 'content', 'review', 'revision']
const CHANNELS = ['Instagram', 'TikTok', 'WhatsApp', 'Website / marketplace']
const CONTENT_TYPES = [
  'Feed Carousel (4:5 Portrait)',
  'Caption Instagram',
  'Copy promosi',
  'Headline',
  'Deskripsi produk',
  'Skrip Reels',
]

interface AgentInfo {
  id: string
  name: string
  role: string
  handle: string
  tagline: string
  badgeColor: string
  modelInfo: string
}

const AGENTS: AgentInfo[] = [
  { id: 'bimo', name: 'Bimo', role: 'AI Project Manager', handle: '@projectmanager', tagline: 'Inisialisasi Kanban & Brief Dispatch', badgeColor: '#f59e0b', modelInfo: 'DeepSeek V4.1 Flash (OpenCode Zen)' },
  { id: 'meda', name: 'Meda', role: 'Marketing & Fashion Strategist', handle: '@marketingstrategist', tagline: 'Target Audiens Gen Z & 3 Opsi Konsep (A/B/C)', badgeColor: '#f43f5e', modelInfo: 'DeepSeek V4.1 Flash (OpenCode Zen)' },
  { id: 'raka', name: 'Raka', role: 'Fashion & Content Researcher', handle: '@researcher', tagline: 'Cek 1.206 Katalog, Size Guide (cm) & Aset Foto', badgeColor: '#0ea5e9', modelInfo: 'DeepSeek V4.1 Flash (OpenCode Zen)' },
  { id: 'bram', name: 'Bram', role: 'Creative Copywriter & Visual Prompter', handle: '@sketchwriter', tagline: 'Naskah 5 Slide AIDA, Caption IG & AI Visual Prompt', badgeColor: '#6366f1', modelInfo: 'DeepSeek V4.1 Flash (OpenCode Zen)' },
  { id: 'vina', name: 'Vina', role: 'Visual Art Director & Carousel Specialist', handle: '@visualcarousel', tagline: 'Render 5 Slide Gambar Final (1080x1350 px PNG) & Live Preview', badgeColor: '#14b8a6', modelInfo: 'openai/gpt-image-2 (OpenCode Zen)' },
  { id: 'human', name: 'Reviewer Manusia', role: 'Final Quality Gate & Human Approval', handle: '@humanreviewer', tagline: 'Quality Gate, Audit Anti-Halusinasi & Persetujuan Tayang', badgeColor: '#10b981', modelInfo: 'Human-in-the-Loop' },
]

const CAROUSEL_SLIDES = [
  { n: 1, title: 'Slide 1: Cover Hook', desc: 'Effortless Campus Rebel · Formula OOTD Ngampus Standout', img: '/output/carousel_latest/slide_1_cover_hero.png' },
  { n: 2, title: 'Slide 2: Hero Top', desc: 'Contrast Stitch Chambray Shirt (Rp 140.900) · Dark Blue', img: '/output/carousel_latest/slide_2_hero_top.png' },
  { n: 3, title: 'Slide 3: Bottom Pairing', desc: 'High Waist Barrel Denim Pants (Rp 329.900) · Black', img: '/output/carousel_latest/slide_3_bottom_pairing.png' },
  { n: 4, title: 'Slide 4: Accessories & Flatlay', desc: 'Colorbox x Liunic Ecru Tote & Layering Advice', img: '/output/carousel_latest/slide_4_accessories_flatlay.png' },
  { n: 5, title: 'Slide 5: Outro CTA', desc: 'Temukan Fit Favoritmu di colorbox.co.id #NeverJustOneThing', img: '/output/carousel_latest/slide_5_outro_cta.png' },
]

interface Output {
  id: string
  stage: number
  agentId: string
  agentName: string
  n: number // version within the stage
  label: string
  text: string
  parsed: Parsed<MarketingResult>
  structured: boolean
  refs: ContextRef[]
  runId: string
  at: Date
}

const blankForm = {
  objective: '',
  product: '',
  channel: '',
  contentType: '',
  count: '',
  audience: '',
  tone: '',
  keyMessage: '',
  cta: '',
  period: '',
  promoFacts: '',
  forbidden: '',
  unknowns: '',
}

type Form = typeof blankForm

const COLORBOX_SAMPLE: Form = {
  objective: 'Meningkatkan ketertarikan produk melalui inspirasi styling OOTD kuliah (Campus Lookbook) di Instagram',
  product: 'Oversize Long Sleeve Checks Blazer (Rp 299.900 - DUSTY OLIVE)',
  channel: 'Instagram',
  contentType: 'Feed Carousel (4:5 Portrait)',
  count: '5',
  audience: 'Remaja/Pemuda Gen Z terutama perempuan (18-25 tahun, Colorbox Babes)',
  tone: 'Fun, effortless, confident, ramah, dan mendukung self-expression #NeverJustOneThing',
  keyMessage: 'Formula styling kampus effortless: paduan blazer checks oversize & denim chic yang standout seharian tanpa ribet',
  cta: 'Cek katalog lengkap dan ukuran di website resmi colorbox.co.id atau gerai terdekat',
  period: '18 November - 22 November 2026',
  promoFacts: 'Koleksi New Arrivals Colorbox 2026 (tanpa promo diskon fiktif)',
  forbidden: 'Jangan mengarang promo, potongan harga fiktif, stok, atau bahan kain yang tidak tercantum di katalog resmi',
  unknowns: 'Pilihan varian warna tambahan di luar katalog resmi',
}

const VERIFIED_CATALOG_SUGGESTIONS = [
  { name: 'Oversize Long Sleeve Checks Blazer', price: 'Rp 299.900', color: 'DUSTY OLIVE' },
  { name: 'Double Breasted Crop Jacket', price: 'Rp 329.900', color: 'LT. GREY' },
  { name: 'Contrast Detail Denim Jacket', price: 'Rp 359.900', color: 'DARK BROWN' },
  { name: 'Oversize Collared Leather Jacket', price: 'Rp 599.900', color: 'DARK RED' },
  { name: 'Bubble Hem Long Sleeve Hoodie', price: 'Rp 299.900', color: 'ECRU' },
  { name: 'Suede Mini Skirt', price: 'Rp 249.900', color: 'NAVY' },
  { name: 'Jeans with Overlap Micro Skirt Details', price: 'Rp 237.528', color: 'DARK NAVY' },
  { name: 'Wide Leg Drawstring Pants', price: 'Rp 199.900', color: 'NAVY' },
  { name: 'Denim Sling Bag', price: 'Rp 129.900', color: 'DENIM' },
  { name: 'Lace Sneakers', price: 'Rp 299.900', color: 'NAVY' },
  { name: 'Contrast Stitch Chambray Shirt', price: 'Rp 140.900', color: 'DARK BLUE' },
  { name: 'High Waist Barrel Denim Pants', price: 'Rp 329.900', color: 'BLACK' },
]

const FIELDS: [keyof Form, string][] = [
  ['audience', 'Target audiens & demografi'],
  ['tone', 'Brand voice & nada bahasa'],
  ['keyMessage', 'Pesan utama / angle styling'],
  ['cta', 'Call to Action (CTA)'],
  ['period', 'Periode kampanye'],
  ['promoFacts', 'Fakta promo / harga katalog'],
  ['forbidden', 'Batasan & klaim terlarang'],
  ['unknowns', 'Hal yang belum diketahui'],
]

function validate(f: Form): Partial<Record<keyof Form, string>> {
  const e: Partial<Record<keyof Form, string>> = {}
  if (!f.objective.trim()) e.objective = 'Tujuan kampanye wajib diisi.'
  if (!f.product.trim()) e.product = 'Produk atau topik wajib diisi.'
  if (!f.channel) e.channel = 'Pilih kanal media sosial.'
  if (!f.contentType) e.contentType = 'Pilih tipe format konten.'
  const n = Number(f.count)
  if (!f.count.trim()) e.count = 'Jumlah slide/output wajib diisi.'
  else if (!Number.isInteger(n) || n < 1 || n > 10) e.count = 'Isi angka bulat 1 sampai 10.'
  return e
}

function briefPrompt(f: Form): string {
  const row = (k: string, v: string) => (v.trim() ? `${k}: ${v.trim()}\n` : '')
  return (
    'Ini brief kampanye resmi dari tim marketing Colorbox Indonesia:\n\n' +
    row('Tujuan Kampanye', f.objective) +
    row('Produk Acuan (Katalog Resmi)', f.product) +
    row('Kanal Media Sosial', f.channel) +
    row('Format Konten', f.contentType) +
    row('Jumlah Output/Slide', f.count) +
    FIELDS.map(([k, l]) => row(l, f[k])).join('') +
    '\nBimo (@projectmanager), tolong periksa brief ini, catat pembagian tugas sprint di papan Kanban, dan panggil @meda (@marketingstrategist) untuk menyiapkan 3 opsi konsep konten.'
  )
}

export default function Marketing() {
  const { bots } = useData()
  const team = teamBots(bots, 'marketing')
  const [agent, setAgent] = useState('bimo')
  const [pending, setPending] = useState('')
  const dirty = useRef(false)
  const cur = team.find((b) => b.id === agent) ?? team.find((b) => b.id === 'bimo') ?? team[0]

  return (
    <section className="page ws" data-team="marketing">
      <PageHead
        title="Marketing Workflow"
        sub="Alur 5-Agent Colorbox: Bimo (PM) → Meda (Strategi) → Raka (Riset Katalog) → Bram (Naskah & AI Prompt) → Vina (Aset Gambar) → Review Manusia."
        actions={
          <div className="ws-agent" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="mkt-agent-badge" style={{ borderColor: '#10b981' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981' }} />
              Alur 5-Agent Colorbox Aktif
            </span>
          </div>
        }
      />
      {!cur ? (
        <Loading text="Memuat agen marketing Colorbox..." />
      ) : (
        <Workspace key={cur.id} leadBot={cur} onDirty={(v) => (dirty.current = v)} />
      )}
      {pending && (
        <ConfirmSwitch
          onYes={() => {
            dirty.current = false
            setAgent(pending)
            setPending('')
          }}
          onNo={() => setPending('')}
        />
      )}
    </section>
  )
}

function Workspace({ leadBot, onDirty }: { leadBot: Bot; onDirty: (v: boolean) => void }) {
  const run = useRun(leadBot.id)
  const [structured, setStructured] = useState(false)
  const [stage, setStage] = useState(0)
  const [form, setForm] = useState<Form>(blankForm)
  const [tried, setTried] = useState(false)
  const [outs, setOuts] = useState<Output[]>([])
  const [view, setView] = useState('')
  const [sid, setSid] = useState('')
  const sidRef = useRef('')
  const counts = useRef<Record<number, number>>({})
  const [last, setLast] = useState<(() => void) | null>(null)

  // Auto-cascade execution state
  const [cascading, setCascading] = useState(false)
  const [cascadeMsg, setCascadeMsg] = useState('')

  // Human Review State (Stage 5)
  const [checklist, setChecklist] = useState({
    catalogFact: true,
    noFabricHallucination: true,
    ratio45: true,
    brandTone: true,
    officialCTA: true,
  })
  const [decision, setDecision] = useState<'pending' | 'approved' | 'revision' | 'rejected'>('pending')
  const [reviewNotes, setReviewNotes] = useState('')
  const [approvedAt, setApprovedAt] = useState<Date | null>(null)

  const errs = validate(form)
  const hasWork = outs.length > 0 || JSON.stringify(form) !== JSON.stringify(blankForm)
  useEffect(() => {
    onDirty(hasWork)
  }, [hasWork, onDirty])

  const stageDone = (i: number) => {
    if (i < 5) return outs.some((o) => o.stage === i)
    return decision === 'approved'
  }

  async function executeAgent(st: number, botId: string, prompt: string, label: string): Promise<Output | null> {
    setLast(() => () => void executeAgent(st, botId, prompt, label))
    const kind = KIND[Math.min(st, KIND.length - 1)]
    const r = await run.send(prompt, {
      botId,
      sid: sidRef.current || undefined,
      instructions: structured ? instructionsFor(kind) : undefined,
      ctx: { workflow: 'marketing', stage: STAGES[st].toLowerCase() },
    })
    if (r.status === 'idle') return null
    if (r.sid) {
      sidRef.current = r.sid
      setSid(r.sid)
    }
    if (r.status !== 'done') return null
    const parsed: Parsed<MarketingResult> = structured
      ? parseMarketing(r.text, kind)
      : { text: r.text.trim(), result: null, state: 'none', raw: '' }
    const n = (counts.current[st] = (counts.current[st] ?? 0) + 1)
    const agentObj = AGENTS[st]
    const o: Output = {
      id: `${st}-${n}`,
      stage: st,
      agentId: botId,
      agentName: agentObj?.name ?? botId,
      n,
      label,
      text: r.text.trim(),
      parsed,
      structured,
      refs: r.result.refs,
      runId: r.runId,
      at: new Date(),
    }
    setOuts((cur) => [...cur, o])
    setView(o.id)
    setStage(st)
    return o
  }

  function submitBrief(e: React.FormEvent) {
    e.preventDefault()
    setTried(true)
    if (Object.keys(errs).length || run.busy) return
    void executeAgent(0, 'bimo', briefPrompt(form), 'Brief & Kanban')
  }

  function callMeda() {
    const prompt =
      'Meda (@marketingstrategist), berdasarkan brief dari Bimo, rumuskan strategi kampanye, target audiens Gen Z, 3 pilar gaya (Urban/Romantic/Chic), dan pilih produk katalog Colorbox resmi. Buat 3 opsi konsep konten (Opsi A/B/C) dengan rekomendasi utama pada Opsi A, lalu delegasikan ke Raka (@researcher).'
    void executeAgent(1, 'meda', prompt, 'Strategi & Konsep')
  }

  function callRaka() {
    const prompt =
      'Raka (@researcher), validasi produk dari konsep Meda ke katalog resmi Colorbox (product-catalog.md), sertakan harga normal/diskon Rp, bedah panduan ukuran cm (lingkar dada, pinggang, panjang) dari product-size-reference.md, cek ketersediaan foto di images/, dan buat Creative Research Brief 5 slide. Lalu teruskan ke Bram (@sketchwriter).'
    void executeAgent(2, 'raka', prompt, 'Riset Katalog & Ukuran')
  }

  function callBram() {
    const prompt =
      'Bram (@sketchwriter), rancang naskah kreatif dan master AI prompt untuk postingan Instagram tanpa menggunakan template baku (JANGAN GUNAKAN TEMPLATE / ZERO RIGID FORMULAS). Buat konsep unik dari nol sesuai produk terpilih dari Raka, susun on-screen micro-copy minimalis (1-2 kata, tanpa harga), caption Instagram lengkap hashtag #NeverJustOneThing dan harga resmi katalog, serta AI Visual Generation Prompt yang sangat detail, fotorealistik, dan kaya arahan artistik (lighting, angle 4:5 Feed Portrait, lensa 35mm, latar arsitektur nyata, dan model styling) untuk model openai/gpt-image-2 via OpenCode. Lalu serahkan ke Vina (@visualcarousel).'
    void executeAgent(3, 'bram', prompt, 'Naskah & Prompt AI')
  }

  function callVina() {
    const prompt =
      'Vina (@visualcarousel), eksekusi arahan visual dan master prompt dari Bram secara bespoke tanpa template baku. Render 5 slide berkas gambar final Instagram Feed Carousel format 4:5 Portrait (1080x1350 px PNG) menggunakan model visual openai/gpt-image-2 (OpenCode Zen) dan foto produk resmi Colorbox tanpa distorsi aspek rasio (contain mode, tidak gepeng) dan bebas dari noise wireframe/dots. Tampilkan pratinjau gambar dan link live interactive preview, lalu serahkan ke Bimo dan Tim Reviewer Manusia.'
    void executeAgent(4, 'vina', prompt, 'Aset Gambar Carousel')
  }

  async function runAutoCascade() {
    if (run.busy || cascading) return
    setTried(true)
    if (Object.keys(errs).length) return

    setCascading(true)
    try {
      // Step 1: Bimo
      setCascadeMsg('Tahap 1/5: Bimo (@projectmanager) memproses brief & kanban...')
      setStage(0)
      const bimoOut = await executeAgent(0, 'bimo', briefPrompt(form), 'Brief & Kanban')
      if (!bimoOut) throw new Error('Bimo gagal memproses brief.')

      // Step 2: Meda
      setCascadeMsg('Tahap 2/5: Meda (@marketingstrategist) menyusun 3 opsi konsep...')
      setStage(1)
      const medaPrompt =
        'Meda (@marketingstrategist), berdasarkan brief dari Bimo, rumuskan strategi kampanye, target audiens Gen Z, 3 pilar gaya (Urban/Romantic/Chic), dan pilih produk katalog Colorbox resmi. Buat 3 opsi konsep konten (Opsi A/B/C) dengan rekomendasi utama pada Opsi A, lalu delegasikan ke Raka (@researcher).'
      const medaOut = await executeAgent(1, 'meda', medaPrompt, 'Strategi & Konsep')
      if (!medaOut) throw new Error('Meda gagal merumuskan konsep.')

      // Step 3: Raka
      setCascadeMsg('Tahap 3/5: Raka (@researcher) memeriksa 1.216 katalog & ukuran cm...')
      setStage(2)
      const rakaPrompt =
        'Raka (@researcher), validasi produk dari konsep Meda ke katalog resmi Colorbox (product-catalog.md), sertakan harga normal/diskon Rp, bedah panduan ukuran cm (lingkar dada, pinggang, panjang) dari product-size-reference.md, cek ketersediaan foto di images/, dan buat Creative Research Brief 5 slide. Lalu teruskan ke Bram (@sketchwriter).'
      const rakaOut = await executeAgent(2, 'raka', rakaPrompt, 'Riset Katalog & Ukuran')
      if (!rakaOut) throw new Error('Raka gagal memvalidasi katalog.')

      // Step 4: Bram
      setCascadeMsg('Tahap 4/5: Bram (@sketchwriter) menulis naskah & visual prompter bespoke...')
      setStage(3)
      const bramPrompt =
        'Bram (@sketchwriter), rancang naskah kreatif dan master AI prompt untuk postingan Instagram tanpa menggunakan template baku (JANGAN GUNAKAN TEMPLATE / ZERO RIGID FORMULAS). Buat konsep unik dari nol sesuai produk terpilih dari Raka, susun on-screen micro-copy minimalis (1-2 kata, tanpa harga), caption Instagram lengkap hashtag #NeverJustOneThing dan harga resmi katalog, serta AI Visual Generation Prompt yang sangat detail, fotorealistik, dan kaya arahan artistik (lighting, angle 4:5 Feed Portrait, lensa 35mm, latar arsitektur nyata, dan model styling) untuk model openai/gpt-image-2 via OpenCode. Lalu serahkan ke Vina (@visualcarousel).'
      const bramOut = await executeAgent(3, 'bram', bramPrompt, 'Naskah & Prompt AI')
      if (!bramOut) throw new Error('Bram gagal menulis naskah.')

      // Step 5: Vina
      setCascadeMsg('Tahap 5/5: Vina (@visualcarousel) merender gambar visual final (openai/gpt-image-2)...')
      setStage(4)
      const vinaPrompt =
        'Vina (@visualcarousel), eksekusi arahan visual dan master prompt dari Bram secara bespoke tanpa template baku. Render 5 slide berkas gambar final Instagram Feed Carousel format 4:5 Portrait (1080x1350 px PNG) menggunakan model visual openai/gpt-image-2 (OpenCode Zen) dan foto produk resmi Colorbox tanpa distorsi aspek rasio (contain mode, tidak gepeng) dan bebas dari noise wireframe/dots. Tampilkan pratinjau gambar dan link live interactive preview, lalu serahkan ke Bimo dan Tim Reviewer Manusia.'
      const vinaOut = await executeAgent(4, 'vina', vinaPrompt, 'Aset Gambar Carousel')
      if (!vinaOut) throw new Error('Vina gagal merender gambar.')

      // Finished! Navigate to Stage 5 (Review Manusia)
      setCascadeMsg('Alur selesai! Membuka gerbang Review Manusia...')
      setStage(5)
    } catch (e) {
      console.error(e)
    } finally {
      setCascading(false)
      setCascadeMsg('')
    }
  }

  function handleDecision(d: 'approved' | 'revision' | 'rejected') {
    setDecision(d)
    if (d === 'approved') {
      setApprovedAt(new Date())
    }
  }

  const inStage = outs.filter((o) => o.stage === stage)
  const shown = outs.find((o) => o.id === view && o.stage === stage) ?? inStage[inStage.length - 1]
  const currentAgent = AGENTS[stage]
  const revCount = (o: Output) => `v${o.n}`
  const meta = (o: Output) => `${o.agentName} · ${revCount(o)} · ${hhmm(o.at)}`

  return (
    <>
      {sid && (
        <div className="ws-bar">
          <OpenInChat botId={leadBot.id} sid={sid} />
          <span className="quiet small ws-sess">
            Semua agen berbagi konteks percakapan multi-turn yang sama ({sid.slice(0, 8)}...).
          </span>
        </div>
      )}

      {/* Stepper with 6 Stages */}
      <ol className="stepper" aria-label="Tahap kerja alur marketing">
        {STAGES.map((s, i) => (
          <li key={s} data-link={i > 0 && stageDone(i - 1) ? 'done' : undefined}>
            <button
              type="button"
              aria-current={stage === i ? 'step' : undefined}
              onClick={() => setStage(i)}
              data-done={stageDone(i) || undefined}
            >
              <span className="step-n" aria-hidden="true">
                {stageDone(i) ? <Icon d={I.check} size={14} /> : i + 1}
              </span>
              <span>
                {s}
                {stageDone(i) && <span className="sr">, selesai</span>}
              </span>
            </button>
          </li>
        ))}
      </ol>

      {/* Auto-cascade Banner if running */}
      {cascading && (
        <div className="mkt-cascade-banner">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 20 }}>⚡</span>
            <div>
              <b style={{ color: '#047857' }}>Alur Otomatis Sedang Berjalan</b>
              <p style={{ margin: 0, fontSize: 13, color: '#065f46' }}>{cascadeMsg}</p>
            </div>
          </div>
          <button type="button" className="btn soft" onClick={() => run.stop()} style={{ fontSize: 13 }}>
            Hentikan
          </button>
        </div>
      )}

      <div className="ws-grid" data-solo={outs.length === 0 || undefined}>
        <div className="ws-main">
          {/* Agent Badge Header for current Stage */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 16,
              padding: '12px 16px',
              borderRadius: 8,
              background: 'var(--raised)',
              border: '1px solid var(--border)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: '50%',
                  background: currentAgent.badgeColor,
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: 14,
                }}
              >
                {currentAgent.name.slice(0, 2).toUpperCase()}
              </span>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <b style={{ fontSize: 15 }}>{currentAgent.name}</b>
                  <code style={{ fontSize: 12, color: 'var(--muted)' }}>{currentAgent.handle}</code>
                  <span className="pill" style={{ fontSize: 11 }}>
                    {currentAgent.role}
                  </span>
                </div>
                <small style={{ color: 'var(--muted)' }}>{currentAgent.tagline}</small>
              </div>
            </div>
            <span className="quiet small" style={{ textAlign: 'right' }}>
              Model: <b>{currentAgent.modelInfo}</b>
            </span>
          </div>

          {/* Stage 0: Brief & PM (Bimo) */}
          {stage === 0 && (
            <form className="ws-form" onSubmit={submitBrief} noValidate>
              <div className="ws-form-head">
                <h2>1. Brief & Task Dispatch (Bimo)</h2>
                <button type="button" className="btn soft" onClick={() => setForm(COLORBOX_SAMPLE)}>
                  Isi contoh Colorbox (Campus Lookbook)
                </button>
              </div>

              <div className="fgrid">
                <Field label="Tujuan Kampanye" err={tried ? errs.objective : ''}>
                  <input
                    value={form.objective}
                    onChange={(e) => setForm({ ...form, objective: e.target.value })}
                    aria-invalid={tried && !!errs.objective}
                    placeholder="Contoh: Inspirasi OOTD kuliah santai tapi stylish di Instagram"
                  />
                </Field>
                <Field label="Produk Acuan (Katalog Resmi 1.216 Produk)" err={tried ? errs.product : ''}>
                  <input
                    value={form.product}
                    onChange={(e) => setForm({ ...form, product: e.target.value })}
                    aria-invalid={tried && !!errs.product}
                    placeholder="Contoh: Oversize Long Sleeve Checks Blazer (Rp 299.900)"
                  />
                  <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <div style={{ fontSize: 11, color: '#10b981', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                      <span>✓</span>
                      <span>Koleksi Terverifikasi (Klik untuk memilih produk acuan bebas halusinasi):</span>
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {VERIFIED_CATALOG_SUGGESTIONS.map((item) => (
                        <button
                          key={item.name}
                          type="button"
                          className="pill"
                          style={{
                            cursor: 'pointer',
                            fontSize: 11,
                            padding: '3px 8px',
                            borderRadius: 12,
                            border: form.product.includes(item.name) ? '1px solid #10b981' : '1px solid rgba(255,255,255,0.12)',
                            background: form.product.includes(item.name) ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255,255,255,0.03)',
                            color: form.product.includes(item.name) ? '#10b981' : 'inherit',
                          }}
                          onClick={() => setForm({ ...form, product: `${item.name} (${item.price} - ${item.color})` })}
                        >
                          {item.name} • {item.price}
                        </button>
                      ))}
                    </div>
                  </div>
                </Field>
                <Field label="Kanal Media Sosial" err={tried ? errs.channel : ''}>
                  <select
                    value={form.channel}
                    onChange={(e) => setForm({ ...form, channel: e.target.value })}
                    aria-invalid={tried && !!errs.channel}
                  >
                    <option value="">Pilih kanal</option>
                    {CHANNELS.map((c) => (
                      <option key={c}>{c}</option>
                    ))}
                  </select>
                </Field>
                <Field label="Tipe Format Konten" err={tried ? errs.contentType : ''}>
                  <select
                    value={form.contentType}
                    onChange={(e) => setForm({ ...form, contentType: e.target.value })}
                    aria-invalid={tried && !!errs.contentType}
                  >
                    <option value="">Pilih format</option>
                    {CONTENT_TYPES.map((c) => (
                      <option key={c}>{c}</option>
                    ))}
                  </select>
                </Field>
                <Field label="Jumlah Slide Output" err={tried ? errs.count : ''}>
                  <input
                    inputMode="numeric"
                    value={form.count}
                    onChange={(e) => setForm({ ...form, count: e.target.value })}
                    aria-invalid={tried && !!errs.count}
                    placeholder="5"
                  />
                </Field>
              </div>

              <details className="opts" open={FIELDS.some(([k]) => form[k].trim() !== '') || undefined}>
                <summary>Parameter Lanjutan (Target Audiens, Nada Bahasa, CTA, dll)</summary>
                <div className="fgrid opts-body">
                  {FIELDS.map(([k, l]) => (
                    <Field key={k} label={l}>
                      <input value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} />
                    </Field>
                  ))}
                </div>
              </details>

              {tried && Object.keys(errs).length > 0 && (
                <p className="field-err" role="alert">
                  Lengkapi {Object.keys(errs).length} kolom wajib di atas sebelum mengirim brief.
                </p>
              )}

              <div className="form-actions" style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <button className="btn primary" type="submit" disabled={run.busy || cascading}>
                  Kirim Brief ke Bimo (Project Manager)
                </button>
                <button
                  type="button"
                  className="btn mkt-auto-btn"
                  disabled={run.busy || cascading}
                  onClick={runAutoCascade}
                >
                  ⚡ Jalankan Alur Lengkap Otomatis (Auto-Cascade)
                </button>
              </div>
            </form>
          )}

          {/* Stage 1: Meda (Strategi & Konsep) */}
          {stage === 1 && (
            <div className="ws-act">
              <h2>2. Strategi & Konsep (Meda)</h2>
              <p className="quiet">
                Meda menganalisis brief dari Bimo, memetakan pilar gaya (Urban / Romantic / Chic), dan merumuskan 3 Opsi
                Konsep Konten (Opsi A/B/C) lengkap dengan kurasi produk resmi Colorbox.
              </p>
              <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
                <button className="btn primary" disabled={run.busy || cascading} onClick={callMeda}>
                  Minta Konsep & Strategi ke Meda
                </button>
                <button
                  type="button"
                  className="btn mkt-auto-btn"
                  disabled={run.busy || cascading}
                  onClick={runAutoCascade}
                >
                  ⚡ Jalankan Alur Otomatis
                </button>
              </div>
            </div>
          )}

          {/* Stage 2: Raka (Riset Katalog & Ukuran) */}
          {stage === 2 && (
            <div className="ws-act">
              <h2>3. Riset Katalog & Ukuran (Raka)</h2>
              <p className="quiet">
                Raka memvalidasi produk ke katalog resmi Colorbox (1.206 produk), membedah panduan ukuran cm (lingkar
                dada, pinggang, panjang) dari reference guide, memeriksa aset foto di images/, dan menyusun Creative
                Research Brief.
              </p>
              <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
                <button className="btn primary" disabled={run.busy || cascading} onClick={callRaka}>
                  Minta Riset Katalog & Ukuran ke Raka
                </button>
                <button
                  type="button"
                  className="btn mkt-auto-btn"
                  disabled={run.busy || cascading}
                  onClick={runAutoCascade}
                >
                  ⚡ Jalankan Alur Otomatis
                </button>
              </div>
            </div>
          )}

          {/* Stage 3: Bram (Naskah & Prompt AI) */}
          {stage === 3 && (
            <div className="ws-act">
              <h2>4. Naskah & Prompt AI (Bram)</h2>
              <p className="quiet">
                Bram menyusun naskah 5 slide carousel AIDA, caption Instagram lengkap hashtag #NeverJustOneThing, serta
                prompt visual detail format 4:5 Feed Portrait untuk model openai/gpt-image-2 via OpenCode.
              </p>
              <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
                <button className="btn primary" disabled={run.busy || cascading} onClick={callBram}>
                  Minta Naskah & Prompt AI ke Bram
                </button>
                <button
                  type="button"
                  className="btn mkt-auto-btn"
                  disabled={run.busy || cascading}
                  onClick={runAutoCascade}
                >
                  ⚡ Jalankan Alur Otomatis
                </button>
              </div>
            </div>
          )}

          {/* Stage 4: Vina (Aset Gambar Carousel) */}
          {stage === 4 && (
            <div className="ws-act">
              <h2>5. Aset Gambar Carousel (Vina)</h2>
              <p className="quiet">
                Vina bertugas sebagai Visual Art Director & Image Generation Specialist menggunakan model visual{' '}
                <b>openai/gpt-image-2</b> (OpenCode Zen). Output wajib berupa berkas gambar visual Instagram Feed
                Carousel format 4:5 Portrait (1080 × 1350 px PNG) menggunakan foto produk asli Colorbox.
              </p>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '10px 14px',
                  borderRadius: 6,
                  background: 'rgba(20, 184, 166, 0.08)',
                  border: '1px solid rgba(20, 184, 166, 0.3)',
                  margin: '12px 0',
                }}
              >
                <span style={{ fontSize: 18 }}>🎨</span>
                <div style={{ fontSize: 13 }}>
                  <b>Engine Model Visual:</b> <code>openai/gpt-image-2</code> · <b>Format:</b> 1080 × 1350 px (4:5 Feed Portrait)
                  <br />
                  <span className="quiet">
                    Jika model gagal merender gambar, status eksekusi ditandai <b>GAGAL</b> sebagai konfirmasi kegagalan.
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 12, marginTop: 14, marginBottom: 20, flexWrap: 'wrap' }}>
                <button className="btn primary" disabled={run.busy || cascading} onClick={callVina}>
                  {run.busy && stage === 4 ? 'Sedang Render Gambar...' : 'Minta Render Gambar Carousel ke Vina'}
                </button>
                <a
                  href="/output/carousel_latest/carousel_preview.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn soft"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                >
                  <span>👁️ Buka Live Interactive Preview</span>
                </a>
              </div>

              {/* Display Carousel Cards */}
              <h3 style={{ fontSize: 16, marginTop: 16, marginBottom: 8 }}>
                🎨 5 Slide Gambar Final Feed Carousel (1080 × 1350 px):
              </h3>
              <div className="carousel-grid">
                {CAROUSEL_SLIDES.map((s) => (
                  <div key={s.n} className="carousel-card">
                    <img src={s.img} alt={s.title} className="carousel-img" />
                    <div className="carousel-card-body">
                      <b>{s.title}</b>
                      <small>{s.desc}</small>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Stage 5: Review Manusia (Human-in-the-Loop Quality Gate) */}
          {stage === 5 && (
            <div className="human-review-card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: 18 }}>6. Review Manusia & Quality Gate</h2>
                  <p className="quiet" style={{ margin: '4px 0 0' }}>
                    Evaluasi akhir oleh manusia sebelum materi carousel dijadwalkan atau diterbitkan ke Instagram resmi
                    Colorbox.
                  </p>
                </div>
                <span
                  className="pill"
                  style={{
                    background:
                      decision === 'approved' ? '#10b981' : decision === 'revision' ? '#f59e0b' : 'var(--raised)',
                    color: decision === 'approved' || decision === 'revision' ? 'white' : 'var(--text)',
                    fontWeight: 600,
                  }}
                >
                  Status:{' '}
                  {decision === 'approved'
                    ? 'Disetujui'
                    : decision === 'revision'
                      ? 'Revisi Diperlukan'
                      : decision === 'rejected'
                        ? 'Ditolak'
                        : 'Menunggu Evaluasi'}
                </span>
              </div>

              {/* Visual Presentation */}
              <div style={{ marginTop: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <b style={{ fontSize: 14 }}>Pratinjau Aset Visual (5 Slide 4:5 Portrait):</b>
                  <a
                    href="/output/carousel_latest/carousel_preview.html"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn soft"
                    style={{ fontSize: 12, padding: '4px 10px' }}
                  >
                    Buka Preview Layar Penuh ↗
                  </a>
                </div>
                <div className="carousel-grid">
                  {CAROUSEL_SLIDES.map((s) => (
                    <div key={s.n} className="carousel-card">
                      <img src={s.img} alt={s.title} className="carousel-img" />
                      <div className="carousel-card-body">
                        <b>{s.title}</b>
                        <small>{s.desc}</small>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quality Checklist */}
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 14 }}>
                <b style={{ fontSize: 14 }}>Daftar Periksa Kualitas (Quality Checklist):</b>
                <div className="review-checklist">
                  <label>
                    <input
                      type="checkbox"
                      checked={checklist.catalogFact}
                      onChange={(e) => setChecklist({ ...checklist, catalogFact: e.target.checked })}
                    />
                    <span>
                      <b>Fakta Produk & Harga Resmi:</b> Nama produk dan harga sesuai katalog resmi Colorbox (tanpa diskon
                      gaib atau stok fiktif).
                    </span>
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={checklist.noFabricHallucination}
                      onChange={(e) => setChecklist({ ...checklist, noFabricHallucination: e.target.checked })}
                    />
                    <span>
                      <b>Bebas Halusinasi Bahan:</b> Tidak mencantumkan persentase komposisi kain yang tidak ada di katalog.
                    </span>
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={checklist.ratio45}
                      onChange={(e) => setChecklist({ ...checklist, ratio45: e.target.checked })}
                    />
                    <span>
                      <b>Format & Proporsi Visual:</b> Kanvas 4:5 Feed Portrait (1080 × 1350 px), bebas tombol UI Reels
                      yang menutupi kanvas.
                    </span>
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={checklist.brandTone}
                      onChange={(e) => setChecklist({ ...checklist, brandTone: e.target.checked })}
                    />
                    <span>
                      <b>Tone of Voice & Tagar:</b> Sapaan ramah Colorbox Babes dan tagar resmi #NeverJustOneThing.
                    </span>
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={checklist.officialCTA}
                      onChange={(e) => setChecklist({ ...checklist, officialCTA: e.target.checked })}
                    />
                    <span>
                      <b>CTA Jelas & Terverifikasi:</b> Mengarahkan ke website resmi colorbox.co.id atau toko offline resmi.
                    </span>
                  </label>
                </div>
              </div>

              {/* Review Notes */}
              <label className="field" style={{ marginTop: 8 }}>
                <span>Catatan / Umpan Balik Reviewer</span>
                <textarea
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Tuliskan catatan persetujuan atau poin revisi untuk agen..."
                />
              </label>

              {/* Decision Buttons */}
              <div>
                <b style={{ fontSize: 13, color: 'var(--muted)' }}>Keputusan Reviewer Manusia:</b>
                <div className="decision-group">
                  <button
                    type="button"
                    className="decision-btn"
                    data-selected={decision === 'approved' ? 'approved' : undefined}
                    onClick={() => handleDecision('approved')}
                  >
                    ✅ Setujui & Siap Terbit (Approved)
                  </button>
                  <button
                    type="button"
                    className="decision-btn"
                    data-selected={decision === 'revision' ? 'revision' : undefined}
                    onClick={() => handleDecision('revision')}
                  >
                    ⚠️ Perlu Revisi (Needs Revision)
                  </button>
                  <button
                    type="button"
                    className="decision-btn"
                    data-selected={decision === 'rejected' ? 'rejected' : undefined}
                    onClick={() => handleDecision('rejected')}
                  >
                    ❌ Tolak (Rejected)
                  </button>
                </div>
              </div>

              {/* Approval Banner */}
              {decision === 'approved' && (
                <div className="approval-banner">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 22 }}>🎉</span>
                    <b style={{ fontSize: 15, color: '#047857' }}>
                      STATUS: DISETUJUI & SIAP TAYANG (APPROVED FOR PUBLISH)
                    </b>
                  </div>
                  <p style={{ margin: 0, fontSize: 13, color: '#065f46' }}>
                    Materi kampanye Instagram Feed Carousel telah lolos seluruh parameter quality gate dan diverifikasi
                    terhadap basis data katalog resmi Colorbox.
                  </p>
                  <small style={{ color: '#047857' }}>
                    Ditandatangani oleh Tim Reviewer Manusia pada{' '}
                    {approvedAt ? hhmm(approvedAt) : hhmm(new Date())} WIB.
                  </small>
                </div>
              )}
            </div>
          )}

          {/* Running Status and Streaming Output */}
          <RunBar
            busy={run.busy}
            tools={run.tools}
            writing={!!run.text}
            since={run.startedAt}
            clarify={run.clarify}
            onAnswer={run.answer}
            onStop={run.stop}
            status={run.status}
            error={run.error}
            onRetry={last ?? undefined}
          />
          {run.busy && run.text && (
            <article className="rcard live">
              <div className="rbody">
                <LiveDraft text={stripBlock(run.text)} />
              </div>
            </article>
          )}

          {/* Latest Output or Empty placeholder */}
          {!run.busy &&
            (shown ? (
              <OutputView o={shown} meta={meta(shown)} />
            ) : stage > 0 || !run.error ? (
              <Empty title={`Belum ada hasil di tahap ${STAGES[stage]}`}>
                {stage === 0
                  ? 'Isi formulir brief di atas lalu kirim ke Bimo untuk memulai alur sprint.'
                  : 'Klik tombol di atas untuk menjalankan tahap ini.'}
              </Empty>
            ) : null)}
        </div>

        {/* History Sidebar */}
        {outs.length > 0 && (
          <aside className="ws-hist" aria-label="Riwayat hasil sprint alur marketing">
            <h2>Riwayat Sprint</h2>
            <ul>
              {[...outs].reverse().map((o) => (
                <li key={o.id}>
                  <button
                    type="button"
                    aria-current={shown?.id === o.id ? 'true' : undefined}
                    onClick={() => {
                      setStage(o.stage)
                      setView(o.id)
                    }}
                  >
                    <b>
                      {STAGES[o.stage]} {revCount(o)}
                    </b>
                    <span className="quiet small">
                      {o.agentName} · {o.label} · {hhmm(o.at)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </aside>
        )}
      </div>

      <details className="opts">
        <summary>Opsi Lanjutan</summary>
        <div className="opts-body">
          <Switch
            checked={structured}
            onChange={setStructured}
            label="Hasil terstruktur JSON (eksperimen)"
            hint="Meminta agen menyertakan blok JSON terstruktur di akhir jawaban."
          />
        </div>
      </details>
    </>
  )
}

const mdComponents = {
  a: ({ href, children }: { href?: string; children?: React.ReactNode }) => (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  ),
  img: ({ src, alt }: { src?: string; alt?: string }) => (
    <img
      src={src}
      alt={alt || ''}
      style={{
        maxWidth: '100%',
        borderRadius: 8,
        margin: '12px 0',
        display: 'block',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
      }}
    />
  ),
}

function OutputView({ o, meta }: { o: Output; meta: string }) {
  if (o.parsed.result) {
    return (
      <>
        <MarketingCard r={o.parsed.result} origin="agent" meta={meta} />
        <AnswerDetails text={o.parsed.text} />
        <Provenance refs={o.refs} workflow="marketing" />
      </>
    )
  }

  return (
    <article className="rcard plain-answer">
      <header>
        <b>
          {o.agentName} ({AGENTS[o.stage]?.handle ?? '@agent'})
        </b>
        <span className="pill" style={{ background: AGENTS[o.stage]?.badgeColor, color: 'white' }}>
          {o.label}
        </span>
      </header>
      <div className="rbody md" style={{ lineHeight: 1.6 }}>
        {o.text ? (
          <Markdown remarkPlugins={[remarkGfm]} components={mdComponents}>
            {o.text}
          </Markdown>
        ) : (
          <p className="quiet">Jawaban kosong.</p>
        )}
      </div>
      <Provenance refs={o.refs} workflow="marketing" />
    </article>
  )
}

function Field({
  label,
  err,
  opt,
  children,
}: {
  label: string
  err?: string
  opt?: boolean
  children: React.ReactNode
}) {
  return (
    <label className="field">
      <span>
        {label}
        {opt && (
          <>
            {' '}
            <Opt />
          </>
        )}
      </span>
      {children}
      {err && (
        <small className="err" role="alert">
          {err}
        </small>
      )}
    </label>
  )
}
