# Riset: knowledge base per user lewat Drive, Gmail, Calendar (11 November 2026)

Sumber: dokumentasi dan kode Hermes lokal di `%LOCALAPPDATA%\hermes\hermes-agent` (DOCS = `website\docs`). Hanya dokumen lokal; gws CLI dan server MCP vendor tidak diuji.

## Kesimpulan
Hermes bisa terhubung ke Google, tetapi **satu akun Google per profil**, bukan per user. Profil kita adalah pegawai AI (rian, diana, ...), jadi semua user akan melihat kotak surat dan Drive yang sama. Koneksi per user yang sebenarnya harus dibangun di BFF dan butuh login dulu.

**Rekomendasi:** tunda konektor per user sampai login ada. Untuk demo: satu akun uji di satu profil lewat skill `google-workspace`, layanan dibatasi, aksi tulis lewat persetujuan. Untuk produksi: BFF yang memegang OAuth per user (opsi c).

## Jalur 1: skill `google-workspace`
- Bisa baca dan tulis: Gmail (cari, baca, kirim, balas, label), Calendar (lihat, buat, hapus), Drive (cari, unduh, unggah, bagikan, hapus), Contacts (baca), Sheets dan Docs (baca, buat, tulis). DOCS `user-guide/skills/bundled/productivity/productivity-google-workspace.md:193-307`.
- Memakai gws CLI bila terpasang, kalau tidak klien Python bawaan. `skills/productivity/google-workspace/scripts/google_api.py:4-6`.
- Token di `HERMES_HOME/google_token.json` (per profil), diperbarui otomatis. `google_api.py:42`.
- Scope luas: gmail.readonly/send/modify, calendar, drive penuh, contacts.readonly, spreadsheets, documents. `google_api.py:46-53`. Bisa dipersempit dengan `--services`.
- Setup sekali per profil oleh manusia: buat OAuth client "Desktop" di Google Cloud, tambah test user, tempel balik URL redirect. Bisa tanpa browser lokal (`--auth-url`, `--auth-code`). DOCS `productivity-google-workspace.md:46-168`.
- Konfirmasi sebelum kirim email, hapus file, dan sejenisnya hanya **aturan di prompt skill**, bukan gerbang yang dipaksakan. DOCS `productivity-google-workspace.md:333`.
- Gateway memblokir agen membaca file token. `gateway/platforms/base.py:781-785`.

## Jalur 2: server MCP
- Dikonfigurasi per profil di `config.yaml`, bagian `mcp_servers`; stdio atau HTTP. DOCS `user-guide/features/mcp.md:33-40`.
- Server remote dengan `auth: oauth` didukung (discovery, PKCE, refresh). DOCS `mcp.md:350-352`.
- Google Drive MCP menolak registrasi otomatis; harus pakai `client_id`/`client_secret` sendiri. DOCS `mcp.md:410-422`.
- Token di `profiles/<nama>/mcp-tokens/`, tidak pernah dibagi antarprofil. DOCS `multi-profile-gateways.md:590`.
- `trust: untrusted` membuat panggilan tulis meminta persetujuan. DOCS `user-guide/security.md:60`.
- Notion ada sebagai skill opsional (`NOTION_API_KEY`); OneDrive per user tidak ditemukan.

## Jalur 3: konektor terkelola (toolset `connections`)
- Toolset `connections` (tool `manage_connections`) **sudah aktif** di `platform_toolsets.api_server` profil kita (dicek di `profiles/rian/config.yaml`).
- Satu tool untuk dua jenis aplikasi: konektor terkelola seperti `gmail` yang diotorisasi lewat **gateway Nous**, dan server MCP lokal. Bisa menambah akun kedua per aplikasi dengan nama berbeda. DOCS `reference/tools-reference.md:46-54`.
- Di luar aplikasi desktop Hermes (termasuk API server kita), aksi connect mengembalikan **link sambung per aplikasi**; UI kita bisa menampilkan link itu. DOCS `reference/toolsets-reference.md:58`.
- Butuh identitas Nous. Aksi `manage_connections` pertama otomatis membuat identitas Nous gratis; bisa dimatikan dengan `nous.guest: false`. DOCS `user-guide/features/tool-search.md:184-196`.
- Konektor yang belum disambung mengembalikan error `CONNECTION_REQUIRED`. DOCS `tool-search.md:205-207`.
- Catatan: ini jalur OAuth paling ringan (tanpa membuat OAuth client sendiri), tetapi token dipegang layanan pihak ketiga (Nous) dan tetap satu identitas per profil. Perlu persetujuan tim soal privasi sebelum dipakai. Akun bernama per aplikasi bukan pemisahan per user yang aman: agen yang memilih akun.

## Dampak multi-user
- Tidak ada cara mengirim kredensial per user per permintaan. `X-Hermes-Session-Key` hanya memisahkan memori. DOCS `api-server.md:762-773`.
- Koneksi per user berarti: satu profil Hermes per user (berat), atau BFF memegang token tiap user dan memberi isi file ke agen sebagai konteks.
- Untuk API server, aksi yang butuh persetujuan ditolak bila tidak dijawab lewat `POST /v1/runs/{id}/approval`. DOCS `security.md:52`. BFF kita sudah menangani approval.

## Opsi
| Opsi | Untung | Rugi |
|---|---|---|
| a. Satu akun perusahaan per profil (skill) | Cepat untuk demo | Semua user berbagi kotak surat dan Drive; setup OAuth client manual |
| a2. Konektor terkelola Nous (`connections`) | Toolset sudah aktif; tanpa OAuth client sendiri; link sambung bisa ditampilkan di UI | Token di pihak ketiga; satu identitas per profil |
| b. MCP per profil | Cocok untuk vendor dengan OAuth | Sama: satu identitas per profil |
| c. BFF memegang OAuth per user, isi dikirim ke agen | Satu-satunya yang benar-benar per user | Kita yang menyimpan dan mengamankan token; butuh login |
| d. Tunda sampai login ada | Paling aman | Fitur belum ada |

Keputusan login dan penyimpanan token menyangkut keamanan dan backend; sepakati dengan tim sebelum dibangun.
