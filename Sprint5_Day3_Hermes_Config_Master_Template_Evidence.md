# Evidence & Validation Report: Align Hermes Config Mechanism, Master Template Schema and Model/Skill/Tool Permissions
**Sprint 5 Day 3 - Pegawai AI Core Architecture & Multi-Agent Template Alignment**  
**ClickUp Task:** [Day 3: Align Hermes Config Mechanism, Master Template Schema and Model/Skill/Tool Permissions](https://app.clickup.com/t/z8xxqwh79m) (`z8xxqwh79m`)  
**Parent Epic:** `[BE] VPS Deployment (app.pegawaiAI.com/demo), Auth, Hermes Config, Memory & Telegram` (`z8xxqwh794`)  
**Assignee:** Faiz Febriawan (faiz86791@gmail.com)  
**Date:** November 24, 2026  
**Status:** Completed (Verified on Live VPS `139.190.107.151`)  

---

## 1. Executive Summary

Laporan ini menyajikan bukti implementasi dan validasi komprehensif atas penyelesaian seluruh kriteria penerimaan (*Acceptance Criteria*) untuk task **Day 3: Align Hermes Config Mechanism, Master Template Schema and Model/Skill/Tool Permissions** (`z8xxqwh79m`) pada Sprint 5.

Tujuan utama dari task ini adalah:
1. **Penyelarasan Mekanisme Konfigurasi Hermes:** Menegakkan pemetaan resmi antara struktur profil Hermes (`~/.hermes/profiles/<bot>/`) dengan arsitektur Master Template. Secara jujur dan eksplisit mendokumentasikan `user.md` dan `agents.md` sebagai celah arsitektur (*architecture gaps*) yang tidak didukung secara *native* oleh Hermes CLI, alih-alih membuat implementasi semu (*fake implementation*).
2. **Katalog & Skema Master Template Karyawan AI:** Mengembangkan katalog template baku 7 peran karyawan AI (`CRE-01` s/d `CRE-04`, `CS-01`, `CS-02`, dan `MGT-01`) dengan memisahkan *core* inti yang dilindungi (*immutable core*: `SOUL.md`, `SKILL.md`, `ROLE.md`) dari variabel klien yang dapat diinjeksi secara dinamis (`{{brand_name}}`, `{{industry}}`, `{{target_audience}}`, dll.).
3. **Penyatuan Kontrol Izin Model, Provider, Reasoning Effort, Tool Tier, dan Batasan KB:** Menyediakan endpoint terpadu untuk memeriksa dan memperbarui model LLM, provider, tingkat penalaran (*reasoning effort*), tier FastMCP (`READ`, `WRITE`, `ADMIN`), serta isolasi kategori Knowledge Base (seperti memblokir akses finansial untuk agen CS).

Seluruh deliverable telah diuji secara lokal (337/337 tests passed, 8/8 Day 3 unit tests passed), dideploy ke server VPS Ubuntu (`139.190.107.151`), diverifikasi secara live melalui protokol HTTPS Nginx reverse proxy (`https://139.190.107.151.sslip.io`), serta siap untuk integrasi frontend dan production rollout.

---

## 2. Acceptance Criteria Fulfillment Matrix

| Kriteria Penerimaan | Status | Bukti / Catatan Verifikasi Teknis |
| :--- | :---: | :--- |
| **1. Hermes Config Mechanism Alignment** | **PASSED** | Pemetaan resmi diimplementasikan di `bff/bff/master_template.py` dan diekspos melalui `GET /api/hermes/config-mapping`. File `config.yaml`, `.env`, dan `SOUL.md` diverifikasi didukung *native* per profil. File `user.md` dan `agents.md` didokumentasikan secara eksplisit sebagai *unsupported architecture gaps* tanpa *fake implementation*. |
| **2. Master Template Catalog & Schema** | **PASSED** | 7 peran karyawan AI terdaftar di katalog (`CRE-01` s/d `CRE-04`, `CS-01`, `CS-02`, `MGT-01`). Tiap template memiliki berkas `SOUL.md`, `SKILL.md`, dan `ROLE.md` di direktori `templates/agents/`. Dilengkapi endpoint `GET /api/templates/master` dan `GET /api/templates/master/{role_id}`. |
| **3. Immutable Core vs Pluggable Client Variables** | **PASSED** | *Core* kepribadian, kapabilitas, dan batasan wewenang berstatus *locked* (`is_core_locked: true`). Variabel klien dinamis (`{{brand_name}}`, `{{industry}}`, dll.) dirender secara aman melalui endpoint `POST /api/templates/render`. |
| **4. CS Knowledge Base Integration in Master Template** | **PASSED** | Template `CS-01` dan `CS-02` mengintegrasikan seluruh SOP CS v2.1 hasil RnD Manshi (kebijakan retur 7 hari, tidak ada tukar ukuran langsung, pembatalan pesanan sebelum serah terima kurir, SLA pengiriman, dan isolasi finansial). |
| **5. Model, Skill & FastMCP Tool Permissions** | **PASSED** | Endpoint `GET /api/bots/{bot_id}/permissions` dan `PATCH /api/bots/{bot_id}/permissions` menyediakan konfigurasi terpadu: Model, Provider, Reasoning Effort (`low`, `medium`, `high`), FastMCP Tier (`READ`, `WRITE`, `ADMIN`), daftar tool FastMCP yang diizinkan, serta isolasi KB (`allowed_kb`, `denied_kb`, `can_access_finance`). |
| **6. VPS Deployment & Live HTTPS Testing** | **PASSED** | Seluruh kode dideploy ke VPS `139.190.107.151`. Pytest berjalan 8/8 passed di VPS. Keenam endpoint live diuji melalui `https://139.190.107.151.sslip.io/bff/api/...` dan menghasilkan respon HTTP 200 OK. |

---

## 3. Hermes Configuration Mechanism & Architecture Gap Alignment

### 3.1. Struktur Profil Native Hermes CLI
Hermes CLI mengisolasi bot melalui subdirektori profil:
`~/.hermes/profiles/<profile_name>/`

Pada arsitektur *native* Hermes, berkas yang didukung dan dibaca secara langsung saat inisialisasi adalah:
1. **`config.yaml`**: Konfigurasi teknis runtime LLM, parameter temperature, default model, fallback model, timeout, serta aktivasi tool server.
2. **`.env`**: Kredensial rahasia, token akses API provider (OpenAI, DeepSeek, Anthropic, OpenCode Zen/Go), dan kunci webhook lokal.
3. **`SOUL.md`**: Definisi persona, tone of voice, aturan komunikasi, dan batas etika/kepatuhan agen.

### 3.2. Penjelasan Eksplisit Celah Arsitektur (*Architecture Gaps*)
Sesuai arahan arsitektur, BFF **tidak memalsukan (*fake-implement*)** fitur yang tidak ada di Hermes CLI. Celah arsitektur didokumentasikan secara transparan pada spesifikasi:

```json
{
  "documented_architecture_gaps": {
    "user.md": {
      "status": "unsupported_gap",
      "hermes_support": false,
      "reason": "Hermes CLI profiles do not parse a per-agent user.md file. Contextual user preferences and CRM data are injected dynamically by BFF into run instructions or system prompt wrappers rather than stored in profile directories.",
      "mitigation": "BFF acts as the user context injector, loading user-specific data from Postgres and appending to message instructions."
    },
    "agents.md": {
      "status": "unsupported_gap",
      "hermes_support": false,
      "reason": "Hermes CLI is single-agent per profile and does not natively parse an agents.md multi-agent routing table. Cross-agent orchestration, delegation, and supervision are managed externally by the BFF orchestration layer.",
      "mitigation": "BFF coordinates multi-agent handoffs, escalation routing, and permission enforcement across profiles."
    }
  }
}
```

Endpoint verifikasi: `GET /api/hermes/config-mapping`

---

## 4. Master Template Catalog & Separation of Concerns

### 4.1. Katalog 7 Peran Karyawan AI Baku

| Role ID | Role Name | Team | Default Model | MCP Tier | Allowed KB | Denied KB | Finance Access |
| :---: | :--- | :---: | :--- | :---: | :--- | :--- | :---: |
| **CRE-01** | Content Strategist & Omnichannel Lead | Marketing | `deepseek/deepseek-chat` | `WRITE` | `marketing`, `general`, `catalog` | `finance`, `legal` | **BLOCKED** |
| **CRE-02** | Senior Copywriter & Campaign Creator | Marketing | `deepseek/deepseek-chat` | `WRITE` | `marketing`, `general`, `catalog` | `finance`, `legal` | **BLOCKED** |
| **CRE-03** | Visual & Layout Concept Specialist | Marketing | `deepseek/deepseek-chat` | `WRITE` | `marketing`, `general`, `catalog` | `finance`, `legal` | **BLOCKED** |
| **CRE-04** | Creative Director & Tone Supervisor | Marketing | `deepseek/deepseek-chat` | `WRITE` | `marketing`, `general`, `catalog` | `finance`, `legal` | **BLOCKED** |
| **CS-01** | Omnichannel Frontline Support Specialist | CS | `deepseek/deepseek-chat` | `READ` | `cs`, `general`, `catalog` | `finance`, `legal`, `hr` | **BLOCKED** |
| **CS-02** | Customer Service Lead & Quality Escalation | CS | `deepseek/deepseek-chat` | `READ` | `cs`, `general`, `catalog` | `finance`, `legal`, `hr` | **BLOCKED** |
| **MGT-01** | Project Manager & Operational Lead | Management | `deepseek/deepseek-chat` | `ADMIN` | `general`, `cs`, `marketing`, `catalog`, `finance`, `hr`, `legal` | *(none)* | **ALLOWED** |

### 4.2. Immutable Core vs Dynamic Client Variables
Arsitektur master template menerapkan pemisahan ketat:
- **Protected Core (Immutable):** Berkas `SOUL.md`, `SKILL.md`, dan `ROLE.md` memuat aturan kepatuhan, tata bahasa, batasan wewenang, dan framework berpikir yang tidak boleh diubah oleh klien untuk menjamin stabilitas bot.
- **Dynamic Client Variables (Pluggable):** Variabel bisnis spesifik klien disuntikkan secara dinamis menggunakan template placeholder `{{variable_name}}`:
  - `{{brand_name}}`: Nama brand atau entitas bisnis (misal: "Colorbox Indonesia", "Kopi Sore Hari").
  - `{{industry}}`: Bidang usaha (misal: "Fast Fashion & Apparel", "Food & Beverage").
  - `{{target_audience}}`: Karakteristik demografis dan psikografis target pelanggan.
  - `{{content_pillars}}`: Pilar konten media sosial atau strategi komunikasi brand.
  - `{{official_cta}}`: Panggilan aksi resmi (Call-to-Action) untuk interaksi pelanggan.
  - `{{official_hashtag}}`: Tagar resmi kampanye.

Contoh payload rendering pada endpoint `POST /api/templates/render`:
```json
{
  "role_id": "CRE-01",
  "variables": {
    "brand_name": "Aura Glow Cafe & Bakery",
    "industry": "Artisan Bakery & Cafe",
    "target_audience": "Pecinta pastry dan kopi artisan usia 20-40 tahun"
  }
}
```

---

## 5. Model, Skill & FastMCP Tool Permissions Enforcement

Sistem menyediakan kontrol izin granular terpadu melalui `GET /api/bots/{bot_id}/permissions` dan `PATCH /api/bots/{bot_id}/permissions`.

### 5.1. FastMCP Privilege Tiers & Tool Mapping
FastMCP mengelompokkan tool ke dalam 3 tier hierarki:
1. **Tier READ (Level 1):** `ping`, `drive_search`, `drive_read`, `gmail_search`, `gmail_read`, `kb_search`, `task_list`.
2. **Tier WRITE (Level 2):** Seluruh tool READ + `drive_create`, `drive_update`, `drive_rename`, `drive_move`, `gmail_create_draft`, `gmail_label`, `kb_add_link`, `kb_add_note`, `task_create`, `task_comment`, `task_ask_user`, `task_request_review`, `task_complete`.
3. **Tier ADMIN (Level 3):** Seluruh tool WRITE + tool destruktif atau pengiriman langsung: `drive_trash`, `gmail_trash`, `gmail_send`, `gmail_send_draft`, `task_cancel`.

### 5.2. Isolasi Kategori Knowledge Base (KB)
- Agen CS (`siti`, `diana`, `CS-01`, `CS-02`) secara tegas dibatasi hanya mengakses kategori `cs`, `general`, dan `catalog`.
- Upaya pencarian atau ekstraksi dokumen berkategori `finance` (atau dokumen dengan kata kunci penggajian, laporan rugi laba, invoice, pajak) akan secara otomatis diblokir oleh `kb.assert_agent_access`.
- Akses finansial hanya dibuka untuk peran manajemen operasional (`MGT-01`, `bimo`, `admin`, `owner`).

---

## 6. Verifikasi Test Suite & Live VPS Execution

### 6.1. Hasil Unit & Integration Test Lokal (Pytest)
```
============================= test session starts ==============================
rootdir: D:\ai_developer\project6\bff
collected 8 items

bff\tests\test_day3_sprint5.py::test_master_template_catalog_listing PASSED  [ 12%]
bff\tests\test_day3_sprint5.py::test_master_template_detail_and_immutability PASSED [ 25%]
bff\tests\test_day3_sprint5.py::test_cs_master_template_boundaries PASSED    [ 37%]
bff\tests\test_day3_sprint5.py::test_template_variable_rendering PASSED      [ 50%]
bff\tests\test_day3_sprint5.py::test_hermes_config_mapping_spec PASSED       [ 62%]
bff\tests\test_day3_sprint5.py::test_get_bot_permissions PASSED              [ 75%]
bff\tests\test_day3_sprint5.py::test_update_bot_permissions_round_trip PASSED [ 87%]
bff\tests\test_day3_sprint5.py::test_api_master_templates_endpoints PASSED   [100%]

========================= 8 passed, 1 warning in 1.05s =========================
```
*Full regression test: 337 passed, 63 skipped, 0 failed.*

### 6.2. Hasil Eksekusi Remote di Server VPS (`139.190.107.151`)
```
=== SPRINT 5 DAY 3: DEPLOYMENT & VERIFICATION ===
Connecting to VPS 139.190.107.151...

1. Uploading modified & new BFF files...
 - bff/bff/master_template.py uploaded
 - bff/bff/mcp_privileges.py uploaded
 - bff/bff/main.py uploaded
 - bff/tests/test_day3_sprint5.py uploaded

2. Uploading templates/agents directory...
 - templates/agents uploaded successfully

3. Restarting pegawai-ai-bff service on VPS...
BFF responsive on port 8090 (status: 404) after 8s
BFF status: active

4. Running Pytest Suite directly on VPS...
Pytest VPS Output:
tests/test_day3_sprint5.py::test_master_template_catalog_listing PASSED  [ 12%]
tests/test_day3_sprint5.py::test_master_template_detail_and_immutability PASSED [ 25%]
tests/test_day3_sprint5.py::test_cs_master_template_boundaries PASSED    [ 37%]
tests/test_day3_sprint5.py::test_template_variable_rendering PASSED      [ 50%]
tests/test_day3_sprint5.py::test_hermes_config_mapping_spec PASSED       [ 62%]
tests/test_day3_sprint5.py::test_get_bot_permissions PASSED              [ 75%]
tests/test_day3_sprint5.py::test_update_bot_permissions_round_trip PASSED [ 87%]
tests/test_day3_sprint5.py::test_api_master_templates_endpoints PASSED   [100%]
========================= 8 passed, 1 warning in 1.35s =========================

5. Running Live HTTPS API Verification against Nginx...
[PASSED] GET /bff/api/templates/master: 7 templates found
[PASSED] GET /bff/api/templates/master/CS-01: name='Omnichannel Frontline Support Specialist', mcp_tier='READ'
[PASSED] POST /bff/api/templates/render: successfully rendered variables into SOUL.md
[PASSED] GET /bff/api/hermes/config-mapping: documented gaps=['user.md', 'agents.md']
[PASSED] GET /bff/api/bots/siti/permissions: bot_id='siti', mcp_tier='READ', can_access_finance=False
[PASSED] PATCH /bff/api/bots/siti/permissions: updated reasoning_effort='high'
[PASSED] PATCH /bff/api/bots/siti/permissions: reverted reasoning_effort='medium'

ALL 6 LIVE ENDPOINTS VERIFIED 100% OPERATIONAL ON VPS!
```

---

## 7. Deliverables & File Changes Summary

| Berkas | Status | Deskripsi |
| :--- | :---: | :--- |
| `bff/bff/master_template.py` | Baru | Registry katalog master template, logika rendering variabel, mapping Hermes config, dan endpoints permissions. |
| `bff/bff/mcp_privileges.py` | Diperbarui | Penambahan konstanta `TIER_TOOLS`, matriks privilege agent, dan registrasi dinamis tier FastMCP. |
| `bff/bff/main.py` | Diperbarui | Pendaftaran router API endpoint `/api/templates/*`, `/api/hermes/*`, dan `/api/bots/{bot_id}/permissions`. |
| `bff/tests/test_day3_sprint5.py` | Baru | 8 unit and integration tests mencakup catalog listing, immutability, rendering, Hermes mapping, dan permissions. |
| `templates/agents/CS-01_Omnichannel_Customer_Service/` | Baru | Master template CS frontline (`SOUL.md`, `SKILL.md`, `ROLE.md`) dengan SOP CS v2.1 terintegrasi. |
| `templates/agents/CS-02_Customer_Service_Lead/` | Baru | Master template CS lead & eskalasi mutu (`SOUL.md`, `SKILL.md`, `ROLE.md`). |
| `templates/agents/MGT-01_Project_Manager/` | Baru | Master template manajer proyek operasional dengan privilege tier ADMIN (`SOUL.md`, `SKILL.md`, `ROLE.md`). |
| `vps/deploy_day3_sprint5.py` | Baru | Skrip otomatisasi sinkronisasi SFTP ke VPS, restart service, dan pengujian live endpoint HTTPS. |
| `Sprint5_Day3_Hermes_Config_Master_Template_Evidence.md` | Baru | Laporan komprehensif bukti verifikasi teknis dalam format Markdown. |
| `Sprint5_Day3_Hermes_Config_Master_Template_Evidence.docx` | Baru | Dokumen laporan bukti verifikasi teknis resmi dalam format Microsoft Word (.docx). |

---

## 8. Kesimpulan & Rekomendasi

Seluruh target teknis pada **Day 3 Sprint 5** telah terselesaikan 100% sesuai spesifikasi penerimaan (*Acceptance Criteria*). Arsitektur master template karyawan AI kini berdiri di atas fondasi yang kokoh, dengan isolasi wewenang yang tegas, pemisahan yang bersih antara *core* sistem dan data dinamis klien, serta sinkronisasi penuh pada lingkungan VPS produksi.
