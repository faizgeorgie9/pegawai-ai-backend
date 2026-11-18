# Phase A: Fondasi UI/UX (Frontend, Kevin)

Tanggal: 7 November 2026. Lingkup: hanya Frontend. Backend (Faiz), Marketing (Ivanagita) dan CS (Mansi) tidak dirancang di sini; kebutuhan kita dari mereka ada di `kebutuhan-api-frontend.md`. Referensi visual: `referensi-ui.md`. Wireframe: `wireframe/index.html`.

Legenda status yang dipakai di seluruh dokumen:

| Status | Arti |
|---|---|
| Berfungsi | Ada di kode saat ini atau di `bff-spec.md` bagian 5 |
| Mock | Tampil dengan data contoh berlabel; bukan keberhasilan |
| Belum didukung | Belum ada API; belum ada keputusan untuk membuatnya |
| Diblokir | Sengaja dimatikan; backend yang memutuskan membuka atau tidak |

## 1. Navigasi dan tata letak

### 1.1 Pola tiga kolom

Tetap seperti aplikasi sekarang (`App.tsx`, `Panel.tsx`), tidak dibangun ulang:

1. **Sidebar** (288 px): merek, navigasi bagian, daftar agen per tim dengan status teks, riwayat chat agen yang terbuka.
2. **Area utama**: halaman aktif (chat, daftar, detail).
3. **Panel samping** (300 sampai 560 px, bisa diubah lebarnya): hanya di Chat dan Grup. Tab sekarang: Berpikir, Token, Aktivitas, Info.

Di layar sempit sidebar menjadi laci (tombol menu di `mbar`) dan panel samping menutup (perilaku yang sudah ada).

### 1.2 Bagian sidebar (urutan)

| Bagian | Isi | Catatan |
|---|---|---|
| Dashboard | Ringkasan | Baru |
| Chat | Agen per tim + riwayat agen terbuka | Ada; "Bot" dinamai ulang "Agen" di teks |
| Grup | Daftar grup | Ada, dipertahankan sebagai bonus |
| Agen | Daftar, detail, buat, ubah | Daftar dan buat ada (dialog); detail dan ubah baru |
| Tools / Plugins | Registri toolset | Baru |
| Computer Use | Tugas, status, aktivitas | Baru, Diblokir |
| Scheduler | Daftar job | Baru, Diblokir |
| Workspace Marketing | 5 tahap | Baru, Mock |
| Workspace CS | Alur CS | Baru, Mock, menunggu requirement CS (Mansi) |
| Aktivitas | Log tool | Ada |

Footer sidebar: pil "Sedang dikerjakan" (ada). **Kartu Paket/kuota dihapus dari tampilan** karena di luar PRD. Catatan: BFF masih mengembalikan `plan`/`limits` dan bisa menjawab 402 saat kuota habis; UI hanya menampilkan pesan error biasa (tanpa tombol naik paket). Dialog paket (`PlanDialog`) tidak lagi dibuka dari mana pun.

### 1.3 Rute (hash router)

Rute yang sudah ada (`router.ts`): `#/` , `#/bot/<id>/<sesi?>`, `#/grup/<id>`, `#/aktivitas`.

Usulan rute (baru, perlu implementasi di Phase B):

| Rute | Halaman |
|---|---|
| `#/` | Dashboard |
| `#/chat/<agenId>/<sesi?>` | Chat (menggantikan `/bot/...`; alias lama tetap dibaca agar tautan lama jalan) |
| `#/grup/<id>` | Grup |
| `#/agen` | Daftar agen |
| `#/agen/baru` | Buat agen |
| `#/agen/<id>` | Detail agen |
| `#/agen/<id>/ubah` | Ubah agen |
| `#/tools` | Tools / Plugins |
| `#/computer-use` | Computer Use |
| `#/scheduler` | Scheduler |
| `#/marketing` | Workspace Marketing (`/<briefId>` untuk satu brief) |
| `#/cs` | Workspace CS |
| `#/aktivitas` | Aktivitas |

Hash adalah state: refresh dan tombol back harus tetap bekerja.

## 2. Halaman

Setiap halaman memakai status yang sama: **memuat** (kerangka atau teks "Memuat..."), **kosong** (bingkai tetap tampil, kalimat dalam bahasa kerja), **error** (`ErrorLine` dengan tombol Coba lagi, pesan dari BFF), **validasi** (pesan di bawah kolom, tombol kirim nonaktif), **berhasil** (toast atau status inline).

### 2.1 Dashboard (baru)

- **Tujuan:** menjawab "siapa sedang apa, apa yang perlu perhatian saya".
- **Bagian:** (a) agen dengan status teks; (b) tugas berjalan; (c) perlu perhatian (izin menunggu, error terakhir); (d) aktivitas terbaru; (e) status kapabilitas (ringkasan matriks bagian 5).
- **Data:** `GET /api/bots` (status, activity), `GET /api/runs?status=active`, `GET /api/activity?limit=`, `GET /api/events` (SSE) untuk pembaruan langsung. Semua sudah ada di BFF. Bagian "perlu perhatian" memakai event `approval` yang ada di stream run; belum ada endpoint daftar izin tertunda: usulan.
- **Aksi:** buka chat agen, hentikan tugas (`POST /runs/{id}/stop`), buka Aktivitas.
- **Status:** memuat, kosong ("Belum ada agen"), error, koneksi (bilah "Menyambung ulang..." sudah ada).

### 2.2 Chat

- **Tujuan:** interaksi utama dengan satu agen.
- **Bagian:** header identitas agen; utas pesan (bubble, berpikir inline yang bisa dilipat dengan durasinya, chip tool, kartu izin); kartu hasil terstruktur (bagian 6 dan 7); kotak input; panel samping.
- **Data:** `GET /api/bots/{id}/sessions`, `.../messages`, `POST /api/bots/{id}/runs`, stream run, `GET /api/thinking`, `GET /api/usage`.
- **Aksi:** kirim, hentikan, arahkan (steer), antre, topik baru (reset), ganti judul, hapus sesi, setujui atau tolak izin.
- **Status:** memuat riwayat, kosong (sesi baru), error kirim (baris error + kirim ulang), agen sedang bekerja, koneksi putus, run dihentikan.
- Perilaku rinci di bagian 3 (bagian ini).

### 2.3 Grup (dipertahankan)

- Sudah ada: 2 sampai 6 anggota, maksimal 3 ronde dan 10 pesan bot per kirim, queue/steer, stop (`bff-spec.md` bagian 4 dan 5). Tidak diubah di Sprint 3 selain gaya agar sama dengan halaman lain. Bonus; bukan syarat PRD.

### 2.4 Agen: daftar, detail, buat, ubah

| Halaman | Tujuan | Isi | Aksi | Status |
|---|---|---|---|---|
| Daftar | Melihat semua agen | Kartu: avatar, nama, peran, tim, status teks, tool aktif | Buka chat, buka detail, buat | memuat, kosong, error |
| Detail | Mengenal satu agen | Identitas, ringkasan persona (`about`, maks 280 karakter), toolset aktif, riwayat singkat, pemakaian token | Chat, ubah, hapus (hanya non-bawaan) | memuat, tidak ditemukan, error |
| Buat | Membuat agen baru | Nama (maks 40), peran (maks 40), tim, warna, dari template atau persona kustom (maks 2000) | Buat | validasi, "Membuat agen..." (sekitar 33 detik menurut spek), error, berhasil |
| Ubah | Mengubah agen | Kolom yang sama dengan Buat | Simpan | **Belum didukung**: belum ada API update |

- Buat dan hapus **Berfungsi** (`POST /api/bots`, `DELETE /api/bots/{id}`); hapus ditolak saat ada run aktif.
- Halaman Ubah dibangun di wireframe dan UI, tetapi tombol Simpan tampil nonaktif dengan label "Belum didukung: menunggu API ubah agen" sampai backend menyepakatinya.
- Bagian "tool aktif" di detail hanya menampilkan daftar toolset dari `GET /p/<bot>/v1/toolsets` jika BFF meneruskannya (belum ada di bagian 5; perlu disepakati).

### 2.5 Tools / Plugins

- **Tujuan:** melihat toolset apa yang tersedia, mana yang dimatikan, dan agen mana yang memakainya.
- **Bagian:** tabel toolset (nama, deskripsi, status chip, agen yang memakai); detail per toolset; status koneksi (`connections`).
- **Data:** daftar toolset Hermes. Fakta kita: aktif `web, vision, image_gen, skills, todo, memory, session_search, connections`; dimatikan hardening `terminal, file, code_execution, browser, computer_use, cronjob, delegation`. Endpoint registri dan penugasan per agen belum ada di BFF: perlu disepakati.
- **Aksi:** lihat saja. Menugaskan tool ke agen: **Belum didukung** (toolset diatur backend lewat `bff.harden`, bukan UI).
- **Status:** memuat, kosong, error, chip status per baris.

### 2.6 Computer Use

- **Tujuan:** menjalankan tugas komputer dan melihat statusnya. Tidak pernah melakukan aksi eksternal.
- **Status sekarang:** **Diblokir (keputusan backend)**. `computer_use` dimatikan di hardening.
- **Bagian:** banner status diblokir dengan alasan; formulir tugas (nonaktif); daftar run (kosong); aktivitas.
- **Aksi:** tidak ada selama diblokir. Jika backend membuka: kirim tugas, lihat status, hentikan, kartu izin di chat.
- **Status:** diblokir (tampilan utama), kosong, error. Tidak ada data palsu yang tampil seolah berjalan.

### 2.7 Scheduler

- **Tujuan:** daftar job terjadwal (kartu rutin berurutan waktu).
- **Status sekarang:** **Diblokir (keputusan backend)**. `cronjob` dimatikan.
- **Bagian:** banner diblokir; daftar job kosong dengan bingkai tetap; formulir buat job (nonaktif).
- **Aksi:** tidak ada. Jika dibuka: buat, jeda, hapus, lihat riwayat jalan. Job tidak boleh mengirim pesan atau memposting keluar.

### 2.8 Workspace Marketing

- **Tujuan:** mengerjakan lima tahap konten dengan hasil terstruktur, bukan hanya transkrip.
- **Bagian:** (a) daftar brief dan status; (b) satu brief dengan lima tahap; (c) kartu hasil; (d) log eksperimen dan rubrik untuk reviewer.
- **Status:** **Mock** sampai backend mengirim hasil terstruktur. Pemetaan di bagian 6.

### 2.9 Workspace CS

- **Tujuan:** alur pertanyaan pelanggan sampai eskalasi.
- **Status:** **Mock**, berlabel "menunggu requirement CS (Mansi)". Pemetaan di bagian 7.

### 2.10 Aktivitas

- Sudah ada: tabel log tool (waktu, agen, tool, status ok/error, durasi, pratinjau tersensor, tautan ke chat). Filter agen dan status, "muat lebih banyak". Tambahan Phase A: kolom tipe (tool, Computer Use, Scheduler) hanya jika backend menyediakannya; sampai itu hanya tool.

## 3. Perilaku chat

### 3.1 Identitas agen aktif

Header chat selalu memuat avatar berwarna, nama, peran, tim dan **status teks**: "Siap", "Sedang berpikir", "Sedang bekerja: web_search", "Menunggu izin". Sumber: `status` dan `activity` dari `GET /api/bots` dan event `bot_status` di `/api/events` (ada). "Sedang berpikir" dan "Menunggu izin" diturunkan dari stream run (event `reasoning` dan `approval`, ada); `GET /api/bots` sendiri hanya punya `idle/working/discussing`.

### 3.2 Riwayat

- Daftar sesi di sidebar untuk agen yang terbuka: judul, waktu relatif, ganti judul, hapus dengan konfirmasi (ada). Sumber `GET /api/bots/{id}/sessions`.
- Hanya sesi milik pengguna (`chat_sessions`) dan bukan `grup-*`.
- Riwayat prototipe sudah cukup; tidak ada persistensi produksi.

### 3.3 Reset / clear = sesi baru

- Tombol **Topik baru** (ada) membuka sesi baru tanpa `session_id`; BFF membuat `web-<uuid>` saat kiriman pertama.
- **Riwayat lama tetap ada dan tidak dihapus.** Reset tidak memanggil DELETE. Penghapusan sesi adalah aksi terpisah dengan konfirmasi.
- Konteks agen pada sesi baru kosong (Hermes memisahkan konteks per `session_id`). Layar menampilkan keadaan kosong "Topik baru dengan <nama agen>".
- Jika ada run berjalan di sesi lama, Topik baru tidak menghentikannya; run tetap tampil di pil "Sedang dikerjakan".

### 3.4 Ganti agen dengan aman

Aturan; sebagian sudah ada di kode (`Chat` diberi `key={bot.id}`, ada penanda `epoch` dan `sidRef` untuk membuang hasil lama):

1. Satu komponen Chat per agen; ganti agen membongkar stream SSE lama.
2. Respons yang datang terlambat dibandingkan dengan `bot.id` + `session_id` saat ini; yang tidak cocok dibuang (tidak ditempel ke utas lain).
3. Draf input disimpan per agen+sesi (usulan; sekarang `draft` ikut hilang saat komponen dibongkar).
4. Run agen sebelumnya tetap jalan di server dan tampil di "Sedang dikerjakan"; pengguna bisa kembali lewat tautannya.
5. Setiap pesan asisten menampilkan nama agennya (header kartu hasil memuat agen dan versi).

### 3.5 Kiriman berulang

Memakai queue/steer yang sudah ada:

- **Antre**: pesan menunggu di antrean klien dan dikirim setelah run selesai.
- **Arahkan**: `POST /api/runs/{id}/steer`. Jika 409 ("Bot sudah selesai"), kirim ulang sebagai pesan baru (ada).
- **Hentikan**: `POST /api/runs/{id}/stop` (ada).
- Tombol kirim nonaktif saat teks kosong; Enter tidak menggandakan kiriman saat POST sedang berjalan (run id kosong).
- Batas: 429 menjadi pesan "Terlalu banyak tugas berjalan, coba sebentar lagi".

## 4. Inventaris komponen

| Komponen | Dipakai di | Status |
|---|---|---|
| Sidebar + bagian navigasi | Semua | Perlu disempurnakan (bagian baru, hapus kartu Paket) |
| Mbar / laci mobile | Semua | Ada |
| Kartu status agen (teks status) | Dashboard, Agen, Sidebar | Perlu disempurnakan (status teks, bukan titik saja) |
| BotAvatar | Semua | Ada |
| Pil "Sedang dikerjakan" | Sidebar, header | Ada |
| Bilah koneksi | Shell | Ada |
| Toast | Shell | Ada |
| Dialog | Buat/hapus agen, grup | Ada |
| ErrorLine | Semua | Ada |
| Badge "Contoh data" / "Simulasi" | Semua fixture | Baru |
| Chip status kapabilitas (Berfungsi/Mock/Belum didukung/Diblokir) | Tools, Computer Use, Scheduler, Dashboard | Baru |
| Banner Diblokir | Computer Use, Scheduler | Baru |
| Tabel data (Aktivitas) | Aktivitas, Tools | Ada (Aktivitas); perlu disempurnakan untuk Tools |
| Bubble chat | Chat, Grup | Ada |
| ThinkingBlock (lipat, durasi) | Chat | Ada |
| Chip tool | Chat | Ada |
| Kartu izin (Izinkan/Tolak) | Chat | Ada (`approval` di Chat) |
| Kotak input + antre/arahkan/hentikan | Chat, Grup | Ada |
| Daftar sesi (ganti judul, hapus) | Sidebar | Ada |
| Panel samping (4 tab) | Chat, Grup | Ada |
| Halaman Agen: daftar, detail | Agen | Baru |
| Form agen (buat/ubah) | Agen | Perlu disempurnakan (sekarang dialog) |
| Kartu Tool / baris toolset | Tools | Baru |
| Formulir tugas Computer Use | Computer Use | Baru (nonaktif) |
| Kartu job Scheduler | Scheduler | Baru (kosong/nonaktif) |
| Kartu hasil terstruktur (dasar: header, lencana klasifikasi, peringatan, status review) | Chat, Marketing, CS | Baru |
| Lencana klasifikasi | Marketing, CS | Baru |
| Formulir brief | Marketing | Baru |
| Kartu ide / kalender | Marketing | Baru |
| Kartu draf per tipe konten | Marketing | Baru |
| Kartu review dengan skor | Marketing | Baru |
| Perbandingan sebelum/sesudah + change log | Marketing | Baru |
| Log eksperimen + formulir rubrik 1 sampai 5 | Marketing (reviewer) | Baru |
| Kartu klasifikasi, sumber, draf, ringkasan, prioritas, eskalasi | CS | Baru |
| Label "Simulasi" | CS | Baru |
| Dialog paket / kartu kuota | (dihapus) | Dihapus dari tampilan |

## 5. Matriks status kapabilitas

Hanya berdasarkan fakta: toolset API Hermes aktif `web, vision, image_gen, skills, todo, memory, session_search, connections`; dimatikan hardening `terminal, file, code_execution, browser, computer_use, cronjob, delegation`; API ubah agen belum ada; hasil terstruktur Marketing/CS menunggu backend.

| Kapabilitas | Status | Dasar |
|---|---|---|
| Agen: daftar, buat, hapus | Berfungsi | `GET/POST/DELETE /api/bots` |
| Agen: ubah (update/edit) | Belum didukung | Belum ada API |
| Chat: kirim, stream, stop, steer, riwayat | Berfungsi | `bff-spec.md` bagian 5, `Chat.tsx` |
| Chat: reset (sesi baru) | Berfungsi | Tombol Topik baru; BFF membuat sesi pada kiriman pertama |
| Grup | Berfungsi | `bff-spec.md` bagian 4 |
| Tool `web` | Berfungsi (toolset aktif) | Daftar toolset |
| Tool `vision` | Berfungsi (toolset aktif) | Daftar toolset |
| Tool `image_gen` | Berfungsi (toolset aktif) | Daftar toolset |
| Tool `skills` | Berfungsi (toolset aktif) | Daftar toolset |
| Tool `todo` | Berfungsi (toolset aktif) | Daftar toolset |
| Tool `memory` | Berfungsi (toolset aktif) | Daftar toolset |
| Tool `session_search` | Berfungsi (toolset aktif) | Daftar toolset |
| Tool `connections` | Berfungsi (toolset aktif) | Daftar toolset; endpoint status koneksi untuk UI belum ada |
| Tool `terminal`, `file`, `code_execution`, `browser`, `delegation` | Diblokir (keputusan backend) | Dimatikan hardening |
| Registri tool + penugasan per agen di UI | Belum didukung | Belum ada endpoint |
| Computer Use | Diblokir (keputusan backend) | `computer_use` dimatikan |
| Scheduler | Diblokir (keputusan backend) | `cronjob` dimatikan |
| Knowledge | Belum didukung | Tidak ada endpoint atau toolset knowledge di BFF; hanya `memory` dan `session_search` |
| Marketing: hasil terstruktur | Mock | Menunggu backend; UI memakai fixture berlabel |
| CS: hasil terstruktur | Mock | Menunggu backend dan requirement CS (Mansi) |

Mock tidak pernah dihitung sebagai keberhasilan. Setiap fixture membawa lencana "Contoh data".

## 6. Pemetaan Workspace Marketing

Sumber: Requirement Marketing v1.1 (Ivanagita), ringkasan di `konteks-sprint3.md`. UI hanya menampilkan; isi dan aturan konten milik Marketing.

### 6.1 Metadata dan elemen bersama (di setiap kartu)

- **Header kartu:** jenis kartu, ID brief/output, versi, agen penulis.
- **Lencana klasifikasi** (satu per klaim atau blok): *Public Data*, *Research Findings*, *Assumptions*, *Dummy*. Nada "santai, jelas, ringkas" untuk Colorbox ditandai *Assumptions*.
- **Peringatan:** daftar baris bertanda (klaim tanpa sumber, asumsi kreatif, klaim terlarang).
- **Rujukan:** sumber dan tanggal cek.
- **Status review:** Draf, Perlu review, Direview, Disetujui, Perlu revisi.
- **Lencana "Contoh data"** selama mock.

### 6.2 Lima tahap menjadi kartu

| Tahap | Kartu | Kolom/isi |
|---|---|---|
| 1. Brief dan klarifikasi | Kartu Brief + daftar asumsi + pertanyaan terbuka | Brief terstruktur, asumsi (lencana Assumptions), pertanyaan terbuka, status Siap / Belum siap |
| 2. Perencanaan | Kartu Creative brief, kartu Ide/konsep, kartu Kalender | Creative brief; ide per konsep; kalender per tanggal, kanal, tipe konten |
| 3. Generasi | Kartu draf per tipe konten | Draf, sumber klaim, asumsi kreatif, peringatan |
| 4. Review brand/konten | Kartu Review | Temuan, bukti, rekomendasi, skor |
| 5. Revisi dari feedback | Kartu Revisi | Draf revisi, perbandingan sebelum/sesudah, feedback yang ditindaklanjuti, masalah terbuka, change log |

### 6.3 Tipe konten menjadi kartu

| Tipe konten | Komponen | Isi khusus |
|---|---|---|
| Creative brief | Kartu Creative brief | Ringkasan tujuan, audiens, pesan kunci, CTA |
| Ide/konsep | Kartu Ide | Daftar konsep bernomor, alasan, klasifikasi |
| Kalender | Kartu Kalender | Tabel tanggal, kanal, tipe, konsep |
| Caption Instagram | Kartu Draf | Teks, panjang karakter, CTA, hashtag |
| Copy promosi | Kartu Draf | Teks, fakta promo (terpisah), klaim terlarang diperiksa |
| Headline | Kartu Opsi | Opsi bernomor, tombol pilih |
| Deskripsi produk | Kartu Produk | Dua blok: fakta produk (Public Data) dan saran gaya (terpisah) |
| Skrip | Kartu Skrip | Durasi, daftar adegan, visual, VO/teks layar, CTA |
| Alternatif copy | Kartu Opsi | Varian bersebelahan |
| Repurposing | Kartu Draf + tautan ke sumber | Asal konten, kanal tujuan |
| Review/revisi + change log | Kartu Review, Kartu Revisi | Lihat tahap 4 dan 5 |

### 6.4 Formulir brief (dari template brief)

Bidang: ID brief, versi, tanggal; tujuan; audiens dan dasarnya; produk atau topik; sumber dan tanggal cek; pilar/konsep; kanal dan tipe konten; jumlah output; bahasa dan nada; pesan kunci; CTA; periode; panjang atau durasi; fakta promo; klaim terlarang; hal yang belum diketahui; asumsi. Untuk revisi tambah: ID draf, feedback, bagian yang dipertahankan.

Validasi: tujuan, produk/topik, kanal dan tipe konten wajib; jumlah output angka positif; tanggal valid. Pesan error di bawah kolom. Tombol "Kirim ke agen" mengisi chat dengan brief; hasil kembali sebagai kartu.

### 6.5 Perbandingan sebelum/sesudah dengan change log

Dua kolom (Sebelum, Sesudah) dengan potongan yang berubah ditandai; di bawahnya change log: baris per perubahan (bagian, alasan, feedback terkait), plus "masalah terbuka". Tersedia di Chat dan di Workspace.

### 6.6 Log eksperimen dan rubrik (evaluasi reviewer)

- **Log eksperimen**, kolom: ID kasus, kapabilitas, versi, prompt, output yang diharapkan, output aktual, sumber, rute (UI/Backend/Hermes), skor, status (lulus/gagal/diblokir), error, retest, reviewer, tanggal.
- **Rubrik 1 sampai 5** dengan sembilan dimensi: akurasi, relevansi/audiens, kesesuaian brand, konsistensi, pemakaian knowledge, ikuti instruksi dan format, kelengkapan dan kejelasan, penanganan error, kebutuhan review manusia.
- Ambang lulus usulan: minimal 4 di setiap dimensi dan tanpa kegagalan kritis (UI menandai otomatis, reviewer yang memutuskan).
- Matriks uji TC-01 sampai TC-11 dan contoh E-01 sampai E-05 dipakai sebagai fixture berlabel, bukan output nyata.
- Penyimpanan log: belum ada API; perlu disepakati.

## 7. Pemetaan Workspace CS

**Seluruh halaman diberi label "menunggu requirement CS (Mansi)".** Struktur di bawah adalah dugaan dari ringkasan requirement dan bisa berubah.

| Elemen | Komponen |
|---|---|
| Pertanyaan masuk | Kartu Inquiry (teks pelanggan, kanal, waktu) |
| Klasifikasi | Lencana kelas |
| Sumber | Daftar rujukan knowledge dengan lencana klasifikasi |
| Draf berbasis sumber | Kartu Draf (grounded), tombol salin; tidak ada tombol kirim ke pelanggan |
| Konteks multi-turn | Ringkasan giliran sebelumnya |
| Ringkasan tiket | Kartu Ringkasan |
| Prioritas | Lencana prioritas |
| Rekomendasi eskalasi + alasan | Kartu Eskalasi |
| Kasus pesanan/retur/refund | Kartu dengan label **"Simulasi"** |

Di luar lingkup: pengiriman pesan ke pelanggan, Shopee atau Instagram langsung.

## 8. Urutan dan gerbang

```
A (fondasi, dokumen ini)
  -> B (layout, dashboard, chat, daftar agen, kerangka halaman, mock berlabel, state)
  -> persetujuan pemilik tercatat (C): reviewer, tanggal, versi yang disetujui
  -> D (buat/ubah agen, Tools, Computer Use, Scheduler, Marketing/CS terstruktur)
  -> E (integrasi nyata, uji semua state dan alur, demo, laporan kesiapan)
```

- **Phase D tidak dimulai sebelum persetujuan C tercatat.**
- Phase A selesai jika: dokumen ini, `kebutuhan-api-frontend.md` disepakati dengan backend (Faiz), dan wireframe direview.
- Aturan ClickUp yang dipegang: hasil terstruktur tampil sebagai komponen (transkrip chat saja bukan bukti); setiap kapabilitas berlabel jujur; mock tidak dihitung berhasil; di luar lingkup: login, pembayaran, multi-tenant, Shopee/Instagram langsung, publikasi, pesan pelanggan; Computer Use dan Scheduler tidak pernah melakukan aksi eksternal.

## 9. Belum diverifikasi

- Video referensi Phase A belum ditinjau (dikerjakan Kevin sendiri).
- Pemetaan CS menunggu requirement Mansi.
- Nama dan bentuk endpoint baru adalah usulan sampai disepakati dengan Faiz.
