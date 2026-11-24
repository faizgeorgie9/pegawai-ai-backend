# Colorbox CS Package Index v2.1

**Date:** 2026-11-09 (Asia/Jakarta)  
**Status:** Actual UI demos complete; facilitator-led demonstration only. The complete inquiry-to-escalation workflow is not ready for customer pilot or production. CS sign-off and external handoff are pending.

## 1. Read order

1. `COLORBOX_CS_Business_Readiness_v2_1.md` - explicit readiness decision, limitations, and pending CS sign-off.
2. `COLORBOX_CS_Demo_Scenarios_v2_1.md` - three real UI demos with expected/actual conversation records.
3. `COLORBOX_CS_Validation_Report_v2_1.md` - test results, scores, UI evidence, and recommendation.
4. `COLORBOX_CS_Critical_Retest_v2_1.md` - strict-JSON, V05 priority, and V06 retest records.
5. `COLORBOX_CS_Capability_Matrix_v2_1.md` - actual coverage and gaps.
6. `COLORBOX_CS_Issue_Log_v2_1.md` - open defects and blockers.
7. `COLORBOX_CS_Before_After_v2_1.md` - proof the 14/30-day defect is fixed.
8. `COLORBOX_CS_Frontend_Feedback_v2_1.md` - UI findings.
9. `COLORBOX_CS_Handoff_v2_1.md` - required Backend/CS/Frontend/Operations work.

## 2. Instructions and data

| File | Purpose |
|---|---|
| `COLORBOX_CS_Instructions_v2_1.md` | Current behavior rules and output schema |
| `COLORBOX_CS_Instructions_v2.md` | v2.0 before-case instructions; kept for comparison |
| `COLORBOX_CS_Knowledge_v2.json` | Authorized verified and unknown knowledge records |
| `COLORBOX_CS_Source_Register_v1.csv` | Source IDs, URLs, dates, and limitations |
| `COLORBOX_CS_Dummy_Scenarios_v2.json` | Clearly labeled fictional transaction/policy fixtures |
| `COLORBOX_CS_Test_Corpus_v2.json` | 6 cases / 9 turns and expected behavior |
| `COLORBOX_CS_Test_Results_v2_1.csv` | Machine-readable scores and metadata |
| `COLORBOX_CS_V2_Evaluation_Details.json` | Per-turn checks and parsed outputs |

## 3. Actual execution evidence

| Path | Contents |
|---|---|
| `evidence/run_20261109_v2_1/` | 9 main-run request/response pairs and summary |
| `evidence/run_20261109_v2_1_retest_v03/` | V03 critical JSON retest |
| `evidence/run_20261109_v2_0_before/` | V06 v2.0 before-case |
| `evidence/ui_20261109_v06/` | V06 prompt, notes, result, full-page screenshot |
| `evidence/ui_demos_20261109/` | DEMO-A/B/C actual prompts, result JSON, screenshots, expected manifest |
| `COLORBOX_CS_V2_Evaluation_Report.md` | Evaluator-generated summary |

Each demo was actually submitted through the dashboard. The screenshots and captured result JSON are evidence of UI execution; fixtures and prompt manifests alone are not.

## 4. Scripts

| File | Purpose |
|---|---|
| `run_colorbox_cs_v2_tests.py` | Backend runner, test filters, retrieval shim, JSON recovery |
| `evaluate_colorbox_cs_v2.py` | Eight-dimension scorer, source validation, corpus expectations |
| `generate_ui_demo_prompts.py` | Builds the labeled UI demo prompts and expected manifest |
| `inspect_demo_results.py` | Inspects recorded UI demo results |

## 5. Key numbers and decision

- 6 cases / 9 main turns; 9/9 HTTP 200.
- First-pass rubric: 143/144 (99.3%); 0 critical safety/grounding failures.
- Strict JSON: 8/9 first pass; V03 T2 retest valid in 2/2 turns.
- UI: 4/4 submissions succeeded (V06 + 3 demos), 30.18-59.79 seconds.
- Demos: 3/3 expected primary intent, priority, grounding, and recommendation-only escalation observed.
- v2.0 before-case: 14/30-day account-deletion timeline was fabricated as verified, legal threat repeated, and simulation mislabeled; corrected in v2.1.
- Readiness: facilitator-led demo only. Not ready for customer pilot or production. CS sign-off is pending.
- Evidence timestamps span approximately 52 minutes; focused hours were not tracked, so the six-hour cap cannot be certified.

## 6. Packaging and boundaries

The ZIP is for local/shared-drive handoff; the chat attachment system rejects ZIPs. Attach key reports and the three UI screenshots individually. No live Shopee/Instagram/order/inventory/CRM integration, customer messaging, publishing, transaction, ticket assignment, or authentication was used. Drafts are internal and require human review.
