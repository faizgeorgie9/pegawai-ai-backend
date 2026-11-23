# Colorbox Content & Creative: 4-Agent Consolidated Automation & Content Scheduler Guide
### *R&D Sistem Kolaborasi Multi-Agent Group Chat & Penjadwalan Otomatis (Konsolidasi 4 Pegawai AI)*

> **Dokumen Master Arsitektur & Operasional**  
> **Brand:** Colorbox Indonesia (Delamibrands)  
> **Framework:** Multi-Agent Group Chat & Automated Content Scheduler  
> **Lokasi File Agen:** `hermes/colorbox/marketing/agents/*.md`  
> **Knowledge Base:** `hermes/colorbox/colorbox-knowledge/*.md`  
> **Versi:** v2.0 (Consolidated 4-Bot Architecture) | 23 November 2026

---

## 1. Roster & Struktur 4 Pegawai AI Konsolidasi (Content & Creative)

Mengacu pada arahan master konsolidasi divisi Content & Creative, 8 peran spesialis telah dikonsolidasikan menjadi **4 Pegawai AI komprehensif** dengan kepemilikan siklus kerja end-to-end:

| No | Kode | Nama Agen | Handle | Peran & Tanggung Jawab Utama | File Definisi |
|:---|:---|:---|:---|:---|:---|
| 1 | **CRE-01** | **Content Strategist** | `@contentstrategist` | **Content Strategy & Omnichannel Distribution:** Menentukan pilar konten (*Urban/Romantic/Chic*), riset audiens Gen Z (*Colorbox Babes*), kurasi produk katalog resmi, menyusun kalender editorial mingguan, membuat *creative brief*, serta mengelola adaptasi format multi-platform & antrean penjadwalan distribusi. | [`01_content_strategist.md`](file:///d:/Users/IVANAGITA/aitoptrends/hermes/colorbox/marketing/agents/01_content_strategist.md) |
| 2 | **CRE-02** | **Content & Copywriter** | `@copywriter` | **Creative Copywriting & Storytelling:** Menulis naskah persuasif berdaya konversi tinggi, caption Instagram/TikTok, headline *thumb-stopping*, hook 3 detik pembuka, teks on-screen minimalis, panduan gaya berpakaian, dan *Call to Action* (CTA) dengan kampanye resmi `#NeverJustOneThing`. | [`02_content_and_copywriter.md`](file:///d:/Users/IVANAGITA/aitoptrends/hermes/colorbox/marketing/agents/02_content_and_copywriter.md) |
| 3 | **CRE-03** | **Graphic & Motion Designer** | `@motiondesigner` | **Static & Kinetic Visual Architecture:** Merancang feed carousel 4:5 Portrait (1080x1350 px), wireframe tata letak *safe zone*, banner promosi, infografik *size guide*, elemen animasi *kinetic typography*, transisi visual bergerak, dan menyusun *Master AI Visual Prompts* fotorealistik (Midjourney/FLUX/GPT-Image). | [`03_graphic_and_motion_designer.md`](file:///d:/Users/IVANAGITA/aitoptrends/hermes/colorbox/marketing/agents/03_graphic_and_motion_designer.md) |
| 4 | **CRE-04** | **Video & UGC Creator** | `@videougc` | **Short-Form Video & Authentic UGC Direction:** Mengembangkan konsep video vertikal 9:16 (Reels/TikTok/Shorts), naskah percakapan natural (*spoken script*), panduan talent kreator/UGC (*shot list* & demonstrasi *try-on*), kurasi audio viral/sound effects, dan optimasi visual 3 detik pertama tanpa suara. | [`04_video_and_ugc_creator.md`](file:///d:/Users/IVANAGITA/aitoptrends/hermes/colorbox/marketing/agents/04_video_and_ugc_creator.md) |

---

## 2. Diagram Alur Kerja Otomatis di Group Chat (Auto-Cascading State Machine)

Alur kerja dirancang untuk berjalan di **Group Chat tunggal** (*Single Shared Channel*), di mana koordinasi mengalir secara otomatis (*auto-cascading*) dari strategi hingga distribusi:

```
                  ┌──────────────────────────────────────────────┐
                  │ 1. USER / CRON SCHEDULER TRIGGER             │
                  │    "Brief: Inspirasi Outfit Kuliah Santai"   │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ 2. CONTENT STRATEGIST (@contentstrategist)   │
                  │    - Riset Audiens & Pilar Gaya (Urban/Chic) │
                  │    - Kurasi 3 Opsi Konsep (A/B/C) Katalog    │
                  │    - Menyiapkan Omnichannel Creative Brief   │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ 3. HUMAN-IN-THE-LOOP APPROVAL / TIMEOUT      │
                  │    User memilih: "Opsi A (Effortless Urban)" │
                  └──────────────────────┬───────────────────────┘
                                         │
       ══════════════════════════════════╪═════════════════════════════════
       SISTEM AUTO-CASCADE AKTIF: OTOMATIS BERLANJUT TANPA PROMPT USER
       ══════════════════════════════════╪═════════════════════════════════
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ 4. CONTENT & COPYWRITER (@copywriter)        │
                  │    - Naskah Storytelling & Hook 3 Detik      │
                  │    - Caption Instagram #NeverJustOneThing    │
                  │    - On-Screen Text & Spoken Script Video    │
                  └──────────────────────┬───────────────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
       ┌───────────────────────────────────┐ ┌───────────────────────────────────┐
       │ 5A. GRAPHIC & MOTION DESIGNER     │ │ 5B. VIDEO & UGC CREATOR           │
       │     (@motiondesigner)             │ │     (@videougc)                   │
       │ - Visual Wireframe 5 Slide 4:5    │ │ - Video Storyboard 9:16 (15-30s)  │
       │ - Safe Zone Layout & Typo Motion  │ │ - UGC Creator Script & Shot List  │
       │ - Master AI Visual Prompts        │ │ - Audio Pacing & SFX Direction    │
       └─────────────────┬─────────────────┘ └─────────────────┬─────────────────┘
                         │                                     │
                         └───────────────┬─────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ 6. CONTENT STRATEGIST (@contentstrategist)   │
                  │    - Verifikasi Kepatuhan Klaim & Katalog    │
                  │    - Adaptasi Multi-Format (Feed, Reels, WA) │
                  │    - Penjadwalan Antrean Distribusi (Queue)  │
                  │    - Paket Penyerahan Final ke Reviewer      │
                  └──────────────────────────────────────────────┘
```

---

## 3. Spesifikasi & Setup Content Scheduler (Weekly Content Sprint)

Content Scheduler mengotomatisasi inisialisasi brief konten harian setiap pagi pukul 08:00 WIB:

### A. Matriks Jadwal Konten Mingguan (Weekly Content Sprint)

| Hari | Tema Brief Terjadwal | Pilar Gaya | Target Persona | Fokus Produk Katalog Colorbox Resmi |
|:---|:---|:---|:---|:---|
| **Senin (Day 1)** | "Monday Campus Rush: Effortless Lecture Look" | **Urban** | Mahasiswi aktif (18–21 th) | Oversized Graphic Tee (Rp 99.900) + High Waist Barrel Denim (Rp 329.900) + Liunic Tote Bag (Rp 199.900) |
| **Selasa (Day 2)** | "Sweet Cafe Study Date: Pastel Aesthetic Outfit" | **Romantic** | Mahasiswi feminin (19–22 th) | Fitted Crop Tee Lilac (Rp 89.900) + Stripes Pleated Skort (Rp 199.900) + Cable Knit Sweater (Rp 259.900) |
| **Rabu (Day 3)** | "Midweek Presentation: Chic First-Jobber Look" | **Chic** | Mahasiswi tingkat akhir / Magang (21–24 th) | Contrast Rib Crop Top (Rp 129.900) + Contrast Collar Jacket (Rp 359.900) + Straight Leg Denim (Rp 299.900) |
| **Kamis (Day 4)** | "Rainy Day Comfort: Cozy Coffee Shop Hangout" | **Urban/Chic** | Gen Z Explorer (18–23 th) | Furry Multicolor Sweater (Rp 279.900) + Relaxed Cargo Pants (Rp 319.900) + Canvas Cap (Rp 79.900) |
| **Jumat (Day 5)** | "TGIF Casual Dinner: Day-to-Night Versatile Look" | **Romantic/Chic** | Young Creative Worker (20–25 th) | Sleeveless Suede Mini Dress (Rp 249.900) + Cropped Denim Outer (Rp 329.900) + Micro Shoulder Bag |

### B. Konfigurasi Cron Scheduler

```yaml
# Scheduler Definition: Colorbox 4-Agent Consolidated Content Pipeline
scheduler:
  name: colorbox-omnichannel-daily-pipeline
  timezone: "Asia/Jakarta"
  cron: "0 8 * * 1-5"  # Setiap Senin - Jumat pukul 08:00 WIB
  channel: "#colorbox-content-creative-groupchat"
  
  environment:
    BRAND: "Colorbox Indonesia"
    CATALOG_PATH: "hermes/colorbox/colorbox-knowledge/product-catalog.md"
    AUTO_CASCADE: true
    AUTO_APPROVE_DEFAULT: true   # Jika user tidak memilih dalam 30 menit, pilih Opsi A
    APPROVAL_TIMEOUT_MINUTES: 30
    
  daily_prompts:
    day_1: "Jalankan sprint Day 1: Inspirasi outfit kuliah santai (Urban Campus). Prioritaskan kenyamanan ruang kelas ber-AC dan mobilitas tinggi."
    day_2: "Jalankan sprint Day 2: Outfit cafe study date manis dan feminin (Romantic Pastel)."
    day_3: "Jalankan sprint Day 3: Smart casual look untuk magang kampus dan presentasi (Chic Smart)."
    day_4: "Jalankan sprint Day 4: Cozy knitwear styling untuk cuaca sejuk / hangout sore santai."
    day_5: "Jalankan sprint Day 5: Friday night casual dinner & hangout outfit (Versatile Chic)."
```

---

## 4. Mekanisme Penanganan Masalah & Anti-Halusinasi

1. **Watchdog Timeout:**
   Jika sebuah agen tidak merespons dalam 120 detik, `@contentstrategist` secara otomatis mengirimkan peringatan koordinasi.
2. **Katalog Guardrail:**
   Seluruh produk wajib diverifikasi terhadap `product-catalog.md`. Jika nama produk, SKU, atau harga tidak cocok dengan katalog resmi, draf otomatis ditolak untuk diperbaiki sebelum diteruskan.
3. **Pemisahan Tingkat Data yang Jelas:**
   - `[VERIFIED FACT]`: Fakta katalog resmi (nama item, harga Rp, foto produk asli).
   - `[CREATIVE SUGGESTION]`: Inspirasi padu padan, angle hook, naskah caption, dan panduan visual.
   - `[ASSUMPTION]`: Target audiens dan jam aktif persona Gen Z.

---

## 5. Simulasi Percakapan Penuh di Group Chat (End-to-End Chat Log)

```
[08:00:00] [CRON SCHEDULER]: 🔔 TRIGGER HARIAN AKTIF (Sprint Day 1)
"Selamat pagi Tim Content & Creative! Jadwal brief hari ini: Monday Campus Rush: Effortless Lecture Look."
--------------------------------------------------------------------------------------
[08:00:05] Content Strategist (@contentstrategist):
"Pagi tim! Strategist mengambil alih inisiasi. Brief hari ini berfokus pada mahasiswi Gen Z (18-21 tahun) untuk outfit kuliah santai yang praktis dan stylish.
Berdasarkan kurasi katalog resmi Colorbox (product-catalog.md), berikut 3 opsi konsep konten:

🌸 Opsi A (Urban Campus Rebel):
- Produk: Oversized Graphic T-Shirt OFF WHITE (Rp 99.900) + High Waist Barrel Denim BLACK (Rp 329.900) + Liunic Tote Bag (Rp 199.900). Total look: Rp 629.700.
- Angle: Kenyamanan gerak, siluet santai, anti ribet kelas pagi.

🌸 Opsi B (Romantic Casual Pastel):
- Produk: Fitted Crop Tee LILAC (Rp 89.900) + Stripes Pleated Skort (Rp 199.900) + Cardigan Rajut.
- Angle: Look manis, feminin, dan estetik untuk perpustakaan & cafe.

🌸 Opsi C (Chic Smart Presentation):
- Produk: Contrast Rib Crop Top (Rp 129.900) + Contrast Collar Jacket (Rp 359.900) + Straight Denim.
- Angle: Rapi berwibawa namun tetap modis untuk presentasi tugas.

Rekomendasi utama Strategist adalah OPSI A.
Silakan konfirmasi pilihan Opsi A, B, atau C ya Tim Reviewer / User!"
--------------------------------------------------------------------------------------
[08:01:10] User / Reviewer:
"Pilih Opsi A."
--------------------------------------------------------------------------------------
[08:01:15] Content Strategist (@contentstrategist):
"Siap, Opsi A disetujui!
SISTEM AUTO-CASCADE AKTIF: Beralih otomatis ke tim produksi tanpa perlu dipanggil manual.

📋 [DISPATCH TASK-01: COPY & SCRIPTING] -> @copywriter
Objektif: Tulis naskah lengkap carousel 5 slide, caption Instagram resmi #NeverJustOneThing, dan script video pendek 15 detik. Gunakan fakta harga dan nama produk katalog 100% akurat."
--------------------------------------------------------------------------------------
[08:01:45] Content & Copywriter (@copywriter):
"✍️ Naskah dan narasi Opsi A selesai!
1. Carousel Instagram 5 Slide:
   - Slide 1 (Hook): 'Kelas Jam 8 Pagi, Tetap Slay Tanpa Pusing.'
   - Slide 2: Oversized Graphic Tee (Rp 99.900) — bahan katun adem, cutting relaxed.
   - Slide 3: High Waist Barrel Denim (Rp 329.900) — siluet curved kaki jenjang.
   - Slide 4: Colorbox x Liunic Tote Bag (Rp 199.900) — muat laptop 14 inch & catatan.
   - Slide 5: Outro CTA 'Save ide outfit ini & tap link di bio untuk checkout!'
2. Caption Instagram: Storytelling Gen Z kuliah pagi, tagar resmi #NeverJustOneThing #ColorboxBabes, rincian produk & harga resmi.
3. Spoken Script Video Vertikal (15s): Hook 3 detik suara cepat, voiceover transisi OOTD santai.

Pekerjaan siap dialirkan ke tim visual dan video!"
--------------------------------------------------------------------------------------
[08:01:50] Content Strategist (@contentstrategist):
"Mantap @copywriter! Narasi kuat dan fakta katalog 100% valid.
📋 [DISPATCH TASK-02: PARALLEL CREATIVE ASSETS] -> @motiondesigner & @videougc
- @motiondesigner: Rancang visual wireframe 5-slide carousel 4:5 Portrait dan master AI visual prompt fotorealistik.
- @videougc: Susun video storyboard 9:16 vertikal dan panduan UGC creator styling demo."
--------------------------------------------------------------------------------------
[08:02:30] Graphic & Motion Designer (@motiondesigner):
"🎨 Visual Carousel 5 Slide & Motion Direction siap!
- Wireframe Kanvas: Format 4:5 Portrait (1080x1350 px), safe zone atas 120px, bawah 160px.
- Foto Produk Asli: Terintegrasi dari folder images/ (cbx-02-high-waist-barrel-denim-black.jpg & cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg) dengan contain mode tanpa distorsi aspek rasio.
- Master AI Visual Prompt: Prompt fotorealistik kamera 35mm f/1.8 direct flash model Gen Z Indonesia, detail tekstur katun tee dan denim twill.
- Elemen Kinetic Motion: Transisi slide geser halus dan teks animasi penegas pilar Urban."
--------------------------------------------------------------------------------------
[08:02:35] Video & UGC Creator (@videougc):
"🎬 Video Storyboard 9:16 & UGC Brief siap!
- Durasi: 22 detik ritme dinamis.
- Shot List: 0-3s Visual hook menepuk kasur -> 3-8s Memakai Oversized Graphic Tee -> 8-15s Cermin OOTD Barrel Denim & Tote Bag -> 15-22s Berjalan santai keluar gerbang kampus + CTA link bio.
- Audio Direction: Upbeat lofi-pop trending sound tempo 115 BPM.
- Talent Guidance: Pencahayaan jendela alami, ekspresi percaya diri santai, pakaian terpasang rapi."
--------------------------------------------------------------------------------------
[08:03:00] Content Strategist (@contentstrategist):
"🎉 SELURUH PAKET KONTEN OPSI A SELESAI DENGAN SEMPURNA!

📊 LAPORAN QUALITY CONTROL & DISTRIBUSI STRATEGIST:
- Verifikasi Fakta Katalog: 100% Terverifikasi (Katalog Colorbox resmi, zero-hallucination).
- Format Carousel: 5 Slide 4:5 Portrait (1080x1350 px) dengan wireframe lengkap.
- Format Video: Storyboard 9:16 (22s) + UGC Talent Guidance lengkap.
- Saluran Terjadwal: Instagram Feed Carousel (Senin 11:30 WIB) & TikTok / Reels (Senin 18:30 WIB).
- Status Distribusi: 🟢 MASUK ANTREAN DISTRIBUSI (Menunggu Approval Akhir Reviewer).

Materi telah terarsip dan siap dipublikasikan. Terima kasih tim!"
```

---

## 6. Ringkasan Implementasi & Checklist Kesiapan

- [x] **CRE-01 (Content Strategist):** Merancang strategi pilar konten, riset audiens Gen Z, kurasi katalog anti-halusinasi, orchestrator auto-cascade, dan penjadwalan antrean distribusi multi-kanal.
- [x] **CRE-02 (Content & Copywriter):** Menulis hook viral, narasi persuasif, naskah carousel, caption resmi #NeverJustOneThing, dan script video pendek.
- [x] **CRE-03 (Graphic & Motion Designer):** Menghasilkan layout kanvas 4:5 Portrait, wireframe safe zone, arahan tipografi kinetik, dan master AI visual prompt fotorealistik.
- [x] **CRE-04 (Video & UGC Creator):** Mengembangkan video storyboard vertikal 9:16, panduan talent UGC, kurasi audio ritmis, dan daftar adegan (shot list).
- [x] **Content Scheduler:** Mendukung otomatisasi sprint mingguan (Day 1 s.d. Day 5) dengan auto-approval default 30 menit.
