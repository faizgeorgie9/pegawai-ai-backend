# Colorbox CS initial direct-test report

**Package:** Colorbox CS Sprint 3  
**Evidence run date:** 2026-11-07 (Asia/Jakarta)  
**Instructions evaluated:** v1.0, v1.1, and final v1.2  
**Test method:** Direct `POST /api/v1/agent/execute` to the existing Sprint 2 backend; no UI  
**Model reported by backend:** `opencode-go` / `deepseek-v4.1-flash`  
**Data:** Synthetic test wording and fabricated scenario fixtures only; no real customer data

## Result

Three representative cases were actually run against v1.0, v1.1, and final v1.2. A further T01-only check corrected a product source mapping after the collection/detail pages proved inaccessible. All ten calls returned HTTP 200, `status=success`, `fallback_applied=false`, and the expected provider/model. The expected behavior fixtures were stored outside the model prompt; each request carried only the CS instructions, case-selected knowledge, relevant source-register rows, same-conversation history, and test input.

The final v1.2 results passed the planned business-behavior checks for classification, grounded drafting from supplied records, context retention, simulation labeling, missing-information honesty, priority, and internal escalation recommendation. This is **not** evidence of a working retrieval engine: source selection was manual/prompt-injected, not searched or retrieved by the backend.

## Final actual run (instructions v1.2)

| Test | Coverage | Actual classification / priority | Observed behavior | Assessment | Latency |
|---|---|---|---|---|---:|
| CB-CS-T01 | Product info + availability; selected knowledge/source refs; unknown live stock | Primary `PRODUCT_AVAILABILITY`, secondary `PRODUCT_INFO`, P2 | Returned the dated home-page price, cautioned it may change, said displayed sizes do not prove stock, recommended current-site/human checking, and cited the exact home-page URL and access date. No irrelevant source facts were added to the summary. | Pass | 17.41 s |
| CB-CS-T02 | Multi-turn damaged-item complaint + refund | Primary `RETURN_REFUND`, secondary `COMPLAINT_DAMAGED`, P1 | Retained the item, receipt timing, damage report, and refund request; stated the public 7-day condition; did not approve or promise a refund; recommended human review. Cited the official policy URL/date. | Pass | 17.41 s |
| CB-CS-T03 | Simulated order/return/refund + fictional policy conflict + unknown refund timing | Primary `RETURN_REFUND`, secondary `ORDER_STATUS`, P1 | Clearly marked fixture statuses as simulated, rejected the fictional 30-day claim as policy, used the verified public 7-day condition, said refund timing is unknown, and recommended human review. Cited policy/tracking URLs and dates. | Pass | 31.59 s |

### Quality rubric

Each final response was manually scored 0–2 on accuracy, relevance, grounding, clarity, tone, classification, priority, and escalation (16 maximum). T01: **16/16**; T02: **16/16**; T03: **16/16**. These are one-time human assessments of these three outputs, not a statistically meaningful accuracy rate or a release certification. Actual raw outputs are retained; re-score after any prompt, model, or knowledge change.

## Initial run and correction record

| Issue | Initial evidence | Correction | Corrected evidence |
|---|---|---|---|
| Model returned null/missing source URLs and some access dates, despite citing knowledge/source IDs. | `evidence\CB-CS-T01_response.json` through `CB-CS-T03_response.json` | Added source-register rows and v1.1 citation requirements. The first corrected T01 linked a collection that was not directly verified; the product detail returned HTTP 429. Product fact now cites only the reviewed home page and the failed detail lookup is recorded as a source gap. | Final T01 in `evidence\run_20261107_v1_2\` cites `https://colorbox.co.id/` and `2026-11-07`. All used refs in the final v1.2 run have exact URLs/access dates. |
| Mixed product/availability input did not state how to choose one primary intent. | T01 v1 selected availability as primary and product info as secondary. | v1.1 makes the highest-priority intent primary; in equal-priority cases, use the customer’s main requested outcome. | Final T01 is `PRODUCT_AVAILABILITY` primary, `PRODUCT_INFO` secondary, P2; accepted because live stock is the stricter handling requirement. |
| v1.1 sometimes copied unrelated source-scope facts into the summary and included internal draft-status wording inside customer-facing text. | T01/T03 under `evidence\run_20261107_v1_1\` | v1.2 says summaries must stay relevant and review/status labels belong in metadata, not `customer_reply_draft`. Reran all three cases. | Final v1.2 T01 summary is focused; all final customer drafts contain no internal review label. |

No corrected-case failure was observed in this small corpus. This does not imply the backend enforces the structured schema: responses were inspected manually, and the backend still needs schema validation.

## Evidence map

- Expected inputs and pass/fail criteria: `COLORBOX_CS_Test_Corpus_v1.json` (**fixtures, not generated model results**).
- Actual initial v1.0 requests/responses: `evidence\CB-CS-T01_request.json` through `CB-CS-T03_response.json`.
- Actual corrected v1.1 requests/responses: `evidence\run_20261107_v1_1\`.
- Product-source recheck: `evidence\run_20261107_v1_1_sourcefix\`.
- Final v1.2 requests/responses and summary: `evidence\run_20261107_v1_2\`.
- Source citations: `COLORBOX_CS_Source_Register_v1.csv`; structured knowledge: `COLORBOX_CS_Knowledge_v1.json`.
- Simulations (fictional only): `COLORBOX_CS_Dummy_Scenarios_v1.json`.
- Original/corrected instructions: `COLORBOX_CS_Instructions_v1.md` and `COLORBOX_CS_Instructions_v1_1.md`.

The requests contain the exact prompts and synthetic data; response files contain the exact backend results, timestamps, status, model route, latency, and usage metrics. No expected response was passed to the model.

## Exact remaining blockers / actions

1. **Retrieval not implemented or tested.** Backend needs a source retrieval/indexing mechanism and tests for correct selection, missing records, and conflicting records. Today the three calls manually selected/injected sources.
2. **FAQ answers incomplete.** The official FAQ index shows ordering, product, shipping, returns, payment, and technical categories, but answer text was not extractable/approved in this review. CS must capture and validate the actual answers before they become answerable knowledge.
3. **Product/size details incomplete.** The linked product detail page returned HTTP 429 during review; the size-chart image needs a legible transcription checked by CS. No numeric fit recommendations are approved.
4. **Shipping terms unresolved.** Homepage banners contain varying offer terms. Confirm exact eligibility, fee, delivery, and Click & Collect conditions; until then do not quote a universal fee or delivery commitment.
5. **Refund process incomplete.** Public source does not establish refund processing time or method. Return eligibility for individual cases must be checked by a human.
6. **CS approvals outstanding.** Confirm the Indonesia market assumption and approve the proposed P0–P3 prioritization rules. These labels are not existing Colorbox SLAs.
7. **Engineering receipt outstanding.** Files are prepared for the local shared project folder, but an engineer has not confirmed loading or acceptance. Related ClickUp descriptions/status were not fetched in this run.

## Boundary and release status

No order/status/inventory system, Shopee, Instagram, CRM, ticketing, customer messaging, payments, or transactions were accessed or performed. All drafts require human review. **CS requirements and the initial three-case evidence are ready for Engineering review; complete workflow implementation and source retrieval remain out of scope for this CS handoff and are not represented as done.**
