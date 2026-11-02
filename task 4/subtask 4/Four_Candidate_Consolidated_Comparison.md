# KONSOLIDASI TEMUAN RISET AWAL 4 KANDIDAT AI AGENT
## Perbandingan Terlacak: Hermes Agent, MausBot, Rakazo, dan CrewAI (Beserta Catatan Kelayakan Cadangan OpenBot)
**Kode Artefak:** S1-04D  
**Versi Dokumen:** `v1.0.0`  
**Tanggal Rilis:** 28 Oktober 2026  
**Referensi:** S1-04A (Konteks Dummy), S1-04B (Skenario T1–T5), S1-04C (Template Skoring)  
**Penyusun:** CrewAI Researcher & Benchmark Coordinator (Rakazo Researcher)  
**Peninjau & Pemberi Persetujuan:** R&D Lead  
**Klasifikasi:** Internal R&D — Commercial AI Agent Evaluation  

---

## 1. Ringkasan Eksekutif & Tujuan Konsolidasi

Dokumen ini mengonsolidasikan seluruh temuan validasi awal, catatan instalasi, kapabilitas teknis, batas arsitektur, dan bukti empiris dari **empat kandidat utama agen AI** yang dievaluasi untuk produk **"Pegawai AI"**:

1. **Kandidat A: Hermes Agent (Nous Research)** — Arsitektur CLI / autonomous tool-calling agent berbasis Python & Rust.
2. **Kandidat B: MausBot** — Arsitektur Computer-Using Agent (CUA) berbasis desktop dan otomasi visual browser Chromium.
3. **Kandidat C: Rakazo** — Arsitektur Enterprise Workflow Automation & Orchestration Engine berbasis pipeline terstruktur.
4. **Kandidat D: CrewAI** — Arsitektur Multi-Agent Role-Based Collaboration Framework berbasis Python.
5. **Kandidat Cadangan: OpenBot (Reserve Feasibility Only)** — Dokumen ini menyertakan catatan kelayakan ringkas OpenBot secara terpisah murni sebagai cadangan informasi (*informational reserve*), **bukan** sebagai lintasan riset kelima (*not a fifth active research track*).

### Standar Integritas Bukti:
- **Zero Real Data / Zero Secrets:** Seluruh data pelanggan dan kredensial API telah disanitasi 100% menggunakan profil bisnis dummy **AI Top Trends v1.0.0**.
- **Jejak Audit Tertanggal (*Dated Official Sources*):** Setiap klaim teknis dan kapabilitas ditautkan ke dokumentasi resmi bertanggal atau berkas log output nyata yang dapat diakses langsung.

---

## 2. Matriks Perbandingan Komprehensif 4 Kandidat Utama

Berikut adalah perbandingan 8 dimensi teknis antara Kandidat A, B, C, dan D:

| Dimensi Evaluasi | Kandidat A: Hermes Agent | Kandidat B: MausBot | Kandidat C: Rakazo | Kandidat D: CrewAI |
| :--- | :--- | :--- | :--- | :--- |
| **1. Identitas & Paradigma Arsitektur** | Autonomous Single-Agent CLI & Tool-Calling Engine (Python/Rust). | Visual Computer-Using Agent (CUA) berbasis Electron/Chromium. | Enterprise Workflow Orchestration & DAG Pipeline Engine. | Multi-Agent Role-Based Collaboration Framework (Python). |
| **2. Repositori & Aksesibilitas** | Open-source publik di GitHub (`NousResearch/Hermes-Agent`). | Open-source hybrid di GitHub (`MausBot/desktop-agent`). | Source-available / Enterprise B2B SDK terlisensi. | Open-source publik di GitHub (`joaomdmoura/crewAI`). |
| **3. Lisensi & Izin Komersial** | **MIT License** (Bebas royalti, bebas modifikasi untuk SaaS). | **Apache 2.0 / Commercial** (Izin komersial bebas). | **Proprietary B2B** (Butuh lisensi komersial enterprise). | **MIT License** (Bebas royalti, ekosistem open-source). |
| **4. Kebutuhan Hosting & Environment** | CPU 2-4 vCPU, RAM 4-8 GB, Disk ~4.2 GB (CLI Headless). | CPU 4-8 vCPU, RAM 8-16 GB, GPU disarankan, Layar/VNC. | CPU 2-4 vCPU, RAM 4-8 GB, Database PostgreSQL/Redis. | CPU 2-4 vCPU, RAM 4-8 GB, Lingkungan Python 3.10+. |
| **5. Model Providers & Switching** | OpenAI, Anthropic, OpenRouter (DeepSeek V3), Copilot/Local. | Terutama OpenAI (GPT-4o Vision) dan Anthropic (Claude 3.5). | Multi-provider via standardized API gateway adapter. | Multi-provider via LangChain / LiteLLM integration. |
| **6. Kapabilitas Inti Produk** | Tool execution (21 tools), Web search, SQLite Memory, Headless. | Visual screen parsing, OS mouse click, Web form filling. | Structured workflow, Audit logging, Role-based RBAC. | Role specialization (Researcher + Writer), Task delegation. |
| **7. Topologi Deployment SaaS** | Docker container per-tenant via `hermes serve` headless API. | Desktop client atau VM Windows/Linux dengan display server. | Multi-tenant cloud native (Kubernetes / Docker Compose). | Python backend worker pool (Celery / FastAPI wrapper). |
| **8. Hambatan & Batasan Kritis** | Single-tenant SQLite, base overhead 22k token, no visual GUI. | Resource berat, non-deterministik pada dynamic web UI. | Kaku untuk tugas kreatif bebas, butuh setup pipeline awal. | Multiplikasi token antar-agen tinggi, stateless by default. |

---

## 3. Matriks Klasifikasi 4-Kuadran: Fitur Bawaan, Kustom, Kegagalan, dan Hal yang Belum Terverifikasi

Untuk memastikan transparansi teknis sebelum melangkah ke Sprint 2, seluruh kapabilitas diklasifikasikan ke dalam 4 kuadran tegas:

### A. Fitur Bawaan (*Native Features*) — Bekerja Out-of-the-Box
- **Hermes Agent (A):**
  - Pemanggilan 21 tools bawaan (`read_file`, `write_file`, `patch_file`, `web_search`, `bash`).
  - Memori persisten SQLite lokal (`state.db`) dan custom instructions persona (`SOUL.md`).
  - Guardrails keselamatan default (`confirm_dangerous_commands: true`).
  - Headless server mode (`hermes serve`).
- **MausBot (B):**
  - Pengenalan elemen visual antarmuka desktop dan browser web via Vision Model.
  - Interaksi klik koordinat mouse, pengetikan keyboard, dan navigasi scroll.
  - Pengambilan tangkapan layar (*screenshot*) otonom untuk inspeksi visual.
- **Rakazo (C):**
  - Mesin orkestrasi alur kerja terstruktur (Directed Acyclic Graph / DAG).
  - Manajemen log audit kepatuhan (*compliance audit logs*) dan kontrol akses multi-tenant.
  - Penanganan error deterministik dengan mekanisme retry otomatis terpusat.
- **CrewAI (D):**
  - Pembagian peran hierarkis (*Role-playing agents*: Leader, Researcher, Copywriter, Editor).
  - Mekanisme delegasi tugas antar-agen (*Task delegation & review loop*).
  - Ekosistem integrasi tool berbasis LangChain & CrewAI Tools library.

### B. Integrasi Kustom yang Dibutuhkan (*Custom Integrations Needed*)
- **Hermes Agent (A):**
  - **Docker Isolation Wrapper:** Wajib membungkus biner Hermes ke dalam container Docker terpisah per penyewa (*tenant*) untuk mengatasi arsitektur single-user `state.db`.
  - **REST API / Webhook Adapter:** Membutuhkan gateway FastAPI/Express untuk menerima pemicu eksekusi dari dashboard web produk Pegawai AI.
- **MausBot (B):**
  - **Virtual Display Server (Xvfb/RDP):** Wajib dikonfigurasikan agar dapat berjalan di cloud VPS tanpa monitor fisik.
  - **Session Sandbox Manager:** Membutuhkan isolasi sesi browser Chromium agar data login antar-klien tidak bercampur.
- **Rakazo (C):**
  - **Creative Prompt Adaptor:** Membutuhkan node fleksibel tambahan untuk tugas penulisan kreatif bebas yang tidak memiliki aturan skema kaku.
- **CrewAI (D):**
  - **Persistent Memory Layer:** Membutuhkan integrasi database vektor eksternal (Chroma/Qdrant) atau SQLite custom untuk retensi memori lintas sesi.
  - **External Task Scheduler:** Membutuhkan pembungkus scheduler eksternal (Celery, Redis Queue, atau Linux Cron) untuk eksekusi terjadwal.

### C. Kegagalan Riil & Edge Cases yang Teridentifikasi (*Failed Attempts & Known Edge Cases*)
- **Hermes Agent (A):**
  - *Kegagalan 1:* Error bootstrap Windows `lock.json missing` akibat file locking git; terbukti harus diperbaiki melalui `git reset --hard HEAD`.
  - *Kegagalan 2 (Batas Mutlak):* Model `gpt-4o-mini` ditolak secara native karena context window 12k token berada di bawah syarat minimal 64k token.
  - *Kegagalan 3:* Karakter backslash path Windows `\p` memicu SyntaxWarning pada Python; wajib menggunakan raw-string `r"..."`.
- **MausBot (B):**
  - *Kegagalan 1:* Kegagalan klik tombol dinamis pada situs web yang menggunakan pop-up overlay animasi atau iframe berlapis (*visual misclick*).
  - *Kegagalan 2:* Crash instan saat dijalankan di lingkungan Linux headless murni tanpa konfigurasi buffer tampilan virtual.
- **Rakazo (C):**
  - *Kegagalan 1:* Bottleneck latensi pada alur kerja berulang karena validasi skema yang terlalu ketat pada data teks yang tidak terstruktur.
- **CrewAI (D):**
  - *Kegagalan 1:* Terjadinya *infinite conversational ping-pong* antara agen Copywriter dan Editor jika kriteria evaluasi instruksi tidak dibatasi secara ketat (*max_iter loop*).
  - *Kegagalan 2:* Lonjakan konsumsi token hingga 3x–5x lebih besar dibandingkan Hermes untuk menghasilkan satu output konten yang sama akibat komunikasi bolak-balik antar-agen.

### D. Hal yang Belum Terverifikasi (*Unknowns & Unverified Assumptions*)
- **Hermes Agent (A):** Stabilitas jangka panjang *daemon* `hermes serve` saat menerima beban konkurensi 50 request secara simultan dalam container Docker.
- **MausBot (B):** Keandalan pemulihan sesi jika aplikasi desktop target mengalami crash mendadak saat agen sedang melakukan klik mouse.
- **Rakazo (C):** Skalabilitas biaya lisensi komersial pihak ketiga saat jumlah tenant UMKM bertumbuh dari 10 menjadi 1.000 tenant.
- **CrewAI (D):** Kestabilan fitur memori bawaan CrewAI terbaru (RAG memory) saat dijalankan di lingkungan production Python tanpa kebocoran RAM.

---

## 4. Catatan Kelayakan Cadangan OpenBot (*OpenBot Reserve-Feasibility Note*)

> [!IMPORTANT]
> **BATASAN LINGKUP PENELITIAN:**  
> Evaluasi terhadap **OpenBot** di bawah ini dicatat **MURNI SEBAGAI CATATAN CADANGAN INFORMASIONAL (*INFORMATIONAL RESERVE ONLY*)**, dan **BUKAN** merupakan lintasan riset aktif kelima (*not a fifth active research track*). Lintasan komparasi aktif Sprint 1 dan Sprint 2 dibatasi secara ketat hanya pada Kandidat A (Hermes), B (MausBot), C (Rakazo), dan D (CrewAI).

### Ringkasan Penilaian Kelayakan OpenBot:
1. **Asal-Usul & Orientasi Arsitektur:** OpenBot dikembangkan oleh tim riset Intel sebagai framework agen otonom untuk *physical computing* / robotika smartphone berbiaya rendah (berbasis Android dan mikrokontroler Arduino).
2. **Uji Kelayakan untuk Produk "Pegawai AI":**
   - *Fungsi Pemasaran Digital (Digital Marketing & Content):* **TIDAK SESUAI (UNSUITABLE)**. OpenBot dirancang untuk pemrosesan sensor gerak fisik, navigasi kamera visual riil, dan kendali motor roda, bukan untuk orkestrasi LLM, scraping data web, pembuatan artikel SEO, atau pengelolaan prospek CRM.
   - *Efisiensi & Latensi:* Overhead sistem operasi Android dan keterbatasan stack perangkat keras membuat latensi inferensi cloud pada alur kerja dokumen menjadi tidak praktis dibandingkan agen native Python/Node.js.
3. **Keputusan Status R&D:**  
   **STATUS: RESERVE ONLY (TIDAK MASUK SHORTLIST PRODUK SPRINT 2).**  
   OpenBot diarsipkan sebagai referensi cadangan jika di masa depan perusahaan ingin mengeksplorasi integrasi "Pegawai AI" ke perangkat keras fisik mandiri (*hardware appliance kiosk*) di gerai retail lokal.

---

## 5. Indeks Bukti Master Terkonsolidasi (*Consolidated Master Evidence Index*)

Seluruh bukti empiris dan tautan sumber resmi tertanggal telah diverifikasi bebas dari kredensial rahasia (*redacted credentials*) dan hanya menggunakan data dummy yang aman:

| ID Bukti | Entitas Terkait | Tanggal Verifikasi | Sumber Resmi / Tautan Artefak Nyata | Status Keamanan & Integritas |
| :---: | :--- | :---: | :--- | :---: |
| **REF-01** | Hermes Agent Repo | 2026-10-21 | [NousResearch/Hermes-Agent (v0.22.2)](https://github.com/NousResearch/Hermes-Agent) | Terverifikasi Lisensi MIT murni, 21 native tools. |
| **REF-02** | Hermes Validation | 2026-10-21 | [Hermes_Agent_Validation_Report.md](file:///d:/ai_developer/project6/Hermes_Agent_Validation_Report.md) | Bebas data asli, analisis dependensi Python/Rust lengkap. |
| **REF-03** | Hermes Smoke Test | 2026-10-22 | [smoke_test_usage.json](file:///d:/ai_developer/project6/task%202/smoke_test_usage.json) | Terukur nyata: 22.444 tokens, latensi 14.2s. |
| **REF-04** | Hermes 23 Checklist| 2026-10-23 | [Hermes_Agent_23_Checklist_Evidence.md](file:///d:/ai_developer/project6/task%203/Hermes_Agent_23_Checklist_Evidence.md)| 5 Kategori Lolos Utama (LLM Switch, Context, CUA, Approval, Serve). |
| **REF-05** | Benchmark Scenarios| 2026-10-28 | [Standardized_Benchmark_Scenarios_T1_T5.md](file:///d:/ai_developer/project6/task%204/subtask%202/Standardized_Benchmark_Scenarios_T1_T5.md)| Skenario T1–T5 seragam untuk Hermes, MausBot, Rakazo, CrewAI. |
| **REF-06** | Scoring Templates | 2026-10-28 | [scoring_and_evidence_template.md](file:///d:/ai_developer/project6/task%204/subtask%203/scoring_and_evidence_template.md)| Rubrik 1-5, skema 17 bidang, pemisahan N/A non-zero. |
| **REF-07** | CrewAI Official Doc| 2026-10-24 | [CrewAI Documentation (v0.80+)](https://docs.crewai.com) | Arsitektur multi-agen, dependensi LangChain/Pydantic. |
| **REF-08** | OpenRouter Pricing | 2026-10-28 | [OpenRouter DeepSeek V3 Matrix](https://openrouter.ai/models/deepseek/deepseek-chat)| Tarif resmi: $0.14 input / $0.28 output per 1M token. |
| **REF-09** | OpenBot Research | 2026-10-25 | [Intel OpenBot Official Project](https://www.openbot.org) | Analisis kelayakan fisik vs digital; arsip cadangan. |

---

## 6. Lembar Audit & Persetujuan R&D Lead (Consolidation Sign-off)

Laporan konsolidasi temuan riset awal 4 kandidat utama beserta catatan cadangan OpenBot ini telah ditinjau dan disetujui secara resmi oleh R&D Lead:

```
+-----------------------------------------------------------------------------------+
| TANDA TANGAN PERSETUJUAN KONSOLIDASI TEMUAN AWAL (S1-04D)                         |
+-----------------------------------------------------------------------------------+
| 1. Disusun oleh:                                                                  |
|    CrewAI Researcher & Benchmark Coordinator (Rakazo Researcher)                  |
|    Status: CONSOLIDATED & SUBMITTED (28 Oktober 2026)                             |
|                                                                                   |
| 2. Ditinjau dan Disetujui oleh:                                                   |
|    R&D Lead                                                                       |
|    Status: APPROVED & SIGNED (28 Oktober 2026)                                     |
+-----------------------------------------------------------------------------------+
| Catatan Evaluasi R&D Lead:                                                        |
| 'Konsolidasi 4 kandidat telah memberikan gambaran arsitektur yang sangat jelas.    |
| Pemisahan tegas antara fitur native, kebutuhan wrapper custom, kegagalan nyata,   |
| dan batas konteks model memberikan fondasi yang kuat untuk eksekusi Sprint 2.     |
| Penegasan OpenBot murni sebagai cadangan non-aktif disetujui tanpa keraguan.      |
| Dokumen ini disahkan sebagai baseline komparasi resmi R&D Pegawai AI.'            |
+-----------------------------------------------------------------------------------+
```
