# Telegram Native & Rencana UX Memori (Hari 4)

**Ringkasan**

- **Belum ada integrasi Telegram sama sekali** di repo: tidak ada route, webhook, env, migrasi, atau UI; `channel_directory.json` kosong dan `gateway_state.json` hanya berisi `api_server`. Karena itu **tidak ada sampel live**; semua temuan di bawah berasal dari kode Hermes terpasang `0.22.5+3201.ga4994d4` dan diberi label **UNTESTED terhadap Pegawai**.
- **Rekomendasi sementara: output native cukup** untuk teks, notifikasi, dan ringkasan tugas. Tabel pipa **otomatis berubah menjadi grup bullet** (`helpers.py:322`) — dapat diterima di chat. Lever ringan, jika tabel native benar-benar dibutuhkan, adalah **konfigurasi Backend** (`platforms.telegram.extra.rich_messages: true`, default `False` di `adapter.py:609`) plus perubahan hint prompt; **renderer kustom ditunda**.
- **Memori: rencana saja.** Yang tersedia hari ini hanya riwayat/hapus sesi dan sakelar toolset "Ingatan". Baca/kelola/hapus memori jangka panjang **belum punya endpoint**; lima lapisan adalah target arsitektur, bukan fitur bawaan Hermes.
- **Risiko utama:** memori Hermes terikat **profil**, bukan pengguna akhir. Selama satu profil dipakai beberapa anggota workspace, `session_search` dapat membuka sesi anggota lain (`tools/session_search_tool.py:601-628`). Opsi A/B/C untuk Backend ada di §8.

Path repo relatif terhadap root `pegawai-ai-backend`; path Hermes relatif terhadap `%LOCALAPPDATA%\hermes\hermes-agent`. Kode repo pada `feat/frontend-prototype` (HEAD `8d05aaf`).

---

## 1. Status verifikasi

| Aspek | Status |
|---|---|
| Sampel output Telegram live | **TIDAK ADA** — tidak ada bot/token/chat di sisi Pegawai |
| Analisis rendering | Dari kode + tes Hermes (bukan observasi live) — **UNTESTED** |
| Kandidat memori | Kajian dokumen/primary source — **UNTESTED** terhadap Pegawai |
| Kontrak memori BFF | Tidak ada (grep `memories\|MEMORY.md` di `bff/` = kosong) |
| Migrasi terakhir | `020_auth_users.sql`; tidak ada tabel memori |

Cara menutup gap: satu bot uji + satu chat uji dari Backend, lalu tangkap (a) balasan teks biasa, (b) balasan berisi tabel, (c) ringkasan tugas panjang. Redaksi ID chat/pengguna sebelum disimpan.

---

## 2. Rendering native Hermes → Telegram

| Konten | Jalur default (MarkdownV2) | `rich_messages: true` (opt-in) |
|---|---|---|
| Teks | bold/italic/strike/spoiler/code/link/header | Sama |
| Panjang pesan | Dipecah pada **4.096 karakter** (`adapter.py:525`) dengan penanda `(1/2)` | Batas rich lebih besar (32.768) |
| Tabel pipa | **Ditulis ulang menjadi judul tebal + grup `• Header: nilai`** (`helpers.py:299,322`) | Dikirim sebagai rich message; fallback otomatis bila ditolak klien |
| Task list / `<details>` / matematika | Terdegradasi/plain | Native |
| Output tugas panjang | Terpotong per 4.096 | Satu pesan lebih panjang |
| Berkas/gambar | `MEDIA:/path`, gambar sebagai foto | Sama |
| Panduan ke model | Hint sistem: utamakan bullet/baris berlabel, **hindari tabel** | Hint sama — tabel tetap jarang dipicu |

Catatan penting:

1. **Dokumentasi Hermes dan kode terpasang berbeda.** Dokumen menyebut tabel lebar jatuh ke blok kode dan ada flag `pretty_tables`; kode `0.22.5` **selalu** mengubah tabel menjadi bullet dan tidak punya flag tersebut. Keputusan harus mengutip **kode**, bukan dokumen.
2. `hermes send` memakai adapter gateway bila hidup (bisa rich), tetapi jatuh ke pengirim MarkdownV2 mandiri tanpa jalur rich bila tidak.
3. Konsekuensi untuk agen marketing: tabel kalender/storyboard yang lebar akan menjadi daftar bullet panjang, bukan tabel.

**Contoh bentuk yang diharapkan** (dari tes Hermes, bukan observasi): `| Pemain | Skor |` + baris → `**Alice**` / `• Skor: 150`, baris kosong, `**Bob**` / `• Skor: 120`.

---

## 3. Rekomendasi sementara

| Keputusan | Isi | Alasan |
|---|---|---|
| **Native cukup** | Teks, notifikasi, ringkasan tugas, balasan CS | Formatting dasar sudah baik; tidak ada biaya FE |
| **Tabel: terima degradasi** | Tabel menjadi grup bullet; kirim ringkasan pendek + berkas `.md` penuh atau tautan ke Kanban/detail | Menghindari renderer dan biaya perawatan; isi tetap lengkap |
| **Lever ringan (kondisional)** | `rich_messages: true` + hint prompt yang mengizinkan tabel + QA klien | Hanya jika tabel native menjadi kebutuhan produk; milik Backend, bukan FE |
| **Tunda** | Renderer HTML/kartu/gambar kustom, template per platform | Usaha tinggi, manfaat belum terbukti |

**Status: provisional.** Keputusan final menunggu sampel live (butuh token bot dari Backend). Selama itu, jangan menulis "Telegram sudah terintegrasi" di materi klien.

### 3.1 Mitigasi yang tidak butuh renderer

| Masalah | Mitigasi |
|---|---|
| Tabel panjang jadi sulit dibaca | Kebijakan pengiriman: ringkasan ≤ 10 baris di chat, detail sebagai berkas atau tautan |
| Pesan terpotong di tengah | Minta agen menutup dengan ringkasan; batasi output terjadwal |
| Data pelanggan di chat pribadi | Kebijakan kanal: hanya notifikasi status, bukan isi percakapan |

---

## 4. Kandidat memori (7) — semua UNTESTED

| Kandidat | Apa itu (sumber primer) | Integrasi di Hermes terpasang | Kecocokan UX/API | Scoping & izin | Retensi/hapus | Putusan UX |
|---|---|---|---|---|---|---|
| **Obsidian** | Aplikasi desktop vault Markdown lokal; catatan = berkas biasa ([penyimpanan](https://obsidian.md/help/data-storage), [lisensi](https://obsidian.md/license)) | **Tidak ada memory-provider.** Plugin komunitas hanya UI (browse/edit) | Familiar untuk pengguna teknis; tanpa API server, tanpa multi-user; sinkronisasi berbayar | Berbasis filesystem; tidak ada tenant | Hapus berkas; tanpa audit/undo | **Tolak sebagai mesin memori**; opsional target ekspor |
| **Hindsight** | Memori jangka panjang MIT dengan knowledge graph/entity resolution ([repo](https://github.com/vectorize-io/hindsight)) | Plugin katalog `hindsight.yaml`; 3 tool `retain/recall/reflect`; `bank_id` | "Reflect" menjelaskan sintesis; **tidak ada tool forget eksplisit** → cerita hapus lemah | Bank per konfigurasi/profil; bank per pengguna harus dibangun | `auto_retain` aktif; hapus di level bank (belum terverifikasi) | Recall kuat, **hapus lemah**; tunda |
| **memO → Mem0** | Lapisan memori Apache-2.0, ekstraksi fakta di server ([repo](https://github.com/mem0ai/mem0), [lisensi](https://github.com/mem0ai/mem0/blob/main/LICENSE)) | Plugin katalog `mem0.yaml` (tidak lagi di core); 4 tool termasuk `update`/`delete` per ID; telemetri PostHog aktif kecuali dimatikan | Cerita CRUD/hapus terbaik; `user_id` + `agent_id` kelas satu | Scoping `user_id` native; tetap butuh plumbing identitas BFF | Hapus per ID; hapus massal belum terdokumentasi | **Kandidat MVP terbaik untuk lapisan jangka panjang** |
| **Honcho** | Pemodelan pengguna peer/session, **AGPL-3.0** ([repo](https://github.com/plastic-labs/honcho), [lisensi](https://github.com/plastic-labs/honcho/blob/main/LICENSE)) | Plugin katalog `honcho.yaml`; 5 tool; pemetaan identitas hanya di gateway (`pinUserPeer`, alias) | Kartu profil + dialektika kuat, tetapi jargon berat untuk pengguna bisnis | Model peer paling matang, tetapi pemetaan **hanya gateway** (BFF memakai API server) | `honcho_conclude`; hapus peer belum jelas | Lisensi + kompleksitas; tunda |
| **OpenViking** | Basis konteks **AGPL-3.0**, hierarki `viking://` (Volcengine) ([repo](https://github.com/volcengine/OpenViking)) | Plugin katalog `openviking.yaml`; 6 tool termasuk `browse`, `read`, `forget` per URI | Metafora penjelajah berkas cocok untuk "lihat yang diingat agen"; butuh server | `OPENVIKING_ACCOUNT`/`USER`; isolasi per pengguna workspace tidak default | `viking_forget` per URI; massal belum jelas | Browse bagus, operasional berat + AGPL; tunda |
| **Cognee** | Memori knowledge-graph Apache-2.0 ([repo](https://github.com/topoteretes/cognee), [lisensi](https://github.com/topoteretes/cognee/blob/main/LICENSE)) | Plugin katalog komunitas; 6 tool termasuk `forget`, `switch_dataset`, `recap`; server lokal `127.0.0.1:8011`; **store `~/.cognee` dibagi antar profil**; data dikirim ke LLM ([dokumen](https://docs.cognee.ai/integrations/hermes-agent-integration)) | `switch_dataset` cocok untuk lapisan Proyek; `recap` berguna | Otak bersama + egress LLM bertentangan dengan isolasi per profil/tenant | `cognee_forget`; hapus dataset belum jelas | **Tunda** sampai ada store per tenant |
| **AgentMemory** | Server memori lokal Apache-2.0 untuk agen coding, viewer UI, MCP/REST/hooks ([dokumen](https://www.agent-memory.dev/docs), [panduan Hermes](https://www.agent-memory.dev/docs/integrations/hermes.md)) | Dokumen vendor mengklaim provider native **dan** entri katalog; katalog terpasang `0.22.5` **tidak punya `agentmemory.yaml`** (yang ada `agent_memory_es.yaml`, produk Elasticsearch berbeda) | **Viewer/browse terbaik out-of-box**; `memory_save/recall/search`; hapus per record | Scope profil + penulis turn, tetapi dokumen menyatakan filter **level aplikasi, bukan otorisasi**; MCP melewati filter | Hapus eksplisit; tanpa antrean offline | **Pilot untuk pelajaran viewer**; belum aman multi-tenant |

### 4.1 Catatan ambiguitas yang harus diselesaikan sebelum menulis rekomendasi final

1. **"memO" tidak ditemukan sebagai produk.** Diasumsikan **Mem0**; tulis asumsi ini di setiap dokumen agar tidak dianggap salah kutip. Konfirmasi ke Backend.
2. **"AgentMemory" ambigu** antara `agent-memory.dev` (di atas) dan `agent_memory_es` milik Hermes (Elasticsearch, visibilitas private/team/common). Keduanya berbeda; jangan mencampur fitur.
3. **Klaim katalog AgentMemory** berasal dari dokumen vendor; katalog terpasang tidak memuatnya. Jangan menjanjikan "bisa dipasang" tanpa cek ulang versi.
4. **"Obsidian tidak ada integrasi"** benar untuk *memory provider*, tetapi plugin komunitas untuk melihat/mengedit vault ada. Nyatakan batasnya.

---

## 5. Model mental memori untuk pengguna

### 5.1 Dua cakupan, dua kata kerja

| Cakupan | Kalimat UI (ID) | Isi | Kata kerja |
|---|---|---|---|
| **Sesi** | "Percakapan ini" | Transkrip + konteks satu percakapan | "Hapus percakapan" |
| **Jangka panjang** | "Yang diingat \<nama agen\>" | `MEMORY.md` (catatan agen, 2.200 karakter) + `USER.md` (profil pengguna, 1.375 karakter), level profil | "Lupakan / kosongkan ingatan" |

Aturan copy yang tidak boleh dilanggar:

1. Menghapus sesi **tidak** menghapus yang diingat agen — dan sebaliknya.
2. **Pengetahuan ≠ Memori.** Hari ini mengetik "ingat ini" + tautan diperlakukan sebagai **ingesti KB** (`frontend/src/kb-ui.tsx:17`), jadi pengguna sudah bingung. UI harus menyebut perbedaan ini secara eksplisit.
3. Sakelar "Ingatan" (`frontend/src/ui-extra.tsx:80`) hanya menyalakan/mematikan **toolset** `memory`; ia **tidak** menghapus memori yang sudah ada. Copy wajib mengatakan itu.
4. Perubahan yang disimpan berlaku pada **sesi berikutnya** (snapshot dibekukan saat sesi mulai, `memory.md:55-63`).

### 5.2 Lima lapisan (target arsitektur, bukan fitur bawaan)

| Lapisan | Arti target | Hermes native hari ini | Kode Pegawai hari ini | Perlakuan UX |
|---|---|---|---|---|
| 1 Sesi | Konteks percakapan aktif | Sesi + kompaksi; `session_search` FTS atas `state.db` | `chat_sessions` per pengguna; list/pesan/rename/hapus (`main.py:346-381`) | **Tersedia**: riwayat + hapus |
| 2 Karyawan | SOP/peran + catatan kerja yang dipelajari | `MEMORY.md` per profil; `SOUL.md`/persona | Profil per bot (`bots.py:140-205`); persona; sakelar toolset `memory` (`apps.py:291-355`) | **Sebagian**: lihat kapasitas/hapus = direncanakan; sakelar = tersedia |
| 3 Pelanggan/Tenant | Merek, kebijakan, fakta pelanggan | **Tidak ada** (satu `USER.md` per profil) | Bundel KB + produk; tidak ada tabel memori tenant | **Direncanakan**; label "Belum tersedia" |
| 4 Proyek | Status kampanye/kalender/tugas | **Tidak ada** (tugas ada di BFF) | `tasks`, jadwal, item KB | **Direncanakan**; tampilkan fakta proyek dari Kanban, read-only |
| 5 Jangka panjang | Pola/insight lintas proyek | **Tidak ada** selain `MEMORY.md` 2.200 karakter | **Tidak ada** (tanpa migrasi/endpoint) | **Direncanakan**; bergantung provider |

Catatan: hanya **satu** provider eksternal yang dapat aktif per profil (`memory-providers.md:9`), jadi mencampur provider per lapisan tidak mungkin.

### 5.3 Permukaan UI yang dipakai ulang (tanpa design system baru)

| Permukaan | Jangkar | Pemakaian |
|---|---|---|
| Bagian Pengaturan | `frontend/src/Settings.tsx:14-21` | Tambah bagian `memori`: default memori agen, status provider, copy retensi |
| Blok detail agen | `frontend/src/Agents.tsx:158-232` | Tambah kotak "Memori" setelah Persona: meter kapasitas (2.200/1.375), terakhir diubah, "Kelola" |
| Panel samping percakapan | `frontend/src/Panel.tsx:15,57-58,182-191` | Tambah tab `memori`: header "Percakapan ini" + aksi sesi; pertahankan Info/Biaya/Aktivitas |
| Konfirmasi hapus | `frontend/src/ChatLayout.tsx:374-386` | Pola konfirmasi dua langkah yang sudah ada dipakai untuk hapus destruktif |
| Sakelar kemampuan | `frontend/src/skills-ui.tsx:12-63` + `ui-extra.tsx:80` | Sudah menyalakan toolset `memory`; copy harus menyebut "tidak menghapus memori lama" |
| Aktivitas | `frontend/src/Activity.tsx:73-102`; `main.py:991-1011` | Filter `tool=memory` untuk menulis memori, per pengguna |
| Halaman Pengetahuan | `frontend/src/Pengetahuan.tsx:226`; `kb-ui.tsx:17` | Tautan silang "Pengetahuan ≠ Memori"; perbaiki tabrakan intent "ingat/hafal" |

### 5.4 Matriks operasi (tersedia vs direncanakan)

| Operasi | Cakupan | Status | Kontrak | Izin | Konfirmasi | Error |
|---|---|---|---|---|---|---|
| Lihat daftar/pesan sesi | Sesi | **Tersedia** | `GET /api/bots/{id}/sessions[/{sid}/messages]` (`main.py:346-362`) | Pemilik bot (`_owned_session`, `main.py:329-333`) | — | 404 sesi asing; 502 Hermes |
| Hapus sesi | Sesi | **Tersedia** | `DELETE /api/bots/{id}/sessions/{sid}` (`main.py:375-381`) | Pemilik | Konfirmasi inline dua langkah (`ChatLayout.tsx:374-386`) | 404, 502 |
| Nyalakan/matikan kemampuan ingatan | Karyawan | **Tersedia** | `PUT /api/agents/{slug}/skills {name:"memory"}` (`main.py:318-322`) | Pemilik agen | Langsung + toast; jelaskan "memori lama tetap ada" | 400 skill tersembunyi; 502 |
| Lihat isi memori jangka panjang | Karyawan | **Direncanakan** | Perlu `GET /api/agents/{slug}/memory`; Hermes hanya mengekspos **ukuran** berkas lewat dashboard (`hermes_cli/web_routers/ops.py:495-509`) | Pemilik/admin; wajib Bearer valid | — | 404, 502, 423 bila profil sibuk |
| Kosongkan satu store | Karyawan | **Direncanakan** | Perlu `DELETE …?store=memory\|user`; Hermes punya `memory reset --target` | **Hanya owner/admin** | Konfirmasi ketik + pratinjau cakupan (jumlah entri, karakter, nama agen) + ekspor dulu | 401/403/409/502; tidak boleh sukses sebagian diam-diam |
| Tambah/edit entri | Karyawan | **Ditunda** | Belum ada kontrak; tool `memory` hanya untuk agen | Owner/admin | Pratinjau diff | — |
| Kosongkan lapisan 3–5 | Pelanggan/Proyek/Jangka panjang | **Tidak tersedia** | Tidak ada | — | — | Tampilkan "Belum tersedia"; jangan tombol palsu |
| Pilih provider | Workspace | **Ditunda** | `hermes memory setup` per profil (CLI) | Admin | — | — |
| Ekspor | Semua | **Tersedia (chat)** | `GET /api/export/history` (`main.py:807`) | Pemilik | — | — |

**Aturan kejujuran UI:** setiap baris menampilkan badge **"Tersedia"** atau **"Direncanakan"**; tidak ada tombol nonaktif yang menyiratkan bug backend. Meter kapasitas menjelaskan kenapa agen "lupa" (error batas di `memory.md:185-203`).

### 5.5 Kebijakan izin dan konfirmasi

1. **Lihat:** pemilik agen; 404 untuk agen asing (`bots.py:59,65`).
2. **Kosongkan memori jangka panjang:** `owner`/`admin` workspace; anggota mendapat 403 dengan "Minta admin".
3. **Wajib autentikasi:** endpoint memori harus menolak token hilang/kedaluwarsa. Hari ini middleware jatuh ke `default` (`main.py:53-68`) — dapat diterima untuk route lama, **tidak** untuk operasi destruktif.
4. **Core vs editable:** SOUL/persona builtin read-only; entri memori editable. Jangan pernah mengekspos `.env`, kunci provider, atau berkas profil lain.
5. **Jangan aktifkan `memory.write_approval: true`** sebelum ada UI persetujuan: tulisan akan menggantung dan hanya bisa di-approve lewat CLI (`memory.md:332-347`), terlihat seperti "agen lupa".
6. **Kode error:** 409 bila run aktif, 502 bila Hermes mati, 429 untuk rate limit; error tidak boleh mengubah data.

---

## 6. Risiko isolasi tenant (red flags)

| # | Temuan | Bukti | Dampak |
|---|---|---|---|
| 1 | Lapisan sesi **sudah** user-scoped di BFF | `chat_sessions.user_id` + `_owned_session` (`main.py:329-333`); Activity memfilter `runs.user_id` (`main.py:1011`) | Baik — pertahankan |
| 2 | Memori karyawan **profil-scoped**, bukan user-scoped | `MEMORY.md`/`USER.md` di `profile_dir(bot)/memories`; body run hanya `input`, `session_id`, parameter model (`engine.py:161`) | Identitas pengguna akhir tidak pernah sampai ke memori Hermes |
| 3 | `session_search` dapat membaca **semua sesi dalam profil**; parameter `profile=` bahkan membuka profil lain (read-only) | `tools/session_search_tool.py:601-628` | Bila satu profil dipakai beberapa anggota, satu anggota dapat mengingat chat anggota lain |
| 4 | `memory` dan `session_search` sengaja **tidak** masuk deny-list hardening | `harden.py:27` (DENY tidak memuat keduanya) | Tool tetap tersedia di API server |
| 5 | Provider eksternal tidak memperbaiki ini di jalur BFF | `initialize()` menerima `user_id` hanya "bila ada" (`memory_provider.py:124-135`); `/v1/runs` tidak mengirimnya | Scoping per pengguna tidak otomatis |
| 6 | Lapisan 3–5 tanpa schema/API | Migrasi terakhir `020`; tidak ada tabel/endpoint/job memori | Harus dilabeli "Belum tersedia" |

**Kondisi saat ini menahan kebocoran:** bot adalah baris per pengguna (`bots.py:59,65`) dan profil dibuat per id bot, sehingga dua akun login **hari ini** tidak berbagi profil. Rancangan ini patah begitu "agen builtin milik workspace" dibagikan — langkah yang paling wajar berikutnya.

---

## 7. Opsi arsitektur untuk Backend (A/B/C)

| Opsi | Isi | Kelebihan | Kekurangan | Rekomendasi |
|---|---|---|---|---|
| **A** | Memori dimiliki BFF di Postgres, diambil per pengguna, disuntik lewat field `instructions` sebelum run (`engine.py:161` sudah mendukung) | Kontrol tenant penuh; ramah UI; purge saat akun dihapus; tidak butuh perubahan Hermes | Biaya token per run; memori internal Hermes tetap hanya level karyawan | **MVP yang disarankan** |
| **B** | Profil/gateway terpisah per `(workspace, user, bot)` | Isolasi kuat di level proses | Operasional berat (proses, port, kunci per pengguna); bertabrakan dengan "satu VPS" | Tunda; terkait "VPS terpisah per pengguna" yang sudah dinyatakan sprint berikutnya |
| **C** | Dukungan hulu Hermes untuk identitas pengguna akhir pada run API server, lalu scoping provider per pengguna (`user_id`/`bank_id`) | Paling bersih jangka panjang | Di luar kendali repo; menunggu hulu | Target jangka panjang |

**Postur aman sementara (tanpa menunggu keputusan):**

1. Pertahankan memori native hanya untuk fakta karyawan/workspace.
2. Tambahkan instruksi: "jangan simpan data pribadi pelanggan di memori".
3. Pertimbangkan mematikan `session_search` pada bot yang dipakai bersama.
4. Tandai lapisan 3–5 "Belum tersedia" di semua materi.

---

## 8. Dependensi dan langkah berikutnya

| ID | Pekerjaan | Pemilik | Prasyarat |
|---|---|---|---|
| T1 | Sampel output Telegram live (teks/tabel/tugas) + catatan keputusan final | Backend (token bot) → FE mencatat | Bot uji + chat uji |
| T2 | Terapkan kebijakan format (konfigurasi saja, tanpa renderer) | Backend | T1 |
| T3 | Kontrak memori: baca ukuran/isi, hapus per store, audit | Backend | Blueprint Hari 4 |
| T4 | Perbaikan copy sekarang: cakupan "Ingatan", KB ≠ Memori, teks hapus sesi | FE | Tidak ada |
| T5 | Keputusan isolasi tenant (A/B/C) | Backend/Sprint 6 | Dokumen ini |

**Yang tidak boleh diklaim selesai:** integrasi Telegram, UI memori penuh, lima lapisan memori, atau operasi hapus memori. Semuanya belum ada dan tidak menjadi gate sprint ini.

---

## 9. Rujukan

- Hermes terpasang: `plugins/platforms/telegram/adapter.py:525,609`; `gateway/platforms/helpers.py:288-352`; `tools/session_search_tool.py:601-628`; `website/docs/user-guide/features/memory.md:17-18,55-63,88,178-203,332-347`; `memory-providers.md:9`.
- Repo: `bff/bff/main.py:331-381,807,991-1011`; `bff/bff/bots.py:59,65,140-205`; `bff/bff/apps.py:291-355`; `bff/bff/harden.py:27`; `bff/bff/engine.py:161`; frontend `Settings.tsx`, `Agents.tsx`, `Panel.tsx`, `ChatLayout.tsx`, `skills-ui.tsx`, `ui-extra.tsx`, `Activity.tsx`, `Pengetahuan.tsx`, `kb-ui.tsx`.
- Sumber eksternal: tautan per kandidat di §4.
- ClickUp: Hari 4 `z8xxqwh79v`; induk `z8xxqwh792`. Backend Hari 4 (Telegram + blueprint memori) di `local://s5-others.md`.
