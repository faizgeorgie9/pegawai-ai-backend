// Katalog jenis usaha untuk onboarding awal (halaman #/mulai).
// DRAF R&D: berkas ini satu-satunya tempat mengubah daftar. Tidak ada kode di sini; layar membacanya apa adanya.
//
// Cara baca:
//  * Industry  = satu pilihan "jenis usaha" (kartu di langkah 1).
//  * Division  = bagian kerja dalam usaha itu (Pemasaran, Layanan pelanggan, ...). Divisi yang punya >= 2 pegawai
//                terpilih ikut dibuatkan Tim (grup chat) bernama "Tim <label divisi>".
//  * Employee  = satu pegawai yang disarankan.
//      - status 'ready'   : `template` adalah id template di BFF (GET /templates). Layar hanya menampilkannya sebagai
//                           bisa dipilih bila id itu benar-benar dikembalikan BFF; bila tidak, ia tampil "Belum tersedia".
//                           Saat ini BFF hanya punya 5 template: rian, budi, diana, siti, hendra (migrations/001_init.sql).
//      - status 'planned' : belum ada template. Hanya tampil sebagai baris "Segera hadir"; tidak bisa dicentang.
//                           `plan` = kode peran di templates/agents (CRE-01, CRE-04, MGT-01) atau di docs-kaf/sprint5
//                           (MKT-01, MKT-03, MKT-07), atau 'usulan' bila belum tertulis di dokumen mana pun.
//
// Aturan teks (untuk pemilik usaha non-teknis): bahasa Indonesia sehari-hari; tanpa istilah teknis
// (prompt, model, token, template, SOUL, agen); `title` = apa yang dikerjakan, bukan nama jabatan Inggris.
// Menambah industri: salin satu blok Industry, ganti id unik (huruf kecil, tanpa spasi), isi, simpan.
// Menambah pegawai siap pakai: tambahkan template di BFF dulu, lalu satu baris `ready(...)` di sini.

export type EmployeeStatus = 'ready' | 'planned'

export interface CatalogEmployee {
  status: EmployeeStatus
  template: string // id template BFF bila status 'ready'; '' bila 'planned'
  plan: string // kode rencana bila status 'planned'; '' bila 'ready'
  title: string // tugasnya, bahasa awam, <= 40 huruf
  why: string // satu kalimat: kenapa cocok untuk usaha ini, <= 90 huruf
  preselect: boolean // sudah tercentang saat langkah 2 dibuka (hanya berlaku bila 'ready')
}

export interface CatalogDivision {
  id: string
  label: string // nama divisi di layar, juga dipakai untuk nama Tim ("Tim Pemasaran")
  blurb: string // satu kalimat apa yang dikerjakan divisi ini
  employees: CatalogEmployee[]
}

export interface Industry {
  id: string
  label: string // judul kartu, <= 32 huruf
  examples: string // contoh usaha, <= 60 huruf
  divisions: CatalogDivision[]
}

const ready = (template: string, title: string, why: string, preselect = false): CatalogEmployee => ({ status: 'ready', template, plan: '', title, why, preselect })
const planned = (plan: string, title: string, why: string): CatalogEmployee => ({ status: 'planned', template: '', plan, title, why, preselect: false })

// Judul tetap per template (sama dengan ROLE_LABELS di ui.tsx), supaya semua industri memakai kata yang sama.
const T = {
  rian: 'Penulis naskah dan caption',
  budi: 'Perancang visual',
  diana: 'Penilai mutu konten',
  siti: 'Penjawab pelanggan',
  hendra: 'Ketua layanan pelanggan',
}

const MARKETING = 'Pemasaran'
const SUPPORT = 'Layanan pelanggan'
const OPS = 'Operasional'

export const INDUSTRIES: Industry[] = [
  {
    id: 'fashion',
    label: 'Fashion dan pakaian',
    examples: 'Butik, distro, toko baju online',
    divisions: [
      {
        id: 'marketing',
        label: MARKETING,
        blurb: 'Membuat tulisan, gambar, dan jadwal posting untuk koleksi Anda.',
        employees: [
          ready('rian', T.rian, 'Menulis caption produk dan teks promo koleksi baru.', true),
          ready('budi', T.budi, 'Merancang tampilan foto, carousel, dan banner koleksi.', true),
          ready('diana', T.diana, 'Memeriksa tulisan sebelum diposting agar tidak ada klaim berlebihan.'),
          planned('CRE-01', 'Penyusun strategi konten', 'Menyusun tema dan kalender konten tiap bulan.'),
          planned('CRE-04', 'Pembuat video pendek', 'Membuat ide video untuk Reels dan TikTok.'),
          planned('MKT-03', 'Pengelola iklan berbayar', 'Mengatur iklan Instagram dan Google.'),
        ],
      },
      {
        id: 'customer_support',
        label: SUPPORT,
        blurb: 'Menjawab pelanggan yang bertanya lewat WhatsApp.',
        employees: [
          ready('siti', T.siti, 'Menjawab pertanyaan ukuran, stok, ongkir, dan retur.', true),
          ready('hendra', T.hendra, 'Menangani komplain barang cacat dan permintaan refund.'),
        ],
      },
      {
        id: 'operations',
        label: OPS,
        blurb: 'Mengurus pesanan dan stok.',
        employees: [planned('usulan', 'Admin pesanan dan stok', 'Mencatat pesanan dan mengingatkan stok yang menipis.')],
      },
    ],
  },
  {
    id: 'fnb',
    label: 'Makanan dan minuman',
    examples: 'Kafe, restoran, katering, kedai',
    divisions: [
      {
        id: 'marketing',
        label: MARKETING,
        blurb: 'Membuat promo menu dan cerita tempat Anda.',
        employees: [
          ready('rian', T.rian, 'Menulis caption menu baru, promo, dan cerita tentang tempat Anda.', true),
          ready('budi', T.budi, 'Merancang foto menu dan poster promo.', true),
          ready('diana', T.diana, 'Memeriksa tulisan sebelum diposting.'),
          planned('CRE-04', 'Pembuat video pendek', 'Membuat ide video menu dan suasana tempat.'),
        ],
      },
      {
        id: 'customer_support',
        label: SUPPORT,
        blurb: 'Menjawab pelanggan yang bertanya lewat WhatsApp.',
        employees: [
          ready('siti', T.siti, 'Menjawab pertanyaan menu, jam buka, reservasi, dan pesan antar.', true),
          ready('hendra', T.hendra, 'Menangani komplain pesanan salah atau terlambat.'),
        ],
      },
      {
        id: 'operations',
        label: OPS,
        blurb: 'Mengurus pesanan, reservasi, dan stok bahan.',
        employees: [
          planned('usulan', 'Pencatat pesanan dan reservasi', 'Merapikan pesanan dan reservasi yang masuk.'),
          planned('usulan', 'Pengingat stok bahan', 'Mengingatkan bahan yang hampir habis.'),
        ],
      },
    ],
  },
  {
    id: 'jasa',
    label: 'Jasa dan salon',
    examples: 'Salon, barbershop, spa, bengkel, laundry',
    divisions: [
      {
        id: 'marketing',
        label: MARKETING,
        blurb: 'Membuat promo layanan dan paket.',
        employees: [
          ready('rian', T.rian, 'Menulis caption layanan, promo paket, dan testimoni.', true),
          ready('budi', T.budi, 'Merancang poster promo dan foto sebelum-sesudah.', true),
          ready('diana', T.diana, 'Memeriksa tulisan sebelum diposting.'),
        ],
      },
      {
        id: 'customer_support',
        label: SUPPORT,
        blurb: 'Menjawab pelanggan yang bertanya lewat WhatsApp.',
        employees: [
          ready('siti', T.siti, 'Menjawab pertanyaan layanan, harga, dan jam buka.', true),
          ready('hendra', T.hendra, 'Menangani keluhan pelanggan yang tidak puas.'),
        ],
      },
      {
        id: 'operations',
        label: OPS,
        blurb: 'Mengatur jadwal dan janji.',
        employees: [planned('usulan', 'Pengatur jadwal booking', 'Mencatat booking dan mengingatkan pelanggan sebelum janji.')],
      },
    ],
  },
  {
    id: 'pendidikan',
    label: 'Kursus dan pendidikan',
    examples: 'Bimbel, kursus bahasa, pelatihan, sekolah musik',
    divisions: [
      {
        id: 'marketing',
        label: MARKETING,
        blurb: 'Mengajak calon siswa mendaftar.',
        employees: [
          ready('rian', T.rian, 'Menulis caption program, jadwal kelas, dan cerita siswa.', true),
          ready('budi', T.budi, 'Merancang poster pendaftaran dan infografis materi.', true),
          ready('diana', T.diana, 'Memeriksa tulisan agar janji hasil belajar tidak berlebihan.'),
        ],
      },
      {
        id: 'customer_support',
        label: SUPPORT,
        blurb: 'Menjawab calon siswa dan orang tua lewat WhatsApp.',
        employees: [
          ready('siti', T.siti, 'Menjawab pertanyaan program, biaya, dan jadwal.', true),
          ready('hendra', T.hendra, 'Menangani keluhan siswa atau orang tua.'),
        ],
      },
      {
        id: 'operations',
        label: OPS,
        blurb: 'Mengurus jadwal kelas dan tagihan.',
        employees: [planned('usulan', 'Pengingat jadwal dan tagihan', 'Mengingatkan jadwal kelas dan iuran bulanan.')],
      },
    ],
  },
  {
    id: 'properti',
    label: 'Properti',
    examples: 'Agen properti, developer kecil, kos, sewa',
    divisions: [
      {
        id: 'marketing',
        label: MARKETING,
        blurb: 'Memasarkan unit yang dijual atau disewakan.',
        employees: [
          ready('rian', T.rian, 'Menulis deskripsi unit dan iklan.', true),
          ready('budi', T.budi, 'Merancang brosur dan poster unit.', true),
          ready('diana', T.diana, 'Memeriksa deskripsi agar tidak menjanjikan hal yang belum pasti.'),
          planned('CRE-04', 'Pembuat video pendek', 'Membuat ide video tur singkat unit.'),
        ],
      },
      {
        id: 'customer_support',
        label: SUPPORT,
        blurb: 'Menjawab calon pembeli atau penyewa lewat WhatsApp.',
        employees: [
          ready('siti', T.siti, 'Menjawab pertanyaan harga, lokasi, dan jadwal lihat unit.', true),
          ready('hendra', T.hendra, 'Menangani keluhan dan negosiasi yang rumit.'),
        ],
      },
      {
        id: 'operations',
        label: OPS,
        blurb: 'Mencatat calon pembeli dan jadwal survei.',
        employees: [planned('usulan', 'Pencatat calon pembeli', 'Mencatat siapa yang tertarik dan jadwal survei unit.')],
      },
    ],
  },
  {
    id: 'klinik',
    label: 'Kesehatan dan klinik',
    examples: 'Klinik, apotek, klinik kecantikan, dokter gigi',
    divisions: [
      {
        id: 'marketing',
        label: MARKETING,
        blurb: 'Membuat konten edukasi dan promo layanan.',
        employees: [
          ready('rian', T.rian, 'Menulis konten edukasi dan promo layanan dengan bahasa yang sopan.', true),
          ready('budi', T.budi, 'Merancang infografis edukasi dan poster layanan.', true),
          ready('diana', T.diana, 'Memeriksa tulisan agar tidak ada klaim kesehatan yang berlebihan.', true),
        ],
      },
      {
        id: 'customer_support',
        label: SUPPORT,
        blurb: 'Menjawab pasien dan calon pasien lewat WhatsApp.',
        employees: [
          ready('siti', T.siti, 'Menjawab pertanyaan layanan, jam praktik, dan cara mendaftar.', true),
          ready('hendra', T.hendra, 'Menangani keluhan pasien.'),
        ],
      },
      {
        id: 'operations',
        label: OPS,
        blurb: 'Mengatur janji temu.',
        employees: [planned('usulan', 'Pengatur janji temu', 'Mencatat janji pasien dan mengingatkan sebelum jadwal.')],
      },
    ],
  },
  {
    id: 'toko',
    label: 'Toko online dan produk',
    examples: 'Kosmetik, elektronik, perlengkapan rumah, oleh-oleh',
    divisions: [
      {
        id: 'marketing',
        label: MARKETING,
        blurb: 'Membuat promo dan tampilan produk.',
        employees: [
          ready('rian', T.rian, 'Menulis deskripsi produk dan caption promo.', true),
          ready('budi', T.budi, 'Merancang foto produk dan banner promo.', true),
          ready('diana', T.diana, 'Memeriksa tulisan sebelum diposting.'),
          planned('MKT-03', 'Pengelola iklan berbayar', 'Mengatur iklan Instagram dan Google.'),
        ],
      },
      {
        id: 'customer_support',
        label: SUPPORT,
        blurb: 'Menjawab pembeli yang bertanya lewat WhatsApp.',
        employees: [
          ready('siti', T.siti, 'Menjawab pertanyaan produk, stok, ongkir, dan retur.', true),
          ready('hendra', T.hendra, 'Menangani komplain barang rusak dan refund.'),
        ],
      },
      {
        id: 'operations',
        label: OPS,
        blurb: 'Mengurus pesanan dan stok.',
        employees: [planned('usulan', 'Admin pesanan dan stok', 'Mencatat pesanan dan mengingatkan stok yang menipis.')],
      },
    ],
  },
  {
    id: 'umkm',
    label: 'Usaha lain',
    examples: 'Bila belum ada yang cocok, mulai dari yang paling umum',
    divisions: [
      {
        id: 'marketing',
        label: MARKETING,
        blurb: 'Membuat tulisan dan gambar untuk media sosial.',
        employees: [
          ready('rian', T.rian, 'Menulis caption dan teks promo.', true),
          ready('budi', T.budi, 'Merancang gambar dan poster promo.', true),
          ready('diana', T.diana, 'Memeriksa tulisan sebelum diposting.'),
          planned('CRE-01', 'Penyusun strategi konten', 'Menyusun tema dan kalender konten tiap bulan.'),
        ],
      },
      {
        id: 'customer_support',
        label: SUPPORT,
        blurb: 'Menjawab pelanggan yang bertanya lewat WhatsApp.',
        employees: [
          ready('siti', T.siti, 'Menjawab pertanyaan pelanggan dengan sopan.', true),
          ready('hendra', T.hendra, 'Menangani komplain yang sulit.'),
        ],
      },
      {
        id: 'operations',
        label: OPS,
        blurb: 'Mengatur pekerjaan tim.',
        employees: [planned('MGT-01', 'Pengatur tugas tim', 'Membagi pekerjaan ke pegawai lain dan merangkum hasilnya.')],
      },
    ],
  },
]

export const industryById = (id: string): Industry | undefined => INDUSTRIES.find((i) => i.id === id)
