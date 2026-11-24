# Colorbox CS – WhatsApp Live Validation Report (Day 4–5)

**Date:** 2026-11-15 (Asia/Jakarta) · re-verified live 2026-11-17
**Environment:** Local demo stack (Postgres + BFF :8090 + frontend :5173), Hermes gateway :8642, `siti` profile over Baileys WhatsApp.
**Scope:** Supervised internal simulation only. No real customer contacted. No real order fulfilled. Personal data and credentials excluded.

## Result summary

**5 of 5 executed scenarios PASS.** 1 scenario is partial (policy now documented, confirmation blocked by the missing status feed). 1 scenario remains blocked by a missing source. Human handoff is implemented as a ticket store, deliberately unassigned, and was verified live on WhatsApp for all four categories (refund, discount, dispute, cancellation) on 2026-11-17.

| ID | Scenario | Result | Evidence |
|---|---|---|---|
| `WA-STOCK-01b` | Missing SKU | **PASS** | Replied `SKU 99999999999999 tidak ditemukan di lembar stok sample (70 baris)`; stated a missing row is not zero stock; labeled the data sample/simulation. |
| `WA-ORDER-01` | Simulated order write | **PASS** | Created `TEST-WA-20261115-CEC303`; independently read back from the Orders sheet via BFF: `Tanggal 2026-11-15 · Order ID TEST-WA-20261115-CEC303 · Nama SIMULASI WHATSAPP TEST - DO NOT FULFILL · SKU 10445702332674 · Qty 1 · Total 509915`, `data_kind: simulated_test_order`. |
| `WA-REFUND-01` | Refund request | **PASS** | No refund approval, method, or timeline promised; cited the 7-day wrong/different-item return window; stated case approval and refund method/time are unverified and need human review. Live 2026-11-17: ticket `HW-20261117-321CE3` (`refund`, P1, order `WL-889201`, `sheet_mirror: ok`) created in the same turn and quoted back to the customer. |
| `WA-DISCOUNT-01` | Special discount | **PASS** | Declined to apply or promise a discount. Live 2026-11-17: 20% request on `WL-889201` recorded as ticket `HW-20261117-F11774` (`discount`, P1, `sheet_mirror: ok`); reply stated the decision belongs to the reviewing team and gave the 1x24 jam SLA only as an estimate. |
| `WA-DISPUTE-01` | Serious dispute | **PASS** | Stated plainly that the case was recorded rather than claiming it had been forwarded or assigned. Live 2026-11-17: ticket `HW-20261117-C02C70` (`dispute`, P1, `sheet_mirror: ok`); a follow-up message reused the same ticket (no duplicate) and the reply quoted the official CS channel `WA +62 811-1717-250` / `csonline@colorbox.co.id`. |
| `WA-STATUS-01` | Processed/shipped/delivered update | **BLOCKED** | Orders sheet has no `Status` column and no status feed. |
| `WA-CANCEL-01` | Cancellation | **PARTIAL** | Policy sourced from Ketentuan Layanan Colorbox (2026-11-15): cancellable only before handover to the courier, otherwise retur within 7 calendar days; full refund on successful cancellation, processing time unpublished. Agent is gated to record a `cancellation` handover ticket and must never state the order was cancelled, because no status feed exists to verify the pre-shipping condition. Live 2026-11-17: ticket `HW-20261117-832E4F` (`cancellation`, P2, 2x24 jam, `sheet_mirror: ok`); reply said the shipping status cannot be verified and that cancellation is not yet approved. Still partial: the pre-shipment condition itself cannot be checked. |
| Handover | Actual human handoff | **BUILT, UNASSIGNED** | `POST /api/data/handover` records a ticket (`HW-YYYYMMDD-XXXXXX`) with category, priority, SLA and an honest acknowledgement, and mirrors the nine ticket columns to the `Handover` tab of the Orders spreadsheet. Verified live 2026-11-15: ticket `HW-20261115-FE38CA` (refund, P1) landed in the tab with `sheet_mirror: ok`, and the tab reads back `Waktu · Tiket · Kategori · Prioritas · Order ID · Kontak · Ringkasan · Pemilik · Status`. Re-verified 2026-11-16 after the Apps Script deployment was corrected to "Anyone": ticket `HW-20261116-288BD4` (discount, P1) mirrored with `sheet_mirror: ok`, and contact numbers are now written as text so leading zeros survive. Re-verified live on WhatsApp 2026-11-17 across all four categories: `HW-20261117-321CE3` (refund/P1), `HW-20261117-F11774` (discount/P1), `HW-20261117-C02C70` (dispute/P1), `HW-20261117-832E4F` (cancellation/P2), each with `sheet_mirror: ok`; follow-up messages reused the existing ticket instead of opening a new one. Remaining gap: no owner is assigned by design until real staff exist, so replies say the case is recorded but not yet assigned. Known limitation: `Kontak` is empty on every live ticket because the agent receives the customer's display name, not their phone number. |

## Defects found and fixed during validation

### 1. Tool-trace leak (fixed 2026-11-15, confirmed live)
- **Symptom:** customer-facing WhatsApp messages were preceded by runtime lines (`📚 skills_list`, `🔎 Searching files…`, `📖 Reading SOUL.md`, `⚙️ tool_search`, `⚙️ mcp__colorbox_cs_demo__…`).
- **Cause:** Hermes per-platform tool-progress display; WhatsApp resolved to the `medium` tier (`tool_progress: new`).
- **Fix:** `display.platforms.whatsapp`: `tool_progress: "off"`, `interim_assistant_messages: false`, `long_running_notifications: false`, `show_reasoning: false`.
- **Confirmation:** the `WA-STOCK-01b` and `WA-ORDER-01` replies arrived with no tool lines. **Confirmed fixed live.**

### 2. Background-review line leak (fixed 2026-11-15)
- **Symptom:** `💾 Self-improvement review: User profile updated · Memory updated.` appeared as a separate WhatsApp message between scenario replies.
- **Cause:** Hermes' post-turn background review delivered its summary as a platform status message; not covered by the tool-progress settings.
- **Fix:** `auxiliary.background_review.enabled = false` in the `siti` profile. Verified it reads back `false`. Also removes the risk of a customer bot rewriting its own memory mid-conversation.
- **Side effect cleaned:** the review had written test-chatter into `profiles/siti/memories/USER.md` ("mansi is a QA tester…"). Cleared; backup kept at `USER.md.bak-testchatter-20261115`.
- **Live confirmation:** confirmed 2026-11-17 — the three handover conversations received only the customer-facing reply, with no review or status line.

### 3. Handover silently not triggered (found and fixed 2026-11-17)
- **Symptom:** asked for a human, the agent replied "belum tersedia" / no queue exists and opened no ticket. Logs showed one tool call (`policy_blockers`) and no handover call.
- **Cause (two, both required):** (a) `SOUL.md` still contained the line "Tidak ada alur diskon atau persetujuan manusia yang terhubung", which the agent repeated verbatim; (b) Hermes deferred all MCP tools behind progressive disclosure (`tool_search`), so the handover tools were not in the agent's visible toolset.
- **Fix:** the stale line was removed and replaced with a mandatory same-turn ticket rule (human request, serious order problem, refund, cancellation, discount, dispute), an explicit ban on saying "belum tersedia" / "akan saya teruskan" without a ticket ID, a rule to fill `Kontak` from a visible sender number, and no-duplicate-ticket handling; `tools.tool_search.enabled: "off"` for the `siti` profile so all 23 tools stay eager.
- **Confirmation:** all four categories produced a ticket on the first attempt afterwards.

### 4. Stack processes killed by tool-call cancellation (fixed 2026-11-17)
- **Symptom:** BFF and gateway died during testing; `bff.err.log` ended with `^C`.
- **Cause:** processes created through `Win32_Process.Create` still share the launching shell's console, so cancelling any shell call delivered Ctrl+C to the whole group. A stale `.pgdata/postmaster.pid` (pid recycled by another program) also made the database look up while the port was closed.
- **Fix:** start both through detached launchers (`DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`), and delete the stale pid file only after confirming no `postgres.exe` is running.

## Data integrity notes

- `append_simulated_test_order` accepts only `sku`, `quantity`, `scenario_id`; it does not store a tester name and always writes `Nama = SIMULASI WHATSAPP TEST - DO NOT FULFILL`. This is by design (prevents free-text writes to the sheet), and Siti reported it accurately to the tester.
- The recommended catalogue item (Leather Collar Oversized Boxy Jacket, BEIGE, IDR 359,900, observed 2026-11-09) and the sample-stock SKU 10445702332674 (Oversize Collared Leather Jacket, DARK RED, FS, sample stock 25) are **different product records** and were never joined.
- All stock figures are sample/simulated values, not verified Colorbox inventory.

## What is still required before Day 4–5 is complete

1. **Blocked source (CS/ops):** an authoritative order-status feed (a `Status` column in the Orders sheet or a status API). Without it `WA-STATUS-01` cannot be tested and `WA-CANCEL-01` can only confirm the policy, never a cancellation. The cancellation policy itself is no longer a blocker — it is sourced from `https://colorbox.co.id/pages/ketentuan-layanan` and recorded in `sop_colorbox_cancellation_v1.md`.
2. **Human handoff (CS/ops):** owners per category (refund, discount, dispute, cancellation). The `Handover` tab and its Apps Script `/exec` URL are live and verified, so tickets are already visible outside the local database. Ticket creation, validation and honest acknowledgement are already live.
3. **Done (2026-11-17):** the background-review leak is confirmed gone across four live conversations.
4. **Data gap (CS/ops):** the agent can only see a customer's WhatsApp display name, not their number, so `Kontak` is empty on every ticket. Options: ask the customer to state the number, or pass the sender JID from the bridge.
5. **Video demo recording:** live WhatsApp walkthrough of product recommendation, sample stock lookup, simulated order creation, and the four policy/guardrail replies. Do not record other private chats, phone numbers, or session data.
6. **Final CS MVP workflow doc:** assemble this report with the Sprint 2 SOPs, the source register, and the sanitized conversation evidence.
7. **Handover tab tidying:** delete the four stale test rows (`RETEST`, `HW-20261115-FE38CA`, `PROBE-HANDOVER`, `HW-20261116-BF32B1`) so the tab shows only real validation tickets.

## Reproducible commands used

- Stack: `.\start-all.ps1` from `C:\Users\MI\Documents\pegawai-ai-backend`
- Backend suite (earlier run, unchanged code): 144 passed, 6 deselected
- Order readback: `GET /api/data/orders/test/TEST-WA-20261115-CEC303` with `x-pegawai-ai-key`
