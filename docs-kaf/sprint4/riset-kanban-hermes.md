# Riset Kanban bawaan Hermes (Sprint 4)

Diriset 15 Nov 2026 dari dokumentasi resmi dan source di GitHub (main). Belum dicek ke instalasi lokal.

## Ringkasan

- Kanban Hermes disimpan di SQLite `~/.hermes/kanban.db` (satu papan default, **dipakai bersama semua profil**). Papan lain di `~/.hermes/kanban/boards/<slug>/kanban.db`. Sumber: <https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban>
- Status: `triage`, `todo`, `ready`, `running`, `blocked`, `review`, `done`, `archived`.
- Field tugas utama: `title`, `body`, `assignee` (nama profil), `tenant`, `priority`, `scheduled_at`, dependensi antar tugas, komentar.
- Yang memindahkan tugas: tools agen `kanban_*`, CLI `hermes kanban`, dashboard, dan dispatcher (tiap 60 detik).
- **API server (port 8642) tidak punya endpoint Kanban.** Sumber: <https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server>. Endpoint HTTP hanya ada di plugin dashboard (`/api/plugins/kanban/...`), dengan catatan keamanan soal auth.

## Cara BFF membaca

1. **Utama:** jalankan `hermes kanban list --json` / `show --json` di host Hermes (subprocess dengan timeout). Ini antarmuka terdokumentasi paling kecil.
2. Cadangan: baca langsung SQLite (skema tidak terdokumentasi).
3. Event `tool.completed` di stream run dipakai hanya sebagai pemicu refresh, bukan sumber status.

## Batasan

- Tidak ada field pengguna. BFF mengisi `tenant` dengan ID pengguna saat membuat tugas dan memfilter berdasarkan itu; otorisasi tetap di BFF.
- Perubahan status otomatis bisa telat sampai ~60 detik.
- Tools Kanban hanya aktif di profil yang mengaktifkan toolset `kanban`.

## Belum diverifikasi

- Apakah CLI `list` menerima filter `--tenant`.
- Keberadaan `gateway/session_kanban.py` di tag v0.23.0.
- Port dan cara menjalankan dashboard Hermes.
