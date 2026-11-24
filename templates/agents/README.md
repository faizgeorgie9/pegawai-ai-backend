# AI Top Trends — Master AI Employee Templates Architecture (B2B Multi-Industry Framework)

> **Status:** Universal Master Implementation-Ready Templates  
> **Divisi:** Content & Creative (CRE-01 sampai CRE-04)  
> **Filosofi Produk:** *Fixed Immutable Agent Engine + Pluggable Dynamic Knowledge Base*  
> **Standar Versi:** v3.0 | 24 November 2026

---

## 1. Konsep Desain: Mengapa Bot Harus Template?

Dalam arsitektur produk B2B SaaS AI Employee di PT AI Top Trends:
1. **Agen AI bersifat Tetap (Immutable Engine):**
   * Karakter, etika kerja, batasan wewenang (`SOUL.md`), serta standar SOP 8-tahap dan kemampuan modular (`SKILL.md`) **terkunci permanen**. Klien tidak perlu dan tidak boleh mengubah kode logika bot.
2. **Konteks Bisnis Klien bersifat Dinamis (Pluggable Knowledge Base):**
   * Seluruh konteks merek—seperti nama brand, sektor industri, katalog produk, harga resmi, warna desain, dan target konsumen—disuntikkan secara dinamis melalui file **Knowledge Base (KB)** yang diunggah klien saat onboarding.
3. **Zero Hardcoded Bias:**
   * Di dalam file template `SOUL.md`, `SKILL.md`, dan `ROLE.md`, **TIDAK ADA NAMA PERUSAHAAN ATAU PRODUK YANG DI-HARDCODE**. Semua menggunakan placeholder terstandarisasi.

---

## 2. Struktur Folder Template Agen

```
templates/agents/
├── README.md                                          <-- Panduan arsitektur & integrasi
├── CRE-01_Content_Strategist/
│   ├── SOUL.md                                        <-- Persona, karakter, tone, batasan
│   ├── SKILL.md                                       <-- SOP 8-tahap, modular skills, quality gate
│   └── ROLE.md                                        <-- 11 Komponen wajib lengkap master
├── CRE-02_Content_and_Copywriter/
│   ├── SOUL.md
│   ├── SKILL.md
│   └── ROLE.md
├── CRE-03_Graphic_and_Motion_Designer/
│   ├── SOUL.md
│   ├── SKILL.md
│   └── ROLE.md
└── CRE-04_Video_and_UGC_Creator/
    ├── SOUL.md
    ├── SKILL.md
    └── ROLE.md
```

---

## 3. Kamus Variabel Dinamis (Dynamic Injection Slots)

Saat runtime (eksekusi bot), sistem secara otomatis menggantikan placeholder berikut dengan data nyata klien:

| Placeholder | Sumber Data Klien | Contoh Isi (Fashion) | Contoh Isi (F&B) | Contoh Isi (Klinik Skincare) |
|---|---|---|---|---|
| `{{brand_name}}` | Profil Klien | Colorbox | Kopi Sore Hari | GlowLab Aesthetic |
| `{{industry}}` | Profil Klien | Fashion Retail | F&B / Kuliner | Dermatologi & Skincare |
| `{{target_audience}}` | `audience-persona.md` | Wanita Gen Z 18-25th | Pekerja kantoran WFC | Pasien jerawat 20-35th |
| `{{content_pillars}}` | `brand-guidelines.md` | Urban, Romantic, Chic | Sensory, Spot Kerja, Promo | Edukasi Dokter, Q&A, Promo |
| `{{knowledge_catalog}}` | `product-catalog.md` | 1.206 Produk Pakaian | Menu Kopi & Pastry | Daftar Perawatan & Serum |
| `{{official_cta}}` | `channels-setup.md` | Klik link di bio / Web | Pesan via GoFood / Mampir | Booking konsultasi WhatsApp |
| `{{official_hashtag}}`| `brand-guidelines.md` | #NeverJustOneThing | #KopiSoreHari #NgopiSantai | #GlowSkinDoctor #KlinikKulit |

---

## 4. Alur Onboarding Klien Baru (5 Menit Tanpa Coding)

1. Buat profil tenant/klien baru di dashboard.
2. Unggah 5 file Knowledge Base klien:
   * `brand-guidelines.md` (Logo, warna Hex, tone of voice, forbidden words)
   * `product-catalog.md` (Daftar SKU, varian, bahan, harga resmi IDR, foto asli)
   * `audience-persona.md` (Demografi, psikografi, keresahan target audiens)
   * `channels-setup.md` (Kanal medsos aktif, frekuensi posting)
   * `promotional-calendar.md` (Jadwal promo bulanan/tanggal kembar)
3. Bot langsung aktif dan bekerja sesuai SOP master tanpa perlu mengubah baris kode program apa pun.
