# AI Top Trends — Content & Creative Division: Consolidated 4-Bot Architecture
## Penataan Ulang Struktur Peran AI Employee (Sprint 5)

> **Referensi Brief:** [ClickUp Sprint Brief](https://app.clickup.com/90182967516/v/dc/2kzn5r6w-5798/2kzn5r6w-2038)  
> **Katalog Induk:** [AI Top Trends Master Catalog 30 Pegawai AI v1.0](https://app.clickup.com/90182967516/v/dc/2kzn5r6w-5998)  
> **Status:** Konsolidasi Efisiensi Tim Kreatif (Dari 8 Jabatan Menjadi 4 Jabatan Terpadu)  
> **Tanggal Efektif:** 23 November 2026

---

### 1. Matriks Konsolidasi Peran (8 Peran ➔ 4 Peran Terpadu)

Untuk meningkatkan efisiensi komputasi, menyederhanakan alur orkestrasi multi-agent, dan memberikan pengalaman pengguna (UX) yang lebih terintegrasi bagi klien bisnis B2B, divisi **Content & Creative** disederhanakan dari 8 peran menjadi **4 Pegawai AI komprehensif**:

| Kode Baru | Jabatan Konsolidasi Baru | Peran Asal yang Digabung | Tanggung Jawab Inti Terpadu | Dokumen Detail |
|---|---|---|---|---|
| **`CRE-01`** | **Content Strategist** | `CRE-01` Content Strategist + `CRE-08` Content Distribution Specialist | Merancang pilar konten, riset audiens & tren, menyusun kalender terpadu, membuat creative brief, adaptasi format kanal, serta mengelola antrean dan jadwal distribusi otomatis. | [`01_CONTENT_STRATEGIST.md`](./01_CONTENT_STRATEGIST.md) |
| **`CRE-02`** | **Content & Copywriter** | `CRE-02` Content Writer + `CRE-03` Copywriter | Menghasilkan narasi edukatif terstruktur (artikel blog, SEO, size guide) sekaligus pesan persuasif berdaya konversi tinggi (hook, caption medsos, copy iklan, teks slide carousel, CTA). | [`02_CONTENT_AND_COPYWRITER.md`](./02_CONTENT_AND_COPYWRITER.md) |
| **`CRE-03`** | **Graphic & Motion Designer** | `CRE-04` Graphic Designer + `CRE-06` Motion Graphics Specialist | Merancang aset visual statis (poster, carousel 5 slide 4:5, banner web) dan elemen grafis bergerak (motion graphics, kinetic typography, logo bumper, transisi visual dinamis). | [`03_GRAPHIC_AND_MOTION_DESIGNER.md`](./03_GRAPHIC_AND_MOTION_DESIGNER.md) |
| **`CRE-04`** | **Video & UGC Creator** | `CRE-05` Video Creator + `CRE-07` UGC Specialist | Merancang konsep video pendek vertikal (TikTok/Reels 9:16), storyboard detik-demi-detik, panduan talent UGC, shot list kamera HP, dan demonstrasi gaya padu padan busana autentik. | [`04_VIDEO_AND_UGC_CREATOR.md`](./04_VIDEO_AND_UGC_CREATOR.md) |

---

### 2. Alur Orkestrasi Multi-Agent (Autonomous Creative Cascade)

Dalam sistem multi-agent Hermes dan BFF Service, keempat bot ini bekerja dalam sebuah siklus produksi yang saling terhubung secara terstruktur:

```
                  [MGT-01 Project Manager / Klien]
                                │ (Brief Kampanye / Drop Produk Baru)
                                ▼
        ┌─────────────────────────────────────────────────┐
        │  CRE-01 | Content Strategist & Distribution     │
        │  • Analisis Katalog & Riset Tren                │
        │  • Tentukan Content Pillars & Kalender Jadwal   │
        │  • Rilis Master Creative Brief                  │
        └───────────────────────┬─────────────────────────┘
                                │
                                ▼
        ┌─────────────────────────────────────────────────┐
        │  CRE-02 | Content & Copywriter                  │
        │  • Naskah Slide-by-Slide (Slide 1–5)            │
        │  • Pilihan Hook Thumb-Stopping                  │
        │  • Teks Iklan, Caption Medsos, & CTA            │
        └───────────────────────┬─────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐
│ CRE-03 | Graphic & Motion     │ │ CRE-04 | Video & UGC Creator  │
│ Designer                      │ │                               │
│ • Render 5 Slide Carousel PNG │ │ • Storyboard TikTok/Reels 9:16│
│ • Safe-Zone Boundary Check    │ │ • Brief Talent & Shot List HP │
│ • Kinetic Typography & Bumper │ │ • Dynamic On-Screen Captions  │
└───────────────┬───────────────┘ └───────────────┬───────────────┘
                │                                 │
                └───────────────┬─────────────────┘
                                ▼
        ┌─────────────────────────────────────────────────┐
        │  CRE-01 | Queue Scheduling & Distribution       │
        │  • Verifikasi Aset & Kepatuhan Format Platform  │
        │  • Masukkan ke Antrean Scheduler (Level 2)      │
        │  • Monitor Metriks Performa Pasca Tayang        │
        └─────────────────────────────────────────────────┘
```

---

### 3. Kepatuhan Penuh Terhadap 11 Mandatory Checklist

Setiap dokumen peran telah memuat kesebelas komponen wajib yang dipersyaratkan oleh sprint brief:
1. **Scope of Work & Boundaries:** Pemisahan tegas antara tanggung jawab sendiri (*In Scope*), tanggung jawab peran lain (*Out of Scope*), dan mekanisme kolaborasi.
2. **Persona, Language & Tone of Voice:** Karakter peran, derajat formalitas, preferensi istilah industri fesyen/marketing, dan format tampilan.
3. **Triggers & Use Cases:** Contoh prompt pemicu dari user dan minimal 3 skenario dunia nyata konkret.
4. **Modular Skills & Capabilities:** Pemetaan keterampilan *Core*, *Supporting*, dan *Advanced*.
5. **SOP & Task Execution Pattern:** Siklus kerja 8 tahap standar (*Understand $\rightarrow$ Analyze $\rightarrow$ Clarify $\rightarrow$ Plan $\rightarrow$ Execute $\rightarrow$ Verify $\rightarrow$ Report $\rightarrow$ Follow Up*).
6. **Operating Rules & Prohibitions:** Prinsip operasional berbasis katalog riil (Zero Hallucination) dan daftar larangan keras.
7. **Tools, Integrations & Permissions:** Matriks hak akses (*Read / Write / Execute / Approval Required*) berbasis prinsip *Least Privilege*.
8. **Knowledge Base & Memory Needs:** Dokumen wajib dari klien dan integrasi arsitektur memori 5 layer Hermes (Session, Employee, Customer, Project, Long-term).
9. **Input & Expected Output Standards:** Input yang dibutuhkan dari pengguna dan standar format deliverable siap pakai.
10. **Approval & Escalation Rules:** Pembagian tindakan ke dalam Level 1 (Otonom), Level 2 (Butuh Persetujuan), dan Level 3 (Khusus Manusia) beserta protokol eskalasi.
11. **Model Recommendation & KPIs:** Kategori model LLM, tingkat *reasoning effort*, suhu (*temperature*), dan metrik keberhasilan terukur.
