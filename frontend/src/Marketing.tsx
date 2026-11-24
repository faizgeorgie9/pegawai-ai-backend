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
  '1. Strategi & Brief (CRE-01)',
  '2. Naskah & Copy (CRE-02)',
  '3. Visual Carousel 4:5 (CRE-03)',
  '4. Video UGC 9:16 (CRE-04)',
  '5. Review Manusia & Quality Gate',
] as const

const KIND: MarketingKind[] = ['brief', 'plan', 'content', 'review', 'revision']
const CHANNELS = ['Instagram', 'TikTok', 'WhatsApp', 'Website / marketplace']
const CONTENT_TYPES = [
  'Feed Carousel (4:5 Portrait)',
  'Video UGC Vertikal (9:16)',
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
  { id: 'cre-01', name: 'CRE-01 Content Strategist', role: 'Content Strategist & Omnichannel Lead', handle: '@contentstrategist', tagline: 'Analisis Brief, Kurasi Produk Katalog & Flow Controller', badgeColor: '#f59e0b', modelInfo: 'DeepSeek V4.1 Flash (OpenCode Go)' },
  { id: 'cre-02', name: 'CRE-02 Content & Copywriter', role: 'Content & Copywriter Lead', handle: '@copywriter', tagline: 'Hook 3 Detik, Storytelling Gen Z, Zero-Text 5 Slide & IG Caption', badgeColor: '#f43f5e', modelInfo: 'DeepSeek V4.1 Flash (OpenCode Go)' },
  { id: 'cre-03', name: 'CRE-03 Graphic & Motion Designer', role: 'Graphic & Motion Designer Lead', handle: '@graphicdesigner', tagline: 'Render 5 Slide Carousel 4:5 (1080x1350 px), 5 Pilar Estetik & Anti-Stretch', badgeColor: '#14b8a6', modelInfo: 'openai/gpt-image-2 (OpenCode Zen)' },
  { id: 'cre-04', name: 'CRE-04 Video & UGC Creator', role: 'Video & UGC Creator Lead', handle: '@videocreator', tagline: 'Naskah, Storyboard & Video UGC Vertikal 9:16 (720x1280 px MP4)', badgeColor: '#6366f1', modelInfo: 'grok-imagine-video / OpenCode API' },
  { id: 'human', name: 'Reviewer Manusia (Ivanagita)', role: 'Final Quality Gate & Human Approval', handle: '@humanreviewer', tagline: 'Quality Gate Level 2, Audit Anti-Halusinasi & Persetujuan Tayang', badgeColor: '#10b981', modelInfo: 'Human-in-the-Loop' },
]

const CAROUSEL_SLIDES = [
  { n: 1, title: 'Slide 1: Cover Hook', desc: 'Split Editorial / Hero Cutout · Formula OOTD Gen Z Standout', img: '/output/carousel_latest/slide_1_cover_hero.png' },
  { n: 2, title: 'Slide 2: Hero Top', desc: 'Craftsmanship Detail · Foto Produk Asli Proporsional Anti-Stretch', img: '/output/carousel_latest/slide_2_hero_top.png' },
  { n: 3, title: 'Slide 3: Bottom Pairing', desc: 'Padu-Padan Bawahan · Siluet Harmonis Tanpa Pengulangan Produk', img: '/output/carousel_latest/slide_3_bottom_pairing.png' },
  { n: 4, title: 'Slide 4: Accessories & Flatlay', desc: 'Cozy Flatlay & Ambient Boutique · Layering Guide Estetik', img: '/output/carousel_latest/slide_4_accessories_flatlay.png' },
  { n: 5, title: 'Slide 5: Outro CTA', desc: 'Paper-Doll Wardrobe Summary · Cek Link Bio #NeverJustOneThing', img: '/output/carousel_latest/slide_5_outro_cta.png' },
]

interface Output {
  id: string
  stage: number
  agentId: string
  agentName: string
  n: number
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
  objective: 'Meningkatkan ketertarikan produk melalui inspirasi styling OOTD Gen Z (Campus Lookbook) di Instagram',
  product: 'Oversize Long Sleeve Checks Blazer (Rp 299.900 - DUSTY OLIVE)',
  channel: 'Instagram',
  contentType: 'Feed Carousel (4:5 Portrait)',
  count: '5',
  audience: 'Remaja/Pemuda Gen Z cewek 13–24 tahun, Colorbox Babes',
  tone: 'Playful, expressive, authentic, fearless, dan mendukung self-expression #NeverJustOneThing',
  keyMessage: 'Formula styling kampus effortless: paduan blazer checks oversize & denim chic yang standout seharian tanpa ribet',
  cta: 'Cek katalog lengkap dan ukuran di website resmi colorbox.co.id atau gerai terdekat',
  period: '18 November - 22 November 2026',
  promoFacts: 'Koleksi New Arrivals Colorbox 2026 (tanpa promo diskon fiktif)',
  forbidden: 'DILARANG teks di atas visual (Zero Text on Visual Rule), dilarang mengarang promo, potongan harga fiktif, stok, atau bahan kain yang tidak tercantum di katalog resmi',
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
    '\nCRE-01 Content Strategist (@contentstrategist), tolong periksa brief ini, rumuskan pilar kampanye #NeverJustOneThing, tentukan arahan produk katalog resmi, dan panggil @cre-02 (@copywriter) untuk menyusun naskah storytelling dan caption.'
  )
}

export default function Marketing() {
  const { bots } = useData()
  const team = teamBots(bots, 'marketing')
  const [agent, setAgent] = useState('cre-01')
  const [pending, setPending] = useState('')
  const dirty = useRef(false)
  const cur = team.find((b) => b.id === agent) ?? team.find((b) => b.id === 'cre-01') ?? team[0]

  return (
    <section className="page ws" data-team="marketing">
      <PageHead
        title="Marketing Workflow (Content & Creative)"
        sub="Alur 4-Pegawai AI Colorbox: CRE-01 (Content Strategist) → CRE-02 (Content & Copywriter) → CRE-03 (Graphic & Motion Designer) → CRE-04 (Video & UGC Creator) → Review Manusia."
        actions={
          <div className="ws-agent" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="mkt-agent-badge" style={{ borderColor: '#10b981' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981' }} />
              Divisi Content & Creative (CRE-01 s/d CRE-04) Aktif
            </span>
          </div>
        }
      />
      {!cur ? (
        <Loading text="Memuat tim Content & Creative Colorbox..." />
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

  // Human Review State (Stage 4)
  const [checklist, setChecklist] = useState({
    catalogFact: true,
    noFabricHallucination: true,
    ratio45: true,
    brandTone: true,
    officialCTA: true,
    zeroTextRule: true,
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
    if (i < 4) return outs.some((o) => o.stage === i)
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
    void executeAgent(0, 'cre-01', briefPrompt(form), 'Strategi & Brief')
  }

  function callCRE02() {
    const prompt =
      'CRE-02 Content & Copywriter (@copywriter), berdasarkan brief dari CRE-01, susun hook 3 detik thumb-stopping, storytelling Gen Z (#NeverJustOneThing), naskah 5 slide carousel dengan aturan Zero-Text on Visual, dan caption Instagram lengkap dengan harga katalog resmi (product-catalog.md). Lalu delegasikan ke CRE-03 (@graphicdesigner).'
    void executeAgent(1, 'cre-02', prompt, 'Naskah & Copy')
  }

  function callCRE03() {
    const prompt =
      'CRE-03 Graphic & Motion Designer (@graphicdesigner), eksekusi arahan visual dan naskah dari CRE-02. Render 5 slide berkas gambar final Instagram Feed Carousel format 4:5 Portrait (1080x1350 px PNG) menggunakan model visual openai/gpt-image-2 (OpenCode Zen) dan foto produk resmi Colorbox tanpa distorsi aspek rasio (contain mode, tidak gepeng) dan bebas dari noise wireframe/dots. Tampilkan pratinjau gambar dan link live interactive preview, lalu delegasikan ke CRE-04 (@videocreator).'
    void executeAgent(2, 'cre-03', prompt, 'Visual Carousel 4:5')
  }

  function callCRE04() {
    const prompt =
      'CRE-04 Video & UGC Creator (@videocreator), rancang konsep dan storyboard detik-demi-detik video vertikal 9:16 (720x1280 px MP4) fit check model asli Colorbox, panduan UGC talent, dan tautan pratinjau video live. Lalu serahkan kembali ke CRE-01 dan Tim Reviewer Manusia.'
    void executeAgent(3, 'cre-04', prompt, 'Video UGC 9:16')
  }

  async function runAutoCascade() {
    if (run.busy || cascading) return
    setTried(true)
    if (Object.keys(errs).length) return

    setCascading(true)
    try {
      // Step 1: CRE-01
      setCascadeMsg('Tahap 1/4: CRE-01 (@contentstrategist) merumuskan brief & strategi pilar...')
      setStage(0)
      const out1 = await executeAgent(0, 'cre-01', briefPrompt(form), 'Strategi & Brief')
      if (!out1) throw new Error('CRE-01 gagal memproses brief.')

      // Step 2: CRE-02
      setCascadeMsg('Tahap 2/4: CRE-02 (@copywriter) menulis storytelling & naskah zero-text...')
      setStage(1)
      const prompt2 =
        'CRE-02 Content & Copywriter (@copywriter), berdasarkan brief dari CRE-01, susun hook 3 detik thumb-stopping, storytelling Gen Z (#NeverJustOneThing), naskah 5 slide carousel dengan aturan Zero-Text on Visual, dan caption Instagram lengkap dengan harga katalog resmi (product-catalog.md). Lalu delegasikan ke CRE-03 (@graphicdesigner).'
      const out2 = await executeAgent(1, 'cre-02', prompt2, 'Naskah & Copy')
      if (!out2) throw new Error('CRE-02 gagal merumuskan naskah copy.')

      // Step 3: CRE-03
      setCascadeMsg('Tahap 3/4: CRE-03 (@graphicdesigner) merender 5 slide visual carousel 4:5...')
      setStage(2)
      const prompt3 =
        'CRE-03 Graphic & Motion Designer (@graphicdesigner), eksekusi arahan visual dan naskah dari CRE-02. Render 5 slide berkas gambar final Instagram Feed Carousel format 4:5 Portrait (1080x1350 px PNG) menggunakan model visual openai/gpt-image-2 (OpenCode Zen) dan foto produk resmi Colorbox tanpa distorsi aspek rasio (contain mode, tidak gepeng) dan bebas dari noise wireframe/dots. Tampilkan pratinjau gambar dan link live interactive preview, lalu delegasikan ke CRE-04 (@videocreator).'
      const out3 = await executeAgent(2, 'cre-03', prompt3, 'Visual Carousel 4:5')
      if (!out3) throw new Error('CRE-03 gagal merender gambar.')

      // Step 4: CRE-04
      setCascadeMsg('Tahap 4/4: CRE-04 (@videocreator) merender konsep video vertikal UGC 9:16...')
      setStage(3)
      const prompt4 =
        'CRE-04 Video & UGC Creator (@videocreator), rancang konsep dan storyboard detik-demi-detik video vertikal 9:16 (720x1280 px MP4) fit check model asli Colorbox, panduan UGC talent, dan tautan pratinjau video live. Lalu serahkan kembali ke CRE-01 dan Tim Reviewer Manusia.'
      const out4 = await executeAgent(3, 'cre-04', prompt4, 'Video UGC 9:16')
      if (!out4) throw new Error('CRE-04 gagal memproduksi video UGC.')

      // Finished! Navigate to Stage 4 (Review Manusia)
      setCascadeMsg('Alur selesai! Membuka gerbang Review Manusia (Ivanagita)...')
      setStage(4)
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

      {/* Stepper with 5 Stages */}
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

          {/* Stage 0: Brief & Strategi (CRE-01) */}
          {stage === 0 && (
            <form className="ws-form" onSubmit={submitBrief} noValidate>
              <div className="ws-form-head">
                <h2>1. Brief & Perencanaan Kampanye (CRE-01)</h2>
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
                <Field label="Produk Acuan (Katalog Resmi 1.206 Produk)" err={tried ? errs.product : ''}>
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
                  Kirim Brief ke CRE-01 (Content Strategist)
                </button>
                <button
                  type="button"
                  className="btn mkt-auto-btn"
                  disabled={run.busy || cascading}
                  onClick={runAutoCascade}
                >
                  ⚡ Jalankan Alur Lengkap Otomatis (CRE-01 s/d CRE-04)
                </button>
              </div>
            </form>
          )}

          {/* Stage 1: CRE-02 (Naskah & Copy) */}
          {stage === 1 && (
            <div className="ws-act">
              <h2>2. Naskah Storytelling & Copywriting (CRE-02)</h2>
              <p className="quiet">
                CRE-02 menyusun hook 3 detik thumb-stopping, storytelling Gen Z (#NeverJustOneThing), naskah 5 slide
                carousel dengan aturan ketat <b>Zero-Text on Visual</b> (teks disimpan pada caption Instagram), SKU, dan
                harga katalog resmi (product-catalog.md).
              </p>
              <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
                <button className="btn primary" disabled={run.busy || cascading} onClick={callCRE02}>
                  Minta Naskah & Copy ke CRE-02
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

          {/* Stage 2: CRE-03 (Visual Carousel 4:5) */}
          {stage === 2 && (
            <div className="ws-act">
              <h2>3. Desain Visual Carousel 4:5 (CRE-03)</h2>
              <p className="quiet">
                CRE-03 bertindak sebagai Visual Art Director & Canvas Specialist menggunakan model visual{' '}
                <b>openai/gpt-image-2</b> (OpenCode Zen). Output berupa berkas gambar visual Instagram Feed Carousel format
                4:5 Portrait (1080 × 1350 px PNG) yang estetik ala Pinterest, menjaga foto produk asli tidak terdistorsi (contain mode),
                dan bebas dari teks kanvas yang mengganggu.
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
                    5 Pilar Visual: Split Editorial, Cozy Fur Flatlay, Detail Zoom Callouts, Ambient Boutique, Paper-Doll Wardrobe.
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 12, marginTop: 14, marginBottom: 20, flexWrap: 'wrap' }}>
                <button className="btn primary" disabled={run.busy || cascading} onClick={callCRE03}>
                  {run.busy && stage === 2 ? 'Sedang Render Gambar...' : 'Minta Render Visual Carousel ke CRE-03'}
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

          {/* Stage 3: CRE-04 (Video UGC 9:16) */}
          {stage === 3 && (
            <div className="ws-act">
              <h2>4. Produksi Video UGC Vertikal 9:16 (CRE-04)</h2>
              <p className="quiet">
                CRE-04 merancang konsep dan storyboard detik-demi-detik video vertikal 9:16 (720 × 1280 px MP4) fit check
                model asli Colorbox, panduan UGC talent berkamera HP, transisi ritmis, serta naskah hook video Reels/TikTok.
              </p>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '10px 14px',
                  borderRadius: 6,
                  background: 'rgba(99, 102, 241, 0.08)',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  margin: '12px 0',
                }}
              >
                <span style={{ fontSize: 18 }}>🎬</span>
                <div style={{ fontSize: 13 }}>
                  <b>Engine Model Video:</b> <code>grok-imagine-video / OpenCode API</code> · <b>Format:</b> 9:16 Vertikal (720 × 1280 px MP4)
                  <br />
                  <span className="quiet">
                    Durasi: 5–15 Detik High-Definition Fit Check Model Cewek Asli Colorbox.
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 12, marginTop: 14, marginBottom: 20, flexWrap: 'wrap' }}>
                <button className="btn primary" disabled={run.busy || cascading} onClick={callCRE04}>
                  {run.busy && stage === 3 ? 'Sedang Memproses Video UGC...' : 'Minta Konsep & Video UGC ke CRE-04'}
                </button>
                <a
                  href="/output/carousel_latest/ugc_video.mp4"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn soft"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                >
                  <span>▶️ Putar Video UGC (MP4)</span>
                </a>
              </div>

              <div
                style={{
                  maxWidth: 320,
                  margin: '16px 0',
                  borderRadius: 12,
                  overflow: 'hidden',
                  border: '1px solid var(--border)',
                  background: 'var(--raised)',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
                }}
              >
                <video
                  src="/output/carousel_latest/ugc_video.mp4"
                  controls
                  loop
                  muted
                  playsInline
                  style={{ width: '100%', display: 'block', maxHeight: 480, objectFit: 'cover' }}
                />
                <div style={{ padding: 12 }}>
                  <b style={{ fontSize: 13, display: 'block' }}>Video UGC Vertikal 9:16 (Colorbox Model)</b>
                  <small style={{ color: 'var(--muted)' }}>Output resmi dari CRE-04 Video & UGC Creator</small>
                </div>
              </div>
            </div>
          )}

          {/* Stage 4: Review Manusia (Ivanagita) */}
          {stage === 4 && (
            <div className="human-review-card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: 18 }}>5. Review Manusia & Quality Gate Level 2</h2>
                  <p className="quiet" style={{ margin: '4px 0 0' }}>
                    Evaluasi akhir oleh Marketing Specialist (Ivanagita) sebelum materi carousel dan video UGC dipublikasikan.
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

              {/* Video UGC Preview in Human Review */}
              <div style={{ marginTop: 16 }}>
                <b style={{ fontSize: 14 }}>Aset Video UGC Vertikal 9:16:</b>
                <div style={{ marginTop: 8, display: 'flex', gap: 16, alignItems: 'center' }}>
                  <a
                    href="/output/carousel_latest/ugc_video.mp4"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn soft"
                    style={{ fontSize: 12, padding: '6px 12px' }}
                  >
                    ▶️ Tonton Video UGC (MP4) ↗
                  </a>
                  <span className="quiet small">Format: 9:16 Vertikal (720 × 1280 px MP4)</span>
                </div>
              </div>

              {/* Quality Checklist */}
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 14, marginTop: 16 }}>
                <b style={{ fontSize: 14 }}>Daftar Periksa Kualitas (Quality Checklist Level 2):</b>
                <div className="review-checklist">
                  <label>
                    <input
                      type="checkbox"
                      checked={checklist.catalogFact}
                      onChange={(e) => setChecklist({ ...checklist, catalogFact: e.target.checked })}
                    />
                    <span>
                      <b>Fakta Produk & Harga Resmi:</b> Nama produk dan harga sesuai katalog resmi Colorbox (tanpa diskon fiktif).
                    </span>
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={checklist.zeroTextRule}
                      onChange={(e) => setChecklist({ ...checklist, zeroTextRule: e.target.checked })}
                    />
                    <span>
                      <b>Zero-Text on Visual Rule:</b> Tidak ada teks promosi/harga yang menumpuk di atas kanvas gambar; seluruh copy tersimpan di caption.
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
                      <b>Format & Proporsi Visual:</b> Kanvas 4:5 Feed Portrait (1080 × 1350 px), garmen tidak terdistorsi (contain mode).
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
                <span>Catatan / Umpan Balik Reviewer (Ivanagita)</span>
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
                    Materi kampanye Instagram Feed Carousel dan Video UGC telah lolos seluruh parameter quality gate dan diverifikasi
                    terhadap basis data katalog resmi Colorbox.
                  </p>
                  <small style={{ color: '#047857' }}>
                    Ditandatangani oleh Ivanagita (Marketing Specialist) pada{' '}
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
                  ? 'Isi formulir brief di atas lalu kirim ke CRE-01 untuk memulai alur sprint.'
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
