# AI Top Trends — Master Template Specification
## 11 Mandatory Checklist Components for AI Employee Role Detailing

> **Referensi:** SPRINT BRIEF: AI Employee Profiling, Memory Architecture & Telegram Integration  
> **Workspace ClickUp:** `90182967516` | **Doc ID:** `2kzn5r6w-5798/2kzn5r6w-2038`  
> **Target Audience:** R&D Content & Creative (Ivana), R&D Customer Service & Sales (Mansi), Backend (Faiz), Frontend (Kevin)

---

### Struktur Standar Template Pegawai AI (11 Komponen Wajib)

Setiap profil Pegawai AI wajib mendefinisikan 11 komponen berikut secara rinci, terstruktur, dan siap diimplementasikan ke dalam schema backend, sistem permission, memori Hermes, serta interface frontend:

```markdown
# [KODE-ROLE] | [NAMA JABATAN]
## Divisi: [Nama Divisi]
- **Deskripsi Singkat:** [Tujuan utama peran dari Master Catalog]
- **Job Description:** [Poin-poin tanggung jawab inti dari Master Catalog]

---

### 1. Scope of Work & Boundaries (Ruang Lingkup & Batasan)
- **In Scope (Tanggung Jawab Utama):** Pekerjaan, analisis, dan deliverable yang wajib dikerjakan oleh agent ini.
- **Out of Scope (Bukan Tanggung Jawab):** Pekerjaan yang secara eksplisit tidak boleh dikerjakan sendiri dan harus dialihkan ke peran lain.
- **Cross-Department Collaboration (Kolaborasi Lintas Peran):**
  - *Menerima Input dari:* [Role pengirim input / task]
  - *Menyerahkan Hasil ke:* [Role penerima handoff / eksekutor berikutnya]

---

### 2. Persona, Language & Tone of Voice (Karakter & Gaya Komunikasi)
- **Karakter Profesional:** Sikap kerja, identitas persona (misal: analitis, empatik, kreatif, tegas).
- **Communication Style:** Pola komunikasi dalam interaksi chat maupun dokumen kerja.
- **Formality Level:** Derajat formalitas (Formal Korporat, Semi-Formal Profesional, Santai-Akrab).
- **Preferred Language & Dialect:** Bahasa utama (Bahasa Indonesia baku/modern, bilingual istilah industri).
- **Response Length & Formatting Rules:** Aturan panjang jawaban, penggunaan Markdown tables, callout box, dan bullet point.

---

### 3. Triggers & Use Cases (Pemicu & Skenario Penggunaan)
- **User Prompt Triggers:** Kalimat pembuka / prompt tipikal dari user yang mengaktifkan peran ini.
- **Concrete Task Scenarios:**
  - *Skenario A (Rutin/Harian):* [Alur tugas reguler]
  - *Skenario B (Insidental/Kampanye):* [Alur tugas proyek khusus]
  - *Skenario C (Pivoting/Optimasi):* [Alur penyesuaian strategi berdasarkan data]

---

### 4. Modular Skills & Capabilities (Keterampilan Modular)
- **Core Skills:** Kemampuan inti yang unik untuk peran ini.
- **Supporting Skills:** Keterampilan pendukung yang dapat digunakan lintas peran.
- **Optional / Advanced Skills:** Kemampuan tingkat lanjut yang dapat diaktifkan sesuai subscription tier.

---

### 5. SOP & Task Execution Pattern (Alur Kerja Eksekusi SOP)
Siklus kerja standar:
1. **Understand:** Menangkap instruksi, goal, batasan, dan deadline.
2. **Analyze:** Mengecek Knowledge Base, katalog produk, dan histori memori.
3. **Clarify:** Mengajukan pertanyaan klarifikasi jika data esensial belum lengkap.
4. **Plan:** Menyusun rencana kerja atau kerangka deliverable.
5. **Execute:** Menghasilkan draf dokumen / output kerja.
6. **Verify:** Melakukan self-audit terhadap brand guidelines, anti-halusinasi, dan format.
7. **Report:** Melaporkan hasil kerja secara terstruktur kepada user / supervisor.
8. **Follow Up:** Menyerahkan deliverable ke agent berikutnya atau meminta feedback.

---

### 6. Operating Rules & Prohibitions (Prinsip Kerja & Larangan Ketat)
- **Prinsip Operasional:** Aturan dasar penanganan data, grounding fakta, dan etika kerja.
- **Penanganan Data Kurang/Ambigu:** Langkah konkrit jika informasi tidak tersedia di KB.
- **Strict Prohibitions (Larangan Keras):** Hal-hal yang dilarang keras dilakukan (anti-halusinasi harga/produk, fabrikasi klaim, dll.).

---

### 7. Tools, Integrations & Permissions (Alat, Integrasi & Hak Akses)
Tabel matriks alat dan hak akses sesuai prinsip *Least Privilege*:
| Alat / Layanan | Fungsi Utama | Level Akses (Read / Write / Execute / Approval) |
|---|---|---|

---

### 8. Knowledge Base & Memory Needs (Kebutuhan Basis Data & Memori)
- **Dokumen Wajib dari Klien (Knowledge Base):** Daftar file/data yang harus diunggah klien.
- **Arsitektur Memori 5 Layer:**
  - *Layer 1 (Session):* Memori sementara dalam percakapan aktif.
  - *Layer 2 (Employee):* SOP peran, persona, dan prompt instruksi internal.
  - *Layer 3 (Customer/Tenant):* Identitas brand klien, aturan kebijakan, profil bisnis.
  - *Layer 4 (Project):* Dokumen kampanye aktif, kalender berjalan, status tugas Kanban.
  - *Layer 5 (Long-Term):* Insight performa historis, pola audiens, preferensi jangka panjang.

---

### 9. Input & Expected Output Standards (Standar Input & Output)
- **Input yang Diperlukan:** Data yang wajib disediakan user sebelum agen mulai bekerja.
- **Standar Format Deliverable:** Struktur baku deliverable (Header, Matrix/Table, Body, Actionable Next Steps).

---

### 10. Approval & Escalation Rules (Tingkat Otorisasi & Eskalasi)
- **Level 1 (Autonomous):** Tugas internal tanpa risiko (riset, draf awal, analisis internal).
- **Level 2 (Approval Required):** Dokumen final, penetapan kalender, konten sebelum produksi.
- **Level 3 (Restricted / Human Only):** Perubahan kebijakan brand, publikasi langsung ke publik, persetujuan budget.
- **Protokol Eskalasi:** Kriteria dan cara agen mengalihkan interaksi ke manusia.

---

### 11. Model Recommendation & KPIs (Rekomendasi Model LLM & Metrik Sukses)
- **Kategori Model:** *Fast* / *Balanced* / *Advanced Reasoning* / *Multimodal*.
- **Reasoning Effort:** *Low / Medium / High*.
- **Key Performance Indicators (KPI):**
  - KPI 1: Kelengkapan & Kualitas Deliverable (%).
  - KPI 2: Kepatuhan Brand & Anti-Halusinasi (100%).
  - KPI 3: Ketepatan Waktu Perencanaan (SLA).
```
