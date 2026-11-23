"""Pegawai AI BFF: FastAPI app. Run: uv run uvicorn bff.main:app --port 8090 (binds 127.0.0.1)."""
import asyncio
import hmac
import json
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from urllib.parse import quote

from fastapi import APIRouter, Depends, FastAPI, File, Header, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response, StreamingResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import actions, apps, auth, bots, bridge, catalog, config, connections, costs, db, engine, evaluations, groups, harden, hermes, integrations, kb, mcp_privileges, memory, product_images, scheduler, sequences, settings, tasks, usage, whatsapp
from .engine import LIVE, hub
from .errors import ApiError


bridge_app = bridge.BridgeApp(bridge.build())  # MCP tools for the Hermes agents at /mcp (see bridge.py)


@asynccontextmanager
async def lifespan(app: FastAPI):
    bridge.ensure_key()
    await asyncio.to_thread(bridge.ensure_registered)
    await db.open_pool()
    await catalog.sync()
    hermes.start_client()
    await engine.recover()
    await groups.recover()
    await sequences.recover()
    await scheduler.recover()
    await kb.recover()
    await bots.adopt_sessions()
    cleaner = asyncio.create_task(db.cleanup_loop())
    sched = asyncio.create_task(scheduler.loop())
    async with bridge_app.mcp.session_manager.run():
        yield
    cleaner.cancel()
    sched.cancel()
    await hermes.stop_client()
    await db.close_pool()


app = FastAPI(title="Pegawai AI BFF", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

_current_user_var: ContextVar[str] = ContextVar("current_user", default="default")


@app.middleware("http")
async def auth_context_middleware(request: Request, call_next):
    auth_header = request.headers.get("Authorization")
    user_id = "default"
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = auth.decode_token(token)
            user_id = payload.get("sub", "default")
        except Exception:
            pass
    token_reset = _current_user_var.set(user_id)
    try:
        response = await call_next(request)
        return response
    finally:
        _current_user_var.reset(token_reset)


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
    """Returns the authenticated user ID extracted from Bearer token, or 'default' fallback."""
    return _current_user_var.get()


public = APIRouter(prefix="/api")
api = APIRouter(prefix="/api", dependencies=[Depends(require_key)])


# ---------- Authentication Endpoints (Sprint 5) ----------

@public.post("/auth/login")
async def auth_login(request: Request):
    """Authenticate user with email and password, returning a JWT token and user profile."""
    b = await body_of(request)
    email = b.get("email", "")
    password = b.get("password", "")
    res = await auth.authenticate(email, password)
    return JSONResponse(res)


@public.post("/auth/register")
async def auth_register(request: Request):
    """Register a new user account with hashed password and return a JWT token."""
    b = await body_of(request)
    name = b.get("name", "")
    email = b.get("email", "")
    password = b.get("password", "")
    company = b.get("company", "Colorbox")
    res = await auth.register(name, email, password, company)
    return JSONResponse(res)


@public.get("/auth/me")
async def auth_me(request: Request):
    """Retrieve current authenticated user profile using Bearer token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise ApiError(401, "Kredensial login tidak valid atau belum login")
    token = auth_header.split(" ", 1)[1]
    payload = auth.decode_token(token)
    user_id = payload.get("sub")
    user = await auth.get_user_by_id(user_id)
    if not user:
        raise ApiError(404, "Data pengguna tidak ditemukan")
    return JSONResponse(jsonable_encoder({"ok": True, "user": user}))


@public.post("/auth/logout")
async def auth_logout():
    """Client-side logout acknowledgement."""
    return JSONResponse({"ok": True, "message": "Berhasil logout"})


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
    month = await costs.month(uid, plan["monthly_usd"])
    return {"user": user, "plan": {"id": plan["id"], "name": plan["name"]}, "limits": plan_view(plan),
            "usage": {"tokens_month": await engine.tokens_month(uid), "bots": nb, "groups": ng,
                      "active_runs": await engine.active_runs(uid),
                      **{k: month[k] for k in ("cost", "limit", "remaining", "percent", "state", "basis")}}}


def plan_view(plan: dict) -> dict:
    """monthly_usd travels as an exact decimal string, not a float."""
    return {**plan, "monthly_usd": costs.money(plan["monthly_usd"])}


@api.get("/plans")
async def plans():
    return [plan_view(p) for p in await db.q("select * from plans order by sort")]


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


# ---- Aplikasi: Hermes connector catalog and per-agent skills (apps.py) ----
@api.get("/apps/catalog")
async def apps_catalog(fresh: int = 0):
    return {"categories": [{"id": i, "name": n} for i, n in apps.CATEGORIES], "apps": await apps.catalog(bool(fresh))}


@api.post("/apps/{app_id}/connect")
async def apps_connect(app_id: str):
    return await apps.connect(app_id)


@api.get("/apps/{app_id}/status")
async def apps_status(app_id: str):
    return await apps.status(app_id)


@api.post("/apps/{app_id}/disconnect", status_code=204)
async def apps_disconnect(app_id: str):
    await apps.disconnect(app_id)


@api.get("/skills")
async def skills_all():
    return await apps.all_skills(current_user())


@api.get("/agents/{slug}/skills")
async def agent_skills(slug: str):
    return {"skills": await apps.agent_skills(current_user(), slug)}


@api.put("/agents/{slug}/skills")
async def agent_skill_set(slug: str, request: Request):
    b = await body_of(request)
    return {"skills": await apps.set_skill(current_user(), slug, b.get("name"), b.get("enabled") is True)}


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
        return JSONResponse({"error": "Mesin agen menolak permintaan"}, status_code=502 if r.status_code >= 500 else r.status_code)
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


# ---- Ingatan: what one agent remembers long-term (Hermes MEMORY.md / USER.md) ----
# File I/O and Hermes' lock live in memory.py; every route first proves the caller owns the bot.

@api.get("/bots/{bot_id}/memory")
async def bot_memory(bot_id: str):
    await bots.get_bot(current_user(), bot_id)
    return await asyncio.to_thread(memory.snapshot, bot_id)


@api.delete("/bots/{bot_id}/memory/{item_id}", status_code=204)
async def delete_memory_item(bot_id: str, item_id: str):
    await bots.get_bot(current_user(), bot_id)
    await asyncio.to_thread(memory.delete_item, bot_id, item_id)


@api.delete("/bots/{bot_id}/memory", status_code=204)
async def clear_bot_memory(bot_id: str, request: Request, confirm: bool = False):
    await bots.get_bot(current_user(), bot_id)
    if not confirm:
        try:
            body = await request.json()
        except ValueError:
            body = {}
        confirm = isinstance(body, dict) and body.get("confirm") is True
    if not confirm:
        raise ApiError(400, "Konfirmasi diperlukan untuk menghapus semua ingatan")
    await asyncio.to_thread(memory.clear_all, bot_id)


# ---------- runs ----------

@api.post("/bots/{bot_id}/runs", status_code=202)
async def create_run(bot_id: str, request: Request):
    uid = current_user()
    bot = await bots.get_bot(uid, bot_id)
    b = await body_of(request)
    text, sid = b.get("input"), b.get("session_id")
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 20000:
        raise ApiError(400, "Pesan wajib diisi (maksimal 20000 karakter)")
    kb_ids = await kb.owned_ids(uid, b.get("kb_items"))
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
    saved = []
    if workflow != "cs":  # CS runs only see the authorized CS evidence (knowledge v2.1), never the user's own files
        saved = await kb.save_links(uid, text)
        if block := await kb.retrieve(uid, text, kb_ids, saved, bot_id=bot_id):
            ins = f"{ins}\n\n{block}" if ins else block
    run = await engine.start_run(uid, bot_id, sid, text.strip(), "chat", instructions=ins, context=context, origin=origin)
    return {"run": engine.run_view(run), "session_id": sid, "kb": saved}


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


@public.get("/product-images/{name}")
async def product_image(name: str):
    """Bundled product photos. Only plain *.jpg names that exist in the assets folder are served (no path traversal)."""
    p = product_images.safe_image_path(name)
    if not p:
        raise ApiError(404, "Foto produk tidak ditemukan")
    return FileResponse(p, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})


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


# ---------- knowledge base (the user's own files and links) ----------

@api.get("/kb/items")
async def kb_items():
    return await kb.list_items(current_user())


@api.post("/kb/files", status_code=201)
async def kb_upload(request: Request, file: UploadFile = File(...)):
    if int(request.headers.get("content-length") or 0) > kb.MAX_FILE_BYTES + 1024 * 1024:  # before reading the whole body
        raise ApiError(413, f"Berkas terlalu besar (maksimal {kb.MAX_FILE_BYTES // (1024 * 1024)} MB).")
    data = await file.read(kb.MAX_FILE_BYTES + 1)
    return await kb.ingest_file(current_user(), file.filename or "", data)


@api.post("/kb/links", status_code=201)
async def kb_add_link(request: Request):
    url = (await body_of(request)).get("url")
    if not isinstance(url, str):
        raise ApiError(400, "Alamat web wajib diisi")
    return await kb.ingest_url(current_user(), url.strip())


@api.delete("/kb/items/{item_id}", status_code=204)
async def kb_delete(item_id: str):
    await kb.delete_item(current_user(), item_id)


@api.get("/kb/{item_id}/file")
async def kb_file(item_id: str):
    name, mime, data = await kb.get_file(current_user(), item_id)
    disp = "attachment" if mime.endswith("wordprocessingml.document") else "inline"  # Word cannot be shown by a browser
    return Response(data, media_type=mime, headers={
        "Content-Disposition": f"{disp}; filename*=UTF-8''{quote(name, safe='')}",
        "X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"})


@api.get("/kb/{item_id}/text")
async def kb_text(item_id: str):
    return await kb.get_text(current_user(), item_id)


@api.post("/kb/items/{item_id}/refresh")
async def kb_refresh(item_id: str):
    return await integrations.refresh_item(current_user(), item_id)


@api.get("/kb/matrix")
async def kb_access_matrix():
    """Retrieve the per-agent KB privilege and access matrix."""
    return kb.get_kb_access_matrix()


@api.get("/kb/access-check")
async def kb_access_check(bot_id: str, item_id: str | None = None, category: str | None = None):
    """Verify if a specific agent has permission to access a KB item or category."""
    cat = category
    item_name = ""
    if item_id and not cat:
        item = await db.q1("select * from kb_items where id = %s and user_id = %s", kb._own_id(item_id), current_user())
        if not item:
            raise ApiError(404, "Item tidak ditemukan")
        cat = item.get("category", "general")
        item_name = item.get("name", "")
    
    cat = cat or "general"
    allowed = kb.can_agent_access_item(bot_id, cat, item_name)
    reason = (
        f"Agen '{bot_id}' diizinkan mengakses dokumen kategori '{cat}'."
        if allowed else
        f"Akses ditolak: Agen '{bot_id}' tidak memiliki izin mengakses dokumen kategori '{cat}'. Dokumen Finance/Keuangan terisolasi."
    )
    return {
        "bot_id": bot_id,
        "category": cat,
        "item_id": item_id,
        "item_name": item_name,
        "allowed": allowed,
        "reason": reason
    }


@api.post("/kb/items/{item_id}/category")
async def kb_update_category(item_id: str, request: Request):
    """Categorize a KB item (general, finance, cs, marketing, catalog, hr, legal)."""
    body = await body_of(request)
    category = body.get("category")
    if not category or category not in ("general", "finance", "cs", "marketing", "catalog", "hr", "legal"):
        raise ApiError(400, "Kategori tidak valid (pilih: general, finance, cs, marketing, catalog, hr, legal)")
    
    updated = await db.q1(
        "update kb_items set category = %s where id = %s and user_id = %s returning *",
        category, kb._own_id(item_id), current_user()
    )
    if not updated:
        raise ApiError(404, "Item tidak ditemukan")
    return kb.view(updated)


# ---------- mcp multi-account privileges ----------

@api.get("/mcp/privileges")
async def mcp_privileges_list():
    """List configured MCP accounts, privilege tiers (Read/Write/Admin), and tool classifications."""
    return mcp_privileges.list_mcp_privileges()


@api.post("/mcp/verify")
async def mcp_verify_privilege(request: Request):
    """Verify whether a bot/account can call an MCP tool without executing it."""
    body = await body_of(request)
    bot_id = body.get("bot_id", "default")
    tool_name = body.get("tool_name")
    account_id = body.get("account_id")
    if not tool_name:
        raise ApiError(400, "tool_name wajib diisi")
    
    allowed, reason = mcp_privileges.check_mcp_privilege(bot_id, tool_name, account_id)
    return {
        "bot_id": bot_id,
        "tool_name": tool_name,
        "account_id": account_id,
        "allowed": allowed,
        "required_privilege": mcp_privileges.TOOL_PRIVILEGES.get(tool_name, "write"),
        "agent_privilege": mcp_privileges.get_agent_privilege(bot_id).value,
        "reason": reason
    }


# ---------- connections (Google Drive, Gmail) ----------

@api.get("/connections")
async def connections_list(fresh: bool = False):
    return await integrations.list_checked(current_user(), fresh)


@api.post("/connections/{provider}/start")
async def connections_start(provider: str):
    return await connections.start(current_user(), provider)


@api.get("/connections/{family}/callback")
async def connections_callback(family: str, request: Request):
    """The provider sends the browser here after consent (through the same proxy as the app, so the key header is present)."""
    if family != "google":
        raise ApiError(404, "Tidak ditemukan")
    return RedirectResponse(await connections.callback(current_user(), family, dict(request.query_params)), status_code=303)


@api.delete("/connections/{provider}", status_code=204)
async def connections_disconnect(provider: str):
    await connections.disconnect(current_user(), provider)


@api.get("/connections/gdrive/files")
async def drive_files(q: str = "", page: str | None = None):
    return await integrations.drive_list(current_user(), q, page)


@api.post("/connections/gdrive/import")
async def drive_import(request: Request):
    return {"items": await integrations.drive_import(current_user(), (await body_of(request)).get("ids"))}


@api.post("/connections/gmail/draft", status_code=201)
async def gmail_draft(request: Request):
    b = await body_of(request)
    return await integrations.gmail_draft(current_user(), b.get("to"), b.get("subject"), b.get("body"))


@api.get("/tools/integrations")
async def tools_integrations():
    """Unified status overview of all third-party tool integrations (Google Drive, Gmail, Notion, WhatsApp)."""
    try:
        conns = await integrations.list_checked(current_user(), False)
    except Exception:
        conns = []
    conn_map = {c["provider"]: c for c in conns}
    try:
        notion_status = await asyncio.wait_for(apps.status("notion"), timeout=4.0)
    except Exception:
        notion_status = {"status": "not_connected", "waiting": False}
    wa_status = await whatsapp.get_status()
    return {
        "tools": [
            {
                "id": "gdrive",
                "name": "Google Drive",
                "category": "docs",
                "type": "oauth",
                "configured": conn_map.get("gdrive", {}).get("configured", False),
                "status": conn_map.get("gdrive", {}).get("status", "disconnected"),
                "account": conn_map.get("gdrive", {}).get("account"),
                "redirect_uri": conn_map.get("gdrive", {}).get("redirect_uri")
            },
            {
                "id": "gmail",
                "name": "Gmail",
                "category": "comms",
                "type": "oauth",
                "configured": conn_map.get("gmail", {}).get("configured", False),
                "status": conn_map.get("gmail", {}).get("status", "disconnected"),
                "account": conn_map.get("gmail", {}).get("account"),
                "redirect_uri": conn_map.get("gmail", {}).get("redirect_uri")
            },
            {
                "id": "notion",
                "name": "Notion",
                "category": "docs",
                "type": "connector",
                "configured": True,
                "status": notion_status.get("status", "not_connected"),
                "waiting": notion_status.get("waiting", False)
            },
            {
                "id": "whatsapp",
                "name": "WhatsApp Business",
                "category": "comms",
                "type": "webhook",
                "configured": wa_status.get("webhook_verify_token_configured", True),
                "status": wa_status.get("status", "ready"),
                "webhook_url": wa_status.get("webhook_url")
            }
        ]
    }


@api.get("/connections/notion/status")
async def notion_connection_status():
    return await apps.status("notion")


@api.post("/connections/notion/start")
async def notion_connection_start():
    return await apps.connect("notion")


# ---------- whatsapp routing & webhook ----------

@public.get("/whatsapp/webhook")
async def whatsapp_webhook_verify(request: Request):
    """Meta WhatsApp Webhook verification handshake or browser status check."""
    mode = request.query_params.get("hub.mode", "")
    token = request.query_params.get("hub.verify_token", "")
    challenge = request.query_params.get("hub.challenge", "")
    if mode or token or challenge:
        verified_challenge = whatsapp.verify_token(mode, token, challenge)
        return PlainTextResponse(verified_challenge)
    
    # If opened directly in browser without handshake query parameters:
    conn = await whatsapp.get_evolution_connection_state()
    return {
        "status": "active",
        "gateway": "WhatsApp Webhook Gateway (Evolution API & Meta Cloud API)",
        "instance": whatsapp.EVOLUTION_INSTANCE,
        "connection_state": conn.get("instance", {}).get("state", "open"),
        "note": "Incoming WhatsApp messages are received via HTTP POST."
    }


@public.post("/whatsapp/webhook")
async def whatsapp_webhook_post(request: Request):
    """Receive incoming WhatsApp messages (Meta Cloud API format or direct simulation)."""
    try:
        body = await request.json()
    except Exception:
        raise ApiError(400, "Payload harus berupa JSON valid")
    
    messages = whatsapp.parse_webhook_payload(body)
    if not messages:
        return {"status": "ok", "processed": 0, "messages": []}

    results = []
    for m in messages:
        msg_id = m.get("message_id")
        if msg_id and whatsapp.is_duplicate_message(msg_id):
            log.info("Skipping duplicate WhatsApp message_id: %s from %s", msg_id, m.get("sender"))
            continue
        res = await whatsapp.route_and_process_message(
            user_id="default",
            sender=m["sender"],
            customer_name=m["customer_name"],
            message=m["message"],
            requested_bot=m.get("bot_id"),
            metadata=m.get("raw")
        )
        results.append(res)
    return {"status": "ok", "processed": len(results), "messages": results}


@api.post("/whatsapp/simulate")
async def whatsapp_simulate(request: Request):
    """Frontend & CS test endpoint to simulate an incoming customer WhatsApp message and test routing."""
    body = await body_of(request)
    sender = body.get("sender") or "6281234567890"
    name = body.get("customer_name") or "Pelanggan"
    msg = body.get("message")
    if not msg or not str(msg).strip():
        raise ApiError(400, "Pesan wajib diisi")
    bot = body.get("bot_id")
    return await whatsapp.route_and_process_message(
        user_id=current_user(),
        sender=str(sender).strip(),
        customer_name=str(name).strip(),
        message=str(msg).strip(),
        requested_bot=bot
    )


@api.get("/whatsapp/messages")
async def whatsapp_list_messages(sender: str | None = None, limit: int = 50):
    """Retrieve logged WhatsApp interactions."""
    return await whatsapp.list_messages(current_user(), limit=limit, sender=sender)


@api.get("/whatsapp/takeover")
async def whatsapp_get_takeover():
    """List all customers currently in human takeover mode (bot paused)."""
    return {"paused_senders": whatsapp.get_paused_senders()}


@api.post("/whatsapp/takeover")
async def whatsapp_toggle_takeover(request: Request):
    """Pause or resume automatic bot replies for a specific customer."""
    body = await body_of(request)
    sender = body.get("sender")
    action = body.get("action", "pause")
    if not sender:
        raise ApiError(400, "Nomor sender wajib diisi")
    if action == "pause":
        duration = int(body.get("duration", 7200))
        whatsapp.pause_sender(sender, duration)
        return {"status": "ok", "sender": sender, "action": "paused", "duration": duration}
    else:
        whatsapp.resume_sender(sender)
        return {"status": "ok", "sender": sender, "action": "resumed"}


@public.get("/whatsapp/qr")
@api.get("/whatsapp/qr")
async def whatsapp_get_qr(request: Request, format: str | None = None):
    """Retrieve WhatsApp QR code for Evolution API connection."""
    data = await whatsapp.get_evolution_qr()
    if format == "json" or "application/json" in request.headers.get("accept", ""):
        return data
    
    b64 = data.get("base64")
    err = data.get("error")
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>WhatsApp Web QR Code - Pegawai AI</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            background: #0f172a;
            color: #f8fafc;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        .card {{
            background: #1e293b;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            text-align: center;
            max-width: 420px;
            width: 100%;
            border: 1px solid #334155;
        }}
        h2 {{ margin-top: 0; color: #38bdf8; }}
        .qr-container {{
            background: white;
            padding: 16px;
            border-radius: 12px;
            display: inline-block;
            margin: 20px 0;
        }}
        .qr-container img {{
            display: block;
            width: 260px;
            height: 260px;
        }}
        .steps {{
            text-align: left;
            font-size: 14px;
            line-height: 1.6;
            color: #94a3b8;
            background: #0f172a;
            padding: 14px 18px;
            border-radius: 8px;
            margin-top: 15px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            background: #10b981;
            color: white;
            margin-bottom: 10px;
        }}
        .btn {{
            background: #2563eb;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 15px;
            text-decoration: none;
            display: inline-block;
        }}
        .btn:hover {{ background: #1d4ed8; }}
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">Evolution API v2 • Baileys Engine</span>
        <h2>Sambungkan WhatsApp</h2>
        <p style="font-size: 14px; color: #94a3b8; margin: 0;">Scan QR code di bawah menggunakan aplikasi WhatsApp di HP Anda:</p>
        
        {f'<div class="qr-container"><img src="{b64}" alt="WhatsApp QR Code" /></div>' if b64 else f'<div style="padding: 40px; color: #f87171;">{err or "Memuat QR code atau sudah terhubung... Silakan refresh."}</div>'}
        
        <div class="steps">
            <strong>Cara Menghubungkan:</strong>
            <ol style="margin: 8px 0 0 18px; padding: 0;">
                <li>Buka WhatsApp di HP Anda</li>
                <li>Pilih <strong>Perangkat Tertaut (Linked Devices)</strong></li>
                <li>Ketuk <strong>Tautkan Perangkat</strong></li>
                <li>Arahkan kamera ke QR Code di atas</li>
            </ol>
        </div>
        <a href="" onclick="window.location.reload(); return false;" class="btn">🔄 Refresh QR Code</a>
    </div>
</body>
</html>"""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


@public.get("/whatsapp/connection")
@api.get("/whatsapp/connection")
async def whatsapp_get_connection():
    """Inspect live connection state from Evolution API."""
    return await whatsapp.get_evolution_connection_state()


@api.get("/whatsapp/status")
async def whatsapp_get_status():
    """Inspect WhatsApp routing gateway health and configuration."""
    return await whatsapp.get_status()


# ---------- approvals of risky agent actions ----------

@api.get("/actions")
async def list_actions(status: str | None = None):
    return await actions.list_actions(current_user(), status)


@api.post("/actions/{aid}/approve")
async def approve_action(aid: str):
    return await actions.approve(current_user(), aid)


@api.post("/actions/{aid}/reject")
async def reject_action(aid: str):
    return await actions.reject(current_user(), aid)


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


# ---------- schedules ----------

@api.get("/schedules")
async def list_schedules():
    return await scheduler.views(current_user())


@api.post("/schedules", status_code=201)
async def create_schedule(request: Request):
    return await scheduler.create(current_user(), await body_of(request))


@api.post("/schedules/{sid}/pause")
async def pause_schedule(sid: str):
    return await scheduler.pause(current_user(), _sched_id(sid))


@api.post("/schedules/{sid}/resume")
async def resume_schedule(sid: str):
    return await scheduler.resume(current_user(), _sched_id(sid))


@api.delete("/schedules/{sid}", status_code=204)
async def delete_schedule(sid: str):
    await scheduler.delete(current_user(), _sched_id(sid))


def _sched_id(v: str) -> str:
    try:
        return str(uuid.UUID(v))
    except ValueError:
        raise ApiError(404, "Jadwal tidak ditemukan")


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
    return await groups.send(current_user(), _uuid(gid), b.get("text"), b.get("mode") or "queue", b.get("kb_items"))


@api.post("/groups/{gid}/messages/{message_id}/steer")
async def steer_group_message(gid: str, message_id: int):
    return await groups.steer_queued(current_user(), _uuid(gid), message_id)


@api.delete("/groups/{gid}/messages/{message_id}/queued")
async def cancel_group_message(gid: str, message_id: int):
    return await groups.cancel_queued(current_user(), _uuid(gid), message_id)


@api.post("/groups/{gid}/plans/{message_id}/approve")
async def approve_plan(gid: str, message_id: int):
    return await tasks.approve_plan(current_user(), _uuid(gid), message_id)


@api.post("/groups/{gid}/plans/{message_id}/cancel")
async def cancel_plan(gid: str, message_id: int):
    return await tasks.cancel_plan(current_user(), _uuid(gid), message_id)


@api.post("/groups/{gid}/plans/{message_id}/revise", status_code=202)
async def revise_plan(gid: str, message_id: int, request: Request):
    return await tasks.revise_plan(current_user(), _uuid(gid), message_id, (await body_of(request)).get("feedback"))


@api.post("/groups/{gid}/stop")
async def stop_group(gid: str):
    return await groups.stop(current_user(), _uuid(gid))


# ---------- tasks ----------

def _task_id(v: str) -> str:
    return tasks._task_uuid(v)


@api.get("/tasks/board")
async def tasks_board(agent: str | None = None, group: str | None = None, q: str | None = None, archived: bool = False):
    return await tasks.board(current_user(), agent or None, _uuid(group) if group else None, q, archived)


@api.post("/tasks", status_code=201)
async def create_task(request: Request):
    return await tasks.create(current_user(), await body_of(request))


@api.get("/tasks/{tid}")
async def get_task(tid: str):
    return await tasks.detail(current_user(), _task_id(tid))


@api.patch("/tasks/{tid}")
async def edit_task(tid: str, request: Request):
    return await tasks.edit(current_user(), _task_id(tid), await body_of(request))


@api.post("/tasks/{tid}/comments", status_code=201)
async def comment_task(tid: str, request: Request):
    return await tasks.comment(current_user(), _task_id(tid), (await body_of(request)).get("text"))


@api.post("/tasks/{tid}/{verb}")
async def task_verb(tid: str, verb: str, request: Request):
    return await tasks.do(current_user(), _task_id(tid), verb, await body_of(request))


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
    """With session_id or group_id: that conversation (tokens, USD cost, month block). With neither: the month view of the
    account (period, cost, limit, remaining, percent, state, basis, by agent / model / day)."""
    uid = current_user()
    limit = (await engine.get_plan(uid))["monthly_usd"]
    if session_id is None and group_id is None:
        return await costs.month(uid, limit)
    sid, gid = _scope(session_id, group_id)
    return await usage.conversation(uid, sid, gid, limit)


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
app.router.routes.append(bridge_app.route())
