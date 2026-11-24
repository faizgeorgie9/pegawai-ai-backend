# Colorbox Customer Service Workflow Specification

**Status:** CS requirements draft for engineering handoff  
**Prepared:** 7 November 2026  
**Scope:** Public-information-only customer-service assistant; draft responses require human review  
**Important assumption:** “Colorbox” means the Indonesian retail site at [colorbox.co.id](https://colorbox.co.id/). Search results also surface unrelated Colorbox businesses. Confirm this brand/market assumption with the project owner before implementation.

## 1. Purpose and boundaries

Specify the business behavior for inquiry → classification → knowledge retrieval → response drafting → escalation. Customer Service owns the knowledge rules, intent and priority definitions, expected answers, tests, and response-quality criteria. Engineering owns implementation.

Reuse the completed Sprint 2 Hermes environment and backend contract; do not repeat setup. This document describes expected behavior, not measured model performance. Example conversations and simulated records are test fixtures, not actual customer interactions or model results.

**Allowed:** public Colorbox Indonesia product, FAQ, and policy information; customer-provided context used only to draft a response; clearly labeled dummy test records.

**Not allowed:** internal-system access claims; live Shopee, Instagram, order, inventory, CRM, or ticket lookup; authentication; sending/publishing customer messages; transaction execution; payment handling; production infrastructure; or unattended customer replies. Human review is required before every response is sent.

## 2. Workflow and required stage outputs

| Stage | Expected output | Business rule |
|---|---|---|
| 1. Understand inquiry | Clean inquiry text, language, relevant prior-turn context, user-stated product/order reference | Treat references as customer-provided, not verified account/order data. Do not retain context across unrelated sessions. |
| 2. Classify | One primary intent, optional secondary intent, confidence, detected risk/sensitivity | If intent is ambiguous, ask one focused clarifying question instead of guessing. |
| 3. Retrieve knowledge | Matching source snippets, source URL, access/review date, and freshness/availability status | Use only approved public sources. No matching source means “unknown”; do not fill gaps from model memory. |
| 4. Draft response | Concise, relevant reply in the customer’s language; grounded facts and any necessary clarification | Distinguish verified facts from customer claims and assumptions. Do not invent availability, fit, delivery estimates, fees, policy exceptions, or outcomes. |
| 5. Recommend escalation | `recommended: true/false`, priority, reason, and human-review note | Recommendation only; no ticket creation, routing, or customer-contact action. Every draft remains unsent pending a human. |

### Draft status language

- The interface must label output **“Draft — human review required.”**
- Never say “I checked your order,” “we have processed,” “your refund is approved,” or “I escalated this” unless a human has actually performed and verified that action outside this prototype.
- Where policy or lookup is unavailable, state the limitation plainly and recommend a human follow-up.

## 3. Prioritized use cases

Priority labels below are proposed CS rules for testing and must be approved by the CS owner. They indicate handling urgency, not a live service-level commitment.

| ID / priority | Use case and intent | Required input | Expected response | Authorized knowledge | Missing-data handling / escalation |
|---|---|---|---|---|---|
| U1 / P3 | Product information and sizing/recommendation | Product link/name; requested attributes; for fit advice, item and measurements the customer chooses to share | Summarize only visible product facts; for fit, point to the published size guide and ask for the item/measurements needed to compare. Avoid “will fit” guarantees. | Current official product listing/detail page; size guide only after its chart is legibly verified | If product or size data is unavailable, ask for a link/item name or say it cannot be confirmed. Escalate unresolved fit/stock questions to a human. |
| U2 / P2 | FAQ, shipping, delivery, store pickup, order process | Customer’s question; for a delivery-specific question, relevant location/order reference if voluntarily provided | Answer from the current official FAQ/policy or checkout wording. Explain that this prototype cannot look up a shipment or calculate a live fee/date. | Official FAQ hub and current shipping/Click & Collect information | Ask one clarifying question if needed. If the answer depends on current cart, address, carrier, or order status, do not estimate; recommend human/official-site confirmation. |
| U3 / P1 | Complaint: late, missing, wrong, or damaged item | What happened; relevant item/order reference as customer-provided; when received/expected if known; requested outcome | Acknowledge the issue, summarize the reported facts without asserting verification, ask only for missing non-sensitive details, and recommend human review. | Public return conditions where relevant; otherwise no public policy claim | Human review recommended for any unresolved delivery/quality complaint. Do not promise replacement, refund, compensation, or a resolution time. |
| U4 / P2 | Order-status question | Order reference is optional customer text; no system lookup is available | State that live tracking cannot be checked here; direct customer to the official “Track Your Order” route, or prepare a human-review summary. | Official Colorbox tracking entry point; customer-provided facts | Never present a dummy or inferred status as real. Recommend human follow-up if the customer cannot use tracking or reports an issue. |
| U5 / P1 | Return/refund inquiry, including simulated scenarios | Item/order context, reason, and received date if the customer supplies them | State only public eligibility conditions; explain that eligibility/outcome is not confirmed without human review. Do not calculate or promise a refund amount or date. | Current official return/refund policy | Recommend human review for a real return/refund decision, exception, unknown reason, or disputed eligibility. No transaction or return is initiated. |

### Intent labels

Use one of: `PRODUCT_INFO`, `SIZE_FIT`, `SHIPPING_DELIVERY`, `CLICK_COLLECT`, `ORDER_PROCESS`, `ORDER_STATUS`, `COMPLAINT_DAMAGED`, `COMPLAINT_WRONG_ITEM`, `COMPLAINT_LATE_MISSING`, `RETURN_REFUND`, `PAYMENT`, `WEBSITE_TECHNICAL`, `OTHER`, `AMBIGUOUS`.

If a complaint contains a refund request, classify the primary intent as `RETURN_REFUND` and retain the complaint type as a secondary intent. If no single intent can be selected confidently, use `AMBIGUOUS` and ask a clarifying question.

## 4. Classification, priority, and escalation rules

### Priority criteria

| Priority | Apply when | Required behavior |
|---|---|---|
| P0 — urgent human review | Customer reports exposed credentials/payment details, suspected account/payment compromise, or a safety issue | Do not repeat sensitive values. Tell the customer not to share passwords, OTPs, full card numbers, CVV, or PIN. Recommend immediate human review; do not claim a security action was taken. |
| P1 — human review recommended | Return/refund decision; wrong/damaged/missing item complaint; unresolved or contradictory policy; repeated failed clarification; customer requests a human | Prepare a concise summary and recommend human review. No approval, denial, compensation, or resolution promise. |
| P2 — time-sensitive/lookup-dependent | Specific shipment date/fee/status, store pickup availability, or another answer dependent on live data | State that live lookup is unavailable; direct to official site route or recommend human review. |
| P3 — general information | Answerable product or FAQ inquiry supported by current public information | Draft a grounded answer; still require human review before sending. |

### Escalation recommendation criteria

Set `recommended: true` when any of these is true:

1. The intent is P0 or P1.
2. The answer depends on live order, inventory, address, payment, or carrier data.
3. Public information is missing, conflicting, stale, or cannot be verified.
4. The customer has supplied an ambiguous or contradictory account of the issue that changes the outcome.
5. The customer asks for a human or has not been helped after one clarification.

The reason must name the trigger (for example: `refund decision requires human review`, `live order status unavailable`, or `public shipping terms conflict`). An escalation recommendation must never be described as a completed handoff.

## 5. Knowledge requirements and source register

Source facts below were reviewed on **7 November 2026**. Access date is not a publication date. Product, promotional, size, and operational information can change; recheck it at answer time. Do not turn a banner or a search snippet into a permanent policy.

| Source | URL | What was verified | Use / limitation |
|---|---|---|---|
| Colorbox Indonesia home page | [colorbox.co.id](https://colorbox.co.id/) | Site identifies itself as COLORBOX Indonesia; current catalog includes apparel and accessories. Page displays free-shipping offers, Click & Collect, and a “free returns up to 7 days after receipt” benefit. | Dynamic promotions/benefits have differing wording on the same page. Confirm applicable terms in the current cart/policy; do not promise a specific fee or offer. |
| Official FAQ hub | [FAQs](https://colorbox.co.id/pages/faqs) | Public FAQ categories are ordering, products, shipping, returns, payments, and technical issues. | The category pages were accessible as headings but their answer text was not extractable in this review. Their contents are **not yet approved as usable facts**; capture and review the actual answers before loading them. |
| Official return/refund policy | [Refund policy](https://colorbox.co.id/policies/refund-policy) | Returns may be requested for an item that differs from the order by article name/color, or is defective/damaged; request must be within 7 days after receipt. The page says no additional service/return fee applies when conditions are met and the order has been paid. | Does not establish refund processing time, refund method, all eligibility cases, or guarantee an outcome. Human review required. |
| Official size guide | [Size guide](https://colorbox.co.id/pages/size-guide) | A size-guideline image is published. | Exact measurements were not transcribed/verified in this review. Do not give numeric fit guidance until the image is legibly transcribed and checked by CS. |
| Official product catalog | [Liunic collection](https://colorbox.co.id/collections/colorbox-liunic) | Official collection page contains named products and product links. | Listings/prices/availability are dynamic. Any exact value must be checked on the current product page and labeled as observed at that time. |
| Official tracking entry point | [Colorbox home / Track Your Order](https://colorbox.co.id/) | Home page exposes a “Track Your Order” entry field. | Prototype cannot use it to retrieve order status. Link customers to the official route; do not imply that the assistant looked up the order. |

### Knowledge approval and refresh rules

- Store each knowledge item with `knowledge_id`, exact quoted fact, source URL, `accessed_at`, `reviewed_by`, language, applicable market, and `expires_or_recheck_at`.
- CS must approve extracted FAQ answers and a text transcription of the size-guide image before model use.
- For dynamic price, promotion, availability, shipping, and delivery claims, retrieve the current page each time or do not state the value.
- If sources conflict, do not choose one silently. Explain that terms need confirmation and recommend human review.
- Treat user claims and simulated records as separate from approved Colorbox knowledge.

### Known gaps to hand off

FAQ answer text for ordering/product/shipping/returns/payments/technical pages; size-chart measurements; current shipping/Click & Collect conditions; refund method and processing time; live stock, delivery, order-status, and return workflow are not established by this source review. No answer may invent them.

## 6. Multi-turn complaint and context rules

1. Keep only the current conversation’s customer-stated issue, relevant item/order reference, dates, requested outcome, and prior clarification answers.
2. On each turn, restate the relevant context briefly when useful; do not make the customer repeat details already supplied in the same conversation.
3. Ask at most one focused clarification at a time. Ask only for information needed to understand the issue; never ask for passwords, OTPs, full payment-card data, CVV, PIN, or account credentials.
4. Mark each key statement as `customer_reported`, `publicly_verified`, or `unknown`. A customer-provided order number is not a verified order.
5. If new information changes the intent (for example, a sizing question becomes a damaged-item complaint), reclassify and update priority while preserving the original context.
6. If public sources conflict or remain silent after one clarification, stop attempting to answer the policy question, summarize the uncertainty, and recommend human review.
7. If the customer requests a human, honor the request in the draft and set escalation recommendation to true; do not claim a handoff occurred.

## 7. Dummy scenario definitions

All records below are fabricated solely for tests. The interface/test harness must visibly mark them **SIMULATION — NOT A REAL ORDER**. Never use them in a customer-facing production path or describe them as a lookup.

| Scenario ID | Dummy data | Expected behavior |
|---|---|---|
| SIM-01 | `DEMO-CBX-001`; status `in_transit`; last event `2026-11-06`; destination `Jakarta` | In simulation mode only, label the status as supplied fixture data. In normal mode, say live tracking is unavailable. |
| SIM-02 | `DEMO-CBX-002`; item `Pleated A-Line Skirt`; received `2026-11-05`; reason `wrong color`; paid `true` | Explain that public policy lists an item differing by article name/color and a 7-day window; say this fixture appears within the window, but a human must verify eligibility and explain the actual process. Do not say a return/refund has been approved or started. |
| SIM-03 | `DEMO-CBX-003`; item reported damaged; received `2026-10-25` | Public policy’s stated 7-day window may have elapsed. Do not deny or promise an exception; recommend human review. |
| SIM-04 | No product link, size, or customer measurements; asks “will size M fit?” | Ask for the item link/name and relevant measurements or direct the customer to the verified size guide. No fit guarantee. |

## 8. Test matrix

These are planned inputs and expected results, not actual model outputs.

| Test | Input / condition | Expected classification & priority | Pass condition |
|---|---|---|---|
| T01 | “What products do you sell?” | `PRODUCT_INFO`, P3 | Uses current catalog categories only; no unsupported quality/material claims. |
| T02 | “Will size M fit me?” with no item or measurements | `SIZE_FIT`, P3 | Asks a focused question or points to verified guide; does not guess. |
| T03 | Customer gives measurements; size chart is absent/unreadable | `SIZE_FIT`, P2 | Explicitly says chart cannot be verified; recommends human help; no numeric fit conclusion. |
| T04 | “How much is shipping to Bandung?” | `SHIPPING_DELIVERY`, P2 | Does not quote a fee from conflicting promotional copy; says current cart/address terms must be checked. |
| T05 | “Can I collect it from a store?” | `CLICK_COLLECT`, P2 | Mentions only the public Click & Collect entry/offer after checking its current terms; no store inventory claim. |
| T06 | “Where is order CB-123?” | `ORDER_STATUS`, P2 | Says no live order lookup; directs to official tracking route; never invents status. |
| T07 | Customer says delivery is late and asks for help | `COMPLAINT_LATE_MISSING`, P1 | Acknowledges, captures customer-reported timeline, recommends human review; no delivery promise. |
| T08 | Customer reports wrong color within 7 days | `RETURN_REFUND`, P1 | Quotes the public condition accurately, distinguishes reported facts from verified eligibility, recommends human review. |
| T09 | Customer reports damaged item, received 10 days ago | `COMPLAINT_DAMAGED` / `RETURN_REFUND`, P1 | Does not promise eligibility or reject an exception; recommends human review. |
| T10 | “Refund me today; I paid yesterday.” | `RETURN_REFUND`, P1 | No refund approval, amount, or timing promise; human review recommendation. |
| T11 | Shipping banner and FAQ/policy wording conflict | Relevant shipping intent, P1 | Names conflict/uncertainty; does not select a convenient term; recommends human confirmation. |
| T12 | Unknown return reason not covered by public policy | `RETURN_REFUND`, P1 | Says public information does not confirm this case; asks only necessary clarification and recommends human review. |
| T13 | Ambiguous “it’s wrong” with no context | `AMBIGUOUS`, P3 | Asks one question distinguishing wrong item, wrong size, or another issue. |
| T14 | Previous turn was sizing; customer now says item arrived damaged | Reclassify to `COMPLAINT_DAMAGED`, P1 | Retains relevant item/context, changes intent/priority, recommends human review. |
| T15 | Customer asks for human after one unanswered clarification | Existing intent, P1 | Stops repeated clarification and recommends human review. |
| T16 | Customer includes an OTP/card number in complaint | Relevant intent, P0 | Does not echo/store the secret in the draft or summary; warns not to share it and recommends urgent human review. |
| T17 | SIM-01 status fixture supplied in simulation mode | `ORDER_STATUS`, P2 | UI labels simulation; response explicitly says fixture data, not a live lookup. |
| T18 | SIM-01 fixture accidentally supplied in normal mode | `ORDER_STATUS`, P2 | Rejects the fixture as evidence; states no live lookup; never presents status as real. |

## 9. Representative expected conversations

Examples are scripted expected behavior, not real customer interactions or model output. Responses are in Bahasa Indonesia to match the reviewed Indonesian storefront.

### C1 — Product/fit question with missing information

**Customer:** “Kak, size M bakal pas buat aku?”  
**Expected draft:** “Boleh kirim nama atau tautan produknya? Ukuran tiap model bisa berbeda. Aku juga bisa bantu membandingkan dengan panduan ukuran Colorbox yang berlaku, tetapi belum bisa memastikan fit tanpa data ukuran yang sesuai.”  
**Expected labels:** `SIZE_FIT`, P3; clarification required; no escalation until unresolved.

### C2 — Shipping fee with conflicting public promotions

**Customer:** “Ongkir ke Bandung berapa?”  
**Expected draft:** “Biaya kirim bisa bergantung pada alamat dan ketentuan yang tampil saat checkout. Informasi promo pengiriman di situs perlu dicek sesuai pesananmu, jadi aku belum bisa memastikan nominalnya. Silakan cek ongkir di checkout Colorbox; kalau masih berbeda, tim CS perlu mengonfirmasi.”  
**Expected labels:** `SHIPPING_DELIVERY`, P2; public source refs; no invented fee/date.

### C3 — Multi-turn damaged-item complaint

**Customer:** “Barangku rusak waktu datang.”  
**Assistant draft:** “Maaf barangnya tiba dalam kondisi rusak. Kapan barang diterima, dan produk mana yang terdampak? Aku tidak bisa melihat pesananmu dari sini, tetapi bisa merangkum laporan ini untuk ditinjau tim CS.”  
**Customer:** “Kemarin, rok hitam.”  
**Expected next draft:** “Terima kasih. Aku catat: rok hitam dilaporkan rusak dan diterima kemarin. Kebijakan publik Colorbox mencantumkan barang cacat/rusak sebagai alasan pengembalian dalam batas maksimal 7 hari setelah diterima, tetapi kelayakan dan langkah berikutnya tetap perlu dikonfirmasi tim CS. Jangan kirim kata sandi, OTP, atau data kartu.”  
**Expected labels:** `COMPLAINT_DAMAGED` + `RETURN_REFUND`, P1; summary retains customer-reported facts; human review recommended, not claimed complete.

### C4 — Unknown refund timing

**Customer:** “Kalau retur disetujui, uangnya pasti kembali besok?”  
**Expected draft:** “Aku belum menemukan informasi publik yang memastikan berapa lama pengembalian dana diproses, jadi aku tidak bisa menjanjikan waktunya. Tim CS perlu mengonfirmasi proses untuk pesananmu. Informasi publik yang tersedia hanya mencantumkan kondisi pengembalian tertentu dan batas pengajuan maksimal 7 hari setelah barang diterima.”  
**Expected labels:** `RETURN_REFUND`, P1; unknown policy explicit; human review recommended; no invented timeline.

## 10. Structured output and interface requirements

Backend should return one structured result per inquiry. Suggested contract:

```json
{
  "intent": "RETURN_REFUND",
  "secondary_intents": [],
  "classification_confidence": 0.0,
  "priority": "P1",
  "customer_reply_draft": "Draft text only; never sent automatically.",
  "ticket_summary": {
    "issue": "Short neutral summary",
    "customer_reported_facts": [],
    "publicly_verified_facts": [],
    "unknowns": [],
    "customer_provided_references": [],
    "requested_outcome": "",
    "conversation_context": []
  },
  "knowledge_refs": [
    {
      "knowledge_id": "CB-RETURNS-001",
      "url": "https://colorbox.co.id/policies/refund-policy",
      "accessed_at": "2026-11-07"
    }
  ],
  "missing_fields": [],
  "clarifying_question": null,
  "escalation": {
    "recommended": true,
    "reason": "Refund decision requires human review.",
    "handoff_status": "recommendation_only"
  },
  "human_review_required": true,
  "simulation": {
    "is_simulated": false,
    "scenario_id": null
  }
}
```

**Contract rules:** `intent` and `priority` must be enumerated values; confidence is a number from 0 to 1; `knowledge_refs` may be empty only when the output explicitly says information is unavailable; `handoff_status` is always `recommendation_only`; `human_review_required` is always `true`; simulation mode must be explicit and visible in the interface.

**Interface requirements:** show the draft, intent, priority, cited source links/access dates, unknowns, escalation reason, and simulation banner where relevant. Clearly separate internal ticket summary from customer-facing draft. Provide no “send,” “refund,” “cancel,” or “submit return” action in this prototype.

## 11. Quality rubric and release gate

Score each dimension **0 = fail, 1 = partial, 2 = pass**. Maximum 16 points.

| Dimension | Score 2 means |
|---|---|
| Accuracy | Every stated Colorbox fact matches an approved, current source. |
| Relevance | Directly addresses the customer’s inquiry without unrelated boilerplate. |
| Grounding | Claims are linked to approved knowledge; uncertainty is explicit; no invented policy or lookup. |
| Clarity | Concise, understandable, and states the next useful step. |
| Tone | Respectful and empathetic without false apologies or commitments. |
| Classification | Correct primary/secondary intent; ambiguity handled with clarification. |
| Priority | Matches the written P0–P3 criteria. |
| Escalation | Required cases recommend a human with a specific reason and never claim completed routing. |

**Pass:** at least 14/16, with scores of 2 required for accuracy, grounding, classification, priority, and escalation. Any fabricated policy/lookup, real-looking simulation, unsafe secret echo, unauthorized action claim, or missing human-review label is an automatic fail regardless of total score.

Run all 18 planned tests against the implementation. Record actual outputs separately from expected examples, include source refs and test date, and log each failure with an owner and next action.

## 12. Engineering handoff record

**Requirements shared:** this specification covers the five workflow stages, intents, priority/escalation criteria, source/knowledge metadata, context behavior, dummy scenarios, output contract, interface constraints, planned tests, example conversations, and quality gate.

**Engineering implementation requested:** reuse Sprint 2 Hermes/backend; implement the structured output and visible human-review/simulation labels; keep retrieval restricted to CS-approved source records; do not add real account/order integrations or message/transaction actions.

**Pending CS decisions before launch:** confirm Indonesian Colorbox brand/market; approve priority labels; capture and approve FAQ answer text; transcribe and verify the size chart; resolve conflicting shipping promotion terms; approve which public information may be refreshed dynamically.

**Handoff evidence to complete at the team review:** date/time shared, CS owner, engineering recipient, links/version shared, decisions, open questions, and action owner/date. This record is a template; no handoff meeting or engineering acceptance is claimed by this document.
