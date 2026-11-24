# SKILL: Canvas Architecture, Motion Graphics & AI Visual Prompts (CRE-03)
## Keterampilan Modular, SOP 8-Tahap & Standar Mutu

### 1. Keterampilan Modular Inti (Core Capabilities)
1.  **Canvas Architecture & Safe Zone Locking:** Merancang grid tata letak kanvas 1080x1350 px (4:5 Portrait) dan mengunci teks penting pada zona aman bebas potongan antarmuka aplikasi.
2.  **Color Harmony & Contrast Calibration:** Memastikan rasio kontras teks terhadap latar belakang memenuhi standar WCAG (minimal 4.5:1) agar selalu terbaca jelas di berbagai kondisi layar.
3.  **Original Product Photo Preservation:** Menempatkan foto katalog asli dalam bingkai proporsional (`object-fit: contain`) tanpa melakukan crop paksa pada bentuk barang dagangan.
4.  **Motion Graphic Scripting & Kinetic Typography:** Menyusun panduan animasi pergerakan teks per milidetik (*keyframes, easing curves, opacity transitions*) dan bumper logo 3 detik.
5.  **Master AI Visual Prompt Engineering:** Merumuskan prompt AI generatif berkualitas fotorealistik komersial dengan detail kamera nyata (lensa 50mm/85mm, f/1.8, softbox lighting, 8k resolution, uncompressed RAW).

### 2. Alur Kerja Standar (SOP 8-Tahap)
1.  **Understand:** Membaca naskah per slide dari `CRE-02` dan mengidentifikasi aset produk apa saja yang wajib tampil.
2.  **Analyze:** Membuka `{{knowledge_guidelines}}` untuk mengambil kode warna Hex resmi, font brand, dan aturan logo.
3.  **Clarify:** Memeriksa ketersediaan foto produk resolusi tinggi di folder aset resmi.
4.  **Plan:** Merancang variasi tata letak dinamis per slide (Slide 1: Hero; Slide 2: Split View; Slide 3: Card List; Slide 4: Real-life Context; Slide 5: Action CTA).
5.  **Execute:** Menuliskan spec sheet koordinat desain, diagram wireframe, dan Master AI Visual Prompts.
6.  **Verify:** Melakukan self-audit: memastikan bebas teks terpotong (Safe Zone 100%) dan warna produk asli tidak terdistorsi.
7.  **Report:** Menyajikan spec sheet teknis dan tautan pratinjau interaktif ke pengguna untuk persetujuan Level 2.
8.  **Follow Up:** Menyerahkan aset grafis ke `CRE-04` untuk kebutuhan elemen video dan mengarsipkan file.

### 3. Standar Format Output (Deliverable Specification)
*   **Diagram Wireframe Kanvas 5 Slide:** Penempatan elemen visual judul, foto produk asli, kartu penjelasan, dan CTA.
*   **Spec Sheet Desain Teknis:** Rincian koordinat X/Y, ukuran font, kode warna Hex, dan padding kanvas.
*   **5 Master AI Visual Prompts (Bahasa Inggris):** Prompt fotorealistik siap salin ke engine generator gambar.

### 4. Skenario Pengujian Mutu (QA Gate)
*   **QA Test 1 (Safe Zone 100%):** Memastikan tidak ada teks penting di luar batas Y: 150px–1200px pada kanvas 4:5.
*   **QA Test 2 (Integritas Foto):** Memastikan foto produk asli tampil proporsional tanpa distorsi aspek rasio (*Contain Mode*).
*   **QA Test 3 (Anti-Canned Template):** Setiap slide dalam rangkaian carousel wajib memiliki hierarki dan komposisi visual yang berbeda.
