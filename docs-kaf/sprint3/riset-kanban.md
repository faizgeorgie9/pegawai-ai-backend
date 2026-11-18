# Riset: Kanban Hermes (11 November 2026)

Sumber: dokumentasi dan kode Hermes lokal di `%LOCALAPPDATA%\hermes\hermes-agent` (DOCS = `website\docs`). Belum diuji langsung.

## Kesimpulan
Kanban cocok sebagai mesin untuk papan "Tugas tim" dan rantai kerja antaragen (brief → draf → review), karena sudah punya antrean permanen, retry, dan worker per profil. Tetapi **tidak bisa diakses lewat API gateway 8642** yang dipakai BFF sekarang, dan dukungan Windows belum terdokumentasi.

**Rekomendasi:** uji coba kecil dulu (spike) di mesin ini: BFF memanggil `hermes kanban ... --json` (CLI) untuk membuat dan membaca tugas. Pindah ke REST dashboard hanya setelah auth-nya jelas. Jangan membaca `kanban.db` langsung.

## Apa itu
- Papan tugas SQLite yang dipakai bersama semua profil: `~/.hermes/kanban.db`, atau satu file per papan di `kanban/boards/<slug>/`. DOCS `user-guide/features/kanban.md:11, 126-151`.
- Tugas: judul, isi, satu assignee (nama profil), status, prioritas, skill, model override, `max_retries`, idempotency key. Status: `triage | todo | ready | running | blocked | review | done | archived`. DOCS `kanban.md:131`.
- Tugas bisa berantai (parent → child): child naik ke `ready` setelah parent selesai. DOCS `kanban.md:132`.
- Dispatcher jalan di dalam gateway, tiap 60 detik: memulihkan worker macet dan menjalankan `hermes -p <assignee> chat -q <prompt>`. DOCS `kanban.md:138, 320-325`; `kanban-worker-lanes.md:33-45`.
- Gagal berulang → otomatis `blocked` (`kanban.failure_limit`, bawaan 2). DOCS `kanban.md:138`.
- Worker menutup tugas dengan `kanban_complete`, `kanban_request_review`, atau `kanban_block`. DOCS `kanban.md:568-575`.

## Cara akses
| Jalur | Status |
|---|---|
| API gateway 8642 (yang dipakai BFF) | **Tidak ada** route Kanban (`gateway/platforms/api_server.py`: 0 kecocokan "kanban") |
| CLI `hermes kanban ...` | Ada, beberapa perintah punya `--json`. DOCS `kanban.md:941-1003` |
| REST dashboard (bawaan `127.0.0.1:9119`, `/api/plugins/kanban/`) | Ada: board, tasks, comments, dispatch, runs, log, WebSocket `/events`. DOCS `kanban.md:877-894, 1047-1058` |
| Tool `kanban_*` untuk agen | Ada, tetapi toolset `hermes-api-server` membuangnya. DOCS `reference/toolsets-reference.md:98` |

- Auth REST dashboard **belum jelas**: dokumen bilang route plugin melewati auth, tetapi kode (`hermes_cli/dashboard_auth/native_http.py:231`) menjaga path `/api/plugins/`. Harus dicek sebelum dipakai.
- Memantau kemajuan: `task_events` (append-only), `task_runs` (hasil, ringkasan, log), WebSocket `/events?since=<id>`, atau `hermes kanban log <id>`. Pemetaan run Kanban ke sesi Hermes belum terkonfirmasi.

## Syarat dan risiko
- Gateway harus jalan agar dispatcher bekerja; hanya satu gateway boleh jadi pemilik dispatch (`kanban.dispatch_in_gateway`). DOCS `kanban.md:320-340`; `kanban-multi-gateway.md:21-41`.
- Panduan setup Windows tidak ada (aturan systemd hanya Linux). DOCS `kanban.md:344-368`. Belum terkonfirmasi.
- Model keamanan: satu host, user tepercaya; dashboard jangan dibuka ke `0.0.0.0`. DOCS `kanban.md:136, 919`.
- Worker berjalan sebagai proses penuh profil; toolset dan hardening kita (`bff/bff/harden.py`) perlu dicek ulang untuk jalur ini karena worker memakai `chat`, bukan API server.

## Opsi
| Opsi | Untung | Rugi |
|---|---|---|
| a. BFF → REST dashboard | JSON rapi dan WebSocket | Auth belum jelas, port terpisah, bukan key per profil |
| b. BFF → CLI `--json` | Terdokumentasi, tanpa layar | Satu proses per panggilan, quoting di Windows |
| c. Baca `kanban.db` langsung | Cepat | Skema tidak dijamin stabil, melewati aturan internal |
| d. Tidak dipakai | Tidak ada risiko baru | Kehilangan antrean, retry, dan worker siap pakai |

## Hasil spike (11 November 2026)
Diuji di papan terpisah `spike-bff` (sudah diarsipkan ke `kanban/boards/_archived/`), tanpa assignee sehingga tidak ada worker yang jalan.
- **Berhasil:** `create --json` (tugas induk dan anak lewat `--parent`), `list --json`, `comment`, `complete --summary`, `show --json` (event `created`, `commented`, `completed`). Setelah induk selesai, anak otomatis naik dari `todo` ke `ready`. `dispatch --dry-run --json` melewati tugas tanpa assignee (`skipped_unassigned`).
- **Lambat:** satu panggilan CLI sekitar 8,5 detik di Windows (start Python). Untuk UI perlu cache atau jalur REST, bukan satu proses per klik.
- **Risiko keamanan (temuan utama):** worker Kanban berjalan dengan toolset platform `cli`, bukan `api_server` (`gateway/session_kanban.py:69`: `platform='cli'`, ditambah `kanban`). Untuk profil `rian`, toolset `cli` saat ini membuka `terminal`, `file`, `code_execution`, `browser`, `computer_use`, `delegation`, `cronjob` (`hermes -p rian tools list --platform cli`). Itu semua yang diblokir `bff/bff/harden.py` untuk API server. Jadi menugaskan tugas ke pegawai AI akan **melewati hardening kita**.
- Karena itu worker sungguhan belum dijalankan. Syaratnya dulu: `harden.py` juga membatasi `platform_toolsets.cli` profil pegawai AI (perubahan konfigurasi persisten; juga mengubah perilaku `hermes -p rian chat` di terminal).

## Uji worker (11 November 2026, setelah toolset `cli` dikunci di 8d73525)
Papan `uji-worker` (sudah diarsipkan), satu tugas untuk `rian`: tulis satu tagline, batas 300 detik.
- Dispatcher jalan: event `claimed` → `spawned` → `owner_admitted` (sesi `source: kanban` dibuat, model `deepseek-v4.1-flash`) → `worker_bound`.
- **Model tidak pernah dipanggil.** Sesi worker tidak berisi prompt tugas, `tool_call_count: 0`; setelah 5 menit `timed_out`, gateway mencatat `gateway.session_managed_worker: Managed worker lost: EOFError`. Diulang otomatis sekali dengan hasil sama, lalu `blocked` (`repeated_failures`, `failure_limit` 2).
- Sesi worker hanya berisi pesan sistem "An automated delivery was interrupted and was not run again".
- Log profil `rian` di jendela itu tidak berisi error lain selain baris di atas; chat biasa lewat API (BFF) tetap berjalan normal di waktu yang sama.
- **Kesimpulan:** di Windows (gateway multipleks native, bukan WSL) worker terkelola Kanban tidak menjalankan giliran model. Pembuatan, rantai, dan pembacaan tugas lewat CLI berfungsi; eksekusi oleh pegawai AI belum. Ini cocok dengan catatan riset bahwa dukungan Windows tidak terdokumentasi.
- **Analisis penyebab (dari kode Hermes):**
  - Alurnya: `kanban_worker_client` (proses kecil) menyerahkan tugas ke gateway pemilik profil; gateway menjalankan anak proses `python -m agent.managed_worker` dan bicara lewat stdin/stdout (`gateway/session_managed_worker.py:596`). `EOFError` hanyalah akibat: setelah 300 detik Kanban mematikan worker, pipa tertutup.
  - Penyebab sebenarnya tersembunyi: stderr anak proses dibuang ke `DEVNULL` karena di gateway multipleks `profile_id` bukan path absolut (`session_managed_worker_log.py:25-28` mengembalikan None), jadi `managed-worker.log` tidak pernah ditulis.
  - Petunjuk terkuat: tepat saat worker dibuat, log `rian` mencatat `credential pool: no available entries (all exhausted or empty)`; baris ini tidak muncul pada run biasa lewat API hari itu. Anak proses untuk profil yang di-route hanya menerima `.env` milik profil itu, dengan kredensial proses gateway dihapus (`session_managed_worker.py:399-435`, "a routed home's worker sees its own files only"). Dugaan: kunci provider ada di home utama, bukan di profil `rian`, sehingga worker tidak punya kredensial dan tidak memulai giliran.
  - Belum terbukti: `hermes -p rian chat -q "..."` langsung dari terminal **berhasil** (24 dtk), tetapi proses CLI tidak dibersihkan env-nya seperti anak proses gateway. Untuk memastikan, stderr worker perlu dilihat (jalankan gateway khusus profil `rian`, bukan multipleks) atau kunci provider ditambahkan ke `.env` profil.
- Opsi lanjut: (1) laporkan ke Hermes / cek versi lebih baru, (2) uji di WSL atau Linux, (3) untuk prototipe, pakai rantai tugas Kanban hanya sebagai papan, dan eksekusi tetap lewat Runs API dari BFF (seperti sequence evaluasi sekarang).

## Langkah spike lanjutan (bila disetujui)
1. Cek `hermes kanban --help` dan buat satu tugas uji untuk profil `rian` (bukan `coder`).
2. Pastikan dispatcher di gateway Windows menjalankan worker dan tugas sampai `done`.
3. Cek toolset worker tidak membuka terminal/file yang kita blokir.
4. Baru putuskan: halaman "Tugas tim" atau workflow antaragen.
