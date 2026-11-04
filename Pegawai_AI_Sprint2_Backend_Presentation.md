# Presentasi Laporan Teknis Sprint 2: Pegawai AI Backend PoC
**Perusahaan:** PT AI Top Trends  
**Presenter:** Intern 1 (Backend Lead & Technical Research)  
**Periode Sprint:** 29 Oktober – 3 November 2026  
**Workstation:** `LOQ-WIN11-DEV`  
**Deliverables Selesai:** S2-01A (Setup), S2-02A (Architecture & API), S2-03A (PoC), S2-04A (Validation)

---

## Slide 1: Judul Presentasi
* **Judul:** Pegawai AI — Digital Workforce Backend PoC
* **Subjudul:** Riset Teknis, Arsitektur Shared Backend, Orkestrasi Multi-Agent, & Validasi Integrasi Hermes Agent dengan Model DeepSeek V4.1 Flash via Opencode Zen.
* **Metadata Proyek:**
  - Role: Intern 1 (Backend Lead & Research)
  - Sprint: Sprint 2 Minimal Working PoC
  - Status: 100% Complete & Verified

---

## Slide 2: Latar Belakang & Sasaran Sprint 2 (Business Context)
### Problem Statement: Beban Operasional Repetitif
* **Burnout Tim Konten:** Tuntutan jadwal harian multi-kanal memangkas ruang berpikir kreatif dan menurunkan kualitas editorial naskah.
* **Respon CS di Luar Jam Kerja:** Keterbatasan staf manusia membuat tiket komplain tertunda hingga jam operasional berikutnya.
* **Pekerjaan Berulang UMKM:** Waktu tersita untuk mencatat pesanan manual, merekap nota, dan menjawab pertanyaan yang polanya sama.
* **Risiko Overpromising AI:** Perlunya sistem cerdas yang patuh pada SOP perusahaan, berwibawa, dan bebas dari janji palsu ("kaya instan").

### Sasaran Sprint 2: Minimal Working PoC
* **Shared Technical Foundation:** Membangun satu backend bersama yang dapat dipakai langsung oleh Intern 2 & 3 (Workflows) dan Intern 4 (Frontend).
* **Integrasi Hermes Engine:** Menghubungkan CLI Hermes Agent v0.22.2 ke model resmi DeepSeek V4.1 Flash via Opencode Zen.
* **Orkestrasi Multi-Agent Mandiri:** Pembagian peran otonom (Copywriter, QC Auditor, Visual Specialist, CS QA Lead) dengan audit kritis nyata.
* **Disiplin Batasan PoC:** Fokus validasi alur inti; infrastruktur produksi (Kubernetes, Redis, DB multi-tenant) sengaja ditangguhkan ke sprint berikutnya.

---

## Slide 3: Riset & Pemilihan Model (DeepSeek V4.1 Flash)
### Karakteristik & Keunggulan Model
* **Kecepatan Inferensi Tinggi:** Sangat responsif untuk pipeline multi-agent yang menghasilkan naskah panjang dan audit berlapis.
* **Efisiensi Token Optimal:** Biaya komputasi jauh lebih efisien untuk jendela konteks besar (teruji hingga 185k+ context tokens).
* **Penalaran Multi-Peran Kritis:** Mampu membedakan nada empati (Siti CS) dengan ketajaman audit SOP (Hendra QA) dalam satu alur sesi.
* **Disiplin Aturan Negatif:** Sangat patuh pada batasan larangan (larangan kata terlarang, larangan nama divisi internal, dan batas 80–180 kata).

### Verifikasi Resmi & Integritas Teknis
* **Identifier Model Resmi:** `deepseek-v4.1-flash` (Canonical: `deepseek/deepseek-v4.1-flash-1017`).
* **Upstream Provider:** Opencode Zen API melalui provider Hermes `opencode`.
* **Prinsip Anti-Substitusi:** Tidak ada tebakan nama model atau substitusi diam-diam; fallback Copilot hanya berstatus standby jika kredensial nihil.
* **Pengelolaan Kredensial Aman:** Kunci diinjeksi via `OPENCODE_ZEN_API_KEY` pada `.env` lokal yang terproteksi `.gitignore`.

---

## Slide 4: Arsitektur Shared Backend & Kontrak API
### Zero-Dependency Python Architecture
* **Single Shared Process:** Berjalan di atas `http.server` standar Python (`server.py:8080`) tanpa ketergantungan runtime eksternal.
* **Zero Dependency Hell:** Seluruh anggota tim dapat langsung menjalankan server hanya dengan perintah `python server.py` tanpa Docker atau Redis.
* **Alur 3-Tier Nyata:** Client (UI/CLI) &rarr; Shared Ingress Router &rarr; Hermes Agent Engine &rarr; DeepSeek Cloud Inference.
* **SOP Injection Otomatis:** Backend menyuntikkan dokumen SOP markdown divisi ke prompt secara dinamis sebelum diserahkan ke model.

### Spesifikasi Kontrak REST API
* `POST /api/v1/agent/execute`: Menerima payload tugas, routing divisi, dan mengembalikan output terstruktur 3 agen.
* `GET /health`: Memeriksa kesehatan server, ketersediaan biner Hermes, dan kredensial model aktif.
* `GET /api/v1/sops`: Menyediakan data panduan SOP (Marketing, Customer Support, Sales) ke frontend.
* `GET /api/v1/mocks/{name}`: 7 berkas mock JSON mandiri untuk pengujian frontend offline.
* **Standardisasi Run ID & Status:** Format ID `run_YYYYMMDD_HHMMSS_hex` dan status lifecycle (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`).

---

## Slide 5: Kolaborasi Tim & Team Enablement
### Dukungan untuk Frontend & Workflow Tim
* **7 Berkas Mock JSON Siap Pakai:** Disimpan di `mock_fixtures/` agar Intern 4 (Frontend) bisa langsung mendesain UI tanpa terhambat backend.
* **Struktur Output Modular:** Data respon multi-agent dikembalikan dalam array `multi_agent_data.agents` yang siap di-render menjadi kartu UI.
* **Integrasi Skrip Workflow:** Intern 2 (Marketing) dan Intern 3 (CS) dapat langsung menembak endpoint HTTP tanpa membuat subprocess wrapper duplikat.
* **Pemisahan Tanggung Jawab:** Intern 1 fokus menjaga stabilitas core backend, kontrak API, dan orkestrasi inferensi Hermes.

### Repository GitHub & Sanitasi Kredensial
* **Repository Terpusat:** Proyek backend shared template telah dipublikasikan ke GitHub: [faizgeorgie9/pegawai-ai-backend](https://github.com/faizgeorgie9/pegawai-ai-backend).
* **Panduan Setup Lengkap:** File `README.md` menyajikan instruksi step-by-step dari instalasi Python hingga eksekusi tugas.
* **Keamanan API Key:** File `.env` berisi kunci asli terbukti 100% diproteksi oleh `.gitignore` dan tidak bocor ke publik.
* **Distribusi Template Aman:** Rekan tim cukup menyalin `.env.example` dan memasukkan kredensial Opencode mereka masing-masing.

---

## Slide 6: Problem Solving & Blocker Management
### Tantangan Nyata yang Berhasil Diatasi
* **Blocker Kredensial (`BLK-S2-01A-01`):** Hermes CLI sempat gagal membaca provider Opencode Zen. Diatasi dengan auto-load env pada backend template.
* **Eliminasi Template Statis ("Kunci Jawaban"):** Prompt awal menyertakan contoh teks di instruksi sehingga jawaban selalu sama. Dirombak total menjadi instruksi dinamis bebas template.
* **Crash Encoding Windows (`charmap`):** Karakter Unicode dan emoji memicu crash di terminal Windows. Diatasi dengan penegasan encoding UTF-8 dan replace-error handling.
* **Penyesuaian Gateway Timeout:** Beban komputasi inferensi multi-agent memakan waktu >60 detik. Timeout dinaikkan ke 180 detik sehingga request berjalan stabil.

### Dampak Pembaruan Arsitektur
* **Audit Diana (QC) 100% Nyata:** Menghasilkan skor kepatuhan dinamis (88/100, 87/100) dan kritik tajam spesifik terhadap topik, bukan angka statis.
* **Evaluasi CS Hendra (QA Lead) Otonom:** Memeriksa kepatuhan batas 80–180 kata, mengevaluasi empati, dan menentukan status eskalasi tiket.
* **Banner Pillow Dinamis:** Mockup visual banner 1080x1080 px otomatis dirender dengan teks judul topik tugas pengguna, bukan gambar statis.
* **Zero Blocker Kritis:** Seluruh isu teknis diselesaikan tuntas tanpa kompromi pada integritas model DeepSeek V4.1 Flash.

---

## Slide 7: Live Demo AI & Guardrails SOP
### Divisi Pemasaran & Kreatif (3 Agen)
* **✍️ Rian (Copywriter):** Menulis naskah AIDA lengkap, mengangkat empati pemilik UMKM, transparansi janji penawaran, dan 7 tagar resmi.
* **🔍 Diana (QC Auditor):** Mengaudit brand voice (rendah hati & otoritatif), filter kata terlarang (anti janji instan), dan memberi Skor QC 88/100.
* **🎨 Budi (Visual Specialist):** Merancang konsep visual fotografi meja kerja kayu UMKM, palet warna (`#14433B`, `#F3E9D2`), dan prompt Midjourney v6.
* **Banner Otomatis:** Generator grafis Pillow otomatis merender file PNG 1080x1080 px siap unduh di server.

### Divisi Customer Support (2 Agen)
* **💬 Siti (Frontline CS):** Menghasilkan draf balasan resmi 162 kata (patuh batas 80–180 kata), empati tinggi, 3 langkah konkrit, dan pengingat keamanan OTP.
* **🛡️ Hendra (CS QA Lead):** Mengaudit draf Siti, memberikan Skor QA 91/100, dan menetapkan status eskalasi `BUTUH_MONITORING`.
* **Kepatuhan Komunikasi:** Bersih dari janji hasil yang belum pasti, tidak menyebut divisi internal (Billing/Legal), dan tidak berhalusinasi resi palsu.
* **Human-in-the-Loop:** Stempel resmi memastikan draf harus ditinjau manusia sebelum dipublikasikan/dikirim ke pelanggan.

---

## Slide 8: Metrik Kinerja, Limitasi, & Roadmap Sprint 3
### Telemetri Kinerja Riil POC
* **Durasi Eksekusi:** Rata-rata 48 detik (Marketing 3 agen) hingga 91 detik (Customer Support 2 agen komprehensif).
* **Penggunaan Token:** Tercatat riil 19,967 tokens (Marketing) hingga 185,135 context tokens (Customer Support).
* **Keandalan Eksekusi:** Exit code 0 pada seluruh pengujian representatif Day 3 dan Day 4 tanpa server crash.
* **Validasi Error Cepat:** Validasi input 400 Bad Request berhasil menghentikan payload tidak lengkap tanpa membuang kuota token.

### Limitasi POC & Rencana Sprint 3
* **Limitasi 1 (Single Process):** Backend berbasis synchronous http.server; memadai untuk PoC lokal, butuh migrasi ASGI/FastAPI di fase produksi.
* **Limitasi 2 (Isolasi Tenant Sintetis):** ID pelanggan dan otentikasi token masih statis; database multi-tenant ditangguhkan.
* **Rencana Sprint 3 (`S3-02C`):** Implementasi Retry Mechanism & Circuit Breaker untuk menangani kegagalan jaringan secara mandiri.
* **Rencana Sprint 3 (`S3-01D`):** Tracking biaya token mendalam dan integrasi streaming Server-Sent Events (SSE) pada UI.
