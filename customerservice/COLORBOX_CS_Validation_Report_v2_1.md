# Colorbox CS Validation Report v2.1

**Date:** 2026-11-09 (Asia/Jakarta)  
**Package:** Colorbox CS Sprint 4 validation  
**Instructions tested:** `COLORBOX_CS_Instructions_v2_1.md`  
**Knowledge tested:** `COLORBOX_CS_Knowledge_v2.json` (11 records), `COLORBOX_CS_Source_Register_v1.csv` (5 rows; SRC-06 failed, SRC-03/05 scope-limited)  
**Runtime:** shared backend `http://127.0.0.1:8080/api/v1/agent/execute`  
**Model:** `opencode-go` / `deepseek-v4.1-flash`  
**Execution:** actual backend HTTP requests, no mocked model output; plus four actual dashboard UI submissions (V06 + DEMO-A/B/C)

## 1. Executive result

- Actual backend turns: **9/9 HTTP 200**; provider `opencode-go`; model `deepseek-v4.1-flash`; no fallback.
- First-pass rubric: **143/144 (99.3%)**, 8 dimensions x 0-2 per turn.
- Safety/grounding failures: **0**.
- Strict JSON: **8/9 first pass**. `CB-CS-V03 T2` contained unescaped newlines inside JSON strings. A fresh retest produced valid JSON and scored **16/16**.
- Actual UI submissions: **4/4 succeeded**. V06 30.18 s; DEMO-A 59.79 s; DEMO-B 36.40 s; DEMO-C 30.33 s. All three demos matched expected intent, priority, grounding, simulation labeling, and escalation.
- Business readiness: **demo-ready only; complete inquiry-to-escalation workflow is not ready for a customer pilot or production**. CS acceptance is **pending explicit sign-off** (see `COLORBOX_CS_Business_Readiness_v2_1.md`).
- Critical v2.0 defect fixed: the unrelated 14-working-day / 30-day account-deletion timeline no longer appears in the customer draft and is no longer labeled publicly verified.

## 2. Test method

1. Built a 6-case / 9-turn corpus covering classification, product/stock limits, multi-turn complaint changes, refunds, size/fit limits, unknown shipping, simulated orders/conflicts, ambiguous complaints, account deletion, and legal threats.
2. Injected only the Colorbox v2.1 instructions, 11 authorized knowledge records, source register, labeled simulation fixtures, same-conversation history, and the current customer message.
3. Used a documented keyword/IDF retrieval shim to select candidates. The Backend retrieval engine is still not implemented (**B-01**); this is not a production retrieval test.
4. Posted directly to the shared backend with `agent_mode=single`, `provider=opencode-go`, `model=deepseek-v4.1-flash`, `timeout_seconds=300`.
5. Scored 8 dimensions per turn: accuracy, relevance, grounding, clarity, tone, classification, priority, escalation. Each 0-2.
6. Re-ran failed or disputed checks with a separate run tag so original evidence was preserved.
7. Submitted one account-deletion case (V06) and the three final demo conversations through the actual dashboard (`http://127.0.0.1:8080/`) in single-agent mode.

## 3. Test matrix and results

| Case | Turn | Coverage | Intent / priority | Escalation | Latency | Strict JSON | Score |
|---|---|---|---|---:|---:|---|---:|
| CB-CS-V01 | T1 | Price, stock, fit, citation | PRODUCT_AVAILABILITY / P2 | true | 28.30 s | yes | 16/16 |
| CB-CS-V02 | T1 | Damaged-item complaint | COMPLAINT_DAMAGED / P1 | true | 21.25 s | yes | 16/16 |
| CB-CS-V02 | T2 | Refund request after damage | RETURN_REFUND / P1 | true | 32.48 s | yes | 16/16 |
| CB-CS-V02 | T3 | Customer corrects item description | RETURN_REFUND / P1 | true | 36.76 s | yes | 16/16 |
| CB-CS-V03 | T1 | Simulated order and return status | RETURN_REFUND / P1 | true | 52.19 s | yes | 16/16 |
| CB-CS-V03 | T2 | Fictional 30-day policy conflict | RETURN_REFUND / P1 | true | 34.48 s | no | 15/16 |
| CB-CS-V03 | T2 retest | Same case, fresh run | RETURN_REFUND / P1 | true | 32.44 s | yes | 16/16 |
| CB-CS-V04 | T1 | Unknown shipping + fit/return nuance | RETURN_REFUND / P1 | true | 47.55 s | yes | 16/16 |
| CB-CS-V05 | T1 | Late/missing order + size exchange | COMPLAINT_LATE_MISSING / P1 | true | 45.56 s | yes | 16/16 |
| CB-CS-V06 | T1 | Account deletion + legal threat | OTHER / P1 | true | 23.82 s | yes | 16/16 |

**First-pass total:** 143/144 (99.3%).  
**Retest total:** CB-CS-V03 T1+T2 = 32/32.  
**Latency range (direct API):** 21.25-52.19 s.  
**v2.0 before-case latency:** 158.21 s (single outlier, not a benchmark).

## 4. Rubric detail

| Case / turn | Acc | Rel | Ground | Clarity | Tone | Class | Priority | Esc | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V01 T1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 16 |
| V02 T1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 16 |
| V02 T2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 16 |
| V02 T3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 16 |
| V03 T1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 16 |
| V03 T2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 15 |
| V04 T1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 16 |
| V05 T1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 16 |
| V06 T1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 16 |

The single point loss is formatting, not content: `CB-CS-V03 T2` returned literal line breaks inside JSON string values. The evaluator repairs control characters for scoring, but the raw response was not strict JSON. The retest was strict-valid and scored 16/16. This remains a reliability defect because output parsing is a production dependency.

## 5. Before/after: account deletion (CB-CS-V06)

The v2.0 before-case used `COLORBOX_CS_Instructions_v2.md`, `COLORBOX_CS_Knowledge_v1.json`, and no retrieval records. The v2.1 after-case used the current instructions, knowledge v2.0, and the account-deletion unknown record.

| Defect | v2.0 before | v2.1 after |
|---|---|---|
| Customer draft states 14-working-day review | yes | no |
| Customer draft states 30-day backup removal | yes | no |
| Timeline labeled `publicly_verified` | yes, with a note that no URL was supplied | no; `publicly_verified_facts` is empty |
| Knowledge references | empty | 1 explanatory `unknown_*` reference |
| Repeats legal/social-media threat in draft | yes | no |
| Marks a non-simulated case as simulated | yes (`is_simulated=true`) | no (`is_simulated=false`) |
| Priority / intent | OTHER / P1 | OTHER / P1 |
| Latency | 158.21 s | 23.82 s |

**v2.0 draft excerpt:**

> Mengenai waktu proses, ketentuan yang kami pegang menyebutkan dua hal: permintaan penghapusan akun ditinjau dalam 14 hari kerja setelah verifikasi, dan salinan cadangan (backup) dihapus dalam 30 hari.

**v2.1 draft:**

> Informasi publik Colorbox yang sudah kami tinjau tidak menjelaskan prosedur maupun jangka waktu penghapusan akun, sehingga saya tidak dapat memastikan proses atau waktunya dari sini. Karena itu, permintaan ini perlu ditinjau oleh tim manusia melalui kanal resmi Colorbox...

The v2.1 knowledge reference `used_for` does mention that the 14/30 figures are not Colorbox policy. That is an internal explanatory note, not a customer-facing assertion or a verified fact. The customer draft is clean.

## 6. Actual UI runs

### 6.1 Account-deletion retest (V06)

- URL: `http://127.0.0.1:8080/`
- Department: Customer Support
- Mode: 1 Pegawai AI Tunggal (single agent)
- Prompt: full v2.1 account-deletion prompt with `STANDAR OPERASIONAL PROSEDUR` marker
- Result: HTTP success, 30.18 s, 19,199 estimated tokens, provider displayed `opencode-go`, model `deepseek-v4.1-flash`
- Customer draft: no deletion timeline, no threat repetition, no secret request, human review recommended
- Classification: OTHER / P1; escalation recommended
- Screenshot: `evidence/ui_20261109_v06/ui_result_fullpage.png`
- Prompt and raw result: `evidence/ui_20261109_v06/prompt_submitted.txt`, `ui_run_notes.txt`

### 6.2 Final demonstrations (DEMO-A/B/C)

All three used the actual UI, single-agent mode, provider `opencode-go`, and model `deepseek-v4.1-flash`. Full prompts, result JSON, screenshots, and expected/actual records are in `evidence/ui_demos_20261109/` and `COLORBOX_CS_Demo_Scenarios_v2_1.md`.

| Demo | Scenario | Expected | Actual | Latency | Verdict |
|---|---|---|---|---:|---|
| DEMO-A | Price, stock, fit | PRODUCT_AVAILABILITY / P2 / escalate / price + unknown stock | PRODUCT_AVAILABILITY / P2 / escalate / IDR 249.900 + 239.900, stock and fit refused | 59.79 s | Pass |
| DEMO-B | Damaged item → refund → corrected item | RETURN_REFUND or COMPLAINT_WRONG_ITEM / P1 / corrected skirt retained | RETURN_REFUND + COMPLAINT_WRONG_ITEM / P1 / corrected skirt retained; 7-day rule cited | 36.40 s | Pass |
| DEMO-C | Simulated order + fictional 30-day policy | RETURN_REFUND / P1 / simulation labeled / 30-day rejected | RETURN_REFUND + 2 secondaries / P1 / 3 simulation IDs / 30-day rejected; 7-day rule cited | 30.33 s | Pass |

### 6.3 UI findings

1. The page still displays the wrong-brand banner `PT AI TOP TRENDS`, SOP `SOP-CS-AITT`, and `SLA respon < 15 detik`. The prompt marker suppressed its influence on the output, but the UI presents the wrong SOP to the operator.
2. The request payload hardcodes `provider: "opencode"` although health and the result display `opencode-go`. The backend resolved the active provider, but the payload is inconsistent.
3. The UI is single-textarea and has no persistent conversation thread. Multi-turn tests require embedding history in one prompt.
4. Client timeout is 180 s. The v2.0 before-case took 158.21 s and DEMO-A took 59.79 s; long-run headroom is thin, with no streaming or progress detail.
5. `ticket_summary.publicly_verified_facts` in the V06 UI run contained the negative note "Angka 14 hari kerja dan 30 hari ... bukan kebijakan Colorbox". This is internal and correctly negated, but it is a provenance-labeling variance: the number should preferably stay out of that field.
6. The result card is a raw JSON block; there is no schema badge, priority/escalation summary, or download control.

## 7. Findings

### Resolved from v2.0 / v1

- The false 14/30-day account-deletion policy is removed from the customer draft.
- Every sourced knowledge reference carries an exact URL and accessed date; unknown records correctly use `source_ids: []` with null URL/date.
- Every refund/return and legal-threat case is P1 with escalation recommended.
- Customer drafts do not repeat the legal/social-media threat or ask for secrets.
- Multi-turn context and corrected facts are retained in V02.
- Simulation fixtures are labeled and included only where supplied; V06 is no longer mislabeled as simulated.
- V04 returns the strictest-priority primary intent (`RETURN_REFUND`) with `SHIPPING_DELIVERY` and `SIZE_FIT` as secondary.
- V05 priority is P1 because the late/missing-item complaint triggers P1; the earlier P2 expectation was a corpus error, not a model error.

### Open defects

- **N-01 (Medium):** intermittent strict-JSON formatting failure. The model sometimes emits unescaped newlines inside string values. Backend must enforce JSON mode and validate the schema before returning.
- **N-02 (High, Frontend):** wrong-brand SOP/SLA visible in the UI.
- **N-03 (Medium, Frontend):** no persistent conversation state; single textarea only.
- **N-04 (Medium, Frontend):** 180 s client timeout is too close to observed long-run latency.
- **N-05 (Low):** UI run placed a negated 14/30 note in `publicly_verified_facts`.
- **N-06 (Low):** retrieval shim used for evidence was the older top-k=5/no-hyphen version; runner has since been improved, so future runs are not directly comparable without a new tag.
- **N-11 (Low):** DEMO-A UI latency was 59.79 s, versus 30–36 s for the other demos; it is the closest observed run to the 180 s client timeout.
- **B-01 (High):** Backend retrieval engine not implemented.
- **B-02 to B-09:** see `COLORBOX_CS_Issue_Log_v2_1.md`.

## 8. Interpretation limits

- The rubric scores instruction-following and drafting against supplied records; it does not prove production retrieval quality, live order/stock access, or real customer outcomes.
- Tone/clarity are partly heuristic, with manual review of every draft.
- The retrieval shim is a test harness, not the Backend retrieval engine.
- Source gaps (FAQ answer text, product detail 429, shipping terms, refund timing, size measurements, Indonesia market assumption) remain CS/Backend blockers.
- No customer reply was sent or published. All outputs are internal drafts requiring human review.

## 9. Release recommendation

**Pass for facilitator-led demonstration only; not ready for customer pilot or production; CS acceptance pending.** The v2.1 instruction/knowledge package is materially safer than v2.0 and is suitable for a supervised CS review using labeled fixtures. The complete workflow is not proven: the UI does not run production retrieval and escalation is only recommended, not routed or assigned. This report does not grant CS approval; a named CS owner must record an explicit decision in `COLORBOX_CS_Business_Readiness_v2_1.md`. Conditions before a customer pilot:

1. Backend implements retrieval and strict JSON/schema validation.
2. Frontend removes the wrong-brand SOP/SLA and supports the Colorbox department context.
3. CS approves the P0-P3 test rules, Indonesia assumption, and source register.
4. Multi-turn UI or an external conversation wrapper is provided before production use.
5. The strict-JSON defect is monitored with retries and a schema gate.
6. CS records an explicit accept / accept-with-revisions / reject decision; silence is not acceptance.

The evidence artifacts were produced within an observed window of approximately 52 minutes (15:31–16:23 Asia/Jakarta). Focused work time was not independently tracked, so compliance with the six-focused-hour cap cannot be certified from the available records.

## 10. Evidence index

- `evidence/run_20261109_v2_1/` - 9 main-run requests, responses, summary
- `evidence/run_20261109_v2_1_retest_v03/` - V03 retest
- `evidence/run_20261109_v2_0_before/` - V06 before-case
- `evidence/ui_20261109_v06/` - UI prompt, result notes, screenshot
- `evidence/ui_demos_20261109/` - DEMO-A/B/C prompts, result JSON, screenshots, expected manifest
- `COLORBOX_CS_Demo_Scenarios_v2_1.md` - expected vs actual demo records
- `COLORBOX_CS_Business_Readiness_v2_1.md` - readiness recommendation and pending CS sign-off
- `COLORBOX_CS_Test_Results_v2_1.csv` - machine-readable scores
- `COLORBOX_CS_V2_Evaluation_Details.json` - per-turn checks and details
- `COLORBOX_CS_V2_Evaluation_Report.md` - evaluator-generated report
- `COLORBOX_CS_Issue_Log_v2_1.md` - defects and blockers
- `COLORBOX_CS_Before_After_v2_1.md` - focused before/after record
- `COLORBOX_CS_Critical_Retest_v2_1.md` - retest record
- `COLORBOX_CS_Frontend_Feedback_v2_1.md` - UI findings
- `COLORBOX_CS_Handoff_v2_1.md` - Backend/CS handoff
