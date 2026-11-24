# Colorbox CS Complaint, Context & Escalation v1

**Version:** 1.0 (split deliverable from CS Sprint 3 v1.2)
**Prepared:** 2026-11-07
**Owner:** CS (business rules/quality); Backend (implementation)
**Source package:** COLORBOX_CS_Sprint3_Package

## 1. Purpose

Define multi-turn complaint handling, retained context, clarification, escalation triggers/reasons, priority, and the labeled dummy order/return/refund dataset. Escalation is an internal recommendation only - never a live support action, case assignment, or customer message.

## 2. Multi-turn complaint context

Retain only same-session, relevant customer-provided facts:
- Issue description
- Item/product involved
- Dates (purchase, delivery, complaint)
- Customer-provided order reference (NOT proof of an order)
- Requested outcome
- Answers to clarifying questions

Mark each fact as: customer_reported, publicly_verified, or unknown.

Rules:
- Reclassify if the issue changes (e.g., sizing question becomes damaged-product complaint). Preserve relevant prior context. Update priority/escalation.
- On conflicting descriptions: ask one clarification. If still unresolved, stop guessing and recommend human review.
- Never claim a complaint was independently verified.

## 3. Escalation triggers

Set escalation.recommended = true for:
- P0/P1 priority cases
- Required live lookup (order, carrier, inventory, address, cart, delivery fee/date, store availability)
- Material source conflict or missing policy
- Unresolved ambiguity after clarification
- Explicit customer request for human
- Return/refund decision
- Damaged/wrong/missing-item complaint
- Reported exposed credentials/payment secret or safety concern

handoff_status is always "recommendation_only". Never say a case has been escalated, assigned, processed, or resolved.

## 4. Escalation reason (one precise reason)

Examples:
- "Return/refund request requires human review per SOP"
- "Reported payment secret exposure - urgent review"
- "Conflicting sources on shipping policy - cannot resolve"
- "Customer explicitly requested human agent"
- "Unresolved ambiguity after clarification"

## 5. Priority rules (test rules, not SLA)

| Priority | Trigger | Required action |
|---|---|---|
| P0 | Exposed credentials/payment secret, suspected compromise, safety concern | Do not repeat sensitive values; remind customer not to share passwords/OTP/card/CVV/PIN; recommend urgent human review |
| P1 | Return/refund, damaged/wrong/missing complaint, unresolved/conflicting policy, repeated failed clarification, explicit human request | Summarize neutral facts; recommend human review; no outcome promise |
| P2 | Depends on live order/carrier/inventory/address/cart/delivery fee/date/store availability | State lookup limitation; point to official self-service page if verified; recommend human review if unresolved |
| P3 | General product/FAQ answerable from approved public knowledge | Draft concise grounded reply; human review still required |

Do not communicate priority labels as customer promises.

## 6. Dummy order/return/refund dataset

Fixtures with IDs beginning SIM- are fabricated. Rules:
- is_simulated must be true in output
- Include scenario ID in output
- Say "the supplied simulation fixture says..." when describing fixture values
- Never state or imply a fixture was looked up in Colorbox systems
- Dummy policy is not real policy and must never override verified public policy
- Never imply refund approval, shipment status, or transaction execution

Example scenario IDs: SIM-ORDER-001, SIM-RETURN-001, SIM-REFUND-001 (see COLORBOX_CS_Dummy_Scenarios_v1.json for full dataset).

## 7. Ticket summary fields (from output schema)

| Field | Type | Notes |
|---|---|---|
| issue | string | Neutral short summary |
| customer_reported_facts | array | Facts the customer stated |
| publicly_verified_facts | array | Facts verified from public sources |
| unknowns | array | What cannot be confirmed |
| customer_provided_references | array | Order refs, etc. (not proof) |
| requested_outcome | string | What the customer wants |
| context_retained | array | Relevant prior-turn facts |

## 8. Structured expected handoff examples

### Example - Contextual complaint (P1)
Input turn 1: "Paket saya rusak saat datang"
Input turn 2: "Nomor order saya CB-12345, mau refund"
Expected output:
- primary_intent: COMPLAINT_DAMAGED (turn 1) -> RETURN_REFUND (turn 2, stricter)
- priority: P1
- context_retained: ["damaged package reported", "order ref CB-12345 (customer-reported, unverified)"]
- escalation.recommended: true, reason: "Return/refund request requires human review per SOP"
- customer_reply_draft: acknowledges damage, states no refund decision can be made here, recommends human review

### Example - Dummy refund scenario (P1, simulated)
Input: "Saya mau refund untuk pembayaran bulan ini" with SIM-REFUND-001 fixture
Expected output:
- simulation.is_simulated: true, scenario_ids: ["SIM-REFUND-001"]
- customer_reply_draft: references "the supplied simulation fixture says..." for fixture values
- escalation.recommended: true

## 9. Test coverage

Shared with Sprint 3 corpus. Context/escalation behavior assessed in 3 direct backend cases. Blockers: no live lookup (by design); dummy data must stay unmistakably labeled.

## 10. Handoff to Backend

- Implement context retention across turns (same session)
- Implement escalation as recommendation_only (never actual assignment)
- Enforce simulation.is_simulated = true for SIM-* fixtures
- Never expose internal status labels in customer_reply_draft
EOF
echo done