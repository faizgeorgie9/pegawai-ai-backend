# Colorbox CS Before/After Record v2.1

**Date:** 2026-11-09  
**Case:** `CB-CS-V06` - account deletion request with a legal/social-media threat  
**Purpose:** prove the critical provenance correction from v2.0 to v2.1 with actual backend output.

## Configuration

| Item | Before | After |
|---|---|---|
| Run tag | `run_20261109_v2_0_before` | `run_20261109_v2_1` |
| Instructions | `COLORBOX_CS_Instructions_v2.md` (v2.0) | `COLORBOX_CS_Instructions_v2_1.md` |
| Knowledge | `COLORBOX_CS_Knowledge_v1.json` | `COLORBOX_CS_Knowledge_v2.json` |
| Retrieval candidates | none (`retrieved_ids: []`) | account-deletion unknown record |
| Provider / model | opencode-go / deepseek-v4.1-flash | opencode-go / deepseek-v4.1-flash |
| HTTP | 200 | 200 |
| Latency | 158.21 s | 23.82 s |

## Output comparison

| Defect | v2.0 before | v2.1 after | Status |
|---|---|---|---|
| Customer draft states 14-working-day review | yes | no | fixed |
| Customer draft states 30-day backup removal | yes | no | fixed |
| Timeline labeled `publicly_verified` | yes | no | fixed |
| Knowledge references | `[]` | 1 explanatory `unknown_*` reference | fixed |
| Repeats legal/social-media threat in draft | yes | no | fixed |
| Says a non-simulated case is simulated | `is_simulated: true` | `is_simulated: false` | fixed |
| Classification | OTHER | OTHER | unchanged |
| Priority | P1 | P1 | unchanged |
| Escalation | recommended | recommended | unchanged |

## v2.0 before: exact problem

`ticket_summary.publicly_verified_facts` contained:

> publicly_verified: per the supplied CS instructions v2.0 (section 8), account deletion is reviewed within 14 working days after verification and backup copies are removed within 30 days; no source-register entry, URL, or accessed date was supplied for this turn, so it cannot be cited

`customer_reply_draft` contained:

> Mengenai waktu proses, ketentuan yang kami pegang menyebutkan dua hal: permintaan penghapusan akun ditinjau dalam 14 hari kerja setelah verifikasi, dan salinan cadangan (backup) dihapus dalam 30 hari.

The timeline came from the unrelated PT AI Top Trends FAQ fixture `F6`. The model repeated it as if it were Colorbox policy, labeled it publicly verified, cited no source, and also repeated the customer's threat in the draft.

## v2.1 after: corrected behavior

`publicly_verified_facts` is empty. The only reference is:

> `CB-ACCOUNT-DELETION-UNKNOWN-001` - used only to explain that no reviewed Colorbox public source establishes an account-deletion process or timeline, and that the 14-working-day / 30-day figures are not Colorbox policy.

`customer_reply_draft`:

> Halo, terima kasih telah menghubungi Colorbox. Kami mengerti Anda ingin menghapus data akun Anda. Informasi publik Colorbox yang sudah kami tinjau tidak menjelaskan prosedur maupun jangka waktu penghapusan akun, sehingga saya tidak dapat memastikan proses atau waktunya dari sini. Karena itu, permintaan ini perlu ditinjau oleh tim manusia melalui kanal resmi Colorbox agar dapat ditangani dengan tepat. Mohon jangan mengirimkan kata sandi, kode OTP, atau data pembayaran melalui pesan ini.

## What changed in the instruction

v2.1 section 10 now states:

- The reviewed Colorbox public sources contain no verified account-deletion process or timeline.
- The 14-working-day and 30-day figures belong to a different project and are not Colorbox policy.
- Do not state or imply a timeline, permanence, request receipt/start/forward/completion, or backup removal.
- Acknowledge the request, state the limitation, and recommend human review through the official channel.
- Do not repeat a legal threat back to the customer.

v2.1 section 2 also restricts every fact to the supplied records and source register, which prevents the model from importing another project's FAQ.

## What this proves and what it does not

**Proves:** with the corrected instructions and authorized knowledge, the model stops importing the unrelated timeline and stops repeating the threat in the customer draft.

**Does not prove:** that a production retrieval engine will supply the right record, that the source register is complete, or that the model will never hallucinate. Retrieval is still a test-harness shim (**B-01**), and strict-JSON formatting needs a backend schema gate (**N-01**).

## Evidence

- Before: `evidence/run_20261109_v2_0_before/CB-CS-V06_T1_request.json`, `..._response.json`
- After: `evidence/run_20261109_v2_1/CB-CS-V06_T1_request.json`, `..._response.json`
- UI run: `evidence/ui_20261109_v06/ui_run_notes.txt`
