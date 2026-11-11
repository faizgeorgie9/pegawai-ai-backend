"""Workspace settings (per user), the model catalog Hermes serves, and the model parameters sent on runs.
Settings are one JSON row merged over DEFAULTS. Model/provider/reasoning_effort exist per bot only; nothing is sent to Hermes
when a bot has none (Hermes then uses the profile default). Old workspace model keys in the row are ignored."""
import asyncio
import json
import re
import time

from ruamel.yaml import YAML

from . import db, harden, hermes, knowledge
from .errors import ApiError

EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh")
TIMEZONES = ("Asia/Jakarta", "Asia/Makassar", "Asia/Jayapura")  # WIB, WITA, WIT
RETENTION_DAYS = 90  # db.cleanup_loop deletes tool-event logs older than this
DEFAULTS = {
    "company_name": "Colorbox", "language": "id", "timezone": "Asia/Jakarta",
    "notify": {"done": True, "failed": True, "input": True},
}
_MODEL = re.compile(r"^[\w.:/@+-]{1,120}$")
_PROVIDER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
RUN_FIELDS = ("model", "provider", "reasoning_effort")


def clean_run_fields(body: dict) -> dict:
    """Validate model / provider / reasoning_effort of a PATCH body (only the keys present). Pure: no I/O.
    model and provider travel together: both set or both null (Hermes resolves credentials by the provider)."""
    out: dict = {}
    for k in RUN_FIELDS:
        if k in body:
            out[k] = body[k]
    if ("model" in out) != ("provider" in out):
        raise ApiError(400, "Model dan provider harus diubah bersama")
    if out.get("model") is not None or out.get("provider") is not None:
        if not isinstance(out.get("model"), str) or not _MODEL.match(out["model"]):
            raise ApiError(400, "Model tidak valid")
        if not isinstance(out.get("provider"), str) or not _PROVIDER.match(out["provider"]):
            raise ApiError(400, "Provider tidak valid")
    if out.get("reasoning_effort") is not None and out["reasoning_effort"] not in EFFORTS:
        raise ApiError(400, "Tingkat berpikir harus salah satu dari: " + ", ".join(EFFORTS))
    return out


def merge_run_params(bot: dict) -> dict:
    """Request fields for POST /v1/runs from the bot's own model (with its provider) and reasoning_effort. Only what is set
    is returned."""
    out: dict = {}
    if bot.get("model") and bot.get("provider"):
        out.update(model=bot["model"], provider=bot["provider"])
    effort = bot.get("reasoning_effort")
    if effort:
        out["model_options"] = {"reasoning_effort": effort}
    return out


def clean_settings(body: dict) -> dict:
    """Validate a PATCH /api/settings body; returns only the keys to change. Pure: no I/O."""
    unknown = sorted(set(body) - set(DEFAULTS))
    if unknown:
        raise ApiError(400, "Kolom tidak dikenal: " + ", ".join(unknown))
    if not body:
        raise ApiError(400, "Tidak ada yang diubah")
    out: dict = {}
    if "company_name" in body:
        v = body["company_name"]
        v = " ".join(v.split()) if isinstance(v, str) else ""
        if not 1 <= len(v) <= 40:
            raise ApiError(400, "Nama perusahaan wajib diisi (maksimal 40 karakter)")
        out["company_name"] = v
    if "language" in body:
        if body["language"] != "id":
            raise ApiError(400, "Saat ini hanya Bahasa Indonesia")
        out["language"] = "id"
    if "timezone" in body:
        if body["timezone"] not in TIMEZONES:
            raise ApiError(400, "Zona waktu tidak dikenal")
        out["timezone"] = body["timezone"]
    if "notify" in body:
        n = body["notify"]
        if not isinstance(n, dict) or not n or set(n) - set(DEFAULTS["notify"]) or not all(isinstance(v, bool) for v in n.values()):
            raise ApiError(400, "Notifikasi harus berisi done, failed, input (true atau false)")
        out["notify"] = n
    return out


async def get(user_id: str) -> dict:
    row = await db.q1("select data from settings where user_id = %s", user_id)
    data = (row or {}).get("data") or {}
    return {**DEFAULTS, **{k: v for k, v in data.items() if k in DEFAULTS}, "notify": {**DEFAULTS["notify"], **(data.get("notify") or {})}}


async def patch(user_id: str, body: dict) -> dict:
    ch = clean_settings(body)
    if "notify" in ch:
        ch["notify"] = {**(await get(user_id))["notify"], **ch["notify"]}
    await db.ex("insert into settings (user_id, data) values (%s, %s) on conflict (user_id) do update "
                "set data = settings.data || excluded.data, updated_at = now()", user_id, json.dumps(ch))
    return await get(user_id)


async def run_params(bot_id: str) -> dict:
    row = await db.q1("select model, provider, reasoning_effort from bots where id = %s", bot_id)
    return merge_run_params(row or {})


# ---------- model catalog ----------

_cache: dict = {"at": 0.0, "data": None}


async def catalog(user_id: str) -> dict:
    """Providers that are signed in on the gateway, each with its models, from Hermes GET /api/model/options (any bot's API
    serves the same inventory). Cached 5 minutes. `default` is the profile default of that bot."""
    if _cache["data"] and time.monotonic() - _cache["at"] < 300:
        return _cache["data"]
    bot = await db.q1("select id from bots where user_id = %s and deleted_at is null order by builtin desc, created_at limit 1", user_id)
    if not bot:
        raise ApiError(404, "Belum ada agen")
    r = await hermes.call(bot["id"], "GET", "/api/model/options", timeout=30)
    try:
        d = r.json()
        provs = [{"slug": p["slug"], "name": p.get("name") or p["slug"], "models": [m for m in p["models"] if isinstance(m, str)]}
                 for p in d["providers"] if p.get("authenticated") and p.get("models")]
    except (ValueError, KeyError, TypeError):
        provs = None
    if r.status_code != 200 or provs is None:
        raise ApiError(502, "Daftar model belum bisa dibaca dari Hermes")
    data = {"default": {"model": d.get("model"), "provider": d.get("provider"), "reasoning_effort": profile_effort(bot["id"])},
            "providers": provs}
    _cache.update(at=time.monotonic(), data=data)
    return data


HERMES_EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra")


def profile_effort(slug: str) -> str | None:
    """What "Default" resolves to for the thinking level: agent.reasoning_effort of the profile config.yaml; Hermes documents an
    empty/unset value as "medium" (docs/user-guide/configuration.md, section Reasoning Effort). No Hermes API exposes it, so this
    reads that one key from config.yaml (never .env). None when the file or value cannot be read."""
    try:
        data = YAML(typ="safe").load((hermes.profile_dir(slug) / "config.yaml").read_text(encoding="utf-8")) or {}
        raw = (data.get("agent") or {}).get("reasoning_effort")
    except Exception:
        return None
    raw = str(raw).strip().lower() if raw is not None else ""
    if not raw:
        return "medium"
    return raw if raw in HERMES_EFFORTS else None


async def check_model(user_id: str, model: str | None, provider: str | None) -> None:
    """A model/provider pair is accepted only when Hermes lists it (Hermes would reject anything else at run time)."""
    if model is None:
        return
    cat = await catalog(user_id)
    if not any(p["slug"] == provider and model in p["models"] for p in cat["providers"]):
        raise ApiError(400, "Model itu tidak tersedia di provider yang dipilih")


# ---------- read-only overviews ----------

async def security(user_id: str) -> dict:
    """Toolsets switched off and the approval mode per bot. Reads the gateway toolset list and the profile config.yaml
    (approvals.mode only); never the .env."""
    rows = await db.q("select id, name from bots where user_id = %s and deleted_at is null order by builtin desc, created_at, id", user_id)

    async def one(b: dict) -> dict:
        off, ok = [], True
        try:
            r = await hermes.call(b["id"], "GET", "/v1/toolsets", timeout=8)
            data = r.json()["data"] if r.status_code == 200 else None
            if not isinstance(data, list):
                raise ValueError
            off = sorted(t["name"] for t in data if t.get("enabled") is not True and t["name"] in harden.DENY)
        except (ApiError, ValueError, KeyError, TypeError):
            ok = False
        return {"bot_id": b["id"], "name": b["name"], "ok": ok, "blocked": off, "approvals": _approval_mode(b["id"])}
    return {"deny": sorted(harden.DENY), "bots": await asyncio.gather(*(one(b) for b in rows))}


def _approval_mode(slug: str) -> str | None:
    try:
        data = YAML(typ="safe").load((hermes.profile_dir(slug) / "config.yaml").read_text(encoding="utf-8")) or {}
        mode = (data.get("approvals") or {}).get("mode")
        return mode if isinstance(mode, str) else None
    except Exception:
        return None


def knowledge_docs() -> list[dict]:
    """The documents knowledge.py loads into runs, with version and date (read only for now)."""
    dates = [r.get("accessed_date") for r in knowledge.cs_register().values() if r.get("accessed_date")]
    hub = knowledge.marketing_bundle()
    return [
        {"id": "colorbox-hub", "title": "Colorbox Hub", "workflow": "marketing", "version": None, "date": knowledge.HUB_ACCESSED,
         "files": [{"name": f["id"], "title": f["title"]} for f in hub]},
        {"id": "cs-v2.1", "title": "CS v2.1", "workflow": "cs", "version": f"{knowledge.INSTRUCTIONS_VERSION} (data {knowledge.knowledge_version()})",
         "date": max(dates) if dates else None,
         "files": [{"name": p.name, "title": p.name} for p in (knowledge.CS_INSTRUCTIONS, knowledge.CS_KNOWLEDGE, knowledge.CS_REGISTER)]},
    ]


async def export_history(user_id: str) -> dict:
    """All chat history of the user as one JSON document: every owned session with its messages (read from Hermes) and every
    group with its stored messages. A session Hermes cannot return is listed with `error` instead of failing the whole export."""
    bots = await db.q("select id, name from bots where user_id = %s and deleted_at is null order by builtin desc, created_at, id", user_id)
    owned = await db.q("select session_id, bot_id from chat_sessions where user_id = %s", user_id)
    gate = asyncio.Semaphore(4)

    async def messages(bot: str, sid: str):
        async with gate:
            try:
                r = await hermes.call(bot, "GET", f"/api/sessions/{sid}/messages")
                return r.json().get("data", []) if r.status_code == 200 else None
            except (ApiError, ValueError, AttributeError):
                return None

    async def one(b: dict) -> dict:
        ids = {o["session_id"] for o in owned if o["bot_id"] == b["id"]}
        try:
            r = await hermes.call(b["id"], "GET", "/api/sessions?limit=200")
            rows = [s for s in r.json().get("data", []) if s.get("id") in ids] if r.status_code == 200 else []
        except (ApiError, ValueError):
            rows = []
        msgs = await asyncio.gather(*(messages(b["id"], s["id"]) for s in rows))
        return {"bot_id": b["id"], "name": b["name"],
                "sessions": [{"id": s["id"], "title": s.get("title"), "started_at": s.get("started_at"),
                              "last_active": s.get("last_active"), **({"messages": m} if m is not None else {"error": "Pesan tidak terbaca"})}
                             for s, m in zip(rows, msgs)]}

    out_bots = await asyncio.gather(*(one(b) for b in bots))
    groups = []
    for g in await db.q("select id, name from groups where user_id = %s and deleted_at is null order by created_at", user_id):
        msgs = await db.q("select author, bot_id, text, created_at from group_messages where group_id = %s order by id", g["id"])
        groups.append({"id": str(g["id"]), "name": g["name"], "messages": msgs})
    return {"exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "bots": out_bots, "groups": groups}
