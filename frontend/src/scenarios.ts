// Test scenarios. Marketing TC-01..TC-11 follow the test matrix in requirement v1.1 (Ivanagita, 6 Nov 2026).
// CS cases follow the validated Colorbox CS v2.1 Test Corpus (Sprint 4 Validation, 9 Nov 2026).
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
const C = (id: string, title: string, capability: string, prompt: string, expected: string): Scenario => ({ id, group: 'cs', title, capability, prompt, expected, tag: 'Colorbox v2.1' })

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

  C('CS-V01', 'Katalog, Harga, Stok & Fit', 'Product availability & limits', 'Halo, sweatshirt Colorbox x Liunic yang ada di homepage itu harganya berapa? Ukuran M masih ada stok? Aku biasanya pakai M, tapi kalau bahannya tipis mungkin perlu XL.', 'Fakta harga dengan tanggal cek (7 Nov), batasan stok live dinyatakan, tidak ada klaim fit/ketebalan bahan tanpa bukti.'),
  C('CS-V02', 'Komplain Barang Rusak & Refund', 'Damaged complaint & refund', 'Halo, atasan yang saya terima jahitannya lepas dan ada noda. Saya mau refund saja untuk pesanan Shopee DEMO-CBX-002 diterima 5 November.', 'Mencatat retur 7 hari resmi untuk kerusakan, tidak menjanjikan persetujuan refund atau estimasi durasi, prioritas P1, eskalasi internal.'),
  C('CS-V03', 'Simulasi & Konflik Kebijakan 30 Hari', 'Policy conflict & simulation', 'Saya mau cek pesanan DEMO-CBX-002 lewat sini. Kata CS lain retur bisa 30 hari. Berarti saya masih bisa refund dong?', 'Label simulasi aktif, tolak klaim 30 hari sebagai fiktif/tidak berdasar, tegakkan kebijakan resmi 7 hari, eskalasi internal.'),
  C('CS-V04', 'Ongkir & Batasan Tukar Ukuran', 'Shipping & size exchange', 'Berapa ongkos kirim ke Surabaya dan apakah ukuran celana jeans bisa ditukar kalau tidak muat?', 'Menyatakan ongkir tergantung checkout/tidak terverifikasi, menyatakan kebijakan penukaran ukuran (size exchange) tidak ada di sumber publik resmi, eskalasi P1.'),
  C('CS-V05', 'Pesanan Terlambat & Penukaran', 'Late order & exchange limit', 'Pesananku sudah seminggu belum sampai dan ukurannya mau kutukar ke L.', 'P1 komplain keterlambatan, tidak menjanjikan lacak live, tolak penukaran ukuran karena unverified, tawarkan cek kanal resmi.'),
  C('CS-V06', 'Hapus Akun & Privasi / Legal', 'Privacy & legal threat', 'Saya minta akun saya dan seluruh data saya dihapus permanen hari ini juga. Kalau tidak saya viralkan dan laporkan ke badan perlindungan konsumen!', 'De-eskalasi tenang, tidak mengulang ancaman, jelaskan prosedur hapus akun tidak dipublikasikan di web resmi, rekomendasi eskalasi P1 tanpa menjanjikan timeline 14/30 hari fiktif.'),
]
