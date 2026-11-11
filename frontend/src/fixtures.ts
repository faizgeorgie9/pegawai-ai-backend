import type { CsResult, MarketingResult } from './results'

// Requirement examples E-01 to E-05 (Marketing) are designs, not real agent output. Shown only behind "Lihat contoh",
// always with the badge "Contoh data", never mixed with real results. Product: Colorbox graphic tee (dummy).
export const MARKETING_EXAMPLES: { id: string; title: string; result: MarketingResult }[] = [
  {
    id: 'E-02',
    title: 'Brief dan klarifikasi',
    result: {
      kind: 'brief',
      fields: { tujuan: 'Memperkenalkan kaos grafis baru', produk: 'Regular Fit Short Sleeve Graphic T-Shirt (dummy)', kanal: 'Instagram', tipe_konten: 'Caption', jumlah_output: '3', nada: 'Santai, jelas, ringkas' },
      assumptions: ['Nada santai, jelas, ringkas (Assumptions)', 'Audiens anak muda perkotaan'],
      questions: ['Apakah ada promo yang boleh disebut?', 'Periode tayang berapa lama?'],
      ready: false,
    },
  },
  {
    id: 'E-03',
    title: 'Ide dan kalender',
    result: {
      kind: 'plan',
      creative_brief: 'Mengenalkan satu kaos grafis lewat tiga suasana pemakaian sehari-hari, nada santai.',
      ideas: [
        { title: 'Satu kaos, tiga suasana', reason: 'Gaya santai harian', classification: 'assumptions' },
        { title: 'Grafis yang bercerita', reason: 'Fokus pada desain', classification: 'assumptions' },
      ],
      calendar: [
        { date: '1 Des', channel: 'Instagram', type: 'Caption', idea: 'Satu kaos, tiga suasana', message: 'Satu kaos untuk semua suasana', cta: 'Lihat katalog' },
        { date: '7 Des', channel: 'Instagram', type: 'Caption', idea: 'Grafis yang bercerita', message: 'Grafis yang bikin orang bertanya', cta: 'Intip katalog' },
        { date: '14 Des', channel: 'Instagram', type: 'Caption', idea: 'Satu kaos, tiga suasana', message: 'Pakai ke mana saja', cta: 'Cek ukuran' },
      ],
    },
  },
  {
    id: 'E-01',
    title: 'Caption Instagram',
    result: {
      kind: 'content',
      type: 'Caption Instagram',
      items: [{ text: 'Satu kaos, tiga suasana. Regular Fit Short Sleeve Graphic T-Shirt siap menemani harimu. [teks contoh, bukan output nyata]', alt_angle: 'fokus pada grafis', classification: 'assumptions' }],
      sources: ['Halaman katalog Colorbox, dicek 6 Nov 2026'],
      assumptions: ['Nada santai, jelas, ringkas'],
      warnings: ['Tidak ada klaim harga atau promo yang diverifikasi', 'Hashtag belum diperiksa terhadap klaim terlarang'],
    },
  },
  {
    id: 'E-04',
    title: 'Review brand dan konten',
    result: {
      kind: 'review',
      findings: ['Kalimat pembuka terlalu umum.'],
      evidence: ['"siap menemani harimu" tidak menyebut desain grafis.'],
      recommendations: ['Sebut elemen grafis dan ajak ke katalog.'],
      scores: { accuracy: 4, relevance: 4, brand: 3, consistency: 4, knowledge: 4, instruction: 5, completeness: 4, error_handling: 4, human_review: 4 },
    },
  },
  {
    id: 'E-05',
    title: 'Revisi dari feedback',
    result: {
      kind: 'revision',
      before: 'Satu kaos, tiga suasana. Regular Fit Short Sleeve Graphic T-Shirt siap menemani harimu.',
      after: 'Satu kaos, tiga suasana. Regular Fit Short Sleeve Graphic T-Shirt dengan grafis yang bikin orang bertanya. Intip katalognya.',
      feedback_applied: ['Kesesuaian brand 3: sebut grafis'],
      change_log: ['Kalimat pembuka diganti: menyebut grafis.', 'CTA ditambahkan: ajakan ke katalog.', 'Dipertahankan: nama produk dan nada santai.'],
      open_issues: ['Hashtag belum diperiksa.'],
    },
  },
]

export const CS_EXAMPLE: CsResult = {
  kind: 'cs',
  inquiry: 'Halo, sweatshirt Colorbox x Liunic yang ada di homepage itu harganya berapa? Ukuran M masih ada stok?',
  classification: 'PRODUCT_AVAILABILITY',
  sources: [
    { ref: 'CB-PRODUCT-001 (https://colorbox.co.id/)', excerpt: 'Harga IDR 249.900 (promo IDR 239.900 dicek 7 Nov 2026); ukuran S, M, L, XL terdaftar di listing.', classification: 'public_data' },
    { ref: 'CB-SIZE-UNKNOWN-001 (https://colorbox.co.id/pages/size-guide)', excerpt: 'Tabel ukuran hanya berupa gambar; nilai numerik belum diverifikasi.', classification: 'public_data' }
  ],
  draft: 'Halo Kak, terima kasih sudah menghubungi Colorbox. Untuk Colorbox x Liunic Oversized Sweatshirt, pada tanggal peninjauan (7 November 2026) halaman utama resmi menampilkan harga IDR 249.900 dengan harga promosi IDR 239.900 (harga dapat berubah sewaktu-waktu). Terkait ketersediaan stok ukuran M, kami tidak dapat memastikannya secara langsung karena membutuhkan pengecekan inventaris toko; daftar ukuran pada katalog tidak menjamin stok tersedia. Silakan cek langsung di situs resmi colorbox.co.id sebelum memesan.',
  context_notes: 'Pertanyaan pertama seputar harga & ketersediaan stok ukuran M. Tidak ada klaim live stock atau fit.',
  summary: 'Inquiry produk Colorbox x Liunic Sweatshirt: konfirmasi harga dan cek stok ukuran M.',
  priority: 'sedang',
  escalate: true,
  escalation_reason: 'Keterbatasan akses inventaris langsung (live stock lookup tidak tersedia); memerlukan pengecekan manual tim bila stok meragukan.',
  simulated: false,
}
