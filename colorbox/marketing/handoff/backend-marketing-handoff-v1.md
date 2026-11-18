# Backend Handover Specification: Marketing Agent v1.0.0

> **To:** Team 3 — Backend Engineering  
> **From:** Marketing & Content R&D Division  
> **Brand / Project:** Colorbox Indonesia (Delamibrands) — Hermes AI Employee  
> **Handover Date:** 9 November 2026  
> **Version:** 1.0.0  
> **Status:** READY FOR BACKEND INGESTION & INTEGRATION

---

## 1. Ringkasan Serah Terima (Handover Summary)

Dokumen ini memuat spesifikasi teknis lengkap untuk memasang basis pengetahuan (*knowledge hub*), instruksi master prompt (*agent instructions*), template format output, dan perkakas penelusuran (*tools*) untuk **Marketing & Content AI Employee** pada framework **Hermes Agent**.

### Berkas yang Diserah-terimakan:
1. `colorbox/marketing/knowledge/brand-profile-v1.md` (Profil brand resmi)
2. `colorbox/marketing/knowledge/brand-guidelines-v1.md` (Tone of voice, 3 persona, 3 pilar gaya)
3. `colorbox/marketing/knowledge/claim-and-compliance-guidelines-v1.md` (Aturan anti-halusinasi klaim)
4. `colorbox/marketing/knowledge/content-pillars-v1.md` (4 pilar konten editorial)
5. `colorbox/marketing/knowledge/source-register-v1.md` (Daftar sumber audit publik)
6. `colorbox/marketing/instructions/marketing-agent-instructions-v1.md` (Master Prompt 5 Tahap)
7. `colorbox/marketing/instructions/marketing-templates-v1.md` (5 Template output baku)
8. `colorbox/product-catalog.md` (Katalog data 1.206 produk terverifikasi)

---

## 2. Strategi Pemuatan Basis Pengetahuan (Knowledge Ingestion Architecture)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        BACKEND INGESTION SCHEME                        │
├────────────────────────────────────┬───────────────────────────────────┤
│ STATIC KNOWLEDGE (Direct Prompt)   │ DYNAMIC KNOWLEDGE (Tool Calling)  │
├────────────────────────────────────┼───────────────────────────────────┤
│ • brand-profile-v1.md              │ • product-catalog.md (230 KB)     │
│ • brand-guidelines-v1.md           │   (Diindeks ke SQLite / JSON      │
│ • claim-and-compliance-v1.md       │    untuk pencarian kata kunci)    │
│ • content-pillars-v1.md            │                                   │
│ • marketing-agent-instructions-v1  │                                   │
└────────────────────────────────────┴───────────────────────────────────┘
```

### A. Pemuatan Statis ke System Prompt
Berkas profil, panduan gaya, pilar konten, dan instruksi master digabungkan ke dalam *system prompt* Hermes Agent. Total ukuran teks statis ini berkisar ~25 KB (~6.000 token), sangat aman dan berada jauh di bawah ambang batas context window LLM.

### B. Pemuatan Dinamis Katalog Produk (Anti Context-Overflow)
Berkas `product-catalog.md` memiliki ukuran ~230 KB (1.206 baris tabel). 
**PANDUAN BACKEND:** Dilarang menginjeksikan berkas katalog ini secara utuh ke dalam prompt statis. Backend wajib menyediakan perkakas fungsi (*tool*) bagi Hermes Agent:

```python
# Spesifikasi Tool Hermes untuk Backend
{
    "type": "function",
    "function": {
        "name": "search_colorbox_products",
        "description": "Mencari produk aktif di katalog resmi Colorbox berdasarkan kategori, kata kunci, warna, atau rentang harga.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Kata kunci nama produk, misal 'graphic t-shirt', 'knit shirt', 'denim'"},
                "category": {"type": "string", "enum": ["TOPS", "DENIM", "KNITWEAR", "BOTTOMS", "DRESS", "OUTERWEAR"], "description": "Filter kategori"},
                "has_discount_only": {"type": "boolean", "description": "Hanya cari produk yang memiliki harga coret diskon"},
                "max_price": {"type": "number", "description": "Batas harga maksimum dalam Rupiah"},
                "limit": {"type": "integer", "default": 5, "description": "Jumlah maksimal item yang dikembalikan"}
            },
            "required": ["query"]
        }
    }
}
```

---

## 3. Spesifikasi Kontrak Payload API (API Contract)

Backend disarankan menggunakan endpoint yang kompatibel dengan arsitektur Sprint 2 (`POST /api/v1/agent/execute`):

### Request Payload (Client -> Backend):
```json
{
  "department": "marketing",
  "agent_id": "marketing_content_v1",
  "prompt": "Buat 1 caption Instagram untuk Double Layer Fitted Polo Shirt dengan 2 opsi variasi copy (Playful vs Chic).",
  "context_params": {
    "style_pillar": "Chic & Urban",
    "target_persona": "Persona 2: The Smart-Casual First-Jobber",
    "campaign_umbrella": "#NeverJustOneThing"
  },
  "enable_claim_audit": true
}
```

### Response Payload (Backend -> Client):
```json
{
  "status": "success",
  "session_id": "sess_mkt_20261109_01",
  "department": "marketing",
  "workflow_stage_completed": "STAGE_4_SELF_AUDITED",
  "output_markdown": "### 📸 Format: Instagram Caption...\n\n**Opsi A (Playful)...**\n\n**Opsi B (Chic)...**",
  "products_referenced": [
    {
      "name": "Double Layer Fitted Short Sleeve Polo Shirt",
      "price": 119900,
      "original_price": 129900,
      "discount_percent": 8,
      "color": "OFF WHITE",
      "url": "https://colorbox.co.id/products/double-layer-fitted-short-sleeve-polo-shirt-off-white-26i"
    }
  ],
  "claim_audit_result": {
    "status": "COMPLIANT",
    "unsupported_claims_detected": 0,
    "verified_facts_count": 4,
    "human_review_required": true
  }
}
```

---

## 4. Tiga Contoh Kasus Acuan untuk Verifikasi Backend

Backend dapat menjalankan 3 contoh payload uji berikut untuk memvalidasi integrasi:
1. **Kasus 1 (Planning):** Input brief permintaan kalender editorial mingguan -> Expected: Kalender 5 hari kerja dengan 4 pilar konten dan 5 produk terverifikasi.
2. **Kasus 2 (Multi-Format):** Input brief produk knitwear & denim -> Expected: Caption Opsi A (Playful), Caption Opsi B (Chic), Naskah Video 15s (Storyboard), dan 3 Headline.
3. **Kasus 3 (Unsupported Claim Handling):** Input brief yang meminta klaim katun Mesir fiktif dan diskon 85% -> Expected: Backend/Agent mendeteksi bendera peringatan (*flags warning*), memberikan pushback santun, dan menyajikan opsi produk resmi yang valid.

