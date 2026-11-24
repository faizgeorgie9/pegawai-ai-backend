# Bukti Uji Live — Sprint 5 FE (Hari 5)

**Ringkasan**

- Uji dijalankan pada **24 November 2026, 07.15–07.45 WIB (00.15–00.45 UTC)** terhadap aplikasi yang **sudah ter-deploy** di VPS, hanya lewat URL publik `https://139.190.107.151.sslip.io/demo/` (aplikasi yang sama juga dilayani di `/`), memakai browser sungguhan (Chromium) dan permintaan HTTP.
- Build yang diuji: `demo/assets/index-Wuwce_Ud.js` + `demo/assets/index-DRDF3-V3.css` (hash sama dengan yang tercatat di `audit-vps.md`, 23 Nov 2026) — jadi yang dinilai adalah artefak yang benar-benar dipakai pengguna, bukan `npm run dev`.
- Akun uji: `admin@pegawai.ai` (peran `admin`, workspace `default`, paket `pro`). Kata sandi demo diambil dari `bff/migrations/020_auth_users.sql` dan **tidak ditulis** di dokumen ini.
- **Mode admin: mati** selama seluruh uji (kunci `pegawai-ai.admin-mode` tidak diisi). Yang diuji adalah UI untuk pengguna awam; halaman grup Admin tidak dibuka.
- **Sanitasi:** token diganti `<jwt>`; email akun tersambung diganti `<akun>` — pada tangkapan Aplikasi teks email di DOM disamarkan menjadi `<akun>` sebelum gambar diambil, tidak ada data lain yang diubah. Tidak ada kata sandi, token, kunci, atau email pribadi di dokumen ini.
- **Verdict:** `PASS` = perilaku sesuai harapan; `FAIL` = perilaku salah; `BLOCKED(BE)` = tidak bisa dipakai/diuji karena kontrak Backend belum ada atau tidak benar.

| # | Journey | Verdict |
|---|---|---|
| 1 | Auth (login, salah sandi, `/auth/me`, logout, sesi berakhir) | **PASS (FE)** — empat jalur data sensitif **BLOCKED(BE)** |
| 2 | Beranda | **PASS** (dengan catatan kinerja: skeleton ± 7 dtk) |
| 3 | Tim + grup | **PASS** |
| 4 | Chat (kirim 1 pesan, hapus topik) | **PASS** |
| 5 | Jadwal & tugas (buat, pindah, arsip) | **PASS** untuk buat/pindah/arsip; **BLOCKED(BE)** untuk hapus permanen |
| 6 | Pengetahuan + KB lewat chat (md/pdf/docx + link) | **PASS** |
| 7 | Aplikasi (daftar tersambung, cari katalog, alur sambung lalu batal) | **PASS** alur; **FAIL** tampilan kartu Gmail |
| 8 | Pengaturan 5 bagian (baca saja) | **PASS** |
| 9 | Detail pegawai 4 tab + dialog Atur | **PASS** baca; **FAIL** (2 defect FE: pilihan ketelitian mati, kartu tidak menyegar setelah simpan) |
| 10 | Responsif 1280×800 & 375×812, gelap 2 halaman | **PASS** (tidak ada overflow horizontal; 1 kartu rusak = FE-1) |
| 11 | Konsol & permintaan gagal per halaman | **PASS** (0 error konsol, 0 permintaan 4xx/5xx tak terduga) |
| 12 | Foto produk (`/api/product-images/*`, migrasi 013/014) | **PASS** endpoint; **BLOCKED(BE)** pemetaan data (semua `image_url` kosong) |
| 13 | Log server selama jendela uji | **PASS** (0 respons 5xx) |

**Ringkas angka:** 0 error konsol, 0 respons 5xx, 2 defect FE baru (FE-1, FE-2) + 1 defect FE perilaku (FE-3) + 3 catatan kecil, 4 blocker BE (auth, logout, hapus tugas, latensi/pemetaan gambar).

---

## 1. Metode, batasan, dan bukti

### 1.1 Yang dijalankan

| Aspek | Keterangan |
|---|---|
| Browser | Chromium headless (viewport 1280×800 dan 375×812, `deviceScaleFactor 2` untuk 375) |
| Basis data | Tidak ada tulisan langsung ke DB. Semua perubahan lewat UI/API aplikasi |
| Server | Tidak ada deploy, restart, atau tulis file di VPS. SSH hanya untuk membaca `journalctl` dan access log nginx (read-only) |
| Data uji | Dibuat lalu dihapus/dipulihkan pada uji yang sama; bukti di §12 |
| LLM | **Satu** pesan chat pendek (`Balas satu kata: oke`) ke Siti, lalu topiknya dihapus. Tidak ada run tugas, tidak ada persetujuan aksi, tidak ada kirim email/WhatsApp |
| OAuth | Hanya dibuka sampai halaman tunggu login, lalu dibatalkan. Tidak ada akun tersambung/terputus |

### 1.2 Cara membaca bukti

- Path permintaan ditulis relatif ke origin: `/bff/api/...` adalah jalur yang dipakai UI (proxy Vite/nginx), `/api/...` adalah jalur BFF langsung. Status dan bentuk respons dicatat apa adanya, tanpa token.
- Tangkapan layar ada di `docs-kaf/sprint5/` dengan awalan `live-`; indeks lengkap di §14.
- Angka `scrollHeight` diambil dari elemen `.page` (halaman yang memakainya) atau `main` (halaman chat/tim yang memakai kolom sendiri), seperti diminta.

---

## 2. Auth

### 2.1 API

| # | Langkah | Permintaan | Harapan | Hasil teramati | Verdict |
|---|---|---|---|---|---|
| 1 | Login benar | `POST /api/auth/login` body `{"email":"admin@pegawai.ai","password":"<rahasia>"}` | 200 + token + user | **200**; `{"token":"<jwt>","user":{"id":"default","name":"Super Admin","email":"<akun>","role":"admin","company":"Colorbox","plan_id":"pro"}}`; token 233 karakter, 3 segmen, berawalan `eyJ` | PASS |
| 2 | Kata sandi salah | `POST /api/auth/login` | 401 + pesan | **401** `{"error":"Email atau kata sandi tidak cocok"}` | PASS |
| 3 | `/auth/me` token valid | `GET /api/auth/me` + header `Authorization` | 200 + user | **200** `{"ok":true,"user":{"id":"default","role":"admin","company":"Colorbox","plan_id":"pro","is_active":true}}` | PASS |
| 4 | `/auth/me` tanpa token | `GET /api/auth/me` | 401 | **401** `{"error":"Kredensial login tidak valid atau belum login"}` | PASS |
| 5 | `/auth/me` token rusak | `GET /api/auth/me` + `<jwt-rusak>` | 401 | **401** `{"error":"Token autentikasi tidak valid atau rusak."}` | PASS |
| 6 | Logout | `POST /api/auth/logout` | 200 | **200** `{"ok":true,"message":"Berhasil logout"}` | PASS |
| 7 | Token lama setelah logout | `GET /api/auth/me` + token yang sama | 401 | **200** — token masih berlaku (diuji 2×: token hasil login via curl dan token sesi browser) | **BLOCKED(BE)** |
| 8 | Data terlindungi tanpa token | `GET /api/bots` | 401 | **200**, 7 agen tenant `default` (`siti, hendra, bimo, meda, raka, bram, vina`) | **BLOCKED(BE)** |
| 9 | Data terlindungi token rusak | `GET /api/bots` + `<jwt-rusak>` | 401 | **200**, 7 agen yang sama | **BLOCKED(BE)** |
| 10 | Papan tugas tanpa token | `GET /api/tasks/board` | 401 | **200** `{"queue":4,"running":0,"needs_you":3,"done":0}` | **BLOCKED(BE)** |
| 11 | Pengetahuan tanpa token | `GET /api/kb/items` | 401 | **200**, 4 dokumen tenant `default` | **BLOCKED(BE)** |
| 12 | Pengaturan/pengguna tanpa token | `GET /api/settings`, `GET /api/me` | 401 | **200**; `/api/me` mengembalikan `{"user":{"id":"default","name":"Super Admin","plan_id":"pro"}, …}` | **BLOCKED(BE)** |
| 13 | Sambungan & katalog tanpa token | `GET /api/connections`, `GET /api/apps/catalog` | 401 | **200**; daftar sambungan memuat status `connected` milik tenant `default` | **BLOCKED(BE)** |

Catatan: temuan 7–13 identik dengan temuan lokal (`bukti-uji-lokal.md` §1.1 baris 8–12) dan `catatan-untuk-backend.md` §2.1/§2.8. FE tidak memperbaikinya, dan UI **tidak** bergantung pada penolakan server — lihat §2.2 baris 5 (UI tetap menutup sesi dari 401 `/auth/me`).

### 2.2 UI

| # | Langkah | Harapan | Hasil teramati | Verdict | Bukti |
|---|---|---|---|---|---|
| 1 | Buka aplikasi tanpa sesi | Halaman masuk, tanpa data workspace | Form "Masuk" tampil; 6 permintaan total (dokumen, JS, CSS, font) — **tidak ada** panggilan `/bff/api/*` sebelum login | PASS | `live-01-login.png` |
| 2 | Masuk dengan kata sandi salah | Pesan jelas, tetap di form | Banner "Email atau kata sandi salah."; `POST /bff/api/auth/login` **401**; `localStorage.pegawai_ai_token` tetap kosong; form tetap tampil | PASS | `live-02-login-gagal.png` |
| 3 | Masuk dengan kredensial benar | Masuk ke Beranda sebagai Super Admin | `POST /auth/login` **200**; `#/` tampil; token 233 karakter/3 segmen di `localStorage`; sidebar 7 menu (tanpa grup Admin, sesuai mode admin mati) | PASS | `live-03-beranda.png` |
| 4 | Klik "Keluar" | Kembali ke halaman masuk, sesi lokal dibersihkan | `POST /bff/api/auth/logout` **200**; form masuk tampil; kunci `pegawai_ai_token` hilang (tersisa `pegawai.notifyAsked`) | PASS | `live-55-logout.png` |
| 5 | Isi `localStorage` dengan token rusak, muat ulang | Kembali ke login dengan pesan sesi berakhir | `GET /bff/api/auth/me` **401**; banner "Sesi Anda berakhir, silakan masuk lagi."; token dihapus | PASS | `live-43-sesi-berakhir.png` |

Catatan konsol: saat logout, satu entri `requestfailed` muncul untuk `GET /bff/api/events: net::ERR_ABORTED`. Itu penutupan stream SSE saat sesi berakhir (disengaja), bukan kegagalan halaman.

---

## 3. Beranda

| # | Langkah | Harapan | Hasil teramati | Verdict | Bukti |
|---|---|---|---|---|---|
| 1 | Buka `#/` setelah masuk | Ringkasan hari ini, aksi utama jelas | Judul "Yang perlu Anda lakukan hari ini.", CTA **Beri tugas**, progres "3/5 langkah selesai", blok **Perlu persetujuan Anda · 3** dengan tombol **Tinjau** per item, jadwal terdekat, daftar pegawai + "Lihat semua 7 pegawai" | PASS | `live-03-beranda.png` |
| 2 | Amati waktu muat | Skeleton singkat | Skeleton "Memuat beranda..." masih tampil pada detik ke-3 dan hilang sebelum detik ke-9 (± 7 dtk) karena setiap panggilan API butuh ± 6,5 dtk (lihat §12.3). Lalu konten lengkap | PASS (UX buruk, akar di BE) | `live-03-beranda.png` |
| 3 | Aksi berisiko | Tidak ada aksi yang berjalan sendiri | Tiga item "Perlu persetujuan" **tidak** disetujui/ditolak selama uji | PASS | — |

`.page` scrollHeight 1280×800: **956 px**; 375×812: **1807 px**; tidak ada overflow horizontal di kedua ukuran.

---

## 4. Tim + grup

| # | Langkah | Harapan | Hasil teramati | Verdict | Bukti |
|---|---|---|---|---|---|
| 1 | Buka `#/grup` | Daftar tim + tim terpilih | Dua tim: **test** (2 anggota) dan **Tim Kampanye Marketing Colorbox** (5 anggota: Bimo, Meda, Raka, Bram, Vina). Rute `#/grup` langsung membuka tim terakhir yang dipakai (**test**) — perilaku "ingat pilihan", bukan halaman kosong | PASS | `live-04-tim.png` |
| 2 | Baca panel tim | Kolom percakapan tim, tanpa data asing | Panel **test** menampilkan "Belum ada pesan" + kolom "Pesan untuk tim test"; tombol **Atur anggota**, **Detail** | PASS | `live-04-tim.png` |
| 3 | Kirim pesan ke tim | — | **Tidak dijalankan**: memicu run LLM untuk 1–5 pegawai (di luar batas LLM uji). Perilaku kirim pesan satu-pegawai sudah dibuktikan di §5 | Tidak diuji (sengaja) | — |

`main` scrollHeight 1280×800: **800 px**; 375: `.page` **119 px** (hanya intro + tombol **Tim baru**; daftar tim ada di panel geser), CTA **Tim baru** terlihat di layar pertama.

---

## 5. Chat (satu pesan, lalu hapus topik)

### 5.1 Langkah

1. Buka `#/chat/siti`; catat daftar riwayat (**0 topik**).
2. Tulis `Balas satu kata: oke` di kolom pesan, tekan Enter.
3. Tunggu balasan; catat waktu dan status permintaan.
4. Tutup ajakan notifikasi browser dengan **Nanti** (tidak memberi izin).
5. Hover baris riwayat → ikon hapus → konfirmasi **Hapus topik**.
6. Pastikan daftar riwayat kembali kosong.

### 5.2 Permintaan dan hasil

| Aksi | Permintaan | Status | Hasil | Verdict |
|---|---|---|---|---|
| Kirim pesan | `POST /bff/api/bots/siti/runs` | **202** | Run dibuat; UI menampilkan pesan pengguna + status bekerja | PASS |
| Stream hasil | `GET /bff/api/runs/{id}/stream` | **200** | Balasan asisten **"oke"** muncul **12,1 detik** setelah kirim | PASS |
| Langkah kerja | `GET /bff/api/thinking?session_id=…` | **200** | Panel langkah kerja tersedia lewat sakelar "Tampilkan langkah kerja" | PASS |
| Ajakan notifikasi | — | — | Panel "Mau diberi tahu saat pegawai selesai bekerja?" muncul sekali; ditutup dengan **Nanti** | PASS |
| Hapus topik | `DELETE /bff/api/bots/siti/sessions/{sid}` | **204** | Baris riwayat hilang; daftar kembali "Belum ada percakapan dengan Siti."; `GET /bots/siti/sessions` → `{"object":"list","data":[]}` | PASS |

### 5.3 Verdict UI

| Aspek | Verdict | Bukti |
|---|---|---|
| Balasan tampil utuh + tombol Salin / Simpan sebagai draf Gmail | PASS | `live-06-chat-balasan.png` |
| Konfirmasi hapus topik menyebut cakupan ("Hanya topik ini yang dihapus. Ingatan Siti dan dokumen di Pengetahuan tidak berubah.") | PASS | `live-07-hapus-topik-konfirmasi.png` |
| Setelah hapus, riwayat kosong dan tombol hapus memakai gaya berbahaya (`btn danger`) | PASS | `live-08-topik-dihapus.png` |

Catatan: jejak run `Balas satu kata: oke` tetap terlihat di tab **Pekerjaan** milik Siti (riwayat run, bukan topik). Tidak ada endpoint untuk menghapus baris run — lihat §12.

`main` scrollHeight 1280×800: **800 px**; 375: **800 px** (kolom percakapan + komposer tetap dalam satu layar), CTA **Topik baru** di layar pertama.

---

## 6. Jadwal & tugas

### 6.1 Langkah

1. Buka `#/kanban`; catat angka kolom (baseline).
2. Isi quick-add `Uji QA live Sprint 5 - hapus setelah tes`, Enter (pegawai default **Siti**).
3. Buka menu ⋯ kartu → **Batalkan** → konfirmasi **Batalkan** → kartu pindah ke Arsip.
4. Filter **Tampilkan → Arsip** → kartu tampil sebagai "Dibatalkan" → **Pulihkan** → kartu kembali ke Antre.
5. Batalkan sekali lagi supaya data uji tidak mengganggu papan (lihat §12 soal hapus permanen).
6. Cek angka kolom dan arsip lewat API sebelum/sesudah.

### 6.2 Permintaan yang teramati

| Langkah | Metode & path | Status | Catatan |
|---|---|---|---|
| Muat papan | `GET /bff/api/tasks/board` | 200 | Kolom Antre / Dikerjakan / Perlu Anda / Selesai |
| Buat tugas | `POST /bff/api/tasks` | **201** | Tombol berubah menjadi "Menambah…" selama ± 7 dtk (masih "Menambah…" pada detik ke-5, selesai sebelum detik ke-13), lalu kartu muncul di **Antre** |
| Muat ulang papan | `GET /bff/api/tasks/board` | 200 | — |
| Batalkan (arsip) | `POST /bff/api/tasks/{id}/cancel` | **200** | Kartu hilang dari Antre, masuk Arsip |
| Pulihkan | `POST /bff/api/tasks/{id}/restore` | **200** | Kartu kembali ke Antre |
| Arsip | `GET /bff/api/tasks/board?archived=1` | 200 | Daftar arsip + tombol Pulihkan |

### 6.3 Angka kolom (bukti perpindahan)

| Tahap | queue | running | needs_you | done | archived |
|---|---|---|---|---|---|
| Baseline | 4 | 0 | 3 | 0 | 1 |
| Setelah buat | **5** | 0 | 3 | 0 | 1 |
| Setelah Batalkan | 4 | 0 | 3 | 0 | **2** |
| Setelah Pulihkan | **5** | 0 | 3 | 0 | **1** |
| Setelah Batalkan lagi (akhir) | 4 | 0 | 3 | 0 | **2** |

### 6.4 Verdict

| Aspek | Verdict | Bukti |
|---|---|---|
| Buat tugas lewat quick-add, muncul di Antre sebagai "Belum dikerjakan" | PASS | `live-09-kanban.png`, `live-10-task-created.png` |
| Menu kartu berisi **Ubah** dan **Batalkan**, dengan konfirmasi | PASS | `live-11-task-menu.png` |
| Pindah status Antre → Arsip dan Arsip → Antre | PASS | `live-12-task-archived.png`, `live-13-arsip.png`, `live-14-arsip-akhir.png` |
| Hapus permanen dari UI/API | **BLOCKED(BE)** — tidak ada `DELETE /api/tasks/{id}` maupun tombol Hapus; satu-satunya jalur adalah arsip | §12 |
| "Kerjakan sekarang" (Antre → Dikerjakan) | Tidak diuji: memicu run LLM penuh (batas LLM uji) | — |

Catatan FE kecil: konfirmasi "Batalkan" memakai tombol bergaya **primary** (sama dengan tombol aman), sedangkan hapus topik chat memakai `btn danger`. Untuk aksi merusak, gaya seragam akan lebih aman (lihat §11 FE-5).

`main` scrollHeight 1280×800: **800 px** (papan mengisi layar, kolom digulir sendiri); 375: `.page` **760 px**, tombol **Filter** dan **Tambah** di layar pertama; label "Tugas berulang" menyusut menjadi "berulang" (kelas `.hide-sm`, disengaja) dengan `aria-label` tetap "Tugas berulang, 1".

---

## 7. Pengetahuan + KB lewat chat

### 7.1 Langkah

1. Buka `#/chat/siti`, klik ikon **Lampirkan ke Pengetahuan** (paperclip) — tanpa mengirim pesan.
2. Unggah `uji-live.md`, `uji-live.pdf` (PDF minimal buatan sendiri), `uji-live.docx` sekaligus.
3. Unggah `uji-live-pdf-valid.pdf` (PDF dengan xref benar) untuk membedakan "PDF rusak" dari "jalur PDF tidak jalan".
4. Tempel `https://example.com` di kolom pesan → chip **Simpan ke Pengetahuan** → klik.
5. Buka `#/pengetahuan`; cek status, ukuran, dan isi teks lewat **Lihat**.
6. Hapus kelima entri uji (Hapus → konfirmasi inline Hapus).

### 7.2 Permintaan dan respons teramati

| Aksi | Permintaan | Status | Respons (ringkas) | Verdict |
|---|---|---|---|---|
| Unggah MD | `POST /bff/api/kb/files` | **201** | `status:"ready"`, 144 B, 139 karakter | PASS |
| Unggah PDF (xref salah) | `POST /bff/api/kb/files` | **201** | `status:"failed"`, `error:"PDF ini tidak bisa dibaca. Coba simpan ulang dari aplikasi asalnya."` | PASS (error terlihat per item) |
| Unggah DOCX | `POST /bff/api/kb/files` | **201** | `status:"ready"`, 1 KB, 38 karakter | PASS |
| Unggah PDF valid | `POST /bff/api/kb/files` | **201** | `status:"ready"`, 615 B, 40 karakter | PASS |
| Simpan link publik | `POST /bff/api/kb/links` `{"url":"https://example.com"}` | **201** | `{"name":"Example Domain","status":"ready","chars":156}` | PASS |
| Hapus 5 entri | `DELETE /bff/api/kb/items/{id}` ×5 | **204** | Daftar kembali ke 4 dokumen awal | PASS |

Semua unggahan terjadi tanpa mengirim pesan chat (tidak ada run LLM).

### 7.3 Verdict UI

| Aspek | Verdict | Bukti |
|---|---|---|
| Tray menampilkan status per berkas ("tersimpan" / "gagal: …") | PASS | `live-16-kb-unggah.png`, `live-17-kb-status.png` |
| Chip "Simpan ke Pengetahuan" muncul saat URL ditempel, lalu tersimpan | PASS | `live-18-kb-link-chip.png`, `live-19-kb-tray.png` |
| Halaman Pengetahuan menampilkan 9 entri (4 awal + 5 uji) dengan jenis, ukuran, tanggal | PASS | `live-20-pengetahuan.png` |
| **Lihat** menampilkan teks hasil ekstraksi | PASS — link: "This domain is for use in documentation examples…"; MD: penanda `UJI-LIVE-MD-2026` terbaca; PDF valid membuka penampil dokumen | `live-21-kb-lihat.png`, `live-22-kb-teks-md.png`, `live-23-kb-teks-pdf.png` |
| Hapus entri (konfirmasi di baris, bukan dialog) | PASS | `live-24-pengetahuan-bersih.png` |

Catatan: PDF yang tidak punya tabel xref ditolak sebagai item `failed` (bukan 4xx) — sama seperti hasil lokal (`BE-4`), masih dapat diterima sebagai desain status-per-item.

`.page` scrollHeight 1280×800: **800 px** (daftar digulir di dalam panel, `main` 846 px); 375: **760 px**, tombol **Unggah berkas** dan **Tambah link** di layar pertama.

---

## 8. Aplikasi

### 8.1 Keadaan dan katalog

| Aksi | Permintaan | Status | Hasil | Verdict |
|---|---|---|---|---|
| Daftar sambungan | `GET /bff/api/connections` | 200 | `gdrive`: `connected`, akun `<akun>`; `gmail`: `disconnected` | PASS |
| Katalog | `GET /bff/api/apps/catalog` | 200 | **54** aplikasi, **semua** `not_connected`; UI menampilkan bagian **Tersambung · 1** (Google Drive) dan **Aplikasi lain · 39** (entri teknis disembunyikan saat mode admin mati) | PASS |
| Cari "notion" | (filter lokal, tanpa permintaan) | — | 1 hasil, tombol **Hubungkan** | PASS (`live-26-aplikasi-cari.png`) |
| Cari kata acak | — | — | "Aplikasi lain · 0" + "Tidak ada aplikasi yang cocok. **Hapus pencarian**" | PASS (`live-27-aplikasi-cari-kosong.png`) |

### 8.2 Alur sambung (Box) — dibuka lalu dibatalkan

| Langkah | Hasil | Verdict |
|---|---|---|
| Klik **Hubungkan** pada Box | Dialog "Hubungkan Box" — "Anda akan diarahkan ke halaman login Box. Masuk dan setujui izin yang diminta." + tombol **Lanjut ke halaman login** | PASS (`live-28-hubungkan-box.png`) |
| Klik **Lanjut ke halaman login** | `POST /bff/api/apps/box/connect`; dialog berubah menjadi "Menunggu Anda menyelesaikan login di tab lain…" + tautan **Buka halaman login lagi** + **Batal**; polling `GET /bff/api/apps/box/status` | PASS (`live-29-tunggu-oauth.png`) |
| Klik **Batal** | Dialog tertutup; `POST /bff/api/apps/box/disconnect` → status `{"status":"not_connected","waiting":false}` | PASS (`live-30-batal-oauth.png`) |

Tidak ada OAuth yang diselesaikan; tidak ada akun tersambung atau terputus.

### 8.3 Defect tampilan: kartu Gmail

Pada bagian **Aplikasi lain**, kartu Gmail rusak di 1280 maupun 375:

- Judul "Gmail" terlipat per huruf karena kolom judul menyusut menjadi **1 px** (terlihat "G" di atas dan "I" di bawah), ikon Gmail tertimpa tombol **Hubungkan**, dan deskripsi terpotong menjadi 2 baris.
- Penyebab: `.app-mini` memakai grid `minmax(0, 1fr) auto`; kolom kedua berisi dua tombol (Hubungkan + **Cara kerja tombol draf**, 100 px + 174 px) sehingga kolom `auto` menghabiskan lebar kartu dan menyisakan 1 px untuk judul.
- Bukti: `live-25-aplikasi.png`, `live-31-gmail-kartu.png`.

`.page` scrollHeight 1280: **800 px**; 375: **1784 px**; tanpa overflow horizontal.

---

## 9. Pengaturan (5 bagian, baca saja)

| Bagian | Isi yang teramati | Permintaan | Konsol | Verdict | Bukti |
|---|---|---|---|---|---|
| Umum | Nama bisnis "Colorbox" + Simpan; Bahasa Indonesia; zona waktu WIB; Tema Terang/Gelap; **Mode admin: Mati** | — | 0 error | PASS | `live-32-pengaturan-umum.png` |
| Notifikasi | Notifikasi browser "Belum diizinkan. Izinkan"; 3 sakelar tugas (Nyala) | — | 0 error | PASS | `live-33-pengaturan-notifikasi.png` |
| Keamanan | Penjelasan izin; tabel kemampuan dimatikan untuk semua pegawai; "Selalu menunggu izin Anda" | `GET /settings/security` 200 | 0 error | PASS | `live-33-pengaturan-keamanan.png` |
| Paket dan biaya | Paket Pro; biaya bulan ini $0.27 dari $15.00; 7/10 pegawai; 2/5 tim; 0/3 tugas bersamaan; rincian per pegawai & per hari | `GET /usage` 200 | 0 error | PASS | `live-33-pengaturan-paket.png` |
| Data | Lama simpan log 90 hari; Ekspor riwayat chat (Unduh) | `GET /settings/knowledge` 200 | 0 error | PASS | `live-33-pengaturan-data.png` |

Tidak ada setelan yang diubah (tidak ada permintaan tulis dari halaman ini selama uji). Tema gelap diuji dengan kunci preferensi lokal `pa.theme` (nilai yang sama yang ditulis sakelar Tema), lalu dihapus lagi — bukan perubahan setelan server.

Catatan isi: rincian biaya Paket masih menyebut **Rian, Budi, Diana** (pegawai yang sudah di-soft-delete, total 10 nama padahal "Pegawai 7 dari 10"). Ini data Backend, bukan cacat tampilan FE, tetapi membingungkan pengguna.

`.page` scrollHeight: 1280 **800 px**, 375 **760 px**, tanpa overflow.

---

## 10. Detail pegawai (4 tab) + dialog Atur

Objek uji: **Siti** (pegawai bawaan; `color:"sky"`, `model:null`, `provider:null` sebelum uji).

### 10.1 Tab

| Tab | Isi yang teramati | Permintaan | Verdict | Bukti |
|---|---|---|---|---|
| Ringkasan | Blok **Bisa Anda ubah** (Warna: Biru langit; Tingkat ketelitian: Ikuti bawaan) + **Diatur sistem** (Nama dan tugas, Aturan inti, Izin keamanan — tanpa editor) + Tugas dan gaya bicara | `GET /bots/siti`, `/sessions`, `/runs`, `/usage/bots`, `/models` — semua 200 | PASS | `live-34-agen-ringkasan.png` |
| Pekerjaan | Tabel tugas terakhir (waktu, tugas, status); termasuk run uji "Balas satu kata: oke" | — | PASS | `live-35-agen-pekerjaan.png` |
| Keahlian | Daftar kemampuan + sakelar (Cari di internet, Baca gambar, Ingatan, Cari percakapan lama, …) | `GET /agents/siti/skills` 200 | PASS | `live-36-agen-keahlian.png` |
| Ingatan | **Belum ada yang diingat** + penjelasan "Ingatan ini dipakai bersama…". Tidak ada tombol hapus (0 item) | `GET /bots/siti/memory` 200 | PASS (baca saja) | `live-37-agen-ingatan.png` |

Mode admin mati: tidak ada nama model mentah, provider, SOUL, atau daftar toolset di layar; hanya label manusiawi dan pemisahan "Bisa Anda ubah" vs "Diatur sistem".

### 10.2 Dialog Atur — ubah lalu pulihkan warna

| # | Langkah | Harapan | Hasil teramati | Verdict | Bukti |
|---|---|---|---|---|---|
| 1 | Buka **Atur** | Pilihan warna + tingkat ketelitian | Dialog "Atur Siti" dengan **9 swatch** termasuk **Warna Netral**, dan 4 pilihan ketelitian | PASS | `live-38-atur-dialog.png` |
| 2 | Pilih **Hijau toska**, klik **Simpan** | `PATCH /bots/siti` 200, tersimpan | **200**; server: `{"color":"teal","model":null,"provider":null}` | PASS | `live-39-atur-tersimpan.png` |
| 3 | Periksa kartu tanpa muat ulang | Nilai baru tampil | Kartu **masih "Biru langit"** dengan avatar biru; nilai baru baru muncul setelah muat ulang | **FAIL (FE-3)** | `live-39-atur-tersimpan.png` vs `live-40-atur-setelah-muat-ulang.png` |
| 4 | Muat ulang | Nilai tersimpan | "Hijau toska" + avatar toska (`#0b8a7f`) | PASS | `live-40-atur-setelah-muat-ulang.png` |
| 5 | Ubah **Tingkat ketelitian** ke Seimbang | Pilihan bisa dipilih, lalu `PATCH` mengirim model | Ketiga pilihan (**Hemat & cepat, Seimbang, Paling teliti**) **disabled**; hanya "Ikuti bawaan" yang bisa dipilih; tidak ada `PATCH` yang terkirim | **FAIL (FE-2)** | `live-41-atur-ketelitian.png` |
| 6 | Pulihkan warna **Biru langit**, Simpan | Kembali ke nilai awal | **200**; server: `{"color":"sky","model":null,"provider":null}`; setelah muat ulang UI "Biru langit" / "Ikuti bawaan" | PASS | `live-42-atur-dipulihkan.png` |

Catatan: defect FE-1 versi uji lokal ("Netral tidak bisa dipilih lagi") **tidak tereproduksi** di build ini — swatch **Warna Netral** ada dan berfungsi. Lihat §13.

### 10.3 Akar masalah FE-2

`GET /api/models` di produksi mengembalikan `{"default":{"model":"deepseek-v4.1-flash","provider":"opencode"},"providers":[…,"opencode-zen"…]}`. `frontend/src/modelTiers.ts` (`tiersFrom`) hanya memakai provider yang `slug === cat.default.provider`, sehingga daftar tier kosong → `Dialogs.tsx:517` (`off = !tiers[t.id].length …`) menonaktifkan ketiga pilihan. Di lokal slug cocok, jadi kontrolnya hidup.

### 10.4 Tampilan responsif

`.page` scrollHeight 1280×800: **828 px**; 375×812: **942 px**; tombol **Ajak bicara** dan **Atur** terlihat di layar pertama; tanpa overflow horizontal.

---

## 11. Responsif 1280×800 vs 375×812

Semua halaman diuji dengan sesi yang sama, tema terang. Tidak ada overflow horizontal di satu pun halaman (`documentElement.scrollWidth === innerWidth`).

| Halaman | `.page` scrollHeight 1280 | `.page` scrollHeight 375 | Overflow 1280 / 375 | Aksi utama di layar pertama (375) | Bukti |
|---|---|---|---|---|---|
| Beranda | 956 | 1807 | tidak / tidak | **Beri tugas** (atas), **Tinjau** (y 355–395) | `live-03`, `live-45-beranda-375` |
| Tim | — (`main` 800) | 119 | tidak / tidak | **Tim baru** (y 192–232) | `live-04`, `live-46-tim-375` |
| Chat | — (`main` 800) | — (`main` 800) | tidak / tidak | **Topik baru** (y 60–100), komposer terlihat | `live-05`, `live-47-chat-375` |
| Jadwal & tugas | 800 (papan) | 760 | tidak / tidak | **Filter** (y 76–116), **Tambah** (y 132–172) | `live-09`, `live-48-kanban-375` |
| Pengetahuan | 800 | 760 | tidak / tidak | **Unggah berkas** (y 113–153), **Tambah link** (y 231–271) | `live-20`, `live-49-pengetahuan-375` |
| Aplikasi | 800 | 1784 | tidak / tidak | Pencarian + **Hubungkan** (y 538–578) | `live-25`, `live-50-aplikasi-375` |
| Pengaturan | 800 | 760 | tidak / tidak | Tab 5 bagian + **Simpan** (y 266–306) | `live-32`, `live-51-pengaturan-375` |
| Detail pegawai | 828 | 942 | tidak / tidak | **Ajak bicara**, **Atur** (y 223–263) | `live-34`, `live-52-agen-375` |

**Tema gelap (spot-check 2 halaman, 1280×800):** Beranda (`.page` 956 px) dan Chat (`main` 800 px) — kontras teks/latar baik, tanpa overflow, 0 error konsol, 0 permintaan gagal (`live-53-beranda-1280-gelap.png`, `live-54-chat-1280-gelap.png`).

**Catatan responsif kecil:** di 375, baris Pengetahuan memberi kolom nama hanya ± **119 px** (judul berkas terlipat 3–4 baris) — masih terbaca dan tanpa overflow, tetapi rapat (FE-6). Kartu Gmail tetap rusak di 375 (FE-1).

---

## 12. Konsol, jaringan, dan log server

### 12.1 Per halaman (1280×800, tema terang)

| Rute | Judul | Error konsol | Permintaan gagal (4xx/5xx) | Overflow |
|---|---|---|---|---|
| `#/` | Beranda | 0 | 0 | tidak |
| `#/grup` | Tim (grup **test**) | 0 | 0 | tidak |
| `#/chat/siti` | Siti | 0 | 0 | tidak |
| `#/kanban` | Jadwal & tugas | 0 | 0 | tidak |
| `#/pengetahuan` | Pengetahuan | 0 | 0 | tidak |
| `#/aplikasi` | Aplikasi | 0 | 0 | tidak |
| `#/pengaturan` | Pengaturan | 0 | 0 | tidak |
| `#/agen/siti` | Siti (detail) | 0 | 0 | tidak |

Permintaan 4xx yang **disengaja** selama uji: `POST /auth/login` 3× 401 (1 lewat `/bff` dari UI, 2 lewat `/api` dari curl), `GET /auth/me` 3× 401 (tanpa/rusak/sesi berakhir) + 1× 499 (klien menutup saat muat ulang), `GET /api/products/search` 1× 400 (probe tanpa parameter), `GET /api/product-images/{nama}` 3× 404 (probe nama tak ada). Satu-satunya `requestfailed` adalah penutupan stream `/bff/api/events` saat logout (disengaja).

### 12.2 Log server (read-only, jendela uji 00.10–00.45 UTC / 07.10–07.45 WIB)

| Sumber | Hasil |
|---|---|
| `journalctl -u pegawai-ai-bff` (150 baris) | Tidak ada traceback, exception, atau 5xx. Satu baris cocok pola "500" hanyalah `"POST /mcp HTTP/1.1" 200 OK` |
| `journalctl -u nginx` | Tidak ada baris error/crit/emerg |
| Access log nginx | 306× 200, 7× 304, 7× 204, 6× 401, 6× 201, 3× 404, 1× 499, 1× 400, 1× 301, 1× 202 — **0 respons 5xx** |

Rincian 204/201 pada jendela uji (bukti aksi uji terjadi dan bersih):

```
201 POST /bff/api/tasks            07:20:24
201 POST /bff/api/kb/files         07:24:57 (3×)
201 POST /bff/api/kb/files         07:25:20
201 POST /bff/api/kb/links         07:25:45
204 DELETE /bff/api/bots/siti/sessions/web-…   07:19:04
204 DELETE /bff/api/kb/items/{id}  07:27:14 … 07:27:32 (5×)
204 POST /bff/api/apps/box/disconnect          07:28:58
```

### 12.3 Kinerja API (terukur)

| Sasaran | Connect/TLS | TTFB | Total |
|---|---|---|---|
| `GET /demo/` (statis) | 0,05 dtk | **0,10 dtk** | 0,10 dtk |
| `GET /api/me` | 0,06 / 0,09 dtk | **6,55 dtk** | 6,55 dtk |
| `GET /api/me` (ulang) | 0,05 / 0,08 dtk | **6,58 dtk** | 6,58 dtk |
| `GET /api/tasks/board` | — | **6,19 dtk** | 6,19 dtk |

Jaringan ke VPS cepat (TLS ± 0,09 dtk), jadi ± 6,5 detik itu **waktu proses server** (kemungkinan koneksi/kueri Postgres Neon per permintaan), bukan jaringan klien. Dampak langsung: setiap perpindahan halaman menampilkan skeleton ± 6–8 dtk, tombol "Menambah…" menahan ± 8 dtk, dan Beranda baru lengkap setelah ± 7 dtk.

---

## 13. Foto produk (migrasi 013/014)

| # | Uji | Hasil | Verdict |
|---|---|---|---|
| 1 | `GET /api/products/search?q=dress` | **200**, data produk lengkap (id, kategori, harga, warna, ukuran, url) | PASS |
| 2 | `GET /api/products/search` tanpa parameter | **400** "Isi q atau salah satu filter…" | PASS |
| 3 | `GET /api/product-images/cbx-01-contrast-stitch-chambray-shirt.jpg` | **200** `image/jpeg`, 80.322 B, JPEG valid 554×800 | PASS |
| 4 | `GET /api/product-images/cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg` | **200** `image/jpeg`, 64.447 B | PASS |
| 5 | `GET /api/product-images/cbx-05-double-pocket-flared-denim-grey.jpg` | **200** `image/jpeg`, 39.523 B | PASS |
| 6 | Nama tak ada / ekstensi bukan `.jpg` | **404** "Foto produk tidak ditemukan" | PASS |
| 7 | Pemetaan foto ke produk (`image_url`, `image_description`) | **Semua produk** yang dicari (`dress`, `tote`, `skirt`, `chambray`, `barrel`) mengembalikan `image_url: null` dan `image_description: null` | **BLOCKED(BE)** — tabel `product_images`/`product_image_descriptions` ada (endpoint tidak 500 lagi) tetapi **kosong** |

Kesimpulan: masalah 500 migrasi 013/014 dari audit 23 Nov **sudah tidak terjadi** (endpoint melayani JPEG), tetapi foto belum dipetakan ke katalog sehingga tidak ada foto produk yang bisa tampil di UI. Ini pekerjaan data/sync Backend, bukan FE.

Catatan keamanan kecil (bukan temuan baru): `GET /api/product-images/..%2f..%2f.env` dibalas **200 text/html 666 B** — yaitu shell SPA (`index.html`), bukan isi berkas; tidak ada kebocoran. Sama kelasnya dengan catatan `location /demo` (alias + try_files) di `audit-vps.md` #18.

---

## 14. Perbandingan dengan uji lokal + regresi

| Aspek | Lokal (22 Nov, `bukti-uji-lokal.md`) | Live (24 Nov) | Selisih |
|---|---|---|---|
| Login / salah sandi / sesi berakhir | PASS | PASS | sama |
| Logout (UI) | PASS | PASS | sama |
| Logout tidak menginvalidasi token | BLOCKED(BE) | BLOCKED(BE) | sama |
| `/api/*` tanpa token → 200 | BLOCKED(BE), 10 bot | BLOCKED(BE), 7 bot | sama (data prod beda) |
| Kanban buat/pindah/arsip | PASS | PASS | sama |
| Hapus permanen tugas | BLOCKED(BE) | BLOCKED(BE), `archived` 1→2 | sama |
| KB unggah TXT/MD/PDF/DOCX + link | PASS | PASS (+1 PDF rusak → `failed`, PDF valid → `ready`) | sama |
| Aplikasi: alur sambung lalu batal | PASS (Box → portal connector) | PASS (Box → dialog tunggu login, lalu Batal) | sama (UI hanya sampai dialog tunggu) |
| Katalog aplikasi | 54 aplikasi, 1 tersambung (Canva) | 54 aplikasi, **0** tersambung; Gmail `disconnected` | **beda konfigurasi prod** (Canva tidak tersambung) |
| Kartu Gmail di "Aplikasi lain" | Tidak terlihat (Gmail tersambung → tampil sebagai baris) | **Rusak** (judul 1 px, ikon tertimpa) | **regresi terlihat di prod** (FE-1) |
| Tingkat ketelitian di dialog Atur | Bisa dipilih (Seimbang → `PATCH` model) | **Semua pilihan disabled** | **regresi di prod** (FE-2) |
| Warna Netral di dialog Atur | **Tidak ada** pilihan Netral (FE-1 lokal) | **Ada** dan berfungsi | **defect lokal sudah tidak ada** |
| Kartu "Bisa Anda ubah" setelah Simpan | Tidak dicatat (langsung muat ulang) | Menampilkan nilai lama sampai muat ulang | defect baru teramati (FE-3) |
| Responsif 375 | PASS (arsip tangkapan) | PASS terukur (0 overflow, CTA terlihat) kecuali kartu Gmail | beda hanya FE-1 |
| Latensi API | cepat (BFF lokal + Postgres 5433) | **± 6,5 dtk TTFB** per panggilan | **regresi lingkungan prod** (B-4) |
| Foto produk | Endpoint 500 (tabel hilang) | Endpoint 200 JPEG; pemetaan kosong | **membaik sebagian** |

### 14.1 Daftar regresi (yang di lokal baik, di live tidak)

| # | Regresi | Bukti | Tingkat |
|---|---|---|---|
| R-1 | Pilihan **Tingkat ketelitian** mati total di dialog Atur (tidak bisa mengubah model) | §10.2 baris 5, §10.3 | Tinggi (kontrol terlihat tetapi tidak bisa dipakai) |
| R-2 | Kartu **Gmail** di Aplikasi rusak (judul terlipat 1 px, ikon tertimpa tombol) | §8.3 | Sedang (kosmetik, menutupi nama aplikasi) |
| R-3 | Setiap panggilan API ± 6,5 dtk → skeleton Beranda ± 7 dtk, tombol "Menambah…" ± 8 dtk | §12.3 | Tinggi (persepsi "lambat/rusak") |
| R-4 | Konektor Canva tidak tersambung di prod (di lokal tersambung) | §8.1 | Info (konfigurasi deploy) |

### 14.2 Yang membaik dibanding lokal

- Defect FE lokal "warna Netral tidak bisa dipulihkan" **tidak ada** di build ini (swatch Netral tampil dan bisa dipilih).
- Endpoint foto produk tidak lagi 500 (tabel migrasi 013/014 ada).

---

## 15. Daftar defect

### 15.1 Frontend (bisa diperbaiki FE)

| # | Gejala | Halaman / langkah | Berkas / akar masalah | Dampak | Severity |
|---|---|---|---|---|---|
| **FE-1** | Kartu **Gmail** di bagian "Aplikasi lain" rusak: judul terlipat satu huruf per baris (kolom judul 1 px), ikon tertimpa tombol **Hubungkan**, deskripsi terpotong. Terjadi di 1280 dan 375 | Aplikasi → Aplikasi lain | `frontend/src/pages.css:641-646` (`.app-mini` grid `minmax(0,1fr) auto`) + `frontend/src/connections.tsx:576-580` (dua tombol di kolom aksi) | Nama aplikasi tidak terbaca; pengguna tidak yakin kartu mana | Sedang |
| **FE-2** | Ketiga pilihan **Tingkat ketelitian** di dialog Atur `disabled`; hanya "Ikuti bawaan" yang bisa dipilih sehingga model pegawai tidak bisa diubah dari UI | Detail pegawai → Atur | `frontend/src/modelTiers.ts` `tiersFrom()` mencocokkan `slug === cat.default.provider`; di prod `default.provider = "opencode"` tetapi katalog berisi `"opencode-zen"` → tier kosong → `Dialogs.tsx:517` menonaktifkan | Tidak bisa mengatur biaya/ketelitian; copy dialog menjanjikan hal yang tidak bisa dilakukan | Tinggi |
| **FE-3** | Setelah **Simpan** di dialog Atur, kartu "Bisa Anda ubah" + avatar tetap menampilkan nilai **lama** (warna) sampai halaman dimuat ulang | Detail pegawai → Atur → Simpan | `frontend/src/Dialogs.tsx` hanya memanggil `refreshBots()` (daftar), sedangkan detail memakai snapshot sendiri: `frontend/src/Agents.tsx:135-136` (`useLoad(() => api.bot(id))`, tanpa muat ulang setelah PATCH) | Pengguna mengira simpan gagal lalu menyimpan berulang | Sedang |
| FE-4 | Copy dialog Atur untuk pegawai bawaan menjanjikan "Anda bisa mengubah warna dan **tingkat ketelitiannya**" padahal ketelitian tidak bisa dipilih (akibat FE-2) | Detail pegawai → Atur | `frontend/src/Dialogs.tsx:481` | Janji tidak terpenuhi | Rendah (ikut FE-2) |
| FE-5 | Konfirmasi **Batalkan** tugas memakai tombol gaya `btn primary` (sama seperti tombol aman), tidak seperti konfirmasi hapus topik yang memakai `btn danger` | Jadwal & tugas → kartu → Batalkan | `frontend/src/Kanban.tsx` (dialog konfirmasi) | Risiko salah klik pada aksi merusak | Rendah |
| FE-6 | Di 375 px, baris Pengetahuan memberi kolom nama hanya ± 119 px; judul berkas terlipat 3–4 baris | Pengetahuan @375 | `frontend/src/pages.css` (`.kb-row`) | Terbaca tetapi rapat | Rendah |

Catatan (bukan defect, untuk diketahui): setelah **Simpan ke Pengetahuan**, teks URL tetap di kolom pesan (bisa terkirim sebagai pesan biasa); label "Tugas berulang" menyusut menjadi "berulang" di 375 (kelas `.hide-sm`, `aria-label` tetap benar); ajakan notifikasi browser muncul sekali setelah run pertama.

### 15.2 Backend (jangan diperbaiki di FE)

| # | Gejala | Bukti | Rujukan |
|---|---|---|---|
| **B-1** | JWT tidak ditegakkan: `/api/*` mengembalikan **200** dengan data tenant `default` untuk permintaan tanpa token maupun token rusak (bots, papan tugas, KB, settings, groups, connections, apps/catalog, /api/me) | §2.1 baris 8–13 | `catatan-untuk-backend.md` §2.1 |
| **B-2** | Logout tidak menginvalidasi token; `/auth/me` dengan token lama tetap **200** (2×) | §2.1 baris 7 | `catatan-untuk-backend.md` §2.8 |
| **B-3** | Tidak ada `DELETE /api/tasks/{id}`: tugas uji hanya bisa diarsipkan, sehingga menyisakan 1 baris arsip di produksi | §6.4, §12 | Kontrak tugas |
| **B-4** | Latensi API ± 6,2–6,6 dtk TTFB per permintaan (statis 0,10 dtk) → skeleton Beranda ± 7 dtk, aksi tulis ± 8 dtk | §12.3 | Kinerja deploy (Neon/koneksi DB) |
| **B-5** | `product_images`/`product_image_descriptions` kosong: semua produk `image_url: null` walau endpoint foto melayani JPEG | §13 | Migrasi 013/014 + sync katalog |
| **B-6** | Registrasi publik tetap terbuka (`POST /api/auth/register`, tab **Daftar** di halaman masuk). **Tidak dijalankan** sesuai batasan uji | §2.2 bukti `live-01-login.png` | `audit-vps.md` #9 |
| **B-7** | PDF tanpa xref tetap membuat item KB (**201**, `status:"failed"`), bukan 4xx | §7.2 | `catatan-untuk-backend.md` §2.9 |
| **B-8** | `BFF_API_KEY` dipakai sebagai secret JWT (temuan audit, tidak diuji ulang di run ini) | — | `audit-vps.md` #2 |
| **B-9** | `app.pegawaiAI.com` tidak punya DNS; pencarian nama domain dari mesin uji **timeout** (tanpa jawaban), hanya `139.190.107.151.sslip.io` yang resolve | §1, §12 | `audit-vps.md` #16 |
| **B-10** | Rincian biaya Paket masih memuat pegawai yang sudah dihapus (Rian, Budi, Diana) — 10 nama padahal "7 dari 10" | §9 | Data usage |

### 15.3 Blocker (yang menghalangi penerimaan)

| # | Blocker | Dampak pada penerimaan Hari 5 |
|---|---|---|
| 1 | **B-1/B-2** — API terbuka tanpa token dan logout no-op | "Login live" secara UI **lulus**, tetapi keamanan akses data **belum**; tidak boleh diklaim aman |
| 2 | **B-3** — tidak ada hapus tugas | Data uji tidak bisa dibersihkan 100%; tersisa 1 arsip |
| 3 | **R-1/FE-2** — tingkat ketelitian mati | Fitur yang tampil di UI tidak bisa dipakai (melanggar aturan "jangan ada kontrol mati") |
| 4 | **B-4** — latensi ± 6,5 dtk/permintaan | Demo ke pengguna terasa lambat; demo langsung berisiko dinilai "tidak jalan" |

---

## 16. Bukti pembersihan

| Data uji | Tindakan | Bukti |
|---|---|---|
| Tugas "Uji QA live Sprint 5 - hapus setelah tes" | Dibuat (201) → dibatalkan → dipulihkan → dibatalkan lagi. **Tidak bisa dihapus permanen** (B-3) | Angka kolom §6.3: queue 4→5→4, archived 1→2; kartu berstatus **Dibatalkan** di Arsip (`live-14-arsip-akhir.png`) |
| Topik chat "Balas satu kata: oke" | `DELETE /bff/api/bots/siti/sessions/{sid}` **204** | Sebelum 0 topik → 1 → **0**; `GET /bots/siti/sessions` → `{"object":"list","data":[]}` (`live-08-topik-dihapus.png`) |
| KB `uji-live.md` | `DELETE /bff/api/kb/items/{id}` **204** | Daftar 4 → 9 → **4** |
| KB `uji-live.pdf` (gagal) | **204** | idem |
| KB `uji-live-pdf-valid.pdf` | **204** | idem |
| KB `uji-live.docx` | **204** | idem |
| Link `Example Domain` | **204** | idem (`live-24-pengetahuan-bersih.png`) |
| Warna Siti | Semula `sky` → `teal` → **dipulihkan `sky`**, `model:null`, `provider:null` | §10.2 baris 6; verifikasi API terakhir: `{'color': 'sky', 'model': None, 'provider': None}` |
| Sambungan Box | Dibatalkan sebelum OAuth; `POST /api/apps/box/disconnect` | `{"status":"not_connected","waiting":false}` |
| Setelan, sambungan, akun lain | Tidak diubah | `GET /api/settings` → `company_name: Colorbox, timezone: Asia/Jakarta, language: id`; `connections` → `gdrive: connected`, `gmail: disconnected` |
| Berkas uji sementara (`.qa-tmp/`) | Dihapus setelah uji | Folder tidak ada lagi |
| Preferensi tema (kunci lokal `pa.theme`) | Diisi `dark` saat spot-check lalu dihapus | `live-53`, `live-54`; setelah uji tema kembali terang |

Verifikasi akhir (24 Nov 2026, 07.45 WIB) lewat API aplikasi:

```
GET /api/kb/items                     → 4 item: 127.0.0.1/admin, docs.google.com/…, httpbin.org/html, panduan_brand_colorbox.md
GET /api/bots/siti/sessions           → {"object":"list","data":[]}
GET /api/tasks/board                  → {"queue":4,"running":0,"needs_you":3,"done":0}
GET /api/tasks/board?archived=true    → {"archived":2}   (1 arsip lama + 1 tugas uji, tidak bisa dihapus — B-3)
GET /api/bots/siti                    → color "sky", model null, provider null
GET /api/apps/box/status              → {"status":"not_connected","waiting":false}
GET /api/connections                  → gdrive connected, gmail disconnected
GET /api/settings                     → company_name Colorbox, timezone Asia/Jakarta, language id
```

Dua entri KB `failed` (`127.0.0.1/admin`, `docs.google.com/document/…`) dan satu arsip lama **sudah ada sebelum uji ini** — bukan dibuat oleh uji Hari 5 dan tidak diubah.

---

## 17. Yang tidak diuji / ditunda (jangan diklaim selesai)

Sesuai `keputusan-scope-hari3.md` §7 dan batasan uji:

| Item | Status | Alasan |
|---|---|---|
| Setelan KB (ukuran chunk, retensi, kuota per agen) | **Ditunda (keputusan Hari 3)** — tidak ada UI/schema; tidak diuji | Tidak ada kontrak Backend |
| Edit `SKILL.md`, `AGENTS.md`, `config.yaml` | **Ditunda** — tidak ada di UI, tidak diuji | Sengaja tidak dibangun |
| Log mentah pegawai (Employee logs) | **Ditunda** — tidak ada endpoint; tidak diuji | Menunggu kontrak redaksi |
| Schema/editor Master Template 11 bagian | **Ditunda** — hanya dokumentasi; tidak diuji | Butuh tabel + editor |
| Hapus/kelola memori jangka panjang | **Tidak diuji** — tab Ingatan hanya dibaca (0 item), tidak ada hapus | Tanpa item memori; sesuai batasan "jangan hapus memori" |
| Temperature LLM | Tidak diuji — tidak ada field | Butuh kontrak Backend |
| Renderer Telegram kustom | Tidak diuji | Menunggu keputusan `rich_messages` |
| "Kerjakan sekarang" / run tugas (LLM penuh) | **Tidak dijalankan** | Batas LLM uji (1 pesan chat) |
| Aksi "Perlu Anda" (setujui/tolak) | **Tidak dijalankan** | 3 item produksi dibiarkan utuh |
| Kirim pesan grup / ke beberapa pegawai | **Tidak dijalankan** | Memicu banyak run LLM |
| OAuth sampai akun tersambung, putuskan sambungan | **Tidak dijalankan** | Hanya dibuka sampai halaman tunggu lalu Batal |
| Registrasi akun (`Daftar`) | **Tidak dijalankan** (terbuka di prod — dicatat B-6) | Batasan uji |
| Kirim email/WhatsApp | **Tidak dijalankan** | Batasan uji |
| Halaman grup Admin (Marketing, CS, Agen, Kemampuan, Evaluasi, Aktivitas) | **Tidak diuji** | Mode admin mati; di luar UI pengguna awam |
| Ekspor riwayat chat (Pengaturan → Data) | Tidak diklik | Menghasilkan unduhan; di luar scope bukti |

---

## 18. Indeks tangkapan layar

Semua berkas ada di `docs-kaf/sprint5/` (1280×800 kecuali yang ditandai 375).

| Berkas | Isi |
|---|---|
| `live-01-login.png` | Halaman masuk tanpa sesi |
| `live-02-login-gagal.png` | Banner "Email atau kata sandi salah." |
| `live-03-beranda.png` | Beranda setelah masuk |
| `live-04-tim.png` | Tim + panel grup **test** |
| `live-05-chat.png` | Chat Siti sebelum ada topik |
| `live-06-chat-balasan.png` | Balasan "oke" untuk pesan uji |
| `live-07-hapus-topik-konfirmasi.png` | Konfirmasi hapus topik |
| `live-08-topik-dihapus.png` | Riwayat kosong setelah hapus |
| `live-09-kanban.png` | Papan tugas (kolom + angka) |
| `live-10-task-created.png` | Tugas uji di kolom Antre |
| `live-11-task-menu.png` | Menu kartu (Ubah/Batalkan) + konfirmasi |
| `live-12-task-archived.png` | Setelah dibatalkan |
| `live-13-arsip.png` | Filter Arsip berisi tugas uji |
| `live-14-arsip-akhir.png` | Keadaan akhir arsip (tugas uji "Dibatalkan") |
| `live-15-kb-tray.png` | Panel lampiran Pengetahuan di chat |
| `live-16-kb-unggah.png` | Status unggah MD/PDF/DOCX |
| `live-17-kb-status.png` | Status setelah PDF valid ditambahkan |
| `live-18-kb-link-chip.png` | Chip "Simpan ke Pengetahuan" untuk URL |
| `live-19-kb-tray.png` | Tray: 4 tersimpan + 1 gagal + link |
| `live-20-pengetahuan.png` | Halaman Pengetahuan (9 entri) |
| `live-21-kb-lihat.png` | Teks tersimpan untuk `example.com` |
| `live-22-kb-teks-md.png` | Teks hasil ekstraksi MD (penanda uji) |
| `live-23-kb-teks-pdf.png` | Penampil PDF valid |
| `live-24-pengetahuan-bersih.png` | Pengetahuan kembali 4 entri |
| `live-25-aplikasi.png` | Tersambung (akun `<akun>`) + katalog |
| `live-26-aplikasi-cari.png` | Cari "notion" → 1 hasil |
| `live-27-aplikasi-cari-kosong.png` | Pencarian tanpa hasil + "Hapus pencarian" |
| `live-28-hubungkan-box.png` | Dialog "Hubungkan Box" |
| `live-29-tunggu-oauth.png` | Menunggu login di tab lain |
| `live-30-batal-oauth.png` | Setelah Batal (status kembali not_connected) |
| `live-31-gmail-kartu.png` | Bukti FE-1: kartu Gmail rusak (potongan) |
| `live-32-pengaturan-umum.png` | Pengaturan → Umum |
| `live-33-pengaturan-notifikasi.png` | Pengaturan → Notifikasi |
| `live-33-pengaturan-keamanan.png` | Pengaturan → Keamanan |
| `live-33-pengaturan-paket.png` | Pengaturan → Paket dan biaya |
| `live-33-pengaturan-data.png` | Pengaturan → Data |
| `live-34-agen-ringkasan.png` | Detail Siti → Ringkasan |
| `live-35-agen-pekerjaan.png` | Tab Pekerjaan |
| `live-36-agen-keahlian.png` | Tab Keahlian |
| `live-37-agen-ingatan.png` | Tab Ingatan (kosong) |
| `live-38-atur-dialog.png` | Dialog Atur (9 swatch termasuk Netral) |
| `live-39-atur-tersimpan.png` | Bukti FE-3: kartu masih "Biru langit" setelah simpan |
| `live-40-atur-setelah-muat-ulang.png` | Setelah muat ulang: "Hijau toska" |
| `live-41-atur-ketelitian.png` | Bukti FE-2: ketiga pilihan ketelitian nonaktif |
| `live-42-atur-dipulihkan.png` | Warna dipulihkan ("Biru langit") |
| `live-43-sesi-berakhir.png` | Banner "Sesi Anda berakhir…" |
| `live-44-beranda-setelah-masuk.png` | Beranda setelah masuk ulang |
| `live-45-beranda-375.png` | Beranda @375 |
| `live-46-tim-375.png` | Tim @375 |
| `live-47-chat-375.png` | Chat @375 |
| `live-48-kanban-375.png` | Jadwal & tugas @375 |
| `live-49-pengetahuan-375.png` | Pengetahuan @375 |
| `live-50-aplikasi-375.png` | Aplikasi @375 |
| `live-51-pengaturan-375.png` | Pengaturan @375 |
| `live-52-agen-375.png` | Detail pegawai @375 |
| `live-53-beranda-1280-gelap.png` | Beranda tema gelap |
| `live-54-chat-1280-gelap.png` | Chat tema gelap |
| `live-55-logout.png` | Kembali ke halaman masuk setelah Keluar |

---

## 19. Kesimpulan

1. **Alur UI terbukti di produksi**: login, sesi berakhir, logout, Beranda, Tim, Chat (kirim + hapus topik), Jadwal & tugas (buat/pindah/arsip), Pengetahuan (unggah MD/PDF/DOCX + link, baca teks, hapus), Aplikasi (daftar, cari, alur sambung lalu batal), Pengaturan 5 bagian, detail pegawai 4 tab, dialog Atur, serta 1280/375 + tema gelap. Tidak ada error konsol dan tidak ada respons 5xx.
2. **Dua defect FE baru** harus diperbaiki sebelum demo: kartu Gmail rusak (FE-1) dan pilihan ketelitian mati (FE-2); satu defect perilaku (FE-3, kartu tidak menyegar setelah simpan).
3. **Blocker BE tetap**: API terbuka tanpa token (B-1), logout no-op (B-2), tidak ada hapus tugas (B-3), latensi ± 6,5 dtk (B-4). Empat hal ini yang membuat demo belum bisa disebut aman dan nyaman, bukan alur UI-nya.
4. **Item yang ditunda tidak diklaim selesai** — daftarnya ada di §17.

---

## Uji ulang setelah perbaikan

**Ringkasan**

- Dijalankan **25 November 2026, 00.26–00.36 WIB (24 Nov 2026, 17.26–17.36 UTC)** terhadap aplikasi live
  `https://139.190.107.151.sslip.io/demo/` — **setelah** deploy rilis **`775783d`** (lihat `audit-vps.md` §14).
- Build yang diuji: `assets/index-aDJo1iqq.js` (`e828d284…`) + `assets/index-8hSpk8Z5.css` (`9023cf85…`) +
  `index.html` (`47fc3629…`) — ketiganya byte-identik dengan hasil `npm run build` lokal dari commit `775783d`.
- Metode sama seperti uji Hari 5: Chromium headless, viewport 1280×800 dan 375×812, akun `admin@pegawai.ai`
  (peran `admin`), **mode admin mati**, sesi login baru lewat form (bukan token lama).
- Batasan: **tidak ada** run LLM, tidak ada tugas dibuat/dibatalkan, tidak ada OAuth, tidak ada perubahan
  KB/sambungan/setelan. Satu-satunya tulisan adalah `PATCH /api/bots/siti` untuk menguji lalu memulihkan
  warna dan tingkat ketelitian Siti (± 6 panggilan tulis, semuanya dikembalikan).
- Sanitasi: tidak ada token, kata sandi, atau email yang dicetak di dokumen ini.

| # | Retest | Verdict |
|---|---|---|
| FE-1 | Kartu Gmail di "Aplikasi lain" (1280 & 375) | **PASS** |
| FE-2 | Pilihan Tingkat ketelitian aktif, ubah → simpan → pulihkan | **PARTIAL** — pilihan aktif dan "Hemat & cepat" tersimpan 200; "Seimbang" ditolak **400 "Model tidak valid"** (temuan baru BE-11) |
| FE-3 | Kartu menyegar tanpa muat ulang setelah Simpan | **PASS** |
| FE-5 | Tombol konfirmasi Batalkan bergaya berbahaya | **PASS** |

---

### 1. FE-1 — kartu Gmail di "Aplikasi lain"

`#/aplikasi`, katalog 39 aplikasi pada bagian "Aplikasi lain".

| Ukuran | Lebar kartu | Kolom judul (`.app-card-head`) | Kolom aksi (`.app-card-act`) | Tumpang tindih | Overflow horizontal |
|---|---|---|---|---|---|
| 1280×800 | 319 px | **183 px** | 100 px | **tidak** | 0 |
| 375×812 | 343 px | **207 px** | 100 px | **tidak** | 0 |

Sebelumnya kolom judul menyusut menjadi **1 px** sehingga "Gmail" terlipat satu huruf per baris. Kini judul
satu baris, ikon Gmail utuh, deskripsi terpotong rapi 2 baris, dan tautan **Cara kerja tombol draf** pindah
ke barisnya sendiri di bawah deskripsi (bukan lagi di kolom aksi). Bukti:
`live-retest-fe1-gmail-1280.png`, `live-retest-fe1-gmail-375.png`.

### 2. FE-2 — pilihan "Tingkat ketelitian" di dialog Atur

Dialog **Atur Siti** sekarang menampilkan 4 baris pilihan (dulu ketiga tier `disabled`):

| Pilihan | Status | Catatan |
|---|---|---|
| Ikuti bawaan | aktif | nilai awal Siti (`model:null`, `provider:null`) |
| Hemat & cepat | **aktif** | satu-satunya model berharga ≤ $1,5 di rute ini: `deepseek-v4.1-flash` |
| Seimbang | **aktif** | 461 model (harga tak dikenal dianggap $3) |
| Paling teliti | `disabled` | tier kosong: tidak ada model berharga > $6 di katalog `opencode-zen` — dinonaktifkan by design (bukan FE-2 kambuh) |

**Alur yang diminta (ubah → simpan → pulihkan):**

| Langkah | Permintaan | Status | Hasil |
|---|---|---|---|
| Pilih **Hemat & cepat** → Simpan | `PATCH /bff/api/bots/siti` body `{"provider":"opencode-zen","model":"deepseek-v4.1-flash"}` | **200** | Kartu langsung menampilkan "Hemat & cepat" tanpa muat ulang |
| Pulihkan **Ikuti bawaan** → Simpan | `{"provider":null,"model":null}` | **200** | Kartu kembali "Ikuti bawaan"; server `model:null`, `provider:null` |
| Pilih **Seimbang** → Simpan | `{"provider":"opencode-zen","model":"~moonshotai/kimi-latest"}` | **400** | Banner merah **"Model tidak valid"**; tidak ada yang tersimpan |

Bukti: `live-retest-fe2-tier-1280.png` (4 pilihan, dua aktif), `live-retest-fe2-tier-saved-1280.png`
(kartu "Hemat & cepat"), `live-retest-fe2-seimbang-gagal-1280.png` (banner 400).

**Akar masalah "Seimbang" (temuan baru BE-11, rinci di `audit-vps.md` §14.8):** katalog `opencode-zen`
memuat 462 model, **19 di antaranya alias berawalan `~`** (`~moonshotai/kimi-latest`, …). `tiersFrom()`
mengambil model median per tier; median tier `seimbang` kebetulan salah satu alias itu, sedangkan validator
backend (`bff/settings.py`, `^[\w.:/@+-]{1,120}$`) menolak karakter `~`. Jadi UI menawarkan pilihan yang
pasti gagal. Perbaikan yang disarankan: izinkan `~` di validator backend, **atau** buang id berawalan `~`
di `tiersFrom()` (diverifikasi: 443 id sisanya lolos validator dan median tier `seimbang` menjadi
`openai/gpt-5.5`). Ini **bukan** cacat tata letak atau logika gating FE-2 yang sudah diperbaiki.

**Verdict:** PARTIAL — kontrol sudah bisa dipakai (tidak lagi mati total) dan tersimpan untuk salah satu
tier, tetapi alur "ubah ke tier lain → simpan" belum 100% andal sampai BE-11 diputuskan.

### 3. FE-3 — kartu menyegar tanpa muat ulang

| Langkah | Permintaan | Status | Hasil teramati |
|---|---|---|---|
| Pilih **Hijau toska** → Simpan | `PATCH /api/bots/siti` `{"color":"teal"}` | **200** | Tanpa reload: kartu "Bisa Anda ubah" → **Hijau toska**, titik warna toska, avatar `--bot: var(--c-teal)` |
| Pilih **Biru langit** → Simpan | `{"color":"sky"}` | **200** | Tanpa reload: kartu → **Biru langit**, avatar `--bot: var(--c-sky)` |

Tidak ada muat ulang di antara kedua langkah. Bukti: `live-retest-fe3-warna-tersimpan-1280.png`
(kartu + avatar toska), `live-retest-nilai-dipulihkan-1280.png` (kembali biru langit, ketelitian "Ikuti bawaan").

### 4. FE-5 — tombol berbahaya pada konfirmasi Batalkan tugas

Kartu di kolom **Antre** → menu ⋯ (**Pilihan lain**) → **Batalkan** membuka dialog "Yakin?":

| Tombol | Kelas | Warna latar | Warna teks |
|---|---|---|---|
| Batal | `btn outline` | transparan | rgb(21,23,28) |
| **Batalkan** | **`btn danger`** | **rgb(196,36,42)** | putih |

Dialog ditutup lewat **Batal** (tidak ada tugas yang dibatalkan). Papan setelah uji tidak berubah:
Antre **4**, Dikerjakan **0**, Perlu Anda **3**, Selesai **0**, Arsip **2**. Bukti:
`live-retest-fe5-konfirmasi-batalkan-1280.png`.

### 5. Konsol, jaringan, dan pemulihan

- Konsol: 0 error halaman. Satu-satunya entri `requestfailed` adalah `GET /bff/api/events: net::ERR_ABORTED`
  saat pindah halaman (penutupan stream SSE, disengaja). Tidak ada respons 5xx selama uji.
- Permintaan tulis selama uji: 2× `PATCH` 400 (Seimbang, ditolak) + 4× `PATCH` 200
  (`model` Hemat, `model` kembali null, `color` teal, `color` sky). Tidak ada `POST` tugas, tidak ada `DELETE`.

| Nilai | Sebelum uji | Sesudah uji | Verifikasi |
|---|---|---|---|
| Warna Siti | `sky` ("Biru langit") | **`sky`** | `GET /api/bots/siti` → `color:"sky"`; kartu "Biru langit" |
| Model/provider Siti | `null` / `null` ("Ikuti bawaan") | **`null` / `null`** | `GET /api/bots/siti` → `model:null, provider:null` |
| Papan tugas | Antre 4 / Dikerjakan 0 / Perlu Anda 3 / Selesai 0 / Arsip 2 | **sama** | `GET /api/tasks/board` |
| Sambungan | gdrive `connected`, gmail `disconnected` | **sama** | `GET /api/connections` |

### 6. Indeks tangkapan layar (retest)

| Berkas | Isi |
|---|---|
| `live-retest-fe1-gmail-1280.png` | Kartu Gmail utuh di "Aplikasi lain" @1280 |
| `live-retest-fe1-gmail-375.png` | Kartu Gmail utuh @375 (tanpa overflow) |
| `live-retest-fe2-tier-1280.png` | Dialog Atur: 4 pilihan ketelitian, "Hemat & cepat" + "Seimbang" aktif |
| `live-retest-fe2-tier-saved-1280.png` | Kartu setelah simpan: "Tingkat ketelitian · Hemat & cepat" tanpa reload |
| `live-retest-fe2-seimbang-gagal-1280.png` | Bukti BE-11: banner merah "Model tidak valid" saat memilih Seimbang |
| `live-retest-fe3-warna-tersimpan-1280.png` | Bukti FE-3: warna + avatar toska tampil tanpa muat ulang |
| `live-retest-fe5-konfirmasi-batalkan-1280.png` | Tombol **Batalkan** merah (`btn danger`) di dialog "Yakin?" |
| `live-retest-nilai-dipulihkan-1280.png` | Keadaan akhir: "Biru langit" + "Ikuti bawaan" (semua nilai dipulihkan) |

---

## Uji setelah kunci akses

**Ringkasan**

- Dijalankan **25 November 2026, 01.37–01.53 WIB (24 Nov 2026, 18.37–18.53 UTC)** di aplikasi live
  `https://139.190.107.151.sslip.io/demo/`, **setelah** deploy rilis **`ebf0e72`** (lihat `audit-vps.md` §15):
  semua route `/api` wajib login, dan Nginx tidak lagi menyuntikkan `X-Pegawai-AI-Key`.
- Build yang dinilai: `assets/index-B4csrld4.js` (`38c94966…`), `assets/index-8hSpk8Z5.css` (`9023cf85…`),
  `index.html` (`323ea785…`) — ketiganya **byte-identik** dengan hasil `npm run build` lokal dari commit
  `ebf0e72`. Bundle lama `index-aDJo1iqq.js` sudah dihapus (404).
- Metode: Chromium headless (viewport 1706×960, `deviceScaleFactor 1`), sesi baru lewat form login; akun
  `admin@pegawai.ai` (peran `admin`) dan `cs@colorbox.co.id` (peran `cs`). Kata sandi demo diambil dari
  `bff/migrations/020_auth_users.sql` dan **tidak ditulis** di dokumen ini.
- **Sanitasi:** token disamarkan `<jwt>`; tidak ada kata sandi, token, atau kunci yang dicetak. Pesan uji
  yang dikirim ke agen: "Balas satu kata: oke" (admin) dan satu pertanyaan katalog untuk uji Telegram.
- **Verdict:** semua alur yang diuji **PASS**; satu penyimpangan rencana dicatat di §3 (rian sudah dihapus).

| # | Uji | Verdict |
|---|---|---|
| 1 | Sesi lama ditolak, login baru berhasil | **PASS** |
| 2 | Grup menu **Admin** langsung terlihat setelah login (tanpa mengubah Pengaturan) | **PASS** |
| 3 | Chat: riwayat termuat, kirim pesan → balasan, hapus topik | **PASS** (dengan catatan: rian sudah soft-delete sejak 18 Nov) |
| 4 | Keluar → login lagi → grup Admin tetap muncul | **PASS** |
| 5 | Akun staf: tanpa grup Admin, `#/agen` dialihkan ke Beranda | **PASS** |
| 6 | Telegram: balasan agen nyata (produk + harga + ukuran) | **PASS** (lihat §4) |
| 7 | Konsol & permintaan gagal selama uji | **PASS** (0 error konsol, 0 `requestfailed`) |
| 8 | Log server selama jendela uji | **PASS** (0 respons 5xx) |

### 1. Login dan tampilan sesi lama

Membuka `/demo/` tanpa sesi menampilkan form **Masuk** dengan banner kuning:

> Sesi Anda berakhir, silakan masuk lagi.

Ini perilaku yang diinginkan: token lama (ditandatangani `BFF_API_KEY`) ditolak `401`, frontend membersihkan
sesi dan menampilkan penjelasan yang tenang. Login `admin@pegawai.ai` → **200**, langsung masuk Beranda;
tidak ada 401 berulang di jaringan setelah token baru dipakai.
Bukti: `live-auth-01-login.png`.

### 2. Grup Admin langsung terlihat

Setelah login (tanpa membuka Pengaturan, tanpa mengubah sakelar apa pun) sidebar memuat grup **Admin**:
Marketing (formulir), Layanan pelanggan, Agen, Kemampuan, Evaluasi, Aktivitas — di samping tujuh menu biasa.
Tidak ada kedipan "memuat" yang menahan grup ini. Bukti: `live-auth-02-admin-langsung.png`.

### 3. Chat: riwayat, balasan, hapus topik

| Langkah | Hasil |
|---|---|
| Buka **Chat** | 7 pegawai aktif tampil (Siti, Hendra, Bimo, Meda, Raka, Bram, Vina); riwayat Siti termuat ("Belum ada percakapan dengan Siti."), tanpa "Menyambung ulang…" terus-menerus |
| Kirim "Balas satu kata: oke" ke Siti | pesan tampil; indikator bekerja/berpikir; balasan **"oke"** datang ±13 detik lewat SSE ber-Bearer |
| Riwayat | topik "Balas satu kata oke" muncul, waktu "baru saja" |
| Hapus topik | hover → tombol **Hapus topik** → dialog "Hapus topik “Balas satu kata oke”? Hanya topik ini yang dihapus…" → **Hapus topik**; setelah muat ulang riwayat kosong lagi |

Bukti: `live-auth-03-chat-balasan.png`, `live-auth-04-topik-dihapus.png`.

**Catatan rencana uji:** permintaan awal adalah mengirim pesan ke **rian**. `rian` (bersama `budi` dan
`diana`) sudah **soft-delete sejak 18 November 2026**, jadi tidak muncul di UI maupun `GET /api/bots`
(7 aktif dari 10 baris). Uji dialihkan ke **Siti**; tidak ada pegawai yang dipulihkan atau diubah untuk uji.

### 4. Telegram — agen nyata, bukan template

Uji tanpa akun Telegram nyata: satu panggilan terautentikasi `POST /api/telegram/simulate` (chat fiktif
`999888111`, `bot_id` `siti`) dengan pertanyaan
**"Berapa harga Hoodie terbaru dan ukurannya apa saja?"**. Waktu **37 detik**, `HTTP 200`,
`status: message_routed`, balasan **1.350 karakter**.

Kutipan balasan (dipotong; isi tidak diubah):

> Halo Kak, terima kasih sudah bertanya ya. Berikut item berjenis hoodie yang terlihat di katalog resmi
> Colorbox saat data kami diamati pada 9 November 2026:
> 1. Embroidered Long Sleeve Hoodie (Outerwear & Jackets), warna TAUPE — Rp 149.900 (harga sebelumnya
>    Rp 229.900), ukuran tertera L, M, S, XL
> 2. Long Sleeve Hoodie Cardigan (Knitwear & Sweaters), warna LT. BEIGE — Rp 249.900, ukuran tertera L, M, S, XL
> 3. Long Sleeve Hoodie Cardigan (Knitwear & Sweaters), warna GREY — Rp 249.900, ukuran tertera L, M, S, XL
> 4. Zipped Up Hoodie Knit Jacket (Knitwear & Sweaters), warna DARK GREEN — Rp 259.900, ukuran tertera L, M, S, XL
> … Sleeveless Ruched Top with Hoodie, warna PLUM — Rp 65.900 (harga sebelumnya Rp 99.900) dengan ukuran tertera L, M, S, XL …
> Colorbox x Liunic Oversized Sweatshirt — Rp 249.900 (promo Rp 239.900), ukuran S, M, L, XL …
> harga di atas adalah harga yang kami catat pada tanggal pengamatan dan bisa berubah.

Balasan memuat produk, harga, dan ukuran nyata dari katalog Colorbox — bukti run Hermes sungguhan lewat
`engine.chat_turn` (bukan balasan template kata kunci).

Pembersihan: sesi `tg-999888111-edcecc56` dihapus lewat API (`DELETE …/sessions/…` → **204**); baris
`telegram_chats` (tanpa endpoint API) dihapus dengan satu `DELETE` SQL. Setelah itu `chat_sessions` uji = 0
dan `telegram_chats` = 0. Pengiriman ke chat fiktif dijawab Telegram **400** (wajar) dan tidak memengaruhi run.

### 5. Admin setelah keluar-masuk, dan akun staf

| Skenario | Hasil |
|---|---|
| **Keluar** dari akun admin, login lagi | grup **Admin tetap muncul** tanpa mengubah Pengaturan — preferensi mode admin dibersihkan saat logout |
| Login `cs@colorbox.co.id` (staf) | sidebar hanya 7 menu biasa; **tidak ada grup Admin**, tidak ada sakelar "Mode admin" |
| Staf membuka `#/agen` | dialihkan ke `#/` (Beranda), bukan halaman kosong/error |

Bukti: `live-auth-05-staf-tanpa-admin.png`.

### 6. Konsol, jaringan, dan log server

| Aspek | Hasil |
|---|---|
| Konsol browser (login → Beranda → Chat) | **0 error**, 0 `pageerror` |
| Permintaan gagal (`requestfailed`) | **0** |
| Nginx access log, jendela 01.36–01.55 WIB | 200 ×140, 401 ×24 (uji tanpa token), 403 ×4 (registrasi & verify WA), 405 ×2 (GET webhook Telegram), 400 ×2 (JSON rusak & kirim Telegram ke chat fiktif), 204 ×2, 304 ×2, 202 ×1, 404 ×1 (bundle lama) — **0 respons 5xx** di seluruh `access.log` |
| Journal BFF sejak restart | bersih dari `traceback`/`exception`/`critical`; hanya baris `400 Bad Request` Telegram untuk chat uji fiktif |

### 7. Indeks tangkapan layar

| Berkas | Isi |
|---|---|
| `live-auth-01-login.png` | Form Masuk dengan banner "Sesi Anda berakhir, silakan masuk lagi." |
| `live-auth-02-admin-langsung.png` | Beranda admin: grup **Admin** sudah terlihat tanpa mengubah Pengaturan |
| `live-auth-03-chat-balasan.png` | Chat Siti: pesan uji, balasan "oke", riwayat "Balas satu kata oke" |
| `live-auth-04-topik-dihapus.png` | Setelah topik dihapus dan halaman dimuat ulang: "Belum ada percakapan dengan Siti." |
| `live-auth-05-staf-tanpa-admin.png` | Akun staf: sidebar tanpa grup Admin, berada di Beranda setelah `#/agen` dialihkan |

### 8. Yang tidak diuji di bagian ini

- Tidak ada akun Telegram nyata, WhatsApp nyata, OAuth, atau KB upload baru.
- Tidak ada perubahan pegawai, warna, model, tugas, atau sambungan.
- Satu-satunya tulisan data: satu topik chat uji (dihapus), sesi Telegram uji (dihapus), dan
  `users.token_version` yang naik karena login/logout verifikasi (disengaja; semua pengguna login sekali).

