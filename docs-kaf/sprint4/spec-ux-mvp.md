# Spec: UX MVP untuk user awam (Sprint 4, hari 5)

Tujuan: pemilik bisnis non-teknis bisa memakai Pegawai AI tanpa bantuan tim teknis. Semua keputusan di bawah sudah diambil; jangan dibuka ulang.

## Aturan umum (berlaku untuk semua worker)
- Repo `pegawai-ai-backend`, branch `feat/frontend-prototype`. Jangan buat branch/worktree baru. Jangan commit, jangan push.
- Ada perubahan lain yang belum di-commit dan BUKAN milikmu (`bff/bff/catalog.py`, `knowledge.py`, `main.py`, `tests/test_catalog.py`, `frontend/src/rich.tsx`, `start-dev.ps1`, `.gitignore`, `bff/assets/`, `product_images.py`, `product_vision.py`). Jangan revert, jangan format ulang. Kalau terpaksa menyentuh salah satunya, edit sekecil mungkin.
- Bahasa UI: Indonesia sederhana, sapaan "Anda", satu kata per konsep (agen, tugas, jadwal, biaya, pengetahuan). Tanpa jargon: token, BFF, OAuth, run, tool/toolset, session, provider, env, redirect URI, Computer Use, model ID.
- Teks kartu: maksimal satu kalimat pendek + tombol. Detail panjang masuk ke tooltip/"Selengkapnya" atau mode admin.
- Pakai komponen dan token CSS yang sudah ada (`ui.tsx`, `ui-extra.tsx`, `styles.css`, `pages.css`). Light dan dark mode harus tetap rapi. Lebar 375px tidak boleh scroll horizontal.
- Mode admin: `frontend/src/adminMode.ts` (`useAdminMode()`, `setAdminMode()`) sudah ada; pakai, jangan diganti.
- Testing: `npm --prefix frontend run build` harus lolos; `cd bff && uv run pytest -q` harus lolos bila BFF disentuh. Verifikasi dengan membuka app di browser (dev server sudah jalan di http://localhost:5173; BFF 8090). Jangan bikin file test sekali pakai; test baru hanya bila perilakunya penting dan masuk suite `bff/tests`.
- Shortcut yang disengaja diberi komentar `shortcut: <batas>, <kapan di-upgrade>`.

## A. Koneksi Google (worker A: `bff/bff/integrations.py`, `bff/bff/connections.py`, endpoint terkait, `bff/tests/test_connections.py`, `frontend/src/connections.tsx`, `gmail-ui.tsx`, `pick-ui.tsx`)
Fakta: Drive API belum aktif di project Google → token sah tapi tiap panggilan 403 `accessNotConfigured`, sementara UI tetap menampilkan "Tersambung" dan pesannya menyuruh user menyambung ulang.
1. Saat Google/Notion menjawab 403/4xx, baca body error. Petakan:
   - `accessNotConfigured` / `SERVICE_DISABLED` → 503, pesan user: "Layanan {name} belum diaktifkan oleh admin. Hubungi admin Anda." dan `needs: "admin"`.
   - `insufficientPermissions` / scope kurang → 403, `needs: "reconnect"`, pesan: "Izin {name} kurang. Sambungkan ulang dan centang semua izin."
   - lainnya tetap seperti sekarang.
   Catat alasan asli Google di log server (tanpa token/data user). Body error Google tidak dikirim mentah ke browser.
2. Status koneksi jujur: `GET /api/connections` (atau endpoint cek baru `POST /api/connections/{provider}/check`) melakukan satu panggilan ringan ke provider (Drive: `files.list pageSize=1`; Gmail: `users/me/profile`; Notion: `users/me`), hasil disimpan sebentar (cache ~60 dtk). Status baru `broken` dengan `reason` ramah user. UI: badge "Perlu perbaikan" (warna peringatan) + kalimat alasan + tombol yang sesuai (Sambungkan ulang / Hubungi admin). Badge hijau "Tersambung" hanya bila cek terakhir berhasil.
3. Halaman Aplikasi untuk user awam: sembunyikan redirect URI, nama variabel env, daftar terisi/kosong kecuali `useAdminMode()` aktif. Provider yang belum diatur admin → badge "Segera hadir", tanpa tombol aktif. Paragraf "Dipakai di: …" dipersingkat jadi satu kalimat.
4. Jelaskan batas agen di kartu Drive (satu kalimat): agen membaca berkas Drive setelah Anda menambahkannya ke Pengetahuan; agen tidak membuka Drive sendiri.
5. Test di `bff/tests/test_connections.py` (mock HTTP) untuk pemetaan error #1 dan status `broken` #2.

## B. Shell, Beranda, onboarding, jargon (worker B: semua file frontend lain; JANGAN sentuh `connections.tsx`, `gmail-ui.tsx`, `pick-ui.tsx`, dan file BFF)
1. Sidebar mode user (default), urutan:
   - Beranda
   - Tim (halaman grup; ganti label "Grup" → "Tim")
   - Chat (agen per orang)
   - Jadwal & tugas (halaman Kanban; label baru, route lama tetap jalan)
   - Pengetahuan (route baru `#/pengetahuan`, isinya bagian Knowledge base yang sekarang ada di Pengaturan; pakai ulang komponen `kb-ui.tsx`, bagian di Pengaturan diganti tautan ke halaman ini)
   - Aplikasi
   - Pengaturan
   Mode admin aktif → muncul kelompok "Admin": Marketing (formulir), Layanan pelanggan, Agen, Kemampuan, Evaluasi, Aktivitas. Route admin tetap bisa dibuka langsung walau mode admin mati (jangan 404).
   Toggle "Mode admin" ada di Pengaturan > Umum, dengan satu kalimat penjelasan.
2. Beranda menjawab "apa yang perlu saya lakukan hari ini?":
   - "Perlu persetujuan Anda": rencana konten yang menunggu persetujuan (data plans yang ada) dengan tombol menuju kartunya; kosong → "Tidak ada yang menunggu".
   - "Berikutnya": 3 jadwal terdekat (judul, agen/tim, waktu).
   - "Biaya bulan ini": USD terpakai / limit USD + bar sisa. Jumlah token TIDAK ditampilkan di mode user (boleh di mode admin).
   - Satu CTA utama: "Minta tim Anda" → buka Tim Marketing (grup pertama) di composer.
   - Panel "Status kemampuan" dan "Aktivitas terbaru" hanya di mode admin.
3. Onboarding: kartu checklist di atas Beranda sampai semua selesai atau ditutup (simpan "ditutup" di localStorage dengan try/catch). Langkah, status diturunkan dari data bila bisa:
   1. Isi nama bisnis (Pengaturan > Umum)
   2. Tambahkan pengetahuan bisnis (ada item KB)
   3. Sambungkan Google Drive (opsional; koneksi `gdrive` connected)
   4. Minta rencana konten pertama ke Tim Marketing (ada plan)
   5. Setujui rencana konten (ada plan approved)
4. Tim & Chat: daftar agen dikelompokkan per tim (Marketing, Layanan pelanggan). Project Manager tiap tim ditaruh paling atas dengan label "Kontak utama". Jabatan tidak terpotong jadi tak terbaca: dua baris atau tooltip. Empty state chat menyarankan memulai dari Tim. Composer grup punya tautan kecil "Pakai formulir brief" ke Marketing.
5. Jargon: ganti nama tool mentah (mis. `session_search`, `web_search`, `read_file`) dengan label ramah di Aktivitas/Beranda (pakai peta label yang sudah ada bila ada; kalau tidak, buat satu peta di satu tempat). "Proses berpikir" → "Tampilkan langkah kerja". "Computer Use" hanya di mode admin.
6. Jadwal & tugas (Kanban): hapus kalimat "Papan agen terhubung (hanya dibaca), belum ada tugas" bila ada kartu; ganti dengan pesan kosong hanya bila benar-benar kosong. Filter Agen/Tim/Hasil dilipat di balik tombol "Filter"; Periode tetap terlihat. Deskripsi halaman satu kalimat.
7. Persingkat teks panjang di halaman yang disentuh (maks satu kalimat per kartu).

## Rubrik penerimaan (orchestrator)
- Build lolos, pytest lolos, 0 error console di Beranda/Tim/Chat/Jadwal/Pengetahuan/Aplikasi/Pengaturan.
- Mode user: sidebar 7 item, tidak ada kata terlarang di layar (cek dengan get_page_text per halaman).
- Drive cek nyata: dengan API aktif → "Tersambung"; simulasi 403 accessNotConfigured (test) → "Perlu perbaikan" + pesan admin.
- 375px tanpa scroll horizontal, dark mode rapi.
