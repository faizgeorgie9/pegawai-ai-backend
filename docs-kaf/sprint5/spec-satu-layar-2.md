# Spec "satu layar" 2 (Sprint 5, FE): Jadwal & tugas, Aplikasi, Pengaturan, Pengetahuan, Tim

Untuk dua frontend-worker. Hanya `frontend/src`. Tidak menyentuh `bff/`, `data.tsx`, `bff.ts`, `App.tsx`, `router.ts`, `Chat.tsx`, `Dashboard.tsx`, `Agents.tsx`. Tidak ada cabang baru (tetap `feat/frontend-prototype`).
Kelanjutan dari `spec-ux-awam.md` dan `spec-satu-layar.md` (Beranda, Chat, Detail pegawai: sudah dikerjakan; rail pemilih pegawai, `.convo-head-chat`, `.convo-more`, `.head-inline`, `.hide-sm`, `.perm-locked`, tab `.tabs` dipakai ulang di sini). Semua keputusan di sana tetap berlaku (bagian 8 di bawah).
Dasar penilaian: rubrik Open Design (`purpose-hierarchy, typography, colour-contrast, layout-rhythm, copy, states, task, fit`) + craft product-ui, laws-of-ux, anti-ai-slop, state-coverage, action-states.

Diukur 22 Nov 2026, http://localhost:5173, akun admin@pegawai.ai, mode admin MATI (`pegawai-ai.admin-mode` tidak ada), Chromium headless, terang (gelap dicek untuk Jadwal dan Pengetahuan: kontras baik, tidak ada temuan warna; sisanya memakai token yang sama). Skrol halaman ada di `.page` (bukan `document`). Tinggi yang dapat dipakai: 1280x800 = 800 px; 375x812 = 760 px (bilah `.mbar` 52 px). `.page` berpadding atas 24, bawah 48, gap 24 (16 di ponsel), gutter 24 (16 di ponsel).

Data uji: 10 pegawai, 2 tim, 2 tugas Selesai (0 Antre/Dikerjakan/Perlu Anda), 0 tugas berulang, 12 dokumen Pengetahuan, 40 aplikasi di katalog (3 tersambung: Drive, Gmail, Canva), 11 keahlian, biaya `$0.89`, 0 rencana konten menunggu. **Catatan jujur:** papan hampir kosong, jadi angka Jadwal "sebelum" terlalu rendah. Saya menambah angka beban nyata dengan menggandakan kartu di DOM (6 kartu per kolom, tidak disimpan, tidak menulis ke BFF); BFF mengirim sampai 40 kartu per kolom (`PER_COLUMN = 40`).

## 1. Kritik per layar (rubrik)

Format sama dengan spec sebelumnya: `verdict` + maks 5 `findings`, terpenting dulu. Bukti = tangkapan layar 1280x800 terang (+gelap), 375x812 terang, dan ukuran DOM di bawah.

### 1.1 Jadwal & tugas (`Kanban.tsx`, `TaskPanel.tsx`, `#/kanban`)

Tinggi isi `.page`: **800 @1280x800** (papan sedang kosong, kolom tertinggi berakhir y=518), **1177 @375x812** (viewport 760). Dengan 6 kartu per kolom (simulasi DOM): **1501 @1280**, **4859 @375**. Posisi @375 (papan kosong): kepala 76-207, Antre 223-512, Dikerjakan 528-634, Perlu Anda 650-755, Selesai 771-1181; dengan 6 kartu: Perlu Anda baru mulai di y≈2643. Kartu 173 px (1280) / 165 px (375).

```json
{ "verdict": "polish", "findings": [
  { "area": "task", "where": "375, empat kolom ditumpuk",
    "problem": "'Perlu Anda' adalah pekerjaan pemilik, tetapi kolom ketiga: judul di y=658 saat papan kosong, y≈2643 dengan 6 kartu per kolom. 'Dikerjakan' jatuh di y=536 (kosong) atau ≈1525 (6 kartu). Tidak ada petunjuk bahwa kolom-kolom itu ada di bawah.",
    "fix": "Di ≤1100 px empat kolom jadi empat tab ('Antre 0 | Dikerjakan 0 | Perlu Anda 2 | Selesai 2') dengan jumlah; satu kolom tampil dan daftar kartunya menggulung sendiri; tab awal = 'Perlu Anda' bila ada isinya (bagian 3.2)." },
  { "area": "layout-rhythm", "where": "1280, kolom tumbuh bebas",
    "problem": "Setiap kolom memanjang mengikuti jumlah kartu: dengan 6 kartu halaman 1501 px, judul kolom ikut terskrol hilang, dan tombol 'Tugas berulang'/'Filter' di kepala tidak lagi terlihat bersama kartu. Aturan lama `.kb-col ul { max-height: none; overflow: visible }` (dibuat agar menu kartu tidak terpotong) membuat daftar tidak pernah menggulung sendiri.",
    "fix": "Papan mengisi sisa tinggi layar (grid `flex:1`), judul kolom di luar area gulir (selalu terlihat), daftar `.kb-cards` menggulung sendiri; menu `⋯` kartu jadi `position: fixed` agar tidak terpotong (bagian 3.1, 3.3)." },
  { "area": "task", "where": "formulir 'Tambah tugas' di dalam kolom Antre, 1280 dan 375",
    "problem": "Aksi utama 'beri tugas baru' terkubur di kolom pertama: tiga kontrol bertingkat (judul, 'Dikerjakan oleh', 'Mulai (opsional)' + 'Jadwalkan') memakai 150 px di 1280 dan 190 px di 375 sebelum kartu pertama, dan tidak ada tombol 'Tambah' (hanya Enter). Di ponsel saat tab/kolom lain dibuka, formulir ikut hilang.",
    "fix": "Satu baris `.tq-bar` di bawah kepala (input + 'Dikerjakan oleh' + 'Jadwalkan' + tombol primer 'Tambah'); di ponsel dua baris: input + 'Tambah', lalu 'Untuk Rian · Ubah' yang membuka pilihan (bagian 3.1)." },
  { "area": "copy", "where": "kolom kosong, 1280 dan 375",
    "problem": "Tiga dari empat kolom kosong memakai ±110 px untuk dua kalimat yang sama maknanya (petunjuk kolom 'Pegawai sedang mengerjakan' lalu 'Tidak ada yang sedang dikerjakan.'), dan kolom Antre kosong menyuruh 'Tambahkan tugas di atas' padahal formulir ada di dalamnya.",
    "fix": "Petunjuk kolom pindah ke `title`/teks sr-only; hanya satu kalimat kosong yang tampil ('Belum ada yang antre.'; kolom Perlu Anda: 'Tidak ada yang perlu Anda putuskan.'), bagian 3.4." },
  { "area": "purpose-hierarchy", "where": "kepala, 375; 'Tugas berulang' di papan",
    "problem": "Kepala 131 px (judul, subjudul 2 baris, dua tombol di baris sendiri). Setelah ada tugas berulang, `<details>` 'Tugas berulang N' muncul sebagai baris ekstra di atas papan dan bila dibuka mendorong seluruh papan turun; 'atur tugas berulang' jadi dua tempat berbeda (tombol di kepala = buat, baris di atas papan = kelola).",
    "fix": "Kepala satu baris (`head-inline`: judul kiri, 'berulang' + 'Filter' kanan); 'Tugas berulang N' satu tombol yang membuka dialog berisi daftar (Jeda/Lanjutkan/Hapus) dan tombol 'Tugas berulang baru' (bagian 3.5)." }
] }
```

`TaskPanel.tsx` (dialog tugas, `#/kanban` klik kartu): **ok**, tidak ada temuan fit. Di 1280 dialog 554 px dalam 800, tombol 'Arsipkan' / 'Ulangi' di y=620-656; di 375 sheet penuh, tombol di dasar (y=748-792), tidak menggulung. Satu poles kecil: teks 'Hasil terakhir' tampil lebih besar (±17 px) daripada 'Instruksi' (14 px) karena `<Md>`; samakan (bagian 3.6).

### 1.2 Aplikasi (`connections.tsx`, `skills-ui.tsx`, `pick-ui.tsx`, `#/aplikasi`)

Tinggi isi `.page`: **4057 @1280x800** (muatan pertama lebih dari 3,5 dtk; selama skeleton `Loading` tampil, `.page` sementara 800), **7688 @375x812**. Tab 'Keahlian pegawai': **1212 @1280**, **2481 @375** (11 kartu). Posisi @1280: tab 102-146, pencarian 170-206, chip kategori 218-288 (dua baris), 'Tersambung' 312-384, 'Dokumen & catatan' 408-1103 (kartu Drive 444-731), Gmail 2381-2647; @375: pencarian 227-263, 'Tersambung' 327-399, kartu Drive 451-717, Gmail 4484. 40 kartu di 9 kategori + 1 strip.

```json
{ "verdict": "rework", "findings": [
  { "area": "task", "where": "1280 dan 375, katalog 40 kartu",
    "problem": "Tugas utama ('sambungkan / putuskan aplikasi saya') bercampur dengan menjelajah 40 aplikasi: Gmail yang sudah tersambung ada di y=2381 (1280) / y=4484 (375). Strip 'Tersambung' (312-384) hanya berisi pil mati yang tidak bisa diklik, jadi tidak ada cara memutuskan atau menata dari sana.",
    "fix": "'Tersambung' jadi baris-baris yang bisa ditindak (nama, akun, 'Putuskan', 'Pilih dari Drive', 'Cara kerja') dan selalu di atas; katalog hanya berisi yang BELUM tersambung, diberi nama 'Aplikasi lain', 12 kartu dulu + 'Tampilkan lebih banyak' (bagian 4.1-4.3)." },
  { "area": "layout-rhythm", "where": "1280, kepala pencarian",
    "problem": "Pencarian + 10 chip kategori memakai dua baris (170-288, 118 px) sebelum konten; tiap kategori punya judul sendiri (9 judul × 24 px) dan kartu tinggi 150-290 px (deskripsi penuh, akun, tombol di dasar).",
    "fix": "Pencarian dan chip dalam satu baris (chip menggulung ke samping), tanpa judul kategori; kartu katalog dipadatkan ±112 px (deskripsi maks 2 baris, tombol 'Hubungkan' sejajar nama) (bagian 4.2)." },
  { "area": "fit", "where": "375, chip kategori dan strip",
    "problem": "Halaman 7688 px (10 layar): pemilik harus skrol 10 layar untuk sampai ke akhir, tanpa penanda posisi. Chip kategori terpotong di tepi kanan ('Desain & konten', 'Pema…') tanpa petunjuk.",
    "fix": "Total ≈2200 px (3 layar) berkat batas 12 kartu; chip tetap menggulung ke samping dengan fade tepi 24 px (bagian 4.2)." },
  { "area": "states", "where": "Tab 'Keahlian pegawai', kartu keahlian",
    "problem": "11 kartu dengan baris 'Dipakai: Rian, Diana, Budi, Siti, Hendra, Mira, Sari, Reza, Wulan, Vino' (2 baris) + tombol 'Atur' di dasar kartu: 205 px per kartu, halaman 1212 (1280) / 2481 (375). Judul 'Keahlian pegawai' dobel dengan tab.",
    "fix": "Kartu ±110 px: judul + 'Atur' sejajar, deskripsi maks 2 baris, 'Dipakai: Rian, Diana +8' (nama lengkap di `title`), judul bagian dijadikan sr-only; 11 kartu = 4 baris di 1280, tanpa skrol halaman (bagian 4.4)." },
  { "area": "copy", "where": "hasil pencarian kosong dan akun",
    "problem": "'Tidak ada aplikasi yang cocok dengan pencarian Anda.' tanpa jalan keluar; 'Tersambung sebagai' + email memakai dua baris di tiap kartu tersambung.",
    "fix": "Tombol 'Hapus pencarian' di keadaan kosong; akun jadi satu baris 'Akun: email' di baris tersambung (bagian 4.5)." }
] }
```

### 1.3 Pengaturan (`Settings.tsx`, lima bagian, `#/pengaturan/<bagian>`)

Tinggi isi `.page` (800 / 760 berarti tidak menggulung): Umum **800 @1280** (isi berakhir y=541), **862 @375**; Notifikasi 800 / 760 (isi 459 / 742); Keamanan 800 / 760 (451 / 600, satu baris karena semua pegawai punya aturan sama); **Paket dan biaya 1147 @1280**, **1294 @375**; Data 800 / 760 (296 / 476). Di 375: kepala 76-130, nav 146-193, judul bagian 209-240, baris 'Nama bisnis' 256-366, lalu Bahasa 382-491, Zona waktu 507-617, Tema 633-740, Mode admin 756-866 (terpotong di tepi). Tab nav di 375: Umum x=16-83, Notifikasi 83-168, Keamanan 168-261, 'Paket dan biaya' 260-388 (terpotong), **Data x=388-443 (di luar layar 375)**.

```json
{ "verdict": "polish", "findings": [
  { "area": "task", "where": "375, nav bagian",
    "problem": "Lima tab tidak muat 343 px: 'Paket dan biaya' terpotong ('Paket dan bi…') dan 'Data' sama sekali di luar layar (x=388); satu-satunya petunjuk adalah fade 24 px. 'Unduh data' tidak bisa ditemukan tanpa menggeser.",
    "fix": "Label pendek di ponsel ('Paket'), padding tab 8 px: Umum 59, Notifikasi 77, Keamanan 85, Paket 55, Data 47 = 323 px, semua terlihat tanpa geser (bagian 5.1)." },
  { "area": "layout-rhythm", "where": "375, baris pengaturan",
    "problem": "Setiap baris menumpuk judul, petunjuk, kontrol dan memakai 110 px (tombol/saklar/pilihan kecil ada di baris sendiri), sehingga 5 baris = 610 px dan 'Mode admin' jatuh di y=756-866, terpotong. Judul bagian ('Umum') 31 px mengulang tab yang sedang aktif tepat di atasnya.",
    "fix": "Baris satu deret (teks kiri, kontrol kanan) kecuali 'Nama bisnis' (input lebar, tetap bertingkat); judul bagian sr-only di ponsel. Umum jadi ±330 px, berakhir y≈545 (bagian 5.2)." },
  { "area": "task", "where": "Paket dan biaya, 1280 dan 375",
    "problem": "Angka paket dan biaya terlihat di layar pertama (y=140-210), tetapi 'Rincian biaya' dua daftar tertumpuk (Per pegawai 9 baris dari y=415, Per hari dari y=815) dan halaman 1147 (1280) / 1294 (375). 'Per hari' tidak pernah terlihat tanpa skrol.",
    "fix": "Desktop: Per pegawai dan Per hari berdampingan (selesai y≈700, tanpa skrol); ponsel: 5 pegawai + 'Lihat semua 9', 'Per hari' dilipat `<details>` (bagian 5.3)." },
  { "area": "layout-rhythm", "where": "1280, kolom isi",
    "problem": "Isi dibatasi 720 px di sebelah nav 200 px, tetapi `.page` tidak mengisi tinggi: di Umum/Notifikasi/Data 260-500 px kosong di bawah; jika bagian menjadi panjang (Paket, Keamanan dengan 10 aturan berbeda) seluruh halaman, termasuk judul 'Pengaturan' dan nav, ikut terskrol.",
    "fix": "`.set-body` yang menggulung sendiri, nav dan kepala tetap di tempat (bagian 5.1)." },
  { "area": "copy", "where": "Paket, baris 'Tugas berjalan bersamaan'",
    "problem": "Label dua baris ('Tugas berjalan / bersamaan') di kolom 160 px memecah ritme daftar angka.",
    "fix": "Kolom label 200 px di desktop; di ponsel label kiri, nilai kanan (bagian 5.3)." }
] }
```

### 1.4 Pengetahuan (`Pengetahuan.tsx`, `kb-ui.tsx`, `#/pengetahuan`)

Tinggi isi `.page`: **1137 @1280x800** (12 dokumen; daftar 277-1089, baris 66 px), **1810 @375x812** (baris 112 px, daftar 450-1814). Posisi @1280: judul 'Sumber milik Anda' 102-133, paragraf 145-187, tombol/URL 199-235, catatan format 247-265, dokumen pertama 289-343 (7 baris terlihat). @375: paragraf 3 baris (±215-265), 'Unggah berkas' 306-342, URL 354-390, dokumen pertama 508-529 (hanya 2,5 baris terlihat).

```json
{ "verdict": "polish", "findings": [
  { "area": "task", "where": "1280 dan 375, daftar dokumen",
    "problem": "Daftar tersimpan menyatu dengan halaman: 12 dokumen = 1137 px; dengan 60 dokumen halaman melebihi 4000 px dan 'Unggah berkas' ikut hilang dari layar. Di 375 setiap baris 112 px (pil status, 'Lihat', 'Hapus' di satu baris; nama di baris kedua; ukuran di baris ketiga), jadi hanya 2,5 dokumen terlihat.",
    "fix": "Aksi (Unggah, Drive, Tambah link) menetap di atas; daftar mengisi sisa tinggi dan menggulung sendiri; baris 56 px (1280) / 64 px (375) (bagian 6.1-6.2)." },
  { "area": "purpose-hierarchy", "where": "1280 dan 375, kepala",
    "problem": "Judul halaman ('Pengetahuan') lalu judul bagian ('Sumber milik Anda') lalu paragraf 2 baris sebelum tombol pertama (y=199 di 1280, y=306 di 375). Tombol 'Unggah berkas' dan 'Pilih dari Drive' tidak dibedakan dari 'Tambah link' (semua `outline`), padahal 'Unggah berkas' aksi utama.",
    "fix": "'Unggah berkas' (primer) + 'Pilih dari Drive' pindah ke kepala halaman; paragraf jadi satu baris kecil; judul bagian diganti judul daftar 'Tersimpan · 12' (bagian 6.1)." },
  { "area": "states", "where": "baris dokumen",
    "problem": "Setiap baris menampilkan pil 'Tersimpan' hijau yang sama untuk 12 dokumen: status normal diulang 12 kali sedangkan yang penting ('Memproses', 'Gagal') tertutup keramaian.",
    "fix": "Pil hanya untuk 'Memproses' dan 'Gagal'; 'Tersimpan' menjadi hitungan di judul daftar (bagian 6.2)." },
  { "area": "copy", "where": "paragraf pengantar, 375",
    "problem": "Tiga baris pengantar ('Semua pegawai AI Anda membaca berkas dan link ini, dan menyebut sumbernya. Ini bukan ingatan percakapan: …') + catatan format 2 baris + tautan Aplikasi: ±130 px teks sebelum tindakan.",
    "fix": "Satu kalimat: 'Semua pegawai membaca ini dan menyebut sumbernya.'; format berkas jadi `title`/bantuan di bawah tombol unggah satu baris kecil (bagian 6.1)." },
  { "area": "layout-rhythm", "where": "375, baris URL",
    "problem": "Placeholder 'https://… (website atau Google Drive)' terpotong ('… atau Google') pada input 175 px karena tombol 'Tambah link' (96 px) berbagi baris.",
    "fix": "Placeholder pendek 'Tempel link website atau Drive'; input mengambil sisa lebar (bagian 6.1)." }
] }
```

### 1.5 Tim / grup (`ChatLayout.tsx` `GroupLayout`, `Group.tsx`, `#/grup`, `#/grup/<id>`)

Tinggi isi: halaman ini tidak memakai `.page`; `.with-rail` **800 @1280** / **760 @375** (tidak menggulung). Kontainer yang menggulung: `.scroll` pesan 5009 px dalam kotak 596 px (1280), 7779 dalam 516 (375). Rail daftar tim sudah menggulung sendiri (`.rail-body > ul`). @1280: rail baris 58-160, komposer 660-760. @375: `.convo-head` 52-160 (108 px, dua deret), pesan 160-676 (516), komposer 676-800 (122 px).

```json
{ "verdict": "polish", "findings": [
  { "area": "layout-rhythm", "where": "375, kepala percakapan tim",
    "problem": "Kepala 108 px dua deret ('Daftar tim' + judul; 'Atur anggota' + 'Detail') memakan 14% tinggi layar; ruang pesan tinggal 516 px. Chat pegawai sudah satu deret 56 px (`.convo-head-chat` + menu titik tiga), tim belum.",
    "fix": "Pola yang sama: 'Daftar tim' | judul + nama anggota (satu baris, ellipsis) | menu titik tiga berisi 'Atur anggota' dan 'Detail' (bagian 7.1)." },
  { "area": "task", "where": "375, komposer",
    "problem": "Placeholder 'Tulis pesan. Ketik @ untuk menyebut anggota.' dua baris di 343 px membuat komposer 122 px (satu baris = 98 px); kata 'pesan' tidak menyiratkan bahwa tim mengerjakan tugas, padahal itu pekerjaan utamanya.",
    "fix": "Di ponsel: 'Tulis tugas untuk tim, atau @nama' (satu baris); desktop tetap teks lama (bagian 7.2)." },
  { "area": "states", "where": "rencana konten menunggu persetujuan",
    "problem": "[INFERENCE: tidak ada rencana tertunda di data uji, dibaca dari kode `PlanCard.tsx`] Tombol 'Setujui rencana' ada di dasar kartu rencana di dalam alur pesan. Selama kartu itu pesan terbaru, skrol otomatis menampilkan tombolnya; begitu ada pesan lain (pegawai menjawab, antrean pesan Anda) kartu bergeser ke atas dan tidak ada penanda di luar alur bahwa Anda masih ditunggu.",
    "fix": "Pita 'Rencana menunggu persetujuan Anda · Lihat dan setujui' di atas komposer, hanya bila ada rencana `pending` yang kartunya di luar layar (bagian 7.3)." },
  { "area": "typography", "where": "375, judul tim",
    "problem": "Subjudul 'Diana, Rian, Budi · diskusi berjalan' tumpah ke dua baris untuk tim dengan 5-6 anggota ('Mira, Sari, Reza, Wulan, Vino' 39 karakter) pada judul yang hanya 243 px.",
    "fix": "Subjudul satu baris dengan ellipsis; nama lengkap di `title` dan di 'Atur anggota' (bagian 7.1)." }
] }
```

## 2. Jalan tugas (walk) sebelum perubahan

"Terlihat" = kontrol langkah berikutnya (atau, untuk 'lihat ...', isinya) berada seluruhnya di layar pertama tanpa skrol (1280x800: y<800; 375x812: y<812). Nilai = `top-bottom` elemen (px dari atas viewport). `kond.` = lulus pada data uji yang hampir kosong, gagal pada beban nyata (angka dari simulasi 6 kartu/kolom).

| Layar | Tugas | Kontrol langkah berikutnya | 1280x800 | 375x812 | Catatan |
|---|---|---|---|---|---|
| Jadwal | Beri tugas baru | input 'Tambah tugas, lalu tekan Enter' di kolom Antre | **PASS** (187-223) | **PASS** (285-321) | Tanpa tombol 'Tambah'; hanya Enter. |
| Jadwal | Lihat apa yang perlu saya tanggapi | judul + kartu kolom 'Perlu Anda' | **PASS** (judul 114-136, kartu mulai 168) | **FAIL kond.** (judul 658-680, isi kosong 700; dengan 6 kartu di Antre/Dikerjakan: y≈2643) | Kolom ketiga di tumpukan. |
| Jadwal | Lihat tugas yang sedang dikerjakan | judul + kartu 'Dikerjakan' | **PASS** (114-136) | **PASS kond.** (536-559; dengan 6 kartu Antre: y≈1525 = FAIL) | |
| Jadwal | Atur tugas berulang | tombol 'Tugas berulang' | **PASS** (42-78) | **PASS** (167-207) | Setelah ada jadwal, baris `<details>` tambahan di atas papan (belum terukur: 0 jadwal). |
| Aplikasi | Sambungkan Google Drive | kartu Google Drive (Hubungkan / Putuskan / Pilih dari Drive) | **PASS** (kartu 444-731) | **PASS** (451-717) | Karena Drive kebetulan kategori pertama. |
| Aplikasi | Sambungkan Gmail | kartu Gmail ('Hubungkan' / 'Cara kerja tombol draf') | **FAIL** (2381-2647) | **FAIL** (y=4484) | Pil Gmail di strip 'Tersambung' (y=349-375) tidak bisa diklik. |
| Aplikasi | Cari aplikasi lain | input 'Cari aplikasi' + chip kategori | **PASS** (170-206; chip 218-288) | **PASS** (227-263; chip 275-307, terpotong kanan) | Hasil muncul di bawah strip, kategori yang cocok saja. |
| Aplikasi | Atur keahlian pegawai | tab 'Keahlian pegawai' lalu 'Atur' pada kartu | **PASS** (tab 102-146; 'Atur' kartu pertama 440-476) | **PASS** (tab 167-211; kartu pertama 356-540, 'Atur' di dasar kartu ±490-526) | Kartu 184-205 px; baris kedua kartu y=504-688 (1280). |
| Pengaturan | Ganti nama bisnis | input 'Nama bisnis' + 'Simpan' | **PASS** (164-200) | **PASS** (317-353) | Bagian Umum adalah bagian awal. |
| Pengaturan | Cek biaya & paket | tab 'Paket dan biaya', lalu 'Biaya bulan ini' | **PASS** (nav 219-256; angka $0.89 di y=188-210 setelah satu klik) | **PASS parsial** (tab 260-388, terpotong 'Paket dan bi…'; angka y=330-355) | Satu klik di keduanya. |
| Pengaturan | Unduh data | tab 'Data', lalu tombol 'Unduh' | **PASS** (nav 258-295; 'Unduh' ±247-283) | **FAIL** (tab 'Data' x=388-443, di luar layar 375) | Hanya bisa dicapai dengan geser horizontal. |
| Pengetahuan | Unggah berkas | 'Unggah berkas' | **PASS** (199-235) | **PASS** (306-342) | |
| Pengetahuan | Tambah link | input URL + 'Tambah link' | **PASS** (199-235) | **PASS** (354-390; placeholder terpotong) | |
| Pengetahuan | Lihat dokumen yang tersimpan | daftar dokumen | **PASS** (baris pertama 289-343; 7 baris terlihat) | **PASS parsial** (nama pertama y=508; 2,5 baris terlihat, baris 112 px) | Tidak ada pencarian bila dokumen banyak. |
| Tim | Beri tugas ke tim | komposer grup | **PASS** (660-760) | **PASS** (676-800, placeholder 'Tulis pesan…') | |
| Tim | Setujui rencana | 'Setujui rencana' di `PlanCard` | **tak terukur** [INFERENCE: PASS bila rencana pesan terbaru] | **tak terukur** [INFERENCE: sama] | Tidak ada rencana tertunda di data uji. |
| Tim | Buka tim lain | baris di rail / 'Daftar tim' | **PASS** (rail 58-160) | **PASS** ('Daftar tim' 60-100, lalu lembar rail) | |

Ringkas: di 1280x800 **15 lulus, 1 gagal** (Sambungkan Gmail), 1 tak terukur; di 375x812 **10 lulus, 3 gagal** (Perlu Anda [kond.], Sambungkan Gmail, Unduh data), 2 lulus parsial (Cek biaya, Lihat dokumen), 1 lulus kondisional ('Dikerjakan': gagal pada beban nyata), 1 tak terukur. Di luar walk, kegagalan "fit": halaman menggulung jauh melebihi layar pada Aplikasi (4057 / 7688), Pengetahuan (1137 / 1810), Paket (1147 / 1294), Jadwal bila terisi (1501 / 4859). Target setelah perubahan: 17 dari 17 di kedua ukuran (rencana: diuji dengan data buatan oleh Main), `.page` Jadwal, Aplikasi (≥901 px), Pengetahuan tidak menggulung (internal saja), Pengaturan ≤ viewport pada 4 dari 5 bagian di 1280.

## 3. Jadwal & tugas: perubahan (`Kanban.tsx`, `TaskPanel.tsx`, `pages.css`)

Kontrak: tidak mengubah panggilan BFF atau bentuk data. Seret-lepas, konfirmasi, filter, arsip, kartu, `TaskPanel`, `NewSchedule`, `Confirm` tidak berubah perilakunya.

### 3.1 Susunan (≥1101 px)

Urutan DOM dalam `<section className="page kanban">`: `header.page-head.head-inline` → `p.state.ok` (notice) / `ErrorLine` (problem) → `form.tq-bar` (QuickAdd, kini di luar kolom) → (dialog) → `div.kb-grid`.

```css
.page.kanban { overflow: hidden; padding-bottom: var(--s-4); }
.kb-grid { flex: 1; min-height: 0; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); grid-template-rows: minmax(0, 1fr); gap: var(--s-4); align-items: stretch; }
.kb-grid[data-one] { grid-template-columns: minmax(0, 560px); }
.kb-col { min-height: 0; overflow: hidden; }                                /* sudah flex column + gap */
.kb-col > header { flex: none; }                                            /* judul tidak ikut terskrol */
.kb-col > header .kb-hint { }                                               /* sr-only, lihat 3.4 */
.kb-cards { list-style: none; margin: 0; padding: 2px 4px 2px 0; display: flex; flex-direction: column; gap: var(--s-2); flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; scrollbar-gutter: stable; }
.kb-col > .kb-note { flex: none; }                                          /* 'dan N lainnya' di luar area gulir */
```
Hapus aturan lama: `.kb-col ul { … max-height: 68vh … }` (pages.css:264) dan `.kb-col ul { max-height: none; overflow: visible; }` (pages.css:488); tambah kelas `kb-cards` pada `<ul>`. `.kcard:hover` mengangkat 2 px (`--lift`), karena itu `padding-top: 2px` pada `.kb-cards` agar tidak terpotong. Ukuran 1280x800: kepala 24-78, `.tq-bar` 94-134 (40 px), grid 150-784 (634 px); judul kolom 40 px; area kartu ≈ 560 px (±3,9 kartu 142 px). Halaman: `.page` `scrollHeight` = 800 (tetap, apa pun jumlah kartu).

Kartu dipadatkan (±173 → ±142 px): `.kc-meta` (avatar + nama) tetap; `kc-note` dibatasi dua baris (`display:-webkit-box; -webkit-line-clamp:2; overflow:hidden`); baris biaya (`.kc-foot` yang hanya berisi `kc-cost`) dipindah ke dalam `.kc-act` sebelum tombol: `<span className="kc-cost num">…</span>` lalu tombol primer lalu `⋯` (`margin-left:auto` pada `⋯` tetap). `.kc-foot` dengan pil `Penting`/`Gagal`/status admin tetap di tempatnya (hanya biaya yang pindah). Perkiraan: 10 + 22 (judul 1 baris) + 6 + 18 + 6 + 32 + 6 + 32 + 10 = 142.

Menu `⋯` tidak boleh terpotong oleh `overflow` area gulir: ganti dengan `position: fixed`.

```tsx
const [pos, setPos] = useState<{ top?: number; bottom?: number; right: number } | null>(null)
// di tombol:
onClick={(e) => {
  e.stopPropagation()
  const r = e.currentTarget.getBoundingClientRect()
  const up = r.bottom + 4 + c.more.length * 40 + 8 > window.innerHeight   // tidak muat di bawah: buka ke atas
  setPos(up ? { bottom: window.innerHeight - r.top + 4, right: window.innerWidth - r.right } : { top: r.bottom + 4, right: window.innerWidth - r.right })
  setMenu(!menu)
}}
// popmenu:
<div className="popmenu" role="menu" style={pos ? { position: 'fixed', ...pos } : undefined}>
// efek yang sudah ada: tambahkan penutup saat skrol
document.addEventListener('scroll', off, true); return () => document.removeEventListener('scroll', off, true)
```
Escape pada tombol/menu menutup dan mengembalikan fokus ke `⋯` (tambahkan `onKeyDown` seperti `convo-more` di `Chat.tsx`). `.kcard:has(.kc-menu [aria-expanded="true"]) { z-index: 3 }` boleh dihapus (tidak berguna lagi).

### 3.2 Tab kolom (≤1100 px, termasuk ponsel)

`const narrow = useNarrow()` (hook lokal di `Kanban.tsx`: `matchMedia('(max-width: 1100px)')` + `change` listener, nilai awal sinkron). `const [tabCol, setTabCol] = useState<TaskColumnId>('queue')` dan `const picked = useRef(false)`. Pada `load` yang berhasil pertama: `if (!picked.current) { if (b.counts.needs_you > 0) setTabCol('needs_you'); picked.current = true }` (memilih sekali; saat pengguna mengklik tab, `picked.current = true`). Pada tampilan arsip (`archived`) tidak ada tab (satu kolom).

```tsx
{state === 'ok' && narrow && !archived && (
  <div className="tabs kb-tabs" role="tablist" aria-label="Kolom tugas" onKeyDown={onTabKey}>
    {columns.map((c) => (
      <button key={c.id} id={`kbt-${c.id}`} type="button" role="tab" aria-selected={tabCol === c.id} aria-controls={`kb-${c.id}-body`} tabIndex={tabCol === c.id ? 0 : -1} onClick={() => { picked.current = true; setTabCol(c.id) }}>
        {c.label} <b className={'num' + (c.id === 'needs_you' && c.total > 0 ? ' pill warn' : '')}>{c.total}</b>
      </button>
    ))}
  </div>
)}
```
`onTabKey`: panah kiri/kanan (berputar), Home, End; pindahkan fokus ke tab baru (`document.getElementById('kbt-'+id)?.focus()`), pola sama dengan `Agents.tsx` (tab Detail). Kolom: `<section className="kb-col" id={`kb-${c.id}-body`} hidden={narrow && !archived && tabCol !== c.id} role={narrow && !archived ? 'tabpanel' : undefined} aria-labelledby={narrow && !archived ? `kbt-${c.id}` : `kb-${c.id}`}>` (`[hidden]{display:none!important}` sudah ada di chat.css).

```css
@media (max-width: 1100px) {
  .kb-grid { grid-template-columns: minmax(0, 1fr); }
  .kb-grid:not([data-one]) > .kb-col { padding: var(--s-2) 0 0; background: transparent; }  /* tab sudah jadi judul */
  .kb-grid:not([data-one]) > .kb-col > header { display: none; }
  .kb-tabs { flex: none; }
  .kb-tabs button { flex: 1 1 0; justify-content: center; padding: 0 var(--s-1); font-size: var(--t-small); white-space: nowrap; }
  .kb-tabs .num { font-weight: 500; font-size: 12px; padding: 1px 7px; border-radius: 999px; background: var(--surface); color: var(--muted); }
  .kb-tabs .num.pill.warn { background: var(--warn-bg); color: var(--warn-ink); }
}
```
(Jika token `--warn-bg` tidak ada, pakai pasangan yang dipakai `.pill.warn` di `styles.css`.) Pada 1101+ `<div.kb-tabs>` tidak dirender. Tabel ukuran ponsel (375x812): lihat 3.7.

Seret-lepas ke Antre hanya berarti di desktop; di ponsel (`hasTouch`) tidak ada perubahan (aksi 'Antre ulang' sudah ada di menu `⋯`/tombol utama).

### 3.3 Tambah tugas satu baris (`QuickAdd` → `.tq-bar`, ≥641 px satu deret; ponsel dua deret)

`QuickAdd` pindah dari dalam kolom `queue` ke atas `.kb-grid` (render hanya bila `!archived`). Tambahkan `const [opts, setOpts] = useState(false)`. Label 'Dikerjakan oleh' / 'Mulai (opsional)' tidak lagi terlihat (diganti `aria-label` dan teks tombol).

```tsx
<form className="tq-add tq-bar" onSubmit={(e) => void submit(e)}>
  <input className="tq-title" value={title} maxLength={120} onChange={(e) => setTitle(e.target.value)} placeholder="Tugas baru, lalu tekan Enter" aria-label="Judul tugas baru" />
  <button type="submit" className="btn primary tq-go" disabled={!title.trim() || !target || busy}>{busy ? 'Menambah...' : 'Tambah'}</button>
  <button type="button" className="btn link sm tq-toggle" aria-expanded={opts} aria-controls="tq-opts" onClick={() => setOpts((v) => !v)}>
    Untuk {nameOf(target)}{at ? ` · ${shortTime(at)}` : ''} · Ubah
  </button>
  <div id="tq-opts" className="tq-opts" data-open={opts || undefined}>
    <select className="tq-who" aria-label="Dikerjakan oleh" value={target} onChange={(e) => setWho(e.target.value)}>…optgroup Pegawai / Tim (tidak berubah)…</select>
    {sched ? (<><input type="datetime-local" lang="id" aria-label="Mulai pada" value={at} onChange={…} /><button type="button" className="btn link sm" onClick={…}>Hapus jadwal</button></>)
           : (<button type="button" className="btn outline" onClick={…}>Jadwalkan</button>)}
  </div>
  {problem && <ErrorLine text={problem} />}
</form>
```
`nameOf(target)`: nama pegawai/tim dari `bots`/`groups` (`'bot:id'` / `'group:id'`); `shortTime(at)`: `new Date(at).toLocaleString('id-ID', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })`.

```css
.tq-bar { flex-direction: row; flex-wrap: wrap; align-items: center; gap: var(--s-2); }
.tq-bar .tq-title { flex: 1 1 280px; min-width: 0; height: 40px; }
.tq-bar .tq-go { order: 4; height: 40px; }
.tq-bar .tq-toggle { display: none; }
.tq-opts { display: contents; }
.tq-opts > * { order: 2; }
.tq-opts select { width: 200px; height: 40px; }
.tq-opts .btn { height: 40px; }
.tq-opts input[type="datetime-local"] { height: 40px; width: 190px; }
.tq-bar > [role="alert"], .tq-bar > .problem-bar { flex-basis: 100%; order: 5; }
@media (max-width: 640px) {
  .tq-bar .tq-title { order: 1; flex: 1 1 0; }
  .tq-bar .tq-go { order: 2; }
  .tq-bar .tq-toggle { display: inline-flex; order: 3; flex-basis: 100%; justify-content: flex-start; height: 32px; padding: 0; }
  .tq-opts { display: none; order: 4; flex-basis: 100%; grid-template-columns: minmax(0, 1fr) auto; gap: var(--s-2); }
  .tq-opts[data-open] { display: grid; }
  .tq-opts select, .tq-opts input[type="datetime-local"] { width: 100%; }
}
```
Hapus aturan lama `.tq-row` (grid dua kolom) dan `.tq-field`. Tinggi: 40 px desktop; ponsel 44+0 baris pertama + 32 baris 'Untuk Rian · Ubah' = 76 px (96 bila pilihan terbuka). Enter di input tetap menyimpan (form submit). Fokus kembali ke input setelah berhasil (`titleRef.current?.focus()`). Tombol 'Tambah' nonaktif bila judul kosong (aturan `.btn:disabled` global).

### 3.4 Kolom: judul, petunjuk, keadaan

- `<header><h2 id={`kb-${c.id}`} title={hint}>{c.label} <b className="num">{c.total}</b></h2><p className="sr kb-hint">{hint}</p></header>` (petunjuk `COLUMN_HINT` tetap ada untuk pembaca layar; tidak tampil). Desktop kolom: header 40 px.
- Kosong: satu kalimat, `<p className="quiet small kb-none">`: Antre 'Belum ada yang antre.', Dikerjakan 'Tidak ada yang sedang dikerjakan.', Perlu Anda 'Tidak ada yang perlu Anda putuskan.', Selesai 'Belum ada pekerjaan yang selesai.', Arsip 'Arsip masih kosong.' (ubah `COLUMN_EMPTY.queue`; selainnya tetap). Filter aktif: 'Tidak ada yang cocok dengan filter.' (tetap) + tombol `btn link small` 'Hapus filter' (`setAgent(''); setGroup('')`).
- Loading: `Loading shape="ledger" rows={3}` di dalam `.kb-grid` (kotak 160 px minimal agar tab/halaman tidak melompat); error: `ErrorLine` + 'Coba lagi' (tetap).
- 'dan N lainnya. Persempit dengan Filter.' jadi `<p className="quiet small kb-note">`, di luar area gulir.

### 3.5 Kepala, 'Tugas berulang', 'Filter'

Kepala: `className="page-head head-inline"` dan subjudul disembunyikan di ponsel (`.page.kanban .page-head p { display: none }` pada ≤640 px). Tombol: `<button className="btn outline" onClick={openRecurring}><span className="hide-sm">Tugas </span>berulang{rec.length > 0 && <b className="num count-pill">{rec.length}</b>}</button>` (label ponsel: 'berulang'; `aria-label="Tugas berulang"`). 'Filter' tetap (`Filter (n)` bila aktif). Panel filter `.kb-more` tetap di bawah kepala dan mendorong papan turun saat terbuka (acceptable; tertutup default).

`Recurring` diganti dialog: `const [recOpen, setRecOpen] = useState(false)`; `openRecurring = () => (rec.length ? setRecOpen(true) : setCreating(true))`.

```tsx
{recOpen && (
  <Dialog title="Tugas berulang" onClose={() => setRecOpen(false)}>
    <div className="dlg-body">
      <ul className="kb-rec-list">…isi `li` yang sama seperti `Recurring` sekarang (judul, target · irama, Jeda/Lanjutkan, Hapus dengan Confirm)…</ul>
      <div className="dlg-foot"><button className="btn primary" onClick={() => { setRecOpen(false); setCreating(true) }}>Tugas berulang baru</button></div>
    </div>
  </Dialog>
)}
```
Hapus komponen `<details className="kb-rec">` dan CSS `.kb-rec*` (ganti `.kb-rec-list` = `.kb-rec ul` lama). Jeda/Hapus tetap memakai `act` dan `setConfirm`; setelah `Hapus`, dialog tetap terbuka bila daftar masih ada (karena `Confirm` adalah dialog lain). Jika daftar menjadi kosong, tutup dialog (`useEffect(() => { if (recOpen && rec.length === 0) setRecOpen(false) }, [rec.length, recOpen])`).

Tinggi kepala ponsel: ±40 px (judul 24 px di kiri; dua tombol 40 px di kanan; 150 + 95 + 72 + 16 = 333 ≤ 343).

### 3.6 `TaskPanel.tsx` (poles)

Teks 'Hasil terakhir' (`<Md>`) memakai ukuran badan 14 px: `.tp-sec .md, .tp-sec .md p { font-size: var(--t-body); }` (cek nama kelas pembungkus `Md` di `rich.tsx`; jika tidak ada kelas, bungkus dengan `<div className="tp-result">` dan atur ukuran di sana). Tidak ada perubahan lain.

### 3.7 Perkiraan setelah (Jadwal)

[INFERENCE] dihitung dari ukuran terukur, belum dirender.

| Elemen | 1280x800 top-bottom | 375x812 top-bottom |
|---|---|---|
| Kepala (+ 'berulang', 'Filter') | 24-78 | 76-116 |
| `.tq-bar` | 94-134 | 132-176 (+32 baris 'Untuk Rian · Ubah' = 208) |
| Tab kolom | tidak ada | 220-264 |
| Papan / kolom terlihat | 150-784 (4 kolom, kartu mulai y=202) | 276-796 (satu kolom, kartu mulai 276; ±3,7 kartu) |
| `.page` `scrollHeight` | **800** (apa pun isinya) | **760** (apa pun isinya) |
| Skrol internal | `.kb-cards` (6 kartu ≈ 870 px dalam ≈560) | `.kb-cards` (6 kartu ≈ 870 dalam ≈520) |

Tugas: 'Beri tugas baru' y=94-134 / 132-176 (lulus); 'Perlu Anda' tab y=220-264 di 375 dan kolom 150-784 di 1280 (lulus bahkan bila ada 40 kartu Antre); 'Dikerjakan' sama; 'Tugas berulang' y=42-78 / 76-116.

## 4. Aplikasi: perubahan (`connections.tsx`, `skills-ui.tsx`, `pages.css`; `pick-ui.tsx` tidak berubah)

### 4.1 Susunan dan keadaan data

`<section className="page apps">`: `PageHead` (tidak berubah) → banner (`result`/`joined`/`saved`/`problem`, tidak berubah) → `.tabs` (tidak berubah) → toolbar → `div.apps-scroll` (berisi 'Tersambung', katalog). State baru: `const [limit, setLimit] = useState(12)`. Hapus `groups.map(...)` berkepala kategori; katalog jadi satu daftar rata.

```css
@media (min-width: 901px) {
  .page.apps { overflow: hidden; padding-bottom: var(--s-4); }
  .apps-scroll { flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; display: flex; flex-direction: column; gap: var(--s-4); padding-right: var(--s-1); scrollbar-gutter: stable; }
}
@media (max-width: 900px) { .apps-scroll { display: flex; flex-direction: column; gap: var(--s-4); } }   /* halaman menggulung biasa */
```
Ukuran 1280x800: kepala 24-78, tab 94-138, toolbar 150-190, area gulir 206-784 (578 px): 'Tersambung' 206-230, baris 238-366 (3 baris dalam 2 kolom: Drive|Gmail, Canva), 'Aplikasi lain · 37' 382-406, kartu mulai 414 (3 baris = 9 kartu terlihat sampai 784). `.page` `scrollHeight` = 800.

### 4.2 Toolbar satu baris

```tsx
<div className="apps-tools apps-tools-row">
  <input type="search" … placeholder="Cari aplikasi" />
  <div className="apps-cats" role="group" aria-label="Kategori">…Semua + kategori (tidak berubah)…</div>
</div>
```
```css
.apps-tools-row { flex-direction: row; align-items: center; gap: var(--s-3); min-width: 0; }
.apps-tools-row input[type="search"] { flex: none; width: 240px; max-width: 40%; height: 40px; }
.apps-tools-row .apps-cats { flex: 1; min-width: 0; flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; padding-bottom: 0; -webkit-mask-image: linear-gradient(to right, black calc(100% - 24px), transparent); mask-image: linear-gradient(to right, black calc(100% - 24px), transparent); }
.apps-tools-row .apps-cats button { flex: none; }
@media (max-width: 640px) {
  .apps-tools-row { flex-direction: column; align-items: stretch; gap: var(--s-2); }
  .apps-tools-row input[type="search"] { width: 100%; max-width: none; }
  .apps-tools-row .apps-cats { margin-inline: 0; padding-inline: 0; }   /* menggantikan margin negatif lama */
}
```
Tab 'Keahlian pegawai' memakai toolbar yang sama (hanya input pencarian, `max-width: 420px`). Tinggi desktop 40 px; ponsel 40 + 8 + 32 = 80 px.

### 4.3 'Tersambung' yang dapat ditindak

Daftar: `linkedOauth` (Drive/Gmail bawaan, status `connected` / `needs_scope` / `reconnect` / `broken`) + `linkedHermes` (status `connected`), memakai fungsi `oauthCard(id, 'row')` dan `appCard(a, 'row')` yang sama (parameter kedua menambah kelas `app-row` pada `<li>`; logika tombol, konfirmasi 'Putuskan X?', `pickDrive`, 'Cara kerja tombol draf', admin hint, chip status tidak berubah).

```tsx
<section className="apps-group apps-linked-sec" aria-labelledby="g-linked">
  <header><h2 id="g-linked">Tersambung{linkedCount > 0 && <span className="quiet"> · {linkedCount}</span>}</h2></header>
  {linkedCount === 0
    ? <p className="quiet">Belum ada aplikasi tersambung. Pilih salah satu di bawah.</p>
    : <ul className="app-rows">{linkedOauth.map((id) => oauthCard(id, 'row'))}{linkedHermes.map((a) => appCard(a, 'row'))}</ul>}
</section>
```
Aplikasi yang bermasalah (`reconnect`, `broken`, `needs_scope`) diurutkan lebih dulu (`.sort` stabil dengan kunci status) dan tombol 'Sambungkan ulang' tetap `btn primary`.

```css
.app-rows { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--s-2); }
.app-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; column-gap: var(--s-3); row-gap: 2px; min-height: 56px; padding: var(--s-2) var(--s-3); }
.app-row > .app-card-head { grid-column: 1; grid-row: 1; }
.app-row .app-card-head .app-mark { width: 32px; height: 32px; }
.app-row > .app-card-act { grid-column: 2; grid-row: 1 / span 3; margin: 0; padding: 0; justify-content: flex-end; }
.app-row > p { grid-column: 1; margin: 0; }
.app-row > p:not(.connect-acct):not(.connect-warn):not(.quiet):not(.note-box) { display: none; }   /* deskripsi hanya di katalog */
.app-row > .connect-acct { font-size: var(--t-small); color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.app-row > .connect-acct b { font-weight: 500; color: inherit; }
.app-row > .note-box, .app-row > .connect-warn { grid-column: 1 / -1; }
.app-row .app-card-act .confirm-actions { flex-wrap: wrap; justify-content: flex-end; }
@media (max-width: 900px) { .app-rows { grid-template-columns: minmax(0, 1fr); } }
@media (max-width: 640px) { .app-row > .app-card-act { grid-column: 1 / -1; grid-row: auto; justify-content: flex-start; } .app-row { row-gap: var(--s-1); } }
```
Teks akun jadi `Akun: <b>email</b>` (ganti 'Tersambung sebagai' pada baris `row` saja; kartu katalog tidak menampilkan akun). Chip 'Tersambung' dihapus pada baris (judul seksi sudah menyatakannya); chip peringatan tetap. Tinggi baris: Canva 56 px; Drive 56 + 20 (akun) = ±76 px (dua tombol 'Pilih dari Drive' + 'Putuskan' sejajar kanan); Gmail ±76 px. Ponsel: tombol turun ke baris kedua (Drive ±100 px, Gmail ±100 px, Canva ±56 px).

### 4.4 Katalog 'Aplikasi lain' dan batas 12

```tsx
const catalog = groups.flatMap((g) => [...g.oauth.map((id) => ({ k: 'o' as const, id })), ...g.apps.map((a) => ({ k: 'a' as const, a }))])
  .filter(/* sudah muncul di 'Tersambung' disaring (status connected/needs_scope/reconnect/broken, dan app Hermes yang terhubung) */)
const shown = catalog.slice(0, limit)
<section className="apps-group" aria-labelledby="g-catalog">
  <header><h2 id="g-catalog">Aplikasi lain<span className="quiet"> · {catalog.length}</span></h2></header>
  <ul className="app-grid app-mini-grid">{shown.map((x) => (x.k === 'o' ? oauthCard(x.id, 'mini') : appCard(x.a, 'mini')))}</ul>
  {catalog.length > limit && <button type="button" className="btn soft apps-more" onClick={() => setLimit((n) => n + 12)}>Tampilkan lebih banyak ({catalog.length - limit} lagi)</button>}
  {catalog.length === 0 && (term || only) && <p className="quiet">Tidak ada aplikasi yang cocok. <button type="button" className="btn link small" onClick={() => { setQ(''); setOnly('') }}>Hapus pencarian</button></p>}
</section>
```
`groups` tetap dihitung seperti sekarang (kategori + `hit()`), hanya tidak lagi dirender per kategori. Aplikasi bawaan (Drive/Gmail) yang belum tersambung muncul paling awal pada urutan `Semua` (karena `oauth` mendahului `apps` dalam `g`; kategori 'docs' dan 'comms' berurutan: tambahkan `sort` stabil: `k === 'o'` lebih dulu). Pencarian/kategori mengubah `catalog`; `limit` kembali 12 saat `q` atau `only` berubah (`useEffect(() => setLimit(12), [q, only])`).

Kartu `mini` (class `app-mini`; kolom grid sama `.app-grid`, minmax 250 → 3 kolom di 1280, 1 di 375): 

```css
.app-mini-grid { grid-template-columns: repeat(auto-fill, minmax(min(100%, 280px), 1fr)); gap: var(--s-2); }
.app-mini { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; column-gap: var(--s-3); row-gap: var(--s-1); padding: var(--s-3); }
.app-mini > .app-card-head { grid-column: 1; grid-row: 1; }
.app-mini .app-card-head .app-mark { width: 32px; height: 32px; }
.app-mini > .app-card-act { grid-column: 2; grid-row: 1; margin: 0; padding: 0; }
.app-mini > .app-card-act .btn { height: 32px; padding: 0 var(--s-3); }
.app-mini > p { grid-column: 1 / -1; grid-row: 2; margin: 0; font-size: var(--t-small); color: var(--muted); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.app-mini > .connect-warn, .app-mini > .note-box, .app-mini > .quiet { grid-column: 1 / -1; -webkit-line-clamp: unset; display: block; }
.apps-more { align-self: flex-start; margin-top: var(--s-2); }
```
Tinggi kartu ±96 px (12 + 32 + 4 + 36 deskripsi + 12): 12 kartu = 4 baris × 96 + gap = ±420 px di 1280, 12 × 108 = ±1300 px di 375. Tombol aksi kartu katalog: 'Hubungkan' (`btn soft`), 'Segera hadir' (chip, tanpa tombol, perilaku lama), 'Belum diatur admin' (admin). Chip status tetap di bawah judul.

### 4.5 Tab 'Keahlian pegawai' (`skills-ui.tsx` `SkillsSection`)

```tsx
<section className="apps-group" aria-labelledby="g-skills">
  <header><h2 id="g-skills" className="sr">Keahlian pegawai</h2><p className="quiet small">Kemampuan bawaan yang bisa dinyalakan atau dimatikan untuk tiap pegawai.</p></header>
  …
  <li key={s.name} className="app-card skill-card app-mini" data-skill={s.name}>
    <div className="app-card-head"><div className="app-top"><h3>{label}</h3></div></div>
    <div className="app-card-act"><button type="button" className="btn soft sm" onClick={() => setOpen(s.name)} aria-label={`Atur ${label}`}>Atur</button></div>
    <p>{text}</p>
    <p className="quiet small" title={who.join(', ')}>{who.length ? `Dipakai: ${who.slice(0, 2).join(', ')}${who.length > 2 ? ` +${who.length - 2}` : ''}` : 'Belum dipakai pegawai mana pun.'}</p>
  </li>
```
Kartu keahlian memakai CSS `.app-mini` (4.4) dengan baris ketiga (`Dipakai`): `.skill-card > p.quiet { -webkit-line-clamp: 1 }`. Tinggi ±112 px; 11 kartu = 4 baris di 1280 (3 kolom): 4 × 112 + 3 × 8 = 472 px; toolbar 150-190, kartu 206-678, halaman tidak menggulung. Dialog 'Atur' (pemilih pegawai per keahlian, `AgentRow`) tidak berubah.

### 4.6 Tidak berubah / keadaan

Loading: `Loading shape="ledger"` selama `!ready`, di dalam `.apps-scroll` (tinggi min 160 px). Galat: `ErrorLine` + 'Coba lagi' per sumber (`conns`, `cat`), data parsial tetap tampil. Dialog `ConnectDialog`, `SourcePicker`, banner hasil OAuth, `forwardOldConnectLink`, `AppsLink` tidak berubah. Admin: 'Kode: `id`', `AdminHint`, 'Belum diatur admin' tetap.

### 4.7 Perkiraan setelah (Aplikasi)

[INFERENCE] belum dirender.

| Elemen | 1280x800 | 375x812 |
|---|---|---|
| Kepala + tab | 24-78 / 94-138 | 76-130 / 146-190 |
| Toolbar (cari + chip) | 150-190 | 206-286 |
| 'Tersambung' judul + baris | 206-230 / 238-366 (Drive, Gmail satu deret; Canva di bawahnya) | 302-326 / 334-~600 (Drive 100, Gmail 100, Canva 56, gap 8) |
| 'Aplikasi lain · 37' | 382-406, kartu 414-784 (9 kartu) | ≈616-640, kartu pertama ≈648-756 |
| `.page` `scrollHeight` | **800** (gulir internal `.apps-scroll`) | ≈ **2200** (3 layar; sebelumnya 7688) |
| Tab Keahlian | ≈ 800 (tanpa skrol) | ≈ 1450 (sebelumnya 2481) |

Tugas: 'Sambungkan Drive/Gmail' baris di y=238-314 (lulus kedua-duanya, sebelumnya Gmail 2381); 'Cari aplikasi lain' y=150-190 / 206-246; 'Atur keahlian' tab 94-138 / 146-190, 'Atur' kartu pertama ±222-254 (1280).

## 5. Pengaturan: perubahan (`Settings.tsx`, `workspace.css` baru di akhir berkas)

### 5.1 Kerangka: satu bagian sekali tampil, isi menggulung sendiri

Kerangka `set-layout` (nav kiri + `set-body`) dipertahankan. Tambahkan `className="page set-page"` pada `<section>`. `Settings` merender label tab pendek di ponsel:

```tsx
{SECTIONS.map((s) => (
  <a key={s.id} href={`#/pengaturan/${s.id}`} aria-current={s.id === cur ? 'page' : undefined} aria-label={s.label}>
    {s.id === 'paket' ? <>Paket<span className="hide-sm"> dan biaya</span></> : s.label}
  </a>
))}
```
(`aria-label` memastikan pembaca layar tetap membaca 'Paket dan biaya'.)

```css
@media (min-width: 901px) {
  .page.set-page { overflow: hidden; padding-bottom: var(--s-4); }
  .set-layout { flex: 1; min-height: 0; }
  .set-body { height: 100%; min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding-right: var(--s-2); scrollbar-gutter: stable; }
}
@media (max-width: 640px) {
  .set-nav { padding-right: 0; -webkit-mask-image: none; mask-image: none; }
  .set-nav a { padding: 12px 8px; min-width: 48px; text-align: center; }
  .set-h { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }  /* judul bagian = tab aktif */
}
```
Tambahkan `className="set-h"` pada `<h2>` pertama setiap bagian (Umum, Notifikasi, Keamanan dan izin, Paket dan pemakaian, Data). Ukuran tab 375: Umum 43+16=59, Notifikasi 77, Keamanan 85, Paket 39+16=55, Data 47 = **323 ≤ 343**; tinggi 44. Fokus: bawaan `:focus-visible`; `aria-current="page"` tetap.

### 5.2 Baris pengaturan ringkas

`Row` mendapat prop `stack?: boolean` → `className={'set-row' + (stack ? ' set-row-stack' : '')}`; hanya 'Nama bisnis' memakai `stack` (input lebar). Aturan ponsel lama `.set-row { flex-direction: column; align-items: stretch }` diganti:

```css
@media (max-width: 640px) {
  .set-row { flex-direction: row; align-items: center; justify-content: space-between; gap: var(--s-3); padding: var(--s-2) 0; min-height: 56px; }
  .set-row.set-row-stack { flex-direction: column; align-items: stretch; gap: var(--s-2); }
  .set-text small { font-size: 12px; }
  .set-ctl select { max-width: 160px; }
  .set-ctl .btn { min-height: 40px; }
  .set-check { min-height: 44px; }                       /* target sentuh */
  .set-sec { gap: var(--s-2); }
}
```
Perkiraan 375x812 Umum: nav 146-190; Nama bisnis 202-302 (100), Bahasa 302-358, Zona waktu 358-414, Tema 414-470, Mode admin 470-526; berakhir **y≈530** (sebelumnya 866, terpotong). Notifikasi: 4 baris × 56-60 = ±230 → y≈430. Nama bisnis, `markNamed()`, tombol Simpan nonaktif hingga ada perubahan, pesan `problem-bar` tetap.

### 5.3 Paket dan biaya

Tampilkan angka dulu, lalu rincian. DOM:

```tsx
<h2 className="set-h">Paket dan pemakaian</h2>
<dl className="kv kv-wide plan-sum">…tidak berubah (Paket aktif, Biaya bulan ini, [token admin], Pegawai, Tim, Tugas berjalan bersamaan)…</dl>
<h2>Rincian biaya</h2>
{…catatan, loading, error tidak berubah…}
{d && <UsageDetail u={d} admin={admin} />}
```
`UsageDetail` (non-admin): `<div className="usage-split">` berisi `Split` 'Per pegawai' dan blok 'Per hari' (pindah ke dalam grid; admin tetap: Per pegawai | Per model, lalu Per hari di bawah seperti sekarang).

```tsx
// Split mendapat prop `clamp?: number` (dipakai ponsel)
const [all, setAll] = useState(false)
<ul className="usage-list" data-clamp={(!all && rows.length > 5) || undefined}>…</ul>
{rows.length > 5 && <button type="button" className="btn link small usage-more" aria-expanded={all} onClick={() => setAll((v) => !v)}>{all ? 'Tampilkan lebih sedikit' : `Lihat semua ${rows.length}`}</button>}
// Per hari
<details className="usage-days" open={wide}><summary><h3>Per hari</h3></summary><ul className="usage-list">…</ul></details>
const [wide] = useState(() => window.matchMedia('(min-width: 641px)').matches)
```
```css
.kv.kv-wide.plan-sum { grid-template-columns: 200px minmax(0, 1fr); gap: 6px var(--s-4); }
.usage-days summary { cursor: pointer; list-style: none; }
.usage-days summary::-webkit-details-marker { display: none; }
.usage-days summary h3 { display: inline; }
.usage-more { display: none; }
@media (max-width: 640px) {
  .usage-list[data-clamp] li:nth-child(n+6) { display: none; }
  .usage-more { display: inline-flex; }
  .kv.kv-wide.plan-sum { grid-template-columns: minmax(0, 1fr) auto; gap: 4px var(--s-3); }   /* label kiri, nilai kanan */
  .kv.kv-wide.plan-sum dt, .kv.kv-wide.plan-sum dd { margin: 0; padding: 6px 0; border-bottom: 1px solid var(--rule); }
  .usage-days summary h3::after { content: " ▾"; color: var(--muted); }
}
@media (min-width: 641px) and (max-width: 760px) { .usage-split { grid-template-columns: repeat(2, minmax(0, 1fr)); } }   /* menggantikan satu kolom ≤760 untuk non-admin */
```
`.set-body` di bagian Paket tidak dibatasi 720 px di non-admin? Dibiarkan 720: dua kolom 340 px cukup (nama + `$0.27` + bar). Perkiraan 1280: ringkasan 102-300 (5 baris × 33 + judul), 'Rincian biaya' 316-346, catatan 362, Per pegawai / Per hari mulai 394, 9 baris × 43 = 387 → **berakhir ≈ 790**, `.set-body` hampir tidak menggulung (cadangan: gulir internal). Ponsel: ringkasan 5 × 40 = 200 (209-420), Rincian 436, catatan 470, Per pegawai 5 baris × 40 = 200 (506-706) + tombol 'Lihat semua 9' 706-742, 'Per hari ▾' 758-: **cek biaya terlihat di y≈250-290; halaman ≈ 880** (sebelumnya 1294), skrol sedikit untuk 'Per hari'.

Keamanan (tabel `plain` bawaan): tidak berubah selain `.set-h`; bila `rows.length > 6` tabel menggulung dalam `.set-body` (desktop) atau halaman (ponsel kartu per baris, aturan `.act` lama). Data: tidak berubah.

### 5.4 Keadaan

Loading `Loading text="Memuat paket..."` (tinggi min 160 px di `.set-sec`), galat `ErrorLine` + 'Coba lagi', 'Data paket belum terbaca.' kosong: semua tetap; `problem-bar` untuk gagal simpan tetap di dasar bagian. Tidak ada pesan baru.

### 5.5 Perkiraan setelah (Pengaturan)

| Bagian | 1280x800 isi / `.page` | 375x812 isi |
|---|---|---|
| Umum | 541 / 800 | **≈530** (866) |
| Notifikasi | 459 / 800 | ≈430 (742) |
| Keamanan | 451 / 800 | ≈ 560 (600) |
| Paket dan biaya | **≈790** tanpa skrol (1147) | ≈**880** (1294); angka biaya y≈250-290 |
| Data | 296 / 800 | ≈ 400 (476) |

Semua tab terlihat di 375 (kanan 359). 'Unduh' pada Data y≈330-370 (375); 'Nama bisnis' input y≈217-253 (375).

## 6. Pengetahuan: perubahan (`Pengetahuan.tsx`, `kb-ui.tsx` tidak berubah, `workspace.css`)

### 6.1 Kepala dengan aksi, tambah link, daftar

`MySources` kini mengembalikan `<> <PageHead …/> <div className="kb-sec kb-fit"> … </div> </>` (komponen hanya dipakai di `Pengetahuan`); `Pengetahuan()` membungkus: `<section className={'page kb-page'}><MySources />{admin && …}</section>` (dokumen bawaan admin pindah ke dalam area gulir, lihat bawah). Urutan:

```tsx
<PageHead
  title="Pengetahuan"
  sub="Ajari pegawai AI tentang bisnis Anda lewat berkas dan link."
  actions={<>
    <button className="btn primary" disabled={!!busy} onClick={() => file.current?.click()}>Unggah berkas</button>
    <button className="btn outline" disabled={!!busy} onClick={() => setPicker('gdrive')}>Pilih dari Drive</button>
  </>}
/>
<div className="kb-sec kb-fit">
  <input ref={file} type="file" hidden multiple accept={KB_ACCEPT} aria-label="Pilih berkas" onChange={…tidak berubah…} />
  <p className="quiet small kb-intro">Semua pegawai membaca ini dan menyebut sumbernya. Berkas: {KB_TYPES_TEXT}. Drive pribadi perlu disambungkan dulu di <a className="kb-link" href="#/aplikasi">Aplikasi</a>.</p>
  <form className="set-inline kb-link-form" onSubmit={…tidak berubah…}>
    <input value={url} … placeholder="Tempel link website atau Drive" aria-label="Alamat web atau link Google Drive" inputMode="url" />
    <button className="btn outline" type="submit" disabled={!!busy || !url.trim()}>Tambah link</button>
  </form>
  {problem && <p className="problem-bar small" role="alert">…tidak berubah…</p>}
  <header className="kb-list-head">
    <h2>Tersimpan{items.data && <span className="quiet"> · {items.data.length}</span>}</h2>
    {items.data && items.data.length > 8 && <input type="search" className="kb-find" value={find} onChange={(e) => setFind(e.target.value)} placeholder="Cari dokumen" aria-label="Cari dokumen" />}
  </header>
  <div className="kb-scroll">
    {loading / error / busy row / empty …}
    <ul className="kb-list">…baris…</ul>
    {admin && <BuiltinDocs />}
  </div>
</div>
```
`find` (state baru) menyaring `items.data` menurut nama/sumber (huruf kecil); 'Tidak ada dokumen yang cocok. [Hapus pencarian]' bila kosong. Pengantar satu baris di desktop, dua baris di ponsel (12 px).

```css
.page.kb-page { overflow: hidden; padding-bottom: var(--s-4); }
.kb-fit { flex: 1; min-height: 0; display: flex; flex-direction: column; gap: var(--s-3); }
.kb-intro { margin: 0; }
.kb-link-form { flex: none; display: flex; gap: var(--s-2); }
.kb-link-form input { flex: 1; min-width: 0; width: auto; height: 40px; }
.kb-link-form .btn { height: 40px; }
.kb-list-head { flex: none; display: flex; align-items: center; justify-content: space-between; gap: var(--s-3); }
.kb-list-head h2 { margin: 0; font-size: var(--t-lead); font-weight: 600; }
.kb-find { width: 240px; max-width: 50%; height: 36px; }
.kb-scroll { flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; scrollbar-gutter: stable; }
.kb-row { min-height: 56px; padding: var(--s-2) 0; }
@media (max-width: 640px) {
  .page.kb-page .page-head .head-actions { display: flex; flex: 1 1 100%; gap: var(--s-2); }
  .page.kb-page .page-head .head-actions .btn { flex: 1; height: 40px; }
  .page.kb-page .page-head p { display: none; }
  .kb-row { min-height: 64px; flex-wrap: nowrap; row-gap: 0; }
  .kb-find { width: 100%; max-width: none; }
}
```
(`PageHead` dipakai tanpa prop `inline`: di ≤640 px `.page-head` membungkus, dan `.head-actions` ber-`flex: 1 1 100%` turun ke baris sendiri di bawah judul.) Tinggi 1280: kepala 24-78 (tombol di kanan), pengantar 94-114, form URL 126-166 (40), judul daftar 178-208, daftar 216-784 (568 px = **10 baris 56 px**, sebelumnya 7 baris di y>289). 375: kepala 76-112 (judul 36) + tombol 124-164 (40) + pengantar 2 baris 176-214 + form 226-266 + judul 278-308 + daftar 316-796 (**7,5 baris 64 px**).

### 6.2 Baris dokumen

Baris desktop (≥641): `[nama + meta] [pil Memproses/Gagal bila ada] [Lihat] [Perbarui bila ada] [Hapus]`. Perubahan DOM per baris: pil `STATUS_TEXT` hanya untuk `status !== 'ready'`; pil jenis (`Website`, `Google Drive`) tetap di depan nama untuk non-berkas; urutan meta: `ukuran · tanggal`, sumber URL satu baris ellipsis di bawah nama (hanya non-berkas). `kb-open` (tombol nama) tetap membuka `KbPreview`. Ponsel (≤640): nama + meta di kiri (flex 1, ellipsis), `Lihat` dan `Hapus` di kanan masing-masing ≥44 px lebar (`btn quiet-btn sm`, `min-height: 44px` lewat `.kb-list .btn` yang sudah ada di workspace.css:243). 'Perbarui' (hanya URL/Drive) ke menu `⋯`: tidak dibuat; tampil sebagai tautan kecil di baris meta (`btn link small`) agar tidak menambah tombol ketiga di kanan. Konfirmasi hapus (`confirm-actions`) menggantikan tombol Hapus inline seperti sekarang (baris sementara 2 deret, boleh).
Hapus aturan lama ponsel yang memecah baris (`.kb-row { flex-wrap: wrap }`, `.kb-rtext { flex: 1 1 100%; order: 1 }`, `.kb-row > .pill:first-child { order: 0 }` dst. di pages.css:305-310): `workspace.css` menimpa dengan `.kb-row { flex-wrap: nowrap }` dan `.kb-rtext { flex: 1 1 0; order: 0 }`; pembersihan baris lama dilakukan Worker A (lihat bagian 9).

### 6.3 Keadaan

Memuat: `Loading shape="lines"` di dalam `.kb-scroll`; galat: `ErrorLine` + 'Coba lagi' di `.kb-scroll`; kosong: `.kb-empty` ('Belum ada pengetahuan.' + 'Unggah berkas atau tempel link di atas.') di `.kb-scroll`; memproses: baris `data-s="processing"` di puncak `.kb-scroll`, `aria-live="polite"` (tetap). `problem-bar` dari unggah gagal tetap di atas judul daftar. Drag file ke halaman: tidak ada (tidak ada sekarang).

## 7. Tim: perubahan (`Group.tsx`, `chat.css`; `ChatLayout.tsx` `GroupLayout` tidak berubah)

Desktop dan rail tim sudah memenuhi satu layar (tidak ada perubahan selain 7.3). Pertahankan: rail menggulung sendiri (`.rail-body > ul`), `.scroll` pesan, 'Tim baru' di kepala rail, `Intro` di `#/grup` ponsel.

### 7.1 Kepala satu deret di ponsel (`Group.tsx`)

Ganti `<header className="convo-head">` menjadi pola Chat (`Chat.tsx` bagian `convo-head-chat`): tambahkan `const [more, setMore] = useState(false)`, `const moreBtn = useRef<HTMLButtonElement>(null)` dan efek penutup klik-luar yang sama seperti `ChatLayout` (`document.addEventListener('click', …)` saat `more`). Import `DOTS` dan `PENCIL` dari `./ui` (sudah ada `Icon`, `PENCIL`).

```tsx
<header className="convo-head convo-head-chat convo-head-group">
  <button className="btn soft sm rail-open" onClick={onRail}>Daftar tim</button>
  <div className="convo-title">
    …h1 / rename (tidak berubah, teks nama dibungkus `<span className="title-text">`)…
    <p title={members.map((m) => m.name).join(', ')}>{members.map((m) => m.name).join(', ') || 'Belum ada anggota'}{running ? ' · diskusi berjalan' : ''}</p>
  </div>
  <span className="avatar-stack" aria-hidden="true">…tidak berubah…</span>
  <span className="convo-extras">
    <button className="btn soft sm" onClick={() => setDialog({ kind: 'group', id })}>Atur anggota</button>
    <PanelButtons />
  </span>
  <span className="convo-more" onKeyDown={(e) => { if (e.key === 'Escape') { setMore(false); moreBtn.current?.focus() } }}>
    <button ref={moreBtn} className="icon-btn" aria-label={`Menu tim ${group.name}`} aria-haspopup="menu" aria-expanded={more} onClick={(e) => { e.stopPropagation(); setMore((v) => !v) }}><Icon d={DOTS} /></button>
    {more && (
      <div className="popmenu" role="menu" onClick={(e) => e.stopPropagation()}>
        <button role="menuitem" onClick={() => { setMore(false); setDialog({ kind: 'group', id }) }}><Icon d={PENCIL} />Atur anggota</button>
        <div role="none" className="convo-menu-row" onClick={() => setMore(false)}><PanelButtons /></div>
      </div>
    )}
  </span>
</header>
```
CSS (`chat.css`, tambah setelah aturan `.convo-head-chat` yang ada, `≤640`): `.convo-head-group .convo-title p { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }`, `.convo-head-group .convo-title h1 { min-width: 0; }`, `.convo-head-group .title-btn { display: inline-flex; align-items: center; gap: 6px; max-width: 100%; min-width: 0; }`, `.convo-head-group .title-text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }`. Aturan `.convo-head-chat { flex-wrap: nowrap; min-height: 56px; … }`, `.convo-extras { display: none }`, `.convo-more { display: block }` sudah berlaku karena kelas `convo-head-chat` dipakai ulang (komentar di chat.css diubah menjadi "kepala percakapan pegawai dan tim"). Desktop: tidak berubah (`.convo-extras` tampil, `.convo-more` tersembunyi). Judul: 343 - 88 ('Daftar tim') - 40 (⋯) - 16 (gap) ≈ **199 px**: 'Tim Konten Colorbox ✎' (±170) utuh; subjudul ellipsis. Tinggi kepala 108 → **56 px**; pesan 516 → ±568 px.

### 7.2 Komposer (`Group.tsx`)

```tsx
const phone = useMedia('(max-width: 640px)')   // hook lokal 6 baris, sama dengan useNarrow
placeholder={running ? RUNNING_PLACEHOLDER : phone ? 'Tulis tugas untuk tim, atau @nama' : 'Tulis pesan. Ketik @ untuk menyebut anggota.'}
```
Komposer 122 → ±98 px. Tidak ada perubahan lain (`KbAttach`, antrean, 'Berhenti', 'Kirim sekarang' tetap).

### 7.3 Pita 'Rencana menunggu persetujuan' (`Group.tsx`)

`const pending = [...msgs].reverse().find((m) => m.plan?.state === 'pending')`. Bungkus `PlanCard` di `GroupBubble` dengan `id={`plan-${m.id}`}` pada `.gmsg` (elemen `div.msg`). State `planOut` dihitung di `onScroll` yang sudah ada dan setelah `msgs` berubah:

```ts
function checkPlan() {
  const el = pending && document.getElementById(`plan-${pending.id}`)
  const box = scroller.current
  if (!el || !box) return setPlanOut(false)
  const a = el.getBoundingClientRect(), b = box.getBoundingClientRect()
  setPlanOut(a.bottom < b.top + 40 || a.top > b.bottom - 40)
}
```
Render tepat di atas `.composer-wrap` pertama (di dalam `composer-wrap`, sebelum antrean):
```tsx
{pending && planOut && (
  <div className="plan-pin" role="status">
    <span>Rencana menunggu persetujuan Anda.</span>
    <button type="button" className="btn primary sm" onClick={() => document.getElementById(`plan-${pending.id}`)?.scrollIntoView({ block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })}>Lihat dan setujui</button>
  </div>
)}
```
```css
.plan-pin { display: flex; align-items: center; justify-content: space-between; gap: var(--s-3); margin-bottom: var(--s-2); padding: var(--s-2) var(--s-3); border-radius: var(--radius-control); background: var(--warn-bg); color: var(--warn-ink); font-size: var(--t-small); font-weight: 500; }
.plan-pin .btn { flex: none; min-height: 36px; }
```
Warna: peringatan lembut (arti = menunggu Anda, sama dengan pil 'Perlu persetujuan'), tombol tetap `.btn.primary` hitam. Tinggi 52 px (36 + 16) memakan sebagian pesan hanya saat perlu. Tidak memengaruhi `PlanCard` (tombol 'Setujui rencana' tetap di kartu).

### 7.4 Perkiraan setelah (Tim)

| Elemen | 1280x800 | 375x812 |
|---|---|---|
| Kepala | 0-64 (tidak berubah) | 52-108 (sebelumnya 52-160) |
| Pesan | 64-660 | 108-~676 (568 px) |
| Komposer | 660-760 | ~676-774 (98 px) |
| 'Beri tugas ke tim' | 660-760 | 676-774 |
| 'Buka tim lain' | rail 58-160 | 'Daftar tim' 60-100 |
| 'Setujui rencana' | di kartu atau pita (y≈700-750 di komposer) | pita 52 px di atas komposer, ≈624-676 |

## 8. Tidak boleh mundur (keputusan yang dipertahankan)

Dari spec sebelumnya: kosakata 'pegawai' dan 'Tingkat ketelitian'; `roleLabel`; 'Atur' membuka `EditBotDialog`; token hanya mode admin (baris token Paket tetap `admin &&`); biaya dalam dolar sesuai label BFF; galat selalu dengan 'Coba lagi'; tautan 'Lihat batasan keamanan'; 'Tampilkan langkah kerja' (teks penuh tetap).
Jadwal: seret kartu hanya dari 'Perlu Anda' dan 'Selesai' ke Antre, 'Dikerjakan' tidak pernah jadi sasaran, rencana tidak diseret; konfirmasi untuk verba berbahaya (`a.confirm`); pil 'Penting', 'Gagal', 'Dibatalkan', status hanya admin; 'dan N lainnya' (batas 40 per kolom); Filter pegawai/tim dan tampilan Arsip; pembuat 'Tugas berulang' dengan copy yang sama; Jeda/Lanjutkan/Hapus dengan konfirmasi 'Hapus tugas berulang "…"? …'; Enter menyimpan tugas baru; `Agen` → `Pegawai` pada `kc-note`/`COLUMN_HINT`; `TaskPanel` (balas, revisi, 'Riwayat').
Aplikasi: status 'Tersambung', 'Perlu disambungkan ulang', 'Perlu perbaikan', 'Perlu izin tambahan', 'Segera hadir' (non-admin) vs 'Belum diatur admin' (admin); konfirmasi 'Putuskan X?'; 'Pilih dari Drive' (`SourcePicker`) dan banner 'N item disimpan ke Pengetahuan' + tautan; 'Cara kerja tombol draf' Gmail; tab terakhir tersimpan di `pegawai-ai.apps-tab`; Drive dan Gmail menyatu dengan kartu Hermes (OWN_AS_HERMES); admin: 'Kode', hint, catatan restricted scope; pencarian dan chip kategori; dialog 'Atur' keahlian.
Pengaturan: lima bagian dan rute `#/pengaturan/<id>`; satu kalimat per opsi; 'Nama bisnis' dengan `markNamed()` dan Simpan nonaktif sampai berubah; 'Mode admin' nyala/mati; tema tersimpan di `pa.theme`; keamanan baca-saja (satu baris 'Semua pegawai' bila sama); 'Unduh' riwayat chat; `Perkiraan` pil.
Pengetahuan: tiga cara menambah (unggah, Drive, link), 'Berkas: TXT, MD, CSV, PDF, DOCX (maksimal 10 MB)', tautan ke Aplikasi bila Drive belum tersambung (`needsDrive` + `DriveLink`), `KbPreview`, 'Perbarui', konfirmasi hapus, pesan galat per berkas, dokumen bawaan hanya admin.
Tim: 'Tim baru', rail menggulung sendiri, `Intro` ponsel, 'Atur anggota', 'Detail', ganti nama tim di judul, antrean pesan/steer/stop, `PlanCard` (Setujui/Revisi/Batalkan), 'Jadikan tugas'.
Umum: fokus `:focus-visible` bawaan; target sentuh ≥40-44 px di ponsel; `prefers-reduced-motion` (tidak ada animasi baru kecuali `scrollIntoView` smooth yang mematuhi preferensi); tema gelap lewat token (tidak ada warna keras baru; `--warn-bg/--warn-ink` atau pasangan yang dipakai `.pill.warn`).

## 9. Berkas yang disentuh worker (dibagi dua, tidak saling menimpa)

### Worker A: Jadwal & tugas + Aplikasi

| Berkas | Perubahan |
|---|---|
| `frontend/src/Kanban.tsx` | `useNarrow`, tab kolom + `onTabKey`, `QuickAdd` → `.tq-bar` di luar kolom (`opts`), dialog 'Tugas berulang' menggantikan `Recurring` `<details>`, kepala `head-inline`, `kb-cards`/`kb-note`/`kb-hint`, menu `⋯` `position: fixed`, kartu dipadatkan, kosong 'Hapus filter' (bagian 3) |
| `frontend/src/TaskPanel.tsx` | Hanya ukuran teks hasil (3.6) |
| `frontend/src/connections.tsx` | `limit`, 'Tersambung' sebagai baris (`oauthCard`/`appCard` terima `'row' \| 'mini'`), katalog rata + 'Tampilkan lebih banyak', toolbar satu baris, `apps-scroll` (bagian 4) |
| `frontend/src/skills-ui.tsx` | Kartu keahlian `app-mini`, judul sr-only, 'Dipakai: A, B +N' (4.5) |
| `frontend/src/pages.css` | Blok Kanban (`.kb-grid`, `.kb-col`, `.kb-cards`, `.kb-tabs`, `.kcard`/`.kc-*`, `.tq-*`, hapus `.kb-col ul`, `.kb-rec*` → `.kb-rec-list`), blok Aplikasi (`.apps-tools-row`, `.apps-cats` baris, `.app-rows`, `.app-row`, `.app-mini*`, `.apps-scroll`, `.apps-more`, hapus margin negatif ponsel `.apps-cats`), dan **setelah Worker B selesai** membersihkan aturan lama yang digantikan: `.set-row` ponsel kolom (pages.css:235), `.kb-row` ponsel (305-310), `.usage-split` satu kolom ≤760 (229) (lihat 5.3, 6.2) |
| `frontend/src/pick-ui.tsx` | Tidak berubah |

### Worker B: Pengaturan + Pengetahuan + Tim

| Berkas | Perubahan |
|---|---|
| `frontend/src/Settings.tsx` | `set-page`, `Row stack`, label tab pendek + `aria-label`, `.set-h`, Paket (`plan-sum`, `usage-more`, `<details>` Per hari, Per hari dalam grid non-admin) (bagian 5) |
| `frontend/src/Pengetahuan.tsx` | `PageHead` dengan aksi, `kb-fit`/`kb-scroll`, `find`, pil status hanya Memproses/Gagal, `BuiltinDocs` di dalam area gulir (bagian 6) |
| `frontend/src/kb-ui.tsx` | Tidak berubah |
| `frontend/src/Group.tsx` | Kepala `convo-head-chat convo-head-group` + menu ⋯, `useMedia` + placeholder, pita rencana + `id="plan-…"` (bagian 7) |
| `frontend/src/ChatLayout.tsx` | Tidak berubah (`GroupLayout` sudah memenuhi satu layar) |
| `frontend/src/chat.css` | `.convo-head-group` (ellipsis `p`, `title-btn`, `title-text`), `.plan-pin`; komentar `.convo-head-chat` diperbarui |
| `frontend/src/workspace.css` | Blok baru di akhir: `.page.set-page`, `.set-body`, `.set-nav` ponsel, `.set-row` ponsel, `.set-h`, `.plan-sum`, `.usage-*` tambahan, `.page.kb-page`, `.kb-fit`, `.kb-intro`, `.kb-link-form`, `.kb-list-head`, `.kb-find`, `.kb-scroll`, `.kb-row` (bagian 5-6). `workspace.css` dimuat terakhir (setelah `pages.css`) jadi menimpa aturan lama dengan spesifisitas sama; semua selektor baru diawali `.page.` / kelas khusus layar sehingga tidak bocor |

Urutan: A dan B bekerja paralel pada berkas masing-masing. `pages.css` hanya disentuh A. Pembersihan aturan lama dilakukan A setelah B melapor. Tidak ada berkas bersama lain; `ui-extra.tsx` (`PageHead`) tidak diubah (prop `inline` dan `actions` sudah ada).

## 10. Cara memverifikasi (untuk Main)

Login admin@pegawai.ai, mode admin mati (`localStorage` tanpa `pegawai-ai.admin-mode`). Emulasi 1280x800 (DPR 1) dan 375x812 (DPR 2, mobile), terang lalu `document.documentElement.dataset.theme='dark'`. **Tunggu isi selesai dimuat** (Aplikasi butuh lebih dari 3,5 dtk pada pemuatan pertama; ukur setelah `.app-card` ada): ukuran yang diambil sebelum itu menunjukkan `.page` = 800.

```js
// Tempel di konsol / tab.evaluate pada tiap rute. Mengembalikan kontainer yang menggulung dan top-bottom kontrol kunci.
(labels => {
  const sc = [...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 2 && ['auto','scroll'].includes(getComputedStyle(e).overflowY))
    .map(e => ({ c: String(e.className).slice(0, 40), sh: e.scrollHeight, ch: e.clientHeight }))
  const els = [...document.querySelectorAll('button,a,input,select,h1,h2,h3,summary,[role=tab]')]
  const pos = Object.fromEntries(labels.map(l => {
    const e = els.find(x => ((x.textContent || '') + (x.getAttribute('aria-label') || '')).trim().startsWith(l) || (x.placeholder || '').startsWith(l))
    if (!e) return [l, 'HILANG']
    const r = e.getBoundingClientRect()
    return [l, `${Math.round(r.top)}-${Math.round(r.bottom)}${r.right > innerWidth ? ' (di luar layar)' : ''}`]
  }))
  const p = document.querySelector('.page, .with-rail')
  return { hash: location.hash, page: p && { sh: p.scrollHeight, ch: p.clientHeight }, scrollers: sc, pos }
})(['Tambah','Tugas berulang','berulang','Filter','Perlu Anda','Dikerjakan','Cari aplikasi','Keahlian pegawai','Putuskan','Hubungkan','Nama bisnis','Paket','Data','Unduh','Unggah berkas','Tambah link','Tulis','Daftar tim'])
```
Rute: `#/kanban`, `#/aplikasi` (dan tab Keahlian lewat `localStorage['pegawai-ai.apps-tab']='skills'` + muat ulang), `#/pengaturan/umum|notifikasi|keamanan|paket|data`, `#/pengetahuan`, `#/grup/<id>`, `#/grup` (375). Untuk beban nyata Jadwal klon kartu seperti pada pengukuran sebelumnya (`document.querySelector('.kcard').cloneNode(true)` sampai 6 per `.kb-cards`) lalu pastikan `.page` tetap 800/760.

Kriteria lulus @1280x800:
1. Jadwal: `.page` `scrollHeight` = 800 dengan 6 kartu per kolom; `.kb-cards` menggulung (sh > ch) dan tidak ada skrol lain; `.tq-bar` top < 100; judul 4 kolom top < 170 dan tetap di tempat saat `.kb-cards` digulir; menu `⋯` pada kartu terbawah tidak terpotong (tepi menu di dalam viewport).
2. Aplikasi: `.page` = 800; `.apps-scroll` satu-satunya penggulung; baris 'Putuskan' Drive dan Gmail top < 330; kartu katalog pertama top < 440; ≤ 12 `.app-mini` di DOM; tab Keahlian: 11 kartu, semuanya bottom < 800 tanpa skrol.
3. Pengaturan: `.page` = 800 pada Umum/Notifikasi/Keamanan/Data; Paket `.set-body` `scrollHeight` ≤ ~810 dan 'Per hari' top < 800; tidak ada penggulung selain `.set-body`.
4. Pengetahuan: `.page` = 800; `.kb-scroll` satu-satunya penggulung; ≥ 9 `.kb-row` dengan bottom < 800; 'Unggah berkas' top < 90 (di kepala).
5. Tim: tidak berubah (rail, `.scroll`); `.plan-pin` hanya muncul bila ada rencana `pending` di luar layar.

Kriteria lulus @375x812:
1. Jadwal: `.page` = 760; `.kb-tabs` top < 240 dan 4 tab terlihat; tab awal 'Perlu Anda' bila ada isinya; `.tq-bar` top < 150 dan tinggi ≤ 80; kepala tinggi < 60; daftar kartu top < 300.
2. Aplikasi: baris Drive top < 340; Gmail top < 460; kartu katalog pertama top < 700; `.page` `scrollHeight` < 2600 (sebelumnya 7688).
3. Pengaturan: lima tab semua `right ≤ 359`; 'Mode admin' bottom < 760 pada Umum; Paket: angka biaya top < 340.
4. Pengetahuan: 'Unggah berkas' top < 150, URL top < 240; ≥ 6 baris dokumen terlihat; `.page` tidak menggulung (hanya `.kb-scroll`).
5. Tim: `.convo-head` tinggi ≤ 60; komposer tinggi ≤ 100; 'Daftar tim' top < 100.

Cek juga: urutan fokus papan tab Jadwal (panah kiri/kanan, Home, End), menu `⋯` bisa ditutup dengan Escape dan skrol, `Enter` menyimpan tugas dan input kembali fokus, dialog 'Tugas berulang' (Jeda/Lanjutkan/Hapus + konfirmasi), pencarian aplikasi kosong → 'Hapus pencarian', 'Tampilkan lebih banyak' menambah 12 kartu, Putuskan Drive (konfirmasi inline), Paket di ponsel ('Lihat semua 9', 'Per hari' membuka), tema gelap (pita `plan-pin`, tab Perlu Anda `pill warn`, `.app-row` `.connect-warn`), pegawai 0/1/11, tim 0/1/11 (rail), 40 kartu per kolom, dokumen 0/1/60 (pencarian muncul di > 8), teks panjang pada nama dokumen dan nama tim (ellipsis, tidak ada teks terpotong tanpa `title`).
