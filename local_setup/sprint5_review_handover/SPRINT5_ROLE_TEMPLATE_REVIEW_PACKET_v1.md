# Sprint 5 Role Template Review Packet v1

**Prepared for:** Mansi Bhavsar  
**Scope:** CS-01 + MKT-01–MKT-07 role template cross-review and handover  
**Status:** Drafted for Marketing/Ops review; no final role sign-off recorded  
**Shared working copy:** See `SPRINT5_SHARED_DOC_LINKS_v1.md` in this folder.

## 1. Purpose

This packet records the structural completeness of the eight Sprint 5 role templates, the source basis used to draft them, the sanitized evidence supporting the review, and the decisions still required before the templates can be signed off or configured in production.

This packet is a review artifact, not an approval. No Marketing, Ops, CS, Backend, or Frontend owner has been assigned or has signed off in the available sources.

## 2. Review scope and status

| Item | Status | Meaning |
|---|---|---|
| Eight role templates drafted | Complete | CS-01 and MKT-01–MKT-07 exist as Markdown and DOCX. |
| Eleven required sections in each template | Complete | Every role has all 11 required sections; section numbering inconsistency found earlier was fixed. |
| Structural QA | Complete | DOCX files were generated and checked for headings and tables. |
| CS-01 pilot review | Pattern accepted | User said "its good"; accepted as format/structure/depth pattern only, not production approval. |
| Marketing/Ops persona and tool review | Pending | Decision log below is prepared; no reviewer decision is recorded. |
| Master catalog JD baselines | Blocked | Catalog Doc `2kzn5r6w-5998` returns HTTP 403; must be pasted into Section 0 before sign-off. |
| Depth standard PDF | Blocked | `Task Pegawai AI Template & Profile.pdf` was not found; depth standard is unverified beyond CS-01 pattern. |

## 3. Required 11 sections

1. Scope of Work & Boundaries
2. Persona/Language/Tone
3. Triggers & Use Cases
4. Modular Skills & Capabilities
5. SOP & Task Execution Pattern
6. Operating Rules & Prohibitions
7. Tools/Integrations/Permissions
8. Knowledge Base & Memory Needs
9. Input & Expected Output Standards
10. Approval & Escalation Rules
11. Model Recommendation & KPIs

## 4. 8-role by 11-section coverage matrix

Legend:

- `P` = required section present and drafted.
- `P/R` = present; reviewer decision required because the role, source mapping, owner, or boundary is an assumption.
- `P/B` = present; blocked by unavailable source, tool access, or missing operational owner.

| Role | S1 Scope | S2 Persona | S3 Triggers | S4 Skills | S5 SOP | S6 Rules | S7 Tools | S8 KB | S9 I/O | S10 Approvals | S11 Model/KPIs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CS-01 Omnichannel Customer Service | P | P | P | P | P | P | P/B | P | P | P/R | P/R |
| MKT-01 Marketing Strategist | P/R | P/R | P | P/R | P/R | P | P/B | P/R | P/R | P/R | P/R |
| MKT-02 SEO Specialist | P/R | P | P | P/R | P/R | P/R | P/B | P/B | P/R | P/R | P/R |
| MKT-03 Digital Ads Specialist | P/R | P/R | P | P/R | P/R | P/R | P/B | P/R | P/R | P/R | P/R |
| MKT-04 Email Marketing Specialist | P/R | P/R | P | P/R | P/R | P/R | P/B | P/R | P/R | P/R | P/R |
| MKT-05 Lead Generation Specialist | P/R | P/R | P/R | P/R | P/R | P/R | P/B | P/R | P/R | P/R | P/R |
| MKT-06 Sales Assistant | P/R | P/R | P/R | P/R | P/R | P/R | P/B | P/R | P/R | P/R | P/R |
| MKT-07 Marketing Performance Analyst | P/R | P/R | P | P/R | P/R | P/R | P/B | P/R | P/R | P/R | P/R |

Section 0, `Catalog JD baseline (source blocked)`, is present in all eight templates but remains blocked for every role until the master catalog is accessible. The matrix above covers only the 11 required sections.

## 5. Role-by-role source basis

| Role | Source basis | Review decision required |
|---|---|---|
| CS-01 | Approved user pattern; COLORBOX CS evidence and handoff package; live WhatsApp follow-up implementation. | Confirm production owner for status feed, WhatsApp provider, and handoff queue. |
| MKT-01 | `Aldi - Market Research Strategist`, `Bram - Direct Response Marketer`, `Meda - Meta Andromeda 2.0 Strategist`, `Bimo - AI Project Manager`, `Agent List`, `Agent Marketing`. | Confirm no exact Marketing Strategist dossier; confirm using Bimo behavior for Meda because the Meda dossier is thin. |
| MKT-02 | `Rifqy Yusuf - SEO Specialist`; direct adaptation. | Confirm optional prompt files referenced by the dossier; confirm escalation/KPI/retention additions marked Proposal. |
| MKT-03 | Farid, Raka, Sari, Zara, Bimo, Meda. | Confirm Meta Ads PAUSED-only creation, explicit activation approval, and Raka backend confirmation gates. |
| MKT-04 | Maya, Sari, Bram; CS-01 pattern. | Confirm no exact email dossier exists; confirm draft-only model, no ESP, no self-approval, and named human approver. |
| MKT-05 | Vera, Sari, Bram, Farid; CS-01 pattern. | Confirm no exact lead-generation dossier exists; confirm draft-only preview and human-only publish. |
| MKT-06 | CS-01 boundaries, Sari, Bram, Zara. | Confirm no exact sales-assistant dossier exists; confirm pre-sale-only scope and exact handover line. |
| MKT-07 | Farid, Bimo, Meda, `Agent List`, `Agent Marketing`. | Confirm no exact analytics dossier exists; confirm read-only analytics and no ad-entity writes. |

## 6. Review decision log

No decision below has been signed by Marketing, Ops, CS, Backend, Frontend, or the user unless explicitly noted.

| ID | Decision | Recommendation | Owner group | Status |
|---|---|---|---|---|
| RD-01 | Restore access to master catalog Doc `2kzn5r6w-5998` and paste each role's JD baseline into Section 0. | Block final sign-off until complete. | PM / Backend | Blocked |
| RD-02 | Treat CS-01 as accepted format/structure/depth pattern. | Accept the pattern only; do not treat as production approval. | User / Marketing / Ops | Pattern accepted |
| RD-03 | Confirm MKT-01 role mapping. | Accept mapping as Proposal if no exact dossier is supplied. | Marketing | Pending |
| RD-04 | Confirm MKT-02 optional prompt files. | Keep as Blocker until files are supplied or explicitly waived. | Marketing / Backend | Pending |
| RD-05 | Confirm MKT-03 Meta Ads safety gates. | PAUSED-only create; activation only after explicit user go-ahead; Raka requires active backend and both gates. | Marketing / Backend | Pending |
| RD-06 | Confirm MKT-04 no-send boundary. | Draft-only; no ESP, contact data, payment, refund, or self-approval. | Marketing / Ops / Backend | Pending |
| RD-07 | Confirm MKT-05 publish boundary. | Draft and preview only; named human publishes; no lead/PII store. | Marketing / Ops / Backend | Pending |
| RD-08 | Confirm MKT-06 pre-sale-only scope and exact handover line. | Preserve `Petugas customer service akan segera menghubungi Anda. Mohon tetap di chat ini, ya.` verbatim. | Ops / CS / Backend | Pending |
| RD-09 | Confirm MKT-07 read-only analytics. | No ad-entity writes; MKT-03 remains the only activation role. | Marketing / Backend | Pending |
| RD-10 | Assign named human approvers and escalation owners. | Do not invent names; record owner and queue in the shared document. | Marketing / Ops / CS | Pending |
| RD-11 | Confirm WhatsApp API provider. | Choose Hermes/Baileys demo number or hosted provider such as Fonnte/Wablas/Wati before live flow. | Backend / Ops | Pending |
| RD-12 | Populate simulated order Status values. | Use `baru`, `diproses`, `dikirim`, `diterima`, `batal`; one Order ID per checkout; one row per line item. | Backend / Ops | Pending |
| RD-13 | Supply or waive `Task Pegawai AI Template & Profile.pdf`. | Keep depth-standard verification open until supplied. | PM | Pending |

## 7. Source register

### 7.1 Karyawan.AI source files

| Source ID | File name | File ID | Used by |
|---|---|---|---|
| SRC-K-01 | `Agent Marketing.mhtml` / `.txt` | `1fkZF_lzsi0F92RrdBFW53OBLD1zui61c` | MKT-01, MKT-07 |
| SRC-K-02 | `Agent List.mhtml` / `.txt` | `1B4RP3ojhKfUTmMTiC-4HvPuq-uH9ILKz` | MKT-01, MKT-07 |
| SRC-K-03 | `Aldi - Market Research Strategist.mhtml` / `.txt` | `1jZ7wXWMH9uwxACqXJWmDN9EsLcs7N5rn` | MKT-01, MKT-05 |
| SRC-K-04 | `Bram - Direct Response Marketer.mhtml` / `.txt` | `1GA6S5x5ZqKq-a0TkyapR605908vBMVPd` | MKT-01, MKT-04, MKT-05, MKT-06 |
| SRC-K-05 | `Rifqy Yusuf - SEO Specialist.mhtml` / `.txt` | `1ylop2xz-MFRd_tKoJ6cuLpMSCKg3p4TV` | MKT-02 |
| SRC-K-06 | `Farid - Meta Ads Media Buyer.mhtml` / `.txt` | `1S2leChQ79iEetdmSjqtIVq1-IWXE3ZnG` | MKT-03, MKT-05, MKT-07 |
| SRC-K-07 | `Meda - Meta Andromeda 2.0 Strategist.mhtml` / `.txt` | `1Bho_zAzv9ocvOt50ZPBKlKMcRchFoNCu` | MKT-01, MKT-03, MKT-07 |
| SRC-K-08 | `Raka - Ad Clone Specialist.mhtml` / `.txt` | `15nroa2MGQ-EEGA7piJas1lPHojhe2HMm` | MKT-03 |
| SRC-K-09 | `Maya - Ebook & Content Writer.mhtml` / `.txt` | `14-UFndrdjI__3Gtb8n50QmbzDkb8Aq5_` | MKT-04 |
| SRC-K-10 | `Sari - Meta Sales Copywriter.mhtml` / `.txt` | `1rkDC4qLlhO2aZ4XDV5jeoDlt53JNXaoI` | MKT-03, MKT-04, MKT-05, MKT-06 |
| SRC-K-11 | `Vera - Landing Page Builder.mhtml` / `.txt` | `1DZtB3Sy-R7ug4Rq2mlm7SPbTn-84QSpb` | MKT-05 |
| SRC-K-12 | `Bimo - AI Project Manager.mhtml` / `.txt` | `16D9Zd3wKyPcja-Xs8KCk6LxA0w2hzWpm` | MKT-01, MKT-03, MKT-07 |
| SRC-K-13 | `Zara - Ad Script Specialist.mhtml` / `.txt` | `1DhhryZcbiT7DuTl6g5ySz7WOQL-gFH2z` | MKT-03, MKT-06 |

### 7.2 Non-Karyawan sources

| Source ID | Source | Status | Used for |
|---|---|---|---|
| SRC-S-01 | Sprint 5 ClickUp task `z8xxqwh793` | Referenced | Scope and task link |
| SRC-S-02 | ClickUp Doc `2kzn5r6w-5798`, page `2kzn5r6w-2038` | Referenced | Sprint 5 page |
| SRC-S-03 | Master catalog Doc `2kzn5r6w-5998` | Blocked HTTP 403 | Catalog JD baselines |
| SRC-S-04 | `Task Pegawai AI Template & Profile.pdf` | Not found | Depth standard referenced by CS-01 |
| SRC-S-05 | `CS-01_Omnichannel_Customer_Service_template_v1.md/.docx` | Pattern accepted | Format, structure, depth, approval style |
| SRC-S-06 | `SPRINT5_BACKLOG_DISPOSITION_REGISTER.md` | Available | Backlog evidence |
| SRC-S-07 | `DAY4_5_WHATSAPP_VALIDATION_REPORT.md` | Available | Live-flow sanitized evidence |
| SRC-S-08 | `COLORBOX_CS_Handoff_v2_1.md` | Available | BE/FE/CS work structure |
| SRC-S-09 | `COLORBOX_CS_Package_Index_v2_1.md` | Available | Package read order and evidence inventory |
| SRC-S-10 | `COLORBOX_CS_Business_Readiness_v2_1.md` | Available | Readiness wording and limitations |
| SRC-S-11 | `COLORBOX_CS_Source_Register_v1.csv` | Available | Public-source evidence format |
| SRC-S-12 | `COLORBOX_CS_Frontend_Feedback_v2_1.md` | Available | Frontend gap patterns |
| SRC-S-13 | `COLORBOX_CS_Backend_Handoff_v1.md` | Available | Backend handoff format |

## 8. Sanitized test and backlog evidence

### 8.1 Day 4–5 WhatsApp validation

| Evidence item | Sanitized result | Limitation |
|---|---|---|
| Executed scenarios | 5 of 5 executed scenarios PASS | Does not clear blocked or partial scenarios. |
| `WA-STATUS-01` | Blocked | No authoritative order-status source; simulated values still required. |
| `WA-CANCEL-01` | Partial | Cancellation path requires operational owner and status feed. |
| Handoff ticket store | Four ticket categories verified live with deliberately unassigned tickets | No real assignment or owner exists. |
| Customer contact | No real customer contacted | Evidence is internal/simulated only. |

### 8.2 Backlog disposition

| ID | Item | Status | Review meaning |
|---|---|---|---|
| B1 | Authoritative order-status feed | Open blocker | Required before status/cancel retest. |
| B2 | Human handoff owners | Open by design | Must remain unassigned until Ops names owners. |
| B3 | Background-review line leak | Closed | Do not reintroduce internal notes in customer-visible drafts. |
| B4 | Ticket `Kontak` empty | Fixed, pending live retest | Verify with a named test after backend/ops setup. |

### 8.3 COLORBOX readiness evidence

- Response behavior on tested fixtures: demo-ready only.
- Complete inquiry-to-escalation workflow: not ready.
- Production/unattended use: not ready.
- No external handoff, ticket, approval, or customer action completed.

## 9. Approval gates to enforce

- Do not mark any role signed off until RD-01 and the role-specific pending decisions are resolved.
- Do not issue production credentials, tokens, or API keys in the packet or task payloads.
- Do not place credentials, customer data, internal IDs, or calendar dates in ClickUp `title`, `ai_input`, or `ai_result`.
- Do not publish MKT-04 email drafts or MKT-05 landing-page drafts without a named human approver.
- Do not activate MKT-03 ads without explicit user go-ahead.
- Do not allow MKT-06 to append order-sheet rows unless Ops signs off on the disabled-by-default write.
- Do not treat Recommendation-only handoff as an assigned live ticket.

## 10. Sign-off block

| Role owner | Decision | Name / role | Date |
|---|---|---|---|
| Marketing | Accept / Accept with revisions / Reject | ____________________ | __________ |
| Ops | Accept / Accept with revisions / Reject | ____________________ | __________ |
| CS owner | Accept / Accept with revisions / Reject | ____________________ | __________ |
| Backend owner | Acknowledge implementation handoff | ____________________ | __________ |
| Frontend owner | Acknowledge implementation handoff | ____________________ | __________ |
| PM | Final archive decision | ____________________ | __________ |
