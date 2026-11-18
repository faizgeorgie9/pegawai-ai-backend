# Spec: Colorbox knowledge and CS v2.1 adjustment, one backend (10 November 2026)

## Sources
- `docs/sprint3/sumber/Shared_Business_Knowledge_Hub_Colorbox.docx` (text copy in `.txt`).
- `docs/sprint3/sumber/cs-handover-v2.1/`, the CS package v2.1 by Mansi:
  - `COLORBOX_CS_Instructions_v2_1.md`
  - Validation Report
  - Business Readiness
  - Demo Scenarios
- Runtime copies, which the BFF reads:
  - `bff/knowledge/colorbox/`: 10 knowledge files. The duplicates `brand-guidlines.md` and `product-katalog.md` were left out.
  - `bff/knowledge/cs-v2.1/`: instructions, knowledge JSON, source register CSV, dummy fixtures, test corpus.
- **Never edit the content of these files.** Ivana and Mansi own them. Read them as they are, including the "Â±" encoding glitch.

## Decisions
1. **One backend: the BFF** (FastAPI, Postgres, Hermes Runs API through the hardened gateway).
   - Faiz's server in `local_setup/backend_template/` (port 8080, it calls `hermes.exe` as a subprocess) leaves the run path. It stays in the repo as an archive.
   - Do not port its mock adapters (scheduler, WhatsApp/Email, Computer Use).
2. **CS follows v2.1. Where the Hub and v2.1 conflict, the stricter rule wins.** The conflicts are size table numbers, refund timing, and shipping ETA/Click & Collect.
   - CS runs get only the v2.1 authorized records: instructions, knowledge JSON and source register (rule 2 of the instructions).
   - The Hub CS files (`business-policies`, `product-size-reference`, `customer-faq`, `customer-inquiry-patterns`) are **not** injected into CS runs.
   - The conflicts are recorded for Ivana and Mansi. We do not resolve them.
3. **Marketing context:** `brand-profile`, `brand-guidelines`, `content-pillars`, `content-research` (Hub 3.2), plus products from the catalog.
4. **The BFF retrieves before the run.** It does not use agent tool calling, so we know exactly what context the agent got.
   - Provenance is exact.
   - Results are deterministic and testable.
   - The Hermes tool hardening stays.

   Upgrade path: a read-only MCP tool, if agents later need several searches in one answer.
5. **The catalog lives in Postgres**, not in a memory index.
   - The BFF searches it with structured filters (category, max price, colour, size) and Postgres text search.
6. **CS output is validated by a Pydantic model of the v2.1 schema.**
   - Use the model's native JSON mode if the Hermes Runs API supports `response_format` or similar. Check this in the Hermes source or docs first; do not guess.
   - Otherwise extract the JSON, validate it, and retry once automatically on failure (N-01).
   - Store the validation result.

## A. Backend (BFF)

### A1. Knowledge loader (`bff/bff/knowledge.py`)
- Load both folders at startup.
- **Marketing bundle:** the 4 files above, with their classification taken from the Hub matrix or `source-register.md`.
- **CS bundle:**
  - instructions v2.1 (the whole file is the base instruction);
  - the 11 records of `COLORBOX_CS_Knowledge_v2.json`;
  - the source register CSV.
- Choose the bundle from the bot's team: marketing gets the Marketing bundle, customer_support gets the CS bundle.
- Expose versions for audit:
  - `instructions_version="cs-2.1"`;
  - `knowledge_version`, taken from the JSON;
  - a file hash for the Marketing files.

### A2. Catalog in Postgres
- **Migration `006_products.sql`:** a `products` table with these columns:
  - id
  - category
  - name
  - price (int rupiah)
  - price_original (nullable; only if the table shows a discount)
  - colors
  - sizes
  - url
  - source (`SRC-02`)
  - accessed_date (`2026-11-09`)
  - a text-search column or index
- **Loader:**
  - Parse the markdown tables of `product-catalog.md`. Each `## n. Category` heading gives the category for its rows. There are 1,206 rows.
  - Load at startup only when the file hash changed, using a small `knowledge_meta` row or similar.
- **`search_products(query, category?, max_price?, color?, size?, limit=5)`:**
  - Exposed as `GET /api/products/search`, with the same auth as the other endpoints.
  - Also used internally before Marketing and CS runs.

### A3. Run context
- **The run endpoint accepts these optional fields:**
  - `workflow`: `"cs"` or `"marketing"`.
  - `stage`: for marketing.
  - `test_mode`: boolean. Only then are the `SIM-*` fixtures from `COLORBOX_CS_Dummy_Scenarios_v2.json` injected, clearly marked as simulation.
- The existing `instructions` passthrough stays, for backward compatibility.
- **When `workflow` is set, the BFF builds the instructions:**
  - the base instruction (v2.1 for CS; for marketing, the structured `pegawai-result` instruction the frontend sends today for the stage);
  - the knowledge bundle;
  - up to 5 products from `search_products` on the user input. For CS, products are dynamic data observed on 9 Nov 2026, and stock is unknown.
- **Store in `runs.meta`:**
  - `context_refs`: a list of `{type: "knowledge"|"product"|"fixture", id, title, classification, source_id, url, accessed_date}`;
  - `instructions_version`, `knowledge_version`;
  - `prompt_hash`: sha256 of the instructions plus the input;
  - latency and tokens, where available;
  - `validation`: `{status: "valid"|"repaired"|"invalid"|"not_applicable", errors: []}`.
- **CS structured result:**
  - Parse the agent output as v2.1 JSON and validate it with the Pydantic model, including these invariants:
    - `classification_confidence` is between 0 and 1;
    - `priority` is P0 to P3;
    - `handoff_status` is `recommendation_only`;
    - `human_review_required` is true;
    - every RETURN_REFUND is P1 with escalation recommended.
  - Store the validated object, for example in `runs.meta.structured`.
  - Return it with the run, through the SSE completion event or the run-detail endpoint, whichever fits the current engine. Document which.
  - A failed validation never hides the raw answer.
- **Escalation is a recommendation only.** When `escalation.recommended` is true, the run shows up in the activity log as "Rekomendasi eskalasi". Nothing is routed, and nothing says "escalated".

### A4. Hermes profiles
- **Back up** `rian`, `diana`, `budi`, `siti` and `hendra` (their SOUL and config) to the scratchpad first. **Never touch the profile `coder`.** Keep the hardening as it is (disabled toolsets, API key).
- **Update SOUL.md:**
  - The company context becomes Colorbox, not "AI Top Trends".
  - For siti and hendra, add a short pointer: follow the per-run CS v2.1 instructions, draft only, never claim to have escalated.
  - Use the BFF's own bot edit path if it covers SOUL; otherwise edit the files directly.
- **Do not run** `local_setup/setup_hermes_bots.py`. Add a header comment saying it is legacy and overwrites hardening.

### A5. Legacy 8080 cleanup
- Remove the PT AI Top Trends content: `context/sops/sop_*.md` with the `SOP-CS-AITT` code and the "< 15 detik" SLA, and the `company_name` in `config.example.yaml`. Replace each with a short pointer to `bff/knowledge/`.
- Add `local_setup/LEGACY.md`: superseded by the BFF on 10 Nov 2026, with a link to the new contract.
- Write the updated contract as one file: `docs/sprint3/kontrak-api-bff.md`. It covers the endpoints, the run fields, the CS v2.1 result and `context_refs`.

### A6. Tests (pytest, reusable)
- `tests/test_knowledge.py`:
  - the bundles per team;
  - the duplicates are absent;
  - there are 11 CS records;
  - every `source_id` in the records resolves through the register, except `unknown_*` records, which have none.
- `tests/test_catalog.py`: the parser gives 1,206 rows with categories and prices. Searching with filters needs a DB, so reuse the existing test DB approach if there is one; otherwise test the parser and SQL builder only.
- `tests/test_cs_schema.py`:
  - a valid sample built from the corpus or demo passes;
  - each invariant violation is rejected.
- `tests/live/test_cs_corpus.py`:
  - marked `live` and skipped by default (pytest marker in `pyproject.toml`);
  - runs V01–V06 through the BFF and asserts a valid schema and the expected primary intent and priority from the corpus.
  - **Do not run it in this task** except for at most one case, as a smoke test.

## B. Frontend
1. **`results.ts`:** add the CS v2.1 type and parser, taking the BFF structured result first. Old `kind:"cs"` records still render.
2. **CS card in `ResultCards.tsx`:**
   - primary intent and secondary intents, with confidence;
   - P0–P3 badge;
   - customer reply draft;
   - ticket summary in sections: customer reported, publicly verified, unknowns, references;
   - knowledge refs with a clickable URL and accessed date;
   - clarifying question;
   - "Rekomendasi eskalasi · perlu tinjauan manusia" with its reason;
   - simulation badge with the scenario IDs;
   - validation status badge.
   - The text "sudah dieskalasi" or "diteruskan" must never appear.
3. **`CS.tsx`:** send `workflow:"cs"`, and add a visible toggle "Mode uji simulasi (SIM-*)" for `test_mode`. Multi-turn keeps working. **`Marketing.tsx`:** send `workflow:"marketing"` and `stage`.
4. **`scenarios.ts`:**
   - CS cases are the corpus V01–V06, keeping their turns, plus DEMO-A/B/C from the demo file.
   - Add the 5 Hub preset scenarios, labelled "Preset Hub".
   - Marketing TC prompts use the real catalog product "Regular Fit Short Sleeve Graphic T-Shirt" (Rp 79.900), labelled "Public Data · 9 Nov 2026". The TC-05 promo stays DUMMY.
   - Remove the "Draf — menunggu Mansi" tags.
5. **Evaluation (`Uji.tsx`):**
   - Multi-turn cases send their turns in order in one session.
   - CS cases use a CS rubric with these 6 criteria from the Hub: Accuracy, Relevance, Brand Alignment, Knowledge Utilization, Anti-Hallucination, Escalation.
   - Marketing keeps its 9 dimensions.
   - The evaluation storage must accept both sets of rubric keys.
6. **Provenance:** a "Sumber jawaban" section in the right panel (Info tab) or under the answer, filled from `context_refs`. It shows the file or record, classification, URL and date, and the products used.
7. **Branding and labels:**
   - "AI Top Trends" in `App.tsx` and the Agents subtitle becomes Colorbox context.
   - Kemampuan: "Pencarian katalog dan knowledge (BFF)" is labelled Working. The labels of the other items are unchanged.

## C. Verification
- `npm run build` and `uv run pytest` (not the live tests) pass.
- `grep -ri "8642\|HERMES_KEY\|API_SERVER_KEY" frontend/src` gives 0 hits.
- In the built-in browser, run DEMO-A, DEMO-B and DEMO-C live in the CS workspace. Compare each with the "Expected" in the demo file. Record intent, priority, escalation, validation, latency and a screenshot.
- Run one Marketing stage live and check that `context_refs` shows the knowledge files and products.
- **Token cap: at most 8 live runs in total.**
- No console errors, desktop and 375 px, light and dark.

## Out of scope
- Resolving the data conflicts.
- CS approvals R-01..R-07.
- Editing the knowledge files.
- Ivana's and Mansi's tasks.
