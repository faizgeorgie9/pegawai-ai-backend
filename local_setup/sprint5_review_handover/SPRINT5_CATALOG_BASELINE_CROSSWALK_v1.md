# Sprint 5 Catalog JD Baseline Crosswalk v1

**Source received:** `AI_Top_Trends_Master_Catalog_30_Pegawai_AI_v1.0.docx`, supplied by the user on 2026-11-22 (Jakarta time).
**Purpose:** verify that each role template contains the exact catalog duty statement and record where each catalog duty maps into the 11-section template.
**Status:** catalog baseline supplied; reviewer cross-check pending. This document does not grant role sign-off.

## Review rule

The catalog is the baseline duty statement. It does not override the role template's explicit boundaries, approval gates or tool permissions. Where a catalog duty is broader than the implemented operating scope, the difference is recorded below and remains a reviewer decision.

## CS-01  |  Omnichannel Customer Service

**Catalog section:** 02. Customer Service & Experience

**Verbatim catalog text:**

Deskripsi singkat: Menangani interaksi pelanggan melalui kanal komunikasi yang terhubung dan memberikan bantuan sepanjang perjalanan pelanggan.

Job description:

- Menjawab pertanyaan produk, harga, ketersediaan, kebijakan, dan FAQ serta membantu pelanggan memilih produk.
- Membantu memeriksa status pesanan dan pengiriman, serta menangani pertanyaan terkait transaksi.
- Menangani keluhan, permintaan retur atau refund sesuai kebijakan, memperbarui konteks layanan, dan mengeskalasi kasus yang membutuhkan keputusan manusia.

**Cross-check:** Catalog duty 1 maps to sections 3, 4, 8 and 9; live product, price, stock, policy and FAQ claims remain limited to approved sources. Catalog duty 2 maps to sections 1, 4, 7 and 10 and remains blocked for live status until an authoritative read-only source is configured. Catalog duty 3 maps to sections 1, 3, 5, 6, 8 and 10 and is implemented as internal drafts plus recommendation-only escalation until a named human owner is assigned. Reviewer decision: confirm whether the catalog division label 'Customer Service & Experience' should replace the template's 'Customer Service & Operations'.

## MKT-01  |  Marketing Strategist

**Catalog section:** 03. Marketing & Sales

**Verbatim catalog text:**

Deskripsi singkat: Menyusun strategi pemasaran berdasarkan pasar, pelanggan, kompetitor, dan tujuan bisnis.

Job description:

- Melakukan riset pasar, kompetitor, tren, dan target audience.
- Menentukan positioning, value proposition, channel, dan pendekatan pemasaran.
- Menyusun rencana marketing dan rekomendasi campaign yang selaras dengan target bisnis.

**Cross-check:** Catalog duty 1 maps to sections 3, 4, 7, 8 and 9 and is covered by the Aldi research module. Catalog duty 2 maps to sections 4, 5 and 9. Catalog duty 3 maps to sections 3, 5, 9, 10 and 11. Reviewer decision: confirm the synthesis mapping MKT-01 = Aldi + Bram + Meda/Bimo; the catalog supplies duties, not the Karyawan.AI source mapping.

## MKT-02  |  SEO Specialist

**Catalog section:** 03. Marketing & Sales

**Verbatim catalog text:**

Deskripsi singkat: Meningkatkan visibilitas organik website melalui riset, evaluasi, dan optimasi SEO.

Job description:

- Melakukan keyword research, search intent analysis, dan analisis kompetitor.
- Melakukan SEO audit serta memberikan rekomendasi optimasi halaman, struktur, dan internal linking.
- Menyusun prioritas keyword dan strategi peningkatan visibilitas serta performa pencarian.

**Cross-check:** Catalog duty 1 maps to sections 3, 4, 5 and 9. Catalog duty 2 maps to sections 3, 4, 5, 9 and 10. Catalog duty 3 maps to sections 5, 9 and 11. All three fit the exact Rifqy dossier adaptation; the no-live-data rule remains active because the catalog does not grant API access.

## MKT-03  |  Digital Ads Specialist

**Catalog section:** 03. Marketing & Sales

**Verbatim catalog text:**

Deskripsi singkat: Merencanakan, memantau, dan mengevaluasi kampanye iklan berbayar untuk mencapai target pemasaran.

Job description:

- Menyusun strategi dan struktur campaign pada platform seperti Meta Ads dan Google Ads.
- Memantau performa iklan, audiens, materi kreatif, dan penggunaan anggaran.
- Menganalisis hasil serta memberikan rekomendasi optimasi campaign, targeting, dan budget.

**Cross-check:** Catalog duty 1 maps to sections 1, 4, 5, 7 and 9. The template currently configures only Meta Ads; Google Ads is named in the catalog but is not connected in the supplied tools and remains a reviewer decision. Catalog duty 2 maps to sections 4, 5, 7, 9 and 11. Catalog duty 3 maps to sections 5, 9 and 11. PAUSED-only creation and explicit activation approval remain active.

## MKT-04  |  Email Marketing Specialist

**Catalog section:** 03. Marketing & Sales

**Verbatim catalog text:**

Deskripsi singkat: Mengelola komunikasi pemasaran melalui email untuk membangun hubungan, engagement, dan konversi.

Job description:

- Menyusun newsletter, email campaign, dan rangkaian email otomatis.
- Mengelola segmentasi audiens, mailing list, dan personalisasi pesan.
- Menganalisis deliverability, open rate, click-through rate, dan konversi untuk meningkatkan performa.

**Cross-check:** Catalog duty 1 maps to sections 3, 4, 5 and 9, but the template implements draft sequences only; sending and automation require an ESP and human approval. Catalog duty 2 maps to sections 4, 8 and 9; the template currently forbids contact/PII and list access, so segment rules must be supplied as non-PII briefs until approved. Catalog duty 3 maps to sections 7, 9 and 11; no ESP analytics tool is connected, so the role can analyze user-supplied reports only. Reviewer decision: confirm whether the draft-only boundary is accepted as the operating scope.

## MKT-05  |  Lead Generation Specialist

**Catalog section:** 03. Marketing & Sales — lanjutan

**Verbatim catalog text:**

Deskripsi singkat: Mencari dan menyiapkan database calon pelanggan yang relevan bagi kegiatan penjualan.

Job description:

- Mengidentifikasi sumber dan menemukan prospek sesuai profil pelanggan ideal.
- Mengumpulkan serta melengkapi informasi kontak dan profil calon pelanggan dari sumber yang diizinkan.
- Menilai, mengelompokkan, dan memprioritaskan kualitas prospek sebelum diserahkan kepada tim sales.

**Cross-check:** Catalog duty 1 maps to sections 3, 4, 5, 8 and 9. Catalog duty 2 maps to sections 4 and 9 but conflicts with the template's no-recipient-PII rule; the catalog says contact information may be collected from permitted sources, while the template only drafts source criteria and does not store contact data. Catalog duty 3 maps to sections 4, 5, 9 and 10. Reviewer decision: resolve the PII boundary before approving this role.

## MKT-06  |  Sales Assistant

**Catalog section:** 03. Marketing & Sales — lanjutan

**Verbatim catalog text:**

Deskripsi singkat: Mendukung proses penjualan dengan menghubungi prospek, mengelola tindak lanjut, dan menyiapkan kebutuhan penawaran.

Job description:

- Membuat dan mengirim pesan pendekatan serta melakukan follow-up melalui kanal yang diizinkan.
- Membantu kualifikasi prospek, menjadwalkan pertemuan, dan memperbarui CRM atau sales pipeline.
- Menyiapkan draft penawaran, proposal, ringkasan kebutuhan pelanggan, dan tindak lanjut penjualan.

**Cross-check:** Catalog duty 1 maps to sections 1, 3, 5 and 9. The template narrows this to pre-sale conversations from approved lead lists and one reply per turn; provider choice is still pending. Catalog duty 2 maps to sections 4, 5 and 9; CRM update and meeting scheduling are not connected in the current template and remain reviewer/backend decisions. Catalog duty 3 maps to sections 4, 5 and 9 as drafts only. Reviewer decision: confirm the pre-sale boundary and whether CRM/scheduling access will be granted.

## MKT-07  |  Marketing Performance Analyst

**Catalog section:** 03. Marketing & Sales — lanjutan

**Verbatim catalog text:**

Deskripsi singkat: Mengolah data pemasaran menjadi laporan dan insight untuk mengevaluasi efektivitas aktivitas marketing.

Job description:

- Menganalisis performa channel, campaign, traffic, leads, dan conversion rate.
- Mengukur metrik seperti biaya akuisisi, efektivitas anggaran, dan marketing ROI jika datanya tersedia.
- Menyusun dashboard, laporan berkala, serta rekomendasi berbasis data untuk tim marketing.

**Cross-check:** Catalog duty 1 maps to sections 3, 4, 5, 9 and 11. Catalog duty 2 maps to sections 5, 7, 9 and 11 and preserves the catalog's 'if the data is available' limit. Catalog duty 3 maps to sections 5, 7, 9 and 11; reports may be saved as new dated files through the configured drive tool. No ad-entity writes are granted.

## Sign-off

| Reviewer | Decision | Name | Date |
|---|---|---|---|
| Marketing | Accept / Revisions / Reject | ____________________ | __________ |
| Ops | Accept / Revisions / Reject | ____________________ | __________ |
| PM | Archive decision | ____________________ | __________ |
