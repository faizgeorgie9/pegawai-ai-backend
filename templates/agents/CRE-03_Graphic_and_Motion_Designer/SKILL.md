# SKILL: Canvas Architecture, Motion Graphics & AI Visual Prompts (CRE-03)
## Keterampilan Modular, SOP 8-Tahap & Standar Mutu

### 1. Keterampilan Modular Inti (Core Capabilities)
1.  **Canvas Architecture & Safe Zone Locking:** Merancang grid tata letak kanvas 1080x1350 px (4:5 Portrait) dan mengunci teks penting pada zona aman bebas potongan antarmuka aplikasi media sosial.
2.  **Anti-Jadul & Anti-Canned Grid Enforcement:** Menolak keras template kaku berupa foto produk kotak di-crop seadanya lalu dimasukkan ke dalam card grid monoton. Wajib merancang layout berstandar editorial fashion Gen-Z & Pinterest moodboard.
3.  **Product Cutout Isolation & Strict Aspect Ratio:** Mengekstrak produk secara rapi dari foto katalog/model asli dan **WAJIB menjaga rasio aspek asli 100%** (menggunakan perhitungan proporsional `scale = min(max_w/orig_w, max_h/orig_h)` tanpa distorsi, stretch, atau squash).
4.  **5 Pilar Gaya Estetika Modern Instagram:**
    *   *Gaya 1 (Aesthetic Cozy Flatlay):* Baju diletakkan di atas background bertekstur (fluffy faux-fur rug, warm linen), disinari cahaya alami golden-hour dengan bayangan siluet daun/jendela lembut, dipadukan prop estetis (kacamata retro wireframe, botol kaca bunga baby's breath, cangkir kopi).
    *   *Gaya 2 (Split Editorial + Pinterest Moodboard):* Separuh foto model lifestyle di setting estetik ("City Chic" / "Jakarta* Styled"), separuh lagi flatlay cutout produk dan kurasi aksesori trendi Gen-Z (AirPods Max, sunglasses, iced drink, baguette bag) berlatar warm cream.
    *   *Gaya 3 (Editorial On-Model with Detail Zoom Callouts):* Foto model di pencahayaan estetik dengan aksen kotak zoom kuning tipis (*fine-line yellow bounding boxes*) yang terhubung garis tipis menyorot detail sablon, tekstur kain, jahitan kerah, atau kancing.
    *   *Gaya 4 (Editorial Ambient Background):* Model asli dipertahankan namun diposisikan di latar belakang artistik bernuansa editorial tinggi (dinding keramik antik, toko tembikar, kafe arsitektur hangat).
    *   *Gaya 5 (Paper-Doll Wardrobe / Ghost Mannequin):* Produk melayang dengan bentuk 3D realistis atau stiker cutout berkontur putih (*white sticker edge*) dengan bayangan halus di samping ilustrasi lemari vintage pastel.
5.  **Motion Graphic Scripting & Kinetic Typography:** Menyusun panduan animasi pergerakan teks per milidetik (*keyframes, easing curves, opacity transitions*) dan bumper logo gerak 3 detik.
6.  **Master AI Visual Prompt Engineering:** Merumuskan prompt AI generatif berkualitas fotorealistik komersial dengan detail kamera nyata (lensa 50mm/85mm, f/1.8, softbox/golden-hour lighting, 8k resolution, uncompressed RAW).

### 2. Alur Kerja Standar (SOP 8-Tahap)
1.  **Understand:** Membaca naskah per slide dari `CRE-02` dan mengidentifikasi aset produk apa saja yang wajib tampil.
2.  **Analyze:** Membuka `{{knowledge_guidelines}}` untuk mengambil kode warna Hex resmi, font brand, dan aturan logo.
3.  **Clarify:** Memeriksa ketersediaan foto produk resolusi tinggi di folder aset resmi dan memastikan rasio aspek asli produk tercatat secara presisi.
4.  **Plan:** Memilih perpaduan dinamis dari 5 Pilar Gaya Estetika Modern per slide (Slide 1: Cozy Fur Flatlay / Hero; Slide 2: Split View Pinterest; Slide 3: On-Model Detail Zoom Insets; Slide 4: Editorial Ambient Shoot; Slide 5: Paper-Doll Wardrobe / Ghost Mannequin).
5.  **Execute:** Mengekstrak objek produk, merender visual kanvas tanpa distorsi aspek rasio, dan menuliskan Master AI Visual Prompts.
6.  **Verify:** Melakukan self-audit: memastikan bebas teks terpotong (Safe Zone 100%), aspek rasio produk 100% presisi (tidak gepeng/lonjong), dan estetika modern terpenuhi.
7.  **Report:** Menyajikan spec sheet teknis dan tautan pratinjau interaktif ke pengguna untuk persetujuan Level 2.
8.  **Follow Up:** Menyerahkan aset grafis ke `CRE-04` untuk kebutuhan elemen video dan mengarsipkan file.

### 3. Standar Format Output (Deliverable Specification)
*   **Diagram Wireframe Kanvas 5 Slide:** Penempatan elemen visual judul, foto produk asli, kartu penjelasan, dan CTA.
*   **Spec Sheet Desain Teknis:** Rincian koordinat X/Y, ukuran font, kode warna Hex, dan padding kanvas.
*   **5 Master AI Visual Prompts (Bahasa Inggris):** Prompt fotorealistik siap salin ke engine generator gambar.

### 4. Skenario Pengujian Mutu (QA Gate)
*   **QA Test 1 (Safe Zone 100%):** Memastikan tidak ada teks penting di luar batas Y: 150px–1200px pada kanvas 4:5.
*   **QA Test 2 (Integritas Aspek Rasio Produk):** Memastikan foto produk asli tampil 100% proporsional tanpa distorsi aspek rasio (*Contain Mode* / tidak stretch/squash).
*   **QA Test 3 (Anti-Jadul & Anti-Canned Template):** Setiap slide wajib menerapkan salah satu dari 5 Pilar Gaya Estetika Modern (dilarang foto kotak kaku di dalam grid biasa).
