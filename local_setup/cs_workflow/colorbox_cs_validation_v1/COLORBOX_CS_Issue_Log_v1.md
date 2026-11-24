# Colorbox CS Issue Log (Sprint 4 Validation)

**Package:** Colorbox CS Sprint 4 Validation
**Date:** 2026-11-07
**Instructions:** v2.0
**Source:** Based on Sprint 3 v1.2 test evidence + v2 improvements

## Resolved issues (from Sprint 3)

| ID | Issue | Severity | Resolution in v2 |
|---|---|---|---|
| I-01 | Source URLs returned null/blank despite citing knowledge IDs | High | v2 Section 4 rule 3: enforce exact URL from register |
| I-02 | Mixed product/availability intent: primary selection unclear | Medium | v2 Section 2: highest-priority intent is primary; tie-break by customer's main outcome |
| I-03 | Summary copied unrelated facts from same source-register row | Medium | v2 Section 5: summary focused on current inquiry only |
| I-04 | Internal draft-status wording appeared in customer-facing text | High | v2 Section 1: customer_reply_draft contains only customer text |
| I-05 | Refund cases marked BUTUH_MONITORING, not PERLU_ESKALASI_MANAJEMEN | High | v2 Section 3: every RETURN_REFUND = escalation.recommended=true, P1 |
| I-06 | Deletion reply said "permanently deleted" without 14-day/30-day timelines | Medium | v2 Section 8: include both timelines when verified |
| I-07 | Legal threat escalated correctly but refund not — inconsistent signal | High | v2 Section 10: escalation consistency rule |

## Open issues / blockers

| ID | Issue | Severity | Status | Owner |
|---|---|---|---|---|
| B-01 | Retrieval engine not implemented; sources manually injected in tests | High | Open | Backend |
| B-02 | FAQ answer text not extractable from official FAQ pages | Medium | Open | CS |
| B-03 | Product detail page returned HTTP 429 during review; size chart not transcribed | Medium | Open | CS |
| B-04 | Shipping terms (fee, delivery, Click & Collect) unverified | Medium | Open | CS |
| B-05 | Refund processing time/method not established from public source | Medium | Open | CS |
| B-06 | CS approval of Indonesia market assumption outstanding | Low | Open | CS |
| B-07 | P0-P3 priority rules not approved as Colorbox SLAs | Low | Open | CS |
| B-08 | Backend schema validation not implemented (responses inspected manually) | Medium | Open | Backend |
| B-09 | Engineering receipt of files unconfirmed | Low | Open | CS/Backend |

## New issues found in v2 validation (design-level)

| ID | Issue | Severity | Notes |
|---|---|---|---|
| N-01 | v2 assumes source register has exact URLs; if register is incomplete, citation fails | Medium | Backend must enforce non-blank URL/date from register |
| N-02 | Account deletion timeline (14/30 days) is a verified fact only if source exists; if unknown, must say unknown | Low | v2 Section 8 handles this: include only verified timelines |
| N-03 | Multi-turn context retention not yet tested with actual backend beyond 2 turns | Medium | Need 3+ turn test cases |
| N-04 | No automated schema validation; manual inspection only | Medium | Backend must add JSON schema validation |
EOF
echo done