# Colorbox Marketing: 5-Agent Automation & Content Scheduler Guide
### *R&D Sistem Kolaborasi Multi-Agent Group Chat & Penjadwalan Otomatis (MVP Pegawai AI)*

> **Dokumen Master Arsitektur & Operasional**  
> **Brand:** Colorbox Indonesia (Delamibrands)  
> **Framework:** Multi-Agent Group Chat & Automated Content Scheduler  
> **Lokasi File Agen:** `hermes/colorbox/marketing/agents/*.md`  
> **Knowledge Base:** `hermes/colorbox/colorbox-knowledge/*.md`  

---

## 1. Roster & Struktur 5 Pegawai AI Colorbox

| No | Nama Agen | Handle | Peran & Tanggung Jawab Utama | File Definisi |
|:---|:---|:---|:---|:---|
| 1 | **Bimo** | `@projectmanager` | **Project Manager & Flow Controller:** Menerima brief/trigger scheduler, memecah task, memantau kanban, menangani agen macet (*unblocking*), dan **mengalirkan pekerjaan secara otomatis (*auto-cascade*)** antar-agen setelah ide disetujui. | [`01_project_manager_bimo.md`](file:///d:/Users/IVANAGITA/aitoptrends/hermes/colorbox/marketing/agents/01_project_manager_bimo.md) |
| 2 | **Meda** | `@marketingstrategist` | **Marketing & Fashion Strategist:** Menganalisis audiens Gen Z (*Colorbox Babes*), memetakan pilar gaya (*Urban / Romantic / Chic*), mengurasi produk resmi dari `product-catalog.md`, dan merumuskan **3 Opsi Konsep Konten (Opsi A, B, C)**. | [`02_marketing_strategist_meda.md`](file:///d:/Users/IVANAGITA/aitoptrends/hermes/colorbox/marketing/agents/02_marketing_strategist_meda.md) |
| 3 | **Raka** | `@researcher` | **Fashion & Content Researcher:** Meneliti fakta katalog resmi (nama item, SKU, warna, harga, cutting), riset ukuran & fitting tubuh (`product-size-reference.md`), melakukan **pengadaan gambar otomatis (*on-demand image scraping*)** jika produk belum ada di folder `images/`, dan menyusun **Creative & Content Research Brief** anti-halusinasi. | [`03_fashion_researcher_raka.md`](file:///d:/Users/IVANAGITA/aitoptrends/hermes/colorbox/marketing/agents/03_fashion_researcher_raka.md) |
| 4 | **Bram** | `@sketchwriter` | **Creative Copywriter & AI Visual Prompt Artist:** Menyusun naskah per slide (hook, body, CTA), menulis caption Instagram resmi (`#NeverJustOneThing`), dan membuat **AI Visual Prompts (Midjourney/FLUX format)** per slide. | [`04_sketch_writer_bram.md`](file:///d:/Users/IVANAGITA/aitoptrends/hermes/colorbox/marketing/agents/04_sketch_writer_bram.md) |
| 5 | **Vina** | `@visualcarousel` | **Visual Art Director & Final Carousel Production Engine:** Merender **aset gambar final siap tayang (5 berkas PNG 1080x1350 px Feed Portrait)** menggunakan foto produk resmi Colorbox, komposisi full-bleed feed bebas margin Reels, dan membangun **pratinjau live carousel interaktif**. | [`05_visual_carousel_vina.md`](file:///d:/Users/IVANAGITA/aitoptrends/hermes/colorbox/marketing/agents/05_visual_carousel_vina.md) |

---

## 2. Diagram Alur Kerja Otomatis di Group Chat (Auto-Cascading State Machine)

Alur kerja dirancang untuk berjalan di **Group Chat tunggal** (Telegram/Slack/WhatsApp Group atau Chat Room Pegawai AI), bukan di form terpisah. Pengguna hanya perlu memilih konsep di awal, setelah itu sistem berjalan otomatis sampai selesai:

```
                  ┌─────────────────────────────────────┐
                  │ 1. USER / CRON SCHEDULER TRIGGER    │
                  │    "Brief: Outfit Kuliah Santai"    │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 2. BIMO (@projectmanager)           │
                  │    Inisialisasi Kanban & Dispatch   │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 3. MEDA (@marketingstrategist)      │
                  │    Riset Audiens & Berikan 3 Opsi   │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 4. HUMAN-IN-THE-LOOP / AUTO-APPROVE │
                  │    Pilih: "Opsi A"                  │
                  └──────────────────┬──────────────────┘
                                     │
       ══════════════════════════════╪═════════════════════════════
       SISTEM AUTO-CASCADE AKTIF: TANPA PROMPT MANUAL PENGGUNA LAGI
       ══════════════════════════════╪═════════════════════════════
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 5. BIMO (@projectmanager)           │
                  │    Auto-Dispatch Task-02            │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 6. RAKA (@researcher)               │
                  │    Katalog Deep-Dive & Brief Riset  │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 7. BIMO (@projectmanager)           │
                  │    Auto-Dispatch Task-03            │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 8. BRAM (@sketchwriter)             │
                  │    Copywriting Hook & Visual Prompt │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 9. BIMO (@projectmanager)           │
                  │    Auto-Dispatch Task-04            │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 10. VINA (@visualcarousel)          │
                  │     Sketsa Mockup Wireframe 5 Slide │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 11. BIMO (@projectmanager)          │
                  │     Final Quality Gate & Presentasi │
                  └─────────────────────────────────────┘
```

---

## 3. Spesifikasi & Setup Content Scheduler (Multi-Day Automation)

Tujuan scheduler adalah menjalankan pipeline beberapa hari berturut-turut untuk menghasilkan paket carousel mingguan tanpa perlu mengetikkan prompt setiap pagi.

### A. Matriks Jadwal Konten Mingguan (Weekly Content Sprint)

| Hari | Tema Brief Terjadwal | Pilar Gaya | Target Persona | Fokus Produk Katalog |
|:---|:---|:---|:---|:---|
| **Senin (Day 1)** | "Monday Morning Campus Rush: Outfit Kuliah Santai" | **Urban** | Mahasiswi aktif (18-21 th) | Oversized Graphic Tee + Barrel Denim + Liunic Tote Bag |
| **Selasa (Day 2)** | "Sweet Cafe Study Date: Outfit Perpustakaan Estetik" | **Romantic** | Mahasiswi feminin (19-22 th) | Fitted Crop Tee Lilac + Stripes Pleated Skort + Cable Sweater |
| **Rabu (Day 3)** | "Midweek Internship Look: Smart Casual Presentation" | **Chic** | Mahasiswi magang / First-jobber (21-24 th) | Contrast Rib Crop Tee + Contrast Collar Jacket + Straight Denim |
| **Kamis (Day 4)** | "Rainy Day Comfort: Cozy Knit & Coffee Hangout" | **Urban/Chic** | Gen Z Explorer (18-23 th) | Furry Sweater Multicolor + High Waist Denim Pants |
| **Jumat (Day 5)** | "TGIF Night Out: Sunset Walk to Casual Dinner" | **Romantic/Chic** | Urban Babes (20-25 th) | Sleeveless Suede Mini Dress + Bubble Hem Hoodie |

### B. Konfigurasi Cron Scheduler

Eksekusi scheduler dapat menggunakan antarmuka cron atau background worker:

```yaml
# Scheduler Definition: Colorbox 5-Agent Content Pipeline
scheduler:
  name: colorbox-carousel-daily-generator
  timezone: "Asia/Jakarta"
  cron: "0 8 * * 1-5"  # Setiap Senin - Jumat pukul 08:00 WIB
  channel: "#colorbox-marketing-groupchat"
  
  environment:
    BRAND: "Colorbox Indonesia"
    CATALOG_PATH: "hermes/colorbox/colorbox-knowledge/product-catalog.md"
    AUTO_CASCADE: true
    AUTO_APPROVE_DEFAULT: true   # Jika user tidak memilih dalam 30 menit, pilih Opsi A
    APPROVAL_TIMEOUT_MINUTES: 30
    
  daily_prompts:
    day_1: "Jalankan sprint Day 1: Inspirasi outfit kuliah santai (Urban Campus). Prioritaskan kenyamanan ruang kelas ber-AC dan mobilitas tinggi."
    day_2: "Jalankan sprint Day 2: Outfit cafe study date yang manis dan feminin (Romantic Pastel)."
    day_3: "Jalankan sprint Day 3: Smart casual look untuk magang kampus dan presentasi (Chic Smart)."
    day_4: "Jalankan sprint Day 4: Cozy knitwear styling untuk musim hujan / hangout sore santai."
    day_5: "Jalankan sprint Day 5: Friday night casual dinner & hangout outfit (Versatile Chic)."
```

---

## 4. Mekanisme Penanganan Agen Macet (Stuck Recovery & Error Handling)

1. **Timeout Trigger (Watchdog):**
   Jika sebuah agen tidak memberikan respons dalam window waktu 120 detik, Bimo mengirimkan *ping* pengingat.
2. **Pendeteksian Halusinasi Produk (Katalog Mismatch):**
   Jika `@researcher` atau `@marketingstrategist` menyebut produk yang tidak ada di `product-catalog.md`, Bimo otomatis menolak draf tersebut dengan format:
   ```markdown
   ⚠️ [BIMO REJECTION - PRODUCT NOT IN CATALOG]
   @researcher: Produk "[Nama Produk]" tidak terdaftar pada katalog resmi Colorbox.
   Harap periksa kembali berkas hermes/colorbox/colorbox-knowledge/product-catalog.md 
   dan ganti dengan item valid dalam kategori yang sama.
   ```
3. **Pendeteksian Sketsa Visual Kurang Lengkap:**
   Jika `@visualcarousel` hanya mengirimkan deskripsi teks tanpa diagram wireframe kanvas atau penempatan safe zone, Bimo meminta regenerasi sketsa visual.
4. **Batas Maksimal Retry:**
   Maksimal 3 kali percobaan per task. Jika tetap gagal, Bimo mengeksekusi *fallback plan* (menggunakan template terverifikasi sebelumnya) dan memberi tahu user.

---

## 5. Simulasi Percakapan Penuh di Group Chat (End-to-End Chat Log)

Berikut adalah simulasi jalannya workflow 5 agen di Group Chat:

```
[08:00:00] [SCHEDULER BOT]: 🔔 TRIGGER HARIAN AKTIF (Day 1 Sprint)
"Halo Tim Marketing Colorbox! Jadwal konten hari ini: 'Inspirasi outfit kuliah santai'."
--------------------------------------------------------------------------------------
[08:00:05] Bimo (@projectmanager): 
"Selamat pagi tim! Bimo ambil alih koordinasi. Brief hari ini: Inspirasi Outfit Kuliah Santai.
Task-01 diinisialisasi.
@marketingstrategist tolong petakan audiens, tentukan pilar gaya, dan siapkan 3 opsi konsep 
beserta produk katalog resminya ya. Let's go! 🚀"
--------------------------------------------------------------------------------------
[08:00:30] Meda (@marketingstrategist): 
"Morning Babes! Meda udah analisis briefnya. Untuk outfit kuliah santai, target kita mahasiswi Gen Z. 
Berikut 3 opsi konsep terbaik dari katalog resmi Colorbox:

🌸 Opsi A: 'Effortless Campus Rebel' (Urban) -> Oversized Graphic Tee + Barrel Denim + Liunic Tote Bag
🌸 Opsi B: 'Sweet Pastel Break' (Romantic) -> Fitted Crop Tee Lilac + Stripes Pleated Skort + Cable Sweater
🌸 Opsi C: 'Smart Casual Presentation' (Chic) -> Contrast Rib Crop Tee + Contrast Collar Jacket + Straight Denim

Rekomendasi utama Meda adalah OPSI A karena paling relatable dengan rutinitas kuliah pagi.
Silakan pilih Opsi A, B, atau C ya @projectmanager / User!"
--------------------------------------------------------------------------------------
[08:01:10] User / Scheduler: 
"Pilih Opsi A."
--------------------------------------------------------------------------------------
[08:01:15] Bimo (@projectmanager): 
"Siap, Opsi A (Effortless Campus Rebel) disetujui!
SISTEM AUTO-CASCADE AKTIF: Tim akan mengeksekusi sampai tuntas tanpa perlu dipanggil satu per satu.

📋 [DISPATCH TASK-02] -> @researcher
Objektif: Validasi data resmi katalog ketiga item Opsi A dan susun Creative Research Brief 
lengkap dengan formula carousel 5-slide. Ditunggu hasilnya Raka!"
--------------------------------------------------------------------------------------
[08:01:45] Raka (@researcher): 
"🔍 Riset selesai Bimo! Data terverifikasi 100% dari product-catalog.md:
1. Oversized Fit Short Sleeve Graphic T-Shirt - OFF WHITE (Rp 99.900)
   - Size: S/M (LD ±99 cm), Siluet: Oversized relaxed. Foto auto-ingested ke images/
2. High Waist Barrel Denim Pants - BLACK (Rp 329.900)
   - Size: 26-30 (Size 27-28 LP 65-72 cm, BB 48-57 kg). Foto siap di images/cbx-02-high-waist-barrel-denim-black.jpg
3. Colorbox x Liunic Tote Bag - ECRU (Rp 199.900)
   - Foto siap di images/cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg
Total Look: Rp 629.700. Panduan ukuran cm dan fitting type sudah selesai diriset dari product-size-reference.md.
Riset tren Instagram mengonfirmasi formula 5 slide: Cover hook relatable, Top breakdown, 
Bottom silhouette, Flat lay accessories, dan Outro CTA.
Creative Brief lengkap sudah diunggah. Silakan dilanjutkan!"
--------------------------------------------------------------------------------------
[08:01:50] Bimo (@projectmanager): 
"Mantap Raka! Verifikasi katalog lolos tanpa halusinasi, foto produk terarsip aman di folder images/, dan spek ukuran cm lengkap.
📋 [DISPATCH TASK-03] -> @sketchwriter
Objektif: Tulis naskah on-screen copy 5 slide, caption Instagram resmi, dan prompt visual AI (FLUX/Midjourney) per slide berdasarkan brief Raka. Gas Bram!"
--------------------------------------------------------------------------------------
[08:02:25] Bram (@sketchwriter): 
"✍️ Siap Bimo! Paket copy dan prompt visual AI sudah beres:
- Slide 1 Hook: 'Kelas Jam 8 Pagi, Tetap Slay Tanpa Pusing.'
- Slide 2: Oversized Graphic Tee highlight
- Slide 3: High Waist Barrel Denim highlight
- Slide 4: Colorbox x Liunic Tote Bag & essentials
- Slide 5: Outro & CTA Save postingan
Caption resmi dengan #NeverJustOneThing dan metadata terverifikasi siap.
5 Prompt visual FLUX/Midjourney rasio 4:5 siap dirender. Silakan dicek!"
--------------------------------------------------------------------------------------
[08:02:30] Bimo (@projectmanager): 
"Copywriter on fire! Copy tajam dan prompt visual detail.
📋 [DISPATCH TASK-04] -> @visualcarousel
Objektif: Susun arsitektur visual dan sketsa wireframe mockup nyata untuk kelima slide carousel 
agar tim bisa melihat tata letaknya langsung di chat. Waktu dan tempat dipersilakan Vina!"
--------------------------------------------------------------------------------------
[08:03:15] Vina (@visualcarousel): 
"🖼️ Halo tim! Vina telah merender KELIMA SLIDE GAMBAR FINAL (1080 × 1350 px PNG) menggunakan foto produk asli Colorbox!
Karena ini format FEED CAROUSEL (bukan Reels), seluruh tombol UI (username, like, comment, bookmark) berada di LUAR gambar, jadi kanvas kita manfaatkan 100% full-bleed secara leluasa dan clean:

📦 Berkas Gambar Final Siap Tayang:
1. slide_1_cover_hero.png (Cover Hook + Total Look Rp 629.700)
2. slide_2_hero_top.png (Chambray Shirt Rp 140.900 diskon 53% + Fit Guide)
3. slide_3_bottom_pairing.png (Barrel Denim Black Rp 329.900 + Spec Sz 27-28)
4. slide_4_accessories_flatlay.png (Liunic Tote Bag Ecru Rp 199.900 + Mini Skort)
5. slide_5_outro_cta.png (Rekap 3 item resmi + Call to Action Save Post)

🌐 Pratinjau Interaktif Live:
Buka carousel_preview.html untuk menggeser langsung kelima slide di browser.
Paket visual final siap posting!"
--------------------------------------------------------------------------------------
[08:03:20] Bimo (@projectmanager): 
"🎉 EXCELLENT WORK TEAM! Seluruh alur selesai tanpa kendala.

📊 LAPORAN QUALITY CONTROL BIMO:
- Verifikasi Katalog: 100% Valid (Tanpa Halusinasi)
- Format Konten: Carousel 5-Slide Instagram Feed Portrait (1080x1350 px)
- Visual Production: 5 Berkas PNG Gambar Final Selesai Dirender + Live HTML Preview
- Status Pipeline: 🟢 SELESAI & SIAP PUBLIKASI

Materi konten 'Effortless Campus Rebel' telah siap diproduksi dan diarsipkan ke jadwal posting.
Terima kasih semuanya!"
```

---

## 6. Ringkasan Implementasi & Checklist Kesiapan

- [x] **Agent 1 (Bimo):** Mampu mendispatch tugas, auto-cascade antar-agen, unblocking, dan memantau status kanban.
- [x] **Agent 2 (Meda):** Memahami persona Gen Z, 3 pilar gaya (Urban, Romantic, Chic), dan mengurasi 3 opsi dari katalog resmi.
- [x] **Agent 3 (Raka):** Memvalidasi SKU, warna resmi, harga, dan menyusun Content Research Brief 5 slide.
- [x] **Agent 4 (Bram):** Menulis hook headline, copy per slide, caption terverifikasi, dan prompt visual AI (FLUX/Midjourney).
- [x] **Agent 5 (Vina):** Menghasilkan sketsa visual wireframe ASCII/block yang terlihat, safe-zone layout, dan spec desain.
- [x] **Content Scheduler:** Mendukung eksekusi beruntun multi-hari (Day 1 s.d. Day 5) dengan trigger cron mandiri.

