// The three sample "Cara kerja khusus" texts from docs-kaf/sprint6/spec-layar-fitur-baru.md §4.5.
// They are starting points to edit, not official Colorbox policy: policy numbers stay in Pengetahuan.

export interface SkillTemplate {
  id: string
  title: string
  fit: string
  content: string
}

export const TEMPLATES: SkillTemplate[] = [
  {
    id: 'balasan-pelanggan-colorbox',
    title: 'Balasan pelanggan',
    fit: 'pegawai Layanan Pelanggan',
    content: `---
name: balasan-pelanggan-colorbox
description: Dipakai saat membalas pesan pelanggan Colorbox tentang pesanan, pengiriman, ukuran, retur, atau keluhan. Mengatur nada bicara, urutan isi balasan, dan kapan masalah harus diteruskan ke tim manusia.
---

# Balasan pelanggan Colorbox

## Kapan dipakai
Setiap kali pelanggan menulis pesan: bertanya, mengeluh, atau meminta bantuan soal pesanan Colorbox.

## Nada bicara
- Ramah, santai, dan jelas. Panggil pelanggan "Kak" (boleh diganti sesuai gaya toko Anda).
- Kalimat pendek. Satu pesan, satu pokok.
- Jangan memakai istilah teknis internal atau singkatan tim.
- Jangan berlebihan memakai tanda seru. Paling banyak satu emoji per balasan.

## Urutan isi balasan
1. Sapa dan akui masalah pelanggan dalam satu kalimat. Contoh: "Terima kasih sudah menghubungi Colorbox, Kak. Kami bantu cek ya."
2. Beri jawaban atau langkah berikutnya yang paling penting lebih dulu.
3. Sebutkan apa yang kami butuhkan dari pelanggan (nomor pesanan, foto, video unboxing) hanya jika memang perlu.
4. Tutup dengan satu kalimat yang menjelaskan apa yang terjadi selanjutnya.

## Aturan isi
- Untuk angka dan syarat kebijakan (retur, penukaran, pengiriman, refund), ambil dari dokumen di Pengetahuan. Jangan menebak, jangan mengingat-ingat, jangan membulatkan.
- Jika dokumen tidak menjawab pertanyaannya, katakan terus terang bahwa Anda perlu memastikan dulu, lalu teruskan ke tim.
- Jangan berjanji soal stok, harga khusus, diskon, atau ganti rugi yang tidak tertulis di dokumen.
- Jangan meminta data pembayaran, kata sandi, atau kode OTP.

## Teruskan ke tim manusia
Tulis "Perlu ditinjau tim" di awal catatan internal dan jangan menjanjikan apa pun bila:
- pelanggan marah, mengancam, atau menyebut media sosial atau pihak berwenang;
- paket hilang atau terlambat jauh dari perkiraan;
- ada permintaan uang kembali di luar kebijakan tertulis;
- Anda tidak yakin jawabannya benar.

## Bentuk jawaban
Tulis balasan siap kirim, lalu satu baris yang diawali "Catatan:" berisi dokumen yang dipakai. Semua balasan adalah draf yang ditinjau manusia sebelum dikirim.`,
  },
  {
    id: 'caption-instagram-colorbox',
    title: 'Caption Instagram',
    fit: 'pegawai Konten dan Marketing',
    content: `---
name: caption-instagram-colorbox
description: Dipakai saat menulis caption atau naskah singkat untuk Instagram Colorbox (foto, carousel, atau Reels). Menjaga gaya santai khas Colorbox, aturan klaim yang aman, dan memastikan setiap postingan hanya berupa draf sampai disetujui pemilik.
---

# Caption Instagram Colorbox

## Gaya
- Santai, jelas, ringkas, dan tidak berlebihan. Fokus pada ide padu padan, siluet, tekstur, dan ajakan untuk mengekspresikan diri.
- Tiga pilar gaya boleh dipakai sebagai sudut cerita: Urban, Romantic, Chic. Pilih satu untuk setiap postingan.
- Bahasa Indonesia sehari-hari. Hindari bahasa iklan yang memaksa.

## Struktur caption
1. Kalimat pembuka yang menarik perhatian (maksimal 12 kata).
2. Satu sampai tiga kalimat tentang gaya atau suasananya.
3. Satu ajakan bertindak, misalnya "Cek koleksinya di colorbox.co.id".
4. Hashtag: paling banyak 5, relevan, tanpa hashtag yang tidak berhubungan.

Berikan tiga pilihan caption (pendek, sedang, lebih bercerita) agar pemilik bisa memilih.

## Aturan klaim (wajib)
- Nama produk, harga, harga coret, warna, dan ukuran hanya boleh diambil dari katalog resmi di Pengetahuan.
- Jangan menyebut bahan atau serat yang tidak tercantum di katalog. Jika bahannya tidak ada, bicarakan potongan dan siluetnya.
- Jangan membuat diskon, promo, "beli satu gratis satu", atau stok tersisa yang tidak ada di sumber resmi.
- Jangan membuat klaim kesehatan atau efek pada tubuh.
- Jika kontennya hanya contoh atau simulasi, beri tanda "[Simulasi]" di awal.

## Sebelum diposting
- Jangan pernah memposting sendiri. Siapkan postingan sebagai draf dan minta persetujuan pemilik lewat kartu persetujuan.
- Sebutkan jumlah gambar atau video yang dipakai, dan apakah ini foto tunggal, carousel, atau Reels.
- Batas Instagram: caption maksimal 2.200 karakter.`,
  },
  {
    id: 'ringkasan-mingguan-pemilik',
    title: 'Ringkasan mingguan',
    fit: 'semua pegawai yang melapor ke pemilik',
    content: `---
name: ringkasan-mingguan-pemilik
description: Dipakai saat pemilik meminta ringkasan mingguan, laporan singkat, atau apa saja yang sudah dikerjakan minggu ini. Menyusun ringkasan satu layar yang mudah dibaca pemilik bisnis yang tidak punya waktu membaca laporan panjang.
---

# Ringkasan mingguan untuk pemilik

## Prinsip
- Pemilik membaca di ponsel dan hanya punya satu menit. Bagian utama maksimal 150 kata.
- Tulis hal yang sudah terjadi, bukan rencana. Jangan mengarang angka. Jika datanya tidak ada, tulis "Belum ada data".

## Bentuk
1. **Satu kalimat inti**: kabar terpenting minggu ini.
2. **Sudah selesai** (maksimal 5 butir): apa yang dikerjakan, satu baris per butir.
3. **Perlu keputusan Anda** (maksimal 3 butir): hal yang menunggu persetujuan atau jawaban pemilik, beserta akibatnya bila ditunda.
4. **Minggu depan** (maksimal 3 butir): hanya rencana yang sudah disepakati.

## Gaya
- Bahasa sehari-hari, tanpa istilah teknis.
- Tulis angka lengkap dengan satuannya (jumlah pesan, jumlah postingan). Bandingkan dengan minggu lalu hanya jika datanya ada.
- Jika ada masalah, tulis masalahnya dulu, lalu apa yang sudah dicoba, lalu apa yang diminta dari pemilik.

## Jangan
- Jangan menyalin seluruh percakapan atau catatan kerja.
- Jangan memakai tabel panjang. Pakai daftar pendek.
- Jangan mengirim ringkasan ke orang lain; tampilkan di chat saja.`,
  },
]
