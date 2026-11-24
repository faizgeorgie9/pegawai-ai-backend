# Colorbox CS Business Readiness Decision v2.1

**Date:** 2026-11-09 (Asia/Jakarta)  
**Scope:** Complete inquiry → classification → retrieval → grounded drafting → summary/priority → escalation prototype  
**Evidence basis:** 6 cases / 9 direct backend turns, 2 critical retest turns, 1 v2.0 before-case, 4 actual UI submissions (V06 + DEMO-A/B/C)  
**Instructions / knowledge:** `COLORBOX_CS_Instructions_v2_1.md` / `COLORBOX_CS_Knowledge_v2.json` (11 records)  
**Execution:** shared backend `http://127.0.0.1:8080/api/v1/agent/execute`, provider `opencode-go`, model `deepseek-v4.1-flash`; UI submissions through `http://127.0.0.1:8080/`

## 1. Decision summary

| Decision layer | Status | Meaning |
|---|---|---|
| **Response/policy behavior on tested fixtures** | **DEMO-READY ONLY** | The tested drafts are grounded and appropriately cautious; this supports a facilitator-led demonstration, not a live customer pilot. |
| **Complete inquiry-to-escalation business readiness** | **NOT READY** | Production retrieval is absent, the UI shows another brand's SOP, and escalation only recommends human review; no queue, ticket, owner, or assignment exists. |
| **CS business acceptance** | **PENDING EXPLICIT SIGN-OFF** | This document does not grant CS approval. A named CS owner must accept, accept with revisions, or reject after the demo review. Until then, business status is **not accepted**. |
| **Production / unattended use** | **NOT READY** | Retrieval, schema enforcement, tenant branding, persistent conversation, audit, and source gaps remain open. |
| **Customer action / live ticket** | **NOT PERFORMED** | Every escalation is `recommendation_only`. No ticket was assigned, no customer was contacted, no refund or order action was taken. |

**Plain answer:** the model behavior can be demonstrated to CS using labeled fixtures, but the complete business workflow is **not ready**. The tested UI does not retrieve knowledge itself or create/assign an escalation. No CS approval is recorded.

## 2. What was actually proven

| Required capability | Actual evidence | Status |
|---|---|---|
| Intent classification | 9/9 direct turns matched expected primary intent; 3/3 demos matched (`PRODUCT_AVAILABILITY` P2; `RETURN_REFUND` P1 twice) | Validated |
| Product and FAQ grounding | DEMO-A cites homepage price/promo with review date and size-listing limits; unknown records used only for limitation | Validated |
| Policy retrieval and grounding | Return/refund answers cite the official 7-day policy with exact URL/date; no fee claim beyond the page | Validated against supplied candidates |
| Live stock / order / delivery lookup | Explicitly refused in V01, V03, V05; no invented status | Honest limitation validated |
| Contextual complaint, multi-turn | V02 T1-T3 retains damage → refund → corrected item; DEMO-B uses the corrected skirt/color, not the earlier top | Validated with embedded history |
| Simulated order/return/refund | V03 and DEMO-C label simulation, list scenario IDs, and refuse live status | Validated for labeled fixtures |
| Unknown and conflicting information | 30-day fictional policy rejected; account deletion and refund timing treated as unknown; V04/V05 limitations stated | Validated |
| Summary and priority | All turns complete schema; 3/3 demos correct priority; V05 P1 after corpus correction | Validated |
| Escalation | 3/3 demos and all P1/P0-sensitive turns recommend human review with reason and `handoff_status: recommendation_only` | Validated as recommendation only |
| Clean customer draft | 0 critical safety/grounding failures; no threat repetition, secret request, fabricated timeline, or refund/stock/fit promise | Validated |
| UI execution | 4/4 UI submissions succeeded in single-agent mode; provider/model displayed correctly | Partial |
| Retrieval engine | Keyword/IDF test-harness shim with injected candidates; production engine absent (B-01) | Not validated |
| Strict JSON contract | 8/9 first pass; one unescaped-newline failure; V03 T2 retest strict-valid 2/2 | Partial |
| Audit / run identity | No production run id, prompt hash, or stored validation result in the backend | Not validated |

### Score and reliability

- Direct suite: **143/144** first-pass rubric (8 dimensions × 0-2 per turn); **0** critical safety/grounding failures.
- V03 strict-JSON retest: **32/32**.
- UI demos: **3/3** expected classification, priority, grounding, and escalation; latencies **59.79 s**, **36.40 s**, **30.33 s**.
- UI V06 account-deletion retest: clean draft, **30.18 s**.
- Actual model executions in the package: **16** (9 main + 2 retest + 1 before + 4 UI).
- No customer message was sent or published.

## 3. Acceptance criteria check

| Criterion | Result | Evidence / caveat |
|---|---|---|
| All requested CS capabilities have actual coverage and priority workflows meet business rules through real UI/Hermes | **Partially met** | 6 cases / 9 turns + 3 demos; retrieval is injected by a test shim and escalation is recommendation-only, not an operational handoff |
| At least five actual Day 3 cases and final critical retests preserved | **Met** | 6 cases, 9 turns, V03 retest, V05 priority correction, V06 before/after |
| Each demo has expected/actual evidence; simulations and unknown policies labeled | **Met** | `COLORBOX_CS_Demo_Scenarios_v2_1.md`; `evidence/ui_demos_20261109/`; DEMO-C simulation IDs listed |
| No unresolved critical main-flow defect or accepted fabricated policy/commitment | **Not met for complete workflow** | No fabricated policy was accepted, but missing retrieval, wrong-brand SOP display, and absent escalation assignment are unresolved main-flow gaps |
| CS acceptance/revisions explicit, not automatic | **Pending** | Section 6 lists revisions; section 7 is the sign-off block; no CS approval exists yet |

## 4. Business strengths

1. **Refuses to invent what it cannot verify.** Stock, fit, shipping, delivery status, refund timing, exchange eligibility, and account deletion are all handled as unknowns with human review.
2. **Provenance is auditable.** Sourced claims carry exact URLs and accessed dates; unknown records carry no source and are used only to explain the limitation.
3. **The critical v2.0 defect is fixed.** The unrelated PT AI Top Trends 14/30-day deletion timeline no longer appears in the customer draft or as a verified fact.
4. **Priority follows the rules.** All refund, wrong-item, missing/late, and legal-threat paths are P1 with a human-review escalation.
5. **Context correction works.** The model supersedes the earlier damaged-top description with the corrected skirt/color and keeps the order reference.
6. **Conflict handling is explicit.** The fictional 30-day policy is rejected rather than averaged with the official 7-day rule.
7. **Drafts are customer-safe.** No threats repeated, no internal labels, no secrets requested, no refund/stock/fit guarantee.

## 5. Weaknesses and limits

1. **Retrieval is not the real product.** Candidates are injected by a documented keyword shim; a production engine may retrieve differently and has not been evaluated.
2. **JSON is not guaranteed.** One first-pass response was not strict JSON; the retest passed but the defect is intermittent and production parsers must not rely on repair.
3. **The UI is a generic harness.** Wrong-brand `PT AI TOP TRENDS` / `SOP-CS-AITT` / `SLA respon < 15 detik` is visible; provider is hardcoded in the payload; no persistent thread; 180 s timeout; raw JSON result.
4. **Public source coverage is incomplete.** FAQ answer text, product-detail measurements, shipping fee/ETA, and refund timing/method are unverified; the Indonesia assumption and P0-P3 rules are not CS-approved.
5. **Escalation is a recommendation, not a workflow.** No queue, owner, SLA, ticket, or assignment exists.
6. **Only single-agent UI was tested.** The two-agent CS mode, P0, >3-turn UI, non-Indonesian language, and load behavior are untested.
7. **Time and handoff controls are incomplete.** Evidence artifacts span about 52 minutes (15:31–16:23 Asia/Jakarta), but focused hours were not tracked; no engineering receipt, ClickUp handoff, or CS signature exists.

## 6. Concrete revisions required

### CS-owned revisions (must be explicit)

| ID | Revision | Acceptance test |
|---|---|---|
| R-01 | Approve P0-P3 as **test rules**, not Colorbox SLAs | Signed rule sheet with examples |
| R-02 | Approve the Indonesia market assumption or state the correct market | Written decision |
| R-03 | Approve the source register; resolve FAQ text, product detail/size chart, shipping terms, refund timing | Updated register with approved URLs/dates |
| R-04 | Confirm account deletion and size exchange are genuinely unknown in public sources, or supply approved sources | Written confirmation or new knowledge record |
| R-05 | Define the human-review queue, owner, and response expectation for P1/P0 | Named owner + queue + SLA |
| R-06 | Approve customer-draft tone and the “internal draft only” rule | Signed tone review of DEMO-A/B/C |
| R-07 | Decide pilot scope: which intents are allowed, which always escalate | Pilot scope note |

### Engineering-owned revisions (block production)

| ID | Revision | Acceptance test |
|---|---|---|
| R-08 | Implement production retrieval over approved knowledge (B-01) | Same corpus returns required IDs, no unapproved record, trace stored |
| R-09 | Enforce strict JSON and schema validation server-side (N-01/N-09) | 10/10 repeated runs parse without repair; invalid output rejected |
| R-10 | Remove wrong-brand SOP/SLA and use active provider in UI (N-02/F-01/F-02) | Colorbox branding, correct SOP/version, provider from server |
| R-11 | Add persistent conversation and raise/configure timeout with progress (N-03/N-04) | 3-turn UI run without manual history; no silent 180 s drop |
| R-12 | Move negated provenance notes out of `publicly_verified_facts`; standardize summary language (N-05) | Field contains only verified facts; summary language consistent |
| R-13 | Store run id, prompt hash, versions, latency, tokens, raw response, validation result | Audit record retrievable for every run |

### Validation-owned revisions

| ID | Revision | Acceptance test |
|---|---|---|
| R-14 | Repeat the full corpus twice on the implemented retrieval path | Two consecutive 9/9 runs with strict JSON |
| R-15 | Add a P0 case, a 5-turn case, and a positive exchange/refund path if CS supplies policy | New cases executed and scored |
| R-16 | Confirm Engineering receipt and make the handoff ticket explicit | Receipt recorded; ticket id stored |

## 7. CS acceptance block (explicit, not automatic)

| Field | Value |
|---|---|
| CS decision | ☐ Accept for supervised pilot  ☐ Accept with revisions  ☐ Not ready |
| CS approver name / role | ______________________________ |
| Date | ______________________________ |
| Scope accepted | ____________________________________________________________ |
| Revisions accepted as pilot conditions | R-01 to R-16 as applicable |
| Signature / note | ____________________________________________________________ |

**Current recorded state:** pending. This package is an engineering validation and readiness recommendation, not a CS approval.

## 8. Recommendation

**Proceed with a facilitator-led CS demonstration and review only; do not start a customer pilot or go live.** Use DEMO-A/B/C as the demonstration set. Reassess business readiness only after retrieval is implemented, the UI is correctly branded, escalation routing is operational, strict JSON/schema validation is enforced, and CS records an explicit decision in section 7.

### Prioritized next-phase R&D

1. **P1 — Retrieval engine + evaluation (R-08/R-14).** Highest risk to answer quality; evaluate on the same 9-turn corpus and the demo set.
2. **P1 — JSON/schema gate (R-09).** Remove parser dependence and give the UI a clear failure state.
3. **P1 — Colorbox tenant configuration (R-10).** Wrong-brand SOP is an operator-trust and compliance risk.
4. **P2 — Persistent multi-turn UI and timeout/progress (R-11).** Required for realistic complaint handling.
5. **P2 — CS source/rule approval (R-01 to R-07).** Converts test rules and unknowns into approved business policy.
6. **P3 — P0 and adversarial coverage (R-15).** Add secret exposure, prompt injection, and 5-turn cases.
7. **P3 — Audit and handoff operations (R-13/R-16).** Make every run reproducible and every escalation assignable.

## 9. Evidence index

- `COLORBOX_CS_Demo_Scenarios_v2_1.md` — 3 demo conversations with expected/actual records.
- `COLORBOX_CS_Validation_Report_v2_1.md` — full test matrix and before/after.
- `COLORBOX_CS_Critical_Retest_v2_1.md` — strict JSON, V05 priority, V06 UI retest.
- `COLORBOX_CS_Capability_Matrix_v2_1.md` — coverage and gaps.
- `COLORBOX_CS_Issue_Log_v2_1.md` — open defects and blockers.
- `COLORBOX_CS_Handoff_v2_1.md` — engineering/CS/frontend work.
- `evidence/ui_demos_20261109/` — prompts, result JSON, screenshots.
- `evidence/run_20261109_v2_1/`, `evidence/run_20261109_v2_1_retest_v03/`, `evidence/run_20261109_v2_0_before/`, `evidence/ui_20261109_v06/`.
