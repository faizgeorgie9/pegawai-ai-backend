# S2-03A: Intern 1: Backend Proof of Concept
**Sprint 2 — Day 3: November 2, 2026**  
**Role:** Intern 1 (Local Setup & Technical Research / Backend Lead)  
**Assigned Task:** S2-03A — Minimal Shared Backend POC for One Representative Request  
**Deliverable Status:** COMPLETE  
**Scope Target:** Minimal Proof of Concept (POC) — Production Readiness Not Required  

---

## 1. Executive Summary & Checklist Status

On Day 3 (November 2, 2026), Intern 1 successfully realized and executed the **Minimal Shared Backend Proof of Concept (POC)**. Building upon the Day 2 shared template and API specification, this deliverable connects one agreed representative request flow through **Hermes Agent** and the officially verified **DeepSeek V4.1 Flash** model via the Opencode provider.

### Day 3 Checklist Review:
- [x] **Implement one minimal agreed request flow through the shared backend template**
- [x] **Expose only basic status and output access required by the representative request**
- [x] **Return basic failure information; defer robust timeout/retry/recovery work to S3-02C**
- [x] **Keep minimal sanitized request/response evidence; defer comprehensive execution logging to S3-01D**
- [x] **Retain available provider/model and token/latency observations without building telemetry or cost tracking**
- [x] **Run a small request/response check against the shared contract**

### Evidence & Review Checklist:
- [x] **Attach initial backend source and concise run commands**
- [x] **Attach one representative request/response example, labeled actual or fixture**
- [x] **Record the small execution/status/output check and any exact failure**
- [x] **Retain available sanitized error/usage observations; comprehensive recovery evidence is Sprint 3 work**
- [x] **List real versus simulated components, unverified boundaries and Day 4 one-flow validation next actions**

---

## 2. Concise Run Commands & Backend Source Reference

The backend POC runs on standard Python without complex external process managers or databases:

### Quick Run Commands:
```bash
# 1. Navigate to shared backend template
cd local_setup/backend_template

# 2. Install lightweight dependencies (Pillow for image generator)
pip install -r requirements.txt

# 3. Start Shared Backend Server (Listens on http://127.0.0.1:8080)
python server.py
```

### Health Verification Check:
```bash
curl -X GET http://127.0.0.1:8080/health
```
**Actual Output:**
```json
{
  "status": "healthy",
  "service": "Pegawai AI Shared Backend POC (S2-03A)",
  "sprint": "Sprint 2 - Day 3 (November 2, 2026)",
  "intern_role": "Intern 1: Local Setup & Technical Research",
  "hermes": {
    "installed": true,
    "binary_path": "C:\\Users\\LOQ\\AppData\\Local\\hermes\\bin\\hermes.exe",
    "version": "v0.22.2+3291.gbf0203a (stable)"
  },
  "model_configuration": {
    "target_model": "DeepSeek V4.1 Flash",
    "target_identifier": "deepseek-v4.1-flash",
    "active_provider": "opencode",
    "credentials_status": "READY (Active via Opencode Provider)",
    "live_model_in_use": "deepseek-v4.1-flash"
  },
  "server_time": "2026-11-02T10:13:30+0700"
}
```

---

## 3. Representative Request / Response Execution Evidence (ACTUAL)

A live, representative execution request was dispatched to `POST /api/v1/agent/execute` on November 2, 2026.

### Request Payload (`local_setup/evidence/s2_03a_representative_request.json`):
```json
{
  "customer_id": "cust_aitt_001",
  "department": "marketing",
  "prompt": "Susun naskah pengumuman peluncuran layanan Konsultasi Otomasi AI untuk pelaku UMKM, fokus pada efisiensi waktu kerja dan pemangkasan biaya operasional tanpa overpromising.",
  "agent_mode": "auto",
  "provider": "opencode",
  "model": "deepseek-v4.1-flash",
  "timeout_seconds": 180
}
```
**Headers:**
- `Content-Type: application/json`
- `X-Pegawai-AI-Key: dev-pegawai-ai-2026`
- `X-Department: marketing`

### Actual Response Evidence (`local_setup/evidence/s2_03a_representative_response.json`):
- **HTTP Status Code:** `200 OK`
- **Roundtrip Latency:** `48.78 seconds`
- **Backend Internal Duration:** `48.59 seconds`
- **Status:** `success`
- **Session ID:** `sess_8742cdde`
- **Active Model:** `deepseek-v4.1-flash` (via Opencode Zen API)
- **Fallback Applied:** `false` (Direct primary model execution)
- **Token Telemetry:**
  - `input_tokens`: 14,568
  - `output_tokens`: 5,399
  - `total_tokens`: 19,967

#### Content Highlights Produced:
1. **Agent 1 (Rian - Copywriter):** Formatted narrative depicting a micro-merchant (*Bu Rina*) manually reconciling 40+ chat orders until 23:40, structured 90-minute consultation deliverable breakdown, transparent disclosure *"Yang Kami Janjikan dan Yang Tidak"*, and 7 hashtags.
2. **Agent 2 (Diana - QC Auditor):** Assigned **Skor QC: 88/100**, validated zero forbidden words (*no "kaya instan"*), praised the grounded humble tone, and recommended streamlining the batch-1 explanation.
3. **Agent 3 (Budi - Visual Specialist):** Formatted visual concept of early morning wooden desk with released ballpoint pen, color palette *Deep Tea Green `#14433B`*, *Paper Cream `#F3E9D2`*, and *Saffron `#E8A33D`*, complete with Midjourney v6 prompt.

---

## 4. Basic Status, Output Access & Failure Reporting Check

To satisfy acceptance criteria regarding basic failure reporting without building premature enterprise retry loops:

### Failure Check Test Case: Missing Required Field (`prompt`)
- **Request:** `POST /api/v1/agent/execute` with body `{"customer_id": "cust_err_01", "department": "marketing"}`
- **HTTP Status:** `400 Bad Request`
- **Response Payload (`local_setup/evidence/s2_03a_error_handling_check.json`):**
  ```json
  {
    "error": "Field 'prompt' is required"
  }
  ```
- **Outcome:** Fails fast gracefully without server crash or unhandled exception.

---

## 5. Explicit Inventory: Real vs. Simulated Components

In strict alignment with Day 3 sprint boundaries, the following inventory delineates production-like versus prototype components:

| Component | Status | Implementation Detail |
| :--- | :---: | :--- |
| **Hermes Agent Subprocess** | **REAL** | Native execution of `hermes.exe -z ...` CLI v0.22.2 |
| **Upstream Model Inference** | **REAL** | Native API call to DeepSeek V4.1 Flash via Opencode (`OPENCODE_ZEN_API_KEY`) |
| **Dynamic Multi-Agent Output** | **REAL** | Live reasoning, dynamic scoring (88/100), and custom prompt generation |
| **Pillow Banner Rendering** | **REAL** | 1080x1080 px image rendered dynamically to disk based on prompt text |
| **Basic Error Validation** | **REAL** | HTTP 400 on missing prompt / malformed JSON |
| **Customer Data Isolation** | **SIMULATED** | Synthetic customer ID (`cust_aitt_001`); no multi-tenant DB isolation |
| **Authentication & RBAC** | **SIMULATED** | Static token check (`dev-pegawai-ai-2026`); production JWT/OAuth deferred |
| **Retry & Circuit Breaker** | **DEFERRED** | Deferred to Sprint 3 (`S3-02C`) |
| **Comprehensive Logging & Cost Telemetry** | **DEFERRED** | Basic latency and token count retained; cost modeling deferred to `S3-01D` |
| **Frontend Offline Fixtures** | **MOCKED** | 7 standalone JSON mocks in `mock_fixtures/` for Intern 4 development |

---

## 6. Unverified Customer Boundaries & Day 4 Next Actions

### Unverified Boundaries:
1. **Tenant Separation:** All departments currently execute within the same shared OS process and working directory (`project6`). True database isolation and memory sandbox boundaries are unverified and out of POC scope.
2. **Access Control:** Header token `X-Pegawai-AI-Key` is validated statically; department permissions are not tied to an active identity provider.

### Day 4 Next Actions (One-Flow End-to-End Validation):
1. **Workflow Integration Sync (Interns 2 & 3):** Validate that the Marketing and CS workflow scripts call `POST /api/v1/agent/execute` directly without local subprocess wrapper duplication.
2. **Frontend Wiring (Intern 4):** Connect the live dashboard client (`index.html`) or React UI to `/api/v1/agent/execute`, verifying progressive loading states during the ~48s roundtrip latency.
3. **End-to-End Handover:** Execute one unified flow demonstrating UI input -> Backend routing -> Hermes DeepSeek inference -> Dynamic multi-card presentation.

