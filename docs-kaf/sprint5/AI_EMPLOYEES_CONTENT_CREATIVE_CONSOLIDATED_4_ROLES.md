# AI Top Trends — Content & Creative Division: Consolidated 4-Bot Architecture
## Penataan Ulang Struktur Peran AI Employee (Sprint 5)

> **Referensi Brief:** [ClickUp Sprint Brief](https://app.clickup.com/90182967516/v/dc/2kzn5r6w-5798/2kzn5r6w-2038)  
> **Katalog Induk:** [AI Top Trends Master Catalog 30 Pegawai AI v1.0](https://app.clickup.com/90182967516/v/dc/2kzn5r6w-5998)  
> **Status:** Konsolidasi Efisiensi Tim Kreatif (Dari 8 Jabatan Menjadi 4 Jabatan Terpadu)  
> **Versi Dokumen:** v3.0 (Universal Master Framework & Multi-Industry Grounding)  
> **Tanggal Efektif:** 23 November 2026  
> **Penanggung Jawab:** R&D Content & Creative (Ivana)

---

### 1. Filosofi Master B2B Template & Dynamic Knowledge Base

Berdasarkan tinjauan arsitektur produk dan arahan mentor:
*   **Universal Core Template:** Seluruh profil inti (Scope, Persona, Modular Skills, SOP 8 Tahap, Aturan Operasional, Template Output) dirancang **100% generik** menggunakan placeholder terstandarisasi: `[Nama Brand]`, `[Industri]`, `[Produk Unggulan]`, `[Target Audiens]`, `[Pilar Konten]`, `[Kanal Distribusi Aktif]`, `[CTA Resmi]`.
*   **Dynamic Business Grounding:** Konteks bisnis tidak di-hardcode ke dalam kode bot, melainkan disuntikkan secara dinamis melalui **Knowledge Base (KB)** yang diunggah klien saat onboarding (`brand-guidelines.md`, `product-catalog.md`, `audience-persona.md`, `channels-setup.md`, `promotional-calendar.md`).
*   **Multi-Industry Scenarios:** Contoh penerapan merek (seperti Colorbox) ditempatkan secara eksplisit pada **Bagian 3 (Triggers & Use Cases)** dengan label jelas yang mencakup 3 industri nyata:
    1.  **Contoh Kasus 1: Industri Fashion Retail** (e.g. Colorbox / apparel — mix & match, lookbook carousel, GRWM video).
    2.  **Contoh Kasus 2: Industri F&B / Kuliner** (e.g. Kopi Sore Hari / Artisan Bakery — sensory experience, warm ambiance, barista POV).
    3.  **Contoh Kasus 3: Industri Jasa / Skincare & Klinik** (e.g. GlowLab Aesthetic Clinic — doctor authority, active ingredient breakdown, treatment journey).
*   **Rigorous QA Testing:** Setiap profil bot dilengkapi dengan 3–5 **QA Test Scenarios** (Uji Anti-Halusinasi Produk & Harga, Uji Safe Zone Layar, Uji Penanganan Data Kosong, Uji Brand Safety).

---

### 2. Matriks Konsolidasi Peran (8 Peran ➔ 4 Peran Terpadu)

| Kode Baru | Jabatan Konsolidasi Baru | Peran Asal yang Digabung | Tanggung Jawab Inti Terpadu | Dokumen Detail |
|---|---|---|---|---|
| **`CRE-01`** | **Content Strategist** | `CRE-01` Content Strategist + `CRE-08` Content Distribution Specialist | Merancang pilar konten `[Pilar Konten]`, riset audiens & tren, menyusun kalender editorial terpadu, membuat creative brief, adaptasi format kanal, serta mengelola antrean scheduler pasca-persetujuan Level 2. | [`01_CONTENT_STRATEGIST.md`](./01_CONTENT_STRATEGIST.md) |
| **`CRE-02`** | **Content & Copywriter** | `CRE-02` Content Writer + `CRE-03` Copywriter | Menghasilkan naskah tulisan persuasif, caption medsos berdaya konversi tinggi, hook viral 3 detik, teks slide carousel 1–5, naskah spoken dialog video, serta artikel blog SEO tanpa halusinasi harga/produk. | [`02_CONTENT_AND_COPYWRITER.md`](./02_CONTENT_AND_COPYWRITER.md) |
| **`CRE-03`** | **Graphic & Motion Designer** | `CRE-04` Graphic Designer + `CRE-06` Motion Graphics Specialist | Merancang aset visual statis (feed carousel 4:5 Portrait 1080x1350 px, banner web), spec sheet kanvas dengan zona aman 100% (Zero Text Clipping), foto produk asli berkaidah Contain Mode, tipografi kinetik, dan Master AI Visual Prompts fotorealistik. | [`03_GRAPHIC_AND_MOTION_DESIGNER.md`](./03_GRAPHIC_AND_MOTION_DESIGNER.md) |
| **`CRE-04`** | **Video & UGC Creator** | `CRE-05` Video Creator + `CRE-07` UGC Specialist | Merancang konsep video pendek vertikal 9:16 (TikTok/Reels/Shorts), naskah storyboard detik-demi-detik, panduan talent UGC berkamera smartphone, kurasi audio viral berlisensi komersial, dan penataan takarir ramah penonton tanpa suara. | [`04_VIDEO_AND_UGC_CREATOR.md`](./04_VIDEO_AND_UGC_CREATOR.md) |

---

### 3. Alur Orkestrasi Multi-Agent (Autonomous Creative Cascade)

```
                  [MGT-01 Project Manager / Klien]
                                │ (Brief Kampanye / Drop Produk Baru)
                                ▼
        ┌─────────────────────────────────────────────────┐
        │  CRE-01 | Content Strategist & Distribution     │
        │  • Analisis Knowledge Base & Katalog Resmi      │
        │  • Tentukan Content Pillars & Kalender Jadwal   │
        │  • Rilis Master Creative Brief                  │
        └───────────────────────┬─────────────────────────┘
                                │
                                ▼
        ┌─────────────────────────────────────────────────┐
        │  CRE-02 | Creative Content & Copywriter         │
        │  • Naskah Slide-by-Slide Carousel (1-5)         │
        │  • Thumb-Stopping Hooks & Engagement Captions   │
        │  • Spoken Video Script & Ad Conversion Copy     │
        └───────────────┬─────────────────┬───────────────┘
                        │                 │
           (Teks Slide & Copy)       (Spoken Script & Story)
                        │                 │
                        ▼                 ▼
        ┌─────────────────────────┐  ┌─────────────────────────┐
        │ CRE-03 | Graphic &      │  │ CRE-04 | Video &        │
        │ Motion Designer         │  │ UGC Creator             │
        │ • 4:5 Portrait Carousel │  │ • Vertical 9:16 Concept │
        │ • Safe Zone Layout 100% │  │ • Second-by-Second Board│
        │ • Contain Mode Photos   │  │ • UGC Talent Smartphone │
        │ • Kinetic Typography    │  │ • Commercial Audio Sync │
        │ • Master AI Prompts     │  │ • Sound-Off Subtitles   │
        └───────────────┬─────────┘  └───────────┬─────────────┘
                        │                        │
                        └───────────┬────────────┘
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────┐
        │  Human-in-the-Loop Review (Level 2 Approval)    │
        │  • Klien meninjau paket lengkap di antarmuka    │
        │  • Klik "Setujui" untuk publikasi / produksi    │
        └─────────────────────────────────────────────────┘
```

---

### 4. Matriks Hak Akses & Sistem Otorisasi 3 Tingkat

| Tingkat Akses | Hak Agen AI | Contoh Tindakan Nyata |
|---|---|---|
| **🟢 Level 1: Otonom (Autonomous)** | Menjalankan analisis internal, merumuskan variasi teks, menghitung koordinat kanvas, memeriksa kata-kata dilarang. | • Membaca katalog produk resmi<br>• Menghasilkan draf awal naskah<br>• Menghitung margin safe-zone piksel |
| **🟡 Level 2: Wajib Persetujuan (Approval Required)** | Menahan tindakan hingga ada konfirmasi eksplisit dari supervisor / klien manusia di sistem antarmuka. | • Mengunci kalender konten bulanan<br>• Mengirimkan payload jadwal ke scheduler medsos<br>• Memfinalisasi spec sheet produksi visual |
| **🔴 Level 3: Khusus Manusia (Human-Only)** | Dilarang keras dieksekusi oleh agen AI; wajib dilakukan langsung oleh pemilik akun manusia. | • Mengubah identitas logo / warna brand utama<br>• Eksekusi budget iklan berbayar (top-up saldo)<br>• Pernyataan resmi krisis hukum / PR |

---

### 5. Arsitektur Memori 5 Layer Hermes

1.  **Layer 1 (Session Memory):** Konteks percakapan aktif yang sedang dibahas hari ini.
2.  **Layer 2 (Employee Memory):** Standar operasional internal peran masing-masing bot (formula copywriting, koordinat desain, ritme video).
3.  **Layer 3 (Customer/Tenant Memory):** Profil bisnis klien `[Nama Brand]`, batasan industri `[Industri]`, dan dokumen brand guidelines resmi.
4.  **Layer 4 (Project Memory):** Kalender kampanye aktif bulan berjalan dan status kartu tugas kreatif di papan Kanban.
5.  **Layer 5 (Long-Term Memory):** Pola performa historis (jam tayang terbaik, format dengan save rate tertinggi) untuk iterasi strategi berkelanjutan.

---

### 6. Manifest File Deliverables Resmi

Seluruh dokumen profiling, buku panduan eksekutif, dan preview interaktif telah dihasilkan dan disinkronkan ke lokasi berikut:

1.  **Dokumen Spesifikasi Teknis (.md):**
    *   [`01_CONTENT_STRATEGIST.md`](./01_CONTENT_STRATEGIST.md)
    *   [`02_CONTENT_AND_COPYWRITER.md`](./02_CONTENT_AND_COPYWRITER.md)
    *   [`03_GRAPHIC_AND_MOTION_DESIGNER.md`](./03_GRAPHIC_AND_MOTION_DESIGNER.md)
    *   [`04_VIDEO_AND_UGC_CREATOR.md`](./04_VIDEO_AND_UGC_CREATOR.md)
2.  **Buku Panduan Eksekutif (.docx):**
    *   `Buku_Panduan_dan_Profiling_4_Pegawai_AI_Content_Creative.docx` (Tersimpan di `backend/docs-kaf/sprint5`, `frontend/docs-kaf/sprint5`, workspace root, dan `karyawan ai`).
3.  **Dokumen Word Individual (.docx per bot):**
    *   `CRE-01_Content_Strategist.docx` (dan salinan `_Updated.docx`)
    *   `CRE-02_Content_and_Copywriter.docx`
    *   `CRE-03_Graphic_and_Motion_Designer.docx`
    *   `CRE-04_Video_and_UGC_Creator.docx`
4.  **Halaman Web Interaktif (.html & .mhtml per bot):**
    *   `Karyawan AI — CRE-01 - Content Strategist.html` & `.mhtml`
    *   `Karyawan AI — CRE-02 - Content & Copywriter.html` & `.mhtml`
    *   `Karyawan AI — CRE-03 - Graphic & Motion Designer.html` & `.mhtml`
    *   `Karyawan AI — CRE-04 - Video & UGC Creator.html` & `.mhtml`
    *(Tersimpan di `D:/Users/IVANAGITA/aitoptrends/karyawan ai/`, `backend/docs-kaf/sprint5/`, `frontend/docs-kaf/sprint5/`, dan artifacts).*
