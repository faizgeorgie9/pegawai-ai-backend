# Colorbox CS → Backend handoff v1.1

**Package:** Colorbox CS Sprint 3  
**Prepared:** 2026-11-07 (the assignment’s planned work-package date is 2026-11-06; evidence is not backdated)  
**CS owner:** Intern 3 / Customer Service  
**Implementation owner:** Backend  
**Scope:** CS-owned source/knowledge package and business behavior requirements; no backend implementation changes included here. Handoff materials are prepared locally; no engineer receipt is yet recorded.

## Incremental delivery order

1. Load `COLORBOX_CS_Knowledge_v1.json` and `COLORBOX_CS_Source_Register_v1.csv` as source-labeled public knowledge. Preserve record status, source URL, access date, and limitations; do not load provisional assumptions as policy.
2. Load `COLORBOX_CS_Instructions_v1_2.md` as the current CS behavior contract; retain v1.0 and v1.1 files for audit. The current prompt requires source URLs/access dates, draft-only handling, clean separation of customer text from internal labels, relevant context only, strict unknowns, priority, and internal escalation recommendations.
3. Load `COLORBOX_CS_Dummy_Scenarios_v1.json` only in an explicit simulation/test mode. Keep the simulation warning and scenario IDs visible; reject fixture state as live evidence.
4. Enforce `COLORBOX_CS_Output_Schema_v1.json` at the backend boundary.
5. Use `COLORBOX_CS_Test_Corpus_v1.json` as expected fixtures, not as actual model output. Actual requests/responses are recorded separately under `evidence\`.
6. Review `COLORBOX_CS_Initial_Test_Report_v1.md` and the open gaps before any wider implementation or use.

## Sprint 2 reuse / implementation boundary

Use the existing shared Hermes backend and direct `/api/v1/agent/execute` route; no setup repetition and no UI dependency. CS test requests manually select and inject known source records because the backend has no retrieval engine yet. This tests grounding against supplied evidence, **not retrieval/search quality**. Backend owns retrieval implementation, structured-output enforcement, and interface handling.

No live order, stock, tracking, customer-account, Shopee, Instagram, CRM, ticket, messaging, payment, or transaction integration is requested. Every generated response remains an unsent draft requiring human review.

## Initial direct test result

Three final actual requests were sent to the existing shared backend on 2026-11-07 using instructions v1.2. All returned HTTP 200 from `opencode-go` / `deepseek-v4.1-flash` with no fallback. Initial runs exposed missing URLs/dates, an unverified product-collection citation, irrelevant summary facts, and internal draft-status text; these were corrected in the source mapping/instructions and directly rechecked. Final outputs cite verified URLs/access dates and keep internal labels outside customer drafts. Full versioned inputs/responses and the case-level assessment are in `evidence\` and `COLORBOX_CS_Initial_Test_Report_v1.md`.

The tests manually injected case-selected knowledge; they do not prove an implemented retrieval engine. Engineering still owns retrieval, output-schema validation, and UI controls. FAQ answer text, verified size-chart measurements, shipping terms, refund timing/method, and CS approval of assumptions/priority labels remain open.

## Related ClickUp work references

- [z8xxqwefqf](https://app.clickup.com/t/z8xxqwefqf)
- [z8xxqwefqd](https://app.clickup.com/t/z8xxqwefqd)
- [z8xxqwefqe](https://app.clickup.com/t/z8xxqwefqe)

The assignment states that execution of business behavior is split across these tasks; this package is the shared source/instruction/fixture corpus. Task descriptions/status were not fetched in this run.

## Six-hour package budget (target, not time-tracked)

| Work | Budget |
|---|---:|
| Confirm brand/market assumption and review public source facts | 0.5 h |
| Curate and label knowledge/source register | 1.0 h |
| Draft instructions, output contract, priority/escalation/context rules | 1.0 h |
| Prepare simulated records and expected corpus | 0.75 h |
| Run and assess three direct cases | 1.5 h |
| Review evidence, document blockers, hand off to Backend | 1.25 h |
| **Total planned** | **6.0 h** |

This is a time budget only. Actual focused hours were not time-tracked, and an engineering receipt/acceptance has not been independently recorded.

## Pending handoff receipt

Complete at team review: recipient, date/time, package version/hash, files loaded, implementation owner, decisions, open gaps, and action owner/date. Do not mark accepted until Backend confirms.
