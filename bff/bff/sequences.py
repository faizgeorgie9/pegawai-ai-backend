"""Sequences: several turns of one conversation, run in order on the server (so they finish when the page is closed)."""
import asyncio
import uuid
from typing import Awaitable, Callable

from psycopg.types.json import Jsonb

from . import bots, db, engine, knowledge
from .errors import ApiError

MAX_TURNS, MAX_TURN_LEN = 10, 20000
ACTIVE = ("queued", "running")
STOPS: set[str] = set()  # sequence ids asked to stop
TASKS: dict[str, asyncio.Task] = {}


def clean(b: dict) -> dict:
    """Validate the POST /bots/{id}/sequences body. The bot and the workflow/team match are checked by create()."""
    turns = b.get("turns")
    if not isinstance(turns, list) or not 1 <= len(turns) <= MAX_TURNS:
        raise ApiError(400, f"turns harus berisi 1 sampai {MAX_TURNS} pesan")
    if any(not isinstance(t, str) or not 1 <= len(t.strip()) <= MAX_TURN_LEN for t in turns):
        raise ApiError(400, f"Setiap pesan wajib diisi (maksimal {MAX_TURN_LEN} karakter)")
    workflow, stage, test_mode = b.get("workflow"), b.get("stage"), b.get("test_mode", False)
    if workflow not in (None, "cs", "marketing"):
        raise ApiError(400, "Workflow harus cs atau marketing")
    if stage is not None and (not isinstance(stage, str) or not 1 <= len(stage.strip()) <= 60):
        raise ApiError(400, "Stage harus berupa teks (maksimal 60 karakter)")
    if not isinstance(test_mode, bool):
        raise ApiError(400, "test_mode harus true atau false")
    origin = engine.clean_origin(b.get("origin"))
    if not origin or origin["type"] != "evaluasi" or not origin.get("case_id"):
        raise ApiError(400, "Origin harus berupa {type: evaluasi, case_id}")
    return {"turns": [t.strip() for t in turns], "workflow": workflow, "stage": stage.strip() if stage else None,
            "test_mode": test_mode, "origin": origin}


async def drive(turns: list[str], start: Callable[[int, str], Awaitable[dict]],
                wait: Callable[[str], Awaitable[dict]], save: Callable[..., Awaitable[None]],
                stopped: Callable[[], bool]) -> None:
    """Run the turns one after the other. Stops at the first turn that does not complete and records why.
    start(i, text) starts the run of turn i and returns its row; wait(run_id) returns the finished row."""
    n, run_ids = len(turns), []
    try:
        for i, text in enumerate(turns):
            if stopped():
                return await save(status="stopped", error=f"Dihentikan sebelum giliran {i + 1} dari {n}")
            await save(status="running", current_turn=i + 1)
            try:
                run = await start(i, text)
            except ApiError as e:
                return await save(status="failed", error=f"Giliran {i + 1} dari {n}: {e.message}")
            run_ids.append(str(run["id"]))
            await save(run_ids=run_ids)
            done = await wait(str(run["id"]))
            st = done["status"]
            if st != "completed":
                gone = st == "cancelled" or stopped()
                why = done.get("error") or ("dihentikan" if gone else "tidak selesai")
                return await save(status="stopped" if gone else "failed", error=f"Giliran {i + 1} dari {n}: {why}")
        await save(status="completed")
    except asyncio.CancelledError:
        raise
    except Exception as e:  # never leave a sequence stuck in "running"
        await save(status="failed", error=f"Kesalahan internal: {type(e).__name__}")


async def _save(seq_id: str, **f) -> None:
    sets = ", ".join(f"{k} = %s" for k in f)
    vals = [Jsonb(v) if k == "run_ids" else v for k, v in f.items()]
    await db.ex(f"update sequences set {sets}, updated_at = now() where id = %s", *vals, seq_id)


async def _run_task(seq_id: str, uid: str, bot: dict, session_id: str, v: dict) -> None:
    async def start(i: int, text: str) -> dict:
        ins, ctx = None, None
        if v["workflow"]:
            ins, ctx = await engine.workflow_context(bot, v["workflow"], v["stage"], v["test_mode"], text, None)
        origin = {**v["origin"], "sequence_id": seq_id, "turn": i + 1, "of": len(v["turns"])}
        return await engine.start_run(uid, bot["id"], session_id, text, "chat", instructions=ins, context=ctx, origin=origin)

    async def save(**f):
        await _save(seq_id, **f)

    try:
        await drive(v["turns"], start, engine.wait_done, save, lambda: seq_id in STOPS)
    finally:
        STOPS.discard(seq_id)
        TASKS.pop(seq_id, None)


async def create(uid: str, bot_id: str, body: dict) -> dict:
    bot = await bots.get_bot(uid, bot_id)
    v = clean(body)
    if v["workflow"]:  # same team/workflow rule as the run endpoint (raises 400 on a mismatch)
        knowledge.build_context(bot["team"], v["workflow"], None, [], False)
    await engine.check_quota(uid)  # fail now (402) instead of inside the background task
    sid, seq_id = f"web-{uuid.uuid4().hex[:12]}", str(uuid.uuid4())
    await db.ex("insert into chat_sessions (session_id, user_id, bot_id) values (%s, %s, %s)", sid, uid, bot_id)
    await db.ex("insert into sequences (id, user_id, bot_id, session_id, origin, turns) values (%s, %s, %s, %s, %s, %s)",
                seq_id, uid, bot_id, sid, Jsonb(v["origin"]), Jsonb(v["turns"]))
    TASKS[seq_id] = asyncio.create_task(_run_task(seq_id, uid, bot, sid, v))
    return await get_view(uid, seq_id)


async def _owned(uid: str, seq_id: str) -> dict:
    row = await db.q1("select * from sequences where id = %s and user_id = %s", seq_id, uid)
    if not row:
        raise ApiError(404, "Urutan tidak ditemukan")
    return row


async def view(row: dict) -> dict:
    """Public shape: status, progress and, per turn, the output and structured result of its run."""
    ids = row["run_ids"]
    runs = {str(r["id"]): r for r in await db.q("select * from runs where id = any(%s::uuid[])", ids)} if ids else {}
    out = []
    for i, rid in enumerate(ids):
        r = runs.get(rid)
        if not r:
            continue
        meta = r["meta"] or {}
        out.append({"turn": i + 1, "run_id": rid, "status": r["status"], "input": row["turns"][i], "output": r["output"] or "",
                    "error": r["error"], "structured": meta.get("structured"), "validation": meta.get("validation"),
                    "context_refs": meta.get("context_refs") or []})
    return {"id": str(row["id"]), "bot_id": row["bot_id"], "session_id": row["session_id"], "origin": row["origin"],
            "status": row["status"], "current_turn": row["current_turn"], "of": len(row["turns"]), "run_ids": ids,
            "turns": out, "error": row["error"], "created_at": row["created_at"], "updated_at": row["updated_at"]}


async def get_view(uid: str, seq_id: str) -> dict:
    return await view(await _owned(uid, seq_id))


async def list_for(uid: str, case_id: str | None, limit: int) -> list[dict]:
    limit = max(1, min(limit, 20))
    rows = await db.q("select * from sequences where user_id = %s and (%s::text is null or origin->>'case_id' = %s) "
                      "order by created_at desc limit %s", uid, case_id, case_id, limit)
    return [await view(r) for r in rows]


async def stop(uid: str, seq_id: str) -> dict:
    row = await _owned(uid, seq_id)
    if row["status"] not in ACTIVE:
        raise ApiError(409, "Urutan sudah selesai")
    STOPS.add(seq_id)
    if row["run_ids"]:  # the running turn, if any; a turn that just ended makes this a no-op
        try:
            await engine.stop(uid, row["run_ids"][-1])
        except ApiError:
            pass
    return {"status": "stopping"}


async def recover() -> None:
    """A restart loses the background tasks: say so instead of pretending they continue."""
    await db.ex("update sequences set status = 'failed', error = 'Dihentikan karena server dimulai ulang', "
                "updated_at = now() where status = any(%s)", list(ACTIVE))
