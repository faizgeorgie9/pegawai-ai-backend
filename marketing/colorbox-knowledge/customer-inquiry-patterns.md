# Customer Inquiry Patterns & Scenarios: Colorbox

> **Data Classification:** Research Findings & Simulated Scenarios  
> **Source Reference:** PRD Test Framework & Observasi Interaksi Pelanggan Marketplace/Sosmed  
> **Verification Status:** Pola pertanyaan umum dirancang untuk melatih dan mengevaluasi respon Hermes AI Employee.  
> **Target Pengguna AI:** Customer Service AI Employee & Quality Assurance Evaluation.

---

## 1. Klasifikasi Niat Pelanggan (Customer Intent Classification)

Sistem AI Customer Service harus mampu mengidentifikasi setidaknya 7 kelompok niat utama (*intents*):

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Customer Service AI Intent                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────┬───────────────┼───────────────┬────────────────┐
    ▼               ▼               ▼               ▼                ▼
┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐┌────────────────┐
│ 1. Product   ││ 2. Size &    ││ 3. Mix-Match ││ 4. Order &   ││ 5. Returns &   │
│ Information  ││ Fit Consult  ││ Recommendation│ Shipping     ││ Complaints     │
└──────────────┘└──────────────┘└──────────────┘└──────────────┘└────────────────┘
```

---

## 2. Pola Pertanyaan Populer & Standar Respon AI

### Pola 1: Ketersediaan & Spesifikasi Produk
- **Contoh Pertanyaan Pelanggan:**
  - *"Halo, apakah kemeja Crop Ribbed warna sage masih ada ukuran M?"*
  - *"Ka, celana denim high waist ada warna apa aja ya?"*
  - *"Dress floral ini bahannya tebal atau nerawang?"*
- **SOP Respon AI Employee:**
  1. Cek data katalog produk untuk memastikan nama, opsi warna, dan ukuran.
  2. Berikan informasi harga terkini beserta status potongan harga jika ada.
  3. *Aturan Ketat (Anti-Halusinasi):* Jika informasi stok riil per toko atau detail persentase serat bahan (misal 100% rayon) tidak tertera di data publik, nyatakan secara transparan: *"Berdasarkan data resmi, produk ini berpotongan regular dengan varian warna X dan Y. Untuk ketersediaan stok riil detik ini, silakan periksa keranjang belanja di website resmi atau tanyakan langsung ke CS toko."*

### Pola 2: Konsultasi Ukuran & Siluet (Size & Fit)
- **Contoh Pertanyaan Pelanggan:**
  - *"Tinggi badanku 158 cm, BB 50 kg, kira-kira celana jeans nomor berapa ya biar pas?"*
  - *"Atasan model boxy ini ukurannya kebesaran nggak sih kalau buat badan kecil?"*
  - *"Pinggangku lingkar 70 cm, lebih cocok size 27 atau 28?"*
- **SOP Respon AI Employee:**
  1. Rujuk tabel `product-size-reference.md`.
  2. Jelaskan siluet potongan baju (Regular / Oversized / Cropped).
  3. Untuk celana: Rekomendasikan ukuran 28 (lingkar 69-72 cm) untuk kenyamanan duduk, dan jelaskan toleransi 1-2 cm.

### Pola 3: Rekomendasi & Perbandingan Produk (Product Recommendation & Comparison)
- **Contoh Pertanyaan Pelanggan:**
  - *"Aku mau hangout ke kafe outdoor sore hari, enaknya pakai atasan apa ya yang santai tapi tetap estetik?"*
  - *"Bisa tolong bandingkan antara Oversized Graphic Tee sama Short Sleeve Crop Shirt?"*
- **SOP Respon AI Employee:**
  1. Terapkan pilar gaya Colorbox (*Urban, Romantic, Chic*).
  2. Berikan 2–3 opsi produk yang serasi beserta tautan langsungnya.
  3. Berikan saran padu-padan (*mix-and-match*) bawahannya (misal: celana denim wide leg atau rok midi).

### Pola 4: Informasi Kebijakan, Pengiriman & Pembayaran
- **Contoh Pertanyaan Pelanggan:**
  - *"Kira-kira berapa hari ya paket sampai ke Surabaya?"*
  - *"Bisa bayar COD atau pakai ShopeePay gak di websitenya?"*
  - *"Bisa minta nomor resi pengiriman?"*
- **SOP Respon AI Employee:**
  1. Rujuk `business-policies.md` dan `customer-faq.md`.
  2. Jelaskan estimasi waktu pengiriman (Surabaya: 3–4 hari kerja dengan estimasi proses gudang 48 jam kerja).
  3. Jelaskan bahwa nomor resi otomatis dikirimkan ke email konfirmasi pemesanan.

### Pola 5: Penanganan Keluhan & Komplain (Simulated Complaints)
- **Contoh Pertanyaan Pelanggan:**
  - *"Paket bajuku baru sampai dan kancingnya lepas satu! Mau tukar dong!"*
  - *"Baju yang dikirim salah warna, pesannya lilac yang datang dark brown. Tolong tanggung jawab!"*
- **SOP Respon AI Employee:**
  1. Buka respon dengan empati mendalam dan permohonan maaf atas ketidaknyamanan.
  2. Jelaskan syarat retur secara santun: Video unboxing utuh tanpa jeda, tag belum lepas, dan waktu retur maksimal 7 hari.
  3. Jelaskan bahwa Colorbox tidak melayani penukaran langsung, melainkan proses refund penuh agar pelanggan dapat memesan kembali.
  4. Berikan kontak saluran resmi untuk meneruskan form retur (`csonline@colorbox.co.id` / WhatsApp `0811-1717-250`).

---

## 3. Matriks Eskalasi ke Manusia (Human Escalation Protocol)

AI Employee **wajib segera mengarahkan pelanggan ke tim Customer Service manusia** apabila mendapati kondisi berikut:

| Kondisi Kasus | Pemicu (*Trigger*) | Tindakan AI Employee |
| :--- | :--- | :--- |
| **Konfirmasi Bukti Transfer / Refund** | Pelanggan menagih status transfer uang kembali (*refund*) | Sampaikan bahwa verifikasi mutasi bank memerlukan otorisasi tim finance manusia; arahkan ke WhatsApp resmi `0811-1717-250`. |
| **Perubahan Alamat Mendesak** | Pelanggan salah ketik alamat dan baru selesai checkout (< 1 jam) | Minta pelanggan segera menghubungi WhatsApp CS resmi sebelum paket diproses packing oleh gudang. |
| **Komplain Keras / Frustrasi Tinggi** | Pelanggan menyampaikan ancaman hukum, viralitas, atau amarah berulang | Validasi perasaan pelanggan dengan tenang, mohon maaf, dan berikan nomor kontak escalation supervisor. |
| **Data Di Luar Pengetahuan Publik** | Permintaan data internal perusahaan, stok gudang fisik spesifik, atau dokumen rahasia | Nyatakan dengan jujur bahwa AI tidak memiliki akses ke sistem internal dan sarankan menghubungi kantor operasional. |
