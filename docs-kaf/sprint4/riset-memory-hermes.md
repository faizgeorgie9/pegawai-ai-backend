# Riset memory untuk Hermes (Sprint 4)

Tugas ClickUp: [Research memory for Hermes (Obsidian, Hindsight, memO, Honcho, etc.)](https://app.clickup.com/t/z8xxqwfk8d). Diriset 15 Nov 2026 dari sumber web (dokumentasi resmi dan repo). Instalasi Hermes lokal tidak ditemukan, jadi belum dicek ke kode.

## Kesimpulan

- **MVP: pakai memory bawaan Hermes** (MEMORY.md + USER.md + pencarian sesi di state.db). Tidak butuh infrastruktur baru.
- **Kalau butuh ingatan lebih kaya:** Mem0 self-host (Apache 2.0, mendukung `user_id` bawaan). Alternatifnya Hindsight (MIT, isolasi per bank, butuh Postgres + pgvector).
- **Jangan pakai Obsidian** sebagai memory: bukan provider Hermes, aplikasi desktop, tidak multi-pengguna.
- **Honcho ditunda:** lisensi server AGPL v3 (perlu dicek di repo), kecuali pakai versi cloud.
- **Knowledge Base ≠ memory.** File, Google Drive, dan URL butuh komponen RAG sendiri di BFF (Postgres + pgvector), bukan memory provider.

## Memory bawaan Hermes

Sumber: <https://hermes-agent.nousresearch.com/docs/user-guide/features/memory>

- Dua file kecil di `~/.hermes/memories/`: `MEMORY.md` (catatan agen, maks 2.200 karakter) dan `USER.md` (profil pengguna, maks 1.375 karakter). Dimasukkan ke system prompt saat sesi dimulai; perubahan di tengah sesi baru terbaca di sesi berikutnya.
- Terpisah per profil Hermes (`~/.hermes/profiles/<nama>/memories/`).
- Pencarian sesi lama lewat SQLite FTS5 di `~/.hermes/state.db`.
- Satu provider eksternal bisa aktif (`memory.provider` di config.yaml); memory bawaan tetap jalan. Provider resmi: Honcho, OpenViking, Mem0, Hindsight, Holographic, Supermemory, Memori. Sumber: <https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers>
- Rilis: v0.23.0 (5 Nov 2026), v0.23.1 (9–10 Nov 2026). <https://github.com/NousResearch/hermes-agent/releases>

## Perbandingan kandidat

| Opsi | Hosting | Lisensi | Integrasi Hermes | Isolasi per pengguna | Catatan |
|---|---|---|---|---|---|
| Bawaan Hermes | File lokal | MIT | Langsung | Per profil (file system) | Kapasitas kecil |
| Mem0 | Cloud atau self-host | Apache 2.0 ([repo](https://github.com/mem0ai/mem0)) | Provider resmi | `user_id` bawaan | Sederhana, banyak dipakai |
| Hindsight | Docker/pip/Helm, butuh Postgres + pgvector | MIT ([repo](https://github.com/vectorize-io/hindsight)) | Provider resmi | Per bank | Ada graph/reflect; angka benchmark klaim vendor |
| Honcho | Cloud atau self-host | AGPL v3 (cek repo) | Provider resmi | Peer per pengguna | Kuat di pemodelan pengguna |
| Obsidian | Aplikasi desktop | Proprietary ([lisensi](https://obsidian.md/license)) | Tidak ada | Tidak ada | Tidak cocok untuk backend |

## Yang dibutuhkan BFF kalau memory dipakai per pengguna

- Petakan pengguna + agen ke profil Hermes (atau `user_id`/`bank_id` provider) di sisi server; jangan percaya ID dari klien.
- Buat profil saat pengguna/agen dibuat, hapus saat akun dihapus.
- Kunci provider per profil, bukan satu `.env` global.
- Group chat 5 agen = 5 profil per pengguna; cek beban gateway Hermes.

## Risiko yang belum diverifikasi

- Isolasi per profil hanya di level file system; belum terbukti sebagai batas keamanan jika satu proses melayani banyak pengguna. Perlu diuji.
- Harga cloud Mem0/Hindsight/Honcho dan lisensi Honcho belum dicek dari sumber primer.
- Kunci konfigurasi provider perlu dicek ulang di dokumentasi sebelum dipakai.
