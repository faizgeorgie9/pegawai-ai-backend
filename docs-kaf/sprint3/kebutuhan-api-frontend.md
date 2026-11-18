# Kebutuhan API Frontend: API Contract v1 (sisi frontend)

Tanggal: 7 November 2026. Daftar untuk disepakati dengan backend (Faiz). Ini permintaan dari frontend, bukan desain backend: bentuk internal, tabel, dan cara Hermes dipanggil sepenuhnya urusan backend.

Aturan baca:

- **Ada** = sudah disediakan BFF prototipe (`docs/bff-spec.md` bagian 5), dengan endpointnya.
- **Perlu disepakati** = belum ada. Semua yang ditandai **Usulan** hanyalah usulan bentuk dari frontend; tidak ada jaminan backend mendukungnya.
- Semua lewat `/bff/api/...` (proxy Vite menambah kunci). Tanpa login: pengguna tunggal.

## 0. Konvensi umum

**Bentuk error (ada):** HTTP status yang tepat dan body JSON dalam bahasa Indonesia.

```json
{ "error": "Terlalu banyak tugas berjalan, coba sebentar lagi" }
```

`402` juga membawa `"upgrade": true` di BFF saat ini; UI Sprint 3 tidak menampilkan paket, jadi hanya `error` yang dipakai. Status yang UI tangani: 401, 402, 404, 409, 429, 5xx (`bff.ts`, `fallbackMessage`).

**Usulan untuk endpoint baru:** tambahkan `code` yang stabil agar UI tidak membaca teks.

```json
{ "error": "Fitur ini dimatikan oleh server.", "code": "capability_blocked" }
```

**Status kapabilitas (usulan):** semua fitur yang bisa diblokir mengembalikan satu bentuk status.

```json
{ "status": "working | mock | unsupported | blocked", "reason": "Diblokir oleh keputusan backend (hardening)" }
```

**Pengenal:** `bot.id` = nama profil Hermes (string); `session_id` string (`web-<uuid>`); `run.id` uuid; `group.id` uuid.

**Label data (usulan, untuk Marketing dan CS):** `classification` salah satu dari `public_data`, `research_findings`, `assumptions`, `dummy`.

## 1. Agen

| Operasi | Endpoint | Status |
|---|---|---|
| Daftar | `GET /api/bots` | Ada |
| Detail | `GET /api/bots/{id}` | Perlu disepakati (sekarang detail diambil dari daftar) |
| Buat | `POST /api/bots` | Ada |
| Ubah | `PATCH /api/bots/{id}` | Perlu disepakati. **Usulan.** Belum ada API update |
| Hapus | `DELETE /api/bots/{id}` | Ada |
| Template | `GET /api/templates` | Ada |

Respons daftar/detail (ada):

```json
{ "id": "rian", "name": "Rian", "role": "Copywriter", "team": "marketing", "color": "raspberry",
  "builtin": true, "about": "Ringkasan persona maks 280 karakter", "status": "idle", "activity": "" }
```

`status`: `idle | working | discussing`. Status teks UI ("Sedang berpikir", "Menunggu izin") diturunkan dari stream run, bukan dari field ini.

Buat (ada), dua bentuk:

```json
{ "name": "Dewi", "role": "Analis data", "team": "marketing", "color": "teal", "template": "rian" }
{ "name": "Dewi", "role": "Analis data", "team": "marketing", "persona": "Teks persona maks 2000 karakter" }
```

Respons: 201 dengan agen. Error: 400/422 validasi (nama kosong atau slug kosong), 402/409 (batas atau nama bentrok), 5xx. Catatan: sekitar 33 detik end to end menurut spek; UI menampilkan "Membuat agen..." tanpa kemajuan palsu. Usulan agar UI tidak menunggu satu request: `202` + `status: "creating"` lalu polling `GET /api/bots/{id}`.

Ubah (**usulan**):

```json
PATCH /api/bots/{id}
{ "name": "Dewi", "role": "Analis data", "persona": "..." }
```

Respons: agen terbaru. Error: `409` bila ada run aktif; `403` bila `builtin` dan kolom itu tidak boleh diubah. Backend yang memutuskan kolom mana yang boleh diubah.

Hapus (ada): `DELETE /api/bots/{id}`, 204. Ditolak saat ada run aktif (error 409) dan untuk agen bawaan.

## 2. Chat

| Operasi | Endpoint | Status |
|---|---|---|
| Kirim | `POST /api/bots/{id}/runs` | Ada |
| Stream | `GET /api/runs/{id}/stream` (SSE) | Ada |
| Hentikan | `POST /api/runs/{id}/stop` | Ada |
| Arahkan (steer) | `POST /api/runs/{id}/steer` | Ada |
| Izin | `POST /api/runs/{id}/approval` | Ada |
| Daftar sesi (riwayat) | `GET /api/bots/{id}/sessions` | Ada |
| Pesan sesi | `GET /api/bots/{id}/sessions/{sid}/messages` | Ada |
| Ganti judul / hapus sesi | `PATCH`/`DELETE /api/bots/{id}/sessions/{sid}` | Ada |
| Berpikir per run | `GET /api/thinking?session_id=` | Ada |
| Pemakaian token | `GET /api/usage?session_id=` | Ada |
| Reset (sesi baru) | Lihat di bawah | Ada (tanpa endpoint khusus) |

Kirim (ada):

```json
POST /api/bots/rian/runs
{ "input": "Buat caption untuk kaos baru", "session_id": "web-3f2a..." }
```

`session_id` boleh dihilangkan; BFF membuat `web-<uuid>`. Respons `202`:

```json
{ "run": { "id": "uuid", "bot_id": "rian", "status": "running" }, "session_id": "web-3f2a..." }
```

Event stream (ada): `snapshot`, `delta {text}`, `reasoning {text, step}`, `tool {event, tool, preview, duration, error}`, `approval {request_id, description, choices}`, `status {status}`, `done {status, output, reasoning, usage}`.

Steer (ada): `{ "text": "..." }`. Error `409` dengan pesan "Bot sudah selesai, pesan dikirim sebagai pesan baru": UI mengirim ulang sebagai pesan baru.

Error umum: `429` terlalu banyak run; `402` batas habis; `404` run atau sesi tidak ditemukan.

**Reset:** tidak ada endpoint. Reset = kirim berikutnya tanpa `session_id`; sesi lama tetap tersimpan dan tidak dihapus. Perlu disepakati hanya jika backend ingin sesi kosong dibuat tanpa pesan pertama (**usulan**: `POST /api/bots/{id}/sessions` mengembalikan `{ "session_id": "web-..." }`).

Keamanan ganti agen (kebutuhan frontend, **usulan**): setiap event stream dan pesan membawa `bot_id` dan `session_id` agar UI bisa menolak hasil yang bukan milik layar saat ini. Event `snapshot`/`done` di BFF sekarang sudah dipetakan lewat `run.id`; `bot_id` pada setiap event perlu dikonfirmasi.

## 3. Tools dan penugasan per agen

Semuanya **perlu disepakati**; tidak ada di bagian 5 spek BFF. Fakta yang kita tahu: Hermes mempunyai `GET /p/<bot>/v1/toolsets` (dipakai `bff.harden`); aktif `web, vision, image_gen, skills, todo, memory, session_search, connections`.

| Operasi | Endpoint (usulan) |
|---|---|
| Registri toolset | `GET /api/tools` |
| Tool per agen | `GET /api/bots/{id}/tools` |
| Tugaskan/lepas tool | `PUT /api/bots/{id}/tools` (hanya jika backend mengizinkan; kalau tidak, UI hanya menampilkan) |

Respons `GET /api/tools` (usulan):

```json
{ "tools": [
  { "id": "web", "label": "Pencarian web", "status": "working", "reason": "" },
  { "id": "computer_use", "label": "Computer Use", "status": "blocked", "reason": "Dimatikan hardening" },
  { "id": "terminal", "label": "Terminal", "status": "blocked", "reason": "Dimatikan hardening" }
] }
```

`GET /api/bots/{id}/tools` (usulan): `{ "enabled": ["web","vision"], "available": ["..."] }`.
Error: `404` agen tidak ada; `409` tidak boleh diubah; `403` toolset diblokir.

## 4. Status koneksi

`connections` adalah toolset Hermes yang aktif. Frontend butuh status koneksi per layanan untuk chip di halaman Tools. Belum ada endpoint: **perlu disepakati**.

```json
GET /api/connections   (usulan)
{ "connections": [ { "id": "instagram", "label": "Instagram", "state": "not_connected | connected | error | blocked", "reason": "Di luar lingkup Sprint 3" } ] }
```

Catatan: Shopee dan Instagram langsung di luar lingkup; entri itu harus tampil `blocked`/tidak terhubung, bukan palsu tersambung. Status kesehatan umum sudah ada: `GET /api/health` -> `{ ok, db, hermes }`.

## 5. Computer Use: run dan aktivitas

Status: **Diblokir** (`computer_use` dimatikan hardening). Semua di bawah **perlu disepakati**, dan hanya relevan jika backend memutuskan membukanya. Tidak boleh ada aksi eksternal.

| Operasi | Endpoint (usulan) |
|---|---|
| Status kapabilitas | `GET /api/computer-use/status` |
| Buat tugas | `POST /api/computer-use/runs` |
| Daftar run | `GET /api/computer-use/runs` |
| Detail + aktivitas | `GET /api/computer-use/runs/{id}` |
| Hentikan | `POST /api/computer-use/runs/{id}/stop` |

```json
GET /api/computer-use/status
{ "status": "blocked", "reason": "Dimatikan oleh keputusan backend" }

POST /api/computer-use/runs   (hanya jika status working)
{ "bot_id": "rian", "task": "Buka halaman produk dan catat harganya" }
-> 202 { "id": "uuid", "status": "queued" }

GET /api/computer-use/runs/{id}
{ "id": "uuid", "status": "running", "steps": [ { "time": 1730000000, "action": "buka halaman", "preview": "..." } ] }
```

Error saat diblokir: `403` dengan `{ "error": "...", "code": "capability_blocked" }`. UI Diblokir tidak memanggil endpoint buat.

## 6. Scheduler

Status: **Diblokir** (`cronjob` dimatikan). **Perlu disepakati** dan hanya jika dibuka.

| Operasi | Endpoint (usulan) |
|---|---|
| Status | `GET /api/scheduler/status` |
| Daftar job | `GET /api/scheduler/jobs` |
| Buat | `POST /api/scheduler/jobs` |
| Jeda/lanjut | `PATCH /api/scheduler/jobs/{id}` |
| Hapus | `DELETE /api/scheduler/jobs/{id}` |

```json
POST /api/scheduler/jobs
{ "bot_id": "rian", "name": "Ringkasan mingguan", "schedule": "Sen 08.00", "input": "..." }
-> 201 { "id": "uuid", "status": "active", "next_run": 1730000000 }
```

Job tidak boleh mengirim pesan atau memposting keluar. Daftar kosong: `{ "jobs": [] }`.

## 7. Aktivitas

| Operasi | Endpoint | Status |
|---|---|---|
| Daftar | `GET /api/activity?bot=&status=&session_id=&group_id=&limit=100&before=` | Ada |
| Run aktif/terbaru | `GET /api/runs?status=active\|recent&limit=` | Ada |
| Event global (SSE) | `GET /api/events` | Ada |
| Filter jenis (tool/computer_use/scheduler) | `&kind=` | Perlu disepakati (usulan) |

Baris (ada): waktu, agen, tool, status `ok|error`, durasi, `preview` tersensor, id run, nama chat atau grup. Pratinjau sudah disensor di BFF (bagian 7 spek).

## 8. Hasil terstruktur Marketing

Menunggu backend. Semua **perlu disepakati**. Isi dan aturan konten milik Marketing (Ivanagita); frontend hanya meminta bentuk yang bisa dirender sebagai kartu. Usulan: hasil terstruktur datang sebagai bagian dari pesan asisten (di dalam event `done` atau `GET .../messages`) sebagai `structured`, di samping teks bebas.

```json
{
  "type": "marketing.draft",
  "schema_version": "1",
  "id": "OUT-0012", "brief_id": "BR-0003", "version": 2,
  "stage": "generation",
  "content_type": "instagram_caption",
  "classification": "assumptions",
  "fields": { "text": "...", "cta": "...", "hashtags": ["..."] },
  "sources": [ { "ref": "colorbox.co.id/...", "checked_at": "2026-11-06", "classification": "public_data" } ],
  "warnings": [ { "level": "warn", "text": "Klaim harga belum diverifikasi" } ],
  "review_status": "needs_review"
}
```

Jenis `type` yang dibutuhkan UI (usulan): `marketing.brief` (dengan `ready`, `assumptions`, `open_questions`), `marketing.plan` (creative brief, ide, kalender), `marketing.draft` (per `content_type`), `marketing.review` (temuan, bukti, rekomendasi, skor rubrik), `marketing.revision` (`before`, `after`, `feedback_applied`, `change_log`, `open_issues`).

Operasi pendukung (usulan):

| Operasi | Endpoint |
|---|---|
| Daftar brief | `GET /api/marketing/briefs` |
| Simpan brief | `POST /api/marketing/briefs` |
| Hasil per brief | `GET /api/marketing/briefs/{id}/outputs` |
| Ubah status review | `PATCH /api/marketing/outputs/{id}` `{ "review_status": "approved" }` |
| Log eksperimen | `GET/POST /api/marketing/experiments` |
| Skor rubrik | `POST /api/marketing/outputs/{id}/rubric` `{ "scores": { "accuracy": 4, ... }, "reviewer": "...", "critical_failure": false }` |

Error: `422` bila `structured` gagal validasi skema (UI menampilkan teks bebas dengan baris "Hasil tidak bisa ditampilkan sebagai kartu"); `404`.

Alternatif yang lebih murah (jika backend belum mau menyimpan apa pun): hasil hanya di pesan chat, riwayat prototipe sudah cukup; endpoint daftar brief, log, dan rubrik ditunda dan UI menyimpan di sesi saja. Perlu diputuskan bersama.

## 9. Hasil terstruktur CS

Menunggu requirement CS (Mansi) dan backend. Semua **perlu disepakati**, dan bentuk di bawah hanya dugaan.

```json
{
  "type": "cs.ticket",
  "schema_version": "1",
  "inquiry": { "text": "...", "channel": "chat" },
  "classification": "return",
  "sources": [ { "ref": "kebijakan-retur", "excerpt": "...", "classification": "dummy" } ],
  "draft": "Teks balasan berbasis sumber",
  "context": [ { "turn": 1, "summary": "..." } ],
  "summary": "Ringkasan tiket",
  "priority": "normal | high | urgent",
  "escalation": { "recommended": true, "reason": "..." },
  "simulated": true
}
```

`simulated: true` wajib untuk kasus pesanan, retur, dan refund; UI menampilkan label "Simulasi". Tidak ada endpoint pengiriman ke pelanggan (di luar lingkup). Error sama dengan bagian 8.

## 10. Hal yang kita minta secara umum dari backend

1. Tiap event dan pesan membawa `bot_id` + `session_id` (keamanan ganti agen).
2. Satu bentuk status kapabilitas (`working | mock | unsupported | blocked` + `reason`).
3. Keputusan: apakah `computer_use` dan `cronjob` akan dibuka; sampai itu UI menampilkan Diblokir.
4. Keputusan: ada atau tidaknya API ubah agen.
5. Keputusan: format hasil terstruktur (di dalam pesan atau endpoint terpisah).
6. Konfirmasi bahwa 402 tidak lagi menjadi bagian alur UI (kartu Paket dihapus dari tampilan).

## 11. Skema hasil terstruktur (usulan frontend, perlu disepakati)

Status: **usulan frontend**, dipakai sekarang oleh prototipe supaya hasil bisa tampil sebagai kartu dengan eksekusi Hermes yang nyata. Backend (Faiz) belum punya API hasil terstruktur resmi, dan bagian 8 dan 9 di atas tetap menjadi permintaan resminya. Skema ini bukan pengganti; ini jembatan yang bisa dibuang saat API resmi ada.

**Cara kerja (sementara).** Mode terstruktur (eksperimen), aktif secara default dengan label terlihat. Frontend mengirim run dengan `instructions` (field opsional di `POST /api/bots/{id}/runs`, maksimal 6000 karakter, diteruskan BFF ke Hermes `POST /v1/runs`) yang meminta agen menambahkan satu blok ` ```pegawai-result ` berisi JSON di akhir jawaban biasa. Frontend mengurai blok itu dan menyembunyikannya dari jawaban. Kartu membawa lencana "Hasil agen · belum divalidasi backend". Jika blok tidak ada atau tidak lolos pemeriksaan tipe, frontend menampilkan jawaban teks apa adanya dengan catatan "Format terstruktur tidak terbaca"; kartu tidak pernah dibuat-buat. Kode: `frontend/src/results.ts` (tipe, guard, pengurai, teks instruksi).

Klasifikasi data (`classification`): `public_data`, `research_findings`, `assumptions`, `dummy`. Kasus pesanan, retur, dan refund selalu tampil "Simulasi".

**Marketing**, `kind` salah satu dari `brief | plan | content | review | revision`:

```json
{ "kind": "brief", "fields": { "tujuan": "", "produk": "", "kanal": "" }, "assumptions": [""], "questions": [""], "ready": true }
{ "kind": "plan", "creative_brief": "", "ideas": [ { "title": "", "reason": "", "classification": "assumptions" } ],
  "calendar": [ { "date": "", "channel": "", "type": "", "idea": "", "message": "", "cta": "" } ] }
{ "kind": "content", "type": "caption", "items": [ { "text": "", "alt_angle": "", "classification": "assumptions" } ],
  "sources": [""], "assumptions": [""], "warnings": [""] }
{ "kind": "review", "findings": [""], "evidence": [""], "recommendations": [""],
  "scores": { "accuracy": 4, "relevance": 4, "brand": 3, "consistency": 4, "knowledge": 4, "instruction": 5, "completeness": 4, "error_handling": 4, "human_review": 4 } }
{ "kind": "revision", "before": "", "after": "", "feedback_applied": [""], "change_log": [""], "open_issues": [""] }
```

Skor rubrik: 9 dimensi, bilangan bulat 1 sampai 5. Ambang usulan: minimal 4 di setiap dimensi dan tanpa kegagalan kritis; UI hanya menandai, reviewer yang memutuskan.

**CS** (menunggu requirement Mansi; bentuk bisa berubah):

```json
{ "kind": "cs", "inquiry": "", "classification": "jenis pertanyaan", "sources": [ { "ref": "", "excerpt": "" } ],
  "draft": "", "context_notes": "", "summary": "", "priority": "rendah | sedang | tinggi",
  "escalate": false, "escalation_reason": "", "simulated": false }
```

Catatan bentuk: guard memaafkan string di tempat daftar dan sebaliknya (model sering melakukannya), tetapi kolom wajib per jenis harus ada (brief: `fields`, `ready`; plan: `creative_brief`, `ideas`, `calendar`; content: `items`; review: `scores`; revision: `before`, `after`; cs: `draft`, `escalate`, `priority`). Tanpa itu hasil dianggap tidak terbaca.

**Penyimpanan evaluasi (ada di BFF prototipe).** Migrasi `003_evaluations.sql`; `GET/POST /api/evaluations`, `PATCH /api/evaluations/{id}`. Isi: `case_id`, `bot_id`, `session_id`, `run_id`, `prompt`, `expected`, `actual`, `scores` (per dimensi `{score: 1..5 | null, reason}`; null/N/A wajib beralasan), `verdict` (`pass | fail | blocked`), `notes` (`errors`, `improvements`, `critical`, `reviewed_on`), `reviewer`, `created_at`. Kesalahan validasi: 400 dengan pesan bahasa Indonesia. Matriks uji Marketing TC-01 sampai TC-11 di UI ditulis frontend dari tahap dan tipe konten requirement v1.1 (berkas konteks hanya menyebut ID); minta Ivanagita mengonfirmasi deskripsi tiap TC.
