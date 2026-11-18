# PANDUAN & NASKAH PRESENTASI: PERSIAPAN & DEPLOYMENT VPS PEGAWAI AI

**File Presentasi:** `Pegawai_AI_VPS_Preparation_and_Deployment_Presentation.pptx`  
**Presenter:** Faiz Febriawan (Backend Engineer)  
**Target Audiens:** Lead & Mentor  
**Waktu Pelaksanaan:** November 2026 (Sprint 4: MVP Readiness)  
**Target Server:** Biznet Gio Cloud NEO Lite MS 4.4 (`139.190.107.151`)  

---

## Struktur 9 Slide & Catatan Presenter (Speaker Notes)

### 📌 Slide 1: Judul Presentasi (Title Slide)
- **Judul:** Laporan Persiapan & Deployment VPS Pegawai AI
- **Subjudul:** Infrastruktur Cloud, Hermes Core v0.23+, Multi-Agent & Integrasi WhatsApp CS
- **Poin Kunci:** Transisi sukses dari lingkungan lokal ke server cloud produksi Biznet Gio (139.190.107.151).
- **💡 Naskah Pembuka (Speaker Notes):**
  > *"Selamat pagi/siang rekan-rekan, Lead, dan Mentor. Hari ini saya ingin mempresentasikan pencapaian pengerjaan infrastruktur backend Pegawai AI, yaitu migrasi penuh dan deployment platform kita ke VPS Cloud Biznet Gio. Presentasi ini akan merangkum arsitektur sistem, otomasi multi-agent, penanganan gateway WhatsApp CS, hingga stabilitas server yang kini sudah live dan siap digunakan."*

---

### 📌 Slide 2: Executive Summary (Masalah $\rightarrow$ Eksekusi $\rightarrow$ Hasil)
- **1. Kebutuhan & Tantangan:**
  - *Localhost Terbatas:* Sebelumnya aplikasi berjalan di laptop lokal pengembang, sehingga mentor, QA, dan stakeholders sulit menguji secara langsung.
  - *Ketergantungan Perangkat:* Jika laptop mati atau koneksi putus, seluruh bot AI dan webhook berhenti bekerja.
  - *Integrasi Eksternal:* Webhook WhatsApp Business (Meta) membutuhkan IP publik / URL cloud yang aktif 24/7.
- **2. Eksekusi yang Dilakukan:**
  - Provisi VPS Biznet Gio NEO Lite MS 4.4 (Ubuntu 22.04 LTS, 4 vCPU, 4GB RAM).
  - Pemasangan Hermes Core v0.23+ dan FastAPI BFF sebagai background service otomatis (systemd).
  - Konfigurasi Nginx Reverse Proxy dengan injeksi header keamanan API.
  - Koneksi database terpusat ke Neon Serverless PostgreSQL dengan pool recycling.
- **3. Dampak & Hasil Nyata:**
  - Server live 24/7 di `http://139.190.107.151/`.
  - 7 agen AI aktif serentak (5 Marketing + 2 CS).
  - WhatsApp Gateway aktif dengan Web Simulator interaktif (`/wa-tester.html`).
  - Pemakaian sumber daya sangat efisien: RAM ~5-7%, CPU Load <0.4.

---

### 📌 Slide 3: Arsitektur Sistem Produksi di VPS
- **Layer 1: Ingress & Reverse Proxy (Nginx Port 80):**
  - Gerbang tunggal di IP `139.190.107.151`.
  - Melayani static assets Vite frontend (`/var/www/pegawai-ai`) dan mem-proxy `/bff/` ke port 8090 dengan auto-injeksi header `X-Pegawai-AI-Key`.
- **Layer 2: Backend For Frontend (FastAPI Port 8090):**
  - Dikelola oleh `pegawai-ai-bff.service`.
  - Menangani REST API, SSE streaming, task scheduling, token cost tracking (USD), dan WhatsApp routing.
- **Layer 3: AI Agent Runtime Core (Hermes Gateway Port 8642):**
  - Dikelola oleh `hermes-gateway.service`.
  - Menjalankan engine multi-agent v0.23+ dengan model penalaran DeepSeek V4.1 Flash via provider OpenCode.
- **Layer 4: Data & Persistence Layer (Neon Cloud PostgreSQL):**
  - 19 file migrasi aktif (termasuk `019_whatsapp_messages.sql`).
  - Menggunakan connection recycling (`max_idle=300`) agar kebal terhadap idle disconnection serverless.

---

### 📌 Slide 4: Detail Provisi & Ketahanan Layanan (Systemd & Nginx)
- **Provisi Lingkungan:**
  - Ubuntu 22.04 LTS diprovisi via package manager modern `uv` (v0.13+).
  - Hermes Agent vgit.27e3893 terpasang dengan Python 3.14 dan OpenAI SDK 2.54.0.
  - Build frontend Vite dikompilasi di lokal dan dideploy bersih ke direktori web.
- **Ketahanan Layanan (Self-Healing):**
  - `hermes-gateway.service`: `Restart=always`, jeda restart 3 detik.
  - `pegawai-ai-bff.service`: Memastikan FastAPI selalu menyala otomatis saat server boot.
  - Skrip deployment mandiri (`redeploy_vps.py` & `deploy_vps_day4.py`) memungkinkan pembaruan kode tanpa interupsi manual.

---

### 📌 Slide 5: Konfigurasi 7 Bot Colorbox Resmi
- **5 Bot Tim Pemasaran (Marketing R&D):**
  1. **Bimo (Lead Strategist):** Roadmap kampanye & alokasi anggaran Colorbox.
  2. **Meda (Social Media Lead):** Tren viral TikTok/Reels & kalender konten.
  3. **Raka (Copywriter & Content):** Formula AIDA & gaya bahasa santai Gen-Z.
  4. **Bram (SEO & Performance):** Optimasi kata kunci e-commerce & tracking konversi.
  5. **Vina (Creative & Visual Designer):** Estetika pastel/earthy & arahan desain.
- **2 Bot Customer Service (CS Resmi):**
  1. **Siti (Frontline Support):** Menjawab stok, ukuran baju (XS-XL), dan resi secara ramah (*"Halo Kak... 💕"*).
  2. **Hendra (CS Team Lead & Quality Auditor):** Menangani eskalasi komplain P1 (barang robek/retur) dan audit kepatuhan SOP 7 hari.
- **Grounding Kebijakan Resmi:**
  - Penukaran maksimal 7 hari kalender.
  - Wajib video unboxing & barcode tag utuh.
  - Dilarang keras mengarang garansi di luar SOP.

---

### 📌 Slide 6: Integrasi WhatsApp CS & Simulator Interaktif
- **Standar Webhook Meta Cloud API:**
  - Handshake verifikasi token: `GET /api/whatsapp/webhook`.
  - Penerima pesan real-time: `POST /api/whatsapp/webhook`.
  - Persistensi audit di database `whatsapp_messages`.
- **Routing Engine Cerdas:**
  - Pertanyaan produk / panduan ukuran $\rightarrow$ **Siti** (P3).
  - Komplain cacat / robek / retur $\rightarrow$ **Hendra** (P1 - Eskalasi).
- **Web Simulator Interaktif (`/wa-tester.html`):**
  - Mentor dan lead dapat langsung mencoba simulasi chat WhatsApp di browser tanpa perlu setup HP.
  - Menampilkan badge agen yang membalas, prioritas, dan intent pesan secara transparan.

---

### 📌 Slide 7: Konektor Tools Pihak Ketiga & Troubleshooting
- **Konektor Tools:**
  - Google Drive & Gmail via OAuth 2.0 (token terenkripsi Fernet `CONNECTIONS_KEY`).
  - Notion via Hermes Nous Portal Connectors.
  - Seluruh 54 aplikasi eksternal aktif di halaman `#/aplikasi`.
- **Troubleshooting Bug 503:**
  - *Kendala:* Muncul pesan *"Daftar aplikasi belum bisa dimuat"* saat membuka menu Aplikasi.
  - *Akar Masalah:* Shell script lama di `/home/ubuntu/.local/bin/hermes` mendahului binary resmi Hermes.
  - *Solusi:* Memperbarui symlink ke `/usr/local/bin/hermes`.
  - *Hasil:* Endpoint `GET /api/apps/catalog` langsung merespons **200 OK** dengan 54 aplikasi lengkap.

---

### 📌 Slide 8: Metrik Performa & Bukti Validasi Pengujian
- **Metrik Utama Server:**
  - **257 Unit Tests:** 100% Passed (termasuk 10 test case khusus WhatsApp).
  - **RAM 5.2%:** Sangat efisien, hanya memakai ~210MB dari 4GB kapasitas.
  - **CPU Load 0.36:** Performa responsif tanpa lonjakan beban.
  - **Zero Downtime:** Daemon systemd menjamin layanan selalu online.
- **Validasi Endpoint Live:**
  - `GET /` $\rightarrow$ Web frontend aktif.
  - `GET /bff/api/whatsapp/status` $\rightarrow$ Status ready.
  - `GET /bff/api/tools/integrations` $\rightarrow$ 4 tools terdaftar.
  - `GET /bff/api/apps/catalog` $\rightarrow$ 54 tools eksternal aktif.

---

### 📌 Slide 9: Kesimpulan & Rencana Selanjutnya (Next Steps)
- **Kesimpulan:**
  - Lingkungan VPS Biznet Gio telah terkonfigurasi secara matang, aman, dan siap produksi (*production-ready*).
  - Seluruh target Sprint 4 Day 1 s.d. Day 4 telah tuntas 100%.
- **Rencana Selanjutnya (Next Actions):**
  - Mengaktivasi nomor WhatsApp bisnis asli (input token & Phone Number ID Meta).
  - Memasang domain resmi & sertifikat SSL HTTPS.
  - Menyelesaikan Sprint 4 Day 5 (Final End-to-End Testing & UAT bersama tim internal).
