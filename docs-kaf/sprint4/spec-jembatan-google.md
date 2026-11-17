# Spec: Jembatan Drive dan Gmail untuk agen (Sprint 4, 17 Nov 2026)

Masalah: Drive/Gmail tersambung lewat OAuth milik BFF (token terenkripsi di tabel `connections`), tapi agen Hermes tidak punya alat yang memakai token itu, jadi agen bilang "tidak ada koneksi Drive". Keputusan user: buat jembatan untuk Drive dan Gmail. Token TIDAK pernah keluar dari BFF.

## Aturan umum
Sama dengan `spec-ux-mvp.md` "Aturan umum" (branch `feat/frontend-prototype`, jangan commit/push/branch, jangan sentuh perubahan orang lain yang belum di-commit: product images, catalog.py, knowledge.py, test_catalog.py, rich.tsx, start-dev.ps1, .gitignore, route product-images di main.py, migrasi 013/014; bahasa awam; pytest + build lolos; test baru hanya bila penting dan masuk `bff/tests`; shortcut diberi komentar). Restart dev: PowerShell `.\stop-dev.ps1` lalu `.\start-dev.ps1 -NoBrowser -NoWait` dari root repo.

## Desain (sudah diputuskan)
1. **Server MCP internal di BFF**, endpoint HTTP `POST /mcp` (Streamable HTTP, protokol MCP standar). Pakai SDK resmi Python `mcp` (versi exact di `pyproject.toml`, `uv add`), dipasang ke app FastAPI yang ada. Bila pemasangan ke FastAPI rumit, boleh jalankan sebagai sub-app ASGI di path `/mcp`.
2. **Autentikasi**: header `Authorization: Bearer <MCP_BRIDGE_KEY>`; kunci acak per instalasi disimpan di `bff/.env` (`MCP_BRIDGE_KEY`, buat otomatis bila kosong saat registrasi, tambahkan ke `.env.example` tanpa nilai). Bandingkan dengan `hmac.compare_digest`. Hanya menerima koneksi dari 127.0.0.1 (shortcut: satu mesin; ganti dengan token per profil saat Hermes dan BFF dipisah). User yang dilayani: `current_user()` (sekarang "default").
3. **Alat (semua tanpa efek kirim):**
   - `drive_search(query, limit<=10)` → nama, id, jenis, tanggal ubah, link web.
   - `drive_read(file_id)` → teks berkas (pakai ekstraksi yang sudah ada di `integrations.py`/`kb.py` untuk Google Docs/Sheets/Slides, PDF, DOCX, TXT/MD/CSV), dipotong wajar (mis. 50k karakter) dengan tanda bila terpotong.
   - `gmail_search(query, limit<=10)` → pengirim, subjek, tanggal, cuplikan, id. Butuh scope `gmail.readonly`.
   - `gmail_read(message_id)` → pengirim, penerima, subjek, tanggal, isi teks (HTML diubah ke teks), dipotong wajar.
   - `gmail_create_draft(to, subject, body)` → membuat DRAF saja (scope `gmail.compose` yang sudah ada). Tidak ada alat kirim email.
   Deskripsi alat dalam bahasa Inggris singkat untuk model, jelas bahwa draf tidak dikirim.
4. **Scope Gmail**: tambah `https://www.googleapis.com/auth/gmail.readonly` ke provider `gmail` di `connections.py`. Koneksi Gmail lama (bila ada) tanpa scope baca → alat baca mengembalikan pesan ramah "Sambungkan ulang Gmail di halaman Aplikasi untuk memberi izin membaca." Kartu Gmail di Aplikasi: satu kalimat bahwa agen bisa membaca email dan membuat draf, tidak pernah mengirim. Catatan admin (mode admin saja): `gmail.readonly` dan `drive.readonly` adalah scope terbatas Google; untuk produksi di atas 100 user perlu verifikasi aplikasi Google.
5. **Error ramah** dipetakan dari `integrations.py` (belum tersambung → "Google Drive belum disambungkan. Minta pengguna menyambungkannya di halaman Aplikasi."; API mati → pesan admin; 401 → sambungkan ulang). Tidak pernah membocorkan token atau body error mentah.
6. **Registrasi ke Hermes**: fungsi idempoten di BFF (mis. `apps.ensure_bridge()`) yang dijalankan saat BFF start: untuk setiap profil agen, pastikan `config.yaml` punya server MCP `pegawai` (`url: http://127.0.0.1:8090/mcp`, header Authorization) — pakai `hermes -p <slug> mcp add pegawai --url ... --auth header` bila bisa non-interaktif, atau tulis blok `mcp_servers` di `config.yaml` langsung dengan format yang sama seperti hasil CLI (selidiki formatnya dulu, mis. tambahkan ke profil uji lalu baca). Jangan hapus server MCP lain. Pastikan alat MCP `pegawai` aktif di platform `api_server` dan tidak terblokir oleh `harden.py`. Tanpa restart manual oleh user.
7. **Agen tahu**: tidak perlu mengubah SOUL; deskripsi alat cukup. Di halaman Aplikasi, kartu Drive: ganti kalimat "agen tidak membuka Drive sendiri" menjadi "Agen bisa mencari dan membaca berkas Drive Anda (hanya baca)."

## Tambahan: proses berpikir mentah
Baris ringkasan proses berpikir agen (mis. "Actually there's no 'googledrive' in the list.", "Also they wanted 3-day content — should I produce a plan?") tampil mentah dan berbahasa Inggris di chat 1-agen dan chat tim. Di mode user, ganti baris itu dengan label tetap "Berpikir…" / "Selesai berpikir" (beserta jumlah langkah dan durasi yang sudah ada); teks mentah hanya tampil bila saklar "Tampilkan langkah kerja" aktif atau mode admin.

## Penerimaan
- pytest + build lolos; test baru `bff/tests/test_bridge.py` (HTTP Google di-mock): auth bridge ditolak tanpa/ salah kunci, peta error, pemotongan teks, draft tidak memanggil endpoint kirim, registrasi idempoten (config.yaml sementara).
- Uji nyata: setelah restart, di chat tanya Mira "Cari berkas apa saja di Drive saya tentang <kata dari daftar berkas Drive>" → agen memakai alat `drive_search` dan menjawab dengan nama berkas nyata. Gmail: bila belum tersambung, agen menjawab dengan arahan menyambungkan (jangan menyambungkan akun Gmail user).
