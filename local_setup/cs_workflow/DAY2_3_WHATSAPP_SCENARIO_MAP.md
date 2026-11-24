# Day 2-3 WhatsApp Setup and Scenario Evidence

**Recorded:** 2026-11-13 (Asia/Jakarta)  
**Scope:** Shared Day 2–5 WhatsApp scenario work; continue the same scenario IDs without duplicating implementation.  
**Evidence handling:** No customer messages were sent. No WhatsApp token, linked-device session, or customer's phone number is stored here.

## Setup and source access

| Item | Observed state | Evidence / limit |
|---|---|---|
| WhatsApp demo line | Company-provided demo number paired to Hermes Baileys under the `siti` profile on 2026-11-13; tester access approved | Live test: tester sent `hello`; Siti replied with an Indonesian greeting. Sanitized; no phone number or session credentials recorded. This is an unofficial WhatsApp Web bridge with accepted account restriction risk, not the official Business Platform. |
| Stock spreadsheet | Connected and verified; 70 data rows; headers `SKU, Nama, Kategori, Ukuran, Warna, Stok, Harga` | [Stok Demo](https://docs.google.com/spreadsheets/d/1q5qri13EvnWywYvXwEdHElhOreOazfXvYDID-gm8FfI/edit?usp=sharing). It contains sample counts, not verified Colorbox inventory. |
| Orders spreadsheet | Connected and verified; headers `Tanggal, Order ID, Nama, SKU, Qty, Total` | [Orders](https://docs.google.com/spreadsheets/d/1EFDTTbyB5RNoCsIJSlyInZySPhmt2E1AcI48BuDLvBg/edit?usp=sharing). No `Status` column. The Apps Script writer URL is intentionally omitted because it grants write access. |
| Catalogue | Local catalogue search returned a dated public record | `Leather Collar Oversized Boxy Jacket`, IDR 359,900, observed 2026-11-09; `SRC-02`, [official product page](https://colorbox.co.id/products/leather-collar-oversized-boxy-jacket-beige-26f). This is a dated listing, not a live price or stock guarantee. |
| CS policy package | Supplied v2.1 instructions and knowledge are the authority for tested policy responses | See `COLORBOX_CS_Instructions_v2_1.md`, `COLORBOX_CS_Knowledge_v2.json`, and `COLORBOX_CS_Source_Register_v1.csv` in the supplied handover package. Every response is an internal draft; human review is required. |

## Scenario map and Day 2 results

| ID | Scenario | Source / required control | Day 2 result | Day 3 continuation |
|---|---|---|---|---|
| `WA-PRODUCT-01` | Product explanation and recommendation | Dated catalogue record; cite the product URL; no unsupported attributes or current-price promise | BFF catalog tool smoke test returned 3 `leather jacket` results with SRC-02 links and observation dates. First result: Leather Collar Oversized Boxy Jacket, IDR 359,900, observed 2026-11-09. **PASS for tool lookup; WhatsApp response still pending.** | Tester sends a product recommendation prompt; record the exact reply and its catalogue references. |
| `WA-STOCK-01` | Stock lookup | Connected demo sheet; sample data must be labeled simulated; a missing row is not proof of zero stock | BFF stock tool read all 70 rows and matched SKU `10445702332674`: Oversize Collared Leather Jacket, DARK RED, FS, sample stock 25, sample price IDR 509,915. This does not match the catalog item above (different name/color/SKU context); do not join the records. **PASS for tool read; WhatsApp response pending; no live availability claim.** | Tester asks for that exact SKU and checks the answer labels it simulated. Also test a missing SKU. |
| `WA-ORDER-01` | Create an order | Orders sheet + Apps Script append; explicit confirmation required before any real customer write | Prior Day 1 evidence verified one `TEST-20261113-01` row. New WhatsApp tool is restricted to append a fixed-name `TEST-WA-*` simulated row, but it has not yet been called. **PASS for prior backend write; WhatsApp test-order write pending.** | Tester explicitly requests a simulated test order; verify its new row by exact test ID. Do not duplicate Day 1. |
| `WA-STATUS-01` | Tell customer an order is processed, shipped, or delivered | Requires an authoritative status source and a supported outbound channel | **BLOCKED:** the connected sheet has no status column or status feed. The tool reports status unavailable; do not invent or send a status. WhatsApp is paired for supervised testing. | Requires an approved status source. |
| `WA-CANCEL-01` | Cancel an order | Requires approved cancellation policy and a live order check | **BLOCKED:** the supplied sources establish neither cancellation conditions nor a live order lookup. No cancellation was attempted. | CS must supply the policy and order source; test eligible/ineligible cases without changing real orders. |
| `WA-DISCOUNT-01` | Special discount | Human approval; no discount promise before approval | **MAPPED, NOT TESTED:** no discount approval workflow or named approver/queue is configured. The assistant must not offer or apply a discount. | Add a named human approval path, then test approved and declined outcomes. |
| `WA-REFUND-01` | Refund request | P1 human review; no approval, processing-time, or method claim | Existing `CB-CS-V02`, `CB-CS-V03`, and `DEMO-B/C` evidence covers policy-grounded drafts. Reviewed policy: wrong article/color or defective/damaged item may be returned within 7 days; case eligibility and refund method/time remain unknown. **PASS for draft/escalation recommendation only; no refund action or actual handoff.** | Reuse the same policy scenarios and verify the customer draft remains noncommittal. |
| `WA-DISPUTE-01` | Serious dispute | Human review; do not claim a case was forwarded or assigned | **MAPPED, NOT OPERATIONALLY HANDED OFF:** the CS contract permits only `recommendation_only`; no queue, owner, or ticket endpoint exists. | Test a serious-dispute prompt and record the recommendation. A real handoff requires an approved queue and owner. |

## Implementation and evidence status

- Added test-mode-only stock context in `bff/bff/sheets.py` and `bff/bff/engine.py`. It includes rows only for explicit stock questions, labels values as sample/simulated, and says an absent match is not zero stock. Non-test CS runs do not receive the demo sheet data.
- Added focused tests in `bff/tests/test_sheets.py` and `bff/tests/test_retrieval.py`.
- Existing scenario corpus and results remain authoritative: `COLORBOX_CS_Test_Corpus_v2.json`, `COLORBOX_CS_Test_Results_v2_1.csv`, `COLORBOX_CS_Demo_Scenarios_v2_1.md`, and `evidence/run_20261109_v2_1/`.
- Siti's local Hermes guidance was corrected to identify Colorbox and use bounded data tools. A local MCP server now exposes catalog search, simulated stock lookup, a test-only order append/readback, status-source check, and policy blocker check. Five tools were registered to Siti; the gateway was restarted and port 8642 is listening.
- Local tool smoke tests passed: catalog search returned dated SRC-02 products; the stock tool returned 70 rows and the exact sample SKU; status check reported no status source; policy blocker check reported that no human review queue/recipient is configured. The catalog result and stock row are not the same product. No new test order has been appended through this tool.
- Backend test suite after the changes: **144 passed, 6 deselected**. This validates the BFF code, not live WhatsApp behavior.
- WhatsApp setup and basic chat were verified earlier: tester `hello` received a reply, which incorrectly identified Siti as “Top Trends.” The profile guidance has since been corrected; a tester identity check is now pending. The optional home-channel prompt was skipped.
- No refund, cancellation, discount, status update, or actual human handoff was performed. These remain untested or blocked integrations.
- This is supervised demo/test scope only. The supplied CS instructions require internal drafts and human review; they do not authorize sending replies to customers.

## Day 3–5 continuation

Continue the existing IDs above; do not reimplement or duplicate Day 1. First verify the corrected Colorbox identity over WhatsApp. Then test `WA-PRODUCT-01` and `WA-STOCK-01`, one prompt at a time. After that, explicitly request a simulated `WA-ORDER-01` and verify its new `TEST-WA-*` row. The MCP data tools were smoke-tested locally; WhatsApp must still confirm that Siti calls them and explains their results correctly. Leave status updates and cancellations blocked until source data/policy is supplied. Discounts, refunds, and serious disputes currently have no human queue or recipient, so responses can only state that review is needed; do not claim a handoff or human receipt. Day 4–5 video capture remains pending; do not record other private chats or expose phone numbers/session data.

## Live WhatsApp retest — 2026-11-13

- `WA-PRODUCT-01`: Actual WhatsApp prompt asked for a Colorbox leather-jacket recommendation. Siti returned the dated catalogue item *Leather Collar Oversized Boxy Jacket*, linked `SRC-02`, stated the catalogue observation date (2026-11-09), distinguished a leather-collar jacket from a fully leather jacket, and warned the listed price may change. **Content: PASS, subject to source verification of displayed sizes.**
- **Presentation defect:** Before the final answer, WhatsApp displayed internal progress/tool text (skill lookup, file search/read, tool search, and tool call). Treat this as a failed customer-facing presentation; hide tool traces before the next demo. The final answer itself was useful and appropriately caveated.
- **Next:** Test `WA-STOCK-01` only with the sample sheet SKU `10445702332674` (Oversize Collared Leather Jacket, DARK RED, FS). Require Siti to label any result as simulated/sample stock. Do not treat this row as inventory for the recommended BEIGE catalogue product; they are different product records.

## Presentation defect fix — 2026-11-15

- **Cause:** Hermes' per-platform tool-progress display. The WhatsApp adapter registers `display_tier="medium"`, which resolves `tool_progress` to `new` — one progress line posted every time the active tool changes. These are operator display lines built from tool names/arguments (`📚 skills_list`, `🔎 Searching files for …`, `⚙️ mcp__colorbox_cs_demo__…`), not model-authored customer text.
- **Change:** In the `siti` profile config, added `display.platforms.whatsapp`: `tool_progress: "off"`, `interim_assistant_messages: false`, `long_running_notifications: false`, `show_reasoning: false`. Backup: `config.yaml.bak-20261115`.
- **Verified:** Config parses and resolves `("off", True)`, interim `False`, long-running `False`; the `api_server` surface is unchanged at `("all", False)` so internal chat keeps its trace. Hermes reloads config per turn on file change, so no restart was needed.
- **Live confirmation pending:** send one WhatsApp prompt and confirm only Siti's answer arrives, with no `📚`/`🔎`/`⚙️` lines.

## Live WhatsApp validation - 2026-11-15 (Day 4-5)

Full detail: `DAY4_5_WHATSAPP_VALIDATION_REPORT.md` (same folder).

| ID | Result |
|---|---|
| `WA-STOCK-01` missing SKU | PASS - "tidak ditemukan", missing != zero stock, sample labeled |
| `WA-ORDER-01` | PASS - created `TEST-WA-20261115-CEC303`, row independently read back from the Orders sheet |
| `WA-REFUND-01` | PASS - no approval/method/timeline promise, 7-day window cited, human review stated, no handoff claimed |
| `WA-DISCOUNT-01` | PASS - no discount promised or applied, approval flow stated unavailable |
| `WA-DISPUTE-01` | PASS - "belum diteruskan", no false forwarding claim |
| `WA-STATUS-01` / `WA-CANCEL-01` | BLOCKED - no status source / no approved cancellation policy |
| Human handover | RECOMMENDATION ONLY - no queue or recipient configured |

**Tool-trace leak:** fixed and confirmed live on these replies (no tool lines before answers).
**Second leak found:** `Self-improvement review: User profile updated . Memory updated` posted as a separate WhatsApp message. Cause: post-turn background review summary delivered as platform status text. Fixed with `auxiliary.background_review.enabled = false` in the `siti` profile (reads back `false`). Test-chatter written into `profiles/siti/memories/USER.md` was cleared; backup `USER.md.bak-testchatter-20261115`. Live confirmation of this second fix still pending.
