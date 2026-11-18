# Hermes v0.22.5: facts for stages 2-5 (4 November 2026)

Paths are relative to `%LOCALAPPDATA%\hermes\hermes-agent\`.

## Runs API

- Endpoints, also at `/p/<profile>/...` (`gateway/platforms/api_server_runs.py:284-292`): `POST /v1/runs`, `GET /v1/runs/{id}`, `GET /v1/runs/{id}/events` (SSE), `POST .../approval`, `.../clarify`, `.../steer`, `.../resolve-unknown`, `.../stop`.
- POST body: `input` (string or message list), `session_id` (body field; the `X-Hermes-Session-Id` header is not read on `/v1/runs`), `instructions` (ephemeral system prompt on top of SOUL), `model`, `conversation_history`. There is no per-request toolset field. `Idempotency-Key` header is retained for 24 h. Reply: 202 `{"run_id","status":"started"}`.
- SSE: each frame is `id: <seq>` plus a data JSON with `"event"`; there is no SSE `event:` line. Keepalive every 10 s. Events:
  - `message.delta {delta}` and `message.interim`.
  - `tool.started {tool, preview, tool_call_id}` and `tool.completed {tool, duration, error, preview<=500}`.
  - `approval.request` and `approval.responded`; `run.steered`, `run.stopping`, `run.queued`.
  - Terminal events `run.completed | run.failed | run.cancelled | run.interrupted`. `run.completed` carries `output` and `usage {input_tokens, output_tokens, total_tokens, cache_read_tokens, cache_write_tokens}`.
  - Reasoning is likely **not** streamed (`_thinking` is dropped); not verified.
- Resume: `Last-Event-ID` header or `?last_seq=N`. The backlog keeps 1000 events, and an older offset gives `replay.truncated`. An unconsumed stream expires after 300 s; terminal status is kept for 3600 s.
- Stop returns `{"status":"stopping"}`; the run then settles as `cancelled`.
- Approval body: `{"choice": "once"|"session"|"always"|"deny"}`.

## Steering

- `POST /v1/runs/{id}/steer` with body `{"input": "..."}` (undocumented, in source `api_server_runs.py:1437-1489`). Only works while the status is `running`; otherwise 409. The text is delivered **after the current tool batch, without interrupting**. Several steers are concatenated.
- A real interrupt-and-redirect (`session.redirect`) exists only on the Desktop WebSocket, with no REST route.

## Profiles

- `hermes profile create <name> [--clone | --clone-all | --clone-from SRC] [--no-alias] [--description TEXT]`. `--clone` copies config.yaml, .env, SOUL.md, skills and memories, but no sessions.
- **`--clone` also copies `API_SERVER_KEY`.** Always set a new key.
- `hermes profile delete <name> -y` removes the folder, including sessions.
- With `gateway.multiplex_profiles: true` (active here), a new profile is served without a restart: the CLI pings the gateway, and the gateway also rescans every 30 s. A profile's key is re-read from its `.env` on every request.

## Tool restriction and approval

- `platform_toolsets.api_server: [...]` in the profile config.yaml applies only to the API, so Desktop is unaffected. `agent.disabled_toolsets` is global. Toolsets to remove: `terminal`, `file`, `code_execution`, `browser`, `computer_use`. Check with `GET /v1/toolsets`.
- `approvals.mode`: `manual` | `smart` (default) | `off`. Over the API, a dangerous command emits `approval.request` and waits for `/approval` until the 300 s timeout, then is denied.

## Context and concurrency

- Compression is on for API runs (`compression.threshold 0.50`, `protect_last_n 20`). It rotates the session id internally; the client keeps sending the same `session_id`.
- `gateway.api_server.max_concurrent_runs` defaults to 10. Over the cap the API returns 429 with `Retry-After: 1`. There is no per-profile limiter.
