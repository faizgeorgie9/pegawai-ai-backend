# Sprint 5 Backend/Frontend Handover v1

**Prepared for:** Mansi Bhavsar  
**Status:** Implementation handoff draft; no engineering receipt recorded  
**Related review packet:** `SPRINT5_ROLE_TEMPLATE_REVIEW_PACKET_v1.md`  
**Shared working copy:** See `SPRINT5_SHARED_DOC_LINKS_v1.md` in this folder.

## 1. Handoff boundary

This document converts the eight role templates into implementation work items. It does not authorize production writes, live customer sends, ad activation, publishing, hiring, or ticket assignment. Every open owner field is blank because no named owner was found in the available sources.

## 2. Backend work items

| ID | Work item | Applies to | Acceptance criteria | Status |
|---|---|---|---|---|
| BE-01 | Restore master catalog access and paste the exact JD baseline into Section 0 of each role template. | All 8 roles | Doc `2kzn5r6w-5998` opens; Section 0 in all eight templates matches the catalog text; source ID recorded. | Blocked HTTP 403 |
| BE-02 | Enforce the role-specific permission matrix from Section 7 of each template. | All 8 roles | Default deny; blocked tools return a clear non-execution message; no hidden fallback to a broader account. | Pending |
| BE-03 | Load the 13 Karyawan.AI dossiers and eight role templates into the approved knowledge source. | All 8 roles | Source IDs resolve to the exact `.txt` files; retrieval returns source ID and role version; no unapproved source mixed in. | Pending |
| BE-04 | Expose `karyawan_task_create` and `karyawan_task_move` only where the template allows them. | MKT-02, MKT-07 | Create/move work; no send, publish, delete, hire, or account-change tool exposed. Payload hygiene enforced: no credentials, customer data, internal IDs, or calendar dates in `title`, `ai_input`, or `ai_result`. | Pending |
| BE-05 | Wire Meta Ads tools with PAUSED-only creation and explicit activation gate. | MKT-03 | Campaigns, ad sets, creatives, and ads created PAUSED; `ads_activate_entity` requires explicit user go-ahead; Raka clone path requires active backend and both confirmation gates. | Pending |
| BE-06 | Add draft-only email storage and approval records. | MKT-04 | Bot can write drafts and read approval state; cannot self-approve; no ESP, contact list, payment, refund, or test-send connection. | Pending |
| BE-07 | Add landing-page draft/preview storage with human publish gate. | MKT-05 | Bot can create drafts and previews; publish requires named human; no lead/PII store, form endpoint, or webhook created by the bot. | Pending |
| BE-08 | Constrain WhatsApp pre-sale tool scope. | MKT-06, CS-01 boundary | One reply per turn; exact follow-up text appended as a second paragraph: `Petugas customer service akan segera menghubungi Anda. Mohon tetap di chat ini, ya.`; no post-sale conversations. | Pending |
| BE-09 | Provide an authoritative read-only order-status source for the simulated status set. | CS-01, MKT-06 | Values limited to `baru`, `diproses`, `dikirim`, `diterima`, `batal`; one Order ID per checkout; one row per line item; no invented status. | Pending |
| BE-10 | Keep order-sheet append disabled by default. | CS-01, MKT-06 | Any append requires Ops sign-off; audit record names the human approval; default response refuses to write. | Pending |
| BE-11 | Implement the handoff ticket store with four deliberately unassigned categories. | CS-01, MKT-06 | Ticket categories verified live; `owner_assigned: false` until Ops assigns; handoff is recommendation only, not a live escalation. | Partial |
| BE-12 | Add run id, schema validation, source IDs, and audit records. | All 8 roles | Every run returns a run id, validation result, source IDs, and tool-decision log; invalid output is rejected, not repaired silently. | Pending |
| BE-13 | Supply or explicitly waive `Task Pegawai AI Template & Profile.pdf`. | PM / All 8 roles | Depth standard verified against the PDF or waiver recorded in the shared document. | Pending |
| BE-14 | Confirm the temporary WhatsApp API provider. | Backend / Ops | Decision recorded: Hermes/Baileys demo number or hosted provider such as Fonnte/Wablas/Wati; no credentials in chat or documents. | Pending |

## 3. Frontend work items

| ID | Work item | Acceptance criteria | Status |
|---|---|---|---|
| FE-01 | Role template reviewer for eight roles. | Lists CS-01 and MKT-01–MKT-07; opens the Markdown/DOCX version; shows version `v1`. | Pending |
| FE-02 | 11-section viewer plus Section 0. | All required sections visible in order; blocked/source-badged items cannot be mistaken for approved content. | Pending |
| FE-03 | 8-by-11 coverage matrix view. | Uses the same `P`, `P/R`, and `P/B` legend as the review packet; no cell renders as approved unless the decision log says so. | Pending |
| FE-04 | Review decision log editor. | Pending/Blocked/Pattern accepted states visible; no default approval; named owner and date required before status changes to accepted. | Pending |
| FE-05 | Source register links. | Source IDs open the correct local file or public Drive item; blocked source `2kzn5r6w-5998` shows HTTP 403 state. | Pending |
| FE-06 | Sanitized evidence panel. | Day 4–5 results, backlog statuses, and COLORBOX readiness shown without customer data, credentials, tokens, or internal IDs in task payloads. | Pending |
| FE-07 | Tool permission chips. | Shows execute/draft/read/blocked states from each role's Section 7; PAUSED, no-send, draft-only, publish-blocked, and append-disabled states are visually distinct. | Pending |
| FE-08 | Remove inherited wrong-brand CS UI elements. | No `PT AI TOP TRENDS`, `SOP-CS-AITT`, or `<15 detik` display; active provider from health/config is shown. | Pending |
| FE-09 | Add persistent conversation/thread and progress state. | Multi-turn review works without manual history; timeout is configurable and shows progress rather than silently dropping at 180 seconds. | Pending |
| FE-10 | Surface structured validation and review metadata. | Strict JSON/schema result, run id, priority, escalation state, human-review flag, simulation flag, and source count are visible. | Pending |

## 4. Approval gates

1. Catalog JD baseline gate: no final sign-off until BE-01 is complete.
2. Persona mapping gate: no final sign-off for MKT-01/04/05/06/07 until reviewers accept the stated mapping assumptions.
3. Meta Ads gate: creation PAUSED; activation only after explicit user go-ahead; Raka requires both confirmation gates.
4. Draft/publish gate: MKT-04 and MKT-05 cannot send, publish, or self-approve.
5. WhatsApp gate: pre-sale only; one reply per turn; exact follow-up text; no post-sale takeover.
6. Order data gate: status read-only; simulated values must be supplied; append disabled unless Ops signs off.
7. Ticket gate: categories may be created; owners remain unassigned until Ops assigns them.
8. Payload hygiene gate: no credentials, customer data, internal IDs, or calendar dates in ClickUp task fields.

## 5. Acceptance checklist

- [ ] All eight role DOCX files open and show the required 11 sections plus Section 0.
- [ ] Coverage matrix matches the review packet.
- [ ] RD-01 through RD-13 resolved or explicitly accepted as open conditions.
- [ ] No blocked source rendered as approved.
- [ ] No live send, ad activation, publish, hire, or real ticket assignment performed during review.
- [ ] No secret, token, API key, password, customer data, or calendar date appears in task payloads.
- [ ] Named owners recorded in the shared document.
- [ ] Engineering receipt recorded in this folder or the shared document.

## 6. Open owner fields

| Owner group | Name | Receipt | Date |
|---|---|---|---|
| Backend | ____________________ | ____________________ | __________ |
| Frontend | ____________________ | ____________________ | __________ |
| Marketing reviewer | ____________________ | ____________________ | __________ |
| Ops reviewer | ____________________ | ____________________ | __________ |
| CS owner | ____________________ | ____________________ | __________ |
| PM / final archive | ____________________ | ____________________ | __________ |
