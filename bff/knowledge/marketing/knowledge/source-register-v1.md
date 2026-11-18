# Source Provenance & Verification Register (Version 1.0.0)

> **Version:** 1.0.0  
> **Registration Date:** 9 November 2026  
> **Scope:** Shared Business Knowledge Hub & Marketing Package  
> **Audit Status:** VERIFIED (Public Open Data)  
> **Owner:** Knowledge & Governance Engineering

---

## 1. Tabel Registrasi Sumber Data Publik (Master Data Register)

| ID Sumber | Entitas & Nama Dokumen | URL / Lokasi Akses | Tanggal Akses | Klasifikasi Data | Penggunaan dalam Knowledge Hub |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SRC-01** | Colorbox Official About Us | `https://colorbox.co.id/pages/about-us` | 2026-11-09 | Public Data | `brand-profile-v1.md` |
| **SRC-02** | Colorbox Official Product Collection | `https://colorbox.co.id/collections/colorbox-collection` | 2026-11-09 | Public Data | `product-catalog.md` (1.206 produk) |
| **SRC-03** | Colorbox Size Guide (Panduan Ukuran) | `https://colorbox.co.id` | 2026-11-09 | Public Data | `product-size-reference.md` |
| **SRC-04** | Colorbox Return & Exchange Policy | `https://colorbox.co.id/pages/returns-exchanges` | 2026-11-09 | Public Data | `business-policies.md` |
| **SRC-05** | Colorbox Shipping & Fulfillment Policy | `https://colorbox.co.id/pages/shipping-delivery` | 2026-11-09 | Public Data | `business-policies.md`, `customer-faq.md` |
| **SRC-06** | Akun Instagram Resmi Colorbox Indonesia | `https://instagram.com/colorbox` (`@colorbox`) | 2026-11-09 | Research Findings | `brand-guidelines-v1.md`, `content-pillars-v1.md` |
| **SRC-07** | Studi Rebranding Kampanye "Never Just One Thing" | Liputan Bisnis & Riset Komunikasi Media UGM/UNESA | 2026-11-09 | Research Findings | `brand-guidelines-v1.md`, `content-pillars-v1.md` |
| **SRC-08** | COLORBOX Official Shop di Shopee Mall | `https://shopee.co.id/colorboxofficial` | 2026-11-09 | Public Data & Findings | `customer-faq.md`, kalender promo |
| **SRC-09** | PRD R&D Hermes AI Employee Brief | `colorbox/USE CASE PRODUCT REQUIREMENT DOCUMENT (PRD).pdf` | 2026-11-09 | Requirements Spec | Kerangka pengujian & batasan sistem |
| **SRC-10** | Skenario Uji Rekayasa Pemasaran & CS | Internal R&D Engineering Mock | 2026-11-09 | Simulated Data | `customer-inquiry-patterns.md`, test cases |

---

## 2. Aturan Verifikasi & Batasan Integritas Data

1. **Prinsip Keterlacakan (Traceability):**
   - Setiap entitas data harga, nama produk, dan persentase diskon yang dikutip dalam konten marketing harus dapat dilacak langsung ke item spesifik pada `SRC-02` (`product-catalog.md`).
2. **Karantina Data Tertutup (No Internal Data Claim):**
   - Tidak ada data yang diklaim berasal dari sistem ERP internal, database transaksi kasir, logistik gudang tertutup, atau PII pelanggan riil.
3. **Penyelarasan Berkala:**
   - Registrasi ini diperbarui setiap kali terjadi perubahan struktur produk atau kebijakan publik brand Colorbox.

