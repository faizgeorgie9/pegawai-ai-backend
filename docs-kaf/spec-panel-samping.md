# Spec: side panel, visible thinking, token limits (4 November 2026)

This builds on `docs/bff-spec.md` and `docs/frontend-spec-tahap2-5.md`. Read those and the current code first.

## Why thinking is not visible today (verified in Hermes source)

- `/v1/runs` passes no `reasoning_callback` to the agent (`gateway/platforms/api_server_runs.py`, `_execute_run`).
- The fallback event `reasoning.available` is suppressed whenever the provider streams native reasoning, which DeepSeek does (`agent/turn_response_intake.py:150-153`, flag set in `agent/stream_delivery.py:376`). So no thinking ever arrives on the run stream.
- `/v1/chat/completions` does stream `reasoning_content` live, but its run cannot be stopped or steered: no `active_run_id` is passed, so `/v1/runs/{id}/stop` finds no agent.
- **Decision:** keep the Runs API, because real stop and steer matter more. Thinking is shown **per step**, not per token.
  - While a run is going, the BFF polls `GET /p/<bot>/api/sessions/{session_id}/messages` every 2 s.
  - Every new assistant message's `reasoning` (or `reasoning_content`) is pushed as a `reasoning {text, step}` SSE event on `/api/runs/{id}/stream`. A `group_reasoning {group_id, bot_id, run_id, text}` event goes on `/api/events`.
  - Concatenate it into `runs.reasoning`.
- First verify empirically with one short web-search run whether Hermes persists intermediate assistant messages before the turn ends. If it persists only at the end, the poll still delivers thinking right when the turn completes. Keep the poll anyway, because it costs nothing, and record the result in `docs/bff-spec.md` under "Verified".
- Write a short Indonesian explanation of this limit in `docs/keputusan-frontend.md` under stage 1 or 2.

## Token limits

- The group per-send budget becomes optional: `plans.group_send_token_budget` NULL means no limit, and the default for all seeded plans becomes NULL (migration `002_*.sql`).
- The round and message caps (3 rounds, 10 bot messages) stay. They are the Hermes Desktop rules, and they already stop runaway discussions.
- `plans.monthly_tokens` NULL also means no limit. Set `bisnis` to NULL; gratis and pro keep their numbers.
- The UI shows "Tanpa batas" for a NULL limit.
- Update docs (`keputusan-frontend.md` stage 3 and 4, and `bff-spec.md`).

## Usage API (BFF)

- `GET /api/usage?session_id=…` or `?group_id=…` returns:
  - `{total: {input, output, cache_read, total, runs}, by_bot: [{bot_id, name, input, output, total, runs}], turns: [{run_id, bot_id, created_at, input, output, total, status}]}`
  - `turns` is newest first, limit 50.
- `GET /api/usage/bots?period=month|all` returns per-bot totals for the current user.
- Store `cache_read_tokens` from `usage` too: add a column if it is missing.

## Side panel (frontend)

Use the `design-taste-frontend` skill (app-screen rules) and the current visual language.

- In the header of the bot chat and the group chat, top right, add a row of icon buttons with tooltips and `aria-label`s. They work like a desktop app toolbar: the active icon is highlighted, and clicking it again closes the panel.

  | Icon | Tab | Content |
  |---|---|---|
  | brain / sparkle | **Berpikir** | Thinking for this conversation. Each bot turn is a collapsible block with the bot avatar and name, live-updating while the run is going ("Rian sedang berpikir…"), newest at the bottom, auto-scroll unless the user scrolled up |
  | gauge / chart | **Token** | This conversation: totals (input, output, cache, total), a per-agent breakdown as horizontal bars in each bot's colour, and a turn list. Below that, "Bulan ini" from `/api/usage/bots?period=month` and the plan meter, with "Tanpa batas" where the limit is null |
  | list / activity | **Aktivitas** | The tool log filtered to this conversation (reuse the Activity component with a filter) |
  | users / info | **Info** | Bot: role, team, persona summary. Group: members with status, plus rename and manage members |
  | more | menu | "Tutup panel" and "Buka halaman Aktivitas" |

- Desktop (1024 px and wider): the panel is resizable on the right (default 360 px, min 300, max 560), pushing the chat. Remember the open tab and width in localStorage, inside try/catch.
- Under 1024 px it is an overlay sheet from the right. Under 640 px it is full screen with a close button.
- Keyboard: Esc closes the panel, and the icons are reachable by Tab.
- The existing inline "Proses berpikir" block in bot chat stays, governed by the global toggle. In group chat, add a small "Lihat proses berpikir" link under each bot message that opens the Berpikir tab scrolled to that turn.
- Group typing row: while a bot is thinking, show "Rian sedang berpikir…"; when deltas arrive, show "Rian sedang mengetik…".

## Also do

- Add group delete to the UI, in the Info tab: "Hapus grup" with confirmation, calling `DELETE /api/groups/{id}`. It was missing.

## Acceptance

- `cd bff; uv run pytest` and `cd frontend; npm run build` pass.
- In the browser:
  - Send one web-search question to Rian. The Berpikir tab shows thinking (per step or at completion), and the Token tab shows that turn.
  - In a 2-bot group send, the Berpikir tab shows each bot's turn, and the Token tab shows a per-bot split.
  - With panel tab and width remembered, a reload restores them.
- Screenshots go to `frontend/screenshots/panel-*.png`: desktop with each tab, and mobile with the panel open.
