# Setup koneksi: Google Drive, Gmail, Notion

Panduan untuk pemilik aplikasi (administrator) agar tiap pengguna bisa menyambungkan akunnya sendiri. Ikuti berurutan. Semua nilai rahasia hanya masuk ke `pegawai-ai-backend/bff/.env` (file ini tidak ikut Git). Jangan menempelkannya di chat, kode, atau dokumen.

## Cara kerjanya (singkat)

- Pengguna menekan Hubungkan di Aplikasi, lalu masuk ke halaman izin milik Google atau Notion. Aplikasi tidak pernah melihat kata sandi.
- Token akses disimpan terenkripsi di database (kunci: `CONNECTIONS_KEY`). Tanpa kunci itu, tidak ada token yang disimpan.
- Izin yang diminta seminimal mungkin:
  - Google Drive: baca saja (`drive.readonly`).
  - Gmail: hanya membuat draf (`gmail.compose`). Aplikasi tidak pernah mengirim email.
  - Notion: baca halaman yang dibagikan pengguna ke aplikasi.
- Gmail dan Google Drive adalah dua sambungan terpisah (izin diminta sendiri-sendiri), walau memakai satu OAuth client yang sama.

## 1. Alamat yang dipakai

Tentukan alamat yang Anda pakai untuk membuka aplikasi. Untuk pemakaian lokal: `http://localhost:5173`. Alamat sambungan (redirect URI) dibentuk dari alamat itu, lewat proxy `/bff` yang sama dengan yang dipakai aplikasi:

| Layanan | Redirect URI (tempel persis, tanpa spasi atau garis miring di akhir) |
| --- | --- |
| Google (Drive dan Gmail) | `http://localhost:5173/bff/api/connections/google/callback` |
| Notion | `http://localhost:5173/bff/api/connections/notion/callback` |

Jika Anda membuka aplikasi lewat alamat lain (misalnya domain sendiri), ganti `http://localhost:5173` dengan alamat itu di tabel di atas dan isi `PUBLIC_BASE_URL` di `.env` (langkah 5). Alamat harus melewati proxy yang menambahkan kunci akses BFF, sama seperti halaman aplikasi.

## 2. Google Cloud (Drive dan Gmail)

1. Buka <https://console.cloud.google.com/> dan masuk dengan akun Google Anda.
2. Buat project baru: menu project di bagian atas > Project baru > beri nama, misalnya "Pegawai AI" > Buat.
3. Aktifkan dua API: menu API & Layanan > Library, cari **Google Drive API** lalu Aktifkan. Ulangi untuk **Gmail API**.
4. Layar persetujuan OAuth (OAuth consent screen), menu Google Auth Platform atau API & Layanan > Layar persetujuan OAuth:
   - Jenis pengguna: **Eksternal**.
   - Isi nama aplikasi, email dukungan, dan email kontak developer.
   - Bagian Scope (Akses data): tambahkan `.../auth/drive.readonly` dan `.../auth/gmail.compose` (cari dengan nama Drive API dan Gmail API). Scope `openid` dan `email` sudah ada.
   - Status publikasi: biarkan **Testing** (Pengujian).
   - Bagian Test users (Pengguna uji): **tambahkan email Google Anda sendiri**. Hanya akun yang terdaftar di sini yang bisa menyambung selama status Testing.
5. Buat kredensial: Kredensial > Buat kredensial > **ID klien OAuth**:
   - Jenis aplikasi: **Aplikasi web**.
   - Authorized redirect URIs: tambahkan alamat Google dari tabel di langkah 1.
   - Buat, lalu salin **Client ID** dan **Client secret**.

Catatan Testing: layar izin akan menampilkan peringatan "Google belum memverifikasi aplikasi ini". Itu normal untuk akun Anda sendiri: Lanjutan > lanjutkan ke aplikasi. Di mode Testing, izin (refresh token) kedaluwarsa setelah sekitar 7 hari, lalu kartu akan menampilkan "Perlu disambungkan ulang". Cukup tekan Hubungkan ulang.

## 3. Notion

1. Buka <https://www.notion.so/profile/integrations> dan pilih **Buat integrasi baru** (New integration).
2. Pilih tipe **Public** (Publik). Isi nama, logo bila diminta, dan data perusahaan yang diminta Notion.
3. Redirect URI: tempel alamat Notion dari tabel di langkah 1. Catatan: Notion bisa menolak alamat `http://localhost` pada integrasi publik. Jika ditolak, buka aplikasi lewat alamat https (misalnya terowongan atau domain sendiri) dan pakai alamat itu di semua langkah serta di `PUBLIC_BASE_URL`.
4. Capabilities: centang **Read content**. Tidak perlu izin menulis atau mengubah, dan tidak perlu informasi pengguna.
5. Simpan, lalu salin **OAuth client ID** dan **OAuth client secret** dari tab Secrets.
6. Pengguna memilih halaman yang dibagikan saat menyambung (Select pages). Halaman lain tidak terlihat oleh aplikasi.

## 4. Membuat CONNECTIONS_KEY

Kunci enkripsi untuk token. Buat sekali, simpan aman (misalnya di pengelola kata sandi), dan jangan diganti: jika kunci berubah, token yang sudah tersimpan tidak bisa dibuka dan semua orang harus menyambung ulang.

```
cd pegawai-ai-backend/bff
.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Salin satu baris hasilnya.

## 5. Isi bff/.env

Buka `pegawai-ai-backend/bff/.env` (salin dari `.env.example` jika belum ada) dan tambahkan baris berikut dengan nilai Anda sendiri:

```
CONNECTIONS_KEY=<hasil langkah 4>
GOOGLE_CLIENT_ID=<Client ID dari langkah 2>
GOOGLE_CLIENT_SECRET=<Client secret dari langkah 2>
NOTION_CLIENT_ID=<OAuth client ID dari langkah 3>
NOTION_CLIENT_SECRET=<OAuth client secret dari langkah 3>
# Hanya jika Anda membuka aplikasi di alamat selain http://localhost:5173:
# PUBLIC_BASE_URL=https://alamat-anda
```

Kelompok yang tidak diisi tidak merusak apa pun: kartunya tampil "Belum diatur admin" dan tombolnya nonaktif. Tanpa `CONNECTIONS_KEY`, ketiga kartu tampil "Belum diatur admin" karena token tidak boleh disimpan tanpa enkripsi.

## 6. Mulai ulang dan menyambung

1. Hentikan lalu jalankan lagi aplikasi (`.\stop-dev.ps1`, lalu `.\start-dev.ps1`) agar BFF membaca `.env` yang baru.
2. Buka aplikasi, menu Kemampuan > tab Alat > **Hubungkan aplikasi**.
3. Tekan **Hubungkan** pada Google Drive, masuk dengan akun yang Anda daftarkan sebagai pengguna uji, setujui izin. Anda kembali ke halaman Alat dengan pesan "Google Drive tersambung" dan kartu menampilkan "Tersambung sebagai <email Anda>".
4. Ulangi untuk Gmail dan Notion (Notion meminta memilih halaman yang dibagikan).
5. Cek hasilnya:
   - Pengaturan > Knowledge base > **Pilih dari Drive** atau **Pilih dari Notion**, centang item, Simpan. Item muncul di daftar dengan sumbernya dan tombol **Perbarui**.
   - Chat: ikon klip > **Pilih dari Google Drive**. Link Drive pribadi yang ditempel di chat dengan kata "simpan" kini dibaca lewat sambungan.
   - Di bawah jawaban agen (chat dan grup): **Simpan sebagai draf Gmail**, isi Kepada (boleh kosong), Subjek, Isi, lalu Simpan draf. Buka draf lewat tautan di konfirmasi. Email tidak dikirim.
6. **Putuskan** pada kartu mencabut izin di Google/Notion (bila didukung) dan menghapus token tersimpan.

Jika kartu menampilkan "Perlu disambungkan ulang", izin dicabut atau kedaluwarsa: tekan Hubungkan ulang.

## Verifikasi produksi (nanti)

Scope Drive (`drive.readonly`) dan Gmail (`gmail.compose`) termasuk scope **sensitif/terbatas** menurut Google. Untuk akun Anda sendiri, mode Testing dengan Anda sebagai test user sudah cukup dan tidak perlu verifikasi (batas 100 pengguna uji, izin kedaluwarsa sekitar 7 hari). Sebelum dibuka untuk pengguna umum, aplikasi perlu melalui **verifikasi OAuth Google**: halaman beranda dan kebijakan privasi di domain sendiri, video demonstrasi penggunaan scope, dan untuk scope terbatas kemungkinan penilaian keamanan pihak ketiga (CASA). Siapkan juga status publikasi "In production" setelah lulus. Notion tidak memerlukan verifikasi serupa untuk integrasi publik, tetapi memerlukan tinjauan bila ingin masuk galeri integrasi.

## Langkah berikutnya (belum dikerjakan)

Agen belum bisa memanggil Drive, Gmail, atau Notion sendiri (alat MCP di dalam Hermes). Saat ini sambungan hanya dipakai pengguna lewat tombol: memilih berkas ke Knowledge Base dan menyimpan draf Gmail. Menghubungkan agen langsung ke layanan ini adalah tahap selanjutnya.
