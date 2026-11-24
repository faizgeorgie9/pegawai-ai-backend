# LAPORAN EVALUASI & PENINGKATAN MUTU VISUAL BOT KARYAWAN AI
## Perombakan Arsitektur Prompt, Estetika Editorial Fashion & Anti-Canned Grid

> **Tanggal:** 24 November 2026 | 14:56 WIB  
> **Brand Uji Coba:** COLORBOX (Fashion Retail Gen-Z & Young Women)  
> **Produk Utama:** Oversized Fit Short Sleeve Graphic T-Shirt (LT. PINK / Miami Beach Sunset Club — Rp 99.900)  
> **Status Verifikasi:** 100% Mengadopsi 5 Gaya Estetika Modern Referensi Pengguna  

---

## 1. Latar Belakang & Analisis Masukan Pengguna

Pengguna memberikan kritik membangun dan arahan visual yang sangat presisi:
1. **Penolakan Template Jadul / Kaku:**  
   Format sebelumnya yang hanya memotong foto produk kotak lalu memasukkannya ke dalam card grid dinilai jadul, kaku, dan membosankan untuk audiens media sosial fashion saat ini.
2. **Kaidah Isolasi Produk & Estetika Realistis (Ghost Mannequin / Fur Flatlay):**  
   Pengguna menghendaki produk pakaian diekstrak/diisolasi dari tubuh model, lalu diletakkan di atas background bertekstur alami (seperti karpet bulu lembut) dengan pencahayaan golden-hour hangat, bayangan dedaunan alami, dan properti pendukung estetis (kacamata retro, vas bunga kering), persis seperti foto referensi Asbhoel tee yang dikirimkan.
3. **Kepatuhan Mutlak Rasio Aspek Produk (Strict Aspect Ratio):**  
   Dilarang keras melakukan resize sembarangan yang meregangkan (*stretch*) atau memipihkan (*squash*) bentuk baju atau celana. Proporsi pakaian harus 100% akurat sesuai bentuk fisik aslinya.
4. **Penerapan Gaya Editorial Instagram Asli Colorbox:**  
   Mengadopsi format nyata yang terbukti viral di akun Instagram Colorbox:
   *   *Split Editorial + Pinterest Moodboard Grid* ("Jakarta\* Styled." dengan kurasi aksesori trendi).
   *   *On-Model Detail Zoom Callouts* (4 kotak zoom kuning presisi yang menyorot detail jahitan, print, dan fitting).
   *   *Ambient Location Shoot* (Model di boutique studio keramik antik bernuansa artistik).
   *   *Interactive Paper-Doll Wardrobe* (Lemari vintage pink khas Colorbox dengan stiker pakaian bergaris tepi putih dan polling komunitas).
5. **Video UGC Dinamis (CRE-04):**  
   Video vertikal 9:16 yang menampilkan animasi lemari vintage membuka pintu, stiker pakaian meluncur dengan efek bouncy, bertransisi ke model cewek asli Colorbox yang memperagakan busananya secara stylish.

---

## 2. Peningkatan Standar Operasional & Prompt Bot (CRE-03 & CRE-04)

Tim sistem telah memperbarui secara permanen file panduan peran dan keterampilan di `d:\Users\IVANAGITA\aitoptrends\karyawan ai\templates_agents\`:

### A. Perubahan pada `CRE-03 Graphic & Motion Designer` (`ROLE.md` & `SKILL.md`):
*   **Aturan Anti-Jadul & Anti-Canned Grid:** Menolak keras pembuatan layout grid brosur kaku. Carousel Instagram fashion wajib dirancang sebagai *Editorial Lookbook & Aesthetic Moodboard*.
*   **Mandat Rasio Aspek 100% Presisi:** Objek pakaian wajib diisolasi dan di-scale menggunakan rumus proporsional `scale = min(max_w/orig_w, max_h/orig_h)`. Dilarang mendistorsi bentuk pakaian.
*   **5 Pilar Gaya Estetika Modern:** Mengintegrasikan 5 gaya wajib (Cozy Fur Flatlay, Split Editorial Pinterest, Detail Zoom Insets, Ambient Location, dan Paper-Doll Wardrobe).

### B. Perubahan pada `CRE-04 Video & UGC Creator` (`ROLE.md` & `SKILL.md`):
*   **Standard Animasi Lemari Interaktif & Paper-Doll:** Mengatur ritme animasi pintu lemari 3D membuka, stiker meluncur bouncy, partikel bintang berkilau, dan transisi ke model asli.
*   **Casting Konsistensi Gender:** Memastikan talent perempuan muda yang ekspresif dan relevan dengan audiens Colorbox.
*   **Pacing & Safe Zone:** Menghilangkan teks bertumpuk, mengedepankan gerakan visual yang memikat (*satisfying loop*).

---

## 3. Rincian Eksekusi 5 Slide Carousel & Video UGC

### 📸 Slide 1: Aesthetic Cozy Fur Flatlay (Sesuai Foto 2 — Asbhoel Style)
*   **Visual:** T-shirt pink Colorbox dengan sablon otentik *Miami Beach Sunset Club* dilipat rapi dan diletakkan di atas karpet bulu (*fluffy fur rug*) cream mewah.
*   **Lighting:** Cahaya matahari sore (*golden hour*) alami menyapu dari kiri atas, menciptakan bayangan siluet daun palem tropis lembut di atas bahan kaos dan karpet.
*   **Properti:** Kacamata retro wireframe emas di sebelah kiri dan vas botol kaca berisi bunga kering baby's breath di kanan bawah.
*   **File:** [`slide_1_cover_hero.png`](file:///d:/Users/IVANAGITA/aitoptrends/karyawan%20ai/output_graphic_tee/slide_1_cover_hero.png)

### 📸 Slide 2: Split Editorial + Pinterest Moodboard Grid (Sesuai Foto 5 — "Jakarta* Styled")
*   **Visual Top (50%):** Foto model cantik Colorbox mengenakan pink tee di suasana lifestyle santai dengan tipografi chic *"Jakarta\* Styled."*
*   **Visual Bottom (50%):** Clean Pinterest moodboard flatlay berlatar putih bersih: T-shirt pink Colorbox, segelas iced americano dingin, kacamata hitam oval 90s, Apple AirPods Max silver, rok denim overlap, tas selempang kulit hitam (*slouchy bag*), dan ballet flats.
*   **File:** [`slide_2_hero_top.png`](file:///d:/Users/IVANAGITA/aitoptrends/karyawan%20ai/output_graphic_tee/slide_2_hero_top.png)

### 📸 Slide 3: On-Model Detail Zoom Callouts (Sesuai Foto 3 — Colorbox Official Post)
*   **Visual:** Foto model cewek Colorbox berdiri di bawah sinar matahari hangat luar ruangan.
*   **Fitur Callout:** 4 kotak zoom kuning presisi (*yellow border callout insets*) yang terhubung garis tipis ke:
    1.  *Zoom 1 (Kiri Atas):* Profil wajah ceria dan anting perak model.
    2.  *Zoom 2 (Kiri Tengah):* Tekstur sablon macro *Miami Beach Sunset Club*.
    3.  *Zoom 3 (Kanan Tengah):* Potongan ribbed collar dan jahitan drop shoulder.
    4.  *Zoom 4 (Kiri Bawah):* Drape kain kaos dan perpaduan ban pinggang denim hitam.
*   **File:** [`slide_3_bottom_pairing.png`](file:///d:/Users/IVANAGITA/aitoptrends/karyawan%20ai/output_graphic_tee/slide_3_bottom_pairing.png)

### 📸 Slide 4: Editorial Ambient Location Shoot (Sesuai Foto 4 — Ceramic Boutique Style)
*   **Visual:** Model cantik Colorbox dalam setting boutique studio tembikar dan piring keramik artistik dengan pencahayaan hangat, bernuansa editorial majalah fashion tinggi.
*   **File:** [`slide_4_accessories_layering.png`](file:///d:/Users/IVANAGITA/aitoptrends/karyawan%20ai/output_graphic_tee/slide_4_accessories_layering.png)

### 📸 Slide 5: Paper-Doll Wardrobe / Ghost Mannequin (Sesuai Foto 1 & Video Wardrobe)
*   **Visual:** Lemari vintage pastel pink berukir nama *"COLORBOX"* di sebelah kanan. Di sebelah kiri melayang stiker pakaian (Pink Graphic Tee, Double Breasted Crop Jacket, dan Black Barrel Denim) bergaris tepi putih dengan bayangan halus, dihiasi bintang pastel dan polling interaktif.
*   **File:** [`slide_5_outro_cta.png`](file:///d:/Users/IVANAGITA/aitoptrends/karyawan%20ai/output_graphic_tee/slide_5_outro_cta.png)

### 🎬 Video UGC Reels / TikTok 9:16 (CRE-04)
*   **Visual Animasi:** Pintu lemari pink Colorbox membuka dalam ruang 3D, stiker pakaian meluncur secara bouncy, bintang pastel berkilau, lalu bertransisi mulus ke model cewek asli Colorbox yang sedang fit-check outfit.
*   **Fitur Reels:** Dynamic like counter (+24.8K ❤️), audio ticker (*Colorbox • Sunset Club Original Audio*), dan caption estetik minimalis.
*   **File Video:** [`ugc_video.mp4`](file:///d:/Users/IVANAGITA/aitoptrends/karyawan%20ai/output_graphic_tee/ugc_video.mp4) | [`ugc_video.webm`](file:///d:/Users/IVANAGITA/aitoptrends/karyawan%20ai/output_graphic_tee/ugc_video.webm)

---

## 4. Tautan Pratinjau Interaktif

Seluruh materi dapat dilihat secara langsung dan berdampingan melalui browser:
👉 **[Buka Interactive Carousel Preview](file:///d:/Users/IVANAGITA/aitoptrends/karyawan%20ai/output_graphic_tee/carousel_preview.html)**
