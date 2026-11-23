# Bukti Uji Lokal — Sprint 5 FE (Hari 1 + Hari 3)

**Ringkasan**

- Uji dijalankan pada **22 November 2026** di mesin lokal, branch `feat/frontend-prototype`, tanpa mengubah kode.
- Lingkungan: Vite `http://localhost:5173`, BFF `http://127.0.0.1:8090` (dipanggil lewat proxy `/bff/api`), Hermes gateway `8642`, Postgres `5433`. Semua halaman diuji pada **1280×800**; tangkapan 375 px memakai arsip `frontend/screenshots/sprint5-*`.
- Akun uji: `admin@pegawai.ai` (akun demo, peran `admin`, workspace `default`). Kata sandi tidak ditulis di dokumen ini.
- **Mode admin: mati** selama seluruh uji UI (localStorage `pegawai-ai.admin-mode` tidak diisi), kecuali disebut lain.
- **Sanitasi:** token diganti `<jwt>`, email akun tersambung diganti `<akun>` (pada tangkapan layar Aplikasi, teks email di DOM disamarkan menjadi `<akun>` sebelum gambar diambil; tidak ada data lain yang diubah). Tidak ada kata sandi, token, kunci, atau email pribadi di dokumen ini.
- **Verdict:** `PASS` = perilaku sesuai harapan; `FAIL` = perilaku salah; `BLOCKED(BE)` = tidak bisa diuji/dipakai karena kontrak Backend belum ada.

| # | Journeys | Verdict keseluruhan |
|---|---|---|
| 1 | Auth (Hari 1) | **PASS (FE) / BLOCKED(BE)** — UI benar, penegakan JWT di server belum ada |
| 2 | Kanban (Hari 1) | **PASS** untuk buat/pindah/arsip; **BLOCKED(BE)** untuk hapus permanen |
| 3 | KB lewat chat (Hari 1) | **PASS** |
| 4 | Connect Tools (Hari 1) | **PASS** |
| 5 | Konfigurasi karyawan (Hari 3) | **PASS**, satu defect FE (warna Netral tidak bisa dipulihkan lewat UI) |
| 6 | Responsif 375 px | **PASS** (bukti arsip) |

---

## 1. Auth (Hari 1)

### 1.1 Langkah dan hasil API

| # | Langkah | Permintaan | Harapan | Hasil teramati | Verdict |
|---|---|---|---|---|---|
| 1 | Login benar | `POST /bff/api/auth/login` body `{"email":"admin@pegawai.ai","password":"<rahasia>"}` | 200 + token + user | **200**; body berbentuk `{"token":"<jwt>","user":{"id":"default","name":"Super Admin","email":"admin@pegawai.ai","role":"admin","company":"Colorbox","plan_id":"bisnis"}}`; token 233 karakter, 3 segmen, berawalan `eyJ` | PASS |
| 2 | Kata sandi salah | `POST /bff/api/auth/login` | 401 + pesan | **401** `{"error":"Email atau kata sandi tidak cocok"}` | PASS |
| 3 | Email tidak dikenal | `POST /bff/api/auth/login` dengan email acak | 401, pesan tidak membocorkan apakah email terdaftar | **401** `{"error":"Email atau kata sandi tidak cocok"}` (pesan sama) | PASS |
| 4 | `/auth/me` token valid | `GET /bff/api/auth/me` + `Authorization: Bearer <jwt>` | 200 + user | **200** `{"ok":true,"user":{"id":"default","role":"admin","company":"Colorbox","plan_id":"bisnis","is_active":true,…}}` | PASS |
| 5 | `/auth/me` tanpa token | `GET /bff/api/auth/me` | 401 | **401** `{"error":"Kredensial login tidak valid atau belum login"}` | PASS |
| 6 | `/auth/me` token rusak | `GET /bff/api/auth/me` + `Authorization: Bearer <jwt-rusak>` | 401 | **401** `{"error":"Token autentikasi tidak valid atau rusak."}` | PASS |
| 7 | Logout | `POST /bff/api/auth/logout` | 200 | **200** `{"ok":true,"message":"Berhasil logout"}` | PASS |
| 8 | Token lama setelah logout | `GET /bff/api/auth/me` + token yang sama | 401 (sesi berakhir) | **200** — token masih berlaku | **BLOCKED(BE)** — logout tidak menginvalidasi token |
| 9 | Data terlindungi tanpa token | `GET /bff/api/bots` | 401 | **200**, 10 agen tenant `default` (Rian, Diana, Budi, Siti, …) | **BLOCKED(BE)** — fallback ke tenant admin |
| 10 | Data terlindungi token rusak | `GET /bff/api/bots` + `Authorization: Bearer <jwt-rusak>` | 401 | **200**, 10 agen tenant `default` | **BLOCKED(BE)** — token rusak diperlakukan seperti tamu |
| 11 | Papan tugas tanpa token | `GET /bff/api/tasks/board` | 401 | **200** (`queue:0`, `done:2`) | **BLOCKED(BE)** |
| 12 | Pengetahuan tanpa token | `GET /bff/api/kb/items` | 401 | **200**, daftar dokumen tenant `default` | **BLOCKED(BE)** |

Catatan: temuan 8–12 sama dengan `catatan-untuk-backend.md` §2.1/§2.8 (JWT belum ditegakkan; logout no-op). FE tidak memperbaikinya.

### 1.2 Langkah UI

| # | Langkah | Harapan | Hasil teramati | Verdict | Bukti |
|---|---|---|---|---|---|
| 1 | Buka aplikasi tanpa sesi | Halaman masuk | Form "Masuk" tampil; tidak ada data workspace dimuat | PASS | `uji-01-login.png` |
| 2 | Masuk dengan kata sandi salah | Pesan kesalahan jelas, tetap di form | Banner merah "Email atau kata sandi salah."; tetap di halaman masuk | PASS | `uji-02-login-gagal.png` |
| 3 | Masuk dengan kredensial benar | Masuk ke Beranda sebagai Super Admin | Beranda tampil; `localStorage.pegawai_ai_token` terisi (`length=233`, 3 segmen) | PASS | `uji-03-login-sukses.png` |
| 4 | Klik "Keluar" | Kembali ke halaman masuk, sesi lokal dibersihkan | Form masuk tampil; kunci `pegawai_ai_token` hilang dari localStorage | PASS | `uji-04-logout.png` |
| 5 | Isi localStorage dengan token rusak, muat ulang | Kembali ke login dengan pesan sesi berakhir | Banner "Sesi Anda berakhir, silakan masuk lagi."; token dihapus | PASS | `uji-05-sesi-berakhir.png` |

**Verdict bagian:** alur FE **PASS**; empat jalur data sensitif tetap **BLOCKED(BE)** karena server tidak menolak permintaan tanpa token yang sah.

---

## 2. Kanban (Hari 1)

### 2.1 Langkah

1. Buka **Jadwal & tugas** (`#/kanban`), isi quick-add "Uji QA sprint 5 - hapus setelah tes", tekan Enter.
2. Kartu muncul di kolom **Antre** dengan pegawai Rian dan label "Belum dikerjakan".
3. Klik judul kartu → panel detail terbuka (instruksi, percakapan kosong, riwayat, aksi).
4. Klik **Batalkan** → dialog konfirmasi → **Batalkan**; kartu pindah ke **Arsip** (status "Dibatalkan").
5. Buka panel kartu arsip, klik **Pulihkan** → kartu kembali ke **Antre**.
6. Batalkan lagi, lalu buka filter **Tampilkan → Arsip** untuk memastikan kartu ada di arsip.
7. Bersihkan data uji.

### 2.2 Permintaan yang teramati

| Langkah | Metode & path | Status | Catatan |
|---|---|---|---|
| Muat papan | `GET /bff/api/tasks/board` | 200 | Kolom Antre/Dikerjakan/Perlu Anda/Selesai |
| Muat jadwal berulang | `GET /bff/api/schedules` | 200 | — |
| Buat tugas | `POST /bff/api/tasks` | **201** | Body dari quick-add (judul yang diketik; pegawai default terpilih). Respons tidak disimpan mentah; kartu yang muncul menunjukkan Rian |
| Buka panel | `GET /bff/api/tasks/{id}` | 200 | Detail + aksi |
| Batalkan (arsip) | `POST /bff/api/tasks/{id}/cancel` | **200** | Kartu pindah ke Arsip; UI menampilkan "Dibatalkan" |
| Pulihkan | `POST /bff/api/tasks/{id}/restore` | **200** | Kembali ke Antre |
| Batalkan lagi | `POST /bff/api/tasks/{id}/cancel` | **200** | Kartu masuk daftar Arsip |
| Muat ulang papan | `GET /bff/api/tasks/board` | 200 | — |

### 2.3 Verdict

| Aspek | Verdict | Bukti |
|---|---|---|
| Buat tugas lewat quick-add, muncul di Antre | **PASS** | `uji-06-kanban-antre.png` |
| Panel detail terbuka dari kartu | **PASS** | `uji-07-tugas-panel.png` |
| Pindah status (Antre → Arsip → Antre) | **PASS** | `uji-08-tugas-dibatalkan.png`, `uji-09-arsip.png` |
| Arsip terlihat di filter "Arsip" | **PASS** | `uji-09-arsip.png` |
| Hapus permanen dari UI/API | **BLOCKED(BE)** | Tidak ada `DELETE /api/tasks/{id}` maupun tombol Hapus; satu-satunya jalur adalah `cancel` (arsip). Pembersihan akhir dilakukan di database (lihat §8) |

Catatan: aksi "Kerjakan sekarang" sengaja tidak dijalankan karena memicu run LLM penuh; perpindahan status sudah dibuktikan lewat `cancel`/`restore`.

---

## 3. Pengetahuan lewat chat (Hari 1)

### 3.1 Langkah

1. Buka chat **Siti** (`#/chat/siti`), klik ikon **Lampirkan ke Pengetahuan** (paperclip).
2. Unggah `uji-sprint5.txt`, `uji-sprint5.pdf`, lalu `uji-gambar.png` (jenis tidak didukung).
3. Tempel `https://example.com` di kolom pesan, klik **Simpan ke Pengetahuan** pada chip yang muncul.
4. Buka **Pengetahuan** (`#/pengetahuan`) dan pastikan ketiga entri tampil beserta statusnya.
5. Hapus ketiga entri lewat tombol **Hapus** + konfirmasi.
6. Uji tambahan: unggah PNG lewat API (415) dan simpan link internal `http://127.0.0.1:9/…` (gagal ingest), lalu hapus entri gagal tersebut.

Tidak ada pesan chat yang dikirim; unggahan tersimpan saat itu juga dan tidak memicu run LLM.

### 3.2 Permintaan dan respons teramati

| Aksi | Permintaan | Status | Respons (ringkas, tersanitasi) | Verdict |
|---|---|---|---|---|
| Unggah TXT | `POST /bff/api/kb/files` (multipart) | **201** | `{"kind":"file","name":"uji-sprint5.txt","status":"ready","size_bytes":98,"chars":97,…}` | PASS |
| Unggah PDF rusak | `POST /bff/api/kb/files` | **201** | Item dibuat dengan `status:"failed"`, `error:"PDF ini tidak bisa dibaca. Coba simpan ulang dari aplikasi asalnya."` | PASS (error terlihat) |
| Unggah PNG | `POST /bff/api/kb/files` | **415** | `{"error":"Jenis berkas tidak didukung. Pakai: .txt, .md, .csv, .pdf, .docx."}` | PASS |
| Simpan link publik | `POST /bff/api/kb/links` body `{"url":"https://example.com"}` | **201** | `{"kind":"url","name":"Example Domain","source":"https://example.com","status":"ready","size_bytes":156,"chars":156,…}` | PASS |
| Simpan link internal | `POST /bff/api/kb/links` body `{"url":"http://127.0.0.1:9/…"}` | **201** | Item `status:"failed"`, `error:"Alamat ini mengarah ke jaringan internal dan tidak diizinkan."` | PASS (validasi SSRF terlihat) |
| Hapus entri | `DELETE /bff/api/kb/items/{id}` ×4 | **204** | — | PASS |

### 3.3 Verdict UI

| Aspek | Verdict | Bukti |
|---|---|---|
| Tray menampilkan "tersimpan" untuk TXT | **PASS** | `uji-10-kb-unggah.png` |
| Status gagal terlihat per item (PDF tidak terbaca, PNG tidak didukung) | **PASS** | `uji-11-kb-status.png` |
| Link publik tersimpan dan muncul di Pengetahuan | **PASS** | `uji-12-pengetahuan.png` |
| Entri gagal tetap terlihat di daftar dengan pesan kesalahan | **PASS** | `uji-12-pengetahuan.png` |
| Hapus entri dari UI | **PASS** | Konfirmasi "Hapus" → `DELETE /bff/api/kb/items/{id}` **204** untuk ketiga entri uji; bukti akhir di §8 |

---

## 4. Connect Tools / Aplikasi (Hari 1)

### 4.1 Langkah

1. Buka **Aplikasi** (`#/aplikasi`) dengan mode admin mati.
2. Catat keadaan tersambung dan katalog.
3. Klik **Hubungkan** pada **Box** (belum tersambung) → dialog langkah → **Lanjut ke halaman login**.
4. Amati tujuan pengalihan tanpa menyelesaikan login, lalu **Batal**.
5. Klik **Putuskan** pada **Canva** (tersambung) → konfirmasi tampil → **Batal** (tidak jadi memutus).
6. Cek status Notion (endpoint terpisah).

### 4.2 Permintaan dan respons teramati

| Aksi | Permintaan | Status | Respons (ringkas) | Verdict |
|---|---|---|---|---|
| Daftar sambungan | `GET /bff/api/connections` | 200 | `gdrive` dan `gmail`: `status:"connected"`, `account` terisi (disamarkan `<akun>`) | PASS |
| Katalog aplikasi | `GET /bff/api/apps/catalog` | 200 | 54 aplikasi; **1** `connected` (`canva_mcp`), **53** `not_connected`; kategori lengkap. Dengan mode admin mati, UI menyembunyikan entri teknis dan menampilkan **37** ("Aplikasi lain · 37") | PASS |
| Status Notion | `GET /bff/api/connections/notion/status` | 200 | `{"status":"not_connected","waiting":false}` | PASS |
| Mulai sambung Box | `POST /bff/api/apps/box/connect` | **200** | `{"url":"https://portal.nousresearch.com/…"}` (nilai setelah host disamarkan) | PASS |
| Polling status Box | `GET /bff/api/apps/box/status` | 200 | Dipanggil berkala selama dialog menunggu; setelah batal: `{"status":"not_connected","waiting":false}` | PASS |
| Batalkan sambung Box | `POST /bff/api/apps/box/disconnect` | **204** | Status kembali `{"status":"not_connected","waiting":false}` | PASS |
| Konfirmasi putus Canva | — (hanya dialog) | — | "Putuskan Canva?" + tombol Putuskan/Batal; klik Batal menutup konfirmasi tanpa permintaan apa pun | PASS |

### 4.3 Penyedia yang benar-benar didukung

| Penyedia | Keadaan | Bukti |
|---|---|---|
| Google Drive | Tersambung (OAuth milik BFF), tombol "Pilih dari Drive" | `uji-13-aplikasi.png` |
| Gmail | Tersambung, ada penjelasan tombol draf | `uji-13-aplikasi.png` |
| Canva | Tersambung lewat konektor Hermes (`canva_mcp`) | `uji-13-aplikasi.png` |
| 53 konektor lain (mis. Box, Notion, Confluence) | Belum tersambung; tombol **Hubungkan** aktif. Yang diuji: **Box** berakhir di `portal.nousresearch.com/connect/…` | `uji-14-hubungkan-box.png`, `uji-15-tunggu-oauth.png` |
| Status "tidak tersedia" | **Tidak ada** label "Belum tersedia" di build ini. Label yang tersedia untuk penyedia yang belum diatur admin adalah **"Segera hadir"** (pengguna) / **"Belum diatur admin"** (admin). Hari ini tidak ada penyedia berstatus `not_configured`, jadi label itu tidak muncul | `uji-13-aplikasi.png` |

**Verdict:** daftar, keadaan tersambung, alur sambung sampai pengalihan, dan konfirmasi putus semuanya **PASS**. Tidak ada OAuth yang diselesaikan; tidak ada akun baru tersambung.

> Catatan: dialog menjanjikan "halaman login Box", tetapi tujuan sebenarnya adalah portal konektor `portal.nousresearch.com`. Ini perilaku perantara konektor Hermes, bukan bug FE; copy dialog mengasumsikan login langsung ke penyedia.

---

## 5. Konfigurasi karyawan (Hari 3)

Objek uji: **Sari** (pegawai buatan pengguna; nilai awal `color:"plain"`, `model:null`, persona 73 karakter).

### 5.1 Langkah dan hasil

| # | Langkah | Harapan | Hasil teramati | Verdict | Bukti |
|---|---|---|---|---|---|
| 1 | Buka detail Sari, mode admin mati | Hanya field yang boleh diubah terlihat; field inti read-only | Blok **"Bisa Anda ubah"**: Atur, Nama, Tugas dan gaya bicara, Warna, Tingkat ketelitian. Blok **"Diatur sistem"**: Aturan inti (SOUL), Izin keamanan (toolset). Tidak ada editor SOUL/model/toolset | PASS | `uji-17-agen-sari.png` |
| 2 | Buka "Atur", pilih warna **Hijau toska** dan ketelitian **Seimbang** | Perubahan bisa dipilih | Label berubah menjadi "Warna: Hijau toska"; radio Seimbang terpilih | PASS | `uji-18-atur-ubah.png` |
| 3 | Klik **Simpan** | `PATCH /bots/sari` 200 | **200**; `GET /bots/sari` berikutnya: `{"color":"teal","model":"qwen3.7-max","provider":"opencode-go"}` | PASS | `uji-19-agen-tersimpan.png` |
| 4 | Muat ulang halaman | Nilai tersimpan | Detail menampilkan Warna **Hijau toska**, Tingkat ketelitian **Seimbang** | PASS | `uji-19-agen-tersimpan.png` |
| 5 | Kosongkan Nama, klik Simpan | Validasi terlihat, tidak ada permintaan | Pesan "Isi nama pegawai.", `aria-invalid=true`, **0** permintaan `PATCH` | PASS | `uji-20-validasi-nama.png` |
| 6 | Pulihkan nilai awal | Warna Netral, ketelitian Ikuti bawaan | `PATCH /bots/sari` body `{"color":"plain","model":null,"provider":null}` → **200**; UI setelah muat ulang: **Netral**, **Ikuti bawaan** | PASS (lewat API; lihat defect FE-1) | `uji-21-agen-dipulihkan.png` |

### 5.2 Request/response (ringkas)

```
PATCH /bff/api/bots/sari
{"color":"teal","model":"qwen3.7-max","provider":"opencode-go"}
→ 200 {"id":"sari","name":"Sari","color":"teal","model":"qwen3.7-max","provider":"opencode-go", …}

PATCH /bff/api/bots/sari
{"color":"plain","model":null,"provider":null}
→ 200 {"id":"sari","name":"Sari","color":"plain","model":null,"provider":null, …}
```

### 5.3 Mode admin mati — batas editable

- "Atur" hanya menampilkan **Nama, Tugas dan gaya bicara, Warna, Tingkat ketelitian**. Tidak ada nama model mentah, provider, SOUL, atau daftar toolset.
- Pilihan ketelitian hanya menampilkan label manusiawi ("Hemat & cepat", "Seimbang", "Paling teliti") tanpa nama model; nama model hanya muncul saat mode admin hidup.
- Halaman detail memisahkan "Bisa Anda ubah" dan "Diatur sistem"; "Aturan inti" dan "Izin keamanan" hanya teks penjelasan, tanpa kontrol edit.
- Verdict: **PASS** — field terlindungi tidak dapat diedit dari UI dengan mode admin mati.

---

## 6. Responsif 375 px

Tidak diambil ulang; bukti sudah ada di `frontend/screenshots/` (arsip Sprint 5). Semua halaman utama punya tangkapan 375 px:

| Halaman | Berkas bukti |
|---|---|
| Beranda | `sprint5-beranda-375-light.png`, `sprint5-beranda-375-dark.png` |
| Tim | `sprint5-tim-375.png`, `sprint5-tim-375-dark.png` |
| Chat | `sprint5-chat-375-light.png`, `sprint5-chat-375-list.png`, `sprint5-chat-375-menu.png`, `sprint5-chat-375-switcher.png` |
| Grup | `sprint5-group-375-list.png`, `sprint5-group-375-sheet.png` |
| Jadwal & tugas (Kanban) | `sprint5-kanban-375.png`, `sprint5-kanban-375-filter.png`, `sprint5-kanban-375-selesai.png`, `sprint5-kanban-375-schedule.png` |
| Detail pegawai | `sprint5-detail-375-light.png`, `sprint5-detail-375-dark.png`, `sprint5-detail-375-keahlian-light.png`, `sprint5-detail-375-pekerjaan-light.png` |
| Pengetahuan | `sprint5-pengetahuan-375.png` |
| Aplikasi | `sprint5-apps-375.png` |
| Pengaturan | `sprint5-settings-umum-375.png`, `sprint5-settings-keamanan-375.png`, `sprint5-settings-notifikasi-375.png`, `sprint5-settings-data-375.png`, `sprint5-settings-paket-375.png` |
| Keahlian | `sprint5-skills-375.png` |

**Verdict:** **PASS** (bukti arsip; tidak ada perubahan kode yang memengaruhi tata letak sejak tangkapan dibuat).

---

## 7. Daftar defect

### 7.1 Frontend

| # | Gejala | Berkas / baris | Dampak | Severity |
|---|---|---|---|---|
| FE-1 | Setelah warna pegawai diubah, warna asal **Netral** (`plain`) tidak bisa dipilih lagi: dialog "Atur" hanya menampilkan 8 swatch dari `COLORS`, tanpa opsi Netral. Nilai awal hanya bisa dipulihkan lewat API. | `frontend/src/Dialogs.tsx:500-505` (swatch dari `Object.entries(COLORS)`); `frontend/src/ui.tsx:27` (`COLORS` tidak memuat `plain`) | Kosmetik; pengguna tidak bisa kembali ke warna bawaan tanpa bantuan admin | Sedang |

Tidak ada defect FE lain yang ditemukan pada alur di atas.

### 7.2 Backend (bukan milik FE; jangan diperbaiki di FE)

| # | Gejala | Bukti | Rujukan |
|---|---|---|---|
| BE-1 | JWT tidak ditegakkan di `/api/*`: tanpa token atau token rusak tetap **200** dengan data tenant `default` (bots, papan tugas, Pengetahuan) | §1.1 baris 9–12 | `catatan-untuk-backend.md` §2.1 |
| BE-2 | Logout tidak menginvalidasi token; `/auth/me` dengan token lama tetap **200** | §1.1 baris 7–8 | `catatan-untuk-backend.md` §2.8 |
| BE-3 | Tidak ada `DELETE /api/tasks/{id}`; tugas hanya bisa dibatalkan/diarsipkan. Pembersihan data uji harus lewat database | §2.3 | Kontrak tugas |
| BE-4 | PDF yang tidak terbaca tetap membuat item KB (**201**) dengan `status:"failed"`; bukan 4xx. Dapat diterima sebagai desain (status per item), tetapi membingungkan bila klien mengharapkan penolakan | §3.2 | `catatan-untuk-backend.md` §2.9 |

---

## 8. Bukti pembersihan

| Data uji | Tindakan | Bukti |
|---|---|---|
| Tugas "Uji QA sprint 5 - hapus setelah tes" (`025a1ba5-…`) + event-nya | Dibatalkan → dipulihkan → dibatalkan (arsip), lalu dihapus dari `tasks` (event ikut terhapus lewat `ON DELETE CASCADE`) | `DELETE 1`; `select count(*) … like 'Uji QA sprint 5%'` → **0**; `task_events` untuk id itu → **0** |
| KB `uji-sprint5.txt` (`faba5e82-…`) | `DELETE /bff/api/kb/items/{id}` | **204**; item tidak ada di daftar |
| KB `uji-sprint5.pdf` (`c96863c3-…`) | `DELETE /bff/api/kb/items/{id}` | **204** |
| Link `Example Domain` (`200bba6b-…`) | `DELETE /bff/api/kb/items/{id}` | **204** |
| Link internal gagal (`ac2384f3-…`) | `DELETE /bff/api/kb/items/{id}` | **204** |
| Konfigurasi Sari | `PATCH /bots/sari` → `{"color":"plain","model":null,"provider":null}` | Kolom DB: `plain|null`; UI: Netral / Ikuti bawaan (`uji-21-agen-dipulihkan.png`) |
| Sambungan Box | Dibatalkan sebelum OAuth; `POST /apps/box/disconnect` | **204**; status `{"status":"not_connected","waiting":false}` |
| Berkas uji sementara (`uji-sprint5.txt/pdf/png`) | Folder temp dihapus | Folder tidak ada lagi |
| Akun demo/seed | Tidak diubah | — |

Verifikasi akhir di database:

```
select count(*) from tasks where title like 'Uji QA sprint 5%';                         -- 0
select count(*) from kb_items where name ilike '%uji%' or source ilike '%tidak-terjangkau%';  -- 0
select color, model from bots where id='sari';                                          -- plain | (null)
```

Daftar Pengetahuan kembali berisi **11 dokumen seed** (semua bertanggal 18 Nov 2026), tanpa entri uji.

---

## 9. Indeks tangkapan layar

Semua berkas di bawah ada di `docs-kaf/sprint5/` (1280×800).

| Berkas | Isi |
|---|---|
| `uji-01-login.png` | Halaman masuk tanpa sesi |
| `uji-02-login-gagal.png` | Pesan "Email atau kata sandi salah." |
| `uji-03-login-sukses.png` | Beranda setelah masuk |
| `uji-04-logout.png` | Kembali ke halaman masuk setelah Keluar |
| `uji-05-sesi-berakhir.png` | Banner "Sesi Anda berakhir…" untuk token rusak |
| `uji-06-kanban-antre.png` | Tugas baru di kolom Antre |
| `uji-07-tugas-panel.png` | Panel detail tugas |
| `uji-08-tugas-dibatalkan.png` | Tugas berstatus Dibatalkan |
| `uji-09-arsip.png` | Filter Arsip berisi tugas uji |
| `uji-10-kb-unggah.png` | Tray "uji-sprint5.txt tersimpan" |
| `uji-11-kb-status.png` | Status TXT/PDF/PNG + link di tray |
| `uji-12-pengetahuan.png` | Entri uji di halaman Pengetahuan |
| `uji-13-aplikasi.png` | Keadaan tersambung + katalog (akun disamarkan) |
| `uji-14-hubungkan-box.png` | Dialog "Hubungkan Box" |
| `uji-15-tunggu-oauth.png` | Menunggu login di tab lain |
| `uji-16-konfirmasi-putuskan.png` | Konfirmasi "Putuskan Canva?" |
| `uji-17-agen-sari.png` | Batas "Bisa Anda ubah" vs "Diatur sistem" |
| `uji-18-atur-ubah.png` | Warna/ketelitian diubah sebelum simpan |
| `uji-19-agen-tersimpan.png` | Nilai tersimpan setelah muat ulang |
| `uji-20-validasi-nama.png` | Validasi "Isi nama pegawai." |
| `uji-21-agen-dipulihkan.png` | Nilai awal dipulihkan (Netral / Ikuti bawaan) |
