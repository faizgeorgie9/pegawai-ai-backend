# S3-02A: Implement Knowledge Loading and Retrieval Report

**Sprint:** Sprint 3 — Day 2 (November 6, 2026)  
**Task Title:** Implement Knowledge Loading and Retrieval  
**Assignee:** Intern 1 (Backend & Platform Lead)  
**Scope:** Standalone Knowledge Loading & Simple Retrieval Engine (No Heavy Vector DB Required)  
**Target Brand:** Colorbox (PT Delamibrands Kharisma Busana)  
**Status:** COMPLETE (Knowledge Ingested, Engine Verified, 5/5 Tests Passed, Endpoints Exposed)  

---

## 1. Executive Summary & Objective

Task ini merealisasikan arsitektur **Knowledge Loading and Retrieval** untuk dua karyawan AI Colorbox (Marketing & Customer Service). Implementasi ini memanfaatkan kembali fondasi Hermes Agent CLI `v0.22.2` dan model **DeepSeek V4.1 Flash** (`deepseek-v4.1-flash` via provider `opencode`) yang telah terbukti di Sprint 2, **tanpa mengulang instalasi environment dan tanpa memerlukan platform database vektor eksternal (seperti Pinecone/Milvus)**.

### Prinsip Utama yang Diterapkan:
1. **Source-Labeled Safeguards:** Setiap butir pengetahuan diberi label sumber yang eksplisit:
   * `[VERIFIED_FACT]`: Fakta publik resmi Colorbox (kebijakan retur 7 hari, jaringan toko mall).
   * `[ASSUMED_POLICY]`: Asumsi operasional standar ritel pakaian (SLA pengiriman 2–5 hari).
   * `[DUMMY_SIMULATION]`: Fixture sintetis untuk simulasi komplain (`#CBX-2026-9812`).
2. **Department Isolation:** Pengetahuan diisolasi secara ketat per divisi:
   * Agen Marketing hanya menerima Panduan Bersama + Panduan Marketing (tidak bisa mengakses matriks eskalasi atau tingkat retur internal CS).
   * Agen CS hanya menerima Panduan Bersama + SOP CS (tidak bisa mengakses draf kalender kampanye marketing).
3. **Truthful Absent / Missing Data Behavior (Zero Hallucination):** Jika pertanyaan pelanggan berada di luar cakupan dokumen resmi, sistem secara jujur mengembalikan status `KNOWLEDGE_ABSENT`, memicu pesan penolakan sopan, dan mengeskalasikan tiket ke supervisor manusia.
4. **Conflict Resolution:** Jika ada kontradiksi antardokumen, SOP spesifik divisi selalu mengesampingkan panduan umum brand.

---

## 2. Register Sumber Pengetahuan (Versioned Knowledge Files)

Seluruh dokumen pengetahuan disimpan dan di-versioning secara terstruktur di folder `local_setup/backend_template/context/knowledge/`:

| Nama File | Versi | Kode Referensi | Hak Akses Divisi | Ringkasan Konten |
| :--- | :--- | :--- | :--- | :--- |
| [`shared_brand_knowledge_v1.md`](file:///d:/ai_developer/project6/local_setup/backend_template/context/knowledge/shared_brand_knowledge_v1.md) | `1.0.0` | `SHARED_BRAND_KNOWLEDGE_V1` | **Semua Agen (Shared)** | Profil brand Colorbox, target audiens (15–25 th), tone of voice ("Babes" / "Kak"), jaringan toko mall, kanal online, aturan etika & privasi. |
| [`colorbox_marketing_knowledge_v1.md`](file:///d:/ai_developer/project6/local_setup/backend_template/context/knowledge/colorbox_marketing_knowledge_v1.md) | `1.0.0` | `MKT-CBX-GUIDE-01` | **Eksklusif Marketing** | 4 pilar konten (OOTD Styling, Trend Alert, Promosi, Komunitas), formula copywriting AIDA, tagar wajib (`#ColorboxBabes`), palet warna pastel (Pink `#FFD1DC`, Lilac `#C8A2C8`, Sage `#B2C9AB`). |
| [`colorbox_cs_sop_v1.md`](file:///d:/ai_developer/project6/local_setup/backend_template/context/knowledge/colorbox_cs_sop_v1.md) | `1.0.0` | `SOP-CBX-CS-2026` | **Eksklusif CS** | Syarat tukar ukuran 7 hari kalender (`SOP-CBX-RET-01`), larangan cash refund, SLA pengiriman reguler (`SOP-CBX-LOG-02`), unboxing video 48 jam (`SOP-CBX-DEF-03`), matriks eskalasi tiket (`SOP-CBX-ESC-04`), dan data dummy order. |

---

## 3. Implementasi Mesin Retrieval Sederhana (`knowledge_retriever.py`)

Mesin pencari dirancang efisien dan mandiri (*lightweight & dependency-free*) di dalam [`local_setup/backend_template/knowledge_retriever.py`](file:///d:/ai_developer/project6/local_setup/backend_template/knowledge_retriever.py):

```python
from knowledge_retriever import KnowledgeRetriever

retriever = KnowledgeRetriever()

# 1. Mengambil konteks terisolasi per agen
marketing_context = retriever.get_agent_knowledge("marketing")
cs_context = retriever.get_agent_knowledge("cs")

# 2. Melakukan pencarian terlabel berdasarkan query
result = retriever.retrieve("baju kekecilan mau tukar ukuran", department="cs")
```

### Mekanisme Ekstraksi & Pencegahan False-Positive:
* **Tokenizing & Stop Words Filtering:** Menyaring kata tugas umum bahasa Indonesia (`apakah`, `bisa`, `yang`, `dan`) serta nama brand itu sendiri (`colorbox`, `delami`) agar tidak menimbulkan false positive.
* **Exact Word-Boundary Matching (`\b`):** Mencegah pencocokan subkata yang keliru (contoh: kata `"ban"` tidak akan lagi mencocokkan kata `"perbankan"` atau `"pembayaran"`).
* **Scoring & Department Priority (+0.5):** Pasal dari dokumen SOP departemen diberikan bobot lebih tinggi daripada dokumen bersama umum untuk memastikan resolusi konflik yang tepat.

---

## 4. Hasil Pengujian Test Suite (5/5 PASS)

Seluruh fungsi telah divalidasi menggunakan runner pengujian otomatis [`local_setup/test_knowledge_retrieval.py`](file:///d:/ai_developer/project6/local_setup/test_knowledge_retrieval.py).

### Rangkuman Hasil Pengujian:

| No | Nama Skenario Uji | Query / Target Uji | Status | Bukti Temuan |
| :---: | :--- | :--- | :---: | :--- |
| **1** | **Versioned File Loading** | Memeriksa registrasi 3 file markdown | **PASS [OK]** | Semua file ter-load dengan metadata versi `1.0.0` dan ref code yang tepat. |
| **2** | **Grounded CS Retrieval** | *"Kak, baju yang kemarin saya beli di Colorbox kekecilan, apakah bisa ditukar ukurannya?"* | **PASS [OK]** | Mengembalikan `SOP-CBX-RET-01` dengan label `[VERIFIED_FACT]`, syarat 7 hari, dan tag harga utuh. |
| **3** | **Grounded Marketing Retrieval** | *"Rancangan konten promosi summer pastel remaja untuk Instagram"* | **PASS [OK]** | Mengembalikan `MKT-PIL-01` dengan pilar OOTD styling dan palet warna pastel. |
| **4** | **Truthful Missing Knowledge Fallback** | *"Apakah Colorbox menerima gadai emas murni atau jual ban mobil second?"* | **PASS [OK]** | Mengembalikan `status: KNOWLEDGE_ABSENT`, `grounded: false`, dan saran eskalasi ke supervisor. |
| **5** | **Department Knowledge Isolation** | Memeriksa kebocoran konteks antar-divisi | **PASS [OK]** | Konteks Marketing bebas dari matriks eskalasi CS; Konteks CS bebas dari pilar strategi kampanye Marketing. |

Bukti fisik hasil eksekusi pengujian telah disimpan secara permanen di [`local_setup/evidence/s3_02a_knowledge_test_results.json`](file:///d:/ai_developer/project6/local_setup/evidence/s3_02a_knowledge_test_results.json).

---

## 5. Integrasi Endpoint Backend REST API

Mesin pencari ini telah terintegrasi langsung ke dalam [`server.py`](file:///d:/ai_developer/project6/local_setup/backend_template/server.py) pada port 8080:

### 1. Registri Pengetahuan (`GET /api/v1/knowledge/registry`)
Mengembalikan ringkasan dokumen yang terdaftar beserta versinya:
```json
{
  "status": "success",
  "knowledge_base": "Colorbox Retail & Brand Guidelines v1",
  "registry": {
    "shared_brand_knowledge_v1": {
      "filename": "shared_brand_knowledge_v1.md",
      "version": "1.0.0 (Released: 2026-11-06)",
      "ref_code": "SHARED_BRAND_KNOWLEDGE_V1",
      "applicability": "All",
      "section_count": 4
    },
    "colorbox_marketing_knowledge_v1": {
      "filename": "colorbox_marketing_knowledge_v1.md",
      "version": "1.0.0 (Released: 2026-11-06)",
      "ref_code": "MKT-CBX-GUIDE-01",
      "applicability": "EXCLUSIVE to Colorbox Marketing AI Employee",
      "section_count": 4
    },
    "colorbox_cs_sop_v1": {
      "filename": "colorbox_cs_sop_v1.md",
      "version": "1.0.0 (Released: 2026-11-06)",
      "ref_code": "SOP-CBX-CS-2026",
      "applicability": "EXCLUSIVE to Colorbox Customer Service AI Employee",
      "section_count": 6
    }
  }
}
```

### 2. Pencarian Interaktif (`GET /api/v1/knowledge/lookup?query=...&department=...`)
* **Contoh Kasus Sukses (`200 OK`):**
  `GET /api/v1/knowledge/lookup?query=tukar%20ukuran%20baju&department=cs`
  $\rightarrow$ Mengembalikan pasal `SOP-CBX-RET-01` dengan label `VERIFIED_FACT`.
* **Contoh Kasus Tidak Ditemukan (`404 Not Found` dengan format terstruktur):**
  `GET /api/v1/knowledge/lookup?query=jual%20mobil%20antik&department=cs`
  $\rightarrow$ Mengembalikan `status: "KNOWLEDGE_ABSENT"`, `fallback_action: "ESCALATE_TO_SUPERVISOR"`.

---

## 6. Serah Terima & Rencana 9 November (Day 3 Handoff)

* **Status Kesiapan:** Mesin loading dan retrieval pengetahuan Colorbox telah siap 100% dan terhubung ke backend v1.
* **Koordinasi Pemilik Bisnis (Business Owners):** Pemilik bisnis dan tim penguji dapat langsung mengevaluasi grounding respons AI per tanggal **9 November** menggunakan backend nyata tanpa harus menunggu selesainya integrasi UI final (10 November).
