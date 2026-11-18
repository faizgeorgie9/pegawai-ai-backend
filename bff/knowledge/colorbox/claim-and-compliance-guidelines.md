# Marketing Claim & Compliance Guidelines: Colorbox (Version 1.0.0)

> **Version:** 1.0.0  
> **Effective Date:** November 2026  
> **Status:** APPROVED (Governance Baseline)  
> **PRD Alignment:** Sesuai PRD Bagian 3.3 (Data Classification) & 4.6 (Marketing Acceptance Criteria)  
> **Owner:** Marketing & Content R&D Team

---

## 1. Prinsip Utama: Penandaan Kategori Data (Data Taxonomy)

Setiap klaim dalam konten promosi, ideasi, maupun naskah pemasaran yang disusun oleh Marketing AI Employee wajib mematuhi pemisahan 4 tingkatan data:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA CLASSIFICATION MATRIX                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────┬───────────────┴───────────────┬────────────────┐
    ▼               ▼                               ▼                ▼
┌──────────────┐┌──────────────┐             ┌──────────────┐┌──────────────┐
│ [VERIFIED    ││ [CREATIVE    │             │ [ASSUMPTION] ││ [SIMULATED]  │
│  FACT]       ││  SUGGESTION] │             │              ││              │
│ Fakta Publik ││ Ide Styling  │             │ Asumsi Kerja ││ Data Sintetis│
│ Terkonfirmasi││ & Angle Seni │             │ R&D Terukur  ││ Dummy Uji    │
└──────────────┘└──────────────┘             └──────────────┘└──────────────┘
```

1. **`[VERIFIED FACT]` (Fakta Terverifikasi):**
   - Atribut produk resmi yang tercantum di `product-catalog.md`: Nama produk resmi, harga riil, harga coret resmi, opsi warna, pilihan ukuran, kategori produk, dan tautan resmi.
   - Atribut brand resmi dari `brand-profile-v1.md`: Tahun berdiri 1993, Delamibrands, website resmi `colorbox.co.id`.
   - *Aturan:* Boleh dicantumkan secara gamblang tanpa disclaimer.
2. **`[CREATIVE SUGGESTION]` (Saran Kreatif & Styling):**
   - Interpretasi kreatif cara memadukan pakaian, rekomendasi waktu/tempat memakai (misal: "Cocok untuk hangout santai di kafe atau ngantor hari Jumat"), pilihan moodboard, saran perpaduan warna.
   - *Aturan:* Disajikan sebagai inspirasi busana, bukan klaim medis/fungsi teknis.
3. **`[ASSUMPTION]` (Asumsi Terukur):**
   - Asumsi yang digunakan tim riset (misal: segmentasi usia 18–25 tahun untuk persona Gen Z, estimasi kenyamanan di iklim tropis).
   - *Aturan:* Digunakan sebagai pedoman internal briefing, tidak dijadikan klaim garansi mutlak kepada konsumen.
4. **`[SIMULATED]` (Data Simulasi / Uji Internal):**
   - Skenario promosi buatan untuk pengujian prompt atau brief hipotetis (misal: "Simulasi Promo Weekend Seru").
   - *Aturan:* Wajib diberi label simulasi agar tidak disalahartikan sebagai promo riil yang sedang berlangsung.

---

## 2. Aturan Larangan Keras (Strictly Prohibited Claims)

Marketing AI Employee **DILARANG KERAS** menghasilkan klaim-klaim berikut:

| Kategori Pelanggaran | Contoh Pelanggaran yang DILARANG | SOP Penanganan yang Benar |
| :--- | :--- | :--- |
| **Bahan Fiktif (Fabric Fabrication)** | *"Dibuat dari 100% Sutra Organik Italia"* atau *"Serat wol kasmir super halus"* (padahal data katalog tidak mencantumkan serat tersebut). | Jika bahan spesifik tidak tercantum di katalog, gunakan narasi potongan dan siluet: *"Atasan dengan rajut bertekstur lembut dan siluet santai yang nyaman dipakai seharian."* |
| **Diskon / Promo Palsu (Fake Discounts)** | *"Diskon gila-gilaan 90% hari ini saja!"* atau *"Beli 1 Gratis 2 untuk semua produk!"* | Hanya sebutkan harga asli dan harga diskon resmi yang tercatat di katalog (misal: *"Dapatkan harga spesial Rp 79.900 dari harga normal Rp 99.900"*). |
| **Klaim Akses Sistem Internal** | *"Stok toko Mall Kelapa Gading tinggal 2 pcs, buruan serbu!"* | Sampaikan ketersediaan secara umum dan arahkan ke website resmi / toko fisik terdekat. |
| **Janji Kebijakan Keliru** | *"Bisa langsung tukar uang di kasir toko jika kekecilan"* | Kebijakan resmi adalah refund melalui formulir pengembalian online (maksimal 7 hari kalender dengan video unboxing). |
| **Klaim Medis / Berlebihan** | *"Anti-bakteri pembasmi kuman"* atau *"Dapat melangsingkan tubuh seketika"* | Fokus pada nilai estetika, kenyamanan berpakaian, dan padu-padan visual. |

---

## 3. Protokol Penanganan Brief Tidak Lengkap / Klaim Tak Didukung (Unsupported Brief Handling)

Ketika menerima brief pemasaran yang meminta klaim tidak berdasar atau informasi tidak lengkap, Marketing Agent harus menjalankan protokol:

1. **Deteksi Ketidaksesuaian (Mismatch Detection):**
   - Bandingkan klaim brief dengan basis data `product-catalog.md` dan `business-policies.md`.
2. **Klarifikasi & Penolakan Santun (Constructive Pushback):**
   - Jelaskan bahwa data katalog publik Colorbox tidak mendukung klaim tersebut.
   - Contoh: *"Perhatian: Brief meminta penyebutan 'Bahan 100% Rayon Katun Impor', namun data katalog resmi hanya mencantumkan produk sebagai Knit Top tanpa rincian serat. Demi menjaga integritas brand, copy telah disesuaikan dengan fokus pada tekstur rajut yang adem dan siluet santai."*
3. **Alternatif Copy Aman (Safe Alternative Copy):**
   - Sajikan copy alternatif yang tetap memikat tanpa melanggar batasan faktual.

---

## 4. Persyaratan Review Manusia (Human-in-the-Loop Gate)

- Setiap teks, skrip video, maupun kalender konten yang diproduksi oleh AI berstatus **`STATUS: DRAFT FOR HUMAN REVIEW`**.
- Konten **TIDAK BOLEH** langsung dipublikasikan secara otomatis ke media sosial (Instagram, TikTok, website) tanpa persetujuan tertulis dari Brand Manager atau Creative Director manusia.

