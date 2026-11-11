# Source Register & Provenance Index: Colorbox Case Study

> **Data Classification:** Governance & Provenance Record  
> **PRD Alignment:** Sesuai Mandat PRD Bagian 3.2, 3.3, dan 6.4 (Knowledge Hub)  
> **Terakhir Diperbarui:** 2026-11-09  
> **Status Verifikasi:** Seluruh sumber data publik telah diaudit dan dicatat untuk penelusuran (*traceability*).

---

## 1. Daftar Inventaris Sumber Data (Source Inventory)

Berikut adalah rekapitulasi seluruh sumber data eksternal, observasi publik, dan instrumen simulasi yang digunakan dalam penyusunan Shared Business Knowledge Hub untuk Hermes AI Employee:

| Kode Sumber | Nama Sumber / Dokumen | URL / Platform | Klasifikasi Data | Cakupan Penggunaan Dokumen | Status Audit |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SRC-01** | Website Resmi Colorbox Indonesia | [https://colorbox.co.id](https://colorbox.co.id) | Public Data | `brand-profile.md`, `brand-guidelines.md` | Terverifikasi |
| **SRC-02** | Colorbox Official Collection Catalog | [https://colorbox.co.id/collections/colorbox-collection](https://colorbox.co.id/collections/colorbox-collection) | Public Data | `product-catalog.md` (1.206 Produk) | Terverifikasi via Endpoint API Resmi |
| **SRC-03** | Colorbox Official Size Guide | [https://colorbox.co.id](https://colorbox.co.id) | Public Data | `product-size-reference.md` | Terverifikasi |
| **SRC-04** | Kebijakan Retur & Syarat Ketentuan Resmi | [https://colorbox.co.id/pages/returns-exchanges](https://colorbox.co.id) | Public Data | `business-policies.md`, `customer-faq.md` | Terverifikasi |
| **SRC-05** | Layanan Pengiriman & FAQ Colorbox | [https://colorbox.co.id/pages/shipping-delivery](https://colorbox.co.id) | Public Data | `business-policies.md`, `customer-faq.md` | Terverifikasi |
| **SRC-06** | Akun Resmi Instagram `@colorbox` | [https://instagram.com/colorbox](https://instagram.com/colorbox) | Research Findings | `content-pillars.md`, `content-research.md` | Terverifikasi dari Aktivitas Medsos |
| **SRC-07** | Kampanye *"Never Just One Thing"* & Rebranding | Publikasi Berita Bisnis & UGM/UNESA Media Studies | Research Findings | `brand-guidelines.md`, `content-pillars.md` | Terverifikasi Studi Media Publik |
| **SRC-08** | COLORBOX Official Shop di Shopee Mall | [https://shopee.co.id/colorboxofficial](https://shopee.co.id) | Public Data & CS Observations | `customer-faq.md`, `content-research.md` | Terverifikasi |
| **SRC-09** | Kerangka Pengujian Hermes Agent PRD | `USE CASE PRODUCT REQUIREMENT DOCUMENT (PRD).pdf` | Assumptions & Test Standards | `customer-inquiry-patterns.md` | Dokumen Internal R&D Brief |
| **SRC-10** | Skenario Simulasi Komplain & Percakapan | Standar Interaksi CS R&D | Dummy / Simulated Data | `customer-inquiry-patterns.md` | Simulasi R&D |

---

## 2. Taksonomi Klasifikasi Data (PRD 3.3)

Semua data yang digunakan oleh agen dikelompokkan ke dalam 4 kategori ketat:

1. **A. Public Data (Data Publik):**
   - Fakta yang dapat diakses langsung oleh siapa saja di domain publik.
   - Contoh: Nama produk, harga di etalase, varian ukuran, alamat email CS, kebijakan retur 7 hari.
   - *Tingkat Kepastian:* Fakta Mutlak (*Ground Truth*).
2. **B. Research Findings (Temuan Riset):**
   - Interpretasi dan analisis tim terhadap pola publik.
   - Contoh: Pola penulisan caption Instagram, pembagian 4 pilar konten, gaya visual tone & voice.
   - *Tingkat Kepastian:* Analisis Berbasis Data Terbuka.
3. **C. Assumptions (Asumsi R&D):**
   - Hipotesis kerja yang digunakan untuk memandu eksperimen awal.
   - Contoh: Asumsi berat badan vs nomor celana denim (BB 50kg -> size 27), estimasi alur percakapan ideal.
   - *Tingkat Kepastian:* Panduan Operasional Sementara (dapat disesuaikan).
4. **D. Dummy / Simulated Data (Data Simulasi):**
   - Data buatan yang dirancang khusus untuk menguji ketahanan agen (*stress test*) tanpa melibatkan pelanggan riil.
   - Contoh: Skenario komplain kancing lepas, salah kirim warna, tes halusinasi harga.
   - *Tingkat Kepastian:* Data Sintetis (Wajib berlabel simulasi).

---

## 3. Batasan Etika & Keamanan Data (Compliance & Safety)

- AI Employee **dilarang keras** mengklaim kepemilikan atau akses langsung terhadap basis data internal rahasia Colorbox (seperti basis data CRM internal, sistem stok ERP gudang, data penjualan finansial, atau SOP internal non-publik).
- Seluruh data yang disajikan semata-mata berasal dari observasi publik resmi per November 2026 untuk keperluan riset prototipe Hermes Agent.
