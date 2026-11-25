# Sistem Desain Carousel Instagram Modular (Editorial & Lookbook)

Dokumen ini berisi panduan **Sistem Desain Carousel Instagram** yang dirancang secara **modular dan *variable-driven*** berdasarkan analisis referensi visual *editorial fashion* muda yang *playful*, *layered*, dan kasual. 

Sistem ini sengaja dibuat **tidak mengunci** produk spesifik, profil/wajah model, maupun satu latar belakang statis—sehingga tim kreatif dapat mengganti produk, model, dan mengambil latar secara dinamis dari **Folder Aset Background** yang sudah tersedia.

---

## 1. Ringkasan Arah Visual (*Art Direction*)

* **Gaya & *Mood*:** Perpaduan *off-duty cool*, *quirky storytelling*, dan *modern retro/Y2K-tinged casual*. Tetap menonjolkan siluet dan detail busana tanpa terasa kaku seperti katalog *e-commerce* konvensional.
* **Karakter *Framing*:** Mayoritas *full-body* atau *three-quarter portrait* yang memberi ruang napas pada komposisi pakaian serta interaksi model dengan lingkungan sekitar.
* **Pencahayaan:** Fleksibel antara cahaya *flash*/studio yang bersih (mempertegas tekstur kain, kulit, dan rajutan) serta cahaya matahari alami (*harsh/natural sunlight*) untuk kesan *candid*.
* **Prinsip Modularitas:** Semua elemen grafis berfungsi sebagai *frame* dan penunjuk informasi ringan yang menyesuaikan komposisi foto, bukan menutupi fokus utama pada produk dan model.

---

## 2. Arsitektur Slot Konten (*Variable Slots*)

Setiap *slide* disusun menggunakan slot variabel yang dapat diisi ulang untuk setiap rilis produk atau kampanye:

| Kode Slot | Fungsi & Deskripsi | Aturan Penggunaan |
| :--- | :--- | :--- |
| **`[SLOT_MODEL_PHOTO]`** | Foto *subject*/model dengan busana koleksi aktif | Bebas berganti model, pose, maupun *framing* (*full-body*, *3/4*, atau *detail crop*). |
| **`[SLOT_BG_ASSET]`** | Aset latar belakang dari **Folder Aset Background** | Dipilih berdasarkan keselarasan warna/kontras dengan busana pada sesi tersebut. |
| **`[SLOT_HOOK_HEADLINE]`** | Judul utama singkat pada *slide* pembuka | Maksimal 4–7 kata; memancing rasa ingin tahu atau merangkum *vibe* koleksi. |
| **`[SLOT_HERO_ITEM]`** | Label generik penunjuk item busana/aksesori | Contoh: `[ITEM UTAMA 1]`, `[OUTER / LAYER]`, `[BOTTOM / FOOTWEAR]`. Posisi mengikuti letak item. |
| **`[SLOT_LAYER_NOTE]`** | Catatan *styling* singkat (1 kalimat/frasa pendek) | Menjelaskan permainan tekstur, potongan, atau tips *mix & match* tanpa menyebut SKU mati. |
| **`[SLOT_DETAIL_CROP]`** | Potongan *close-up* tekstur bahan, jahitan, atau aksesori | Mengisi *slide* detail untuk memperkuat persepsi kualitas fisik produk. |
| **`[SLOT_CTA_BLOCK]`** | Blok ajakan aksi di *slide* terakhir | Dapat diisi ajakan *save*, *share*, *tag* teman, atau informasi kanal belanja. |

---

## 3. Struktur & Alur *Slide* (Template 6 *Slide*)

### Slide 01 — Cover / Hook
* **Komposisi:** `[SLOT_MODEL_PHOTO]` dipadukan dengan `[SLOT_BG_ASSET]` pilihan.
* **Elemen Grafis:**
  * Header kecil di sudut atas: Nomor *slide* (`01 / 06`) dan tag edisi (`[TAG_KOLEKSI / TEMA]`).
  * `[SLOT_HOOK_HEADLINE]` ditempatkan di area ruang kosong (*negative space*) latar belakang.
  * Indikator geser (`SWIPE →`) di pojok kanan bawah.

### Slide 02 — Focus Look A
* **Komposisi:** *Full-body* atau *3/4 shot* dari *look* pertama di atas `[SLOT_BG_ASSET]`.
* **Elemen Grafis:**
  * 1–2 kapsul penunjuk `[SLOT_HERO_ITEM]` yang diarahkan ke bagian busana terkait.
  * Counter `02 / 06` dan `SWIPE →`.

### Slide 03 — Focus Look B / Styling Angle
* **Komposisi:** *Look* kedua (bisa menggunakan model yang sama atau model berbeda) dengan komposisi dinamis.
* **Elemen Grafis:**
  * `[SLOT_LAYER_NOTE]` singkat di sudut bawah/samping untuk menjelaskan konsep padu padan.
  * Counter `03 / 06` dan `SWIPE →`.

### Slide 04 — Detail & Texture Crop
* **Komposisi:** *Close-up* material, detail kerutan/jahitan, atau aksesori pelengkap.
* **Elemen Grafis:**
  * Label mikro `[DETAIL / MATERIAL]` dengan garis penunjuk tipis.
  * Counter `04 / 06` dan `SWIPE →`.

### Slide 05 — Mix & Match / Variation
* **Komposisi:** Kolase 2 *frame* atau variasi gaya *styling* dari aset foto yang tersedia.
* **Elemen Grafis:**
  * Catatan perbandingan singkat (misalnya: *Look 01* vs *Look 02* atau *Day* vs *Night styling*).
  * Counter `05 / 06` dan `SWIPE →`.

### Slide 06 — Closing & Call to Action (CTA)
* **Komposisi:** Kanvas bersih menggunakan warna latar sistem (`#F4EFEA`) atau bingkai tipis di atas `[SLOT_BG_ASSET]` yang tenang.
* **Elemen Grafis:**
  * `[SLOT_CTA_BLOCK]` di tengah kanvas.
  * Counter `06 / 06` dan penanda identitas *brand* di bagian bawah.

---

## 4. Sistem Grid & Ukuran Kanvas

* **Dimensi Kanvas:** `1080 x 1350 px` (Rasio `4:5` — standar vertikal optimal *feed* Instagram).
* **Resolusi Ekspor:** `72–150 DPI`, format `.jpg` (kualitas 85–95%) atau `.png` untuk menjaga ketajaman teks tipis.
* **Margin & *Safe Zone*:**
  * Jarak aman tepi luar: minimal **`64 px`** di seluruh sisi (atas, bawah, kiri, kanan).
  * **Zona Terlarang Teks:** Hindari menempatkan elemen penting tepat di atas area wajah model, lipatan detail baju utama, pojok kanan atas (ikon *carousel* Instagram), serta area tengah bawah (indikator titik *pagination* Instagram).

---

## 5. Token Warna (*Color System*)

Palet warna dirancang netral dan hangat agar harmonis saat dipasangkan dengan berbagai aset dari **Folder Aset Background**:

| Token | Nama Warna | Kode Hex / RGBA | Fungsi Utama |
| :--- | :--- | :--- | :--- |
| `--bg-base` | **Warm Alabaster** | `#F4EFEA` | Latar belakang *slide* penutup, bingkai editorial, dan panel teks |
| `--ink-primary` | **Espresso Ink** | `#231916` | Teks utama, garis pembatas tipis (`1.5 px`), ikon panah, dan counter |
| `--surface-pill` | **Translucent Cream** | `rgba(244, 239, 234, 0.88)` | Latar kapsul/label teks di atas foto agar terbaca tanpa menutup latar sepenuhnya |
| `--border-subtle` | **Soft Taupe** | `rgba(35, 25, 22, 0.20)` | Garis tepi halus pada *card* kolase atau kotak label |
| `--accent-dynamic` | **Variable Accent** | `[ACCENT_COLOR]` | Satu warna aksen opsional per *batch* (diambil dari *mood* foto/latar: *Terracotta* `#B85A3A`, *Cobalt* `#1F5CE6`, *Blush* `#F3C6CF`, atau *Forest* `#2E473B`) |

---

## 6. Sistem Tipografi

Mengombinasikan satu huruf *serif* berkarakter editorial dengan satu huruf *sans-serif* modern yang sangat mudah dibaca pada layar ponsel:

* **Font Editorial / Aksen Judul:** *Playfair Display* atau *Fraunces* (Regular & Italic) — digunakan untuk kata kunci penekanan pada *headline*.
* **Font UI, Label & Body:** *Plus Jakarta Sans* atau *Inter* (Regular, Medium, SemiBold, Bold) — digunakan untuk teks informatif, label item, dan nomor *slide*.

### Skala Tipografi (Kanvas `1080 x 1350 px`)

| Peran Teks | Font Family | Ukuran | Weight | Line Height | Letter Spacing |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Slide Headline / Hook** | Plus Jakarta Sans + Playfair Italic (aksen) | `56–64 px` | SemiBold / Bold | `1.10` | `-0.02em` |
| **Section Tag & Counter** | Plus Jakarta Sans | `20–22 px` | SemiBold | `1.20` | `+0.08em` (*Uppercase*) |
| **Body / Styling Note** | Plus Jakarta Sans | `26–28 px` | Regular / Medium | `1.35` | `0em` |
| **Item Callout Pill** | Plus Jakarta Sans | `18–20 px` | Medium | `1.20` | `+0.02em` |

---

## 7. Komponen Grafis & Aturan Penggunaan Aset

1. **Kapsul Label (*Callout Pill*):**
   * Bentuk persegi sudut halus (`border-radius: 6 px`) atau kapsul (`999 px`) dengan *padding* `10 px 18 px`.
   * Menggunakan latar `--surface-pill` dan garis tepi `1 px solid --ink-primary`.
   * Posisi **tidak dikunci mati**—desainer bebas menggeser kapsul ke sisi kiri, kanan, atas, atau bawah mengikuti posisi produk di dalam foto.
2. **Garis & Aksen Jahitan (*Editorial Hairline*):**
   * Garis lurus `1.5 px` untuk pemisah *header* (`01 / 06` dan kategori) serta garis penunjuk produk dengan titik ujung berdiameter `6 px`.
3. **Aturan Pemilihan dari Folder Aset Background:**
   * **Kontras Siluet:** Pilih `[SLOT_BG_ASSET]` yang memiliki kontras warna/terang-gelap yang jelas terhadap busana model (hindari latar gelap pekat jika model memakai atasan hitam tanpa *rim light*).
   * **Kepadatan Visual:** Jika aset *background* memiliki banyak tekstur atau pola ramai, wajib gunakan latar belakang solid/translusen (`--surface-pill`) di balik semua teks.
   * **Konsistensi Per *Batch*:** Dalam satu rangkaian carousel (6 *slide*), pilih aset *background* dengan temperatur warna (*warm* atau *cool*) dan pencahayaan yang senada agar transisi antar-*slide* tetap menyatu.
4. **Batas Kepadatan Teks:**
   * Maksimal **6–12 kata** per *slide* untuk teks utama. Penjelasan panjang mengenai detail bahan atau cerita kampanye ditempatkan pada *caption* Instagram.

---

## 8. Checklist Produksi Cepat (Per Konten Carousel)

- [ ] Pilih 1 tema/kampanye dan tentukan 1 warna `--accent-dynamic` yang selaras.
- [ ] Siapkan foto-foto `[SLOT_MODEL_PHOTO]` (pastikan mencakup *full look* dan *detail crop*).
- [ ] Pilih pasangan `[SLOT_BG_ASSET]` dari folder aset dengan pencahayaan & kontras yang cocok.
- [ ] Isi variabel teks (`[SLOT_HOOK_HEADLINE]`, `[SLOT_HERO_ITEM]`, `[SLOT_LAYER_NOTE]`, `[SLOT_CTA_BLOCK]`).
- [ ] Pastikan seluruh teks berada di dalam *safe zone* (`64 px`) dan tidak menutupi produk utama.
- [ ] Ekspor seluruh *slide* dalam format `1080 x 1350 px` dan cek urutan *preview* sebelum unggah.
