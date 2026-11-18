# Spec implementasi: Papan Tugas (18 Nov 2026)

Desain produk: `desain-kanban.md` (DISETUJUI Kevin: kerjakan semua tahap). Dokumen ini = keputusan teknis. Tahap A → B → C dikerjakan berurutan; setiap tahap harus lolos build + pytest sebelum lanjut.

## Aturan umum (semua tahap)
- Branch `feat/frontend-prototype`. Jangan buat branch/worktree, jangan commit/push.
- Jangan sentuh atau stage perubahan orang lain yang belum di-commit (`git status`: .gitignore, catalog.py, knowledge.py, test_catalog.py, rich.tsx, start-dev.ps1, bff/assets, product_images.py, product_vision.py, migrasi 013/014, test_product_*, serta import/route product-images di main.py). Di `main.py` tambahkan route baru sebagai SATU blok berurutan `# ---------- tasks ----------` agar mudah dipisah saat commit.
- Bahasa UI awam Indonesia; detail teknis (id, run, status internal) hanya di mode admin (`useAdminMode`). UI pakai skill design-taste-frontend dan gaya yang ada (`pages.css`, `Dialog`, `btn`).
- Lean: tanpa fitur di luar spec. Shortcut diberi komentar `shortcut: <batas>, <kapan ditingkatkan>`.
- Testing: `npm --prefix frontend run build`; `uv run pytest -p no:cacheprovider --basetemp <folder temp yang bisa ditulis>` di `bff`. Test DB: bila `TEST_DATABASE_URL` belum ada, buat database lokal terpisah `pegawai_test` di server Postgres yang sama dengan `DATABASE_URL` di `bff/.env` (JANGAN pakai/ubah database dev untuk test) dan jalankan test dengan env itu, supaya test DB tidak di-skip. Test baru hanya yang penting (transisi status, cascade batal, dispatcher, alat agen) di `bff/tests/test_tasks.py`; tanpa file test sekali pakai. Web: uji dengan browser bawaan (mcp__Claude_Browser__*) di localhost:5173, mode admin mati, termasuk lebar 375 px.
- Restart dev bila perlu: PowerShell `.\stop-dev.ps1` lalu `.\start-dev.ps1 -NoBrowser -NoWait` di root repo.
- Data user: jangan hapus data user yang ada; buat data uji sendiri dan bersihkan.

## Model data — migrasi `017_tasks.sql`
```
tasks: id uuid pk default gen_random_uuid(), user_id text not null,
  title text not null, body text not null default '',
  assignee_bot text null, assignee_group uuid null references groups(id),   -- tepat satu terisi, kecuali tugas induk rencana (boleh grup)
  status text not null check in ('todo','scheduled','ready','running','blocked','review','done','archived'),
  outcome text null check in ('ok','failed','cancelled'),
  kind text not null default 'task' check in ('task','plan'),               -- plan = induk rencana konten
  priority smallint not null default 0,                                      -- 0 normal, 1 penting
  parent_id uuid null references tasks(id) on delete cascade,
  scheduled_at timestamptz null,
  source text not null check in ('user','chat','agent','plan','recurring'),
  source_ref jsonb not null default '{}',   -- {group_id, message_id, session_id, schedule_id}
  result text null, block_kind text null, block_reason text null,   -- block_kind: needs_input | review | plan_approval | stopped | failed
  attempts int not null default 0, current_run_id uuid null,
  schedule_id uuid null references schedules(id) on delete set null,
  created_at, updated_at, started_at, completed_at timestamptz
task_comments: id bigserial, task_id uuid fk cascade, author text check in ('user','bot','system'), bot_id text null, text text, created_at
task_events:   id bigserial, task_id uuid fk cascade, kind text, payload jsonb default '{}', created_at
alter table runs add column task_id uuid null references tasks(id) on delete set null;
```
Indeks: (user_id, status), (parent_id), (status, scheduled_at), unik parsial `(source_ref->>'message_id')` untuk kind='plan'.

## Status, kolom, transisi (meniru Hermes `kanban_workflow.py`)
Kolom: Antre = todo|scheduled|ready; Dikerjakan = running; Perlu Anda = blocked|review; Selesai = done (outcome sebagai tanda, disembunyikan setelah 14 hari); archived tidak tampil (filter "Arsip").
Modul `bff/bff/tasks.py` memegang SEMUA perubahan status lewat satu fungsi `transition(task, to, actor, **fields)` yang memvalidasi matriks dan menulis `task_events`. Verba:
- `start` (Kerjakan sekarang): todo|scheduled|blocked|review|done → ready (scheduled_at=null).
- `stop` (Hentikan): running → blocked, block_kind=stopped, menghentikan run aktif (pakai jalur stop yang ada: run, grup).
- `reply(text)` (Jawab): komentar user; blocked|review → ready. Agen melanjutkan dengan komentar itu.
- `request_changes(note)` (Minta revisi): review → ready + komentar.
- `approve`: review → done outcome ok; untuk kind=plan → lihat tahap B.
- `cancel` (Batalkan): apa pun kecuali archived → archived outcome cancelled; CASCADE ke semua anak yang belum done; hentikan run yang berjalan.
- `retry` (Ulangi): done → ready (attempts=0).
- `archive` / `restore`: done → archived; archived → todo.
- `move(to_column)` untuk drag: hanya Perlu Anda → Antre (= start) dan Selesai → Antre (= retry). Dikerjakan bukan target drop.
Matriks ditolak → 409 dengan pesan ramah.

## API (blok tasks di main.py, logika di tasks.py)
- `GET /api/tasks/board?agent=&group=&q=` → `{columns:[{id,label,hint,total,cards}], counts}`; kartu: id, title, column, status, kind, assignee {bot|group, name, color}, parent {id,title}, scheduled_at, block_kind, line (satu baris status ramah: pertanyaan agen / jam jadwal / langkah terakhir / ringkasan hasil), cost (dari runs yang task_id-nya cocok), children_done/children_total untuk plan, primary_action, more_actions.
- `GET /api/tasks/{id}` → detail + comments + events (ringkas) + runs (id, status, biaya, waktu) + children.
- `POST /api/tasks` (title wajib, body, assignee_bot|assignee_group, scheduled_at?, priority?) → todo atau scheduled.
- `PATCH /api/tasks/{id}` (title, body, assignee, scheduled_at, priority) hanya saat Antre/Perlu Anda.
- `POST /api/tasks/{id}/{verb}` untuk verba di atas (body: text/note/to).
- `POST /api/tasks/{id}/comments` (komentar user tanpa memindah status bila task sedang Antre).
- `GET /api/kanban` lama dihapus beserta pemakaiannya di frontend; Beranda "Berikutnya" dan badge memakai tasks.

## Tahap A — data, API, papan
1. Migrasi 017, `tasks.py`, route, test transisi + cascade.
2. Frontend: tulis ulang `Kanban.tsx` sebagai papan tugas (judul halaman tetap "Jadwal & tugas"):
   - 4 kolom + baris penjelas + kosong ramah (dari `spec-kanban-kelola.md`, label "Perlu Anda").
   - Tambah cepat di kepala kolom Antre: input judul + pilih agen/tim + jadwal opsional; Enter menyimpan.
   - Kartu: judul, avatar pengerja, line, lencana induk ("Bagian dari: …"), biaya bila selesai, satu tombol utama + "⋯" (pola menu yang sudah ada, termasuk perbaikan z-index).
   - Klik kartu → panel samping (Dialog wide atau drawer) berisi: instruksi (bisa diubah saat Antre), hasil terakhir (markdown pakai renderer yang ada), utas komentar dengan kotak "Balas ke agen…" (mengirim `reply` saat Perlu Anda, komentar biasa saat Antre), riwayat langkah ringkas, tombol aksi sesuai kolom. Untuk plan: daftar anak per hari.
   - Drag-and-drop HTML5 sederhana hanya untuk dua perpindahan yang diizinkan; tetap ada tombol untuk aksesibilitas.
   - Filter yang ada (agen, tim) dipertahankan; filter "Arsip".
   - "Jadwal baru" dari commit 037b885 → menjadi "Tugas berulang" (tahap B membuat templat; di A cukup tetap memakai api.createSchedule).
3. Bersihkan: hapus logika kartu dari runs/occurrence/plan di `kanban.py` yang tak terpakai lagi (boleh hapus modul bila kosong; Hermes read-only boleh dibuang — YAGNI).

## Tahap B — eksekusi, rencana, berulang
1. Dispatcher di loop penjadwal yang ada (`scheduler.tick`): scheduled dengan scheduled_at ≤ now → ready; ambil ready (urut priority desc, created_at) dengan batas satu tugas running per pengerja (bot atau grup); jalankan dengan jalur eksekusi yang sudah dipakai `run_occurrence` (bot langsung / grup `follow_group`), input = judul + instruksi + konteks induk + komentar user sejak run terakhir + (tahap C) id tugas dan petunjuk alat. Set runs.task_id, current_run_id, started_at, attempts+1.
2. Selesai run: bila status tugas masih running (agen tidak memanggil alat tugas) → review, block_kind=review, result = output akhir agen/ringkasan diskusi, line "Hasil siap ditinjau". Gagal → attempts < 2 ? ready : blocked block_kind=failed dengan pesan ramah. Klaim tahan restart: `recover()` mengembalikan running yatim ke ready.
3. Rencana konten: saat pesan rencana valid diposting di grup → buat task kind=plan (source plan, source_ref group/message) status review block_kind=plan_approval, line "Rencana menunggu persetujuan Anda". `approve` pada plan (dari papan ATAU tombol Setujui di chat — keduanya memanggil fungsi yang sama, ganti `scheduler.approve_plan`) → induk ke todo? TIDAK: induk tetap sebagai kartu ringkas di kolom sesuai anaknya: induk status running bila ada anak berjalan, done bila semua anak done; anak per hari dibuat sebagai task scheduled (assignee grup/eksekutor seperti `plan_slots`/`find_executors`). Revisi rencana baru dari agen menggantikan induk lama yang masih plan_approval (arsipkan yang lama, outcome cancelled). Kartu rencana di chat menampilkan status nyata (Menunggu / Disetujui / Dibatalkan) dan tombol "Batalkan" di samping "Setujui".
4. Tugas berulang: tabel `schedules` (kind recurring) tetap sebagai templat; materialisasi membuat task source=recurring, scheduled_at=slot, schedule_id, alih-alih `schedule_occurrences`. Jeda/Hapus templat: anak scheduled yang belum jalan ikut diarsipkan. UI: "Tugas berulang" di papan (dialog 3 pertanyaan yang ada) + daftar kecil templat aktif dengan Jeda/Lanjutkan/Hapus.
5. Migrasi data: occurrence `planned` yang ada → task scheduled; schedule plan lama → task plan (sudah disetujui) + anak. Setelah itu `schedule_occurrences` tidak dipakai lagi untuk eksekusi (tabel dibiarkan; shortcut komentar).
6. Beranda: "Berikutnya" dari tasks Antre terjadwal; "Perlu persetujuan Anda" menyertakan tasks Perlu Anda (selain pending_actions).

## Tahap C — agen ikut mengelola
1. Alat MCP baru di `bridge.py` (pola alat yang ada, pakai konteks bot dari header `X-Pegawai-Bot` + run aktif → task lewat runs.task_id): `task_list(status?)`, `task_create(title, instructions, assignee?, when?)` (assignee default diri sendiri; tim boleh), `task_comment(task_id?, text)`, `task_ask_user(question, task_id?)`, `task_request_review(summary, task_id?)`, `task_complete(summary, task_id?)`, `task_cancel(task_id, reason)` (arsip, boleh langsung atas perintah user). task_id opsional = tugas run aktif. `task_ask_user` tanpa tugas aktif (chat/diskusi biasa) membuat tugas baru di Perlu Anda (source chat, source_ref grup/sesi, assignee = bot/grup itu) berisi pertanyaan; balasan user di kartu juga diposting sebagai pesan ke chat/grup itu lalu tugas lanjut.
   Deskripsi alat dalam bahasa Inggris singkat: kapan memakai (pekerjaan lebih dari satu balasan, menunggu jawaban user, selesai), dan "always end a task with task_complete, task_request_review or task_ask_user".
2. Pastikan alat aktif di semua profil (registrasi `pegawai` yang ada sudah mencakup semua alat server) dan tidak terblok `harden.py`.
3. Chat 1-agen dan grup: tombol kecil "Jadikan tugas" pada pesan user → POST /api/tasks (source chat, judul ~8 kata pertama, instruksi = isi pesan, assignee = bot/grup itu). Pesan agen yang membuat/memperbarui tugas boleh menampilkan chip tautan "Tugas: <judul>" (cukup bila ada task_events terkait run).
4. Uji nyata (browser): di grup Tim Marketing Uji minta "Buatkan rencana konten 2 hari promo kaos oversize pakai HEMATNOV" → kartu rencana di Perlu Anda → Setujui → anak di Antre → "Kerjakan sekarang" pada satu anak → Dikerjakan → selesai ke Perlu Anda/Selesai dengan hasil. Lalu di chat bilang "batalkan rencana itu" → agen memanggil task_cancel → kartu hilang ke Arsip. Hapus data uji setelahnya bila bukan milik user.
