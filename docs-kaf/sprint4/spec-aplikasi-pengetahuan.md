# Spec: Aplikasi mencakup Hermes + buka ulang berkas Pengetahuan (Sprint 4)

Keputusan user (17 Nov 2026), jangan dibuka ulang:
- Halaman Aplikasi = **gabungan**: katalog konektor Hermes (54 aplikasi lewat Nous Portal, `hermes connectors`) + koneksi OAuth milik kita (Drive dan Gmail, tetap seperti sekarang; Notion hanya lewat konektor Hermes).
- Selain konektor, yang ditampilkan untuk user awam hanya **kemampuan bawaan** Hermes (toolset) sebagai "Keahlian agen". **Tidak** menampilkan kanal pesan (WhatsApp/Telegram/Slack/Discord) dan **tidak** ada MCP kustom.
- Pengetahuan: berkas yang diunggah bisa dibuka lagi.

## Aturan umum
Sama dengan `docs-kaf/sprint4/spec-ux-mvp.md` bagian "Aturan umum" (branch `feat/frontend-prototype`, jangan commit/push/branch, jangan sentuh perubahan orang lain yang belum di-commit, bahasa awam tanpa jargon, build + pytest harus lolos, verifikasi di browser, test baru hanya bila penting dan masuk `bff/tests`, shortcut diberi komentar). Mode admin: `frontend/src/adminMode.ts`.
Migrasi baru mulai nomor `015_` (013 dan 014 sudah dipakai berkas orang lain yang belum di-commit).
Dua worker bekerja bersamaan. `bff/bff/main.py`, `frontend/src/bff.ts`, dan CSS bersama: hanya **tambah** blok milikmu, baca ulang sebelum edit, jangan ubah blok lain.

Fakta lingkungan: Hermes home `%LOCALAPPDATA%\hermes`, profil per agen di `profiles/<slug>` (budi, diana, hendra, mira, reza, rian, sari, siti, vino, wulan, coder). CLI: `hermes -p <slug> connectors list|accounts|connect <app>|disconnect`, `hermes -p <slug> tools list`. Gateway toolset per profil: `GET {HERMES_API_URL}/p/<slug>/v1/toolsets` (lihat `bff/bff/harden.py`, yang juga menulis `platform_toolsets.api_server` di `config.yaml` dan memblokir toolset berbahaya; blokir itu harus tetap berlaku). BFF sudah punya `GET /api/tools` (`main.py`) dan peta label awam `toolsetText` di `frontend/src/ui-extra.tsx`.

## Worker C: Aplikasi (BFF `bff/bff/apps.py` baru + endpoint, `frontend/src/connections.tsx`, `frontend/src/Agents.tsx` bagian alat, `ui-extra.tsx` label)
1. Selidiki dulu (catat temuan singkat di bagian "Temuan C" di bawah file ini): apakah akun konektor Nous dipakai bersama semua profil (auth di home root) atau per profil; bagaimana `connectors connect` memberi alamat login (URL di stdout? membuka browser?) dan bagaimana tahu selesai; format output `list`/`accounts` (ada `--json`?).
2. BFF:
   - `GET /api/apps/catalog`: daftar konektor Hermes dengan `id`, nama tampilan awam, kategori awam, deskripsi satu kalimat Bahasa Indonesia, status (`connected`/`not_connected`), akun (label saja). Nama/kategori/deskripsi dari satu peta statis di `apps.py` untuk aplikasi umum (Notion, Canva, Slack, ClickUp, Asana, Shopify, Stripe, Airtable, Calendly, HubSpot/CRM bila ada, Jira, Linear, Todoist, Box, Confluence, Intercom, SendGrid, Resend, Semrush, Ahrefs, dll.); sisanya nama dirapikan dari id (`clickup_mcp` → "ClickUp") dan kategori "Lainnya". Hasil CLI di-cache singkat (~60 dtk) karena lambat.
   - Kategori awam: Dokumen & catatan, Desain & konten, Pemasaran & SEO, Penjualan & toko, Komunikasi, Proyek & tugas, Data & analitik, Keuangan, Pengembang (Pengembang dan aplikasi teknis seperti Sentry/Datadog/Neon/Supabase/Vercel/Railway/Cloudflare/ClickHouse/Turso hanya tampil di mode admin; tandai `technical: true`).
   - `POST /api/apps/{id}/connect` → kembalikan alamat login untuk dibuka user di tab baru (bila CLI hanya bisa membuka browser lokal, jalankan dan kembalikan `{opened: true}`; tulis shortcut comment). `POST /api/apps/{id}/disconnect`. Polling status dari frontend sampai tersambung (maks 3 menit).
   - Bila akun dipakai per profil: sambungkan untuk semua profil agen (atau profil utama + jelaskan), pilih yang paling sederhana yang benar dan jelaskan di Temuan C.
   - `GET /api/agents/{slug}/skills` + `PUT` untuk menyalakan/mematikan kemampuan bawaan per agen (menulis `platform_toolsets.api_server`, menghormati daftar blokir di `harden.py`, toolset terblokir tidak muncul di daftar user). Perubahan berlaku tanpa restart manual oleh user (restart profil gateway bila perlu, otomatis).
   - Validasi `id`/`slug` (regex), argumen CLI sebagai list (tanpa shell), timeout, error ramah. Test di `bff/tests/test_apps.py` dengan CLI di-mock (parsing output, peta nama, validasi id, blokir toolset).
3. Frontend halaman Aplikasi, urutan:
   - Judul "Aplikasi" + satu kalimat: "Hubungkan aplikasi yang Anda pakai agar agen bisa membantu di sana."
   - Kotak cari + chip kategori.
   - "Tersambung" (kartu kecil) di atas, lalu katalog per kategori dalam grid kartu ringkas: logo/inisial, nama, satu kalimat, tombol "Hubungkan"/"Putuskan". Drive/Gmail yang OAuth kita tampil di grid yang sama (kategori Dokumen & catatan / Komunikasi) dengan perilaku sekarang (picker, draf Gmail) — jangan hilangkan fungsinya.
   - Saat menghubungkan: dialog langkah sederhana ("Anda akan diarahkan ke halaman login aplikasi… setelah selesai, kembali ke sini") + status menunggu.
   - Bagian "Keahlian agen": kartu per kemampuan bawaan dengan nama awam + satu kalimat (Cari di internet, Buat gambar, Baca gambar, Ubah teks jadi suara, Ingatan, Rencana tugas, dll.), menunjukkan agen mana yang memakainya, dan tombol "Atur" yang membuka pilihan per agen (saklar). Tab alat di detail Agen memakai saklar yang sama.
   - Tanpa kata: MCP, connector, toolset, OAuth, Nous, Portal, API, CLI, profil, gateway. Info teknis hanya di mode admin.
   - 375px tanpa scroll horizontal.

## Worker D: buka ulang berkas Pengetahuan (BFF `bff/bff/kb.py`, migrasi `015_kb_originals.sql`, endpoint KB, `frontend/src/Pengetahuan.tsx`, `kb-ui.tsx`)
Fakta: sekarang hanya teks hasil ekstraksi (chunks) yang disimpan; berkas asli dibuang.
1. Simpan berkas asli untuk unggahan baru: tabel `kb_files(item_id uuid pk references kb_items on delete cascade, mime text, data bytea)` (shortcut: bytea di Postgres, maks 10 MB per berkas sesuai batas unggah; pindah ke object storage saat volume besar). Hapus item → berkas ikut terhapus.
2. `GET /api/kb/{id}/file`: kirim berkas asli dengan `Content-Disposition: inline; filename*=` aman, `Content-Type` dari daftar putih (pdf, txt, md, csv, docx), `X-Content-Type-Options: nosniff`; docx sebagai attachment (unduh). Hanya milik `current_user()`. 404 ramah bila tidak ada berkas asli.
3. `GET /api/kb/{id}/text`: teks yang tersimpan (gabungan chunks berurutan) untuk semua jenis item (file lama, Drive, website), dibatasi ukuran wajar.
4. Frontend Pengetahuan: klik nama item atau tombol "Lihat" → panel/dialog pratinjau:
   - PDF: tampil di `<iframe>`/`<object>` dari URL blob (fetch lewat client `bff.ts` karena butuh header kunci; jangan taruh kunci di URL).
   - TXT/MD/CSV: tampilkan isi (MD dirender, CSV sebagai tabel sederhana bila kecil).
   - DOCX: tombol "Unduh berkas asli" + teks hasil baca.
   - Drive/website: tombol "Buka sumber" (tab baru, `rel="noopener noreferrer"`) + teks yang disimpan.
   - Berkas lama tanpa berkas asli: tampilkan teks tersimpan + catatan satu kalimat "Berkas asli tidak disimpan untuk unggahan sebelum 17 Nov. Unggah ulang bila perlu."
   - Tombol "Unduh" untuk semua yang punya berkas asli. Esc menutup dialog, fokus kembali ke tombol.
5. Test di `bff/tests` (pakai pola test KB yang ada; yang butuh DB boleh di-skip tanpa `TEST_DATABASE_URL` seperti test lain) untuk: simpan + ambil berkas, kepemilikan, header aman, item tanpa berkas asli → 404.

## Rubrik penerimaan (orchestrator)
- pytest + build lolos.
- Aplikasi: katalog tampil dengan kategori dan pencarian; tidak ada kata terlarang di mode user; satu alur "Hubungkan" bisa dimulai (alamat login atau browser terbuka); Drive/Gmail tetap berfungsi; saklar keahlian agen mengubah toolset nyata (cek `hermes -p <slug> tools list` atau `/v1/toolsets`) dan toolset terblokir tidak bisa dinyalakan.
- Pengetahuan: unggah PDF/TXT baru lalu buka lagi (pratinjau + unduh); item lama menampilkan teks tersimpan.

## Temuan C
Temuan C (17 Nov 2026, worker C):
- Akun konektor dipakai bersama: tersimpan di akun Nous (setiap `profiles/<slug>/auth.json` memuat `user_id` yang sama; `hendra` tanpa login Nous sendiri). Jadi BFF menjalankan CLI sekali di home utama (tanpa `-p`), tidak per agen. Catatan: agen tanpa login Nous (hendra) mungkin tidak melihat konektor; belum diuji karena tidak ada akun yang disambungkan.
- `hermes connectors list` mencetak `<id>  connected|not connected` (54 id, sebagian berakhiran `_mcp`); `accounts` mencetak `<id>  <nama>  <status>` atau "You have no connected accounts."; tidak ada `--json`. Tiap panggilan CLI sekitar 5 detik, maka katalog di-cache 60 dtk dan `list`+`accounts` dijalankan paralel.
- `connect <id>` TIDAK membuka browser: ia mencetak URL login (`https://portal.nousresearch.com/connect/...`) di stdout lalu polling tiap 2 dtk sampai selesai (batas waktu operasi). BFF menjalankannya sebagai proses latar (maks 3 menit), menangkap URL, mengembalikan `{url}`; frontend membukanya di tab baru dan polling `GET /api/apps/{id}/status` (memakai `connectors list`). `disconnect <id> --yes` (plus `--alias` bila akun lebih dari satu).
- Keahlian = `platform_toolsets.api_server` di `config.yaml` profil. Gateway membaca ulang config tiap permintaan, jadi `GET /v1/toolsets` langsung mencerminkan perubahan tanpa restart. Tersembunyi untuk semua orang: daftar blokir `harden.DENY`, `clarify` (selalu aktif), dan toolset kanal pesan (discord, discord_admin, yuanbao). Hanya mode admin: skills, kanban, x_search, context_engine, a2a.
- Endpoint baru: `GET /api/apps/catalog`, `POST /api/apps/{id}/connect`, `GET /api/apps/{id}/status`, `POST /api/apps/{id}/disconnect`, `GET /api/skills`, `GET|PUT /api/agents/{slug}/skills`.
- Belum diuji dengan akun nyata (sengaja): penyelesaian login sampai status `connected`.

## Keputusan 17 Nov (lanjutan)
- Koneksi Notion milik kita DIHAPUS seluruhnya (provider, OAuth, impor halaman, kartu, tombol "Pilih dari Notion"). Notion hanya ditawarkan lewat konektor Hermes `notion` di katalog Aplikasi. Item Pengetahuan lama bertipe `notion` tetap ada (tidak ada migrasi data); nilai `notion` dibiarkan di constraint database.
- Aturan satu kartu: bila sebuah aplikasi ada sebagai koneksi kita dan sebagai konektor Hermes, Aplikasi menampilkan SATU kartu. Peta eksplisit `OWN_AS_HERMES` di `frontend/src/connections.tsx` (`gdrive` ↔ `google_drive`/`googledrive`, `gmail` ↔ `gmail`); konektor Hermes dipilih, dan aksi tambahan kita (mis. "Pilih dari Drive") tetap di kartu itu bila koneksi kita juga tersambung. Saat ini katalog tidak punya yang tumpang tindih.
