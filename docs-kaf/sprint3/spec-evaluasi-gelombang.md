# Spec: evaluasi Sprint 3, gelombang 1 dan 2 (11 November 2026)

Repo: `D:\Programming\AITopTrends-Hermes\pegawai-ai-backend`, branch `feat/evaluasi-sprint3`. Konteks: `todo-evaluasi.md`, `riset-kanban.md`, `kontrak-api-bff.md` (update kontrak bila menambah endpoint). Dokumentasi Hermes lokal (DOCS): `C:\Users\kevin\AppData\Local\hermes\hermes-agent\website\docs`; kode Hermes: `C:\Users\kevin\AppData\Local\hermes\hermes-agent`.

## Aturan tetap
- Frontend tidak pernah memanggil Hermes langsung; semua lewat BFF (`bff/bff/`), FastAPI, psycopg async, migrasi SQL berurutan di `bff/migrations/` (cek nomor terakhir).
- Jangan sentuh profil Hermes `coder`. Jangan baca atau cetak `.env` / key. Jangan jalankan `local_setup/setup_hermes_bots.py`.
- UI ikut gaya yang ada (achromatic ledger, `styles.css`, `pages.css`, `chat.css`): terang, DM Sans, satu aksen biru, tanpa gradien/glow, motion hanya feedback (opacity, tanpa bounce), teks UI Bahasa Indonesia, sesedikit mungkin opsi. Lint gaya: `node D:\Programming\AITopTrends-Hermes\.claude\skills\design-taste-frontend\scripts\lint.mjs --app src` (dari `frontend/`).
- Pemeriksaan wajib: `cd bff; uv run pytest -q` (sekarang 95 lulus, 6 deselected), `cd frontend; npx tsc -b; npm run build`.
- Layanan dev (sudah jalan): Postgres 5433, gateway Hermes 8642, BFF 8090 (`--loop asyncio:SelectorEventLoop`), Vite 5173. Restart BFF: `.\stop-dev.ps1` lalu `.\start-dev.ps1 -NoWait -NoBrowser` (stop-dev juga mematikan gateway; start-dev menyalakan lagi). Log di `.dev-logs\`.
- Commit di branch ini dengan pesan biasa; tanpa trailer Co-Authored-By atau sebutan Claude. Jangan push.
- Testing: web app diuji dengan menjalankan app di browser (atau Playwright CLI); selain itu pakai test suite yang ada atau perintah sekali jalan. Jangan buat file test sekali pakai atau redundan; test baru hanya untuk perilaku penting dan jadi bagian suite.

## A. Clarify (pertanyaan LLM jadi input) + hardening CLI untuk Kanban
1. `bff/bff/harden.py`:
   - Untuk `platform_toolsets.api_server`: tambahkan `clarify` (sekarang tidak ada; daftar sekarang web, vision, image_gen, skills, todo, memory, session_search, connections).
   - Juga keraskan `platform_toolsets.cli` dengan DENY yang sama (worker Kanban memakai platform `cli`: `gateway/session_kanban.py:69`). Bila `cli` belum diset, mulai dari toolset cli yang aktif sekarang (`hermes -p <bot> tools list --platform cli` atau endpoint yang setara) lalu buang DENY.
   - Perbarui docstring. Jalankan `uv run python -m bff.harden` untuk lima bot bawaan saja. Restart gateway bila config tidak terbaca ulang.
2. Pelajari bentuk event clarify dari Runs API (DOCS `user-guide/features/api-server.md` sekitar baris 640-680, `developer-guide/programmatic-integration.md:97`, dan kode `gateway/platforms/api_server.py`): nama event, field (`request_id`/`prompt_id`, `execution_generation`, pertanyaan, pilihan bila ada), dan body `POST /v1/runs/{id}/clarify`.
3. BFF (`engine.py`, tiru alur approval di `_handle` dan `approval()`): publikasikan event SSE `clarify` ke klien (pertanyaan, pilihan, request_id, execution_generation), simpan sebagai event run, endpoint `POST /api/runs/{id}/clarify` `{answer}` yang meneruskan ke Hermes. Event `snapshot` saat sambung ulang harus membawa clarify yang masih menunggu.
4. Frontend: kartu pertanyaan di chat (`Chat.tsx`/`LiveSteps.tsx`/`useRun.ts`) dan di workspace Marketing/CS (`ws-common.tsx` atau yang setara): teks pertanyaan, tombol pilihan bila ada, kotak jawaban bebas, tombol Kirim; hilang setelah dijawab. Tiru gaya kartu approval yang ada.
5. Uji di browser: kirim ke satu bot pesan yang memaksa bertanya (misal "Sebelum menjawab, tanyakan dulu ke saya lewat tool clarify warna favorit saya, lalu jawab"). Jawab lewat kartu, run selesai.

## B. Grup chat stream seperti chat
- `bff/bff/groups.py` `_turn`: teruskan event run tiap bot ke klien grup (delta teks, langkah/reasoning, tool, status), memakai hub/event yang sudah ada. Pesan final tetap disimpan seperti sekarang.
- `frontend/src/Group.tsx`: tampilkan pesan bot yang sedang ditulis dengan teks mengalir (`useSmoothText`) dan langkah (`LiveSteps`), seperti `Chat.tsx`. Indikator berpikir/menulis yang lama boleh diganti.
- Jangan ubah aturan giliran grup (2-6 bot, 3 ronde, `[SILENT]`, `@nama`).
- Uji di browser: kirim pesan di grup, teks bot muncul bertahap.

## C. Model dan reasoning per agen, navigasi, Pengaturan
1. Model per agen: migrasi baru, kolom di tabel bot: `model`, `provider`, `reasoning_effort` (nullable = ikut bawaan). `POST /v1/runs` mengirim `model`, `provider`, `model_options.reasoning_effort` bila diisi (DOCS `api-server.md:395-450`). Endpoint daftar model dari `/v1/models` (lihat `bots.py:194`). PATCH bot menerima ketiganya, dengan validasi effort: `none|minimal|low|medium|high|xhigh`.
2. Halaman edit agen (`Agents.tsx`): dua dropdown "Model" (opsi pertama "Bawaan") dan "Tingkat berpikir" (Bawaan, Rendah, Sedang, Tinggi; nilai lain di bawah "Lanjutan" hanya bila perlu).
3. Pengaturan ruang kerja: tabel `settings` (per user, key/value JSON atau kolom), `GET/PATCH /api/settings`. Agen baru dan agen tanpa model memakai bawaan dari settings.
4. Halaman `#/pengaturan` (`router.ts`, `App.tsx`, file baru `Settings.tsx`): daftar bagian di kiri (tab di layar kecil), isi di kanan, satu kalimat penjelasan per opsi.
   - Umum: nama perusahaan (bawaan "Colorbox"; dipakai di sidebar), bahasa (hanya Indonesia untuk sekarang, tampil tetapi nonaktif dengan keterangan), zona waktu (bawaan Asia/Jakarta), tema terang/gelap (pindahkan toggle dari sidebar ke sini).
   - Model AI: model dan tingkat berpikir bawaan.
   - Notifikasi: notifikasi browser untuk run selesai, butuh izin/pertanyaan, gagal (pakai mekanisme notifikasi yang sudah ada, simpan pilihan di settings).
   - Keamanan dan izin (hanya baca): toolset yang dimatikan dan mode persetujuan per bot, dari BFF (endpoint baca yang memakai data harden/gateway; jangan tampilkan key).
   - Knowledge base (hanya baca untuk sekarang): daftar dokumen yang dimuat `knowledge.py` (Colorbox Hub, CS v2.1) dengan versi dan tanggal; ganti dokumen belum.
   - Paket dan pemakaian: paket aktif, batas, pemakaian token bulan ini (data `plans`/usage yang ada).
   - Data: lama simpan log aktivitas (90 hari, tampil saja) dan ekspor riwayat chat sebagai JSON (endpoint BFF).
   - Kemampuan (Tools, Computer use, Scheduler) cukup ditautkan, jangan diduplikasi.
5. Sidebar: grup "Percakapan" (Beranda, Chat, Grup), grup "Workflow" (Marketing, CS), grup "Pengujian" (Uji, Aktivitas) tetap, grup "Pengaturan" (Agen, Kemampuan, Pengaturan).
6. Uji di browser: ubah model/effort satu agen dan pastikan run berikutnya mengirimnya (cek `runs.meta` atau log BFF); ubah tema dan nama perusahaan di Pengaturan; ekspor riwayat.
