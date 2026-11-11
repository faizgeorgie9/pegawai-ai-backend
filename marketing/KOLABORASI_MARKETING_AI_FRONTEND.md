# LAPORAN KOLABORASI: INTEGRASI BASIS PENGETAHUAN MARKETING DENGAN AI FRONTEND
**Proyek R&D Hermes AI Employee — Kasus Studi: Colorbox Indonesia (PT Delami Garment Industries)**  
**Target Distribusi:** Tim Marketing, Tim Backend Engineering (Team 3), & Tim Frontend Engineering (Team 4)  
**Tanggal Rilis:** 9 November 2026 | **Status:** Terverifikasi & Aktif (Live Testing Ready)

---

## 1. Ringkasan Eksekutif & Konteks Kolaborasi

Sesuai dengan mandat **Product Requirement Document (PRD) Bagian 6 (Shared Business Knowledge Hub)** dan **Dokumen Handover Spesifikasi Teknis**, telah dilakukan kolaborasi dan integrasi menyeluruh antara **Paket Pengetahuan Bisnis Colorbox** (yang disediakan di folder `marketing/`) dengan **Sistem AI Frontend & BFF Backend** yang telah aktif beroperasi.

Kolaborasi ini menghubungkan sumber kebenaran data tunggal (*Single Source of Truth*) hasil riset pasar dan observasi resmi Colorbox ke dalam agen otonom Hermes yang dapat diakses langsung oleh tim melalui antarmuka web interaktif di **`http://localhost:5173/`**.

```
┌────────────────────────────────────────────────────────────────────────┐
│               SHARED BUSINESS KNOWLEDGE HUB (Folder: marketing/)       │
│  brand-profile.md │ brand-guidelines.md │ content-pillars.md │ ...     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Ingest & Grounding
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│            HERMES AGENT MULTI-PROFILE GATEWAY (Port 8642)              │
│   Rian (Copywriting) │ Diana (QC Auditor) │ Budi (Visual Designer)    │
│   Siti (CS Frontline) │ Hendra (CS Team Lead)                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ REST / SSE API (/v1/runs)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               BACKEND FOR FRONTEND / BFF (Port 8090)                   │
│   FastAPI Server │ Neon PostgreSQL Pool │ Token & Quota Manager       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Vite Proxy (/bff/api)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│              FRONTEND AI TESTING INTERFACE (Port 5173)                 │
│  Marketing 5-Stage Workspace │ Chat Bebas │ Runner Evaluasi Uji       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Inventarisasi & Pemetaan 10 Berkas Pengetahuan Bisnis

Seluruh berkas pengetahuan di folder `marketing/colorbox-knowledge/` telah dipetakan dan diintegrasikan ke sistem AI:

| Nama Berkas (.md) | Peruntukan Agen | Klasifikasi Data | Peran & Integrasi Teknis |
| :--- | :--- | :--- | :--- |
| **`brand-profile.md`** | Marketing & CS | Public Data | Profil berdirinya brand (1993), Delamibrands, filosofi *fun* & *effortless self-expression*. |
| **`brand-guidelines.md`** | Marketing & CS | Public Data | *Tone of voice* santai, sapaan "Babes/Besties", 3 pilar gaya busana (**Urban, Romantic, Chic**), aturan nol klaim palsu. |
| **`content-pillars.md`** | Marketing | Research Findings | Payung kampanye *"Never Just One Thing"*, 4 pilar editorial (Self-Expression, Styling Mix & Match, New Drops, Community). |
| **`content-research.md`** | Marketing | Research Findings | Format Reels/TikTok vertikal, pola hook keresahan Gen-Z, panduan lookbook pencahayaan daylight alami. |
| **`product-catalog.md`** | Marketing & CS | Public Data | Indeks terstruktur 1.206 produk resmi untuk pencarian item spesifik tanpa membebani context window. |
| **`product-size-reference.md`** | Customer Service | Public Data | Standar ukuran atasan (XS–XL) dan celana denim (Size 26–32) untuk panduan fitting. |
| **`business-policies.md`** | Customer Service | Public Data | SOP retur 7 hari, syarat video unboxing utuh, kebijakan *refund-only* (tanpa tukar barang fisik). |
| **`customer-faq.md`** | Customer Service | Public Data | FAQ metode pembayaran, estimasi ekspedisi JNE (48 jam gudang), layanan *Click & Collect*. |
| **`customer-inquiry-patterns.md`** | Customer Service | Findings / Sim | Klasifikasi 7 niat belanja pelanggan, draf eskalasi komplain, dan mitigasi risiko. |
| **`source-register.md`** | Tata Kelola / QA | Governance | Audit trail 10 sumber data resmi (SRC-01 s/d SRC-10) untuk verifikasi akuntabilitas. |

---

## 3. Grounding Persona Agen AI Marketing

Profil agen AI di Hermes telah di-update secara permanen dengan pengetahuan Colorbox:

### A. Rian (`rian`) — Copywriting Specialist
- **Fokus:** Penulisan naskah iklan, caption media sosial Instagram/TikTok, formula AIDA, dan variasi hook.
- **Karakter & Gaya:** Kasual, ramah, energik, menyapa audiens dengan "Babes" atau "Besties".
- **Kepatuhan:** Menerapkan payung tema *"Never Just One Thing"*, membedakan antara usulan gaya kreatif dengan fakta katalog, serta tidak mengarang diskon atau bahan pakaian.

### B. Diana (`diana`) — Creative Director & QC Auditor
- **Fokus:** Mengaudit draf naskah dari Rian dan arahan visual dari Budi.
- **Rubrik 9 Dimensi Mutu PRD (Skala 1–5):**
  1. *Akurasi & Keandalan Fakta* (anti-halusinasi)
  2. *Relevansi & Kecocokan Audiens* (keselarasan Gen-Z)
  3. *Kesesuaian Brand* (DNA fun & effortless)
  4. *Konsistensi Nada & Gaya*
  5. *Pemakaian Knowledge* (ketepatan pilar Urban/Romantic/Chic)
  6. *Kepatuhan Format & Instruksi*
  7. *Kelengkapan & Kejelasan*
  8. *Penanganan Error & Batasan*
  9. *Kebutuhan Review Manusia*
- **Aturan Revisi:** Maksimal 2 putaran revisi dengan catatan perbaikan yang tajam dan terukur.

### C. Budi (`budi`) — Visual Designer & Art Director
- **Fokus:** Konsep visual lookbook, rekomendasi palet warna (pastel, warm earth tone, bold accents), dan penyusunan prompt detail bahasa Inggris untuk AI Image Generator (DALL-E / Midjourney).
- **Estetika:** Pencahayaan daylight alami, lokasi urban street / kafe modern, pose effortless natural.

---

## 4. Implementasi Alur 5 Tahap Marketing di Frontend

Kolaborasi ini langsung terhubung dengan komponen **Marketing Workspace** di Frontend (`http://localhost:5173/#/marketing`):

```
[Tahap 1: Brief] ──► [Tahap 2: Rencana] ──► [Tahap 3: Konten] ──► [Tahap 4: Review] ──► [Tahap 5: Revisi]
  Form terstruktur      Creative brief &      Naskah AIDA &          Audit 9 dimensi       Draf ter-update
   + Verifikasi          Kalender 3 hari       Alternatif angle       oleh Diana (QC)      + Prompt visual
   Kelayakan            (Urban/Chic/Rom)      oleh Rian              (Skor 1-5)            oleh Budi
```

1. **Tahap 1 (Brief):** Memvalidasi tujuan, audiens target, kanal, dan batasan klaim (misal: "tanpa klaim diskon").
2. **Tahap 2 (Rencana):** Agen menyusun konsep kreatif bernomor dan kalender publikasi terencana.
3. **Tahap 3 (Konten):** Rian memproduksi naskah AIDA lengkap dengan hook keresahan Gen-Z dan tagar resmi `#NeverJustOneThing #ColorboxBabes`.
4. **Tahap 4 (Review):** Diana memeriksa naskah terhadap 9 dimensi mutu dan memberikan masukan objektif.
5. **Tahap 5 (Revisi):** Rian memperbarui draf sesuai feedback, sementara Budi melengkapi konsep visual lookbook dan prompt foto.

---

## 5. Pemisahan Data & Kepatuhan PRD (Anti-Halusinasi)

Mengacu pada prinsip inti PRD Bagian 14 (*"Separate Facts from Simulations"*), setiap hasil keluaran AI dikelompokkan dengan penandaan transparan:
- **`[Public Data]`**: Fakta terverifikasi dari website resmi (pilar Urban/Romantic/Chic, berdiri 1993, filosofi self-expression, tagar resmi).
- **`[Research Findings]`**: Pola komunikasi dari riset media sosial (anatomi hook keresahan Gen Z, format Reels/TikTok 9:16).
- **`[Assumptions]`**: Asumsi kreatif dalam draf (misal: saran padu padan graphic tee dengan relaxed trousers atau mini skirt).
- **`[Dummy / Simulated]`**: Data pesanan contoh atau nomor tiket simulasi (misal: order `#CBX-2026-9812`).
- **`[Informasi Tidak Tersedia]`**: Pengakuan jujur jika data spesifik (seperti klaim bahan detail 100% katun atau persentase diskon) tidak tercantum pada berkas knowledge, sehingga AI tidak berhalusinasi.

---

## 6. Cara Menguji dan Melihat Hasil di Frontend

1. **Buka Aplikasi Frontend:**
   Akses browser pada tautan: **[http://localhost:5173/](http://localhost:5173/)**
2. **Uji Melalui Halaman Marketing Workspace:**
   - Navigasi ke menu **Marketing** di bilah navigasi samping (`http://localhost:5173/#/marketing`).
   - Pilih agen yang ingin diajak kolaborasi (misal: **Rian** untuk naskah atau **Diana** untuk review).
   - Isi form brief kampanye (tersedia tombol *"Gunakan data contoh Colorbox"* untuk pengisian instan).
   - Klik **Kirim Brief**, lalu lanjutkan ke tahap Rencana, Konten, Review, dan Revisi.
3. **Uji Melalui Chat Bebas:**
   - Masuk ke menu **Chat** (`http://localhost:5173/#/chat`).
   - Pilih bot **Rian** dan kirimkan prompt bebas, misalnya:
     > *"Halo Rian, tolong buatkan 1 caption Instagram untuk mempromosikan Graphic Tee dengan tema kampanye #NeverJustOneThing!"*
   - Perhatikan kotak proses berpikir (*thinking process*) yang dapat diklik untuk melihat transparansi logika AI sebelum memberikan draf balasan.
4. **Uji Skenario Standar di Halaman Uji:**
   - Masuk ke menu **Uji** (`http://localhost:5173/#/uji`).
   - Pilih skenario **TC-01 s/d TC-11** untuk Marketing, jalankan secara otomatis, dan beri skor evaluasi reviewer langsung pada panel penilaian skala 1–5.

