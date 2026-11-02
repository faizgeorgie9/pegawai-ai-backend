# HERMES AGENT SETUP GUIDE & REPRODUCIBILITY MANUAL (TASK 2)
**Kandidat:** A - Hermes Agent (Nous Research)  
**Versi Terverifikasi:** `v0.22.2`  
**Platform Target:** Windows 11 / Windows 10 (win32-x64)  
**Peneliti:** Candidate A Researcher  
**Target Pembaca:** R&D Lead & Tim Pengembang Pegawai AI  

---

## 1. Prasyarat Sistem & Dependensi (*Prerequisites*)

Sebelum memulai instalasi, pastikan sistem memenuhi spesifikasi minimal berikut:
- **Sistem Operasi:** Windows 10/11 64-bit (x64) atau Linux/macOS.
- **Git for Windows:** Git versi 2.40+ (disarankan mengaktifkan opsi *longpaths support*).
- **PowerShell:** Windows PowerShell 5.1 atau PowerShell 7 Core.
- **Python Package Manager:** Dikelola otomatis oleh `uv` (v0.12.3+). Python 3.14 diprovosikan mandiri tanpa mengganggu instalasi Python sistem.
- **Koneksi Internet:** Diperlukan untuk proses bootstrap unduhan Git release dan model dependencies.

---

## 2. Langkah-Langkah Instalasi Lengkap (*Step-by-Step Installation*)

### Langkah 2.1: Unduh Installer Resmi
Unduh file installer resmi `Hermes-Setup.exe` dari repositori atau portal rilis Nous Research ([github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)). Simpan di direktori kerja, misalnya `D:\ai_developer\project6\Hermes-Setup.exe`.

### Langkah 2.2: Jalankan Bootstrap Installer
Klik dua kali `Hermes-Setup.exe` atau jalankan via terminal:
```powershell
Start-Process "D:\ai_developer\project6\Hermes-Setup.exe"
```
Installer akan menjalankan 9 tahap otomatis:
1. `prerequisites` (Pemeriksaan Git & arsitektur host)
2. `repository` (Kloning repositori NousResearch/hermes-agent)
3. `venv` (Penyediaan Python terisolasi via Astral `uv`)
4. `python-deps` (Instalasi paket dependensi sesuai `uv.lock`)
5. `config` (Penyusunan konfigurasi dasar)
6. `products` (Penyediaan binary CLI & Desktop App)
7. `setup` (Inisialisasi wizard profil)
8. `gateway` (Konfigurasi background messaging gateway)
9. `complete` (Verifikasi akhir instalasi)

---

## 3. Catatan Masalah Instalasi & Solusi Reproduksinya (*Troubleshooting & Gotcha*)

> [!IMPORTANT]
> **Kendala Nyata Windows & Cara Mengatasinya:**
> Pada instalasi di OS Windows, installer dapat mengalami hambatan izin berkas saat memindahkan direktori `.git` sementara:
> ```text
> [X] Cannot remove item ...\.hermes-clone-xxxx\tree\.git: You do not have sufficient access rights.
> [X] Cannot find path '...\hermes-agent\pm\lock.json' because it does not exist. stage=venv
> ```
> 
> **Solusi Pemulihan yang Terbukti (*Verified Recovery*):**
> 1. Buka PowerShell dan arahkan ke repositori hermes yang baru dibuat:
>    ```powershell
>    cd "$env:LOCALAPPDATA\hermes\hermes-agent"
>    git reset --hard HEAD
>    ```
>    *Perintah ini akan memulihkan 18.508 file yang tertinggal/belum ter-checkout.*
> 2. Klik tombol **`Retry install`** pada jendela installer Hermes.
> 3. Instalasi akan langsung berstatus **"HERMES IS READY"**.

---

## 4. Konfigurasi Kredensial & Secrets yang Aman (*Safe Configuration*)

Untuk mencegah kebocoran API Key ke repositori publik/tim:
1. **Salin Template Environment:**
   ```powershell
   Copy-Item "task 2\.env.example" "$env:LOCALAPPDATA\hermes\.env"
   ```
2. **Isi API Key di `$env:LOCALAPPDATA\hermes\.env`:**
   ```dotenv
   OPENROUTER_API_KEY="sk-or-v1-xxxxxxxx"
   ANTHROPIC_API_KEY="sk-ant-xxxxxxxx"
   ```
3. **Konfigurasi Model & Guardrail (`config.yaml`):**
   Salin pengaturan dari `task 2\config.example.yaml` ke `$env:LOCALAPPDATA\hermes\config.yaml`.
   - Pastikan `confirm_dangerous_commands: true` tetap aktif (*Human-in-the-loop*).
   - Jangan aktifkan `yolo_mode` pada server produksi.

---

## 5. Lokasi Berkas & Binary yang Terpasang

- **CLI Binary:** `C:\Users\<User>\AppData\Local\hermes\bin\hermes.exe`
- **Desktop GUI:** `C:\Users\<User>\AppData\Local\hermes\hermes-agent\apps\desktop\release\win-unpacked\Hermes.exe`
- **Konfigurasi:** `C:\Users\<User>\AppData\Local\hermes\config.yaml`
- **Kredensial:** `C:\Users\<User>\AppData\Local\hermes\.env` dan `auth.json`
- **Log Sistem:** `C:\Users\<User>\AppData\Local\hermes\logs\agent.log`

---

## 6. Verifikasi Instalasi (*Health Check*)

Jalankan perintah berikut di PowerShell untuk memastikan binary aktif:
```powershell
& "$env:LOCALAPPDATA\hermes\bin\hermes.exe" config
```
Jika konfigurasi, path database, dan daftar provider tampil dengan normal, maka environment Hermes Agent telah siap untuk menjalankan tugas.
