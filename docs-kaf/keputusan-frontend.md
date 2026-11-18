# Keputusan Frontend Pegawai AI

Tanggal: 4 November 2026. Status: disepakati untuk dikerjakan bertahap. Sumber fakta: dokumentasi Hermes lokal di `%LOCALAPPDATA%\hermes\hermes-agent\website\docs` (singkatan DOCS).

## Prinsip

1. **Frontend tidak pernah memanggil Hermes langsung.** API Hermes memberi akses penuh ke tool, termasuk terminal (DOCS `user-guide/features/api-server.md:844`). Semua lewat backend atau proxy yang memegang key.
2. **Pakai yang sudah ada di Hermes, bangun hanya yang belum ada.**
3. **Batasan ditegakkan di backend atau konfigurasi Hermes, bukan di prompt.** SOUL.md hanya instruksi; toolset dan mode approval yang benar-benar memblokir.

## Arsitektur

```text
Frontend React (chat, riwayat, nanti kantor 3D)
   │
Backend kita: login, kuota, data tenant, penyimpanan run dan room
   │  key per bot, tidak pernah sampai ke browser
Hermes gateway: API server, multiplex per profil
   ├─ /p/rian/...   ├─ /p/diana/...   ├─ /p/siti/...  (satu profil = satu bot)
```

Fakta pendukung:

- Multiplex profil aktif secara default (DOCS `user-guide/multi-profile-gateways.md:101`).
- `/p/<profil>/` wajib memakai `API_SERVER_KEY` milik profil itu; profil tanpa key tertutup (DOCS `api-server.md:799-811`).
- Sesi milik Desktop/CLI tidak bisa dipakai lewat API (HTTP 409) (DOCS `api-server.md:500-512`). **Chat di web adalah sesi web sendiri**, terpisah dari chat Hermes Desktop.

## Keputusan per tahap

### Tahap 1: UI chat bot (dikerjakan sekarang)

| Fitur | Cara |
|---|---|
| Daftar bot | Lima bot tetap: Rian, Diana, Budi, Siti, Hendra |
| Chat streaming | `POST /p/<bot>/v1/chat/completions` dengan `stream: true` dan header `X-Hermes-Session-Id` |
| Proses berpikir, bisa ditampilkan atau disembunyikan | Field `reasoning_content` di stream yang sama (DOCS `api-server.md:222-227`). Stream chat sesi tidak mengirim reasoning, jadi tidak dipakai untuk ini |
| Riwayat chat seperti ChatGPT | `GET /p/<bot>/api/sessions` dan `GET .../api/sessions/{id}/messages`; ganti judul dengan `PATCH`, hapus dengan `DELETE` |
| Chat dengan bot: ringkasan atau sesi baru | Satu chat berlanjut per topik; Hermes memadatkan konteks otomatis. Tombol "Topik baru" membuat sesi baru. Tidak perlu ringkasan manual |
| Proxy | Untuk prototype lokal: proxy Vite yang menyisipkan key per bot dari `.env.local`. Untuk produksi: backend |

Syarat: API server Hermes dinyalakan di profil utama, dan setiap bot punya `API_SERVER_KEY` sendiri. Bot tidak menyalakan API server sendiri (DOCS `multi-profile-gateways.md:415-420`).

Uji awal tahap 1 (spike, sekali): pastikan reasoning DeepSeek benar-benar muncul, dan cek apakah stream ini juga membawa aktivitas tool. Bila tidak, aktivitas tool masuk tahap 2.

**Status 4 November 2026: selesai.** Uji awal lulus: reasoning terkirim lewat `reasoning_content`, aktivitas tool lewat event `hermes.tool.progress`, dan sesi tersimpan dengan judul otomatis. UI chat ada di `frontend/src/Chat.tsx`, `hermes.ts`, dan `chat.css`.

**Proses berpikir tidak per token (dicatat 4 November 2026).** Runs API (`/v1/runs`) tidak mengirim reasoning lewat stream-nya: gateway tidak memasang `reasoning_callback`, dan event `reasoning.available` ditekan bila model (DeepSeek) sudah mengirim reasoning bawaan. Hanya `/v1/chat/completions` yang mengalirkan `reasoning_content` langsung, tetapi run-nya tidak bisa dihentikan atau diarahkan. Kita memilih Runs API karena Stop dan Arahkan lebih penting. Akibatnya, berpikir tampil **per langkah**, bukan per kata: BFF membaca pesan sesi Hermes tiap 2 detik selama run, dan setiap pesan asisten baru ditampilkan di tab Berpikir. Untuk jawaban dengan alat, langkah pertama muncul sebelum alat selesai; langkah terakhir muncul bersama jawaban. Untuk jawaban tanpa alat, berpikir muncul saat jawaban selesai.

Keterbatasan: tombol Stop hanya menghentikan stream di browser. Giliran bot tetap berjalan di Hermes, dan sesi terkunci sekitar 20-40 detik (HTTP 409). Stop yang sesungguhnya memakai Runs API di tahap 2.

### Keputusan umum (dijawab 4 November 2026)

| Topik | Keputusan |
|---|---|
| Backend | Kita bangun backend sendiri (BFF) di `pegawai-ai-backend/bff/`: Python, FastAPI, uv, port 8090. `server.py` milik Intern 1 tidak diubah |
| Database | PostgreSQL 18 lokal |
| Login | Belum ada. Semua data memakai satu `user_id` bawaan supaya login bisa ditambah nanti tanpa ubah skema |
| Key Hermes | Pindah dari proxy Vite ke `.env` BFF. Browser hanya bicara ke BFF |
| Halaman "Tugas tim" | Dihapus. Kerja tim dilakukan lewat grup chat |
| Pertanyaan yang belum dijawab | Memakai praktik standar industri, dicatat di bawah |

### Tahap 2: kerja di latar belakang

- Pakai Runs API: `POST /v1/runs`, sambung ulang lewat `GET /v1/runs/{id}/events`, hentikan dengan `/stop` (DOCS `api-server.md:476-654`).
- Hermes tidak punya daftar run aktif dan buffer event hilang setelah 5 menit (DOCS `api-server.md:594-598`). Jadi **BFF yang membaca event** sampai run selesai dan menyimpannya di Postgres. Browser cukup menyambung ke BFF.
- Bot tetap bekerja saat halaman ditutup. Saat dibuka lagi, frontend mengambil status dan hasil dari BFF.
- Notifikasi: hanya di browser (Notification API, ditambah toast di dalam aplikasi).
- Penyimpanan: riwayat chat, run, dan transkrip grup disimpan tanpa batas waktu. Log aktivitas tool dihapus setelah 90 hari.
- Ringkasan otomatis: tidak perlu dibuat sendiri. Hermes memadatkan konteks sesi yang panjang. Judul sesi dibuat otomatis oleh Hermes; untuk grup, judul diambil dari pesan pertama.

### Tahap 3: diskusi antarbot

- Grup Bot Mode Hermes tidak punya API kirim pesan atau stream yang terdokumentasi (DOCS `developer-guide/gateway-internals.md:13-23`). Jadi **BFF yang menjalankan grup.**
- Setiap bot punya satu sesi Hermes per grup (`grup:<id>:<bot>`). Pada gilirannya, BFF hanya mengirim pesan grup yang belum dilihat bot itu. Riwayat lama tetap di sesi Hermes dan dipadatkan otomatis, jadi token tidak membengkak.
- Aturan mengikuti Hermes Desktop: 2-6 bot per grup, paling banyak 3 ronde dan 10 pesan bot per kiriman user, bot boleh menjawab `[SILENT]`, dan `@nama` memanggil bot tertentu.
- Anggota: bawaannya satu tim. Grup lintas tim boleh dibuat dengan memilih bot dari tim lain.
- Menyela saat bot masih bekerja:
  - **Antre** (bawaan): pesan user menunggu sampai ronde selesai, lalu diproses.
  - **Arahkan sekarang**: pesan dikirim ke bot yang sedang bekerja lewat fitur steer Hermes (`POST /v1/runs/{id}/steer`). Bot menerimanya setelah langkah tool yang sedang berjalan selesai, tanpa membuang kerjanya. Sisa giliran ronde itu dibatalkan, lalu ronde baru dimulai dari pesan user. Steer yang benar-benar memotong hanya ada di WebSocket Desktop, jadi tidak dipakai.
  - Di chat satu bot, cara kerjanya sama: antre atau steer.
- Batas token per kiriman bersifat opsional di paket: `group_send_token_budget` kosong (NULL) berarti tanpa batas, dan itu bawaan semua paket sejak 4 November 2026. Batas ronde (3) dan pesan bot (10) tetap berlaku; keduanya aturan Hermes Desktop dan sudah cukup menghentikan diskusi yang berputar. Bila batas token diisi, diskusi berhenti dengan pesan sistem saat tercapai. UI menampilkan "Tanpa batas" untuk batas kosong.

### Tahap 4: bot dan grup baru, dengan batas paket

- Dibangun lengkap dulu, lalu dipangkas bila perlu.
- Bot dibuat BFF dengan `hermes profile create`; tidak ada API pembuatan profil yang memakai key biasa (DOCS `developer-guide/gateway-internals.md:278-297`). User memilih template (Rian, Diana, Budi, Siti, Hendra) atau menulis peran dan kepribadian sendiri; BFF menyusun SOUL.md dan membuat key API khusus bot itu.
- Hermes hanya punya batas run bersamaan (`max_concurrent_runs`, default 10) dan batas per giliran, tanpa kuota token per user (DOCS `api-server.md:856-859`). **Kuota dibangun di BFF** dari `usage` setiap run (DOCS `api-server.md:526-531`).
- Paket contoh: Gratis, Pro, Bisnis. Batasnya: jumlah bot, jumlah grup, token per bulan, run bersamaan, dan token per kiriman grup. Angkanya disimpan di tabel, jadi mudah diubah. Batas kosong (NULL) berarti tanpa batas: paket Bisnis tidak punya batas token bulanan (4 November 2026), sedangkan Gratis dan Pro tetap memakai angkanya.
- Saat kuota habis, permintaan ditolak dengan pesan yang jelas dan ajakan naik paket. Pembayaran belum dibangun.
- Frontend: tombol tambah bot dan tambah grup di sidebar, serta sisa kuota paket.
- Panel samping (4 November 2026, `docs/spec-panel-samping.md`): di header chat bot dan grup ada deretan ikon Berpikir, Token, Aktivitas, dan Info. Tab Token memakai `GET /api/usage` (total, per agen, daftar giliran) dan `GET /api/usage/bots` (per bot bulan ini). Grup bisa dihapus dari tab Info ("Hapus grup", dengan konfirmasi).

### Tahap 5: halaman log aktivitas

- Bot untuk pelanggan **dilarang memakai terminal**: toolset terminal, file, eksekusi kode, browser, computer use, cronjob, dan delegation dimatikan (bot pelanggan tidak boleh menjadwalkan tugas atau memanggil sub-agent yang terus bekerja setelah disuruh berhenti) di konfigurasi profil. Larangan ini ditegakkan di konfigurasi, bukan di prompt.
- Halaman hanya menampilkan log aktivitas tool dari event Runs API: nama tool, waktu, status, durasi, dan ringkasan.
- Sensor standar sebelum disimpan: pola key dan token, email, nomor telepon, dan path lokal. Isi panjang dipotong sampai 2 KB.

### Tahap 6: kantor 3D

**Status 4 November 2026: ditunda.** Ruang ternyata dijalankan lewat WSL2, jadi tahap ini dibatalkan dulu. Catatan di bawah disimpan untuk nanti; riset ada di `docs/riset/ruang.md`. Endpoint `GET /api/office` di BFF sudah ada dan bisa dipakai saat tahap ini dilanjutkan.

- Halaman sendiri, "Kantor".
- Memakai kode Ruang dulu (MIT, React + Vite + React Three Fiber), dengan atribusi lisensi. Nanti bisa diganti buatan sendiri.
- Data status bot (diam, bekerja, berdiskusi) dan isi percakapan grup diambil dari BFF, bukan dari CLI Hermes seperti Ruang. Isi percakapan muncul sebagai balon kata di atas bot.
- Hanya untuk laptop dan PC. Di layar kecil, halaman menampilkan daftar status bot sebagai pengganti.
- Catatan untuk versi mobile nanti: render 3D hanya saat diminta, model berpoligon rendah, batasi pixel ratio ke 1, matikan bayangan, dan jeda render saat tab tidak terlihat.

## Bukan keputusan frontend (untuk Intern 1 dan mentor)

| Topik | Fakta | Usulan |
|---|---|---|
| Bot tetap bekerja padahal dilarang | SOUL.md hanya instruksi prompt | Matikan toolset yang dilarang per profil dan pakai approval `manual`; jangan andalkan prompt |
| Kuota token per user | Tidak ada di Hermes | Simpan `usage` per run di backend, tolak run saat kuota habis |
| Pemisahan banyak user | Dokumentasi memakai satu profil per user dengan port dan key sendiri (DOCS `api-server.md:906-933`) | Perlu dibahas: profil per tenant di satu gateway, atau gateway terpisah per tenant (VPS) |

## Yang sengaja tidak dipakai

- **Hermes Webapp sebagai UI produk.** Pengguna yang masuk bisa menjalankan perintah sebagai akun sistem (DOCS `user-guide/desktop.md:93-97`). Cocok untuk admin internal saja.
- **WebSocket internal Desktop** (`groups.*`, `prompt.submit`). Parameternya tidak didokumentasikan stabil.
