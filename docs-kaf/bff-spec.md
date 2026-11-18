# BFF spec (stages 2-5)

Implementation spec for the Pegawai AI backend-for-frontend. Decisions and reasons: `docs/keputusan-frontend.md`. Hermes facts with source lines: `docs/riset/hermes-api-tahap2-5.md`. Read both first.

## 1. Shape

- Folder: `pegawai-ai-backend/bff/`. Python 3.12+, managed with uv (`pyproject.toml`, `uv.lock`). FastAPI + uvicorn, `httpx` (async, streaming), `psycopg[binary,pool]` 3 (async). No ORM. SQL migrations as plain `.sql` files applied in order at startup (a `schema_migrations` table records them).
- Binds `127.0.0.1:8090` only.
- Config from `bff/.env` (gitignored) with a committed `bff/.env.example`:
  - `DATABASE_URL`
  - `BFF_API_KEY`: the shared key the Vite proxy sends as `X-Pegawai-AI-Key`. Every `/api/*` request without it gets 401. Compare in constant time.
  - `HERMES_API_URL=http://127.0.0.1:8642`
  - `HERMES_HOME`: defaults to `%LOCALAPPDATA%\hermes`
  - `HERMES_BIN`: defaults to `hermes` on PATH
- Hermes key per bot: read `API_SERVER_KEY` from `<HERMES_HOME>/profiles/<bot>/.env` at call time (small parser, no logging of values). Never return or log any key.
- No login yet: every table has `user_id`. One seeded user `default` on plan `pro`. The current user is resolved by one function (`current_user()`), so login replaces only that function later.
- All user-facing error messages are in Indonesian, in JSON `{"error": "..."}`, with the right HTTP status.

## 2. Database

```sql
plans(id text pk, name text, max_bots int, max_groups int, monthly_tokens bigint,
      max_concurrent_runs int, group_send_token_budget int null, sort int)
-- monthly_tokens and group_send_token_budget are nullable: NULL means no limit (migration 002).
-- seed: gratis (3 bots, 1 group, 200_000 tok, 1 run, no per-send budget)
--       pro    (10, 5, 3_000_000, 3, no per-send budget)
--       bisnis (30, 20, no monthly limit, 8, no per-send budget)
-- runs also has cache_read_tokens int (migration 002), stored from usage.cache_read_tokens
users(id text pk, name text, plan_id text references plans, created_at timestamptz)
bots(id text pk /* = hermes profile name */, user_id text, name text, role text, team text,
     color text, template text null, persona text null, builtin bool, created_at, deleted_at null)
-- seed the five builtin bots (rian, diana, budi, siti, hendra) with name/role/team/color from frontend/src/team.ts
chat_sessions(session_id text pk, user_id, bot_id, created_at)  -- ownership of Hermes 1:1 sessions
runs(id uuid pk, hermes_run_id text, user_id, bot_id, session_id text, group_id uuid null,
     kind text /* chat|group */, status text /* queued|running|completed|failed|cancelled|interrupted */,
     input text, output text, reasoning text null, error text null,
     input_tokens int, output_tokens int, total_tokens int, last_seq int default 0,
     created_at, started_at, finished_at)
run_events(id bigserial pk, run_id uuid, seq int, type text, payload jsonb, created_at)
-- stores tool.*, approval.*, run.* events (redacted). message.delta is NOT stored per delta.
groups(id uuid pk, user_id, name, created_at, deleted_at null)
group_members(group_id, bot_id, position int, primary key(group_id, bot_id))
group_messages(id bigserial pk, group_id, author text /* user|bot|system */, bot_id null,
               text text, run_id uuid null, send_id uuid null, created_at)
group_cursors(group_id, bot_id, last_message_id bigint, primary key(group_id, bot_id))
group_sends(id uuid pk, group_id, message_id bigint, status text /* queued|running|done|stopped */,
            tokens_used int default 0, created_at, finished_at)
```

Add indexes for the obvious lookups: runs by (user_id, status) and (group_id), run_events by (run_id, seq), and group_messages by (group_id, id). On startup, delete `run_events` older than 90 days, then repeat daily.

## 3. Run engine (stage 2)

- `start_run(bot, session_id, input, kind, group_id=None, instructions=None)`:
  1. Check quota (section 6).
  2. Insert a `runs` row (status `queued`).
  3. `POST {HERMES}/p/<bot>/v1/runs` with `{"input", "session_id", "instructions"?}` and the bot's bearer key. Send an `Idempotency-Key` equal to our run id.
  4. Save `hermes_run_id` and set status `running`.
  5. Start one asyncio task that consumes `GET /p/<bot>/v1/runs/{hid}/events`.
- Consumer:
  - Parse frames: `id:` is seq, and the data JSON has `"event"`.
  - Update `last_seq`. Accumulate `message.delta` into memory, and flush `output` to the DB at most every 2 s and at the end.
  - Store `tool.*`, `approval.*` and terminal events redacted (section 7) in `run_events`.
  - On disconnect, reconnect with `Last-Event-ID: last_seq` with backoff (1, 2, 4 s, max 5 tries); after that, poll `GET /v1/runs/{hid}`.
  - On a terminal event, set status, output, tokens from `usage`, and `finished_at`.
  - Publish every event to an in-process pub/sub (section 5).
- Reasoning: `/v1/runs` streams no reasoning (see "Verified"), so while a run is going the BFF polls `GET /p/<bot>/api/sessions/{session_id}/messages` every 2 s (`engine.poll_reasoning`).
  - It finds the user message equal to the run input, and takes the `reasoning` / `reasoning_content` of every assistant message after it. A turn is never mixed with an earlier one.
  - Each new step is redacted and pushed as `reasoning {text, step}` on the run stream and `group_reasoning {group_id, bot_id, run_id, text}` on `/api/events`, and `runs.reasoning` (steps joined by a blank line) is updated.
  - A last sync runs when the run completes. If Hermes ever sends `reasoning.available`, it is used as before.
- Startup recovery: for runs still `queued` or `running`, try `GET /v1/runs/{hid}`. If it is still running, re-attach the consumer from `last_seq`. If it is terminal, settle it. If it is unknown (404), mark it `interrupted`.
- `stop(run)`: call `POST .../stop`. `steer(run, text)`: call `POST .../steer` with `{"input": text}`; on 409, return 409 "Bot sudah selesai, pesan dikirim sebagai pesan baru" so the frontend can resend it as a new message. `approval(run, choice)`: call `POST .../approval`.
- A 429 from Hermes becomes 429 "Terlalu banyak tugas berjalan, coba sebentar lagi".

## 4. Group engine (stage 3)

Rules (the same as Hermes Desktop Bot Mode): 2-6 members, at most 3 rounds and 10 bot messages per user send, `[SILENT]`, `@name` mentions. Members may come from different teams.

- Per (group, bot), the Hermes session id is `grup-<group_id>-<bot_id>`.
- On a bot's turn, the input is every group message with id greater than that bot's cursor, written as `Nama (peran): teks` lines and `User: teks` for user messages. Then advance the cursor. Hermes keeps the older history and compresses it, so we never resend it.
- `instructions` for every group turn (Indonesian): the group name; the member list with roles; "Balas singkat sesuai peranmu"; "Jika tidak ada yang perlu kamu tambahkan, balas persis [SILENT]"; "Sebut @nama untuk meminta anggota lain"; "Jangan mengulang pesan anggota lain".
- `send(group, text, mode)`:
  1. Insert the user message.
  2. If no send is running, start the loop. If one is running and `mode == "queue"`, insert a `group_sends` row with status `queued` and reply 202 `{queued: true}`.
  3. If one is running and `mode == "steer"`:
     - Steer the bot run in progress with `User: text` and advance that bot's cursor past the message.
     - Cancel the turns left in the current round.
     - Start a new loop from this message once the current run finishes.
- Loop for one send:
  - Round 1 responders: the `@mentioned` members if the user message mentions any; otherwise every member in `position` order.
  - Rounds 2 and 3: only the members `@mentioned` in the previous round's bot messages who have not spoken since. If there are none, the loop ends.
  - Each turn is a `start_run(kind="group")`, awaited to completion. Its output is trimmed. Output that is exactly `[SILENT]` or contains only `[SILENT]` is not posted. Otherwise insert a bot message.
  - Stop the loop when any of these happens:
    - The rounds or messages cap is reached.
    - The send's tokens reach the plan's `group_send_token_budget` (NULL = no limit, never checked).
    - The user presses stop.
    - The quota is exhausted.
  - A cap or budget stop inserts a system message in Indonesian, e.g. "Diskusi berhenti: batas 3 ronde tercapai."
  - When the loop finishes, start the next queued send if one exists. All queued user messages are already in the transcript, so one loop covers them.
- Group stop: stop the current run, mark the send `stopped`, and drop the queued sends.
- Startup recovery: mark running sends `stopped` and add a system message "Diskusi terhenti karena server dimulai ulang."
- Bot status for the office and sidebar: `discussing` while the bot has a running group run; `working` while it has a running chat run; otherwise `idle`.

## 5. HTTP API

Everything is under `/api`, as JSON. SSE responses send `retry: 3000`, `id:` per event, and a keepalive every 15 s. The browser reaches it as `/bff/api/...` through the Vite proxy.

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | No key needed. `{ok, db, hermes}` |
| GET | `/api/me` | `{user, plan, limits, usage: {tokens_month, bots, groups, active_runs}}` |
| GET | `/api/plans` | List |
| PUT | `/api/me/plan` | `{plan_id}`: demo plan switch, no payment |
| GET | `/api/templates` | The five builtin personas (id, name, role, team, color, short description) |
| GET | `/api/bots` | Each bot is `{id, name, role, team, color, builtin, about, status, activity}`. `about` is the persona summary (max 280 chars) for the Info tab. `activity` is the latest tool label while working |
| POST | `/api/bots` | `{name, role, team, color?, template?}` or `{name, role, team, color?, persona}`. See section 6. 201 with the bot |
| DELETE | `/api/bots/{id}` | Only for bots that are not builtin. Refused while a run is active. Removes the bot from groups |
| GET | `/api/bots/{id}/sessions` | Hermes sessions for this bot that are owned (`chat_sessions`), excluding `grup-*`, newest first |
| GET | `/api/bots/{id}/sessions/{sid}/messages` | Pass-through of Hermes messages, including reasoning; checks ownership |
| PATCH/DELETE | `/api/bots/{id}/sessions/{sid}` | Rename, or delete |
| POST | `/api/bots/{id}/runs` | `{input, session_id?}`. Without a session_id, create `web-<uuid>` and register it. Reply 202 `{run, session_id}` |
| GET | `/api/runs?status=active\|recent&limit=` | List with bot name, short input, and status |
| GET | `/api/runs/{id}` | The full row plus its tool events |
| GET | `/api/runs/{id}/stream` | SSE. First a `snapshot` (output so far, status, tool events, reasoning so far), then live `delta {text}`, `reasoning {text, step}`, `tool {event, tool, preview, duration, error}`, `approval {request_id, description, choices}`, `status {status}`, and `done {status, output, reasoning, usage}` |
| POST | `/api/runs/{id}/stop` · `/steer` `{text}` · `/approval` `{choice}` | |
| GET/POST | `/api/groups` | POST `{name, bot_ids}`, checked for 2-6 members and the plan limit |
| PATCH/DELETE | `/api/groups/{id}` | Rename or edit members (same checks); delete is soft |
| GET | `/api/groups/{id}/messages?before=&limit=50` | Paged, oldest first |
| POST | `/api/groups/{id}/messages` | `{text, mode: "queue"\|"steer"}`. 202 `{message, queued}` |
| POST | `/api/groups/{id}/stop` | |
| GET | `/api/usage?session_id=` or `?group_id=` | Exactly one of the two. `{total: {input, output, cache_read, total, runs}, by_bot: [{bot_id, name, input, output, total, runs}], turns: [{run_id, bot_id, created_at, input, output, total, status}]}`. `turns` newest first, max 50 |
| GET | `/api/usage/bots?period=month` (or `all`) | Per-bot totals for the current user: `[{bot_id, name, input, output, total, runs}]` |
| GET | `/api/thinking?session_id=` or `?group_id=` | Thinking per bot turn, oldest first: `[{run_id, bot_id, status, created_at, reasoning}]`. Running turns are listed even when still empty |
| GET | `/api/activity?bot=&status=&session_id=&group_id=&limit=100&before=` | Tool events joined with runs: time, bot, tool, status (ok/error), duration, preview (redacted), run id, chat or group name |
| GET | `/api/events` | Global SSE. `run {id, bot_id, kind, status, group_id}`, `bot_status {bot_id, status, activity}`, `group_message {group_id, message}`, `group_typing {group_id, bot_id, on, phase}` (`phase` is `thinking` until the first words, then `writing`), `group_reasoning {group_id, bot_id, run_id, text}`, and `group_send {group_id, status}`. The frontend uses it for notifications, the sidebar, group chat and the office |
| GET | `/api/office` | Snapshot for the 3D office (kept for later; the 3D office is cancelled for now and the frontend does not use it): bots with status and activity, groups with members, and the last 5 messages per group |

## 6. Bots and quota (stage 4)

- Quota check before every run:
  - The month's `sum(total_tokens)` must be below `monthly_tokens` (NULL = no limit, not checked).
  - Active runs must be below `max_concurrent_runs`.
  - Otherwise return 402 `{error, upgrade: true}`, for example "Kuota token bulan ini habis. Naikkan paket untuk melanjutkan."
- Creating a bot or group checks `max_bots` / `max_groups` the same way. Builtin bots count toward `max_bots`.
- Bot creation:
  1. Make a slug from the name: lowercase ASCII `[a-z0-9]`, max 24 characters, with a numeric suffix if it is taken by a profile or bot. Reject names that make an empty slug.
  2. Run `hermes profile create <slug> --clone-from <source> --no-alias` with no shell, an argument list, and a 120 s timeout. The source is the template id, or `rian` for a custom persona. It copies the model config and provider key.
  3. Replace `API_SERVER_KEY` in the new profile `.env` with `secrets.token_urlsafe(32)`. Rewrite only that line, keep every other line byte for byte, and never log it.
  4. Write SOUL.md. A template copies `D:/Programming/AITopTrends-Hermes/bots/souls/<template>.md` with the name and role replaced. A custom persona uses a fixed Indonesian house template (identity, role, team, the user's persona text, then the shared rules: company "AI Top Trends" without PT, short replies, `[SILENT]` alone, at most 2 revision rounds, no unverified facts).
  5. Apply hardening (section 8).
  6. Wait until `GET /p/<slug>/v1/models` answers 200 (poll every 2 s, max 40 s; the gateway rescans every 30 s). Then insert the row.
  - On any failure, run `hermes profile delete <slug> -y` and return a clear error.
- The persona text is limited to 2000 characters, and the name and role to 40. They are user input written into a prompt file, so store them as plain text. They do not grant tools; the toolsets do.

## 7. Redaction (stage 5)

Apply to every stored and returned tool preview and approval description:

- Replace `sk-[A-Za-z0-9_-]{16,}`, `Bearer\s+\S+`, `(api[_-]?key|token|secret|password)\s*[:=]\s*\S+` (keep the name), JWT-like strings `eyJ[\w-]+\.[\w-]+\.[\w-]+`, and hex/base64 runs of 32 or more characters with `[disensor]`.
- Mask emails (`k***@domain`) and phone numbers (`+62` or `08` followed by 8-12 digits, keeping the last 3).
- Shorten absolute paths (`C:\...\x`, `/home/.../x`, `/Users/...`) to `…/<basename>`.
- Truncate to 2048 characters with `…`.

Unit tests for this module are worth keeping in the suite: `bff/tests/test_redact.py`.

## 8. Hardening (applies to the five builtin bots and every new bot)

Use the command `uv run python -m bff.harden [--profile X]`. It is idempotent and backs up `config.yaml` to `config.yaml.bak-<date>` before the first change. For each profile config.yaml:

- Set `platform_toolsets.api_server` to the profile's current API toolsets minus `terminal`, `file`, `code_execution`, `browser`, `computer_use`, `cronjob` and `delegation` (customer bots must not schedule jobs or spawn sub-agents that keep working after being told to stop). Read the real names from `GET /p/<bot>/v1/toolsets` or from `hermes_cli/tools_config.py`.
- Set `approvals.mode: manual`.
- Preserve all other keys and comments. Use `ruamel.yaml` round-trip.
- Verify afterwards with `GET /p/<bot>/v1/toolsets` that terminal, cronjob and delegation are absent.

Desktop Bot Mode uses other platforms, so it is unaffected. Mention that in the command's output.

## 9. Dev wiring

- `frontend/vite.config.ts`:
  - Remove the `/hermes/*` proxy, the `hermesGuard`, the `/api` to 8080 proxy and the image proxy.
  - Add `/bff` to `127.0.0.1:8090`: rewrite `/bff` to an empty prefix, inject `X-Pegawai-AI-Key` from `BFF_API_KEY` in `frontend/.env.local`, and set `timeout: 0` for SSE.
  - The frontend `.env.local` then holds only `BFF_API_KEY`. Remove the `HERMES_KEY_*` lines from `.env.local.example` if present.
- `start-dev.ps1`: start the BFF (`uv run uvicorn bff.main:app --port 8090` in `bff/`, health `/api/health`) instead of `server.py`, then the frontend on 5173. Drop `-Mock`. Keep the `npm.cmd` comment.
- `README` section "Menjalankan BFF": the steps for the user to create the database (`createdb`) and fill in `bff/.env`.

## Verified

Checked on 4 November 2026 against Hermes v0.22.5 with the real gateway.

- **Thinking mid-run (4 November 2026, one web_search run to Rian, deepseek-v4.1-flash):** Hermes persists the intermediate assistant message, with its `reasoning`, before the turn ends. Timeline of the run stream: tool events at 30.8 s, step 1 (198 chars, the thinking before the tool call) at 32.7 s, tool events at 33.1 s, first answer words at 37.4 s, step 2 (308 chars, the thinking of the final answer) and `done` at 38.0 s. So thinking arrives per step while the run is going, but the last step only lands together with the final answer. A 2-bot group send (no tools) showed each bot's thinking at the end of its turn, since a turn without tools is a single step. It is not per token: that needs `/v1/chat/completions`, which cannot be stopped or steered. `usage.cache_read_tokens` came back as 0 for every run.
- **Reasoning on `/v1/runs`: no.** Three chat runs (plain answer, a stopped long answer, a web_search run) produced no `reasoning.available` or any reasoning field in the event stream. Hermes does store it in the session: `GET /p/<bot>/api/sessions/{id}/messages` has `reasoning` / `reasoning_content` on assistant messages, but on the tool-calling run it sat on the first assistant message (the one with the tool call), not on the final one. So the fallback copies the reasoning of **all** assistant messages after the last user message (joined), not only the last one. Since 4 November 2026 the same copy also runs while the run is going and for group runs (section 3). Models do not always reason, so `runs.reasoning` is often null.
- **Toolset names** (`GET /p/<bot>/v1/toolsets`, enabled before hardening): `web, browser, terminal, file, code_execution, vision, image_gen, skills, todo, memory, session_search, connections, delegation, cronjob`. After `bff.harden`: `web, vision, image_gen, skills, todo, memory, session_search, connections, delegation, cronjob` (terminal, file, code_execution, browser absent; `computer_use` was already off). `cronjob` and `delegation` were added to the deny list later (4 November 2026) and are now removed too.
- **No gateway restart needed for hardening.** `platform_toolsets.api_server` is read per request: the toolsets endpoint showed the change within seconds, and a bot cloned from a hardened bot inherits the list.
- **New profile hot-serve:** `POST /api/bots` returned after about 33 s end to end (`hermes profile create` plus waiting for `/p/<slug>/v1/models` to answer 200, which follows the gateway's 30 s rescan). Deleting a bot took about 12 s.
- **Stop:** `POST /v1/runs/{id}/stop` returns `{"status":"stopping"}` and the run settles as `cancelled` within a couple of seconds, with usage 0 (no `usage` on cancelled runs).
- **Windows:** psycopg async cannot use uvicorn's default ProactorEventLoop, so the BFF is started with `--loop asyncio:SelectorEventLoop`.
- `tool.completed` events carry an empty `preview`; the activity log takes the preview from the matching `tool.started` event (same `tool_call_id`).
