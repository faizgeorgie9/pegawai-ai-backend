# DAILY TASK UPDATE — S1-04B: PREPARE STANDARDIZED BENCHMARK SCENARIOS
**Tanggal Pelaporan:** 28 Oktober 2026  
**Kode Subtask:** S1-04B (Bagian dari Task 4 / S1-04: Shared Benchmark Test Kit)  
**Status Eksekusi:** **COMPLETED (100% Selesai)**  
**Penyusun:** MausBot Researcher (Author)  
**Koordinator & Reviewer:** Rakazo Researcher & R&D Lead  

---

## 1. Ringkasan Pencapaian Hari Ini
Hari ini telah diselesaikan penyusunan paket skenario pengujian benchmark terstandarisasi (**Skenario T1 sampai T5**) beserta protokol pengujian pendukung, dataset masukan mesin, pedoman uji ulang, dan aturan penanganan skor N/A untuk 4 kandidat agen (**Hermes Agent**, **MausBot**, **Rakazo**, dan **CrewAI**).

Selain itu, seluruh berkas Subtask 1 (S1-04A) telah dirapikan ke dalam subfolder khusus `task 4/subtask 1` agar struktur proyek tetap bersih dan terorganisir.

---

## 2. Rincian Checklist Pekerjaan Subtask 2

- [x] **Define T1 research and T2 content prompts:**
  - **T1 (Research):** 5 topik industri AI konkret di Indonesia (WhatsApp CS, Open-Source vs Proprietary LLM, AI coding assistants, UU PDP, Micro-SaaS AI agency) dengan syarat minimal 2 sitasi URL kredibel per topik.
  - **T2 (Content):** 1 Strategic Editorial Brief, 1 Artikel Blog SEO (1.200–1.500 kata), dan 3 Draft Medsos spesifik (Instagram Carousel 10 slide, Skrip TikTok/Reels 60 detik tabel 3 kolom, dan LinkedIn Thought Leadership post) dengan penanda wajib `Status: DRAFT_READY_FOR_HUMAN_REVIEW`.
- [x] **Define T3 file and T4 scheduling scenarios:**
  - **T3 (File Ops):** Berkas masukan nyata `leads_raw_sample.csv` (10 UMKM leads), rumus matematis Priority Score, klasifikasi 3 Tier prospek, pembuatan `processed_leads_summary.json` dan `outreach_pipeline.csv`, serta verifikasi mandiri *zero data loss*.
  - **T4 (Scheduling & Idempotency):** Definisi cron `0 9 * * *`, uji persistensi state setelah proses di-kill/restart, dan uji pencegahan eksekusi ganda (*idempotency key deduplication*).
- [x] **Define T5 SOP and session-retention scenario:**
  - Pengujian memori 4 tahap: (1) Umpan dengan frasa klise + koreksi keras SOP oleh manusia, (2) Reset sesi total / New Session ID, (3) Uji kepatuhan SOP pada sesi baru tanpa reminder, dan (4) Sub-uji retensi SOP saat berganti provider LLM (misal GPT-4o ke DeepSeek).
- [x] **Define provider-switching, tool-integration, reliability, security/approval and cost/commercial feasibility checks:**
  - Matriks 4 provider LLM (OpenAI, Anthropic, OpenRouter DeepSeek, Copilot) di bawah temperatur seragam 0.7.
  - Uji ketahanan prompt injection (Jailbreak ekstraksi system prompt dan path traversal OS).
  - Verifikasi default human approval gate (`[Y/N]` confirmation pada aksi berisiko).
  - Rumus kelayakan komersial untuk 100 dan 1.000 task/bulan.
- [x] **Version dummy inputs and document repeat/N/A rules:**
  - Input profil bisnis sintetis versi `v1.0.0` (AI Top Trends).
  - Aturan wajib minimal 2 kali pengujian (*Trial 1* dan *Trial 2*) untuk skenario non-deterministik (T1, T2, T5) dengan batas deviasi $\le 30\%$.
  - Taksonomi skor `N/A (Not Applicable)` objektif untuk membedakan batasan arsitektur dari kegagalan fungsional.
- [x] **Obtain consistency review:**
  - Diverifikasi oleh Benchmark Coordinator (Rakazo Researcher) dan disetujui secara resmi oleh R&D Lead dalam berkas `consistency_review_notes.md`.

---

## 3. Daftar Berkas Artefak yang Dihasilkan
Semua artefak tersimpan rapi di direktori `d:\ai_developer\project6\task 4\subtask 2\`:
1. `Standardized_Benchmark_Scenarios_T1_T5.md` — Dokumen master spesifikasi lengkap T1–T5.
2. `benchmark_scenarios_dataset.json` — Dataset mesin terstruktur (JSON schema) berisi semua prompt dan parameter.
3. `leads_raw_sample.csv` — Berkas sampel 10 leads UMKM untuk pengujian T3.
4. `supporting_checks_and_rules.md` — Spesifikasi teknis provider-switching, tools, reliability, security, approval, repeat, dan N/A rules.
5. `consistency_review_notes.md` — Lembar audit konsistensi dan persetujuan resmi R&D Lead.
6. `Standardized_Benchmark_Scenarios_T1_T5.docx` — Dokumen format Microsoft Word siap baca/cetak.
7. `Standardized_Benchmark_Scenarios_T1_T5.html` — Versi tampilan web modern lengkap dengan tombol *1-Click Copy to Google Docs*.

---

## 4. Langkah Selanjutnya (Next Steps)
- Siap lanjut ke **Subtask 3 (S1-04C: Scoring & Evidence Templates Creation)** untuk menyusun template pencatatan skor, log terminal, konsumsi token, dan matriks perbandingan 4 kandidat.
