# Frontend Feedback - Colorbox CS v2.1 UI Run

**Date:** 2026-11-09  
**Page:** `http://127.0.0.1:8080/`  
**Run:** Customer Support, single agent, account-deletion case (V06)  
**Result:** submission succeeded in 30.18 s; provider displayed `opencode-go`; model `deepseek-v4.1-flash`

## 1. What worked

- The dashboard loaded and accepted a long prompt.
- Single-agent mode executed successfully.
- The result card rendered the full JSON and metrics.
- The result showed `opencode-go` and `deepseek-v4.1-flash`, matching the backend.
- The customer draft was clean: no deletion timeline, no repeated legal/social-media threat, no secret request, and a human-review recommendation.

## 2. Blocking UI problems

### F-01: Wrong brand and wrong SOP are visible

The page banner says `PT AI TOP TRENDS`, the selected SOP card says `SOP-CS-AITT`, and the SLA says `SLA respon < 15 detik`. This is unrelated to Colorbox. The prompt marker `STANDAR OPERASIONAL PROSEDUR` suppressed the SOP's influence on the model output, but the operator is still shown the wrong policy and may believe it applies.

**Fix:** make department/brand/SOP configurable per tenant; for Colorbox, show the Colorbox CS instructions/version and a clear "test harness" label. Never show a different company's SLA.

### F-02: Provider payload does not match the active provider

The UI payload hardcodes `provider: "opencode"`, while the health check and rendered result show `opencode-go`. The backend resolved the active provider in this run, but the mismatch makes the request non-reproducible.

**Fix:** populate provider from `/api/v1/health` (`model_configuration.active_provider`) or a server-side default; do not hardcode a provider string in the client.

### F-03: No persistent conversation

The UI has one textarea and no thread/history. Multi-turn cases require manually embedding prior turns into the prompt, which is error-prone and prevents realistic follow-up testing.

**Fix:** add a conversation/session id and server-side history, or a visible multi-turn transcript with a "send follow-up" action. Keep customer_id and department stable per session.

### F-04: 180-second timeout is too close to observed latency

The client sets `timeout_seconds: 180`. The v2.0 before-case took 158.21 s; a slower provider or multi-agent run could exceed the limit. There is no streaming or partial progress.

**Fix:** raise the client timeout (or make it configurable), add elapsed-time/progress state, and stream or poll for long runs. Do not silently drop a job at 180 s.

## 3. Usability gaps

### F-05: Generic multi-agent framing in single mode

The page still says "Multi-Agent Digital Workforce Studio" and the result card says "Pegawai AI: Asisten Otonom" even in single mode.

**Fix:** reflect the selected mode and department in the header and result card.

### F-06: Raw JSON block only

The result is a raw JSON preformatted block. Priority, escalation, human-review requirement, simulation status, and source coverage are not surfaced as separate badges.

**Fix:** add a summary header with intent, priority, escalation, human-review, simulation, and source count; keep raw JSON behind a collapsible "view raw" control.

### F-07: Hardcoded customer/tenant

The payload hardcodes `customer_id: "cust_aitt_001"`. This is fine for the POC but wrong for Colorbox test evidence.

**Fix:** expose customer/tenant id and department as request context, not literals.

### F-08: No schema validation/error detail

The UI displays whatever JSON comes back. An unescaped-newline response would render but break downstream parsing. Errors are shown via `alert()`.

**Fix:** validate against the output schema; show a clear "invalid JSON/schema" state with the parser error and a retry action; keep the raw body for debugging.

### F-09: No download/copy of structured result

There is a "Salin Respon" copy action, but no JSON download, no evidence metadata, and no run id displayed.

**Fix:** add "download JSON", display run/session id, timestamp, model, provider, latency, token count, and prompt hash.

## 4. UI evidence observations

- Before submission, the selected SOP card visibly said `SOP-CS-AITT` and `SLA respon < 15 detik`.
- After submission, metrics showed `TOTAL LATENSI 30.18 s`, `ESTIMASI TOKEN 19,199`, `MODEL TERPAKAI deepseek-v4.1-flash`, `UPSTREAM PROVIDER opencode-go`.
- The output's `ticket_summary.publicly_verified_facts` contained a negated note about the 14/30-day figures. The customer draft was clean, but this field should contain only verified public facts; move the negative provenance note to `unknowns` or a dedicated limitation field.
- The full-page screenshot is `evidence/ui_20261109_v06/ui_result_fullpage.png`; the submitted prompt is `prompt_submitted.txt`; the raw result and observations are in `ui_run_notes.txt`.

## 5. Priority order for Frontend

1. F-01 wrong brand/SOP (High)
2. F-02 provider mismatch (High)
3. F-04 timeout/progress (Medium-High)
4. F-03 persistent conversation (Medium)
5. F-08 schema validation/error state (Medium)
6. F-05/F-06/F-07/F-09 presentation and context (Low-Medium)
