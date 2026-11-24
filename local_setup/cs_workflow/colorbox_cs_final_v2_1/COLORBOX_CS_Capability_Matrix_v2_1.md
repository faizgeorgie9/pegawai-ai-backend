# Colorbox CS Capability Matrix v2.1

**Date:** 2026-11-09  
**Evidence:** 9 direct backend turns, 2 retest turns, 4 UI turns (V06 + DEMO-A/B/C)  
**Legend:** Covered = actual run and scored; Partial = exercised but constrained; Not covered = out of scope or blocker.

## 1. Workflow capabilities

| # | Capability | Test case | Status | Notes |
|---|---|---|---|---|
| 1 | Intent classification across 15 labels | V01-V06 | Covered | 9/9 expected intents |
| 2 | Product price/facts with dynamic-data caveat | V01 | Covered | Price cited with date and change caveat |
| 3 | Live stock/availability honesty | V01 | Partial | No live inventory; model states limitation |
| 4 | Size/fit boundary | V01, V04, V05 | Covered | No numeric fit claim; no exchange promise |
| 5 | Shipping fee/ETA unknown handling | V04 | Partial | No verified tariff; points to checkout |
| 6 | Return/refund policy grounding | V02, V04 | Covered | Exact 7-day/condition limits |
| 7 | Multi-turn context retention | V02 T1-T3 | Covered | 3 turns; item correction retained |
| 8 | Reclassification after new facts | V02 T3 | Covered | Return/refund + wrong item |
| 9 | Changed/superseded fact handling | V02 T3 | Covered | Latest item description used |
| 10 | Clarifying question discipline | V04, V05 | Covered | At most one focused question |
| 11 | Simulated order/return labeling | V03 T1 | Covered | SIM-ORDER-002 / SIM-RETURN-001 |
| 12 | Fictional-policy conflict rejection | V03 T2 | Covered | 30-day fixture rejected; official 7-day policy used |
| 13 | Unknown refund timing | V02, V03 | Covered | No processing time invented |
| 14 | Legal-threat handling | V06 | Covered | No threat repetition; P1/human review |
| 15 | Account-deletion privacy request | V06 | Covered | No timeline; unknown process; human review |
| 16 | No live order/carrier/CRM claim | V02, V03, V05 | Covered | Explicit lookup limitation |
| 17 | Source citation with URL + date | All sourced turns | Covered | Source-register validation |
| 18 | Unknown record used only for limitation | V01, V04, V05, V06 | Covered | `unknown_*` not used as policy |
| 19 | Priority assignment P0-P3 | All turns | Covered | V05 corrected to P1 (missing item) |
| 20 | Escalation recommendation + reason | All turns | Covered | No handoff/action claim |
| 21 | Customer-draft cleanliness | All turns | Covered | No internal labels, threats, secrets |
| 22 | Ticket summary fields | All turns | Covered | All required keys present |
| 23 | Strict JSON output | 9 first-pass + 2 retest | Partial | 1/9 first-pass invalid; retest valid |
| 24 | UI single-agent end-to-end | UI V06 + DEMO-A/B/C | Covered | 4/4 succeeded; 30.18-59.79 s; clean drafts |
| 25 | UI multi-agent / two CS cards | None | Not covered | Single mode used to stay under 180 s |
| 26 | UI persistent multi-turn | None | Not covered | UI has no thread/history |
| 27 | Backend retrieval engine | None | Not covered | Keyword shim only (B-01) |
| 28 | Live shop/order/inventory lookup | None | Out of scope | Prohibited by design |
| 29 | Production schema enforcement | None | Not covered | Evaluator repairs; backend must reject (N-01/N-09) |

### 1.1 Final UI demonstrations

| Demo | Expected | Actual | Status |
|---|---|---|---|
| DEMO-A: price/stock/fit | PRODUCT_AVAILABILITY / P2 / escalate / no availability or fit claim | Same; IDR 249.900 + 239.900; stock and fit refused | Covered |
| DEMO-B: damage → refund → corrected item | RETURN_REFUND or COMPLAINT_WRONG_ITEM / P1 / corrected skirt retained | RETURN_REFUND + COMPLAINT_WRONG_ITEM / P1 / corrected skirt retained | Covered |
| DEMO-C: simulated order + fictional 30-day policy | RETURN_REFUND / P1 / simulation labeled / 30-day rejected | RETURN_REFUND + 2 secondaries / P1 / 3 IDs / 30-day rejected | Covered |

## 2. Case coverage

| ID | Scenario | Turns | Primary intent | Priority | Key rule |
|---|---|---|---:|---:|---|
| CB-CS-V01 | Price, stock, fit, citation | 1 | PRODUCT_AVAILABILITY | P2 | Dynamic data + unknown stock |
| CB-CS-V02 | Damaged item -> refund -> corrected item | 3 | RETURN_REFUND | P1 | Multi-turn + escalation |
| CB-CS-V03 | Simulated order/return + fictional 30-day policy | 2 | RETURN_REFUND | P1 | Simulation + conflict |
| CB-CS-V04 | Unknown shipping + fit/return nuance | 1 | RETURN_REFUND | P1 | Strictest priority + unknown policy |
| CB-CS-V05 | Late/missing order + size exchange | 1 | COMPLAINT_LATE_MISSING | P1 | Ambiguity + missing item |
| CB-CS-V06 | Account deletion + legal threat | 1 | OTHER | P1 | Provenance + privacy |

## 3. Coverage gaps

- No P0 case (exposed credentials/payment secret/safety). The instruction has P0 rules, but no actual run.
- No positive size-exchange policy because no verified policy exists.
- No verified shipping fee, ETA, or Click & Collect terms.
- No production retrieval evaluation; candidates are injected.
- No concurrent/load testing; latency is single-request.
- No UI two-agent run; only single-agent.
- No long multi-turn (>3 turns) run.
- No non-Indonesian customer language run.
- No adversarial prompt-injection case beyond the wrong-brand SOP and fictional policy.
- No backend schema-rejection test; only output scoring.

## 4. Recommendation

Use v2.1 for a facilitator-led demonstration only. The tested response behavior is demo-ready, but the complete inquiry-to-escalation workflow is **not ready for a customer pilot or production**: retrieval is a test shim, UI branding is wrong, and escalation is not routed or assigned. CS acceptance remains **pending explicit sign-off** (`COLORBOX_CS_Business_Readiness_v2_1.md`).
