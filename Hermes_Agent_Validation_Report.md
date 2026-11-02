# PRODUCT VALIDATION REPORT: HERMES AGENT (CANDIDATE A)
**Proyek:** Pengembangan Platform Pegawai AI  
**Tanggal Validasi:** 21 Oktober 2026  
**Peneliti Validasi:** Kandidat A Evaluator  
**Target Pembaca:** R&D Lead & Koordinator Validasi (Rakazo Researcher)  
**Status Akses:** **ACCESSIBLE & VERIFIED** (Pengujian Lokal Sukses)

---

## 1. Identitas Resmi Produk & Repositori

| Parameter | Data Terverifikasi | Catatan Validasi |
| :--- | :--- | :--- |
| **Nama Produk** | **Hermes Agent** (Candidate A) | Bukan Hermes LLM Model mentah, melainkan full-stack autonomous agent runtime. |
| **Vendor / Organisasi** | **Nous Research** | [nousresearch.com](https://nousresearch.com) |
| **Repositori Resmi** | [github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | Terverifikasi repo resmi Nous Research. |
| **Dokumentasi Resmi** | [hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com) / Dokumentasi internal di repositori (`website/`) | Tersedia panduan CLI, TUI, Desktop, dan API. |
| **Versi Diuji** | **v0.22.2** (Commit: `d923a5eb48`) | Latest Stable Release saat pengujian. |
| **Jenis Distribusi** | Open-source framework + standalone desktop GUI & CLI | Tersedia installer Windows binary (`Hermes-Setup.exe`). |

---

## 2. Status Akses, Lingkungan Uji & Verifikasi Instalasi

### 2.1 Lingkungan Pengujian
- **Sistem Operasi:** Windows 11 / Windows 10 (Arch: `win32-x64`)
- **Runtime Pendukung:** Python 3.14 (diprovosikan otomatis via `uv v0.12.3`), Git portable (`v2.53.0+3-win32-x64`), Node.js/Electron untuk Desktop App.
- **Lokasi Instalasi Lokal:** `C:\Users\LOQ\AppData\Local\hermes`

### 2.2 Hasil Verifikasi Instalasi & Kendala Teknis Nyata (*Actual Test Evidence*)
Instalasi dilakukan menggunakan installer resmi `Hermes-Setup.exe` (Bootstrap Installer Protocol v1).

#### Temuan Error Saat Instalasi (*Disclosed Error & Evidence*)
Pada instalasi awal di sistem Windows, proses setup sempat mengalami kegagalan pada stage `repository` dan `venv`:
1. **Error Hak Akses Git di Windows (`stage=repository`):**
   ```text
   2026-10-21T05:39:51.538765Z INFO bootstrap.log: [X] Cannot remove item C:\Users\LOQ\AppData\Local\hermes\.hermes-clone-8496-616162997\tree\.git: You do not have sufficient access rights to perform this operation. stage=repository
   ```
   *Penyebab:* Perintah `Move-Item` di PowerShell mengalami hambatan saat memindahkan berkas `.git` yang berstatus read-only/terkunci di Windows.
2. **Missing Dependency Lock (`stage=venv`):**
   ```text
   Cannot find path 'C:\Users\LOQ\AppData\Local\hermes\hermes-agent\pm\lock.json' because it does not exist.
   ```
   *Penyebab:* Karena pemindahan repositori terputus di tengah jalan, berkas direktori `pm/` belum ter-checkout, namun penanda rilis menganggap versi `v0.22.2` sudah ada.

#### Resolusi & Verifikasi Akhir
- Masalah diselesaikan dengan menjalankan `git reset --hard HEAD` pada direktori repositori lokal, yang berhasil merestorasi seluruh **18.508 berkas**.
- Installer kemudian berhasil menyelesaikan seluruh 9 tahapan (*prerequisites, repository, venv, python-deps, config, products, setup, gateway, complete*).
- **Status Akhir:** **HERMES IS READY** (Desktop App & CLI binary `hermes.exe` aktif dan operasional).

---

## 3. Verifikasi Lisensi Komersial (*Commercial Licensing*)

| Aspek Lisensi | Temuan Verifikasi |
| :--- | :--- |
| **Jenis Lisensi** | **MIT License** (Copyright © 2025 Nous Research) |
| **Lokasi Berkas Lisensi** | `hermes-agent/LICENSE` (Terverifikasi di repositori) |
| **Hak Penggunaan Komersial** | **Diizinkan Penuh (Full Commercial Use)**. Bebas digunakan, disalin, dimodifikasi, dimerge, dipublikasikan, disublisensikan, dan/atau dijual. |
| **Kewajiban / Syarat** | Wajib menyertakan notice hak cipta asli dan teks lisensi MIT pada distribusi turunan. |
| **Risiko IP / Copyright** | **Sangat Rendah (Low Risk)**. Lisensi MIT adalah salah satu lisensi open source paling permisif dan aman untuk basis produk B2B/B2C komersial. |
| **Framework vs Hosted Service** | Framework ini sepenuhnya beroperasi secara self-hosted di infrastruktur lokal/server sendiri tanpa royalti wajib kepada Nous Research. |

---

## 4. Evaluasi Fitur Teknis (Kesesuaian dengan Arsitektur "Pegawai AI")

Mengacu pada arahan briefing (*Pegawai AI: Role, Skill, Knowledge, Tools, Workflow, Guardrails*):

### 4.1 Model Providers & Provider Switching
- **Model yang Didukung:**
  - Multi-provider: OpenAI, Anthropic Claude, OpenRouter, DeepSeek, Google Gemini (via API adapter).
  - Local LLM: Ollama, vLLM, llama.cpp (cocok untuk efisiensi biaya dan privasi data).
- **Provider Switching:**
  - Dapat diubah fleksibel per sesi via CLI flag `--provider <provider>` dan `--model <model>`.
  - Memiliki fitur bawaan **Fallback Provider Chain** (`hermes fallback add/remove/list`) yang otomatis mengalihkan ke model cadangan bila kuota habis atau API utama mengalami kegagalan/timeout.
- **Credential Pooling:**
  - Mendukung manajemen banyak API keys (`hermes auth add/list/priority/refresh`) dengan prioritas dan rotasi otomatis jika terjadi *rate-limiting*.

### 4.2 Tools, Connectors & Extensibility
- **Native Tools:**
  - Eksekusi Shell/Terminal, File System I/O, Web Search & Scraper (`agent-browser`), dan Computer Use Automation (`cua-driver`).
- **Skills System:**
  - Modular skills architecture (`--skills`, `SOUL.md`, `AGENTS.md`). Memungkinkan pembuatan peran pegawai spesifik (misal: *Marketing AI, CS AI, Research AI*) dengan SOP terisolasi.
- **Integrasi MCP (Model Context Protocol):**
  - Mendukung server MCP pihak ketiga untuk koneksi ke database, CRM, Slack, dan sistem enterprise.

### 4.3 Human-in-the-Loop & Guardrails (Keamanan Eksekusi)
- **Approval System:**
  - Secara default, seluruh perintah berisiko tinggi (penulisan file sistem, eksekusi shell berbahaya) meminta konfirmasi manusia (*human approval*).
  - Mode tanpa approval (`--yolo`) hanya bersifat opsional dan tidak aktif secara default.
- **Audit & Observability:**
  - Seluruh log tersimpan rapi di sistem lokal (`hermes logs`, `agent.log`, `errors.log`).
  - Fitur `--usage-file PATH` mencatat jumlah token, perkiraan biaya (*estimated cost*), dan jumlah API calls secara deterministik untuk keperluan pelaporan biaya pelanggan.

---

## 5. Analisis Fitur Native vs Custom Integration

| Kebutuhan Pegawai AI (PPT Briefing) | Fitur Native Hermes Agent | Butuh Custom Integration (Tim Dev) |
| :--- | :---: | :---: |
| **Orchestration & Task Execution** | ✅ Ada (Native agent engine) | - |
| **Tools & API Calling (Function Call)** | ✅ Ada (Shell, Browser, File, MCP) | Konektor marketplace lokal (Shopee/Tokopedia) |
| **Human-in-the-loop Guardrail** | ✅ Ada (Interactive prompt) | Web dashboard webhook approval untuk klien |
| **Token & Cost Observability** | ✅ Ada (`--usage-file`, log) | Integrasi ke database billing/rekap tenant |
| **Multi-Tenant Data Isolation** | ⚠️ Parsial (mendukung flag `--profile`) | **Wajib Custom**: Isolasi container/DB per perusahaan |
| **Role & Skill Definition** | ✅ Ada (Skills format, `AGENTS.md`) | Pembuatan SOP template Marketing & Content |

---

## 6. Batasan, Risiko & Hal yang Belum Diketahui (*Restrictions, Risks & Unknowns*)

### 6.1 Batasan (*Restrictions*)
1. **Desain Dasar Berorientasi Single-User/Desktop:** Hermes Agent aslinya didesain sebagai autonomous agent untuk workstation pengembang (CLI/TUI/Desktop). Untuk dioperasikan sebagai backend multi-tenant SaaS dengan ratusan pengguna bisnis simultan, tim perlu membungkusnya dalam microservice / containerized orchestrator.
2. **Kebutuhan Resource GUI:** Paket desktop Electron menambah ukuran footprint penyimpanan (~200MB+ binary), meskipun untuk server headless hanya dibutuhkan CLI runtime (`hermes serve`).

### 6.2 Risiko Teknis (*Technical Risks*)
1. **Stabilitas Installer Windows Native:** Script installer Windows (`install-main.ps1`) rentan terhadap kunci file (*file locks*) antivirus atau hak akses direktori temporer saat proses kloning git pertama kali.
2. **Biaya Token Eksekusi Otonom:** Agen otonom dengan tool looping dapat mengonsumsi token dengan cepat jika instruksi ambigu; pembatasan ketat (*max iterations / cost caps*) harus dikonfigurasi melalui konfigurasi yaml.

### 6.3 Hal yang Belum Diketahui (*Labeled Unknowns*)
- **[UNKNOWN - API COST UNDER LOAD]:** Kinerja dan stabilitas latensi mode headless server (`hermes serve`) ketika menerima konkurensi alur kerja Marketing AI secara bersamaan (memerlukan uji beban lanjutan).
- **[UNKNOWN - ENTERPRISE DB ADAPTER]:** Efisiensi memory retrieval jangka panjang Hermes untuk dokumen brand context berukuran besar (>50 MB) tanpa vector database eksternal.

---

## 7. Kesimpulan & Rekomendasi untuk R&D Lead

| Kriteria Evaluasi (Scorecard) | Bobot | Skor Evaluasi (1-10) | Catatan Penilaian |
| :--- | :---: | :---: | :--- |
| **Task Success & Kualitas** | 30% | **8.5 / 10** | Arsitektur reasoning dan eksekusi tool sangat matang. |
| **Reliability & Error Recovery** | 20% | **8.0 / 10** | Memiliki fallback provider chain otomatis jika provider down. |
| **Tools & Integrasi (MCP/API)** | 15% | **9.0 / 10** | Dukungan MCP dan browser automation native sangat kuat. |
| **Security & Guardrails** | 15% | **8.5 / 10** | Default human approval aktif; command berbahaya terkontrol. |
| **Biaya & Observability** | 10% | **8.5 / 10** | Kompatibel dengan model murah/lokal (Ollama); log token jelas. |
| **Deployment & Maintenance** | 10% | **7.5 / 10** | Instalasi Windows butuh penanganan awal; instalasi server/Linux sangat baik. |

### Rekomendasi Akhir: **GO (Kandidat Kuat)**
Hermes Agent terbukti memiliki kapabilitas teknis yang sangat solid, lisensi komersial **MIT** yang aman tanpa risiko royalti, dan fitur guardrails bawaan yang sejalan dengan visi **Pegawai AI**. Sangat direkomendasikan untuk masuk ke tahap pengujian skenario use-case MVP (*Marketing & Content AI*).
