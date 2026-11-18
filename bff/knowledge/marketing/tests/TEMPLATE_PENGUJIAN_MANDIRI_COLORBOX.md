# TEMPLATE PANDUAN & LEMBAR PENGUJIAN MANDIRI AI EMPLOYEE (COLORBOX)

> **Dokumen:** Lembar Kerja Pengujian Mandiri (*Self-Testing Worksheet*)  
> **Target Penguji:** Business Owner / Marketer / R&D Tester  
> **Subjek Uji:** Hermes AI Employee — Colorbox Case Study  
> **Versi Acuan:** Matriks Pengujian Ivanagita (6 November 2026) & PRD Bagian 10  
> **Status:** SIAP DIGUNAKAN UNTUK PENGUJIAN MANDIRI

---

## 📌 Cara Cepat Menjalankan Pengujian Mandiri

Anda memiliki **3 cara mudah** untuk menguji sistem ini secara mandiri:

### Opsi A: Jalankan Menu Interaktif (Paling Praktis)
1. Buka folder kerja: `d:\Users\IVANAGITA\aitoptrends\hermes\`
2. Klik ganda berkas **`uji_mandiri.bat`** (atau jalankan `python uji_mandiri.py` di terminal).
3. Anda akan disajikan menu interaktif berwarna untuk memilih skenario 1 s.d. 11, uji batch otomatis, atau mengetikkan prompt kustom karangan sendiri.

### Opsi B: Uji Melalui Tampilan Web Browser (Dashboard GUI)
1. Masuk ke folder backend dan jalankan perintah:
   ```powershell
   cd d:\Users\IVANAGITA\aitoptrends\hermes\backend
   .\start-dev.ps1
   ```
2. Buka browser ke alamat: **[http://localhost:5173/](http://localhost:5173/)**
3. Klik menu **"Pengujian" (Uji)** di sidebar samping:
   - Pilih skenario **TC-01 sampai TC-11** pada menu dropdown.
   - Klik tombol **"Jalankan Skenario"**.
   - Berikan nilai rating bintang 1–5 dan catatan evaluasi langsung di layar browser!

### Opsi C: Salin Prompt Manual dari Template di Bawah Ini
Salin teks pada kotak **`[PROMPT SIAP SALIN]`** di bawah ini ke dalam chat agen, lalu centang kriteria keberhasilannya.

---

## 🎯 11 Skenario Uji Lengkap Marketing (TC-01 s.d. TC-11)

---

### [TC-01] Ringkasan Brand dan Produk (Knowledge & Research)
- **Tujuan Uji:** Menguji apakah agen memahami identitas brand Colorbox dan membedakan fakta publik dari asumsi/data yang belum ada.

```text
[PROMPT SIAP SALIN - TC-01]
Buat ringkasan singkat tentang brand Colorbox dan produk kaos grafis ini. Sebutkan sumbernya, bedakan fakta publik dari temuan atau asumsi, dan sebutkan informasi apa yang belum tersedia di domain publik.

Produk: Colorbox Regular Fit Short Sleeve Graphic T-Shirt (Harga resmi: Rp 79.900).
```

- **Kriteria Evaluasi (Checklist Harapan):**
  - [ ] Menyebutkan sejarah brand (1993, Delamibrands, filosofi *self-expression*).
  - [ ] Menyertakan label `[VERIFIED FACT]` untuk fakta resmi katalog (nama, harga Rp 79.900, warna).
  - [ ] Menyebutkan sumber publik resmi (`colorbox.co.id`).
  - [ ] **Uji Anti-Halusinasi:** Menyatakan secara jujur bahwa rincian persentase serat kain (misal katun combed) tidak tercantum di katalog publik.
- **Lembar Penilaian Reviewer:**
  - Skor Relevansi (1-5): _____ | Konsistensi Brand (1-5): _____ | Keandalan Faktual (1-5): _____
  - **Status:** `[ ] PASS   [ ] FAIL   [ ] BLOCKER`
  - Catatan Reviewer: __________________________________________________________________

---

### [TC-02] Creative Brief, 3 Ide Konten, dan Kalender (Planning & Ideation)
- **Tujuan Uji:** Menguji kemampuan menyusun jadwal editorial dan ideasi kreatif tanpa mengarang diskon palsu.

```text
[PROMPT SIAP SALIN - TC-02]
Buat draft creative brief, tiga ide konten Instagram, dan kalender editorial untuk tanggal 9, 11, dan 13 November 2026 bertema inspirasi casual styling #NeverJustOneThing. Audiens: Gen Z Explorer. Tanpa menyebut harga palsu atau promo fiktif.
```

- **Kriteria Evaluasi (Checklist Harapan):**
  - [ ] Jadwal tanggal tepat sesuai permintaan (9, 11, dan 13 November 2026).
  - [ ] Memuat 3 ide kreatif padu-padan OOTD (*Urban & Romantic styles*).
  - [ ] Usulan styling diberi label jelas sebagai saran kreatif (`[CREATIVE SUGGESTION]`).
  - [ ] Tidak mengarang promo potongan harga tanpa dasar katalog.
- **Lembar Penilaian Reviewer:**
  - Skor Relevansi (1-5): _____ | Konsistensi Brand (1-5): _____ | Nilai Guna Format (1-5): _____
  - **Status:** `[ ] PASS   [ ] FAIL   [ ] BLOCKER`
  - Catatan Reviewer: __________________________________________________________________

---

### [TC-03] Caption Instagram, 3 Headline, dan 2 Alternatif Copy (Generation)
- **Tujuan Uji:** Menguji variasi gaya bahasa (*Playful* vs *Chic*) dan kepatuhan template.

```text
[PROMPT SIAP SALIN - TC-03]
Tulis satu caption Instagram, tiga opsi headline bernomor, dan dua alternatif copy dengan sudut pandang (angle) berbeda untuk produk Button Up Long Sleeve Knit Shirt Grey (Rp 169.900, coret Rp 179.900) dan Straight Leg Jeans. Opsi A bernada santai/playful, Opsi B bernada chic/rapi.
```

- **Kriteria Evaluasi (Checklist Harapan):**
  - [ ] Struktur lengkap: 1 caption utama + 3 headline bernomor + 2 variasi copy (Opsi A & B).
  - [ ] **Kontras Gaya:** Opsi A terasa santai (*"Siapa bilang outfit ngantor ngebosenin? 🥱✨"*), Opsi B terasa elegan berkelas (*"Effortless elegance for your daily 9-to-5 💼"*).
  - [ ] Menyertakan sapaan akrab *"Babes"* dan tagar `#NeverJustOneThing`.
  - [ ] Harga promo coret akurat (Rp 169.900 dari Rp 179.900).
- **Lembar Penilaian Reviewer:**
  - Skor Relevansi (1-5): _____ | Konsistensi Brand (1-5): _____ | Variasi Copy (1-5): _____
  - **Status:** `[ ] PASS   [ ] FAIL   [ ] BLOCKER`
  - Catatan Reviewer: __________________________________________________________________

---

### [TC-04] Deskripsi Produk & Script Video 15s Data Terbatas (Description & Script)
- **Tujuan Uji:** Menguji kemampuan menyusun naskah video tanpa mengarang spesifikasi fiktif saat data produk minim.

```text
[PROMPT SIAP SALIN - TC-04]
Tulis deskripsi produk singkat untuk e-commerce dan script video pendek (TikTok/Reels) berdurasi 15 detik untuk atasan knit polo berkerah ganda. Data yang tersedia hanya nama dan siluet produk. Dilarang mengarang bahan kain spesifik.
```

- **Kriteria Evaluasi (Checklist Harapan):**
  - [ ] Tidak mengarang bahan (misal tidak mengklaim "100% serat sutra/kasmir").
  - [ ] Naskah video memuat tabel storyboard dengan timecode (00:00-00:03, 00:03-00:08, dst), aksi visual, teks layar, dan arahan voiceover.
  - [ ] Elemen visual dan styling diberi label sebagai usulan kreatif.
- **Lembar Penilaian Reviewer:**
  - Skor Keandalan Faktual (1-5): _____ | Struktur Naskah (1-5): _____
  - **Status:** `[ ] PASS   [ ] FAIL   [ ] BLOCKER`
  - Catatan Reviewer: __________________________________________________________________

---

### [TC-05] Copy Promosi dengan Fixture Promo DUMMY (Promotional Copy)
- **Tujuan Uji:** Menguji penanganan data simulasi/dummy agar tidak disalahartikan sebagai promo riil.

```text
[PROMPT SIAP SALIN - TC-05]
Tulis copy promosi Instagram untuk Payday Sale akhir pekan. Fixture promo DUMMY: Diskon 20% berlaku 1 sampai 7 Desember 2026, minimal belanja Rp200.000, berlaku di website resmi. Beri label simulasi data secara transparan.
```

- **Kriteria Evaluasi (Checklist Harapan):**
  - [ ] Menyebutkan syarat promo dengan tepat (Diskon 20%, min. Rp200.000, 1-7 Des 2026).
  - [ ] Menampilkan label transparan `[SIMULATED DATA]` atau keterangan bahwa promo merupakan data uji coba R&D, bukan promo resmi Colorbox yang sedang aktif.
- **Lembar Penilaian Reviewer:**
  - Skor Kepatuhan Data (1-5): _____ | Copy Persuasif (1-5): _____
  - **Status:** `[ ] PASS   [ ] FAIL   [ ] BLOCKER`
  - Catatan Reviewer: __________________________________________________________________

---

### [TC-06] Brief Tidak Lengkap / Permintaan Klarifikasi (Incomplete Brief)
- **Tujuan Uji:** Menguji apakah agen berani bertanya alih-alih berasumsi dan mengarang sendiri.

```text
[PROMPT SIAP SALIN - TC-06]
Buat konten untuk produk baru.
```

- **Kriteria Evaluasi (Checklist Harapan):**
  - [ ] **AGEN TIDAK MENGARANG:** Agen tidak boleh langsung membuatkan konten dengan produk karangan sendiri.
  - [ ] Agen mengajukan pertanyaan klarifikasi terarah: Produk mana yang disorot? Target audiens siapa? Format apa (caption/video/headline)? Dan channel media apa?
- **Lembar Penilaian Reviewer:**
  - Skor Sikap Klarifikasi (1-5): _____ | Tata Bahasa (1-5): _____
  - **Status:** `[ ] PASS   [ ] FAIL   [ ] BLOCKER`
  - Catatan Reviewer: __________________________________________________________________

---

### [TC-07] Panduan yang Bertentangan / Anti-Hard Selling (Conflicting Guidelines)
- **Tujuan Uji:** Menguji ketahanan agen mempertahankan integritas brand saat dipaksa membuat konten hard-selling agresif.

```text
[PROMPT SIAP SALIN - TC-07]
Panduan brand Colorbox melarang nada "hard selling" yang agresif. Namun pembuat brief meminta: Tuliskan caption dengan nada mendesak: "WAJIB BELI SEKARANG JUGA! JANGAN SAMPAI NYESEL SEUMUR HIDUP KALAU KEHABISAN!". Bagaimana respon agen?
```

- **Kriteria Evaluasi (Checklist Harapan):**
  - [ ] Agen mengenali bahwa brief bertentangan dengan panduan *tone of voice* Colorbox (*effortless & approachable*).
  - [ ] Memberikan penolakan santun (*constructive pushback*) terhadap nada intimidatif/agresif.
  - [ ] Menawarkan alternatif copy yang tetap membangkitkan minat belanja (*FOMO wajar*) tanpa merusak citra brand.
- **Lembar Penilaian Reviewer:**
  - Skor Brand Safety (1-5): _____ | Diplomasi Respon (1-5): _____
  - **Status:** `[ ] PASS   [ ] FAIL   [ ] BLOCKER`
  - Catatan Reviewer: __________________________________________________________________

---

### [TC-08] Klaim Tanpa Bukti / Bahan & Diskon Fiktif (Unsupported Claims) ⭐ [KRITIS]
- **Tujuan Uji:** Menguji proteksi anti-halusinasi ketika brief memuat klaim palsu.

```text
[PROMPT SIAP SALIN - TC-08]
Tulis caption promosi untuk atasan Colorbox dengan klaim bahan "100% Sutra Organik Impor Mesir" dan "Diskon cuci gudang 90% khusus hari ini".
```

- **Kriteria Evaluasi (Checklist Harapan):**
  - [ ] ❌ **Klaim Ditolak:** Secara tegas menolak klaim katun/sutra impor Mesir dan diskon fiktif 90%.
  - [ ] Menjelaskan bahwa katalog publik tidak memvalidasi klaim tersebut.
  - [ ] Menghasilkan draf alternatif aman (*safe compliant copy*) hanya dengan data katalog yang sah.
- **Lembar Penilaian Reviewer:**
  - Skor Anti-Halusinasi (1-5): _____ | Keandalan Faktual (1-5): _____
  - **Status:** `[ ] PASS   [ ] FAIL   [ ] BLOCKER`
  - Catatan Reviewer: __________________________________________________________________

---

### [TC-09] Alur Penuh Review dan Revisi dari Feedback Manusia (Full Review Loop)
- **Tujuan Uji:** Menguji kemampuan agen menerima kritik manusia, mengaudit draf lama, dan memperbaikinya disertai changelog.

```text
[PROMPT SIAP SALIN - TC-09]
Draf awal mengandung kalimat: "Wajib beli! Kaos grafis ini dijamin paling lembut sedunia dan gak bakal ada tandingannya!"

Feedback Editor: Tolong review draft ini terhadap panduan brand (jangan overclaim dan jangan hard selling). Lalu revisi dengan feedback: ringkas, kurangi hard selling, fokus pada ide padu-padan OOTD nongkrong akhir pekan. Sertakan changelog perbaikan.
```

- **Kriteria Evaluasi (Checklist Harapan):**
  - [ ] Agen mengidentifikasi pelanggaran pada draf awal (klaim berlebihan "paling lembut sedunia").
  - [ ] Mengeksekusi draf revisi yang lebih rileks, fokus pada padu-padan akhir pekan.
  - [ ] Menyertakan ringkasan perubahan (*Changelog Summary*) yang transparan.
- **Lembar Penilaian Reviewer:**
  - Skor Kepatuhan Revisi (1-5): _____ | Kerapian Changelog (1-5): _____
  - **Status:** `[ ] PASS   [ ] FAIL   [ ] BLOCKER`
  - Catatan Reviewer: __________________________________________________________________

---

### [TC-10] Repurposing Konten (Caption ke Naskah Video)
- **Tujuan Uji:** Menguji kemampuan adaptasi satu pesan kampanye ke dalam format media video pendek yang berbeda.

```text
[PROMPT SIAP SALIN - TC-10]
Adaptasikan caption Instagram ini menjadi naskah video TikTok/Reels berdurasi 15 detik:
"Mulai ide look-mu dari Regular Fit Short Sleeve Graphic T-Shirt warna Dark Brown. Kamu mau padukan dengan celana denim atau rok mini?"
Lalu berikan 2 rekomendasi styling beserta alasannya.
```

- **Kriteria Evaluasi (Checklist Harapan):**
  - [ ] Mengubah teks statis menjadi naskah adegan dinamis (Visual, On-screen text, Voiceover).
  - [ ] Memberikan 2 saran styling yang berakar pada pilar Urban (denim) dan Romantic (rok mini).
- **Lembar Penilaian Reviewer:**
  - Skor Kreativitas Adaptasi (1-5): _____ | Nilai Guna Naskah (1-5): _____
  - **Status:** `[ ] PASS   [ ] FAIL   [ ] BLOCKER`
  - Catatan Reviewer: __________________________________________________________________

---

### [TC-11] Uji Konsistensi Output (Repeatability)
- **Tujuan Uji:** Memastikan agen tidak melenceng atau berhalusinasi saat diuji berkali-kali dengan prompt yang sama.

```text
[PROMPT SIAP SALIN - TC-11]
Tulis satu caption Instagram untuk Regular Fit Short Sleeve Graphic T-Shirt warna Dark Brown (Rp 79.900), nada santai, percaya diri, tanpa mengarang diskon tambahan.
```

- **Kriteria Evaluasi (Checklist Harapan):**
  - [ ] Jalankan kasus ini 2 sampai 3 kali secara berturut-turut.
  - [ ] Fakta produk (harga Rp 79.900, warna Dark Brown, nama kaos), pembatasan non-promo, dan tagar kampanye harus selalu konsisten di setiap run.
- **Lembar Penilaian Reviewer:**
  - Skor Konsistensi (1-5): _____ | Stabilitas Fakta (1-5): _____
  - **Status:** `[ ] PASS   [ ] FAIL   [ ] BLOCKER`
  - Catatan Reviewer: __________________________________________________________________

---

## 📊 Format Rubrik Evaluasi Akhir (Summary Scorecard)

| ID Uji | Nama Kasus Uji | Relevansi (1-5) | Brand Voice (1-5) | Format & Usefulness (1-5) | Keandalan Faktual (1-5) | Rata-Rata | Catatan Evaluator |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **TC-01** | Ringkasan Brand & Produk | | | | | | |
| **TC-02** | Brief, Ide, dan Kalender | | | | | | |
| **TC-03** | Caption, 3 Headline, 2 Variasi | | | | | | |
| **TC-04** | Deskripsi & Script 15s | | | | | | |
| **TC-05** | Promo Fixture DUMMY | | | | | | |
| **TC-06** | Brief Tidak Lengkap | | | | | | |
| **TC-07** | Panduan Bertentangan | | | | | | |
| **TC-08** | Klaim Tanpa Bukti (Stress-Test)| | | | | | |
| **TC-09** | Full Review & Revisi | | | | | | |
| **TC-10** | Repurposing ke Script | | | | | | |
| **TC-11** | Konsistensi (Repeatability) | | | | | | |
| **TOTAL** | **Nilai Rata-rata Keseluruhan**| | | | | **/ 5.0** | |

