# LAPORAN EKSPLORASI FITUR & ANALISIS BIAYA: HERMES AGENT (DAY 3)
**Kandidat:** A - Hermes Agent (Nous Research)  
**Versi:** `v0.22.2` (Commit: `d923a5eb48`)  
**Tanggal Pengujian:** 26 Oktober 2026  
**Peneliti:** Candidate A Researcher  
**Target Pembaca:** R&D Lead & Tim Pegawai AI  
**Alokasi Waktu Uji Coba:** 5 Jam (3 jam Fitur, 1 jam Biaya, 1 jam Pelaporan)  

---

## 1. Matriks Pengujian Fitur Inti (*Core Feature Exploration*)

Setiap fitur diuji dengan skenario nyata dan diverifikasi bukti terminalnya:

| No | Area Fitur (*Feature Item*) | Status | Kategori Implementasi | Bukti Output & Catatan Pengujian |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **Multi-step Execution & File I/O** | **PASS** | **Native** | Agen menerima instruksi membuat file `employee_profile.json`, membacanya, dan menghitung cost per lead. Output: `Cost per lead: 5.00` (Exit code 0). |
| **2** | **Persistent Context & Session Lineage** | **PASS** | **Native** | Sesi tersimpan otomatis di SQLite (`state.db`). Saat di-resume via flag `--resume <id>`, agen sukses mengingat data angka budget (`500`) dari sesi sebelumnya. |
| **3** | **LLM / Provider Switching** | **PASS** | **Native** | Fleksibel ganti provider (Copilot, OpenRouter, Anthropic, Ollama lokal) via CLI/config dan mendukung **Fallback Chain** otomatis. |
| **4** | **Error Handling & Observability** | **PASS** | **Native** | Perintah `hermes logs` mencatat pesan masuk, latensi API (2.8s), cache hit rate (99%), dan opsi `--usage-file` mencatat total 34.566 tokens. |
| **5** | **Scheduling & Restart Behavior** | **PASS** | **Native** | Background messaging gateway aktif (`hermes gateway status`, PID: 15632) dan mendukung instalasi Windows Scheduled Task (`hermes gateway install`). |
| **6** | **Human Approval Controls (Guardrails)** | **PASS** | **Native** | Konfirmasi interaktif aktif secara default (`confirm_dangerous_commands: true`). Perintah bahaya diblokir kecuali disetujui pengguna. |
| **7** | **Skills & Custom Persona** | **PASS** | **Native** | Mendukung 51+ modular skills, file persona `SOUL.md`, dan injeksi aturan `AGENTS.md` per workspace. |
| **8** | **Browser Operations (Web Research)** | **PASS** | **Native Toolset** | Memiliki toolset native `browser-use` dan `web` (1.9 KB - 3.2 KB schema) untuk scraping dan ekstraksi web. |
| **9** | **Visual Computer Use (CUA)** | **PARTIAL** | **Third-Party / OS Dep** | Toolset `computer-use` tersedia (18 KB schema), namun membutuhkan display aktif dan instalasi driver visual tambahan untuk kontrol mouse/keyboard OS. |
| **10** | **Multi-Tenant Deployment Isolation** | **BLOCKED (N/A Native)** | **Butuh Custom Code** | Hermes aslinya berbasis workstation/single-user (`state.db` tunggal). Belum ada fitur pemisahan database antar-klien bisnis secara bawaan. |

---

## 2. Analisis Biaya Awal Operasional (*Initial Cost Analysis*)

*Catatan: Sesuai aturan evaluasi, angka yang belum memiliki kontrak harga tetap dilabeli `ESTIMATE`, data tanpa biaya berbayar dilabeli `PROVISIONAL`.*

### 2.1 Rincian 5 Kategori Biaya Operasional

| Kategori Biaya | Komponen & Rincian | Estimasi Biaya (USD) | Tipe Biaya / Status |
| :--- | :--- | :---: | :---: |
| **1. Software License** | Lisensi Hermes Agent (Nous Research MIT License). Bebas royalti komersial. | **$0.00** | **SOURCED** (Resmi Open Source) |
| **2. LLM / API Usage** | Berdasarkan pengujian Day 2 & Day 3, rata-rata konsumsi per multi-step task adalah **~30.000 tokens** (karena bootstrap 21 tools & prompt 55 KB). Model `gpt-4o` ($2.5/1M in, $10/1M out) = **~$0.08 / task**. Untuk 1.000 tugas bulanan = **~$80.00 / bulan**. | **~$80.00 / bln** | **ESTIMATE** (Berdasarkan pengukuran token nyata) |
| **3. Infrastructure / Hosting** | Cloud VPS / Server (AWS EC2 / DigitalOcean 4 vCPU, 8GB RAM, SSD 50GB) untuk menjalankan container Docker `hermes serve` dan gateway. | **~$48.00 / bln** | **ESTIMATE** (Tarif pasar Cloud VPS 2026) |
| **4. Optional Managed Services** | Web Search API (Tavily / Serper API) untuk riset pasar otomatis: 1.000 query/bulan (free tier s/d paket $15). | **~$10.00 / bln** | **ESTIMATE** |
| **5. Local Model Alternative** | Jika menggunakan model lokal (Ollama Llama-3.1-70B): Biaya API $0, namun butuh VPS GPU Dedicated (~$150/bln). | **$0 API ($150 GPU)** | **PROVISIONAL** |

**Total Proyeksi Biaya Operasional Awal (Cloud API Track):** **~$138.00 / bulan** (untuk kapasitas ~1.000 pekerjaan Pegawai AI per bulan).

---

## 3. Log Batasan Teknis & Remediasi (*Technical Limitations Log*)

1. **Ukuran Base System Prompt Sangat Besar (55 KB / 21 Tools):**
   - *Temuan:* Hasil `hermes prompt-size` membuktikan sistem prompt dan skema 21 tool bawaan memakan 55 KB.
   - *Dampak:* Model berkonteks kecil (<64k) ditolak. 
   - *Estimasi Upaya Remediasi:* Rendah (cukup filter toolset yang tidak dipakai via flag `-t` / konfigurasi untuk menghemat token).
2. **Ketiadaan Isolasi Multi-Tenant Bawaan:**
   - *Temuan:* Database `state.db` bersifat global untuk semua sesi lokal.
   - *Dampak:* Klien bisnis A berpotensi mengakses sesi Klien B jika dijalankan di satu server tanpa isolasi.
   - *Estimasi Upaya Remediasi:* Sedang (~3-5 hari kerja tim dev untuk membungkus Hermes dalam Docker container per-tenant).

---

## 4. Keputusan yang Dibutuhkan dari R&D Lead (*Lead Decisions Needed*)

1. **Persetujuan Model LLM Standar:** Apakah disetujui menetapkan `gpt-4o` atau `claude-3.5-sonnet` sebagai model standar pengujian alur kerja, mengingat model kecil (`gpt-4o-mini`) tidak didukung oleh framework?
2. **Persetujuan Strategi Hosting:** Apakah tim R&D menyetujui pendekatan **Docker Containerization** untuk pemisahan data pelanggan pada arsitektur SaaS Pegawai AI?

---

## 5. Rekomendasi Prioritas Day 4 (*Day 4 Priorities*)
1. Membangun dan menguji skenario nyata **Use Case MVP: Marketing & Content AI** (Input Brief -> Riset Tren -> Pembuatan Draf Konten Multi-Platform -> Quality Check).
2. Mengukur latensi menyeluruh (*end-to-end turnaround time*) dari satu siklus produksi konten pemasaran.
