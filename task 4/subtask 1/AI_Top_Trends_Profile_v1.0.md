# DUMMY BUSINESS PROFILE & BRAND VOICE SPECIFICATION
**Dokumen:** Shared Benchmark Context Kit (S1-04A)  
**Versi Artefak:** `v1.0.0`  
**Nama Bisnis:** **AI Top Trends** (Fiktif / Dummy)  
**Tujuan Dokumen:** Standar konteks bisnis bersama untuk pengujian benchmark Kandidat A (Hermes Agent), B (MausBot), C (Rakazo), dan D (CrewAI).  
**Penyusun:** Candidate A Researcher (Hermes)  
**Reviewer:** Benchmark Coordinator (Rakazo Researcher) & R&D Lead  
**Status Keamanan Data:** **100% SYNTHETIC & SAFE** (Bebas data pribadi/rahasia)  

---

## 1. Profil Bisnis Fiktif (*Dummy Business Profile*)

| Parameter Bisnis | Nilai Konfigurasi Benchmark |
| :--- | :--- |
| **Nama Brand / Perusahaan** | **AI Top Trends** |
| **Bidang Usaha (Industri)** | Edukasi & Solusi Adopsi Kecerdasan Buatan (AI Agency & Media B2B) |
| **Tagline Utama** | *"Membangun Pekerja Digital yang Menghasilkan Nilai Nyata untuk Bisnis."* |
| **Visi & Misi Bisnis** | Membantu pemilik bisnis lokal dan kreator bertransformasi dari sekadar "mencoba chatbot" menjadi memiliki "Pegawai AI" yang mengotomasi alur kerja pemasaran secara terukur, konsisten, dan aman. |
| **Produk Unggulan MVP** | **"Pegawai AI: Marketing & Content Specialist"** — Paket sistem AI yang menyusun kalender konten, copywriting iklan, adaptasi multi-kanal (IG, TikTok, LinkedIn), dan quality check sebelum disetujui manusia. |
| **Situs Web (Fiktif)** | `https://www.aitoptrends-dummy.internal` |
| **Kontak Bisnis (Fiktif)** | `halo@aitoptrends-dummy.internal` |

---

## 2. Definisi 3 Target Audiens Utama (*Target Audiences*)

Setiap konten yang dihasilkan oleh agen AI harus relevan dan disesuaikan dengan salah satu dari 3 segmen berikut:

### Audiens A: Pemilik Usaha Kecil & Menengah (UMKM / Brand Lokal)
- **Karakteristik:** Pemilik toko online, brand fashion/F&B lokal, reseller e-commerce.
- **Pain Points:** Waktu terbatas, tidak punya tim marketing khusus, kewalahan membuat konten media sosial secara konsisten setiap hari.
- **Kebutuhan:** Solusi praktis dan cepat, bahasa sederhana (hindari istilah teknis rumit), fokus pada peningkatan omzet, hemat biaya, dan kemudahan penggunaan.
- **Pendekatan Pesan:** *"Otomasi konten toko Anda dalam 10 menit tanpa perlu pusing mikirin ide tiap malam."*

### Audiens B: Kreator Konten & Solo Creator (*Creators*)
- **Karakteristik:** Content creator mandiri, freelance copywriter, edukator media sosial.
- **Pain Points:** *Creative burnout*, ide buntu, kesulitan me-repurpose 1 materi panjang menjadi potongan konten TikTok/Instagram/Thread.
- **Kebutuhan:** Inspirasi sudut pandang unik (*angle hook*), struktur skrip video cepat, alur kerja kreatif yang fleksibel.
- **Pendekatan Pesan:** *"Bongkar 1 ide video panjang jadi 5 skrip reels viral dalam 3 menit."*

### Audiens C: Marketer Agensi & Tim Pemasaran Kecil (*Marketers*)
- **Karakteristik:** Digital marketing specialist, social media manager, agensi periklanan.
- **Pain Points:** Menjaga konsistensi brand voice di banyak klien, pelaporan performa, batas waktu produksi kampanye yang ketat.
- **Kebutuhan:** Kalender editorial rapi, metrik terukur (ROI, CTR, lead conversion), dan kepatuhan terhadap approval klien.
- **Pendekatan Pesan:** *"Standarisasi alur kerja konten tim agensi Anda dengan guardrails human-in-the-loop yang aman."*

---

## 3. Panduan Karakter Suara Brand (*Brand Voice & Tone*)

Brand **AI Top Trends** memiliki kepribadian profesional, grounded (membumi), dan berorientasi hasil:

| Dimensi Nada | Aturan Suara Brand | Yang Boleh Dilakukan (*Do's*) | Yang Dilarang (*Don'ts*) |
| :--- | :--- | :--- | :--- |
| **Otoritatif tapi Rendah Hati** | Berbicara seperti praktisi berpengalaman, bukan penjual mimpi. | Berikan data nyata, studi kasus konkret, langkah 1-2-3 yang jelas. | Dilarang membuat janji berlebihan (*"Cepat kaya dengan AI"*, *"100% autopilot tanpa kerja"*). |
| **Praktis & Berorientasi Bisnis** | Fokus pada nilai guna, bukan pamer kecanggihan teknologi. | Jelaskan manfaat bisnisnya (waktu yang dihemat, konsistensi output). | Dilarang memakai jargon AI rumit (hindari istilah *vector embedding*, *temperature sampling* untuk audiens awam). |
| **Transparan & Akuntabel** | Mengedepankan keamanan dan kontrol manusia (*Human-in-the-loop*). | Tegaskan bahwa AI adalah asisten cerdas, keputusan akhir tetap di tangan manusia. | Dilarang mengklaim bahwa AI bisa menggantikan manusia seutuhnya tanpa review. |

---

## 4. Batasan & Aturan Konten (*Content Constraints*)

Seluruh agen kandidat (Hermes, MausBot, Rakazo, CrewAI) wajib mematuhi batasan berikut saat mengeksekusi tugas pembuatan konten:

1. **Wajib Ada Persetujuan Manusia (*No Auto-Publishing*):**  
   Agen dilarang mempublikasikan konten langsung ke platform media sosial. Status akhir berkas harus diberi penanda: `Status: DRAFT_READY_FOR_HUMAN_REVIEW`.
2. **Kewajiban Call-to-Action (CTA):**  
   Setiap output konten harus diakhiri dengan 1 ajakan bertindak yang jelas (misalnya: *"Unduh panduan gratis di bio"*, *"Ketik 'MAU' di kolom komentar"*, atau *"Kunjungi website kami"*).
3. **Standar Format per Saluran:**
   - **Instagram:** Headline/Hook memikat di baris pertama, bodi teks rapi dengan bullet points/spasi paragraf, 3-5 hashtag relevan di akhir.
   - **TikTok / Video Pendek:** Format skrip 3 bagian: `[00:00 - 00:03 Hook Visual/Audio]`, `[00:03 - 00:45 Bodi Solusi/Edukasi]`, `[00:45 - 00:60 Call to Action]`.
   - **LinkedIn / Artikel Blog:** Nada pemikiran profesional (*thought leadership*), fokus pada efisiensi kerja tim dan tren industri.
4. **Keamanan & Kebenaran Fakta (*Factuality & Safety*):**  
   Dilarang memalsukan testimoni pelanggan, dilarang mencantumkan nomor telepon/kredensial asli, dan dilarang mengklaim hasil yang tidak dapat dibuktikan.

---

## 5. Permintaan Uji Coba Standar (*Sample Benchmark Request*)

Permintaan standar yang akan diinputkan secara identik ke 4 kandidat agen:

```json
{
  "request_id": "REQ-BENCH-MKT-001",
  "task_type": "marketing_campaign_draft",
  "business_context": "AI Top Trends (v1.0.0)",
  "target_audience": "Audiens A (Pemilik Toko Online & UMKM Lokal)",
  "campaign_topic": "Mengatasi burnout membuat konten jualan harian dengan Pegawai AI",
  "deliverables_required": [
    {
      "channel": "Instagram Feed",
      "format": "Carousel Script (5 Slides) + Caption + Hashtags"
    },
    {
      "channel": "TikTok / Reels",
      "format": "Short Video Script 45 detik (Hook, Body, CTA)"
    }
  ],
  "constraints": {
    "human_approval_gate": true,
    "forbidden_words": ["autopilot kaya instan", "tanpa kerja", "ajaib"],
    "brand_voice": "Praktis, suportif, berorientasi waktu luang pemilik toko"
  }
}
```

---

## 6. Verifikasi Keamanan Data (*Data Safety Verification*)

- [x] **Zero Real Customer Data:** Tidak ada nama orang, alamat toko, atau merek dagang asli yang dimasukkan ke dalam profil ini.
- [x] **Zero Credentials / Secrets:** Tidak ada kunci API, password, atau token autentikasi di dalam dokumen.
- [x] **Reproducible:** Profil ini dapat diakses dan digunakan secara identik oleh seluruh peneliti untuk mengevaluasi Kandidat A, B, C, dan D secara adil (*fair benchmark*).
