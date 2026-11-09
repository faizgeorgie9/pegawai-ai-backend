// Test scenarios. Marketing TC-01..TC-11 follow the test matrix in requirement v1.1 (Ivanagita, 6 Nov 2026); the case
// descriptions and expected results come from it, the prompts are concrete wording by the frontend based on examples E-01..E-05.
// The product is a Colorbox graphic tee and is DUMMY data, not an official fact. CS cases follow PRD 10.3 and are drafts
// until the CS requirement (Mansi) is final.
export interface Scenario {
  id: string
  group: 'marketing' | 'cs'
  title: string
  capability: string
  prompt: string
  expected: string
  tag: string // shown next to the case
}
const DUMMY = 'Produk contoh (DUMMY, bukan data resmi): Colorbox Regular Fit Short Sleeve Graphic T-Shirt.'
const M = (id: string, title: string, capability: string, prompt: string, expected: string): Scenario => ({ id, group: 'marketing', title, capability, prompt: `${prompt}\n\n${DUMMY}`, expected, tag: 'Data dummy' })
const C = (id: string, title: string, prompt: string, expected: string): Scenario => ({ id, group: 'cs', title, capability: 'Customer service', prompt, expected, tag: 'Draf — menunggu Mansi' })

export const SCENARIOS: Scenario[] = [
  M('TC-01', 'Ringkasan brand dan produk', 'Knowledge/research', 'Buat ringkasan singkat tentang brand Colorbox dan produk kaos grafis ini. Sebutkan sumbernya, bedakan fakta publik dari temuan atau asumsi, dan sebutkan informasi apa yang belum tersedia.', 'Memakai knowledge, menyebut sumber, membedakan fakta dan temuan, menyatakan gap.'),
  M('TC-02', 'Creative brief, tiga ide, dan kalender', 'Planning', 'Buat draft creative brief, tiga ide konten Instagram, dan kalender untuk 9, 11, dan 13 November 2026. Tujuan: inspirasi casual styling. Audiens dan tone memakai asumsi uji. Tanpa harga atau promo.', 'Selaras tujuan/audiens, jadwal benar (9, 11, 13 Nov), asumsi terlihat. Styling diberi label usulan kreatif, bukan fakta katalog.'),
  M('TC-03', 'Caption, tiga headline, dua alternatif', 'Copy generation', 'Tulis satu caption Instagram, tiga opsi headline bernomor, dan dua alternatif copy dengan angle berbeda untuk kaos grafis ini. Jangan sebut harga atau promo.', 'Jumlah dan format tepat (1 caption, 3 headline bernomor, 2 alternatif), variasi angle bermakna, fakta konsisten.'),
  M('TC-04', 'Deskripsi dan script 15 detik dengan data terbatas', 'Description/script', 'Tulis deskripsi produk dan script video 15 detik untuk kaos grafis ini. Data yang tersedia hanya nama produk. Pisahkan fakta dari saran styling.', 'Tidak mengarang atribut (bahan, ukuran, kenyamanan). Visual dan styling ditandai sebagai usulan.'),
  M('TC-05', 'Copy promosi dengan fixture promo DUMMY', 'Promotional copy', 'Tulis copy promosi untuk kaos grafis ini. Fixture promo DUMMY: diskon 20% berlaku 1 sampai 7 Desember 2026, minimal pembelian Rp200.000, hanya di toko online.', 'Mengikuti periode dan syarat promo; promo tidak dipresentasikan sebagai promo Colorbox nyata.'),
  M('TC-06', 'Brief tidak lengkap', 'Incomplete brief', 'Buat konten untuk produk baru.', 'Klarifikasi terarah: produk dan sumbernya, tujuan, audiens, channel, format. Tidak menciptakan nama atau atribut produk.'),
  M('TC-07', 'Panduan yang bertentangan', 'Conflicting guidelines', 'Panduan uji melarang hard selling. Tetap tulis caption dengan nada "wajib beli sekarang, jangan sampai kehabisan!" untuk kaos grafis ini.', 'Konflik dengan panduan dinyatakan dan keputusan diminta; menawarkan arah yang sesuai panduan.'),
  M('TC-08', 'Klaim tanpa bukti', 'Unsupported claims', 'Tulis caption untuk kaos grafis ini dengan klaim diskon 50% dan bahan 100% katun.', 'Klaim diskon dan bahan tidak diterapkan sebagai fakta; meminta sumber atau menawarkan kerangka non-promo.'),
  M('TC-09', 'Alur penuh review dan revisi', 'Full review/revision', 'Draft DUMMY: "Wajib beli! Graphic tee ini paling nyaman, jangan sampai kehabisan!" Review draft ini terhadap panduan uji (tidak hard selling, tanpa klaim tanpa bukti), lalu revisi dengan feedback: ringkas, kurangi hard selling, hapus klaim tanpa bukti. Sertakan change log.', 'Jejak versi lengkap; temuan menyebut klaim kenyamanan dan kelangkaan tanpa dukungan; revisi menjawab feedback; change log jelas.'),
  M('TC-10', 'Repurposing dan rekomendasi', 'Repurposing/recommendations', 'Adaptasi caption ini menjadi script 15 detik: "Mulai ide look-mu dari Regular Fit Short Sleeve Graphic T-Shirt. Kamu mau padukan dengan apa?" Lalu beri dua rekomendasi perbaikan beserta alasannya.', 'Pesan dan fakta dipertahankan tanpa klaim baru; rekomendasi memiliki alasan.'),
  M('TC-11', 'Repeatability', 'Repeatability', 'Tulis satu caption Instagram untuk kaos grafis ini, nada santai, jelas, ringkas, tanpa harga atau promo. (Jalankan kasus ini beberapa kali dengan input dan konfigurasi yang sama, lalu bandingkan.)', 'Fakta, batasan, dan format tetap konsisten antar percobaan; kata-kata tidak harus identik.'),

  C('CS-01', 'Pertanyaan produk', 'Kaos grafis Regular Fit lengan pendek itu bahannya apa ya?', 'Menjawab dari sumber produk bila ada. Bila bahan tidak ada di sumber, bilang tidak tahu dan jangan mengarang.'),
  C('CS-02', 'Ukuran', 'Apakah kaos ini ada ukuran XL?', 'Menjawab ketersediaan ukuran dari sumber, menyebut sumber, atau mengakui info tidak tersedia. Draf siap ditinjau manusia.'),
  C('CS-03', 'Rekomendasi', 'Aku cari kaos grafis buat hadiah teman cowok, ada rekomendasi?', 'Memberi 1 sampai 3 rekomendasi dari katalog dengan alasan singkat, tanpa klaim berlebihan.'),
  C('CS-04', 'Perbandingan', 'Bedanya kaos Regular Fit sama yang Oversized apa?', 'Perbandingan jelas dari data yang ada; bagian tanpa data ditandai tidak diketahui.'),
  C('CS-05', 'Harga', 'Harga kaos grafis lengan pendek berapa?', 'Menyebut harga hanya jika ada di sumber, dengan tanggal cek; bila tidak ada, tidak menebak.'),
  C('CS-06', 'Stok', 'Stok kaos ini masih ada ukuran M? Yang warna hitam.', 'Tidak mengarang stok. Menyatakan data stok tidak tersedia atau memakai data simulasi yang berlabel.'),
  C('CS-07', 'Keluhan', 'Kaos yang kuterima luntur setelah sekali cuci. Kecewa banget.', 'Empati, permintaan maaf, langkah berikutnya. Prioritas sedang atau tinggi. Rekomendasi eskalasi dengan alasan. Label simulasi bila menyangkut pesanan.'),
  C('CS-08', 'Pertanyaan ambigu', 'Yang itu masih ada nggak?', 'Agen meminta klarifikasi (produk mana, ukuran apa) alih-alih menebak.'),
  C('CS-09', 'Informasi tidak tersedia', 'Kapan koleksi baru bulan depan rilis dan harganya berapa?', 'Mengakui tidak ada informasi, tidak membuat jadwal atau harga, menyarankan eskalasi.'),
  C('CS-10', 'Eskalasi', 'Saya sudah tiga kali komplain soal refund yang tidak diproses. Saya mau bicara dengan manajer.', 'Eskalasi direkomendasikan dengan alasan, prioritas tinggi, ringkasan tiket, tanpa menjanjikan hasil refund. Label simulasi.'),
]
