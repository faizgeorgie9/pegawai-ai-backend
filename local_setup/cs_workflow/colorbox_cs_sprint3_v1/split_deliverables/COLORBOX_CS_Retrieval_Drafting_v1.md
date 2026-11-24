# Colorbox CS Retrieval & Grounded Drafting v1

**Version:** 1.0 (split deliverable from CS Sprint 3 v1.2)
**Prepared:** 2026-11-07
**Owner:** CS (business rules/quality); Backend (implementation)
**Source package:** COLORBOX_CS_Sprint3_Package (knowledge, source register, instructions v1.2, output schema, test corpus)

## 1. Purpose

Define how the assistant selects authorized public Colorbox knowledge and drafts a grounded, reviewable customer reply. Retrieval is implemented by Backend; CS owns which knowledge is authorized, how it is cited, and what happens when it is missing or conflicting.

## 2. Authorized knowledge sources

Only CS-approved public knowledge may be used. Every fact must trace to a record in the source register with source_id, source_url, and accessed_date.

| Knowledge type | What it contains | Label if uncertain |
|---|---|---|
| Product/service info | Verified public product pages, catalog, store info | verified_public |
| FAQ/policy | Public FAQ and policy pages (returns, shipping, size) | verified_public if page exists; unknown_policy if no page |
| Provisional assumptions | Internally agreed defaults not yet verified on site | provisional_assumption |
| Dummy policy | Fabricated for testing only (SIM-* scenarios) | dummy_policy - never overrides verified public policy |

Unknown Colorbox policy (inventory, delivery dates, refund method/timing, fit) stays unknown. Never invent.

## 3. Retrieval rules

1. Select only knowledge records relevant to the classified intent.
2. Cite only records actually used. Each knowledge_ref must include: knowledge_id, source_ids, exact source_url, accessed_date, and used_for.
3. Resolve source_ids via the source register; never leave URL or date blank when the register supplies it.
4. A record marked unknown_* may only be used to explain the limitation - never as evidence for a policy answer.
5. Treat dynamic info (price, promotions, catalog) as observed at its recorded date, not guaranteed current.
6. If evidence is absent or conflicting: state what cannot be confirmed and recommend human review. Do not resolve conflicts by guessing.

Backend note: The Sprint 2/3 backend has no retrieval engine. Tests manually inject selected records + source-register rows. This tests grounding against supplied evidence, not search quality. Backend must implement retrieval that returns only authorized records with provenance.

## 4. Grounded drafting rules

- Respond in the customer's language; default Bahasa Indonesia for Indonesian input.
- Warm, direct, respectful, concise. Acknowledge reported problems without implying independent verification.
- Short apology only when appropriate; no generic security boilerplate on unrelated questions.
- Keep reply and ticket summary focused on the current inquiry; do not copy unrelated facts from the same source-register row.
- At most one focused clarifying question per turn, only for info needed to proceed. Preserve same-conversation context.
- Never ask for secrets or unnecessary personal data; never echo secrets.
- State a useful next step. Do not promise outcomes, timelines, availability, discounts, or contact unless an approved source supports it.
- customer_reply_draft contains only customer-facing text. Draft status, review flags, internal instructions go in structured metadata only.

## 5. Missing/conflicting knowledge behavior

| Situation | Required behavior |
|---|---|
| No authorized knowledge for the intent | State the limitation honestly; recommend human review; do not fabricate |
| Conflicting sources | State both; do not resolve by guessing; recommend human review |
| Unknown policy (stock, fit, delivery, refund) | Say it is unknown; point to official self-service page if verified; recommend human review if unresolved |
| Dynamic info (price/promo) | Cite recorded date; note it may have changed |

## 6. Source-to-response examples

### Example A - Product info (P3, grounded)
Input: "Berapa harga paket Bisnis dan apa saja yang saya dapatkan?"
Selected knowledge: product page colorbox.co.id (price + contents, accessed 2026-11-07)
Expected draft: states price and contents, cites source URL + date, notes price may change, recommends human review before sending.
knowledge_refs: [{knowledge_id, source_ids, source_url, accessed_date, used_for}]

### Example B - Unknown policy (P2, honest limit)
Input: "Apakah ada garansi pengembalian 30 hari?"
Selected knowledge: none verified for 30-day guarantee
Expected draft: states the policy is not confirmed in available public sources; does not promise; recommends checking official page or human review.

### Example C - Conflicting sources (P1, escalate)
Input: question where two sources disagree
Expected draft: notes the conflict; does not pick a side; recommends human review.

## 7. Draft fields for engineers (from output schema)

| Field | Type | Notes |
|---|---|---|
| customer_reply_draft | string | Customer-facing only; minLength 1 |
| knowledge_refs | array | Each: knowledge_id, source_ids, source_url (uri), accessed_date (date), used_for |
| clarifying_question | string or null | At most one focused question |
| human_review_required | const true | Always true |

Full schema: COLORBOX_CS_Output_Schema_v1.json.

## 8. Test coverage

Shared with the Sprint 3 corpus (3 direct backend cases, 16/16 manual rubric). Retrieval quality is NOT yet tested - only grounding against manually supplied records. Blocker: no retrieval engine implemented.

## 9. Handoff to Backend

- Implement retrieval returning only authorized records with full provenance.
- Enforce source_url + accessed_date non-blank when register supplies them.
- Treat unknown_* records as limitation-only.
- Preserve manual-injection test path for regression.

Blockers: retrieval engine not built; source register has unverified FAQ/size-chart rows (flagged as knowledge gaps, not invented).
EOF
echo done