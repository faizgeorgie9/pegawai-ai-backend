# Colorbox CS Issue Log v2.1

**Date:** 2026-11-09  
**Instructions:** `COLORBOX_CS_Instructions_v2_1.md`  
**Evidence:** actual backend runs `run_20261109_v2_1`, `run_20261109_v2_0_before`, `run_20261109_v2_1_retest_v03`, and UI runs `ui_20261109_v06`, `ui_demos_20261109`

## 1. Critical correction from v2.0

| ID | Issue | Severity | Resolution in v2.1 | Evidence |
|---|---|---|---|---|
| I-06 | v2.0 treated "14 working days / 30 days" as verified Colorbox account-deletion policy. The figures came from the unrelated PT AI Top Trends FAQ `F6`. | Critical | Removed the timeline. Section 10 now states the process/timeline are unknown and must be referred for human review. Section 2 limits facts to supplied records. | V06 before/after; UI run |

This is a correction to the v1 issue log, which incorrectly described the 14/30-day timeline as a fix to include. The v1 instruction was the source of the defect.

## 2. Resolved in v2.1

| ID | Issue | Resolution | Evidence |
|---|---|---|---|
| I-01 | Source URLs null/blank despite citing knowledge IDs | All sourced references now carry exact URL and accessed date; `unknown_*` records use `source_ids: []` with null URL/date | 9/9 scored turns; source-register validation |
| I-02 | Ambiguous primary intent when multiple intents present | Primary = strictest-priority intent; V04 is RETURN_REFUND with shipping/fit secondary | V04 16/16 |
| I-03 | Summary copied unrelated facts from a source row | Summaries stay focused on the current inquiry | Manual review; V01/V04/V05 |
| I-04 | Internal draft labels appeared in customer text | Customer draft contains only customer-facing text; internal status is metadata | 9/9 drafts |
| I-05 | Refund/escalation inconsistency | Every RETURN_REFUND and legal threat = P1 + escalation recommended | V02, V03, V04, V06 |
| I-07 | Legal threat handled but refund not | Section 12 consistency rule; all observed cases escalate | V06, V02 |
| N-01 | Exact 14/30 timeline missing from deletion reply | **Reversed:** timeline must not be stated; it is unsourced | V06 before/after |

## 3. New defects found in v2.1

| ID | Issue | Severity | Status | Owner | Notes |
|---|---|---|---|---|---|
| N-01 | Intermittent strict-JSON failure: unescaped literal newlines inside string values | Medium | Open | Backend | 1/9 first-pass turns (V03 T2); retest valid. Enforce JSON mode and schema validation |
| N-02 | UI displays wrong-brand `PT AI TOP TRENDS`, `SOP-CS-AITT`, and `SLA respon < 15 detik` | High | Open | Frontend | Prompt marker suppresses model influence, but operator sees wrong SOP |
| N-03 | UI has no persistent multi-turn conversation; one textarea only | Medium | Open | Frontend | History must be embedded manually |
| N-04 | UI client timeout 180 s is close to observed 158.21 s v2.0 run | Medium | Open | Frontend/Backend | No streaming or progress detail |
| N-05 | UI run placed a negated 14/30 note in `publicly_verified_facts` | Low | Open | Backend/Prompt | Internal only; customer draft clean |
| N-06 | Evidence run used older retrieval shim (top-k=5, no hyphen split) | Low | Mitigated | Test harness | Runner now top-k=8 with hyphen-part tokens; retest used new version |
| N-07 | Strict evaluator false positives: ID tokens treated as shouting; internal threat context treated as customer draft | Low | Fixed | Test harness | ID-aware regex; must-not checks now draft-focused |
| N-08 | V05 expected priority was P2 although missing-item complaint triggers P1 | Low | Fixed | Test corpus | Corpus corrected to P1; model was right |
| N-09 | No automated backend JSON-schema validation | Medium | Open | Backend | Evaluator repairs and scores, production must reject invalid JSON |
| N-10 | Source register has gaps: 5 rows, 1 failed detail capture, several scope-limited | High | Open | CS | FAQ answer text, product detail 429, shipping terms, refund timing, size values |
| N-11 | DEMO-A UI latency 59.79 s, highest of the 4 UI runs and closest to the 180 s timeout | Low | Open | Frontend/Backend | Other UI runs 30.18-36.40 s; add progress/streaming and configurable timeout |

## 4. Carry-over blockers

| ID | Issue | Severity | Status | Owner |
|---|---|---|---|---|
| B-01 | Retrieval engine not implemented; tests inject keyword-shim candidates | High | Open | Backend |
| B-02 | FAQ answer text not extractable/approved | Medium | Open | CS |
| B-03 | Product detail returned HTTP 429; size chart not transcribed | Medium | Open | CS |
| B-04 | Shipping fee/ETA/Click & Collect terms unverified | Medium | Open | CS |
| B-05 | Refund processing time/method not established | Medium | Open | CS |
| B-06 | Indonesia market assumption not approved | Low | Open | CS |
| B-07 | P0-P3 rules not approved as Colorbox SLAs | Low | Open | CS |
| B-08 | Backend schema validation not implemented | Medium | Open | Backend |
| B-09 | Engineering receipt of this package unconfirmed | Low | Open | CS/Backend |
| B-10 | ClickUp handoff and CS sign-off not completed | Low | Open | CS |
| B-11 | No operational escalation route, queue, owner, or ticket assignment | High | Open | CS/Operations/Engineering |

## 5. Severity key

- **Critical:** unsafe customer-facing claim or data exposure.
- **High:** blocks production use or misleads the operator.
- **Medium:** reliability or workflow gap with a workaround.
- **Low:** documentation, test-harness, or minor labeling issue.

## 6. Exit criteria for pilot

1. N-01 closed by JSON mode + schema gate.
2. N-02 closed by Colorbox department/brand configuration.
3. B-01 retrieval implemented and evaluated on the same corpus.
4. CS approves P0-P3, Indonesia assumption, and the source register.
5. Multi-turn UI or wrapper available.
6. Repeat run with no critical/high open defects.
7. CS reviews DEMO-A/B/C and records an explicit accept / accept-with-revisions / reject decision.
8. Implement and verify an escalation route; `recommendation_only` is not a completed handoff.
