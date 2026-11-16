# Kontrak API BFF (Sprint 3, 10 November 2026)

One backend: the BFF (`pegawai-ai-backend/bff`, FastAPI, port 8090, Postgres, Hermes Runs API through the hardened gateway). Faiz's server in `local_setup/backend_template/` (port 8080) is an archive, see `local_setup/LEGACY.md`.

Base path `/api`. Every endpoint except `GET /api/health` needs the header `X-Pegawai-AI-Key` (the Vite proxy adds it). Single user, no login. Errors are `{"error": "<pesan Indonesia>"}` with the right HTTP status (`402` also has `"upgrade": true`).

Spec: `docs/sprint3/spec-penyesuaian-knowledge-cs.md`. Knowledge files: `bff/knowledge/` (read as they are, never edited).

## 1. Endpoints

Unchanged from stage 2 (see `docs/bff-spec.md` for their bodies); only the run endpoints and the catalog are new or extended in Sprint 3.

| Area | Endpoint |
|---|---|
| Health | `GET /health` (public) |
| Account | `GET /me`, `GET /plans`, `PUT /me/plan` |
| Bots | `GET /templates`, `GET/POST /bots`, `GET/PATCH/DELETE /bots/{id}`, `GET /tools` |
| Sessions | `GET /bots/{id}/sessions`, `GET /bots/{id}/sessions/{sid}/messages`, `PATCH/DELETE /bots/{id}/sessions/{sid}` |
| **Runs** | `POST /bots/{id}/runs` (extended), `GET /runs` (carries `origin`), `GET /runs/{rid}` (carries `meta`), `GET /runs/{rid}/stream` (SSE, `done` extended), `POST /runs/{rid}/stop`, `/steer`, `/approval`, `/clarify` |
| **Sequences** | `POST /bots/{id}/sequences`, `GET /sequences?case_id=&limit=`, `GET /sequences/{id}`, `POST /sequences/{id}/stop` (new, section 8) |
| **Catalog** | `GET /products/search` (new) |
| Groups | `GET/POST /groups`, `PATCH/DELETE /groups/{gid}`, `GET/POST /groups/{gid}/messages`, `POST /groups/{gid}/stop`, `GET /groups/{gid}/live` (new, section 10) |
| Logs | `GET /activity`, `GET /usage`, `GET /usage/bots`, `GET /thinking`, `GET /events` (SSE), `GET /office` |
| **Settings** | `GET /models`, `GET/PATCH /settings`, `GET /settings/security`, `GET /settings/knowledge`, `GET /export/history` (new, section 12); `PATCH /bots/{id}` also takes `model`, `provider`, `reasoning_effort` |
| Evaluations | `GET/POST /evaluations`, `GET /evaluations/summary`, `PATCH /evaluations/{id}` |

## 2. Start a run

`POST /api/bots/{bot_id}/runs` returns `202 {"run": {...}, "session_id": "web-..."}`.

Body:

| Field | Type | Meaning |
|---|---|---|
| `input` | string, 1 to 20000 chars | Required. The user message. |
| `session_id` | string | Optional. Reuse a session for multi-turn. Omit to open a new one. |
| `instructions` | string, max 6000 chars | Optional, backward compatible. Used as the base instruction of a `marketing` workflow. **Ignored for `cs`** (v2.1 is the only base). Without `workflow` it is passed to Hermes as before. |
| `workflow` | `"cs"` or `"marketing"` | Optional. Must match the bot's team (`customer_support` for `cs`, `marketing` for `marketing`), else `400 "Workflow tidak cocok dengan tim bot ini"`. When set, the BFF builds the instructions and retrieves context before the run. |
| `stage` | string, max 60 chars | Optional, for marketing. Stored in `meta.stage`. |
| `test_mode` | boolean | Optional, default false. Only with `workflow:"cs"`: injects the `SIM-*` fixtures (marked as simulation). Anything non-boolean is `400`. |
| `origin` | `{type, case_id?}` | Optional. `type` is `chat`, `cs`, `marketing` or `evaluasi`; `case_id` is text, max 40 chars. Stored in `meta.origin`. When absent the BFF infers it: group run is `group`, `workflow:"cs"` is `cs`, `workflow:"marketing"` is `marketing`, else `chat`. Anything else is `400`. |

What `workflow` makes the BFF do (the agent does not call tools to fetch knowledge; the BFF retrieves first, so the context is exactly known):

- `cs`: instructions = the whole `COLORBOX_CS_Instructions_v2_1.md` + the 11 records of `COLORBOX_CS_Knowledge_v2.json` + the source register CSV + up to 5 catalog products found for the input (marked as data observed on 9 Nov 2026, stock unknown). The Hub CS files (`business-policies`, `product-size-reference`, `customer-faq`, `customer-inquiry-patterns`) are never injected. With `test_mode`, all `SIM-*` fixtures are added.
- `marketing`: instructions = the `instructions` the client sent + `brand-profile`, `brand-guidelines`, `content-pillars`, `content-research` + up to 5 catalog products.

## 3. Run fields

`GET /api/runs/{rid}` returns the run row (never `hermes_run_id` or `user_id`) plus `events` (tool and approval events, includes the escalation recommendation, see 5):

`id, bot_id, session_id, group_id, kind, status (queued|running|completed|failed|cancelled|interrupted), input, output, reasoning, error, input_tokens, output_tokens, total_tokens, cache_read_tokens, last_seq, created_at, started_at, finished_at, meta, events`.

`meta` of every run: `hermes_version, model, provider, bot_id, soul_hash, toolsets, instructions_mode, bff_commit`, and `origin` (`{type, case_id?}`; the turns of a sequence add `sequence_id, turn, of`, see section 8). Runs from before `origin` existed have none in `meta`.

`meta` of a run started with `workflow` adds:

| Key | Value |
|---|---|
| `workflow` | `"cs"` or `"marketing"` |
| `stage` | string or null |
| `test_mode` | boolean |
| `context_refs` | list, see section 4 |
| `instructions_version` | `"cs-2.1"` (cs only) |
| `knowledge_version` | from the knowledge JSON, currently `"2.0"` (cs only) |
| `knowledge_files` | `{file: first 12 hex of sha256}` of the Marketing files (marketing only) |
| `prompt_hash` | sha256 of the instructions + `\n` + input |
| `validation` | `{status, errors, attempts?}`, see section 6 |
| `structured` | the validated CS v2.1 object (cs only, only when valid or repaired) |
| `latency_ms` | start to finish, ms (set when the run ends) |
| `tokens` | `{input, output, total}`, includes the retry |

`GET /api/runs` (the list) does not carry `meta`. Each row has `origin` instead: `{type: chat|cs|marketing|evaluasi|group, case_id?, sequence_id?, turn?, of?}`, inferred as above when the run has none stored. The frontend uses it to link a running task to its page (Evaluasi case, CS, Marketing, group or bot chat) and to show the line "Evaluasi - V02 - giliran 2 dari 3".

## 4. `context_refs`

Everything the agent got as context, in order: knowledge records or files, then products, then fixtures. Each item:

```json
{ "type": "knowledge | product | fixture", "id": "CB-RETURNS-001", "title": "return_policy",
  "classification": "verified_public", "source_id": "SRC-04",
  "url": "https://colorbox.co.id/policies/refund-policy", "accessed_date": "2026-11-07" }
```

| type | id | title | classification | source_id / url / accessed_date |
|---|---|---|---|---|
| `knowledge` (cs) | record id (`CB-...`) | record `kind` | record `status` (`verified_public`, `unknown_*`, ...) | from the CS source register; `null` for `CB-ACCOUNT-DELETION-UNKNOWN-001` (no source) |
| `knowledge` (marketing) | file name (`brand-profile.md`) | file H1 | Hub class (`Public Data`, `Research Findings`) | Hub source id, URL (can be null), `2026-11-09` |
| `product` | product row id (string) | product name | `Public Data` | `SRC-02`, product URL, `2026-11-09` |
| `fixture` | `SIM-...` scenario id | fixture kind | `Dummy / Simulated Data` | all `null` |

These are what was in the context, not what the answer cited. What the CS answer actually used is in `structured.knowledge_refs`.

## 5. Getting results

The frontend gets the structured result in three places (same data):

1. **SSE `done` event** of `GET /runs/{rid}/stream` (the engine's completion event). For a run with a workflow it adds `structured` (object or null), `validation`, `context_refs` next to `status, output, reasoning, error, usage`. A finished run opened later gets the same `done` frame after the `snapshot`.
2. **Run detail** `GET /runs/{rid}`: `meta.structured`, `meta.validation`, `meta.context_refs`.
3. Activity log `GET /activity`: when `structured.escalation.recommended` is true, an item with `tool: "Rekomendasi eskalasi"`, `preview` = the reason, `status: "ok"`. It is a recommendation only. Nothing is routed and nothing says "escalated".

`output` always holds the raw agent answer. A failed validation never hides it: show `output` when `structured` is null.

The SSE `delta` stream shows the raw model text (for CS, the JSON as it is written). If the automatic retry runs (section 6), the retry's text follows the first attempt's in the stream; the `done` event carries the final `output`.

## 6. CS v2.1 result and validation

The model's native JSON mode is **not available**: Hermes `POST /v1/runs` reads `input`, `instructions`, `session_id`, `model`, `provider`, `model_options` (only `reasoning`, `service_tier`, `fast`); `response_format` appears nowhere in the gateway run path (`gateway/platforms/api_server_runs.py`, `api_server.py` in the installed Hermes 0.22.5). So the BFF extracts the JSON from the answer (whole text, fenced block, or outermost braces), validates it with a Pydantic model (`bff/bff/cs_schema.py`) and, when invalid, retries **once** automatically in the same session with a repair message.

`structured` (instructions v2.1, section 11):

```json
{
  "primary_intent": "PRODUCT_INFO|PRODUCT_AVAILABILITY|SIZE_FIT|SHIPPING_DELIVERY|CLICK_COLLECT|ORDER_PROCESS|ORDER_STATUS|COMPLAINT_DAMAGED|COMPLAINT_WRONG_ITEM|COMPLAINT_LATE_MISSING|RETURN_REFUND|PAYMENT|WEBSITE_TECHNICAL|OTHER|AMBIGUOUS",
  "secondary_intents": ["..."],
  "classification_confidence": 0.9,
  "priority": "P0|P1|P2|P3",
  "customer_reply_draft": "text for the customer only",
  "ticket_summary": {
    "issue": "...", "customer_reported_facts": [], "publicly_verified_facts": [], "unknowns": [],
    "customer_provided_references": [], "requested_outcome": null, "context_retained": []
  },
  "knowledge_refs": [
    { "knowledge_id": "CB-PRODUCT-001", "source_ids": ["SRC-01"], "source_url": "https://colorbox.co.id/",
      "accessed_date": "2026-11-07", "used_for": "..." }
  ],
  "clarifying_question": null,
  "escalation": { "recommended": true, "reason": "...", "handoff_status": "recommendation_only" },
  "human_review_required": true,
  "simulation": { "is_simulated": false, "scenario_ids": [] }
}
```

Invariants enforced (a violation makes the result invalid):

- `classification_confidence` between 0 and 1; `priority` P0 to P3; `primary_intent` and `secondary_intents` from the list above.
- `escalation.handoff_status` is `"recommendation_only"`; `human_review_required` is `true`.
- `primary_intent` RETURN_REFUND means `priority` P1 and `escalation.recommended` true; RETURN_REFUND as a secondary intent also needs `escalation.recommended` true.
- `priority` P0 or P1 means `escalation.recommended` true; a recommended escalation needs a non-empty `reason`.
- Missing required keys (`primary_intent`, `classification_confidence`, `priority`, `customer_reply_draft`, `ticket_summary.issue`, `escalation`, `human_review_required`) are invalid. Other keys default to empty. Unknown extra keys are dropped.

`validation`:

| `status` | Meaning | `structured` |
|---|---|---|
| `valid` | Valid on the first answer | present |
| `repaired` | Invalid at first, valid after the one automatic retry. `errors` = the first attempt's errors | present |
| `invalid` | Still invalid after the retry. `errors` = the final errors (strings like `priority: Input should be ...`) | null |
| `not_applicable` | Marketing runs, or a CS run that did not complete (`errors: ["Tugas tidak selesai"]`) | null |

`attempts` (1 or 2) is present for CS runs. The retry adds a second user turn to the same Hermes session (history shows it); its tokens are included in the run totals.

## 7. Catalog search

`GET /api/products/search?q=&category=&max_price=&color=&size=&limit=5` returns `{"data": [...], "count": n}`. At least one of `q`, `category`, `max_price`, `color`, `size` is required (`400` otherwise).

- `q`: Postgres text search over name, category and colors. Words are OR-ed and ranked, words under 3 letters and filler words (`yang`, `harga`, ...) are dropped. A `q` of only filler words matches nothing.
- `category`, `color`: case-insensitive contains. `max_price`: integer rupiah. `size`: exact size such as `M`, `XL`, `28`. `limit`: 1 to 20, default 5. Order: rank, then price.
- Row: `{id, category, name, price, price_original, colors[], sizes[], url, source: "SRC-02", accessed_date: "2026-11-09"}`. `price_original` is set only when the catalog shows a struck-through price. Stock is unknown, never imply availability.

The catalog (1,206 rows, from `bff/knowledge/colorbox/product-catalog.md`) lives in Postgres table `products` (migration `006_products.sql`) and is reloaded at startup only when the file hash changed (`knowledge_meta`).

## 8. Sequences (multi-turn runs that continue on the server)

A sequence runs several user turns of one conversation in order, in the BFF, so it finishes when the page is closed. Evaluasi uses it for every non-compare run (a single run is a sequence of 1 turn).

`POST /api/bots/{bot_id}/sequences` returns `202` with the sequence view (below). Body:

| Field | Type | Meaning |
|---|---|---|
| `turns` | list of 1 to 10 strings | Required. Each 1 to 20000 chars after trimming. |
| `origin` | `{type: "evaluasi", case_id: string}` | Required. `case_id` 1 to 40 chars. |
| `workflow`, `stage`, `test_mode` | as in section 2 | Optional, same rules (workflow must match the bot's team). The context is built per turn. |

The BFF checks the bot, the body, the workflow/team match and the quota (`402`) before answering, opens one new session, stores the sequence (table `sequences`, migration `007_sequences.sql`) and starts a background task. The task starts turn 1, waits for the run to finish, then starts the next one in the same `session_id`. It stops at the first turn that is not `completed` and records why. Every run gets `meta.origin = {type: "evaluasi", case_id, sequence_id, turn, of}`.

Sequence view (`GET /api/sequences/{id}`, also each item of the list):

`id, bot_id, session_id, origin, status (queued|running|completed|failed|stopped), current_turn, of, run_ids, turns, error, created_at, updated_at`.

`turns` has one item per run started so far: `{turn, run_id, status, input, output, error, structured, validation, context_refs}` (`structured`, `validation` and `context_refs` come from the run's `meta`, see sections 4 to 6). `error` of the sequence is text such as "Giliran 2 dari 3: ...".

- `GET /api/sequences?case_id=V02&limit=1`: the latest sequences (newest first, `limit` 1 to 20, default 1), optionally for one case. The page uses it to restore a running or finished case after a reload or after leaving the page.
- `POST /api/sequences/{id}/stop`: stops the running turn and skips the rest; `409` when the sequence already ended. The status becomes `stopped`.
- A run that was cancelled gives `stopped`; a failed or interrupted run gives `failed`.
- BFF restart: the background tasks are lost and are not resumed. At startup every `queued` or `running` sequence becomes `failed` with `error: "Dihentikan karena server dimulai ulang"`.
- Not covered: Compare mode of Evaluasi still runs its runs from the browser (client-side), so leaving the page during a comparison stops it.

## 9. Clarify (the model asks the user a question)

The five builtin bots have the `clarify` toolset on the API server. When the model calls it, the run pauses until the user answers.

- **SSE `clarify`** on `GET /runs/{rid}/stream`: `{request_id, execution_generation, question, choices}`. `choices` is a list of strings, empty when the question is free text. It is built from the Hermes run event `clarify.request` (`prompt_id`, `execution_generation`, `question`, `choices`, `multi_select`) and stored in `run_events`.
- **SSE `clarify_done`** (`{}`): the question was settled (answered here or elsewhere). Remove the card.
- **Reconnect:** the `snapshot` frame carries `clarify` (the same object, or `null`) while a question is pending, so a reload shows the card again.
- **`POST /api/runs/{rid}/clarify`** `{answer}` (string, 1 to 4000 characters). The BFF adds `request_id` and `execution_generation` from the pending question and calls Hermes `POST /v1/runs/{id}/clarify` with exactly `{request_id, execution_generation, answer}` (Hermes rejects any other field set). Returns `{ok: true}`. Errors: `400` blank answer, `409` no pending question, already answered or expired, run finished; `502` Hermes failure. Answering does not start another turn: the same run continues.

## 10. Group chat streams like chat

The bot turn in a group is a normal run (`kind: "group"`), so its text and steps come from the same run stream as in chat. No new event type carries the text.

- **Global SSE `group_typing`** (`GET /events`) is now `{group_id, bot_id, on, phase?, run_id?}`. `on: true, phase: "thinking"` opens the turn (no `run_id` yet). A second `on: true` follows once the run exists and carries `run_id`: the client subscribes to `GET /runs/{run_id}/stream` (`snapshot`, `delta`, `tool`, `reasoning`, `done`, same shapes as sections 2 and 3) and draws the live bubble. `phase: "writing"` is still sent at the first words. `on: false` is sent AFTER the bot's final message was posted (`group_message`), or without one for a `[SILENT]` or failed turn, so the live bubble hands over to the stored message.
- **`GET /api/groups/{gid}/live`** returns `{"turn": null}` or `{"turn": {"bot_id", "run_id"}}` (`run_id` is `null` before the run started). A page that reloads mid-turn calls it, subscribes to the run stream and gets the text so far from the `snapshot`.
- Group turn rules (2 to 6 bots, 3 rounds, `[SILENT]`, `@name`) and the stored messages are unchanged.

## 11. Approval forwarding (fix)

`POST /api/runs/{rid}/approval` `{choice}` is unchanged for the browser. The BFF now keeps the pending approval from the Hermes event `approval.request` (`prompt_id`, `execution_generation`) and calls Hermes `POST /v1/runs/{id}/approval` with exactly `{request_id, execution_generation, choice}`. The SSE `approval` event keeps its shape (`request_id` is the Hermes `prompt_id`). New error: `409` when no approval is waiting (or it expired).

## 12. Model per agent, workspace settings, Pengaturan

Migration `008_model_settings.sql`: columns `model`, `provider`, `reasoning_effort` on `bots` (all nullable, null = default: nothing is sent and Hermes uses the profile default) and table `settings` (one JSON row per user, merged over the defaults in `bff/settings.py`).

**What Hermes offers.** `GET /p/<bot>/v1/models` only lists the profile itself (`{"id": "<bot>"}`), so it cannot feed a model picker. The BFF reads the picker inventory the gateway serves for external clients, `GET /p/<bot>/api/model/options` (providers with `authenticated`, `models`, current `model` and `provider`), keeps only the signed-in providers with models and caches it 5 minutes.

- `GET /api/models` returns `{default: {model, provider}, providers: [{slug, name, models: [..]}]}`. `default` is the profile default of the first agent.
- `PATCH /api/bots/{id}` accepts `model`, `provider` (both together: both set or both `null`) and `reasoning_effort` (`none|minimal|low|medium|high|xhigh` or `null`). A pair that is not in `GET /api/models` is refused with `400` (Hermes would reject it at run time). Builtin agents may change these three fields (and the colour); everything else stays `403`. The agent view (`GET /bots`, `GET /bots/{id}`) carries the three fields.
- **On a run** the BFF sends `model` and `provider` (the agent's own pair) and `model_options.reasoning_effort` (the agent's own) to `POST /v1/runs`, only what is set; nothing is sent when the agent has none (Hermes then uses the profile default). Model, provider and effort exist per agent only: there is no workspace-wide default. The same fields are kept for the automatic CS repair retry. `runs.meta` records the effective `model`, `provider` and `reasoning_effort` when they were overridden. Group turns use the same rule.
- `GET /api/settings` returns `{company_name ("Colorbox"), language ("id"), timezone ("Asia/Jakarta"), notify: {done, failed, input}}`. `PATCH /api/settings` takes any of these keys and returns the merged object: `company_name` 1 to 40 characters; `language` only `"id"`; `timezone` one of `Asia/Jakarta`, `Asia/Makassar`, `Asia/Jayapura`; `notify` booleans (merged key by key). Unknown key (including `model`, `provider`, `reasoning_effort`, which are per agent only) or empty body is `400`. Old workspace model keys that may still sit in the stored row (and the DB columns) are ignored, not migrated away.
- `GET /api/settings/security` returns `{deny: [..], bots: [{bot_id, name, ok, blocked: [..], approvals}]}`: the denied toolsets that are really off on the gateway for each agent (`ok: false` when Hermes did not answer) and `approvals.mode` read from the profile `config.yaml`. No `.env` and no key is read or returned.
- `GET /api/settings/knowledge` returns `{retention_days: 90, docs: [{id, title, workflow, version, date, files: [{name, title}]}]}` for the documents `knowledge.py` loads (Colorbox Hub, CS v2.1). Read only.
- `GET /api/export/history` returns one JSON file (`Content-Disposition: attachment; filename="riwayat-chat.json"`): `{exported_at, bots: [{bot_id, name, sessions: [{id, title, started_at, last_active, messages | error}]}], groups: [{id, name, messages}]}`. Sessions are the ones the user owns, messages come from Hermes; a session Hermes cannot return carries `error` instead of `messages`.
- **Global SSE `run_input`** (`GET /events`): `{id, bot_id, kind, what}` with `what` `"clarify"` or `"approval"`, sent when a run starts waiting for the user. The frontend uses it for the "butuh izin atau jawaban" notification.

## 13. Open items (not resolved here)

- Data conflicts between the Hub and CS v2.1 (size table numbers, refund timing, shipping ETA and Click & Collect) stay for Ivana and Mansi. CS runs use v2.1 only.
- `knowledge_version` in the JSON is `"2.0"` while the instructions are `2.1`; both are recorded as they are.
- The CS source ids (`SRC-01` to `SRC-06`, CS register) and the Hub source ids (`SRC-01` to `SRC-10`, Hub register) are different registers: read `source_id` together with `type` and the workflow.
