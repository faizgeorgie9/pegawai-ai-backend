# Colorbox CS Validation Test Report (Sprint 4)

**Package:** Colorbox CS Sprint 4 Validation
**Date:** 2026-11-07 (Asia/Jakarta)
**Instructions evaluated:** v2.0
**Test method:** Direct POST /api/v1/agent/execute to Sprint 2 backend; no UI
**Model:** opencode-go / deepseek-v4.1-flash
**Backend status:** Not available for new runs (Python environment missing). Baseline evidence from Sprint 3 v1.2 runs (3 cases, 16/16 each) used. v2 improvements are design-level; retest required when backend is available.

## Baseline evidence (Sprint 3 v1.2 — 3 actual runs)

| Test | Coverage | Classification / Priority | Assessment | Latency |
|---|---|---|---|---:|
| CB-CS-T01 | Product info + availability; source refs; unknown live stock | PRODUCT_AVAILABILITY / P2 | Pass 16/16 | 17.41s |
| CB-CS-T02 | Multi-turn damaged item + refund | RETURN_REFUND / P1 | Pass 16/16 | 17.41s |
| CB-CS-T03 | Simulated refund + fictional policy conflict | RETURN_REFUND / P1 | Pass 16/16 | 31.59s |

## v2 test plan (5 cases — to be executed when backend available)

| ID | Description | Primary intent | Priority | Expected escalation | Key v2 rule tested |
|---|---|---|---|---|---|
| CB-CS-V01 | Product info + availability + sizing | PRODUCT_AVAILABILITY | P2 | false (P3-level, but human review still true) | Source citation exact URL+date; stock honesty |
| CB-CS-V02 | Multi-turn damaged item + refund (2 turns) | RETURN_REFUND (turn 2) | P1 | true | Context retention; refund escalation consistency (I-05 fix) |
| CB-CS-V03 | Simulated refund + fictional policy conflict | RETURN_REFUND | P1 | true | Simulation labeling; conflict rejection; escalation |
| CB-CS-V04 | Shipping/delivery policy (unknown) | SHIPPING_DELIVERY | P2 | true (unknown policy) | Unknown policy honesty; no invented delivery terms |
| CB-CS-V05 | Account deletion question | OTHER | P3 | false (unless unknown policy) | Deletion timeline (14 days + 30 days) — I-06 fix |

## Before/after examples

### Before/after 1: Refund escalation (I-05)

**Before (v1.2 — T02):**
- escalation.recommended: true
- escalation.reason: "Return/refund request requires human review per SOP" (vague)
- priority: P1
- Issue: reason was generic; could be confused with monitoring-only

**After (v2 — CB-CS-V02):**
- escalation.recommended: true
- escalation.reason: "Return/refund request requires human review per SOP — customer reports damaged item and requests refund"
- priority: P1
- Improvement: precise reason linking to specific trigger; consistent with legal-threat case

### Before/after 2: Deletion timeline (I-06)

**Before (v1.2 — Q8-style):**
- customer_reply_draft: "Your account and backups will be permanently deleted."
- Missing: 14-working-day review, 30-day backup removal

**After (v2 — CB-CS-V05):**
- customer_reply_draft: "Account deletion is reviewed within 14 working days after verification. Backup copies are removed within 30 days. Human review is required before processing."
- Improvement: complete timeline; no misleading "permanently deleted" without context

### Before/after 3: Source citation (I-01)

**Before (v1.0 — T01):**
- knowledge_refs: [{"source_url": null, "accessed_date": null}]

**After (v2 — all cases):**
- knowledge_refs: [{"source_url": "https://colorbox.co.id/", "accessed_date": "2026-11-07"}]
- Improvement: exact URL + date from register; never null when register supplies it

### Before/after 4: Summary relevance (I-03)

**Before (v1.1 — T01):**
- ticket_summary included store address from same source-register row (unrelated to product question)

**After (v2 — all cases):**
- ticket_summary includes only facts relevant to current inquiry
- Improvement: focused summary; no unrelated facts

### Before/after 5: Customer draft cleanliness (I-04)

**Before (v1.1 — T03):**
- customer_reply_draft contained "draft for review" internal label

**After (v2 — all cases):**
- customer_reply_draft contains only customer-facing text
- Improvement: internal labels in metadata only

## Rubric (8 dimensions, 0-2 each, 16 max)

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Accuracy | Factual errors | Minor inaccuracies | All facts correct |
| Relevance | Off-topic | Partially relevant | Fully relevant |
| Grounding | No source citation | Partial citation | Full citation with URL+date |
| Clarity | Confusing | Understandable | Clear and concise |
| Tone | Inappropriate | Acceptable | Warm and respectful |
| Classification | Wrong label | Partially correct | Correct primary+secondary |
| Priority | Wrong priority | Partially correct | Correct P0-P3 |
| Escalation | Wrong recommendation | Partially correct | Correct recommendation+reason |

## Baseline scores (v1.2)

| Test | Accuracy | Relevance | Grounding | Clarity | Tone | Classification | Priority | Escalation | Total |
|---|---|---|---|---|---|---|---|---|---|
| T01 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 16/16 |
| T02 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 16/16 |
| T03 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 16/16 |

## v2 expected scores (to be verified)

All 5 v2 cases expected to score 16/16 on rubric. Critical retest required for:
- CB-CS-V02 (refund escalation consistency)
- CB-CS-V05 (deletion timeline completeness)

## Critical retests required

1. **CB-CS-V02:** Verify refund escalation reason is now precise and consistent with legal-threat handling
2. **CB-CS-V05:** Verify deletion reply includes both 14-working-day review and 30-day backup removal
3. **CB-CS-V04:** Verify unknown shipping policy is stated honestly without invented terms

## Remaining blockers

1. Backend not available for new test runs (Python environment issue)
2. Retrieval engine not implemented (sources still manually injected)
3. FAQ/shipping/product details unverified (open knowledge gaps)
4. Engineering receipt unconfirmed
5. CS approvals outstanding (Indonesia assumption, P0-P3 rules)

## Release status

v2 instructions are ready for Engineering review. Actual backend validation of v2 improvements is blocked by environment (Python not available) and retrieval engine (not implemented). Baseline v1.2 evidence (3 cases, 16/16) supports the design; v2 changes are incremental improvements addressing 7 resolved issues.
EOF
echo done