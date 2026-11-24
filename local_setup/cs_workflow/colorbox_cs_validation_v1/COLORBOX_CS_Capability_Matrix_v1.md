# Colorbox CS Capability Coverage Matrix (Sprint 4 Validation)

**Package:** Colorbox CS Sprint 4 Validation
**Date:** 2026-11-07
**Instructions evaluated:** v2.0 (COLORBOX_CS_Instructions_v2.md)
**Test method:** Direct POST /api/v1/agent/execute to Sprint 2 backend; no UI
**Model:** opencode-go / deepseek-v4.1-flash

## Capability coverage

| # | Capability | Test case | Status |
|---|---|---|---|
| 1 | Intent classification (15 labels) | CB-CS-V01, V02, V03, V04, V05 | Covered |
| 2 | Product/service info drafting | CB-CS-V01 | Covered |
| 3 | Sizing/recommendations | CB-CS-V01 (secondary) | Covered |
| 4 | FAQ/shipping retrieval & grounded drafting | CB-CS-V04 | Covered |
| 5 | Multi-turn complaint context | CB-CS-V02 (2 turns) | Covered |
| 6 | Clarification behavior | CB-CS-V05 | Covered |
| 7 | Changed/new info handling | CB-CS-V02 (turn 2) | Covered |
| 8 | Simulated order/return/refund | CB-CS-V03 | Covered |
| 9 | Unknown policy handling | CB-CS-V04, V05 | Covered |
| 10 | Conflicting knowledge handling | CB-CS-V03 | Covered |
| 11 | Ticket summary fields | All cases | Covered |
| 12 | Priority assignment (P0-P3) | All cases | Covered |
| 13 | Escalation recommendation + reason | All cases | Covered |
| 14 | Source citation (URL + date) | All cases | Covered |
| 15 | Simulation labeling (SIM-) | CB-CS-V03 | Covered |
| 16 | No internal labels in customer draft | All cases | Covered |
| 17 | Account deletion timeline | CB-CS-V05 (if triggered) | Covered |

## Test cases (5)

| ID | Description | Primary intent | Priority | Key behaviors tested |
|---|---|---|---|---|
| CB-CS-V01 | Product info + availability + sizing | PRODUCT_AVAILABILITY | P2 | Grounded product facts, price citation, stock honesty, size chart unknown |
| CB-CS-V02 | Multi-turn damaged item + refund request (2 turns) | RETURN_REFUND (turn 2) | P1 | Context retention, reclassification, escalation |
| CB-CS-V03 | Simulated refund + fictional policy conflict | RETURN_REFUND | P1 | Simulation labeling, conflict rejection, escalation |
| CB-CS-V04 | Shipping/delivery policy question (unknown) | SHIPPING_DELIVERY | P2 | Unknown policy honesty, no invented delivery terms |
| CB-CS-V05 | Account deletion question | OTHER | P3/P2 | Deletion timeline (14 days + 30 days), no "permanently deleted" without timeline |

## Before/after improvement summary (v1.2 -> v2)

| Defect | v1.2 behavior | v2 fix | Expected improvement |
|---|---|---|---|
| Refund marked BUTUH_MONITORING not escalated | T02/T03: escalation.recommended=true but reason vague | Explicit rule: every RETURN_REFUND = escalation.recommended=true, P1 | Consistent escalation |
| Deletion timeline missing | Q8-style: said "permanently deleted" without 14/30 days | Rule: include both timelines when verified | Complete deletion info |
| Source URL null/blank | T01 v1.0: null URLs | Enforced exact URL from register | All refs have URL+date |
| Summary copied unrelated facts | T01 v1.1: copied store address | Relevance rule: only current-inquiry facts | Focused summaries |
| Internal labels in customer draft | T03 v1.1: "draft for review" in draft | Metadata-only rule | Clean customer text |
EOF
echo done