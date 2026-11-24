# Sprint 5 - Backlog Disposition Register (CS & Ops)

**Prepared:** 2026-11-21 (Asia/Jakarta)
**Scope:** Clear previous CS & Ops backlogs and validate live CS bot operation on WhatsApp before CS-01 / MKT-01..MKT-07 template work.
**Source of backlog:** `DAY4_5_WHATSAPP_VALIDATION_REPORT.md` section "What is still required before Day 4-5 is complete", plus live-test findings recorded 2026-11-15 to 2026-11-17.
**Evidence rule:** sanitized only. No credentials, API tokens, phone numbers or customer data in this document.

## 1. Backlog items and disposition

| # | Item | Type | Status | Evidence | Next action |
|---|---|---|---|---|---|
| B1 | Authoritative order-status feed (Status column in Orders sheet or status API) | CS/Ops | **OPEN - BLOCKER** | Day 4-5 report, `WA-STATUS-01` blocked; `WA-CANCEL-01` partial | Ops fills/confirms `Status` values and stage rule; then retest WA-STATUS-01 and the cancellable/unshippable branch of WA-CANCEL-01 |
| B2 | Human handoff owners per category (refund, discount, dispute, cancellation) | CS/Ops | **OPEN - by design** | Tickets recorded but `owner_assigned: false` on every live ticket | CS names owners; wire into `handover.py` owner map; retest one ticket per owner |
| B3 | Background-review line leak on WhatsApp | Defect | **CLOSED** | Fixed `auxiliary.background_review.enabled=false`; confirmed clean across four live conversations 2026-11-17 | None |
| B4 | Ticket `Kontak` empty (agent saw display name only) | Defect | **FIXED - pending live retest** | Sender number now rendered on the `**User:**` line and copied into `contact`; code in place, no post-fix live ticket yet | Send one live refund request and confirm `Kontak` is populated |
| B5 | Video demo recording (product rec, sample stock, simulated order, four policy/guardrail replies) | Deliverable | **OPEN** | Not recorded | Record sanitized walkthrough on demo number |
| B6 | Final CS MVP workflow doc (report + Sprint 2 SOPs + source register + sanitized evidence) | Deliverable | **OPEN** | Only Day 4-5 report exists | Assemble once B1/B5 settle |
| B7 | Handover tab stale test rows (`RETEST`, `HW-20261115-FE38CA`, `PROBE-HANDOVER`, `HW-20261116-BF32B1`) | Housekeeping | **OPEN** | Day 4-5 report item 7 | Delete/manual cleanup in sheet |
| B8 | Tool-trace leak in customer replies | Defect | **CLOSED** | Fixed via WhatsApp display settings; confirmed live | None |
| B9 | Handover not triggered without ticket ID | Defect | **CLOSED** | Rule + eager tool loading; four categories produced tickets first attempt 2026-11-17 | None |
| B10 | Stack killed by shell cancellation | Defect | **CLOSED** | Detached launchers; verified | None |
| B11 | Follow-up message after ticket creation (CS person will contact, stay in chat) | Change request | **DONE - pending live retest** | `handover.py` acknowledgement now ends with its own `follow_up` paragraph; SOUL rule added; 151 tests pass | Retest one live ticket |

## 2. Sprint 5 implementation steps - coverage

| Step | Requirement | Current state | Gap |
|---|---|---|---|
| 1 | Inventory previous-sprint pending tasks and blockers with links | This register | ClickUp task set confirmed 2026-11-21 (see section 5); Sprint 4 CS tasks already `completed` in ClickUp |
| 2 | Configure and use temporary third-party WhatsApp API; coordinate routing with Backend Engineering | Hermes Baileys bridge on the demo number, paired 2026-11-13; live since 2026-11-15; routing BFF :8090 + MCP + gateway :8642 | Provider confirmed as the temporary API by the CS owner 2026-11-21; routing owner (Backend Engineering) not yet named in writing |
| 3 | Live CS bot testing with expected vs actual, resolve/retest | 5/5 executed scenarios PASS; `WA-STATUS-01` BLOCKED; `WA-CANCEL-01` PARTIAL; handover live for all 4 categories | Fresh live pass after B4 and B11 changes; stack currently stopped, needs restart first |
| 4 | Clear other pending backlogs with explicit outcomes | See section 1 | B1, B2, B5, B6, B7 open |
| 5 | Store sanitized evidence in shared working document | ClickUp connected 2026-11-21; sprint brief `2kzn5r6w-2038` readable | Sanitized evidence not written yet |

## 3. Exact blockers and next actions

- **Blocker A (Ops):** no order-status source. Blocks `WA-STATUS-01` and full `WA-CANCEL-01`. Owner: CS/Ops.
- **Blocker B (CS):** no handover owners assigned. Does not block recording, blocks "forwarded to X" wording. Owner: CS.
- **Blocker C (access, reference documents):** ClickUp Doc `2kzn5r6w-5998` (base catalog `AI_Top_Trends_Master_Catalog_30_Pegawai_AI_v1.0.docx`) returns HTTP 403 Access denied for this account - this is the "You do not have access to this Doc" text in Mansi's task. `Task Pegawai AI Template & Profile.pdf` is not in the workspace. Google Drive is not signed in on this browser, so the Karyawan.AI reference folder and the Dev Team template folder cannot be opened. Next: request access to the catalog doc and the PDF, and sign in to Drive; record as missing input, do not invent contents.
- **Blocker D (routing owner):** temporary WhatsApp provider is confirmed as Hermes + Baileys on the demo number (CS owner, 2026-11-21), but no Backend Engineering contact is named in writing for routing support.
- **Blocker E (shared template document):** no ClickUp doc for the 8 role templates exists yet; the workspace doc list has only the sprint brief. Day 2 requires "the shared document used with Marketing & Ops" plus its link. Next: agree the location (ClickUp doc vs Drive file) with Marketing & Ops before writing role entries.

## 4. ClickUp task set in scope (assignee: Mansi Bhavsar, id 113655234)

Only these items may be edited; everything else in the workspace stays read-only.

| Task | ID | Status | Scope |
|---|---|---|---|
| [R&D] AI Employee Templates: CS (CS-01) & Marketing/Sales (MKT-01..MKT-07) | `z8xxqwh793` | new | Parent: 8 templates, 11 components each |
| Day 1: Validate Live CS Bot via Temporary WhatsApp API and Clear Backlogs | `z8xxqwh79c` | new | This register + live validation evidence |
| Day 2: Complete 11-Component Templates for CS-01, MKT-01 and MKT-02 | `z8xxqwh79e` | new | 3 roles |
| Day 3: Complete 11-Component Templates for MKT-03, MKT-04 and MKT-05 | `z8xxqwh79d` | new | 3 roles |
| Day 4: Complete 11-Component Templates for MKT-06 and MKT-07 with Approval and Handoff Rules | `z8xxqwh79g` | new | 2 roles |
| Day 5: Review 8 CS/Marketing Templates, Verify Approval Rules and Finalize BE/FE Handover | `z8xxqwh79f` | new | Cross-check + handover |

## 5. Status legend

- **CLOSED** - verified fixed, evidence exists.
- **DONE - pending live retest** - implemented and unit-tested, live proof outstanding.
- **OPEN** - not done or blocked, listed in section 3.
- Nothing in this register is marked complete without evidence.
