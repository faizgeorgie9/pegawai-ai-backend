# Spec: a simple, light UI that is easy to understand (10 November 2026)

## What the owner asked for (the yardstick)
1. **Easy to understand.** Someone opening the app for the first time is not confused. Each screen answers one question, and each screen has one obvious next action.
2. **A clean, tidy colour scheme.** Light (white) is the default.
3. **Few options.** Remove or hide controls that are not needed for the main job.
4. **No overlap.**
   - Example: on the Beranda the status chips run out of their cards.
   - Nothing may overlap, get clipped, or spill out at any width: 1440, 1280, 1024, 768, 390.

The designer has full freedom, but only within these four points.

## Guide
- Skill: `D:\Programming\AITopTrends-Hermes\.claude\skills\design-taste-frontend\` (tasteskill v2.5.x).
- This is an **app screen**, so follow **`references/app-screens.md` in full**: read the whole file, including section 8 onward. The page run in SKILL.md does not apply.
- The skill's house rules still hold:
  - no gradients, no glass, no emoji, no eyebrows, no tiny uppercase labels;
  - no icons in tinted squares, no shadows on things at rest;
  - colour only on data, status and the one main action.
- Run, from the folder `D:\Programming\AITopTrends-Hermes\pegawai-ai-backend\frontend`:
  1. Record the "before": `node <skill>/scripts/inspect.mjs --app http://localhost:5173/ --out .taste-skill/before` (or the closest options), and `lint.mjs --app src`.
  2. Draw the style: `node <skill>/scripts/draw.mjs --app --kind <closest> --brief "Internal R&D tool for testing AI employees (Marketing and Customer Service) for Colorbox: chat, workflows, evaluation" --screens overview,list,detail,settings --theme light --options 3`.
     - Pick one style and write one line on why. A light, quiet style such as `achromatic-ledger` or `framed-sheet` probably fits, but decide on the evidence.
     - Then deal the sheet with `--style`.
  3. Build, then run `inspect.mjs --app` and `lint.mjs --app`. Fix every FAIL; treat each WARN as wrong unless you can defend it in one sentence.
  4. Look at the screenshots and critique them with the 7 questions in app-screens §2.7. Do up to 3 rounds.
  5. Run the final inspect on the production build (`npm run build` plus `vite preview`), into `.taste-skill/after`.
  6. Add `.taste-skill/` to `.gitignore` if it is not there yet.

## Simplification decisions (follow these, adapt the details)
1. **Theme.** Light (white) is the default. Keep dark mode only as an option that follows the system or the existing toggle; it is not the main focus but must not break.
   - One neutral ground, one ink, and **one accent**. The raspberry `#b8336a` may stay as the only accent, or follow the style, as long as there is one accent.
   - The accent goes only on the main action and the main data.
   - Contrast must be AA.
2. **Sidebar.**
   - Contents: the product mark and name ("Pegawai AI · Colorbox") and the group labels Kerja / Pengujian / Pengaturan in plain sentence case.
   - Items: Beranda, Chat, Grup, Marketing, Customer Service, Evaluasi, Log aktivitas, Agen, Kemampuan.
   - **The agent list and the group list move out of the sidebar** into the Chat and Grup pages. They make the sidebar long and confusing.
   - The active item is a neutral grey pill.
3. **Every page has a title (h1) plus one grey sentence about what it is for.** No other banners, legends or explanatory boxes on top.
   - Necessary explanations (data labels, "draf internal, tidak dikirim") become one short line or a small info icon with a tooltip.
4. **Beranda** answers: "What can I do here, and how is the system doing?"
   - At the top: 3 big, clear actions: Chat dengan agen, Jalankan alur kerja (Marketing/CS), Uji dan nilai (Evaluasi).
   - **Capability status** becomes a **simple list**, not chip cards:
     - each row is the name on the left and the status on the right;
     - chips are `flex:none; white-space:nowrap`, so they cannot overflow;
     - one set of status words: **Berfungsi / Simulasi / Nonaktif**.
   - **Update stale statuses:**
     - Customer Service follows CS v2.1 (`Berfungsi · perlu tinjauan manusia`, or similar).
     - Marketing uses the Colorbox knowledge and catalog.
     - Tools must not stay on "Memuat..." forever; give it a timeout or error state.
   - Recent activity: at most 5 rows, with "Lihat semua".
5. **Customer Service.**
   - Shown: agent select, the conversation, the question box, the result.
   - One "Contoh pertanyaan" control (a dropdown or short list) holding the official scenarios DEMO-A/B/C and a few V cases, taken from `scenarios.ts`. **Replace the old quick-pick chips** ("Ukuran XL", "Harga", ...).
   - One toggle: "Mode uji simulasi". Remove "Lihat contoh" (fixtures) from the main view, or tuck it away if it is still needed.
   - The CS v2.1 result card is ordered by importance:
     1. reply draft;
     2. intent and priority;
     3. escalation recommendation;
     4. ticket summary;
     5. sources;
     6. technical details (confidence, validation, raw JSON), folded by default.
6. **Marketing.**
   - The stages brief → rencana → konten → review → revisi are a clear stepper. The current stage is obvious, and there is one main button per stage.
   - "Sumber jawaban" is folded by default.
7. **Evaluasi.**
   - The default view: a list of cases (V, DEMO, TC, Preset Hub) with a simple group filter (Marketing / CS), then "Jalankan" on the selected case.
   - Compare and the experiment summary become clear tabs on the same page, not crammed together.
8. **Chat.**
   - The agent list is in the left column of the Chat page, grouped by team.
   - **CS chat history no longer shows raw JSON.** If an answer is CS v2.1 JSON, show the reply draft with a "Lihat detail" link to the card.
9. **Log aktivitas, Agen, Kemampuan:**
   - tidy tables per app-screens §7: no zebra, sentence-case headers, numbers aligned right;
   - at 390 px they become stacked cards;
   - Kemampuan stays at 3 tabs.
10. **The right panel (token/aktivitas/info):** keep it, but it is closed by default and does not cover content at any width.
11. **Copy:** short, plain Indonesian, in the product's own words. Delete sentences that explain the interface.

## Must not break
- Every route and old route: `#/tools`, `#/computer-use` and `#/scheduler` open the Kemampuan tab.
- Every function:
  - chat with history and thinking;
  - groups;
  - the Marketing and CS workflows (`workflow`, `stage`, `test_mode`);
  - multi-turn evaluation and the two rubric sets;
  - compare and summary;
  - creating, editing and deleting agents;
  - Indonesian validation;
  - the activity log;
  - the CS v2.1 card and its sources.
- The frontend never calls Hermes directly.
- No new dependencies unless they are truly needed (check `package.json`).

## Acceptance
- `npm run build` passes. `uv run pytest` in `bff/` passes.
- `grep -ri "8642\|HERMES_KEY\|API_SERVER_KEY" frontend/src` gives 0 hits.
- `inspect.mjs --app` on the production build shows **0 FAIL** at 1440, 768 and 390.
- An overflow check in the browser at 1440, 1280, 1024, 768 and 390 finds no element whose box spills out of its parent's or card's box on any route. Run it as a one-off script; do not add it to the repo.
- No console errors. Light and dark are both checked.
- Before and after screenshots: `frontend/screenshots/s3-ui-simple-before-*.png` and `-after-*.png`, for at least Beranda, CS, Evaluasi and Chat, at desktop and 390 px.
- Report:
  - the style dealt (name and seed) and why;
  - the face chosen;
  - the one question for each screen;
  - before and after inspect measurements;
  - what was removed or simplified.
