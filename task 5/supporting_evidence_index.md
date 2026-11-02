# INDEKS BUKTI EMPIRIS & JEJAK AUDIT TERINTEGRASI (TASK 1 – 4)
## Repositori Tautan Bukti Tertanggal untuk Sidang Shortlist Hermes Agent (S1-05A)
**Kode Artefak:** S1-05A-EVID  
**Versi:** `v1.1.0`  
**Tanggal Verifikasi:** 28 Oktober 2026  
**Status Audit:** **100% VERIFIED & SANITIZED (Zero Real Secrets)**  

---

## 1. Matriks Jejak Bukti Lengkap (Task 1 s.d. Task 4)

Seluruh pernyataan dan klaim dalam dokumen presentasi Task 5 dapat dilacak ke bukti fisik berikut:

| ID Bukti | Sumber Rujukan | File Artefak Nyata | Temuan Utama yang Dibuktikan |
| :---: | :--- | :--- | :--- |
| **EV-01** | Task 1 Summary | [summary1-3/Hermes R&D.docx](file:///d:/ai_developer/project6/summary1-3/Hermes%20R&D.docx) | Lisensi MIT resmi Nous Research ($0 royalti), arsitektur Python/Rust, syarat mutlak context window $\ge 64.000$ token. |
| **EV-02** | Task 2 Summary | [summary1-3/Hermes R&D (1).docx](file:///d:/ai_developer/project6/summary1-3/Hermes%20R&D%20(1).docx) | Kendala instalasi Windows `.git` permission lock terpecahkan via `git reset --hard HEAD`; konfigurasi guardrail `confirm_dangerous_commands: true`. |
| **EV-03** | Task 2 Smoke Test | [task 2/smoke_test_usage.json](file:///d:/ai_developer/project6/task%202/smoke_test_usage.json) | Pengukuran token riil: **22.444 tokens** (Prompt: 22.383, Completion: 61, Latency: 14.2s) pada tugas one-shot. |
| **EV-04** | Task 3 Summary | [summary1-3/Hermes R&D (2).docx](file:///d:/ai_developer/project6/summary1-3/Hermes%20R&D%20(2).docx) | Laporan pengujian 23 butir checklist R&D: 5 pilar lulus, gateway active (PID 29128), tabel harga model & infrastruktur VPS $48/bln. |
| **EV-05** | Task 3 Multi-Step | [task 3/multistep_usage.json](file:///d:/ai_developer/project6/task%203/multistep_usage.json) | Konsumsi token multi-step: **34.566 tokens**; rata-rata token per tugas terukur **~28.500 tokens**. |
| **EV-06** | Task 4 Subtask 1 | [task 4/subtask 1/AI_Top_Trends_Profile_v1.0.md](file:///d:/ai_developer/project6/task%204/subtask%201/AI_Top_Trends_Profile_v1.0.md) | Profil bisnis dummy `AI Top Trends v1.0.0`, 3 target audiens (UMKM, Creators, Marketers), batasan human review. |
| **EV-07** | Task 4 Subtask 2 | [task 4/subtask 2/Standardized_Benchmark_Scenarios_T1_T5.md](file:///d:/ai_developer/project6/task%204/subtask%202/Standardized_Benchmark_Scenarios_T1_T5.md) | Spesifikasi skenario baku T1 (Riset 5 topik), T2 (Konten), T3 (File), T4 (Jadwal), T5 (Retensi SOP), dan supporting checks. |
| **EV-08** | Task 4 Subtask 3 | [task 4/subtask 3/scoring_and_evidence_template.md](file:///d:/ai_developer/project6/task%204/subtask%203/scoring_and_evidence_template.md) | Rubrik 5 tingkat (1-5), skema 17 bidang bukti, pemisahan skor kualitatif & metrik kuantitatif, aturan N/A non-zero. |
| **EV-09** | Task 4 Subtask 4 | [task 4/subtask 4/Four_Candidate_Consolidated_Comparison.md](file:///d:/ai_developer/project6/task%204/subtask%204/Four_Candidate_Consolidated_Comparison.md) | Matriks komparasi 8 dimensi 4 kandidat (Hermes, MausBot, Rakazo, CrewAI) & catatan kelayakan cadangan OpenBot (Reserve only). |
| **EV-10** | Task 5 Decision | [task 5/Hermes_Agent_Shortlist_Presentation_S1-05A.md](file:///d:/ai_developer/project6/task%205/Hermes_Agent_Shortlist_Presentation_S1-05A.md) | Rekomendasi & Lembar Keputusan Resmi R&D Lead: **CONDITIONAL (Lolos Bersyarat)** dengan 4 prioritas aksi Sprint 2. |

---

## 2. Rujukan Sumber Eksternal Resmi (Dated Official Sources)

1. **Nous Research Hermes Agent Repository:** `https://github.com/NousResearch/Hermes-Agent` (Lisensi MIT, v0.22.2, Oktober 2026).
2. **OpenRouter Official Model Pricing:** `https://openrouter.ai/models/deepseek/deepseek-chat` (Tarif DeepSeek V3: $0.14 input / $0.28 output per 1M token).
3. **OpenAI Official Pricing Matrix:** `https://openai.com/api/pricing/` (Tarif GPT-4o: $2.50 input / $10.00 output per 1M token).
4. **Anthropic Official Model Pricing:** `https://www.anthropic.com/pricing` (Tarif Claude 3.5 Sonnet: $3.00 input / $15.00 output per 1M token).
5. **Intel OpenBot Robotics Project:** `https://www.openbot.org` (Sumber analisis kelayakan hardware fisik vs digital SaaS).
