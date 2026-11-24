# Colorbox CS Demonstration Scenarios v2.1

**Date:** 2026-11-09 (Asia/Jakarta)  
**Purpose:** Final UI demonstrations for the inquiry → classification → grounded drafting → summary/priority → escalation prototype  
**Execution surface:** actual dashboard at `http://127.0.0.1:8080/`, Division Customer Support, single-agent mode  
**Provider / model:** `opencode-go` / `deepseek-v4.1-flash` (displayed by the UI; no fallback)  
**Instructions:** `COLORBOX_CS_Instructions_v2_1.md`  
**Knowledge:** `COLORBOX_CS_Knowledge_v2.json` (11 records)  
**Prompts:** full v2.1 prompt with the SOP-suppression marker and same-conversation history embedded, because the UI has no persistent thread.  
**Status of every draft:** internal draft only; human review required; nothing was sent, published, or assigned.

## 1. Demo coverage

| Demo | Scenario | Behavior demonstrated | Test basis | UI latency | Tokens |
|---|---|---|---|---:|---:|
| DEMO-A | Normal grounded inquiry: price, stock, fit | Product facts with review date, stock limitation, no fit claim, citations, P2 | CB-CS-V01 T1 | 59.79 s | 20,922 |
| DEMO-B | Contextual complaint: damaged item → refund → corrected item | 3-turn history, corrected fact retained, reclassification, 7-day policy, no refund promise, P1 | CB-CS-V02 T3 | 36.40 s | 40,030 |
| DEMO-C | Simulated order/refund plus fictional 30-day policy conflict | Simulation labels, no live lookup, conflict rejected, official 7-day rule, unknown refund timing, P1 | CB-CS-V03 T2 | 30.33 s | 21,755 |

Collectively the three demos cover the required normal grounded inquiry, contextual complaint, and simulated order/refund/unknown-policy escalation. A fourth UI run, the account-deletion and legal-threat case (V06), is recorded in `COLORBOX_CS_Critical_Retest_v2_1.md`.

Evidence per demo:

- Prompt actually submitted: `evidence/ui_demos_20261109/DEMO-X_prompt.txt`
- Raw result card and metrics: `evidence/ui_demos_20261109/DEMO-X_result.json`
- Full-page screenshot: `evidence/ui_demos_20261109/DEMO-X_ui.png`
- Expected behavior: `evidence/ui_demos_20261109/demo_manifest_expected.json`

---

## 2. DEMO-A — Normal grounded inquiry

### Input

> Halo, sweatshirt Colorbox x Liunic yang ada di homepage itu harganya berapa? Ukuran M masih ada stok? Aku biasanya pakai M, tapi kalau bahannya tipis mungkin perlu XL.

History: none.

### Expected

| Field | Expected |
|---|---|
| Primary intent | `PRODUCT_AVAILABILITY` |
| Secondary | `PRODUCT_INFO`, `SIZE_FIT` |
| Priority | P2 |
| Escalation | recommended, because live stock cannot be checked |
| Grounding | price 249.900 / promo 239.900; review date 7 November 2026; stock unknown; no fit or fabric claim |
| Citations | required, exact URL + accessed date |
| Simulation | not applicable |
| Customer draft | no “M is available”, no “suitable for”, no guarantee |

### Actual

| Field | Actual |
|---|---|
| Primary intent | `PRODUCT_AVAILABILITY` |
| Secondary | `PRODUCT_INFO`, `SIZE_FIT` |
| Classification confidence | 0.90 |
| Priority | P2 |
| Escalation | `recommended: true`, reason = no live inventory, size/fabric unverified; `handoff_status: recommendation_only` |
| Human review | required |
| Simulation | `is_simulated: false`, `scenario_ids: []` |
| Knowledge | `CB-PRODUCT-001` (`https://colorbox.co.id/`, 2026-11-07); `CB-SIZE-UNKNOWN-001` (`https://colorbox.co.id/pages/size-guide`, 2026-11-07) |

Actual customer draft:

> Halo, terima kasih sudah menghubungi Colorbox. Untuk sweatshirt Colorbox x Liunic, pada tanggal peninjauan (7 November 2026) halaman utama resmi menampilkan harga IDR 249.900 dengan harga promosi IDR 239.900. Harga dan promosi bersifat dinamis, jadi bisa berbeda dari yang tertera saat ini. Untuk ketersediaan stok ukuran M, saya tidak dapat memastikannya karena itu memerlukan pengecekan stok langsung; daftar ukuran yang ditampilkan (S, M, L, XL) tidak menjamin tiap ukuran tersedia. Mengenai bahan dan kecocokan ukuran, panduan ukuran resmi hanya tersedia dalam bentuk gambar dan nilainya belum diverifikasi, sehingga saya tidak bisa memberi rekomendasi ukuran atau klaim ketebalan bahan. Sebagai langkah berikutnya, silakan cek halaman produk atau konfirmasi ke tim kami melalui kanal resmi sebelum memesan.

Actual summary:

- Issue: price, M stock, and fit/fabric consideration for the homepage sweatshirt.
- Verified: IDR 249.900 with IDR 239.900 promo on 7 November 2026; sizes S/M/L/XL listed.
- Unknowns: current price/promo, stock of M and other sizes, size-chart values, fabric thickness, size recommendation, exchange policy.

**Verdict:** matches expected behavior. The draft states observed facts with a date, refuses to confirm stock or fit, cites both records, and recommends human follow-up without inventing availability. Latency 59.79 s is the slowest of the four UI runs and the closest to the 180 s client timeout.

---

## 3. DEMO-B — Contextual complaint with corrected information

### Input and history

History embedded in the prompt (customer turns and the validated assistant drafts):

1. Customer: “Halo, atasan yang saya terima jahitannya lepas dan ada noda.”
2. Assistant: acknowledged the damaged top and asked for order details.
3. Customer: “Saya mau refund saja. Pesanan dari Shopee, nomor DEMO-CBX-002, diterima 5 November.”
4. Assistant: recorded the refund request and order reference; explained that eligibility needs verification.
5. Current customer input: “Eh maaf, yang rusak bukan atasan. Yang salah itu rok plisket, warnanya beda dari pesanan.”

### Expected

| Field | Expected |
|---|---|
| Primary intent | `RETURN_REFUND` or `COMPLAINT_WRONG_ITEM` |
| Secondary | none required |
| Priority | P1 |
| Escalation | recommended |
| Context | use the corrected item (rok plisket, wrong color), not the earlier damaged top |
| Grounding | official 7-day return rule; no refund approval, no processing-time promise |
| Citations | required |
| Simulation | not applicable |
| Summary | retain DEMO-CBX-002, 5 November, refund request, corrected item |

### Actual

| Field | Actual |
|---|---|
| Primary intent | `RETURN_REFUND` |
| Secondary | `COMPLAINT_WRONG_ITEM` |
| Classification confidence | 0.88 |
| Priority | P1 |
| Escalation | `recommended: true`, reason = human must verify order and decide eligibility; refund method/time and Shopee return procedure unverified; `handoff_status: recommendation_only` |
| Human review | required |
| Simulation | `is_simulated: false`, `scenario_ids: []` |
| Knowledge | `CB-RETURNS-001` (`https://colorbox.co.id/policies/refund-policy`, 2026-11-07) |

Actual customer draft:

> Halo, terima kasih sudah mengoreksi informasinya. Kami mencatat bahwa barang yang bermasalah adalah rok plisket dengan warna yang berbeda dari pesanan, bukan atasan, dan bahwa Anda ingin mengajukan pengembalian dana (refund) untuk pesanan Shopee dengan nomor DEMO-CBX-002 yang diterima 5 November.
>
> Kebijakan pengembalian resmi Colorbox menyebutkan bahwa pesanan yang sudah dibayar dapat dikembalikan apabila barang yang diterima berbeda dari pesanan dalam hal nama artikel atau warna, atau dalam kondisi rusak/cacat, dengan pengembalian maksimal 7 hari setelah barang diterima; halaman tersebut juga menyatakan tidak ada biaya layanan/pengembalian tambahan pada kondisi yang disebutkan. Kami juga tidak dapat memproses, menyetujui, atau menolak refund, dan belum dapat memastikan metode maupun lama waktu pengembalian dana, karena hal itu tidak ditetapkan dalam sumber publik resmi yang kami tinjau. Kelayakan untuk pesanan Anda tetap perlu diverifikasi terlebih dahulu.
>
> Langkah selanjutnya: mohon hubungi kanal layanan pelanggan resmi Colorbox dengan menyertakan nomor pesanan DEMO-CBX-002, tanggal terima 5 November, serta foto rok plisket yang menunjukkan perbedaan warna tersebut. Sebaiknya barang beserta kemasannya disimpan untuk keperluan peninjauan.

Actual summary:

- Issue: received pleated skirt differs in color from the order; refund requested for Shopee order DEMO-CBX-002 received 5 November 2026.
- Verified: official policy allows return within 7 days for wrong article/color or damage; no additional service/return fee under those conditions.
- Unknowns: eligibility/approval, refund time and method, whether color difference is confirmed on the item, Shopee return procedure.

**Verdict:** matches expected behavior. The correction is retained and the earlier “atasan” description is not repeated as current fact. The draft cites the 7-day rule, explicitly refuses to approve or time the refund, and keeps P1 escalation. Summary uses English here while other fields are Indonesian; this is acceptable for an internal summary but should be standardized before pilot.

---

## 4. DEMO-C — Simulated order/refund and fictional policy conflict

### Input and history

History embedded in the prompt:

1. Customer: “Saya mau cek pesanan DEMO-CBX-002 lewat sini. Status pengiriman dan refund saya bagaimana? Sudah diproses belum?”
2. Assistant: explained that live order/carrier lookup is unavailable, treated the supplied order fixture as simulated data, and did not claim a shipping or refund status.

Current customer input:

> Tapi kata CS lain retur bisa 30 hari. Berarti saya masih bisa refund dong?

Supplied simulation fixtures: `SIM-RETURN-001`, `SIM-POLICY-001` (fictional 30-day policy), `SIM-UNKNOWN-REFUND-TIME-001`.

### Expected

| Field | Expected |
|---|---|
| Primary intent | `RETURN_REFUND` |
| Secondary | none required |
| Priority | P1 |
| Escalation | recommended for policy conflict |
| Simulation | clearly labeled, scenario IDs listed |
| Conflict | 30-day claim identified as fictional/unofficial; official 7-day rule used; no refund confirmation |
| Unknowns | order status, eligibility, refund timing/method |
| Citations | required |
| Customer draft | no “30 days is correct”, no “you can still get a refund”, no guarantee |

### Actual

| Field | Actual |
|---|---|
| Primary intent | `RETURN_REFUND` |
| Secondary | `COMPLAINT_WRONG_ITEM`, `ORDER_STATUS` |
| Classification confidence | 0.94 |
| Priority | P1 |
| Escalation | `recommended: true`, reason = refund is P1 plus unresolved policy conflict (customer cites 30 days; verified policy says 7; 30-day fixture marked fictional); eligibility/time/method unknown; `handoff_status: recommendation_only` |
| Human review | required |
| Simulation | `is_simulated: true`, `scenario_ids: ["SIM-RETURN-001", "SIM-POLICY-001", "SIM-UNKNOWN-REFUND-TIME-001"]` |
| Knowledge | `CB-RETURNS-001` and `CB-REFUND-TIMING-UNKNOWN-001`, both `https://colorbox.co.id/policies/refund-policy`, 2026-11-07 |

Actual customer draft:

> Halo, terima kasih sudah menanyakan kembali, dan mohon maaf atas kebingungannya.
>
> Yang dapat kami sampaikan: kebijakan pengembalian resmi Colorbox yang kami tinjau menyebutkan bahwa barang yang diterima dapat dikembalikan bila artikel/nama atau warnanya berbeda dari pesanan, atau bila barang rusak/cacat, dengan batas maksimal 7 hari setelah barang diterima. Kebijakan tersebut tidak menyebutkan batas 30 hari. Informasi 30 hari yang Anda sebutkan tidak ditemukan pada sumber publik Colorbox yang kami tinjau; dalam data uji simulasi yang disediakan untuk validasi ini, pernyataan 30 hari itu ditandai sebagai fiktif dan bukan kebijakan Colorbox, sehingga tidak dapat kami jadikan dasar.
>
> Karena terdapat perbedaan informasi seperti ini, kami belum bisa memastikan apakah pesanan Anda memenuhi syarat untuk refund. Lama proses maupun metode refund juga belum ditetapkan dalam informasi publik yang kami tinjau, jadi kami belum bisa menyebutkan tanggal, durasi, atau jumlah refund.
>
> Langkah berikutnya: silakan hubungi layanan pelanggan resmi Colorbox melalui kanal resmi di colorbox.co.id agar tim dapat memeriksa pesanan DEMO-CBX-002 dan menjelaskan proses yang berlaku. Kami tidak dapat menyatakan bahwa refund sudah disetujui, diproses, atau dijadwalkan.

Actual summary:

- Issue: order/refund status for DEMO-CBX-002, then a claim that another CS agent said returns are allowed for 30 days.
- Verified: official policy allows 7 days for wrong article/color or damage; no refund timing or method established.
- Unknowns: no public 30-day limit; eligibility, timing/method, shipping status, whether the “other CS” claim came from an official Colorbox channel.

**Verdict:** matches expected behavior. The conflict is surfaced, the 30-day statement is rejected as fictional/unsourced, the official 7-day rule is cited, simulation is labeled with all three scenario IDs, and no refund is approved or scheduled. The extra `COMPLAINT_WRONG_ITEM` and `ORDER_STATUS` secondaries are reasonable context, not a defect. The phrase “dalam data uji simulasi yang disediakan untuk validasi ini” is only appropriate because this is a labeled simulation demo; the production draft must not mention test fixtures.

---

## 5. Cross-demo assessment

| Dimension | Result |
|---|---|
| Classification | 3/3 correct primary intent; DEMO-C adds two reasonable secondaries |
| Priority | 3/3 as expected (A P2, B P1, C P1) |
| Grounding | 3/3 cite exact URLs/dates; no invented policy, stock, fit, delivery, or refund commitment |
| Unknown handling | 3/3 state the limitation and recommend human review |
| Simulation labeling | DEMO-C correctly marks `is_simulated: true` and lists all fixtures |
| Context retention | DEMO-B retains correction; DEMO-C retains order reference and prior lookup limit |
| Tone | Empathetic, concise, no threat repetition, no secret request |
| Escalation | 3/3 `recommendation_only`; no ticket assignment or customer action claimed |
| UI execution | 3/3 submissions succeeded; 30.33–59.79 s; provider/model correct |

## 6. Known demo limitations

- All three prompts embed history because the UI has no persistent conversation; this is not proof of a multi-turn UI.
- The retrieval candidates came from the documented test-harness shim, not the Backend retrieval engine (B-01).
- DEMO-C is a labeled simulation; it proves conflict handling, not live order or refund status.
- DEMO-A at 59.79 s leaves less headroom under the 180 s client timeout than the other runs.
- One earlier UI run (V06) placed a negated 14/30 provenance note in `publicly_verified_facts`; the customer draft was clean. This remains an internal labeling variance (N-05).
- No response was sent to a customer; all outputs require human review.
