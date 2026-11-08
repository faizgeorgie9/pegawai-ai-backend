# [COLORBOX_CUSTOMER_SERVICE_SOP_V1]
**Version:** 1.0.0 (Released: 2026-11-06)  
**Ref Code:** SOP-CBX-CS-2026  
**Applicability:** EXCLUSIVE to Colorbox Customer Service AI Employee  
**Department Isolation:** Confidential to Customer Service (Marketing Agents MUST NOT access internal return rates or escalation matrix)  

---

## 1. Kebijakan Penukaran Ukuran & Produk (Product Exchange Policy)
* **[VERIFIED_FACT] [SOP-CBX-RET-01] Batas Waktu:** Penukaran ukuran (*size exchange*) hanya dapat dilakukan maksimal **7 (tujuh) hari kalender** terhitung sejak tanggal struk pembelian (toko fisik) atau tanggal barang diterima oleh kurir (pembelian daring).
* **[VERIFIED_FACT] [SOP-CBX-RET-01] Syarat Mutlak Penukaran:**
  1. Struk fisik asli atau nomor bukti pesanan online terverifikasi wajib ditunjukkan.
  2. Label harga (*price tag*) dan label instruksi pencucian (*care label*) masih terpasang utuh tanpa rusak/lepas.
  3. Produk belum pernah dipakai bepergian, belum dicuci, dan tidak berbau parfum/keringat.
  4. Produk pengganti bergantung pada ketersediaan stok di toko terkait.
* **[VERIFIED_FACT] [SOP-CBX-RET-01] Pengecualian (Non-Exchangeable):** Pakaian dalam (*underwear*), kaus kaki, produk promosi bertanda *Final Clearance / Sale 70%*, dan aksesoris anting tidak dapat ditukar demi alasan kebersihan dan sanitasi.
* **[VERIFIED_FACT] [SOP-CBX-RET-01] Pengembalian Dana (Refund):** Colorbox **tidak menerima pengembalian dana dalam bentuk uang tunai (*No Cash Refund*)**. Jika ukuran pengganti habis, pelanggan diberikan voucher belanja nominal senilai barang yang dapat digunakan di seluruh toko.

---

## 2. Kebijakan Logistik & Kendala Pengiriman (Shipping & Delivery SLA)
* **[ASSUMED_POLICY] [SOP-CBX-LOG-02] Estimasi Waktu Pengiriman:**
  * Wilayah Jabodetabek: 2 – 4 hari kerja.
  * Pulau Jawa (Luar Jabodetabek): 3 – 5 hari kerja.
  * Luar Pulau Jawa: 4 – 8 hari kerja (tergantung wilayah kepulauan).
* **[ASSUMED_POLICY] [SOP-CBX-LOG-02] Penanganan Paket Terlambat:** Jika status pengiriman belum berubah setelah melebihi estimasi maksimal + 2 hari kerja, CS wajib membuatkan tiket pelacakan manual (*trace request*) ke mitra logistik.

---

## 3. Kebijakan Barang Rusak / Cacat Produksi (Defective Product)
* **[VERIFIED_FACT] [SOP-CBX-DEF-03] Bukti Wajib Video Unboxing:** Pelanggan wajib menyertakan video saat membuka paket (*unboxing*) tanpa jeda dalam kurun waktu maksimal 48 jam sejak paket diterima.
* **[VERIFIED_FACT] [SOP-CBX-DEF-03] Biaya Ongkos Kirim:** Seluruh ongkos kirim pengembalian dan pengiriman barang baru yang terbukti cacat produksi ditanggung 100% oleh pihak Colorbox.

---

## 4. Matriks Eskalasi Tiket (Escalation Matrix)
* **[SOP-CBX-ESC-04] Prioritas Kategori:**
  * **LOW:** Pertanyaan stok umum, jam buka toko, panduan tabel ukuran (*size chart*).
  * **MEDIUM:** Permintaan tukar ukuran sesuai SOP, pengecekan resi paket dalam rentang SLA wajar.
  * **HIGH:** Paket terlambat lebih dari 4 hari dari batas estimasi, paket hilang dalam perjalanan kurir.
  * **CRITICAL:** Pelanggan mengancam viralkan ke media sosial, tuduhan penipuan, komplain barang reject parah.
* **[SOP-CBX-ESC-04] Syarat Eskalasi ke Manusia (Human Takeover):**
  * Setiap kasus kategori **CRITICAL** wajib langsung dieskalasi ke Supervisor CS manusia dalam kurun waktu 15 menit.
  * Agen AI tidak boleh mendebat pelanggan yang sedang marah; berikan permohonan maaf tulus atas ketidaknyamanan lalu aktifkan eskalasi tiket.

---

## 5. Data Dummy & Fixture Pengujian Simulasi
* **[DUMMY_SIMULATION] Contoh Pesanan Valid:** Nomor `#CBX-2026-9812` (Item: Casual Linen Shirt Pastel Green Size M, Store: Pondok Indah Mall, Status: Selesai).
* **[DUMMY_SIMULATION] Contoh Pesanan Kendala Kurir:** Nomor `#CBX-2026-4401` (Resi: `JNE-CBX-88129031`, Status: Dalam Perjalanan 6 Hari).
