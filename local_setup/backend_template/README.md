# Pegawai AI - Shared Backend Development Template (Minimal POC)

**Owner / Maintainer:** Intern 1 (Local Setup & Technical Research)  
**Date:** October 29, 2026 (Sprint 2 - Day 1)  
**Target Consumers:** Intern 2 & 3 (Workflows/Tools) and Intern 4 (Frontend UI)  

---

## 1. Quick Start Guide

### Prerequisites
- Python 3.10+ (Tested on Python 3.14.9)
- Hermes Agent installed locally (`hermes --version`)
- No third-party pip dependencies required for minimal POC (uses standard library `http.server`)

### Running the Server
```bash
# From this directory:
python server.py
```
Server will start listening on `http://127.0.0.1:8080`.

---

## 2. API Contract Specification (for Interns 2, 3, and 4)

### Endpoint Summary
| Method | Path | Purpose | Consumed By |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` or `/api/v1/health` | Backend status, Hermes binary check, model status | Intern 4 (UI Status indicator) |
| `GET` | `/api/v1/config` | Customer profile (`AI Top Trends`), SOP defaults, token limits | Intern 2, 3, 4 |
| `POST` | `/api/v1/agent/execute` | Dispatch task to Hermes Agent engine | Intern 2, 3 (Workflows) & Intern 4 (Chat UI) |
| `GET` | `/api/v1/sessions` | View history of executions, latencies, and tokens | Intern 4 (Audit / History view) |

---

### Request / Response Schemas

#### `POST /api/v1/agent/execute`
**Headers:**
```http
Content-Type: application/json
X-Pegawai-AI-Key: dev-pegawai-ai-2026
X-Department: marketing
```

**Request Body:**
```json
{
  "customer_id": "cust_aitt_001",
  "department": "marketing",
  "prompt": "Tuliskan 1 paragraf ringkas copywriting promosi jasa otomasi AI.",
  "provider": "deepseek",
  "model": "deepseek-flash",
  "tools_enabled": ["read_file", "write_file", "terminal"],
  "timeout_seconds": 60
}
```

**Response Body (200 OK):**
```json
{
  "session_id": "sess_a1b2c3d4",
  "status": "success",
  "department": "marketing",
  "requested": {
    "provider": "deepseek",
    "model": "deepseek-flash"
  },
  "executed": {
    "provider": "copilot",
    "model": "gpt-4o",
    "fallback_applied": true,
    "blocker_note": "DEEPSEEK_API_KEY not set. Falling back to verified Copilot/gpt-4o for smoke test execution."
  },
  "execution_time_seconds": 4.12,
  "output": "Siap meningkatkan efisiensi bisnis Anda? Layanan Pegawai AI dari PT AI Top Trends siap...",
  "error": null,
  "metrics": {
    "input_tokens": 280,
    "output_tokens": 45,
    "total_tokens": 325,
    "cache_read_tokens": 0,
    "estimated_cost_usd": 0.0
  },
  "timestamp": "2026-10-29T09:30:00+07:00"
}
```

---

## 3. Notes for Teammates

### For Intern 2 & 3 (Workflows):
- Do NOT build a separate execution engine or mock server. Use `POST /api/v1/agent/execute` to trigger Hermes.
- Pass the appropriate `department` in the payload (`marketing`, `customer_support`, `sales`).
- Pass custom prompts or SOP constraints directly into the `prompt` field.

### For Intern 4 (Frontend UI):
- CORS is enabled (`Access-Control-Allow-Origin: *`).
- Call `/api/v1/health` on initial page load to verify backend and Hermes connectivity.
- Bind the user chat box or form submission to `POST /api/v1/agent/execute`.
- Use the returned `execution_time_seconds` and `metrics` to display latency and token counts on the dashboard.

