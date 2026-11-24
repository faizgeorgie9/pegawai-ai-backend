# Colorbox CS Classification, Priority & Summary v1

**Version:** 1.0 (split deliverable from CS Sprint 3 v1.2)
**Prepared:** 2026-11-07
**Owner:** CS (business rules/quality); Engineers (implementation)
**Source package:** COLORBOX_CS_Sprint3_Package

## 1. Purpose

Define intent labels, required inputs, ambiguity/clarification behavior, priority rules, and ticket summary fields for the Colorbox CS workflow. Engineers implement; CS assesses quality.

## 2. Intent labels

Choose one primary_intent and zero or more secondary_intents:

PRODUCT_INFO, PRODUCT_AVAILABILITY, SIZE_FIT, SHIPPING_DELIVERY, CLICK_COLLECT, ORDER_PROCESS, ORDER_STATUS, COMPLAINT_DAMAGED, COMPLAINT_WRONG_ITEM, COMPLAINT_LATE_MISSING, RETURN_REFUND, PAYMENT, WEBSITE_TECHNICAL, OTHER, AMBIGUOUS.

Multi-intent rule: assign primary to the intent with the strictest handling priority (P0 before P1 before P2 before P3); record others as secondary. If priorities tie, choose the customer's main requested outcome. If competing interpretations would change the answer and cannot be resolved, use AMBIGUOUS and ask one focused clarification.

## 3. Classification rules

- classification_confidence: 0.0-1.0
- When multiple intents present, primary = strictest priority
- AMBIGUOUS when intent unclear and would change the answer
- At most one clarifying question per turn for missing info needed to proceed

## 4. Priority & summary matrix

| Priority | Trigger | Required action | Summary emphasis |
|---|---|---|---|
| P0 | Exposed credentials/payment secret, compromise, safety | Do not repeat secrets; remind not to share; urgent human review | Flag security concern; no secret values in summary |
| P1 | Return/refund, damaged/wrong/missing complaint, unresolved/conflicting policy, repeated failed clarification, explicit human request | Summarize neutral facts; recommend human review; no outcome promise | Neutral facts + escalation reason |
| P2 | Depends on live order/carrier/inventory/address/cart/delivery fee/date/store availability | State lookup limitation; point to official self-service if verified; recommend human review if unresolved | List unknowns requiring lookup |
| P3 | General product/FAQ answerable from approved public knowledge | Draft concise grounded reply; human review still required | Verified facts + source refs |

## 5. Required inputs by intent (examples)

| Intent | Required input | Missing-data handling |
|---|---|---|
| PRODUCT_INFO | Product name/SKU | Ask which product if ambiguous |
| SIZE_FIT | Product + body measurements or size chart ref | Ask for measurements; cite size chart if verified |
| SHIPPING_DELIVERY | Destination + item | State delivery unknown without verified policy; recommend official page |
| ORDER_STATUS | Order reference | State no live lookup; recommend self-service page |
| RETURN_REFUND | Reason + item condition | Escalate to human; no outcome promise |
| COMPLAINT_DAMAGED | Damage description + item | Acknowledge; do not verify; escalate |

## 6. Ticket summary fields

| Field | Type | Required | Notes |
|---|---|---|---|
| issue | string | yes | Neutral short summary |
| customer_reported_facts | string[] | yes | Facts the customer stated |
| publicly_verified_facts | string[] | yes | Facts verified from public sources |
| unknowns | string[] | yes | What cannot be confirmed |
| customer_provided_references | string[] | yes | Order refs, etc. (not proof) |
| requested_outcome | string | yes | What the customer wants |
| context_retained | string[] | yes | Relevant prior-turn facts |

## 7. Structured examples

### Example 1 - Product info (P3)
Input: "Berapa harga paket Bisnis?"
Output:
- primary_intent: PRODUCT_INFO
- priority: P3
- classification_confidence: 0.95
- customer_reply_draft: grounded price + contents + source + date + review note
- ticket_summary.issue: "Customer asks Business plan price and contents"
- escalation.recommended: false (P3 general question, but human_review_required still true)

### Example 2 - Return/refund (P1)
Input: "Saya mau refund untuk pembayaran bulan ini"
Output:
- primary_intent: RETURN_REFUND
- priority: P1
- escalation.recommended: true, reason: "Return/refund request requires human review per SOP"

### Example 3 - Ambiguous (clarification)
Input: "Mau tanya soal produk" (no product specified)
Output:
- primary_intent: AMBIGUOUS
- clarifying_question: "Produk mana yang ingin Anda tanyakan?"
- priority: P3 (default until clarified)

## 8. Test coverage

Shared with Sprint 3 corpus (3 direct backend cases). Classification/summary/priority assessed at 16/16 on manual rubric. Blockers: no retrieval engine; assessments are manual, not automated.

## 9. Handoff to Backend & Frontend

- Implement intent labels as enum (15 values)
- Implement priority rules as test rules (not SLA)
- Enforce ticket_summary fields (7 required keys)
- Frontend: display classification + priority + escalation recommendation as internal metadata only (never in customer reply)

Blockers: none new; inherits from Sprint 3 package.
EOF
echo done