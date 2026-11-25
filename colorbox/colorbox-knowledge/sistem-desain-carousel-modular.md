# Sistem Desain Carousel Instagram Modular (Editorial & Lookbook)

Dokumen ini berisi panduan **Sistem Desain Carousel Instagram** yang dirancang secara **modular, minimalis, dan *variable-driven*** sesuai gaya visual *editorial fashion* muda Colorbox (`SRC-13`).

Sistem ini sengaja dibuat **tidak mengunci** produk spesifik, profil/wajah model, maupun satu latar belakang statis—sehingga tim kreatif dapat mengganti produk, model, dan mengambil latar secara dinamis dari **Folder Aset Background** (`background/`).

---

## 1. Ringkasan Arah Visual (*Art Direction*)

* **Gaya & *Mood*:** Perpaduan *off-duty cool*, *quirky storytelling*, dan *modern retro/Y2K-tinged casual*.
* **Komposit In-Situ (Wajib Remove Background Model):** Foto model katalog yang berlatar belakang polos/studio **WAJIB di-*remove background*** sehingga subjek model berdiri langsung menyatu di atas `[SLOT_BG_ASSET]` dari folder `background/`. **DILARANG** menempelkan foto model berlatar putih sebagai kotak kolase atau kartu bingkai kaku di atas latar belakang.
* **Karakter *Framing*:** *Full-body* atau *three-quarter portrait* yang menyatu natural dengan pencahayaan latar, ditambah *close-up detail* tekstur pada slide berikutnya.
* **Minimasi Tulisan (Zero-Text / Micro-Copy):** Kanvas visual dijaga sangat bersih. Hanya gunakan **1–4 kata *micro-copy*** editorial atau label penunjuk tipis bila perlu. Tidak ada paragraf panjang, tidak ada *counter* kaku berlebihan, dan tidak ada banner promo/harga.

---

## 2. Arsitektur Slot Konten (*Variable Slots*)

| Kode Slot | Fungsi & Deskripsi | Aturan Penggunaan |
| :--- | :--- | :--- |
| **`[SLOT_MODEL_PHOTO]`** | Foto *subject*/model dengan busana koleksi aktif | **Wajib *remove background*** untuk POV *front* / *second-angle* agar menyatu langsung di atas latar `background/`. POV *detail* dapat tampil *full-bleed* fokus kain/jahitan. |
| **`[SLOT_BG_ASSET]`** | Aset latar belakang dari **Folder Aset Background** (`background/`) | Dipilih berdasarkan keselarasan warna/kontras & mood dengan busana pada sesi tersebut. |
| **`[SLOT_MICRO_COPY]`** | Teks editorial sangat singkat (opsional) | **Maksimal 1–4 kata** saja (mis. *"jakarta styled"*, *"structured, effortless"*, *"contrast stitch"*). |
| **`[SLOT_DETAIL_CROP]`** | Potongan *close-up* tekstur bahan, jahitan, atau aksesori | Mengisi *slide* detail (`detail` POV) untuk memperkuat persepsi kualitas fisik produk. |

---

## 3. Struktur & Alur *Slide* (Ringkas: 1–3 *Slide*, Tanpa CTA)

Jumlah *slide* dibuat **ringkas dan padat (1–3 *slide*)**—tidak perlu 6 *slide* dan **tidak menggunakan *slide* CTA penutup**.

### Slide 01 — Cover Hero (*Front* POV In-Situ)
* **Komposisi:** `[SLOT_MODEL_PHOTO]` (*front* POV, sudah *remove background*) berdiri langsung menyatu di atas `[SLOT_BG_ASSET]` *full-bleed* (`1080 x 1350 px`).
* **Elemen Grafis:** Maksimal 1 *micro-copy* singkat (1–4 kata) di area ruang kosong (*negative space*), tanpa kotak kartu dan tanpa *badge* ramai.

### Slide 02 — Detail & Texture Focus (*Detail* POV)
* **Komposisi:** *Close-up* material, detail jahitan kontras, kancing, atau kerah (`detail` POV) *full-bleed* atau dengan bingkai *viewfinder* tipis minimalis.
* **Elemen Grafis:** Opsional label mikro 1–2 kata (mis. *"detail"* atau nama fitur visual).

### Slide 03 — Second Angle / Silhouette (*Back* / *Second* POV In-Situ)
* **Komposisi:** `[SLOT_MODEL_PHOTO]` sudut pandang berbeda (*back* / *second-angle* POV, sudah *remove background*) menyatu langsung di atas `[SLOT_BG_ASSET]` yang senada (atau variasi dari folder `background/`), tanpa *slide* CTA.

---

## 4. Sistem Grid & Ukuran Kanvas

* **Dimensi Kanvas:** `1080 x 1350 px` (Rasio `4:5` — standar vertikal optimal *feed* Instagram).
* **Margin & *Safe Zone*:** Minimal **`64 px`** dari tepi luar untuk teks *micro-copy* apa pun agar tidak terpotong antarmuka Instagram atau menutupi wajah/produk utama.

---

## 5. Token Warna & Tipografi (*Color & Type System*)

| Token | Nama Warna | Kode Hex / RGBA | Fungsi Utama |
| :--- | :--- | :--- | :--- |
| `--bg-base` | **Warm Alabaster** | `#F4EFEA` | Warna dasar netral jika dibutuhkan aksen bingkai tipis |
| `--ink-primary` | **Espresso Ink** | `#231916` | Teks *micro-copy* di area terang & garis tipis |
| `--ink-light` | **Soft Cream** | `#FAF7F2` | Teks *micro-copy* di atas foto gelap dengan *drop shadow* halus |
| `--accent-dynamic` | **Variable Accent** | `[ACCENT_COLOR]` | Aksen opsional sangat halus (*Terracotta* `#B85A3A`, *Cobalt* `#1F5CE6`, *Blush* `#F3C6CF`, *Forest* `#2E473B`) |

* **Tipografi:** *Plus Jakarta Sans* & *Playfair Display* (Italic untuk aksen *micro-copy*).

---

## 6. Checklist Produksi Cepat (1–3 *Slide*)

- [ ] Pastikan `[SLOT_MODEL_PHOTO]` berlatar polos sudah di-***remove background*** agar menyatu mulus di atas `[SLOT_BG_ASSET]`.
- [ ] Gunakan POV model yang berbeda dan sesuai di tiap *slide* (*front*, *detail*, *back* / *second-angle*).
- [ ] Pastikan jumlah *slide* **1–3 *slide*** saja, **tanpa *slide* CTA**.
- [ ] Pastikan tulisan sangat minimal (**1–4 kata** *micro-copy* saja per *slide*).
