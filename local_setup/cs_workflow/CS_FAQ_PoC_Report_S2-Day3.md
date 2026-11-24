# Sprint 2 — Day 3 (November 2, 2026)
## Customer Service (Intern 3) — Basic FAQ Response PoC

**Task focus:** One minimal FAQ/policy response flow using Hermes Agent + DeepSeek V4.1 Flash,
on Intern 1's shared backend template.
**Status:** PoC executed with real model responses. Defects and gaps recorded honestly.
**Not in scope:** automated sending to customers, advanced retrieval, full classification,
ticket workflow, cost analysis, accuracy benchmark.

---

## 1. What this proves — and what it does not

**Proves:** a customer-support question can travel through the shared backend contract to Hermes,
be answered by DeepSeek V4.1 Flash using nothing but an approved knowledge set, be reviewed by a
second QA agent, and come back with latency and token counts. All eight responses below are real
model output — none are fixtures.

**Does not prove:** retrieval quality, multi-customer isolation, production escalation,
ticket management, or that any answer is safe to send to a real customer unattended.

**Draft-only boundary:** every reply here is an internal draft. No email, chat, or ticket was sent.
The escalation blocks are internal recommendations, not actions.

---

## 2. Environment and model verification

| Item | Value | Source |
|---|---|---|
| Machine | `LOQ-WIN11-DEV` (this workstation) | local |
| Hermes binary | `C:\Users\MI\AppData\Local\hermes\bin\hermes.exe` | `hermes --version` |
| Hermes actual version | **v0.22.5 (2026.9.24)**, stable, Python 3.14.9 | `hermes --version` |
| Backend | `local_setup/backend_template/server.py` (Intern 1 template, unmodified) | repo |
| Endpoint | `POST http://127.0.0.1:8080/api/v1/agent/execute` | live |
| Requested provider/model | `opencode-go` / `deepseek-v4.1-flash` | request payload |
| **Actual provider/model (every run)** | **`opencode-go` / `deepseek-v4.1-flash`** | response body |
| Fallback applied | `false` (all 8 runs) | response body |
| Credentials | loaded by the template from `%LOCALAPPDATA%\hermes\.env`; no key committed or printed | server log |

**Model evidence:** the existing `local_setup/evidence/deepseek_v4_1_flash_model_verification.json`
holds the official identifiers and sources. No new model identifier was invented; no silent substitution.

**Discrepancy found:** `/health` reports Hermes `v0.22.2+3291.gbf0203a` because that string is
**hardcoded in `server.py`**, while the installed binary reports **v0.22.5**. The health text is
stale, not the executable. Flagged for Day 4 cleanup.

---

## 3. Method

- **Knowledge:** `faq_knowledge_base.md` — 12 synthetic, authorized FAQ/policy entries (F1–F12)
  plus the escalation rules from `SOP-CS-AITT-2026-V1`.
- **Injection:** the relevant FAQ entries are placed **manually** into the prompt per question
  (`knowledge_ids` in `faq_test_questions.json`). **There is no retrieval engine** — that is
  deliberate for Day 3 and is the main reason "grounded" here means "answered from supplied text".
- **Pipeline:** Intern 1's `customer_support` two-agent path — Siti (customer-facing draft) and
  Hendra (QA score + escalation recommendation).
- **Set:** 8 questions covering standard, missing information, conflicting information,
  sensitive/refund, threat, and policy-difference cases.

---

## 4. Results

| # | Type | Latency | Input / Output / Total tokens | QA score | QA escalation | Verdict |
|---|---|---|---|---|---|---|
| Q1 | standard (pricing) | 98.4 s | 31,937 / 2,644 / 34,581 | 92 | AMAT_AMAN | Correct |
| Q2 | standard (credit rollover) | 158.4 s | 51,240 / 5,037 / 56,277 | 90 | BUTUH_MONITORING | Correct |
| Q3 | standard (change email) | 192.5 s | 31,225 / 2,614 / 33,839 | 92 | AMAT_AMAN | Correct, one added detail |
| Q4 | sensitive (refund request) | 43.8 s | 33,702 / 4,422 / 38,124 | 88 | BUTUH_MONITORING | Correct draft, **wrong escalation level** |
| Q5 | conflicting (30-day claim) | 58.2 s | 33,414 / 4,555 / 37,969 | 92 | BUTUH_MONITORING | Correct correction, **wrong escalation level** |
| Q6 | sensitive (legal/media threat) | 61.3 s | 33,897 / 5,650 / 39,547 | 88 | PERLU_ESKALASI_MANAJEMEN | Correct |
| Q7 | policy difference (Enterprise SLA) | 63.8 s | 50,117 / 3,923 / 54,040 | 93 | BUTUH_MONITORING | Correct |
| Q8 | missing info (delete all data) | 54.9 s | 32,557 / 3,324 / 35,881 | 86 | BUTUH_MONITORING | **Incomplete vs KB F6** |

- HTTP 200 and `status: success` on all 8; zero failures, zero fallbacks.
- Latency: min 43.8 s, max 192.5 s, mean 91.4 s. The first three (Q1–Q3) ran 98–192 s and the
  later five settled at 44–64 s, consistent with a cold start / provider warm-up rather than input size.
- Full requests and responses: `cs_workflow/evidence/Q*_request.json`, `Q*_response.json`;
  consolidated metrics: `cs_workflow/evidence/runs_summary.json`.

---

## 5. Findings

### 5.1 Behaviour that met the design
- **No invented policy.** No reply promised a refund, a discount, a 1-hour SLA, or a completed deletion.
- **Q5 (false 30-day guarantee):** explicitly corrected — KB states 7 days and ≤10% usage, human review.
- **Q7 (Enterprise 1-hour SLA):** correctly refused to confirm; pointed to the individual contract.
- **Q4/Q6 (refund under pressure):** no approval, no denial, no "already escalated" claim; asked for
  the information needed to review and promised follow-up by email only.
- **Q8:** did not claim the data had been deleted; asked for identity verification first.
- **Security line:** every draft includes the "we never ask for passwords/tokens/CVV/PIN" reminder.

### 5.2 Defects to fix (recorded, not hidden)
1. **Escalation misclassification (Q4, Q5).** The SOP says refund requests *must* go to a human, but
   the QA agent marked both `BUTUH_MONITORING`, not `PERLU_ESKALASI_MANAJEMEN`. Q6, which contains a
   legal/media threat, was classified correctly. The escalation classifier is therefore inconsistent
   and cannot yet be trusted as a routing signal.
2. **Q8 contradicts KB F6.** The draft implies the account *and its backups* are deleted permanently,
   but omits both timings in the KB: review within **14 working days** after verification, and backup
   copies removed within **30 days**. As written it would set a false expectation about backups.
3. **Unrequested detail (Q3).** The draft says a "verification code" is sent to the old email; KB F5
   only says verification via the old email. Plausible, but invented specificity.
4. **Boilerplate leakage.** The password/CVV reminder appears in all eight drafts, including Q1
   (pricing) and Q2 (credit expiry), where the SOP only requires it when the case involves an account
   or payment. Harmless but off-SOP and repetitive.
5. **Unnecessary apology (Q1).** "Mohon maaf atas ketidakjelasan informasi" apologises for a fault
   that did not occur; the SOP wants one brief, genuine apology only when something went wrong.
6. **Process promise (Q1).** "Kami akan mengirimkan rincian penawaran tertulis" commits the company to
   sending a written offer. A process promise, not a result promise — but should be a human decision.
7. **Latency.** 91 s mean is far outside the SOP's "<5 minutes for FAQ" target only if measured end to
   end against a customer; as an internal draft it is acceptable, but the frontend must show progress.

### 5.3 Knowledge gaps exposed
- No KB entry covers **invoice/ VAT (PPN) documentation**, **payment method changes**, or
  **usage-limit overage** — questions on those would have to be escalated as unknown.
- No explicit statement of **refund processing time**, only eligibility. The model correctly avoided
  inventing one, which means customers would get "we will inform you by email" with no expectation set.

---

## 6. Real vs simulated inventory

| Component | Status | Detail |
|---|---|---|
| Hermes subprocess + DeepSeek inference | **REAL** | 8 live calls, `fallback_applied: false` |
| Two-agent CS drafting + QA | **REAL** | Siti draft, Hendra score/status |
| Backend API contract | **REAL** | Intern 1 template, unmodified |
| FAQ knowledge injection | **MANUAL / TEMPORARY** | Entries pasted per question; no retrieval |
| FAQ knowledge content | **SYNTHETIC** | F1–F12 invented for this PoC |
| Customer identities | **SYNTHETIC** | `cust_syn_00x` |
| Escalation routing | **RECOMMENDATION ONLY** | Text block; nothing routed, nothing sent |
| Auth | **SIMULATED** | Static `X-Pegawai-AI-Key` header |
| Multi-tenant isolation | **NOT IMPLEMENTED** | Out of scope |
| Retrieval, classification, ticket summaries | **NOT IMPLEMENTED** | Deferred to Sprint 3 tasks |

---

## 7. Day 4 (November 3) next actions

1. Fix the two defects that affect correctness: Q8's omitted timelines (14 working days / 30 days) and
   the refund escalation rule (force `PERLU_ESKALASI_MANAJEMEN` for any refund request).
2. Demo this same flow live: one standard FAQ (Q1) and one sensitive case (Q4), showing the draft,
   the QA block and the evidence files.
3. Present the limitation list above as-is — the "what it got wrong" table is the deliverable, not a
   weakness to hide.
4. Optional, only if time allows: move the security reminder behind the account/payment condition.
5. Do **not** add retrieval, ticket summaries, multi-customer testing, or cost analysis — those stay
   in the existing Sprint 3 tasks.

---

## 8. Evidence index

| File | Contents |
|---|---|
| `cs_workflow/faq_knowledge_base.md` | Synthetic authorized KB, F1–F12 + escalation rules |
| `cs_workflow/faq_test_questions.json` | 8 questions with type, expected behaviour, knowledge IDs |
| `cs_workflow/run_faq_poc.py` | Runner (builds prompt, calls backend, saves evidence) |
| `cs_workflow/digest.py` | Extracts replies, QA scores, escalation, flags |
| `cs_workflow/evidence/Q*_request.json` | Exact payload per question |
| `cs_workflow/evidence/Q*_response.json` | Full real response, HTTP status, latency |
| `cs_workflow/evidence/runs_summary.json` | Model, fallback, tokens, QA score, escalation |
| `local_setup/evidence/server_stderr.log` | Backend log: env loaded, routing per request |
| `local_setup/evidence/hermes_version_output.txt` | Hermes version evidence (v0.22.5 on this machine) |
| `local_setup/evidence/deepseek_v4_1_flash_model_verification.json` | Official model identifiers/sources |

**Blockers:** none. The only open discrepancy is the stale hardcoded Hermes version string in `/health`
(section 2), which does not affect execution.
