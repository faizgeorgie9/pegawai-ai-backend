# Deploy Pegawai AI (satu perintah)

Panduan singkat untuk tim. Semua perintah dijalankan **dari laptop Windows**, di root repo
`pegawai-ai-backend`. Branch lokal yang aktif tidak berpengaruh: yang dideploy selalu `origin/main`.

Server tidak punya Node/npm, jadi frontend **selalu dibangun di laptop**. Skrip deploy membangun
rilis dari commit git (bukan dari working tree), menguji backend, membangun frontend, lalu mengirim
rilis ke server. Berkas `.env` dan rahasia lain tidak pernah dibaca, dikirim, atau dicetak.

## Prasyarat (sekali saja)

- Git, Node.js + npm, `uv`, dan OpenSSH Client (`ssh`, `scp`) ada di PATH.
- Kunci SSH di `~/.ssh/pegawai-ai.pem` (atau tunjuk dengan `-KeyPath`).
- Akses ke `ubuntu@139.190.107.151`.

## Deploy

```powershell
# dari root repo
.\vps\deploy.ps1
```

Bila PowerShell menolak menjalankan skrip:

```powershell
powershell -ExecutionPolicy Bypass -File .\vps\deploy.ps1
```

Yang dilakukan skrip:

1. `git fetch origin`, ambil `origin/main`.
2. Bangun sumber dari `git archive` di folder sementara **di luar repo** (perubahan lokal tidak ikut).
3. Jalankan uji backend (`uv run --frozen pytest`).
4. `npm ci && npm run build` di `frontend`.
5. Rakit `bff/` + `www/` + `SHA` + `MANIFEST.sha256`, buat `tar.gz`, verifikasi ulang.
6. Unggah ke `/home/ubuntu/releases/<sha>` (atau pakai ulang bila sudah ada dan utuh).
7. Jalankan `/home/ubuntu/deploy-pegawai-ai.sh <sha>` dan tampilkan keluarannya: backup → rsync
   backend → dependensi → restart + health → frontend → verifikasi. Bila health gagal, server
   **rollback otomatis**.
8. Tampilkan ringkasan: rilis aktif, health, durasi.

Opsi:

| Opsi | Arti |
|---|---|
| `-DryRun` | Semua tahap lokal + pemeriksaan server, tanpa unggah dan tanpa deploy. |
| `-Ref <sha/branch>` | Deploy commit lain, **hanya bila commit itu bagian dari `origin/main`**. |
| `-SkipTests` | Lewati uji backend (mendesak saja; muncul peringatan). |
| `-Rollback` | Kembali ke rilis sebelumnya (lihat di bawah). |
| `-Yes` | Lewati konfirmasi pada `-Rollback`. |
| `-KeyPath <path>` | Kunci SSH lain. |

Contoh:

```powershell
.\vps\deploy.ps1 -DryRun
```

## Aturan

1. **Hanya deploy dari `main`.** `-Ref` ditolak bila commit belum menjadi bagian `origin/main`.
2. **Umumkan di chat tim** sebelum mulai dan setelah selesai (rilis + hasil health).
3. **Satu deployer pada satu waktu.** Skrip memakai kunci `flock` di server; deploy kedua ditolak.
4. **Jangan mengedit berkas di server secara manual** dan jangan memakai skrip lama (daftar di bawah).
5. Jangan menempelkan isi `.env`, token, atau kata sandi ke chat/log.

## Rollback

```powershell
.\vps\deploy.ps1 -Rollback          # minta konfirmasi
.\vps\deploy.ps1 -Rollback -Yes     # tanpa konfirmasi
```

Skrip menampilkan daftar rilis di server (dengan tanggal), memverifikasi `MANIFEST.sha256` rilis
tujuan, lalu menjalankan skrip deploy server untuk rilis **satu langkah sebelum** `CURRENT_RELEASE`.
Rollback berulang akan terus mundur ke rilis yang lebih lama.

Yang perlu diketahui:

- Migrasi database **tidak** dibatalkan (semuanya aditif). Jangan drop tabel/kolom saat rollback.
- Konfigurasi Nginx/systemd tidak diubah oleh deploy, jadi tidak ikut di-rollback.
- Bila skrip tidak bisa dipakai, pulihkan dari backup di server (lihat di bawah) dan laporkan.

## Backup dan retensi

Setiap deploy membuat `/home/ubuntu/backups/deploy-<UTC>/` (mode 700) berisi:

- `app.tar.gz` — `/home/ubuntu/pegawai-ai` tanpa `.venv` dan tanpa `.env`
- `www.tar.gz` — web root `/var/www/pegawai-ai`
- `neon.dump` — `pg_dump -Fc` lewat kontainer `postgres:18-alpine` (bila docker tersedia)
- salinan konfigurasi Nginx dan unit `pegawai-ai-bff.service`

Yang disimpan: **5 backup deploy terakhir** dan **3 rilis terakhir** di `/home/ubuntu/releases/<sha>/`.
Rilis aktif dicatat di `/home/ubuntu/CURRENT_RELEASE`.

## Cek setelah deploy

```powershell
curl.exe -fsS https://139.190.107.151.sslip.io/api/health
curl.exe -s -o NUL -w "%{http_code}`n" https://139.190.107.151.sslip.io/api/bots   # harus 401 tanpa token
```

Lalu di browser: buka situs, login, pastikan dashboard muncul, dan lakukan hard refresh (Ctrl+F5).
Bila health 200 tetapi tampilan lama, hard refresh; `index.html` dikirim `no-cache`.

## Troubleshooting

| Gejala | Tindakan |
|---|---|
| `deploy lain sedang berjalan` | Tunggu deploy lain selesai. Jangan hapus `/home/ubuntu/.deploy-pegawai-ai.lock` kecuali yakin tidak ada deploy berjalan. |
| `bukan bagian dari origin/main` | Merge/ push ke `main` dulu, lalu `git fetch origin` dan ulangi. |
| `origin/main tidak ditemukan` | Periksa `git remote -v` dan `git fetch origin`. |
| `kunci SSH tidak ditemukan` / auth gagal | Cek `-KeyPath`; uji `ssh -i ~/.ssh/pegawai-ai.pem ubuntu@139.190.107.151`. |
| `npm ci` / `npm run build` gagal | Cek Node/npm dan koneksi; jalankan `npm ci` di `frontend` untuk melihat galat. |
| `uji backend` gagal | Jalankan `uv run --frozen pytest -q` di `bff` dan perbaiki dulu. |
| `rilis ... sudah ada tetapi tidak utuh` | Periksa di server; hapus folder rilis itu **hanya bila bukan rilis aktif**, lalu ulangi. |
| Deploy gagal / health gagal | Server sudah mencoba rollback otomatis. Baca keluaran, cek `journalctl -u pegawai-ai-bff`, perbaiki, deploy ulang. |
| Unggahan terputus | Jalankan ulang; sisa `.upload-*.tar.gz` di `/home/ubuntu/releases/` boleh dihapus bila tidak ada deploy berjalan. |
| Tim melihat UI lama | Hard refresh (Ctrl+F5). Bila tetap, cek `/home/ubuntu/CURRENT_RELEASE` dan hash `index.html`. |

## Skrip lama: JANGAN dipakai lagi

Semua skrip di bawah menyalin kode/konfigurasi langsung ke server tanpa rilis, tanpa backup,
tanpa health check, dan tanpa rollback. Beberapa masih memuat kata sandi dalam teks biasa.
Berkasnya disimpan hanya sebagai riwayat; jangan dijalankan.

| Berkas | Kenapa ditinggalkan |
|---|---|
| `deploy_sprint5_day1.py` | SFTP beberapa berkas pilihan + dist; melewati rilis/backup/health. |
| `deploy_sprint5_day2.py` | Sama: unggah sebagian berkas langsung ke app dir. |
| `deploy_vps_day4.py` | SFTP beberapa berkas + restart manual; tanpa backup/rollback. |
| `redeploy_all_vps.py` | Unggah seluruh bff + dist langsung, tanpa rilis dan tanpa verifikasi. |
| `vps/deploy_day3_sprint5.py` | `upload_dir` via paramiko; menimpa app dir langsung. |
| `vps/deploy_day4_sprint5.py` | SFTP berkas pilihan langsung ke server. |
| `apply_security_hardening.py` | Mengubah UFW dan Nginx lewat SSH/SFTP; perubahan konfigurasi di luar alur deploy. |
| `vps/sync_frontend.py` | Unggah `dist` manual ke `/tmp` dengan path lokal lama; digantikan langkah frontend di rilis. |

Satu-satunya jalur deploy yang sah: `.\vps\deploy.ps1` (dan `-Rollback` bila perlu).

