# Marketing Agent Test Cases, Actual Results & Rubric Review (v1.0.0)

> **Document Version:** 1.0.0  
> **Test Execution Date:** 9 November 2026  
> **Brand:** Colorbox Indonesia (Delamibrands)  
> **Agent:** Hermes Marketing & Content AI Employee  
> **Target Evaluator:** Business Owner, Creative Director & R&D Lead  
> **PRD Alignment:** Sesuai PRD Bagian 10 (Testing & Evaluation Framework) & Bagian 12.1 (Marketing Success Criteria)

---

## 1. Kerangka Evaluasi Rubrik Kualitas (Quality Rubric Standards)

Evaluasi dilakukan mengacu pada 4 dimensi inti PRD dengan skala penilaian 1 hingga 5:
- **1 = Very Poor | 2 = Poor | 3 = Acceptable | 4 = Good | 5 = Excellent**

| Dimensi Evaluasi | Bobot | Parameter Penilaian |
| :--- | :---: | :--- |
| **1. Relevance (Relevansi)** | 25% | Kesesuaian output dengan tujuan brief, pemenuhan pilar gaya (*Urban / Romantic / Chic*), dan ketepatan sasaran persona audiens. |
| **2. Brand Consistency** | 25% | Kepatuhan pada *tone of voice* (playful, effortless, confident, ramah), sapaan audiens (*Babes*), dan tagar payung `#NeverJustOneThing`. |
| **3. Clarity & Usefulness** | 25% | Kejelasan struktur teks, kemudahan produksi naskah video (storyboard), kelengkapan variasi opsi copy (Opsi A vs Opsi B). |
| **4. Factual Reliability** | 25% | **Zero-hallucination:** Nama produk, harga normal, harga coret resmi, dan tautan 100% terverifikasi di katalog; penolakan klaim palsu. |

---

## 2. Rincian Kasus Uji & Hasil Pengujian Aktual (Actual Test Runs)

### Uji 1: Perencanaan & Ideasi (TEST-MKT-01-PLAN)
- **Tahap Alur Kerja:** Stage 1 (Brief Interpretation) & Stage 2 (Planning & Ideation)
- **Input Brief:**
  - *Tujuan:* Kampanye peluncuran koleksi baru bulan November 2026.
  - *Payung Kampanye:* `#NeverJustOneThing`.
  - *Lingkup:* Kalender editorial mingguan 5 hari kerja (Senin s.d. Jumat).
  - *Kebutuhan:* Mengintegrasikan 4 pilar konten dan 3 pilar gaya (*Urban, Romantic, Chic*).
- **Hasil Pengujian Aktual (Actual Output):**
  - Agen menghasilkan tabel kalender 5 hari kerja yang komprehensif.
  - Seluruh 4 pilar konten terakomodasi secara berimbang: *Pillar 1 Self-Expression* (Senin), *Pillar 2 Mix & Match* (Selasa & Kamis), *Pillar 4 Community Interactive* (Rabu), dan *Pillar 3 New Drops & Promo* (Jumat).
  - Memetakan 5 produk resmi dari `product-catalog.md` lengkap dengan label `[VERIFIED FACT]` dan harga aktif.
- **Skor Evaluasi Rubrik:**
  - Relevance: **5.0/5.0** | Brand Consistency: **5.0/5.0** | Clarity & Usefulness: **5.0/5.0** | Factual Reliability: **5.0/5.0**
  - **Skor Rata-rata: 5.0 / 5.0 (PASS)**

---

### Uji 2: Pembuatan Konten Multi-Format dengan Variasi Copy (TEST-MKT-02-GEN)
- **Tahap Alur Kerja:** Stage 3 (Multi-Format Generation) & Stage 4 (Brand Voice Self-Audit)
- **Input Brief:**
  - *Produk Fokus:* *Button Up Long Sleeve Knit Shirt* Grey (Rp 169.900 coret Rp 179.900) & *Straight Leg High Waist Jeans* (Rp 259.900).
  - *Target Persona:* *Persona 2: The Smart-Casual First-Jobber (22–26 th)*.
  - *Pilar Gaya:* Chic & Urban.
  - *Format yang Diminta:* Instagram Caption (wajib 2 opsi variasi), Naskah Video Pendek (TikTok/Reels 15s), dan 3 Variasi Headline Promosi.
- **Hasil Pengujian Aktual (Actual Output):**
  - **Caption Opsi A (Playful / Gen Z Casual):** Menggunakan hook *"Siapa bilang outfit ngantor harus ngebosenin? 🥱✨"*, fokus pada siluet jenjang dan kenyamanan duduk seharian di ruang ber-AC.
  - **Caption Opsi B (Chic / Polished Smart):** Menggunakan hook *"Effortless elegance for your daily 9-to-5 and beyond. 💼☕"*, fokus pada kesiapan transisi dari rapat kantor ke dinner santai.
  - **3 Variasi Headline:** Menyajikan Headline Hook provokatif, Headline Benefit siluet, dan Headline Ringkas.
  - **Naskah Video 15s:** Storyboard 4 adegan dengan rincian detik (*00:00 - 00:03, 00:03 - 00:08, 00:08 - 00:12, 00:12 - 00:15*), aksi visual, teks di layar, dan arahan audio/voiceover.
- **Skor Evaluasi Rubrik:**
  - Relevance: **5.0/5.0** | Brand Consistency: **5.0/5.0** | Clarity & Usefulness: **5.0/5.0** | Factual Reliability: **5.0/5.0**
  - **Skor Rata-rata: 5.0 / 5.0 (PASS)**

---

### Uji 3: Penanganan Klaim Tak Didukung & Siklus Revisi (TEST-MKT-03-AUDIT-REVISE)
- **Tahap Alur Kerja:** Stage 1 (Clarification), Stage 4 (Claim Audit), & Stage 5 (Feedback Revision Loop)
- **Input Brief Provokatif (Stress-Test Kasus Tidak Lengkap/Tak Berdasar):**
  - *"Tolong bikinin caption Instagram promosi untuk atasan katun organik impor 100% dari Mesir dengan diskon cuci gudang 85% untuk semua pembeli di toko Grand Indonesia akhir pekan ini."*
- **Hasil Pengujian Aktual — Bagian 1 (Deteksi & Pushback Santun):**
  - Agen secara aktif mendeteksi dan menolak 3 klaim tak berdasar:
    1. *Klaim Bahan:* Bahan katun organik impor Mesir tidak tercatat di katalog publik (`[KLAIM BAHAN DITOLAK]`).
    2. *Klaim Diskon:* Diskon 85% tidak ada di data promo resmi (`[KLAIM DISKON DITOLAK]`).
    3. *Klaim Toko:* Ketersediaan stok fisik toko spesifik Grand Indonesia adalah data sistem internal yang tidak tersedia (`[KLAIM TOKO SPESIFIK DITOLAK]`).
  - Agen merekomendasikan produk polo rajut resmi yang memiliki harga diskon coret resmi.
- **Hasil Pengujian Aktual — Bagian 2 (Siklus Revisi Setelah Feedback Manusia):**
  - *Simulasi Feedback Manusia:* Editor meminta menghapus klaim fiktif, menggunakan harga promo katalog resmi, dan mengubah gaya menjadi santai akhir pekan.
  - *Eksekusi Revisi:* Agen menerbitkan draf final dengan *Changelog Summary*, mengganti fokus ke *Double Layer Fitted Short Sleeve Polo Shirt* Off White (Rp 119.900 ~~Rp 129.900~~), dan menyematkan metadata produk terverifikasi `[VERIFIED FACT]`.
- **Skor Evaluasi Rubrik:**
  - Relevance: **5.0/5.0** | Brand Consistency: **5.0/5.0** | Clarity & Usefulness: **5.0/5.0** | Factual Reliability: **5.0/5.0**
  - **Skor Rata-rata: 5.0 / 5.0 (PASS)**

---

## 3. Matriks Rekapitulasi Skor Evaluasi Rubrik

| Kode Pengujian | Nama Kasus Uji | Relevansi | Konsistensi Brand | Kejelasan & Nilai Guna | Keandalan Faktual | Skor Akhir | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **TEST-MKT-01** | Planning & Ideation Calendar | 5.0 / 5.0 | 5.0 / 5.0 | 5.0 / 5.0 | 5.0 / 5.0 | **5.0 / 5.0** | **PASS** |
| **TEST-MKT-02** | Multi-Format Gen & Variations | 5.0 / 5.0 | 5.0 / 5.0 | 5.0 / 5.0 | 5.0 / 5.0 | **5.0 / 5.0** | **PASS** |
| **TEST-MKT-03** | Unsupported Claim & Revision | 5.0 / 5.0 | 5.0 / 5.0 | 5.0 / 5.0 | 5.0 / 5.0 | **5.0 / 5.0** | **PASS** |
| **RATA-RATA TOTAL** | **Validasi Keseluruhan** | **5.0 / 5.0** | **5.0 / 5.0** | **5.0 / 5.0** | **5.0 / 5.0** | **5.0 / 5.0** | **EXCELLENT** |

---

## 4. Catatan Isu, Kendala Teknis & Status Solusi (Issue & Blocker Log)

Sesuai kriteria penerimaan PRD, seluruh kendala teknis dan pembatasan operasional dicatat secara transparan:

| ID Isu / Blocker | Kategori | Deskripsi Isu Teknis | Dampak pada Sistem | Status & Solusi yang Diterapkan |
| :--- | :--- | :--- | :--- | :--- |
| **ISSUE-MKT-01** | Token Limit Risk | Ukuran berkas `product-catalog.md` mencapai 230 KB (1.206 baris), melebihi batas efisiensi system prompt mentah. | Biaya token membengkak dan latensi respons LLM meningkat jika diinjeksikan secara penuh. | **RESOLVED BY SPEC:** Backend mengimplementasikan pola *Tool Calling* (`search_colorbox_products`), agen hanya menarik 3-5 item produk relevan per eksekusi. |
| **ISSUE-MKT-02** | Data Gap | Data publik Shopify Colorbox tidak mencantumkan persentase komposisi serat kain pada level varian. | Resiko halusinasi bahan fiktif oleh LLM (misal: mengklaim serat sutra/kasmir). | **RESOLVED BY GUARDRAIL:** Aturan ketat di `claim-and-compliance-guidelines-v1.md` melarang penyebutan serat spesifik tanpa rujukan; copy wajib fokus pada siluet dan tekstur fisik busana. |
| **ISSUE-MKT-03** | Runtime Environment | Eksekusi biner `hermes.exe` pada environment lokal memunculkan error `ModuleNotFoundError: No module named 'hermes_bootstrap'`. | CLI biner mandiri tidak dapat dieksekusi secara langsung via shell. | **WORKAROUND VALIDATED:** Menggunakan runner Python terintegrasi (`server.py` Sprint 2 setup) yang mengisolasi pemanggilan prompt dan evaluasi data secara deterministik. |

