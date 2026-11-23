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
import { ErrorLine, I, Icon } from './ui'
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

// The stepper shows short, everyday words; STAGES stays as the agent's stage id.
const STAGE_LABELS = ['Permintaan', 'Strategi', 'Riset katalog', 'Naskah', 'Gambar', 'Persetujuan'] as const

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
const CONTENT_TYPE_LABELS: Record<string, string> = {
  'Feed Carousel (4:5 Portrait)': 'Carousel Instagram (4:5)',
  'Caption Instagram': 'Caption Instagram',
  'Copy promosi': 'Teks promosi',
  Headline: 'Judul',
  'Deskripsi produk': 'Deskripsi produk',
  'Skrip Reels': 'Naskah Reels',
}

interface AgentInfo {
  id: string
  name: string
  role: string
  tagline: string
  badgeColor: string
  modelInfo: string
}

const AGENTS: AgentInfo[] = [
  { id: 'bimo', name: 'Bimo', role: 'Pengatur tugas', tagline: 'Menyiapkan permintaan dan membagi tugas', badgeColor: 'var(--c-amber)', modelInfo: 'DeepSeek V4.1 Flash' },
  { id: 'meda', name: 'Meda', role: 'Penyusun strategi', tagline: 'Menentukan audiens dan tiga pilihan konsep', badgeColor: 'var(--c-rose)', modelInfo: 'DeepSeek V4.1 Flash' },
  { id: 'raka', name: 'Raka', role: 'Peneliti katalog', tagline: 'Memeriksa produk, ukuran, dan foto', badgeColor: 'var(--c-sky)', modelInfo: 'DeepSeek V4.1 Flash' },
  { id: 'bram', name: 'Bram', role: 'Penulis naskah', tagline: 'Menulis naskah lima slide dan caption', badgeColor: 'var(--c-indigo)', modelInfo: 'DeepSeek V4.1 Flash' },
  { id: 'vina', name: 'Vina', role: 'Perancang gambar', tagline: 'Membuat lima gambar 1080 × 1350 px', badgeColor: 'var(--c-teal)', modelInfo: 'openai/gpt-image-2' },
  { id: 'human', name: 'Anda', role: 'Pemeriksa akhir', tagline: 'Memeriksa hasil dan memberi persetujuan', badgeColor: 'var(--c-green)', modelInfo: 'Diperiksa manusia' },
]

const CAROUSEL_SLIDES = [
  { n: 1, title: 'Slide 1: Pembuka', desc: 'Effortless Campus Rebel · Formula OOTD Ngampus Standout', img: '/output/carousel_latest/slide_1_cover_hero.png' },
  { n: 2, title: 'Slide 2: Atasan', desc: 'Contrast Stitch Chambray Shirt (Rp 140.900) · Dark Blue', img: '/output/carousel_latest/slide_2_hero_top.png' },
  { n: 3, title: 'Slide 3: Bawahan', desc: 'High Waist Barrel Denim Pants (Rp 329.900) · Black', img: '/output/carousel_latest/slide_3_bottom_pairing.png' },
  { n: 4, title: 'Slide 4: Aksesori', desc: 'Colorbox x Liunic Ecru Tote & Layering Advice', img: '/output/carousel_latest/slide_4_accessories_flatlay.png' },
  { n: 5, title: 'Slide 5: Ajakan', desc: 'Temukan Fit Favoritmu di colorbox.co.id #NeverJustOneThing', img: '/output/carousel_latest/slide_5_outro_cta.png' },
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

// Plain words for the form; FIELDS stays as the brief sent to the agent.
const FIELD_LABELS: Partial<Record<keyof Form, string>> = {
  tone: 'Gaya bahasa merek',
  keyMessage: 'Pesan utama',
  cta: 'Ajakan bertindak',
}

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
  const { bots, loadState, error, reload } = useData()
  const team = teamBots(bots, 'marketing')
  const [agent, setAgent] = useState('bimo')
  const [pending, setPending] = useState('')
  const dirty = useRef(false)
  const cur = team.find((b) => b.id === agent) ?? team.find((b) => b.id === 'bimo') ?? team.find((b) => b.id === 'bram') ?? team.find((b) => b.id === 'rian') ?? team[0]

  return (
    <section className="page ws" data-team="marketing">
      <PageHead
        title="Alur kerja marketing"
        sub="Lima pegawai AI bekerja berurutan. Periksa hasilnya, lalu setujui sebelum tayang."
        actions={cur ? <span className="pill ok">Alur 5 pegawai AI aktif</span> : undefined}
      />
      {!cur ? (
        loadState === 'error' ? (
          <ErrorLine text={error} onRetry={reload} />
        ) : loadState === 'ok' ? (
          <Empty title="Belum ada agen marketing">Alur ini butuh agen di tim marketing. Buat agennya di halaman Agen.</Empty>
        ) : (
          <Loading text="Memuat data marketing Colorbox..." />
        )
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
      setCascadeMsg('Langkah 1 dari 5: Bimo menyiapkan permintaan dan membagi tugas...')
      setStage(0)
      const bimoOut = await executeAgent(0, 'bimo', briefPrompt(form), 'Brief & Kanban')
      if (!bimoOut) throw new Error('Bimo gagal memproses brief.')

      // Step 2: Meda
      setCascadeMsg('Langkah 2 dari 5: Meda menyusun strategi dan tiga pilihan konsep...')
      setStage(1)
      const medaPrompt =
        'Meda (@marketingstrategist), berdasarkan brief dari Bimo, rumuskan strategi kampanye, target audiens Gen Z, 3 pilar gaya (Urban/Romantic/Chic), dan pilih produk katalog Colorbox resmi. Buat 3 opsi konsep konten (Opsi A/B/C) dengan rekomendasi utama pada Opsi A, lalu delegasikan ke Raka (@researcher).'
      const medaOut = await executeAgent(1, 'meda', medaPrompt, 'Strategi & Konsep')
      if (!medaOut) throw new Error('Meda gagal merumuskan konsep.')

      // Step 3: Raka
      setCascadeMsg('Langkah 3 dari 5: Raka mencocokkan produk dengan katalog dan ukuran...')
      setStage(2)
      const rakaPrompt =
        'Raka (@researcher), validasi produk dari konsep Meda ke katalog resmi Colorbox (product-catalog.md), sertakan harga normal/diskon Rp, bedah panduan ukuran cm (lingkar dada, pinggang, panjang) dari product-size-reference.md, cek ketersediaan foto di images/, dan buat Creative Research Brief 5 slide. Lalu teruskan ke Bram (@sketchwriter).'
      const rakaOut = await executeAgent(2, 'raka', rakaPrompt, 'Riset Katalog & Ukuran')
      if (!rakaOut) throw new Error('Raka gagal memvalidasi katalog.')

      // Step 4: Bram
      setCascadeMsg('Langkah 4 dari 5: Bram menulis naskah dan arahan gambar...')
      setStage(3)
      const bramPrompt =
        'Bram (@sketchwriter), rancang naskah kreatif dan master AI prompt untuk postingan Instagram tanpa menggunakan template baku (JANGAN GUNAKAN TEMPLATE / ZERO RIGID FORMULAS). Buat konsep unik dari nol sesuai produk terpilih dari Raka, susun on-screen micro-copy minimalis (1-2 kata, tanpa harga), caption Instagram lengkap hashtag #NeverJustOneThing dan harga resmi katalog, serta AI Visual Generation Prompt yang sangat detail, fotorealistik, dan kaya arahan artistik (lighting, angle 4:5 Feed Portrait, lensa 35mm, latar arsitektur nyata, dan model styling) untuk model openai/gpt-image-2 via OpenCode. Lalu serahkan ke Vina (@visualcarousel).'
      const bramOut = await executeAgent(3, 'bram', bramPrompt, 'Naskah & Prompt AI')
      if (!bramOut) throw new Error('Bram gagal menulis naskah.')

      // Step 5: Vina
      setCascadeMsg('Langkah 5 dari 5: Vina membuat lima gambar carousel...')
      setStage(4)
      const vinaPrompt =
        'Vina (@visualcarousel), eksekusi arahan visual dan master prompt dari Bram secara bespoke tanpa template baku. Render 5 slide berkas gambar final Instagram Feed Carousel format 4:5 Portrait (1080x1350 px PNG) menggunakan model visual openai/gpt-image-2 (OpenCode Zen) dan foto produk resmi Colorbox tanpa distorsi aspek rasio (contain mode, tidak gepeng) dan bebas dari noise wireframe/dots. Tampilkan pratinjau gambar dan link live interactive preview, lalu serahkan ke Bimo dan Tim Reviewer Manusia.'
      const vinaOut = await executeAgent(4, 'vina', vinaPrompt, 'Aset Gambar Carousel')
      if (!vinaOut) throw new Error('Vina gagal merender gambar.')

      // Finished! Navigate to Stage 5 (Review Manusia)
      setCascadeMsg('Alur selesai. Membuka tahap persetujuan...')
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
            Semua pegawai AI memakai percakapan yang sama ({sid.slice(0, 8)}...).
          </span>
        </div>
      )}

      {/* Stepper with 6 Stages */}
      <ol className="stepper" aria-label="Tahap kerja alur marketing">
        {STAGES.map((_, i) => (
          <li key={STAGE_LABELS[i]} data-link={i > 0 && stageDone(i - 1) ? 'done' : undefined}>
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
                {STAGE_LABELS[i]}
                {stageDone(i) && <span className="sr">, selesai</span>}
              </span>
            </button>
          </li>
        ))}
      </ol>

      {/* Auto-cascade Banner if running */}
      {cascading && (
        <div className="ok-line ws-banner">
          <div className="ws-row">
            <Icon d={I.log} size={18} />
            <div>
              <b>Alur otomatis sedang berjalan</b>
              <p className="small tight">
                {cascadeMsg}
              </p>
            </div>
          </div>
          <button type="button" className="btn soft" onClick={() => run.stop()}>
            Hentikan
          </button>
        </div>
      )}

      <div className="ws-grid" data-solo={outs.length === 0 || undefined}>
        <div className="ws-main">
          {/* Agent Badge Header for current Stage */}
          <div className="ws-agent-head">
            <div className="ws-row">
              <span className="ws-agent-av" style={{ '--agent-c': currentAgent.badgeColor } as React.CSSProperties} aria-hidden="true">
                {currentAgent.name.slice(0, 2).toUpperCase()}
              </span>
              <div>
                <div className="ws-row ws-row-tight">
                  <b>{currentAgent.name}</b>
                  <span className="pill">{currentAgent.role}</span>
                </div>
                <small className="quiet">{currentAgent.tagline}</small>
              </div>
            </div>
            <span className="quiet small ws-agent-model">
              Model AI: <b>{currentAgent.modelInfo}</b>
            </span>
          </div>

          {/* Stage 0: Brief & PM (Bimo) */}
          {stage === 0 && (
            <form className="ws-form" onSubmit={submitBrief} noValidate>
              <div className="ws-form-head">
                <h2>1. Permintaan dan pembagian tugas (Bimo)</h2>
                <button type="button" className="btn soft" onClick={() => setForm(COLORBOX_SAMPLE)}>
                  Isi contoh Colorbox
                </button>
              </div>

              <div className="fgrid">
                <Field label="Tujuan kampanye" err={tried ? errs.objective : ''}>
                  <input
                    value={form.objective}
                    onChange={(e) => setForm({ ...form, objective: e.target.value })}
                    aria-invalid={tried && !!errs.objective}
                    placeholder="Contoh: Inspirasi pakaian kuliah yang santai tapi rapi di Instagram"
                  />
                </Field>
                <Field label="Produk acuan (katalog resmi, 1.216 produk)" err={tried ? errs.product : ''}>
                  <input
                    value={form.product}
                    onChange={(e) => setForm({ ...form, product: e.target.value })}
                    aria-invalid={tried && !!errs.product}
                    placeholder="Contoh: Oversize Long Sleeve Checks Blazer (Rp 299.900)"
                  />
                  <div className="cat-pick">
                    <div className="quiet small ws-row ws-row-tight">
                      <Icon d={I.check} size={14} />
                      <span>Produk dari katalog resmi. Klik untuk memakai sebagai acuan.</span>
                    </div>
                    <div className="cat-chips">
                      {VERIFIED_CATALOG_SUGGESTIONS.map((item) => (
                        <button
                          key={item.name}
                          type="button"
                          className={form.product.includes(item.name) ? 'pill ok cat-chip' : 'pill cat-chip'}
                          onClick={() => setForm({ ...form, product: `${item.name} (${item.price} - ${item.color})` })}
                        >
                          {item.name} · {item.price}
                        </button>
                      ))}
                    </div>
                  </div>
                </Field>
                <Field label="Kanal media sosial" err={tried ? errs.channel : ''}>
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
                <Field label="Format konten" err={tried ? errs.contentType : ''}>
                  <select
                    value={form.contentType}
                    onChange={(e) => setForm({ ...form, contentType: e.target.value })}
                    aria-invalid={tried && !!errs.contentType}
                  >
                    <option value="">Pilih format</option>
                    {CONTENT_TYPES.map((c) => (
                      <option key={c} value={c}>
                        {CONTENT_TYPE_LABELS[c] ?? c}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Jumlah slide" err={tried ? errs.count : ''}>
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
                <summary>Pengaturan tambahan (audiens, nada bahasa, ajakan, dll.)</summary>
                <div className="fgrid opts-body">
                  {FIELDS.map(([k, l]) => (
                    <Field key={k} label={FIELD_LABELS[k] ?? l}>
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

              <div className="form-actions ws-actions">
                <button className="btn primary" type="submit" disabled={run.busy || cascading}>
                  Kirim permintaan ke Bimo
                </button>
                <button type="button" className="btn soft" disabled={run.busy || cascading} onClick={runAutoCascade}>
                  Jalankan semua langkah
                </button>
              </div>
            </form>
          )}

          {/* Stage 1: Meda (Strategi & Konsep) */}
          {stage === 1 && (
            <div className="ws-act">
              <h2>2. Strategi dan konsep (Meda)</h2>
              <p className="quiet">
                Meda membaca permintaan dari Bimo, menentukan gaya kampanye, lalu menyiapkan tiga pilihan konsep dengan
                produk dari katalog resmi Colorbox.
              </p>
              <div className="ws-actions">
                <button className="btn primary" disabled={run.busy || cascading} onClick={callMeda}>
                  Minta strategi dan konsep
                </button>
                <button type="button" className="btn soft" disabled={run.busy || cascading} onClick={runAutoCascade}>
                  Jalankan semua langkah
                </button>
              </div>
            </div>
          )}

          {/* Stage 2: Raka (Riset Katalog & Ukuran) */}
          {stage === 2 && (
            <div className="ws-act">
              <h2>3. Riset katalog dan ukuran (Raka)</h2>
              <p className="quiet">
                Raka mencocokkan produk dengan katalog resmi Colorbox (1.206 produk), membaca panduan ukuran dalam cm,
                memeriksa foto produk, lalu menyusun bahan riset untuk naskah.
              </p>
              <div className="ws-actions">
                <button className="btn primary" disabled={run.busy || cascading} onClick={callRaka}>
                  Minta riset katalog
                </button>
                <button type="button" className="btn soft" disabled={run.busy || cascading} onClick={runAutoCascade}>
                  Jalankan semua langkah
                </button>
              </div>
            </div>
          )}

          {/* Stage 3: Bram (Naskah & Prompt AI) */}
          {stage === 3 && (
            <div className="ws-act">
              <h2>4. Naskah dan arahan gambar (Bram)</h2>
              <p className="quiet">
                Bram menulis naskah lima slide, caption Instagram dengan tagar resmi #NeverJustOneThing, dan arahan visual
                format 4:5 untuk pembuat gambar.
              </p>
              <div className="ws-actions">
                <button className="btn primary" disabled={run.busy || cascading} onClick={callBram}>
                  Minta naskah dan arahan gambar
                </button>
                <button type="button" className="btn soft" disabled={run.busy || cascading} onClick={runAutoCascade}>
                  Jalankan semua langkah
                </button>
              </div>
            </div>
          )}

          {/* Stage 4: Vina (Aset Gambar Carousel) */}
          {stage === 4 && (
            <div className="ws-act">
              <h2>5. Gambar carousel (Vina)</h2>
              <p className="quiet">
                Vina membuat gambar carousel Instagram ukuran 1080 × 1350 px (4:5) memakai foto produk asli Colorbox.
                Hasilnya lima berkas gambar yang siap diunggah.
              </p>
              <div className="suggest ws-suggest">
                <div className="small">
                  <b>Model gambar:</b> <code>openai/gpt-image-2</code> · <b>Ukuran:</b> 1080 × 1350 px (4:5)
                  <br />
                  <span className="quiet">Kalau gambar gagal dibuat, statusnya ditandai gagal.</span>
                </div>
              </div>

              <div className="ws-actions ws-actions-after">
                <button className="btn primary" disabled={run.busy || cascading} onClick={callVina}>
                  {run.busy && stage === 4 ? 'Sedang membuat gambar...' : 'Minta gambar carousel'}
                </button>
                <a
                  href="/output/carousel_latest/carousel_preview.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn soft"
                >
                  Lihat pratinjau
                </a>
              </div>

              {/* Display Carousel Cards */}
              <h3 style={{ fontSize: 16, marginTop: 16, marginBottom: 8 }}>5 gambar carousel (1080 × 1350 px)</h3>
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
              <div className="ws-row ws-row-split">
                <div>
                  <h2 className="tight">6. Pemeriksaan dan persetujuan Anda</h2>
                  <p className="quiet tight">
                    Periksa hasil akhir sebelum carousel dijadwalkan atau diterbitkan di Instagram Colorbox.
                  </p>
                </div>
                <span
                  className={`pill ${
                    decision === 'approved' ? 'ok' : decision === 'revision' ? 'warn' : decision === 'rejected' ? 'bad' : ''
                  }`}
                >
                  Status:{' '}
                  {decision === 'approved'
                    ? 'Disetujui'
                    : decision === 'revision'
                      ? 'Perlu revisi'
                      : decision === 'rejected'
                        ? 'Ditolak'
                        : 'Menunggu pemeriksaan'}
                </span>
              </div>

              {/* Visual Presentation */}
              <div className="ws-block">
                <div className="ws-row ws-row-split">
                  <b className="small">Pratinjau 5 gambar (4:5):</b>
                  <a
                    href="/output/carousel_latest/carousel_preview.html"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn soft"
                  >
                    Buka pratinjau layar penuh
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
              <div className="ws-rule">
                <b className="small">Daftar periksa sebelum terbit:</b>
                <div className="review-checklist">
                  <label>
                    <input
                      type="checkbox"
                      checked={checklist.catalogFact}
                      onChange={(e) => setChecklist({ ...checklist, catalogFact: e.target.checked })}
                    />
                    <span>
                      <b>Fakta produk dan harga resmi:</b> Nama produk dan harga sesuai katalog resmi Colorbox (tanpa
                      diskon karangan atau stok fiktif).
                    </span>
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={checklist.noFabricHallucination}
                      onChange={(e) => setChecklist({ ...checklist, noFabricHallucination: e.target.checked })}
                    />
                    <span>
                      <b>Bahan sesuai katalog:</b> Tidak menyebut bahan atau komposisi kain yang tidak tercantum di
                      katalog.
                    </span>
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={checklist.ratio45}
                      onChange={(e) => setChecklist({ ...checklist, ratio45: e.target.checked })}
                    />
                    <span>
                      <b>Ukuran dan proporsi gambar:</b> Kanvas 4:5 (1080 × 1350 px), tanpa tombol antarmuka Reels yang
                      menutupi gambar.
                    </span>
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={checklist.brandTone}
                      onChange={(e) => setChecklist({ ...checklist, brandTone: e.target.checked })}
                    />
                    <span>
                      <b>Gaya bahasa dan tagar:</b> Sapaan ramah Colorbox Babes dan tagar resmi #NeverJustOneThing.
                    </span>
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={checklist.officialCTA}
                      onChange={(e) => setChecklist({ ...checklist, officialCTA: e.target.checked })}
                    />
                    <span>
                      <b>Ajakan yang jelas:</b> Mengarahkan ke website resmi colorbox.co.id atau toko resmi.
                    </span>
                  </label>
                </div>
              </div>

              {/* Review Notes */}
              <label className="field" style={{ marginTop: 8 }}>
                <span>Catatan untuk tim</span>
                <textarea
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Tulis catatan persetujuan atau poin revisi untuk pegawai AI..."
                />
              </label>

              {/* Decision Buttons */}
              <div>
                <b className="small quiet">Keputusan Anda:</b>
                <div className="decision-group">
                  <button
                    type="button"
                    className="decision-btn"
                    data-selected={decision === 'approved' ? 'approved' : undefined}
                    onClick={() => handleDecision('approved')}
                  >
                    Setujui
                  </button>
                  <button
                    type="button"
                    className="decision-btn"
                    data-selected={decision === 'revision' ? 'revision' : undefined}
                    onClick={() => handleDecision('revision')}
                  >
                    Minta revisi
                  </button>
                  <button
                    type="button"
                    className="decision-btn"
                    data-selected={decision === 'rejected' ? 'rejected' : undefined}
                    onClick={() => handleDecision('rejected')}
                  >
                    Tolak
                  </button>
                </div>
              </div>

              {/* Approval Banner */}
              {decision === 'approved' && (
                <div className="approval-banner">
                  <div className="ws-row ws-row-tight">
                    <Icon d={I.check} size={20} />
                    <b>Disetujui dan siap tayang</b>
                  </div>
                  <p className="small tight">
                    Carousel ini sudah lolos semua pemeriksaan dan cocok dengan katalog resmi Colorbox.
                  </p>
                  <small>
                    Disetujui pada {approvedAt ? hhmm(approvedAt) : hhmm(new Date())} WIB.
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
              <Empty title={`Belum ada hasil di tahap ${STAGE_LABELS[stage]}`}>
                {stage === 0
                  ? 'Isi formulir di atas, lalu kirim ke Bimo untuk memulai.'
                  : 'Klik tombol di atas untuk menjalankan tahap ini.'}
              </Empty>
            ) : null)}
        </div>

        {/* History Sidebar */}
        {outs.length > 0 && (
          <aside className="ws-hist" aria-label="Riwayat hasil alur marketing">
            <h2>Riwayat hasil</h2>
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
                      {STAGE_LABELS[o.stage]} {revCount(o)}
                    </b>
                    <span className="quiet small">
                      {o.agentName} · {hhmm(o.at)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </aside>
        )}
      </div>

      <details className="opts">
        <summary>Pengaturan tambahan</summary>
        <div className="opts-body">
          <Switch
            checked={structured}
            onChange={setStructured}
            label="Hasil terstruktur untuk mesin (eksperimen)"
            hint="Meminta pegawai AI menyertakan data terstruktur di akhir jawaban."
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
      className="md-img"
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
        <b>{o.agentName}</b>
        <span className="pill">{STAGE_LABELS[o.stage]}</span>
      </header>
      <div className="rbody md">
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
