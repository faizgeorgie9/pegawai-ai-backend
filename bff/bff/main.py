"""Pegawai AI BFF: FastAPI app. Run: uv run uvicorn bff.main:app --port 8090 (binds 127.0.0.1)."""
import asyncio
import hmac
import json
import uuid
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Header, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import bots, catalog, config, db, engine, evaluations, groups, harden, hermes, sequences, settings, usage
from .engine import LIVE, hub
from .errors import ApiError


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.open_pool()
    await catalog.sync()
    hermes.start_client()
    await engine.recover()
    await groups.recover()
    await sequences.recover()
    await bots.adopt_sessions()
    cleaner = asyncio.create_task(db.cleanup_loop())
    yield
    cleaner.cancel()
    await hermes.stop_client()
    await db.close_pool()


app = FastAPI(title="Pegawai AI BFF", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.exception_handler(ApiError)
async def _api_error(_: Request, e: ApiError):
    return JSONResponse({"error": e.message, **e.extra}, status_code=e.status)


@app.exception_handler(RequestValidationError)
async def _invalid(_: Request, e: RequestValidationError):
    return JSONResponse({"error": "Permintaan tidak valid"}, status_code=400)


@app.exception_handler(StarletteHTTPException)
async def _http(_: Request, e: StarletteHTTPException):
    msg = {404: "Tidak ditemukan", 405: "Metode tidak diizinkan"}.get(e.status_code, "Permintaan gagal")
    return JSONResponse({"error": msg}, status_code=e.status_code)


@app.exception_handler(Exception)
async def _boom(_: Request, e: Exception):
    return JSONResponse({"error": "Terjadi kesalahan di server"}, status_code=500)


def require_key(x_pegawai_ai_key: str | None = Header(default=None)) -> None:
    if not config.BFF_API_KEY or not x_pegawai_ai_key or not hmac.compare_digest(
            x_pegawai_ai_key.encode(), config.BFF_API_KEY.encode()):
        raise ApiError(401, "Kunci akses tidak valid")


def current_user() -> str:
    """The only place that knows who is calling. Login replaces this function later."""
    return "default"


public = APIRouter(prefix="/api")
api = APIRouter(prefix="/api", dependencies=[Depends(require_key)])


async def body_of(request: Request) -> dict:
    try:
        d = await request.json()
    except ValueError:
        raise ApiError(400, "Isi permintaan bukan JSON yang valid")
    if not isinstance(d, dict):
        raise ApiError(400, "Isi permintaan harus berupa objek JSON")
    return d


# ---------- SSE ----------

def _frame(type_: str, data, id_: int) -> str:
    return f"id: {id_}\nevent: {type_}\ndata: {json.dumps(data, default=str, ensure_ascii=False)}\n\n"


def sse_response(gen) -> StreamingResponse:
    return StreamingResponse(gen, media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


async def _pump(key: str, q: asyncio.Queue, first=(), skip=None):
    """Yield SSE frames for a hub queue: retry hint, first frames, live events, keepalive every 15 s."""
    n = 0
    try:
        yield "retry: 3000\n\n"
        for t, d in first:
            n += 1
            yield _frame(t, d, n)
        while True:
            try:
                t, d = await asyncio.wait_for(q.get(), 15)
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
                continue
            if skip and skip(t, d):
                continue
            n += 1
            yield _frame(t, d, n)
            if t == "done":
                return
    finally:
        hub.unsubscribe(key, q)


# ---------- health, account ----------

@public.get("/health")
async def health():
    d, h = await db.ping(), await hermes.alive()
    return {"ok": d and h, "db": d, "hermes": h}


@api.get("/me")
async def me():
    uid = current_user()
    user = await db.q1("select id, name, plan_id from users where id = %s", uid)
    plan = await engine.get_plan(uid)
    nb = (await db.q1("select count(*)::int as n from bots where user_id = %s and deleted_at is null", uid))["n"]
    ng = (await db.q1("select count(*)::int as n from groups where user_id = %s and deleted_at is null", uid))["n"]
    return {"user": user, "plan": {"id": plan["id"], "name": plan["name"]}, "limits": plan,
            "usage": {"tokens_month": await engine.tokens_month(uid), "bots": nb, "groups": ng,
                      "active_runs": await engine.active_runs(uid)}}


@api.get("/plans")
async def plans():
    return await db.q("select * from plans order by sort")


@api.put("/me/plan")
async def set_plan(request: Request):
    pid = (await body_of(request)).get("plan_id")
    if not isinstance(pid, str) or not await db.q1("select 1 as x from plans where id = %s", pid):
        raise ApiError(400, "Paket tidak dikenal")
    await db.ex("update users set plan_id = %s where id = %s", pid, current_user())
    return await me()


# ---------- bots ----------

@api.get("/templates")
async def templates():
    return await bots.templates()


@api.get("/bots")
async def list_bots():
    return await bots.list_bots(current_user())


@api.post("/bots", status_code=201)
async def create_bot(request: Request):
    return await bots.create_bot(current_user(), await body_of(request))


@api.get("/bots/{bot_id}")
async def get_bot(bot_id: str):
    return await bots.get_bot_view(current_user(), bot_id)


@api.patch("/bots/{bot_id}")
async def update_bot(bot_id: str, request: Request):
    return await bots.update_bot(current_user(), bot_id, await body_of(request))


@api.get("/tools")
async def tools(bot: str | None = None):
    """Toolsets each bot's Hermes API serves right now (GET /p/<bot>/v1/toolsets). A bot that does not answer is ok=false."""
    async def one(b: dict) -> dict:
        try:
            r = await hermes.call(b["id"], "GET", "/v1/toolsets", timeout=8)
            data = r.json()["data"] if r.status_code == 200 else None
            if not isinstance(data, list):
                raise ValueError
            ts = [{"name": t["name"], "label": t.get("label") or t["name"], "description": t.get("description") or "",
                   "tools": t.get("tools") or [], "enabled": t.get("enabled") is True} for t in data]
            return {"bot_id": b["id"], "name": b["name"], "ok": True, "toolsets": ts}
        except (ApiError, ValueError, KeyError, TypeError):
            return {"bot_id": b["id"], "name": b["name"], "ok": False, "toolsets": []}
    rows = await bots.list_bots(current_user())
    if bot:
        rows = [b for b in rows if b["id"] == bot]
        if not rows:
            raise ApiError(404, "Bot tidak ditemukan")
    return {"deny": sorted(harden.DENY), "bots": await asyncio.gather(*(one(b) for b in rows))}


@api.delete("/bots/{bot_id}", status_code=204)
async def delete_bot(bot_id: str):
    await bots.delete_bot(current_user(), bot_id)


async def _owned_session(bot_id: str, sid: str) -> None:
    await bots.get_bot(current_user(), bot_id)
    if not await db.q1("select 1 as x from chat_sessions where session_id = %s and user_id = %s and bot_id = %s",
                       sid, current_user(), bot_id):
        raise ApiError(404, "Sesi tidak ditemukan")


def _passthrough(r) -> JSONResponse:
    try:
        content = r.json()
    except ValueError:
        content = {}
    if r.status_code >= 400:
        return JSONResponse({"error": "Hermes menolak permintaan"}, status_code=502 if r.status_code >= 500 else r.status_code)
    return JSONResponse(content, status_code=r.status_code)


@api.get("/bots/{bot_id}/sessions")
async def bot_sessions(bot_id: str):
    await bots.get_bot(current_user(), bot_id)
    owned = {r["session_id"] for r in await db.q(
        "select session_id from chat_sessions where user_id = %s and bot_id = %s", current_user(), bot_id)}
    r = await hermes.call(bot_id, "GET", "/api/sessions?limit=200")
    if r.status_code != 200:
        raise ApiError(502, "Gagal mengambil riwayat chat")
    rows = [s for s in r.json().get("data", []) if s.get("id") in owned and not s["id"].startswith("grup-")]
    rows.sort(key=lambda s: s.get("last_active") or s.get("started_at") or 0, reverse=True)
    return {"object": "list", "data": rows}


@api.get("/bots/{bot_id}/sessions/{sid}/messages")
async def session_messages(bot_id: str, sid: str):
    await _owned_session(bot_id, sid)
    return _passthrough(await hermes.call(bot_id, "GET", f"/api/sessions/{sid}/messages"))


@api.patch("/bots/{bot_id}/sessions/{sid}")
async def rename_session(bot_id: str, sid: str, request: Request):
    await _owned_session(bot_id, sid)
    b = await body_of(request)
    title = b.get("title")
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
        raise ApiError(400, "Judul wajib diisi (maksimal 120 karakter)")
    return _passthrough(await hermes.call(bot_id, "PATCH", f"/api/sessions/{sid}", json_body={"title": title.strip()}))


@api.delete("/bots/{bot_id}/sessions/{sid}", status_code=204)
async def delete_session(bot_id: str, sid: str):
    await _owned_session(bot_id, sid)
    r = await hermes.call(bot_id, "DELETE", f"/api/sessions/{sid}")
    if r.status_code >= 400 and r.status_code != 404:
        raise ApiError(502, "Gagal menghapus sesi")
    await db.ex("delete from chat_sessions where session_id = %s", sid)


# ---------- runs ----------

@api.post("/bots/{bot_id}/runs", status_code=202)
async def create_run(bot_id: str, request: Request):
    uid = current_user()
    bot = await bots.get_bot(uid, bot_id)
    b = await body_of(request)
    text, sid = b.get("input"), b.get("session_id")
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 20000:
        raise ApiError(400, "Pesan wajib diisi (maksimal 20000 karakter)")
    if sid is not None:
        await _owned_session(bot_id, str(sid))
    else:
        sid = f"web-{uuid.uuid4().hex[:12]}"
        await db.ex("insert into chat_sessions (session_id, user_id, bot_id) values (%s, %s, %s)", sid, uid, bot_id)
    ins = b.get("instructions")  # optional per-run instructions (the frontend's experimental structured mode)
    if ins is not None and (not isinstance(ins, str) or len(ins) > 6000):
        raise ApiError(400, "Instruksi harus berupa teks (maksimal 6000 karakter)")
    ins = ins.strip() if isinstance(ins, str) and ins.strip() else None
    workflow, stage, test_mode = b.get("workflow"), b.get("stage"), b.get("test_mode", False)
    if workflow not in (None, "cs", "marketing"):
        raise ApiError(400, "Workflow harus cs atau marketing")
    if stage is not None and (not isinstance(stage, str) or not 1 <= len(stage.strip()) <= 60):
        raise ApiError(400, "Stage harus berupa teks (maksimal 60 karakter)")
    if not isinstance(test_mode, bool):
        raise ApiError(400, "test_mode harus true atau false")
    origin = engine.clean_origin(b.get("origin")) or engine.infer_origin(None, workflow)
    context = None
    if workflow:
        ins, context = await engine.workflow_context(bot, workflow, stage, test_mode, text, ins)
    run = await engine.start_run(uid, bot_id, sid, text.strip(), "chat", instructions=ins, context=context, origin=origin)
    return {"run": engine.run_view(run), "session_id": sid}


@api.get("/products/search")
async def products_search(q: str | None = None, category: str | None = None, max_price: int | None = None,
                          color: str | None = None, size: str | None = None, limit: int = 5):
    """Catalog search: Postgres text search on q plus structured filters. At least one of them is required."""
    if not any((q and q.strip(), category, max_price is not None, color, size)):
        raise ApiError(400, "Isi q atau salah satu filter (category, max_price, color, size)")
    if any(v is not None and len(v) > 200 for v in (q, category, color, size)):
        raise ApiError(400, "Parameter pencarian terlalu panjang")
    rows = await catalog.search_products(q, category, max_price, color, size, limit)
    return {"data": rows, "count": len(rows)}


@api.get("/runs")
async def list_runs(status: str = "recent", limit: int = 30, bot: str | None = None):
    limit = max(1, min(limit, 100))
    cond = "r.status = any(%s)" if status == "active" else "not (r.status = any(%s))"
    rows = await db.q(f"select r.id, r.bot_id, b.name as bot_name, r.kind, r.status, left(r.input, 120) as input, "
                      f"r.group_id, r.session_id, r.total_tokens, r.created_at, r.finished_at, r.meta->'origin' as origin, r.meta->>'workflow' as wf "
                      f"from runs r join bots b on b.id = r.bot_id where r.user_id = %s and {cond} "
                      f"and (%s::text is null or r.bot_id = %s) order by r.created_at desc limit %s",
                      current_user(), list(engine.ACTIVE), bot, bot, limit)
    for r in rows:  # runs from before origin existed: infer it
        r["origin"] = r["origin"] or engine.infer_origin(r["group_id"], r["wf"])
        del r["wf"]
    return rows


async def _owned_run(rid: str) -> dict:
    try:
        uuid.UUID(rid)
    except ValueError:
        raise ApiError(404, "Tugas tidak ditemukan")
    row = await db.q1("select * from runs where id = %s and user_id = %s", rid, current_user())
    if not row:
        raise ApiError(404, "Tugas tidak ditemukan")
    return row


async def _run_events(rid: str) -> list[dict]:
    return await db.q("select seq, type, payload, created_at from run_events where run_id = %s "
                      "and (type like 'tool.%%' or type like 'approval.%%') order by seq, id", rid)


@api.get("/runs/{rid}")
async def get_run(rid: str):
    row = await _owned_run(rid)
    return {**engine.run_view(row), "events": await _run_events(rid)}


@api.get("/runs/{rid}/stream")
async def run_stream(rid: str):
    await _owned_run(rid)
    q = hub.subscribe(rid)  # subscribe first so nothing is lost between the snapshot and the live part
    try:
        row = await _owned_run(rid)
        lv = LIVE.get(rid)
        out = "".join(lv.out) if lv else row["output"]
        snap = {"output": out, "status": row["status"], "events": await _run_events(rid),
                "reasoning": "\n\n".join(lv.steps) if lv else row["reasoning"] or "",
                "clarify": lv.clarify if lv else None}
        first = [("snapshot", snap)]
        if row["status"] not in engine.ACTIVE:
            first.append(("done", {"status": row["status"], "output": row["output"], "reasoning": row["reasoning"],
                                   "error": row["error"], "usage": {"input_tokens": row["input_tokens"],
                                                                    "output_tokens": row["output_tokens"],
                                                                    "total_tokens": row["total_tokens"]},
                                   **engine.done_extra(row["meta"])}))
            hub.unsubscribe(rid, q)
            return sse_response(_one_shot(first))
    except BaseException:
        hub.unsubscribe(rid, q)
        raise
    # deltas already inside the snapshot are skipped by their end offset
    return sse_response(_pump(rid, q, first, skip=lambda t, d: t == "delta" and d.get("end", 0) <= len(out)))


async def _one_shot(first):
    yield "retry: 3000\n\n"
    for i, (t, d) in enumerate(first, 1):
        yield _frame(t, d, i)


@api.post("/runs/{rid}/stop")
async def stop_run(rid: str):
    return await engine.stop(current_user(), rid)


@api.post("/runs/{rid}/steer")
async def steer_run(rid: str, request: Request):
    text = (await body_of(request)).get("text")
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 4000:
        raise ApiError(400, "Pesan wajib diisi (maksimal 4000 karakter)")
    return await engine.steer(current_user(), rid, text.strip())


@api.post("/runs/{rid}/approval")
async def approve_run(rid: str, request: Request):
    return await engine.approval(current_user(), rid, (await body_of(request)).get("choice"))


@api.post("/runs/{rid}/clarify")
async def clarify_run(rid: str, request: Request):
    return await engine.clarify(current_user(), rid, (await body_of(request)).get("answer"))


# ---------- settings ----------

@api.get("/models")
async def models():
    return await settings.catalog(current_user())


@api.get("/settings")
async def get_settings():
    return await settings.get(current_user())


@api.patch("/settings")
async def patch_settings(request: Request):
    return await settings.patch(current_user(), await body_of(request))


@api.get("/settings/security")
async def settings_security():
    return await settings.security(current_user())


@api.get("/settings/knowledge")
async def settings_knowledge():
    return {"retention_days": settings.RETENTION_DAYS, "docs": settings.knowledge_docs()}


@api.get("/export/history")
async def export_history():
    data = await settings.export_history(current_user())
    return JSONResponse(jsonable_encoder(data), headers={"Content-Disposition": 'attachment; filename="riwayat-chat.json"'})


# ---------- sequences (multi-turn runs that continue on the server) ----------

@api.post("/bots/{bot_id}/sequences", status_code=202)
async def create_sequence(bot_id: str, request: Request):
    return await sequences.create(current_user(), bot_id, await body_of(request))


@api.get("/sequences")
async def list_sequences(case_id: str | None = None, limit: int = 1):
    return await sequences.list_for(current_user(), case_id, limit)


@api.get("/sequences/{sid}")
async def get_sequence(sid: str):
    return await sequences.get_view(current_user(), _seq_id(sid))


@api.post("/sequences/{sid}/stop")
async def stop_sequence(sid: str):
    return await sequences.stop(current_user(), _seq_id(sid))


def _seq_id(v: str) -> str:
    try:
        return str(uuid.UUID(v))
    except ValueError:
        raise ApiError(404, "Urutan tidak ditemukan")


# ---------- groups ----------

@api.get("/groups")
async def list_groups():
    return await groups.list_groups(current_user())


@api.post("/groups", status_code=201)
async def create_group(request: Request):
    b = await body_of(request)
    return await groups.create_group(current_user(), b.get("name"), b.get("bot_ids"))


@api.patch("/groups/{gid}")
async def update_group(gid: str, request: Request):
    b = await body_of(request)
    return await groups.update_group(current_user(), _uuid(gid), b.get("name"), b.get("bot_ids"))


@api.delete("/groups/{gid}", status_code=204)
async def delete_group(gid: str):
    await groups.delete_group(current_user(), _uuid(gid))


def _uuid(v: str) -> str:
    try:
        return str(uuid.UUID(v))
    except ValueError:
        raise ApiError(404, "Grup tidak ditemukan")


@api.get("/groups/{gid}/live")
async def group_live(gid: str):
    return await groups.live(current_user(), gid)


@api.get("/groups/{gid}/messages")
async def group_messages(gid: str, before: int | None = None, limit: int = 50):
    return await groups.list_messages(current_user(), _uuid(gid), before, limit)


@api.post("/groups/{gid}/messages", status_code=202)
async def send_group_message(gid: str, request: Request):
    b = await body_of(request)
    return await groups.send(current_user(), _uuid(gid), b.get("text"), b.get("mode") or "queue")


@api.post("/groups/{gid}/stop")
async def stop_group(gid: str):
    return await groups.stop(current_user(), _uuid(gid))


# ---------- activity, events, office ----------

@api.get("/activity")
async def activity(bot: str | None = None, status: str | None = None, limit: int = 100, before: int | None = None,
                   session_id: str | None = None, group_id: str | None = None):
    limit = max(1, min(limit, 500))
    group_id = _uuid(group_id) if group_id else None
    if status not in (None, "ok", "error"):
        raise ApiError(400, "Status harus ok atau error")
    rows = await db.q(
        "select e.id, e.created_at as time, r.bot_id as bot, b.name as bot_name, e.payload->>'tool' as tool, "
        "case when e.payload->>'error' = 'true' then 'error' else 'ok' end as status, "
        "(e.payload->>'duration')::float as duration, "
        "coalesce(nullif(e.payload->>'preview', ''), s.payload->>'preview') as preview, r.id as run_id, r.kind, "
        "coalesce(g.name, 'Chat') as source "
        "from run_events e join runs r on r.id = e.run_id join bots b on b.id = r.bot_id "
        "left join groups g on g.id = r.group_id "
        # lateral + limit 1: a run can store several tool.started events with the same tool_call_id, and a plain
        # join then repeated the completed row (duplicate ids in the activity list)
        "left join lateral (select s.payload from run_events s where s.run_id = e.run_id and s.type = 'tool.started' "
        "and s.payload->>'tool_call_id' = e.payload->>'tool_call_id' and e.payload ? 'tool_call_id' "
        "order by s.id desc limit 1) s on true "
        "where e.type = 'tool.completed' and r.user_id = %s and (%s::text is null or r.bot_id = %s) "
        "and (%s::text is null or (case when e.payload->>'error' = 'true' then 'error' else 'ok' end) = %s) "
        "and (%s::bigint is null or e.id < %s) and (%s::text is null or r.session_id = %s) "
        "and (%s::uuid is null or r.group_id = %s) order by e.id desc limit %s",
        current_user(), bot, bot, status, status, before, before, session_id, session_id, group_id, group_id, limit)
    return rows


def _scope(session_id: str | None, group_id: str | None) -> tuple[str | None, str | None]:
    if bool(session_id) == bool(group_id):
        raise ApiError(400, "Isi salah satu: session_id atau group_id")
    return session_id, _uuid(group_id) if group_id else None


@api.get("/usage")
async def usage_of(session_id: str | None = None, group_id: str | None = None):
    sid, gid = _scope(session_id, group_id)
    return await usage.conversation(current_user(), sid, gid)


@api.get("/usage/bots")
async def usage_bots(period: str = "month"):
    if period not in ("month", "all"):
        raise ApiError(400, "Periode harus month atau all")
    return await usage.per_bot(current_user(), period)


@api.get("/thinking")
async def thinking(session_id: str | None = None, group_id: str | None = None):
    """Thinking per bot turn of one conversation, oldest first. Running turns are included even when still empty."""
    sid, gid = _scope(session_id, group_id)
    col, val = ("r.group_id", gid) if gid else ("r.session_id", sid)
    return await db.q(
        "select * from (select r.id as run_id, r.bot_id, r.status, r.created_at, r.started_at, r.finished_at, r.reasoning, "
        "floor(extract(epoch from r.finished_at - coalesce(r.started_at, r.created_at)))::int as seconds from runs r "
        f"where r.user_id = %s and {col} = %s and (r.reasoning is not null or r.status = any(%s)) "
        "order by r.created_at desc limit 50) t order by created_at", current_user(), val, list(engine.ACTIVE))


@api.get("/events")
async def events():
    q = hub.subscribe("*")
    return sse_response(_pump("*", q))


@api.get("/office")
async def office():
    uid = current_user()
    gs = []
    for g in await groups.list_groups(uid):
        msgs = await db.q("select * from (select id, author, bot_id, text, created_at from group_messages "
                          "where group_id = %s order by id desc limit 5) t order by id", g["id"])
        gs.append({**g, "messages": msgs})
    return {"bots": await bots.list_bots(uid), "groups": gs}


# ---------- evaluations ----------

@api.get("/evaluations")
async def list_evaluations():
    return await evaluations.list_all(current_user())


@api.get("/evaluations/summary")
async def evaluations_summary():
    return await evaluations.summary(current_user())


@api.post("/evaluations", status_code=201)
async def create_evaluation(request: Request):
    return await evaluations.create(current_user(), await body_of(request))


@api.patch("/evaluations/{eid}")
async def update_evaluation(eid: str, request: Request):
    return await evaluations.update(current_user(), eid, await body_of(request))


app.include_router(public)
app.include_router(api)
