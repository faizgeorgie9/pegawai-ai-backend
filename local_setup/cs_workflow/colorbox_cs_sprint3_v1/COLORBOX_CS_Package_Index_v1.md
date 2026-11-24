# Colorbox CS Sprint 3 package index

**Package target:** November 6, 2026; six focused-hour budget  
**Prepared and directly tested:** November 7, 2026 (Asia/Jakarta). Evidence is not backdated.  
**Status:** CS source, instruction, fixture, and initial test package ready for Backend review; implementation/receipt is pending.

| File/folder | Purpose |
|---|---|
| `COLORBOX_CS_Knowledge_v1.json` | Structured public brand/product/FAQ/available-policy knowledge, explicit unknowns and provisional assumptions. |
| `COLORBOX_CS_Source_Register_v1.csv` | Public URLs, access dates, captured scope, limits, capture method, and CS approval state. |
| `COLORBOX_CS_Instructions_v1.md` | Initial business instructions used in first actual tests. |
| `COLORBOX_CS_Instructions_v1_1.md` | Citation and primary-intent corrections from the first test cycle. |
| `COLORBOX_CS_Instructions_v1_2.md` | Current instructions; also keeps customer drafts clean of internal labels and summaries relevant. |
| `COLORBOX_CS_Output_Schema_v1.json` | Suggested response contract for backend validation. |
| `COLORBOX_CS_Dummy_Scenarios_v1.json` | Explicitly fictional order, return, dummy-policy, and unknown-policy records. |
| `COLORBOX_CS_Test_Corpus_v1.json` | Three expected test cases; fixtures are not actual outputs. |
| `run_colorbox_cs_direct_tests.py` | Direct API runner; writes actual request/response evidence separately. |
| `COLORBOX_CS_Initial_Test_Report_v1.md` | Actual run summary across revisions, assessment, defects/corrections, and blockers. |
| `COLORBOX_CS_Backend_Handoff_v1.md` | Incremental loading instructions, scope boundaries, task references, and receipt checklist. |
| `evidence\` | First-run v1.0 requests/responses plus corrected v1.1 requests/responses and run summary. |

## What this package does and does not prove

The final three direct model runs use instructions v1.2 and cover product/availability, contextual complaint/refund, and simulated order/return/refund with a fictional conflicting policy and unknown refund timing. All were executed against the existing Sprint 2 endpoint with no UI and no real customer data.

Selected source records were manually injected into each prompt. The run therefore checks grounding and response behavior against supplied knowledge, not retrieval/search quality. The product-detail page returned HTTP 429, so the observed price/size facts are sourced from the home page only. The existing backend has no Colorbox retrieval, live customer data integration, UI guardrails, or schema enforcement from this package.

Formal CS approval remains pending for the Indonesian market assumption, source extracts, and P0–P3 handling labels. No Engineering receipt or ClickUp update is claimed.
