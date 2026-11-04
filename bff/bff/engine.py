"""Run engine (stage 2): starts Hermes runs, consumes their event stream, stores results, fans events out."""
import asyncio
import time
import uuid
from dataclasses import dataclass, field

import httpx

from . import db, hermes
from .errors import ApiError
from .redact import redact

TERMINAL = {"run.completed": "completed", "run.failed": "failed",
            "run.cancelled": "cancelled", "run.interrupted": "interrupted"}
ACTIVE = ("queued", "running")
RECONNECT_WAIT = (1, 2, 4, 4, 4)


class Hub:
    """In-process pub/sub. Key is a run id (per-run stream) or '*' (global events)."""

    def __init__(self):
        self.subs: dict[str, set[asyncio.Queue]] = {}

    def subscribe(self, key: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=2000)
        self.subs.setdefault(key, set()).add(q)
        return q

    def unsubscribe(self, key: str, q: asyncio.Queue) -> None:
        self.subs.get(key, set()).discard(q)

    def publish(self, key: str, type_: str, data: dict) -> None:
        for q in list(self.subs.get(key, ())):
            try:
                q.put_nowait((type_, data))
            except asyncio.QueueFull:
                pass  # slow subscriber: drop (it re-syncs from the snapshot when it reconnects)


hub = Hub()


@dataclass
class Live:
    id: str
    bot: str
    hid: str
    kind: str
    group_id: str | None
    session_id: str
    input: str = ""
    last_seq: int = 0
    out: list = field(default_factory=list)
    reasoning: list = field(default_factory=list)  # from the run stream (reasoning.available), when Hermes sends it
    steps: list = field(default_factory=list)  # per-step reasoning read from the session by poll_reasoning
    delta_seen: bool = False
    activity: str | None = None
    done: asyncio.Event = field(default_factory=asyncio.Event)
    finished: bool = False
    task: asyncio.Task | None = None
    flushed_at: float = 0.0


LIVE: dict[str, Live] = {}


# ---------- views and status ----------

def bot_state(bot_id: str) -> dict:
    status, activity = "idle", None
    for lv in LIVE.values():
        if lv.bot != bot_id:
            continue
        if lv.kind == "group":
            status = "discussing"
        elif status == "idle":
            status = "working"
        activity = activity or lv.activity
    return {"status": status, "activity": activity if status != "idle" else None}


def _publish_bot(bot_id: str) -> None:
    hub.publish("*", "bot_status", {"bot_id": bot_id, **bot_state(bot_id)})


def _publish_run(lv: Live, status: str) -> None:
    hub.publish("*", "run", {"id": lv.id, "bot_id": lv.bot, "kind": lv.kind, "status": status, "group_id": lv.group_id})


def run_view(row: dict) -> dict:
    return {k: v for k, v in row.items() if k not in ("hermes_run_id", "user_id")}


# ---------- quota ----------

async def get_plan(user_id: str) -> dict:
    row = await db.q1("select p.* from users u join plans p on p.id = u.plan_id where u.id = %s", user_id)
    if not row:
        raise ApiError(404, "Pengguna tidak ditemukan")
    return row


async def tokens_month(user_id: str) -> int:
    r = await db.q1("select coalesce(sum(total_tokens), 0)::bigint as n from runs "
                    "where user_id = %s and created_at >= date_trunc('month', now())", user_id)
    return int(r["n"])


async def active_runs(user_id: str) -> int:
    r = await db.q1("select count(*)::int as n from runs where user_id = %s and status = any(%s)", user_id, list(ACTIVE))
    return r["n"]


async def check_quota(user_id: str) -> None:
    # shortcut: check-then-insert is not atomic; fine for one local user, add a per-user lock when real login lands.
    plan = await get_plan(user_id)
    if plan["monthly_tokens"] is not None and await tokens_month(user_id) >= plan["monthly_tokens"]:  # NULL = no limit
        raise ApiError(402, "Kuota token bulan ini habis. Naikkan paket untuk melanjutkan.", upgrade=True)
    if await active_runs(user_id) >= plan["max_concurrent_runs"]:
        raise ApiError(402, "Batas tugas bersamaan di paket Anda tercapai. Tunggu tugas selesai atau naikkan paket.",
                       upgrade=True)


# ---------- start ----------

async def start_run(user_id: str, bot: str, session_id: str, input_: str, kind: str,
                    group_id: str | None = None, instructions: str | None = None) -> dict:
    await check_quota(user_id)
    rid = str(uuid.uuid4())
    await db.ex("insert into runs (id, user_id, bot_id, session_id, group_id, kind, status, input) "
                "values (%s, %s, %s, %s, %s, %s, 'queued', %s)", rid, user_id, bot, session_id, group_id, kind, input_)
    body = {"input": input_, "session_id": session_id}
    if instructions:
        body["instructions"] = instructions
    try:
        r = await hermes.call(bot, "POST", "/v1/runs", json_body=body, headers={"Idempotency-Key": rid})
    except ApiError as e:
        await _fail_early(rid, e.message)
        raise
    if r.status_code == 429:
        await _fail_early(rid, "Terlalu banyak tugas berjalan")
        raise ApiError(429, "Terlalu banyak tugas berjalan, coba sebentar lagi")
    if r.status_code >= 300:
        await _fail_early(rid, f"Hermes menjawab {r.status_code}")
        raise ApiError(502, "Bot gagal memulai tugas")
    hid = r.json()["run_id"]
    row = await db.q1("update runs set status = 'running', hermes_run_id = %s, started_at = now() "
                      "where id = %s returning *", hid, rid)
    lv = Live(rid, bot, hid, kind, group_id, session_id, input=input_)
    LIVE[rid] = lv
    lv.task = asyncio.create_task(consume(lv))
    _publish_run(lv, "running")
    _publish_bot(bot)
    return row


async def _fail_early(rid: str, msg: str) -> None:
    await db.ex("update runs set status = 'failed', error = %s, finished_at = now() where id = %s", msg, rid)


# ---------- consumer ----------

def _clean(ev: dict) -> dict:
    drop = {"run_id", "timestamp", "seq", "output"}
    out = {}
    for k, v in ev.items():
        if k in drop:
            continue
        out[k] = redact(v) if isinstance(v, str) else v
    return out


async def _store_event(lv: Live, seq: int, ev: dict) -> None:
    try:
        await db.ex("insert into run_events (run_id, seq, type, payload) values (%s, %s, %s, %s)",
                    lv.id, seq, ev["event"], _json(_clean(ev)))
    except Exception:
        pass  # a failed log write must not break the run


def _json(obj):
    import json
    from psycopg.types.json import Jsonb
    return Jsonb(json.loads(json.dumps(obj, default=str)))


async def _flush(lv: Live, force: bool = False) -> None:
    if force or time.monotonic() - lv.flushed_at >= 2:
        lv.flushed_at = time.monotonic()
        try:
            await db.ex("update runs set output = %s, last_seq = %s where id = %s",
                        "".join(lv.out), lv.last_seq, lv.id)
        except Exception:
            pass


async def _handle(lv: Live, seq: int, ev: dict) -> str | None:
    """Process one Hermes event. Returns the terminal status when the run ended."""
    name = ev.get("event", "")
    lv.last_seq = max(lv.last_seq, seq)
    if name == "message.delta":
        text = ev.get("delta") or ""
        if lv.kind == "group" and not lv.delta_seen:
            lv.delta_seen = True  # first words: the typing row switches from "berpikir" to "mengetik"
            hub.publish("*", "group_typing", {"group_id": lv.group_id, "bot_id": lv.bot, "on": True, "phase": "writing"})
        lv.out.append(text)
        hub.publish(lv.id, "delta", {"text": text, "end": sum(len(p) for p in lv.out)})
        await _flush(lv)
    elif name.startswith("tool."):
        await _store_event(lv, seq, ev)
        if name == "tool.started":
            lv.activity = ev.get("tool")
            _publish_bot(lv.bot)
        hub.publish(lv.id, "tool", {"event": name, "tool": ev.get("tool"), "preview": redact(ev.get("preview")),
                                    "duration": ev.get("duration"), "error": ev.get("error", False)})
    elif name.startswith("approval."):
        await _store_event(lv, seq, ev)
        if name == "approval.request":
            hub.publish(lv.id, "approval", {"request_id": ev.get("request_id"),
                                            "description": redact(ev.get("description") or ev.get("command")),
                                            "choices": ev.get("choices")})
    elif name == "reasoning.available":
        text = redact(ev.get("text") or "")
        lv.reasoning.append(text)
        if text:
            await _emit_reasoning(lv, text, len(lv.reasoning), persist=False)
    elif name in TERMINAL:
        await _store_event(lv, seq, ev)
        return TERMINAL[name]
    elif name.startswith("run."):
        await _store_event(lv, seq, ev)
    return None


async def consume(lv: Live) -> None:
    final: tuple[str, dict] | None = None
    poller = asyncio.create_task(poll_reasoning(lv))
    try:
        attempts = 0
        while final is None:
            try:
                async for seq, ev in hermes.events(lv.bot, lv.hid, lv.last_seq):
                    attempts = 0
                    st = await _handle(lv, seq, ev)
                    if st:
                        final = (st, ev)
                        break
                if final is None:
                    raise httpx.ReadError("stream ended")
            except (httpx.HTTPError, ApiError) as e:
                if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 404:
                    break  # Hermes forgot the run: ask for its status instead
                if attempts >= len(RECONNECT_WAIT):
                    break
                await asyncio.sleep(RECONNECT_WAIT[attempts])
                attempts += 1
        if final is None:
            final = await _poll_final(lv)
    except asyncio.CancelledError:
        raise
    except Exception as e:  # never leave a run stuck in "running"
        final = ("failed", {"error": f"Kesalahan internal: {type(e).__name__}"})
    poller.cancel()
    await finalize(lv, *final)


async def _poll_final(lv: Live) -> tuple[str, dict]:
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        try:
            r = await hermes.call(lv.bot, "GET", f"/v1/runs/{lv.hid}")
        except ApiError:
            await asyncio.sleep(3)
            continue
        if r.status_code == 404:
            return "interrupted", {}
        if r.status_code == 200:
            d = r.json()
            if d.get("status") in ("completed", "failed", "cancelled", "interrupted"):
                return d["status"], d
        await asyncio.sleep(3)
    return "interrupted", {}


async def _turn_steps(lv: Live) -> list[str]:
    """Reasoning of every assistant message of this turn (after the user message that carries the run input)."""
    try:
        r = await hermes.call(lv.bot, "GET", f"/api/sessions/{lv.session_id}/messages")
        if r.status_code != 200:
            return []
        d = r.json()
        msgs = d if isinstance(d, list) else d.get("data") or d.get("messages") or []
        want = lv.input.strip()
        start = next((i for i in range(len(msgs) - 1, -1, -1)
                      if msgs[i].get("role") == "user" and str(msgs[i].get("content") or "").strip() == want), None)
        if start is None:
            return []  # Hermes has not stored this turn's user message yet: never mix in an earlier turn
        out = []
        for m in msgs[start + 1:]:
            if m.get("role") == "assistant":
                t = m.get("reasoning") or m.get("reasoning_content") or ""
                if isinstance(t, str) and t.strip():
                    out.append(t.strip())
        return out
    except Exception:
        return []


async def _emit_reasoning(lv: Live, text: str, step: int, persist: bool = True) -> None:
    hub.publish(lv.id, "reasoning", {"text": text, "step": step})
    if lv.group_id:
        hub.publish("*", "group_reasoning", {"group_id": lv.group_id, "bot_id": lv.bot, "run_id": lv.id, "text": text})
    if persist:
        await db.ex("update runs set reasoning = %s where id = %s", "\n\n".join(lv.steps), lv.id)


async def sync_steps(lv: Live) -> None:
    for i, t in enumerate(await _turn_steps(lv)):
        if i >= len(lv.steps):
            t = redact(t)
            lv.steps.append(t)
            await _emit_reasoning(lv, t, i + 1)


async def poll_reasoning(lv: Live) -> None:
    """Hermes /v1/runs streams no reasoning (bff-spec 'Verified'), so read it from the session every 2 s."""
    try:
        while True:
            await asyncio.sleep(2)
            await sync_steps(lv)
    except asyncio.CancelledError:
        raise
    except Exception:
        pass  # thinking is a bonus: a failed poll must never touch the run


async def finalize(lv: Live, status: str, ev: dict) -> None:
    if lv.finished:
        return
    lv.finished = True
    output = ev.get("output") if isinstance(ev.get("output"), str) else "".join(lv.out)
    usage = ev.get("usage") or {}
    err = ev.get("error")
    if isinstance(err, dict):
        err = err.get("message")
    error = redact(err) if err else (ev.get("turn_exit_reason") if status == "failed" else None)
    if status == "completed":
        await sync_steps(lv)  # last look at the session: thinking that landed after the final poll
    reasoning = "\n\n".join(lv.steps) or "\n\n".join(t for t in lv.reasoning if t) or None
    inp, outp = int(usage.get("input_tokens") or 0), int(usage.get("output_tokens") or 0)
    total = int(usage.get("total_tokens") or inp + outp)
    cache = int(usage.get("cache_read_tokens") or 0)
    await db.ex("update runs set status = %s, output = %s, reasoning = %s, error = %s, input_tokens = %s, "
                "output_tokens = %s, total_tokens = %s, cache_read_tokens = %s, last_seq = %s, finished_at = now() "
                "where id = %s", status, output, reasoning, error, inp, outp, total, cache, lv.last_seq, lv.id)
    LIVE.pop(lv.id, None)
    lv.done.set()
    hub.publish(lv.id, "status", {"status": status})
    hub.publish(lv.id, "done", {"status": status, "output": output, "reasoning": reasoning, "error": error,
                                "usage": {"input_tokens": inp, "output_tokens": outp, "total_tokens": total}})
    _publish_run(lv, status)
    _publish_bot(lv.bot)


async def wait_done(run_id: str) -> dict:
    lv = LIVE.get(run_id)
    if lv:
        await lv.done.wait()
    return await db.q1("select * from runs where id = %s", run_id)


# ---------- control ----------

async def _owned_active(user_id: str, run_id: str) -> tuple[dict, Live]:
    row = await db.q1("select * from runs where id = %s and user_id = %s", run_id, user_id)
    if not row:
        raise ApiError(404, "Tugas tidak ditemukan")
    lv = LIVE.get(run_id)
    if row["status"] not in ACTIVE or not lv:
        raise ApiError(409, "Tugas sudah selesai")
    return row, lv


def _hermes_error(r: httpx.Response, default: str) -> ApiError:
    if r.status_code == 404:
        return ApiError(409, "Tugas sudah selesai")
    return ApiError(502, default)


async def stop(user_id: str, run_id: str) -> dict:
    _, lv = await _owned_active(user_id, run_id)
    r = await hermes.call(lv.bot, "POST", f"/v1/runs/{lv.hid}/stop")
    if r.status_code >= 300:
        raise _hermes_error(r, "Gagal menghentikan tugas")
    return {"status": "stopping"}


async def steer(user_id: str, run_id: str, text: str) -> dict:
    _, lv = await _owned_active(user_id, run_id)
    r = await hermes.call(lv.bot, "POST", f"/v1/runs/{lv.hid}/steer", json_body={"input": text})
    if r.status_code == 409:
        raise ApiError(409, "Bot sudah selesai, pesan dikirim sebagai pesan baru")
    if r.status_code >= 300:
        raise _hermes_error(r, "Gagal mengarahkan bot")
    return {"accepted": True}


async def approval(user_id: str, run_id: str, choice: str) -> dict:
    if choice not in ("once", "session", "always", "deny"):
        raise ApiError(400, "Pilihan persetujuan tidak valid")
    _, lv = await _owned_active(user_id, run_id)
    r = await hermes.call(lv.bot, "POST", f"/v1/runs/{lv.hid}/approval", json_body={"choice": choice})
    if r.status_code >= 300:
        raise _hermes_error(r, "Gagal mengirim persetujuan")
    return {"ok": True}


# ---------- startup recovery ----------

async def recover() -> None:
    rows = await db.q("select * from runs where status = any(%s)", list(ACTIVE))
    for row in rows:
        rid = str(row["id"])
        if not row["hermes_run_id"]:
            await db.ex("update runs set status = 'interrupted', finished_at = now() where id = %s", rid)
            continue
        lv = Live(rid, row["bot_id"], row["hermes_run_id"], row["kind"],
                  str(row["group_id"]) if row["group_id"] else None, row["session_id"], input=row["input"],
                  last_seq=row["last_seq"])
        lv.out.append(row["output"] or "")  # replay from last_seq would repeat deltas already flushed
        try:
            r = await hermes.call(lv.bot, "GET", f"/v1/runs/{lv.hid}")
        except ApiError:
            r = None
        if r is None or r.status_code == 404:
            await db.ex("update runs set status = 'interrupted', finished_at = now() where id = %s", rid)
        elif r.status_code == 200 and r.json().get("status") in ("completed", "failed", "cancelled", "interrupted"):
            d = r.json()
            await finalize(lv, d["status"], d)
        else:
            LIVE[rid] = lv
            lv.task = asyncio.create_task(consume(lv))
