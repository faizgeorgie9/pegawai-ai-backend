# To do dari evaluasi (11 November 2026)

**Update 11 November, branch `feat/evaluasi-sprint3` (belum di-push):** selesai poin 1 (sidebar dan grup stream, 8ddcc8e), 3 (model dan reasoning per agen, 775111d), 5 (clarify, 8d73525), 6 tahap 1-2 (775111d), hardening `cli` untuk Kanban (8d73525), perbaikan identitas approval (8ddcc8e). Sisa: kartu izin/pertanyaan di UI grup; zona waktu belum dipakai untuk tampilan; uji worker Kanban; konektor dan login (butuh keputusan tim).

Status: dicatat, belum dikerjakan. Urutan kerja yang disarankan: 5, lalu 1, lalu 3. Poin 2 dan 4 menunggu riset (`riset-kanban.md`, `riset-konektor.md`).

## 1. Workflow terpisah dari chat; grup chat seperti chat biasa
- [ ] Sidebar: grup "Percakapan" (Beranda, Chat, Grup) dan grup baru "Workflow" (Marketing, CS). File: `frontend/src/App.tsx`.
- [ ] Grup chat stream seperti chat: BFF (`bff/bff/groups.py`) meneruskan event run tiap bot (langkah, delta teks, status), lalu `frontend/src/Group.tsx` memakai `LiveSteps` dan `useSmoothText`. Sekarang pesan bot muncul utuh, hanya ada indikator berpikir/menulis.

## 2. Fitur Kanban Hermes
- [x] Riset dan spike CLI tanpa worker: lihat `riset-kanban.md` (berhasil, tapi ~8,5 dtk per panggilan).
- [ ] Sebelum worker dijalankan: perluas `bff/bff/harden.py` agar membatasi `platform_toolsets.cli` profil pegawai AI (worker Kanban memakai toolset `cli`, yang sekarang membuka terminal/file).
- [ ] Putuskan apakah dipakai untuk "Tugas tim" atau workflow antaragen.

## 3. Pilihan model dan reasoning effort per agen
- [ ] BFF: simpan `model`, `provider`, `reasoning_effort` per bot (migrasi baru), kirim di `POST /v1/runs` (`model`, `provider`, `model_options.reasoning_effort`; DOCS `api-server.md:395-450`).
- [ ] Daftar model dari `/v1/models` (sudah dipanggil di `bff/bff/bots.py:194`).
- [ ] UI: dua dropdown di halaman edit agen (`frontend/src/Agents.tsx`).

## 4. Knowledge base per user: Drive, email, kalender
- [ ] Riset dulu: lihat `riset-konektor.md`. Butuh login dan penyimpanan token Google; sepakati dengan tim.

## 6. Halaman Pengaturan (tingkat ruang kerja)
- [ ] Tahap 1: halaman `#/pengaturan` dengan tiga bagian: Umum (nama perusahaan, bahasa, zona waktu, tema dipindah dari sidebar), Model AI (model dan reasoning bawaan untuk agen baru; bergantung poin 3), Notifikasi.
- [ ] Tahap 2: Keamanan dan izin (tampilkan isi `harden.py` dan aksi yang butuh persetujuan), Knowledge base (lihat dan ganti dokumen beserta versinya), Paket dan pemakaian (tabel `plans`), Data (lama simpan log, ekspor).
- [ ] Tahap 3: Koneksi (bergantung keputusan konektor), Akun dan anggota tim (bergantung login).
- Tidak masuk Pengaturan: persona/model/tool per agen (halaman Agen), Tools/Computer use/Scheduler (halaman Kemampuan, cukup ditautkan).
- Sidebar grup "Pengaturan": Agen, Kemampuan, Pengaturan.

## 5. Input user saat LLM bertanya (clarify)
- [ ] Aktifkan toolset `clarify` untuk API server: sekarang **tidak ada** di `platform_toolsets.api_server` profil kita (web, vision, image_gen, skills, todo, memory, session_search, connections), dan toolset bawaan `hermes-api-server` sengaja membuangnya (DOCS `reference/toolsets-reference.md:98`). Tambahkan lewat `bff/bff/harden.py`, bukan edit manual.
- [ ] BFF: tangani event clarify dari run seperti approval (`bff/bff/engine.py:264`), endpoint jawaban yang meneruskan ke `POST /v1/runs/{id}/clarify` (`request_id`, `execution_generation`, `answer`).
- [ ] UI: kotak input pertanyaan di chat dan workspace workflow.
- Koreksi (11 November): run **tidak** menggantung hari ini. Karena tool `clarify` tidak aktif, LLM bertanya lewat teks biasa di jawabannya dan user membalas di chat. Fitur ini membuat pertanyaan jadi input terstruktur (misal pilihan), terutama di workspace workflow yang bukan chat.
