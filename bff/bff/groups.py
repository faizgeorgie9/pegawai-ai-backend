"""Group engine (stage 3): bots talk in a group, driven by the BFF (Hermes has no group API)."""
import asyncio
import re
import uuid
from dataclasses import dataclass

from . import db, engine
from .engine import hub
from .errors import ApiError

MAX_ROUNDS = 3
MAX_BOT_MESSAGES = 10
SILENT = "[SILENT]"


@dataclass
class SendState:
    send_id: str
    user_id: str
    task: asyncio.Task | None = None
    run_id: str | None = None
    bot: str | None = None
    stopped: bool = False
    cancel_round: bool = False


ACTIVE: dict[str, SendState] = {}  # group id -> running send


# ---------- groups CRUD ----------

async def get_group(user_id: str, gid: str) -> dict:
    g = await db.q1("select * from groups where id = %s and user_id = %s and deleted_at is null", gid, user_id)
    if not g:
        raise ApiError(404, "Grup tidak ditemukan")
    return g


async def members(gid: str) -> list[dict]:
    return await db.q("select gm.bot_id, gm.position, b.name, b.role, b.team, b.color from group_members gm "
                      "join bots b on b.id = gm.bot_id where gm.group_id = %s order by gm.position", gid)


async def group_view(g: dict) -> dict:
    return {"id": g["id"], "name": g["name"], "created_at": g["created_at"],
            "members": await members(str(g["id"])), "running": str(g["id"]) in ACTIVE}


async def _check_members(user_id: str, bot_ids) -> list[str]:
    if not isinstance(bot_ids, list) or not all(isinstance(b, str) for b in bot_ids):
        raise ApiError(400, "Daftar anggota tidak valid")
    ids = list(dict.fromkeys(bot_ids))
    if not 2 <= len(ids) <= 6:
        raise ApiError(400, "Grup harus punya 2 sampai 6 anggota")
    found = await db.q("select id from bots where user_id = %s and deleted_at is null and id = any(%s)", user_id, ids)
    if len(found) != len(ids):
        raise ApiError(400, "Ada anggota yang tidak ditemukan")
    return ids


def _check_name(name) -> str:
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 60:
        raise ApiError(400, "Nama grup wajib diisi (maksimal 60 karakter)")
    return name.strip()


async def _set_members(gid: str, ids: list[str]) -> None:
    await db.ex("delete from group_members where group_id = %s and bot_id <> all(%s)", gid, ids)
    for pos, b in enumerate(ids):
        await db.ex("insert into group_members (group_id, bot_id, position) values (%s, %s, %s) "
                    "on conflict (group_id, bot_id) do update set position = excluded.position", gid, b, pos)


async def create_group(user_id: str, name, bot_ids) -> dict:
    name, ids = _check_name(name), await _check_members(user_id, bot_ids)
    plan = await engine.get_plan(user_id)
    n = (await db.q1("select count(*)::int as n from groups where user_id = %s and deleted_at is null", user_id))["n"]
    if n >= plan["max_groups"]:
        raise ApiError(402, "Batas jumlah grup di paket Anda tercapai. Naikkan paket untuk menambah grup.", upgrade=True)
    gid = str(uuid.uuid4())
    await db.ex("insert into groups (id, user_id, name) values (%s, %s, %s)", gid, user_id, name)
    await _set_members(gid, ids)
    return await group_view(await get_group(user_id, gid))


async def update_group(user_id: str, gid: str, name, bot_ids) -> dict:
    g = await get_group(user_id, gid)
    if name is not None:
        await db.ex("update groups set name = %s where id = %s", _check_name(name), gid)
    if bot_ids is not None:
        await _set_members(gid, await _check_members(user_id, bot_ids))
    return await group_view(await get_group(user_id, gid))


async def delete_group(user_id: str, gid: str) -> None:
    await get_group(user_id, gid)
    if gid in ACTIVE:
        await stop(user_id, gid)
    await db.ex("update groups set deleted_at = now() where id = %s", gid)


async def list_groups(user_id: str) -> list[dict]:
    rows = await db.q("select * from groups where user_id = %s and deleted_at is null order by created_at", user_id)
    return [await group_view(g) for g in rows]


async def list_messages(user_id: str, gid: str, before: int | None, limit: int) -> list[dict]:
    await get_group(user_id, gid)
    limit = max(1, min(limit, 200))
    return await db.q("select * from (select id, group_id, author, bot_id, text, run_id, created_at from group_messages "
                      "where group_id = %s and (%s::bigint is null or id < %s) order by id desc limit %s) t order by id",
                      gid, before, before, limit)


async def remove_bot_from_groups(bot_id: str) -> None:
    await db.ex("delete from group_members where bot_id = %s", bot_id)


# ---------- messages ----------

async def post(gid: str, author: str, text: str, bot_id: str | None = None, run_id=None, send_id=None) -> dict:
    row = await db.q1("insert into group_messages (group_id, author, bot_id, text, run_id, send_id) "
                      "values (%s, %s, %s, %s, %s, %s) returning id, group_id, author, bot_id, text, run_id, created_at",
                      gid, author, bot_id, text, run_id, send_id)
    hub.publish("*", "group_message", {"group_id": gid, "message": row})
    return row


def _group_event(gid: str, status: str) -> None:
    hub.publish("*", "group_send", {"group_id": gid, "status": status})


# ---------- send ----------

async def send(user_id: str, gid: str, text, mode: str) -> dict:
    g = await get_group(user_id, gid)
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 4000:
        raise ApiError(400, "Pesan wajib diisi (maksimal 4000 karakter)")
    if mode not in ("queue", "steer"):
        raise ApiError(400, "Mode harus queue atau steer")
    if len(await members(gid)) < 2:
        raise ApiError(409, "Grup ini belum punya cukup anggota")
    text = text.strip()
    if gid not in ACTIVE:
        await engine.check_quota(user_id)  # refuse up front, with the upgrade hint
    msg = await post(gid, "user", text)
    st = ACTIVE.get(gid)
    if st is None:
        _start_loop(user_id, gid, [(msg["id"], text)])
        return {"message": msg, "queued": False}
    await db.ex("insert into group_sends (id, group_id, message_id, status) values (%s, %s, %s, 'queued')",
                str(uuid.uuid4()), gid, msg["id"])
    if mode == "steer":
        st.cancel_round = True
        if st.run_id and st.bot:
            try:
                await engine.steer(user_id, st.run_id, f"User: {text}")
                await db.ex("insert into group_cursors (group_id, bot_id, last_message_id) values (%s, %s, %s) "
                            "on conflict (group_id, bot_id) do update set last_message_id = greatest("
                            "group_cursors.last_message_id, excluded.last_message_id)", gid, st.bot, msg["id"])
            except ApiError:
                pass  # run just finished: the message waits for the next loop like a queued one
    return {"message": msg, "queued": True}


def _start_loop(user_id: str, gid: str, msgs: list[tuple[int, str]]) -> None:
    st = SendState(str(uuid.uuid4()), user_id)
    ACTIVE[gid] = st
    st.task = asyncio.create_task(_run_loop(gid, st, msgs))


async def stop(user_id: str, gid: str) -> dict:
    await get_group(user_id, gid)
    st = ACTIVE.get(gid)
    await db.ex("delete from group_sends where group_id = %s and status = 'queued'", gid)
    if st:
        st.stopped = True
        if st.run_id:
            try:
                await engine.stop(user_id, st.run_id)
            except ApiError:
                pass
    return {"stopping": bool(st)}


def _instructions(group_name: str, mems: list[dict]) -> str:
    roster = "; ".join(f"{m['name']} ({m['role']})" for m in mems)
    return (f"Kamu sedang berdiskusi di grup \"{group_name}\". Anggota grup: {roster}.\n"
            "Balas singkat sesuai peranmu.\n"
            f"Jika tidak ada yang perlu kamu tambahkan, balas persis {SILENT}.\n"
            "Sebut @nama untuk meminta anggota lain.\n"
            "Jangan mengulang pesan anggota lain.")


def _mentioned(text: str, mems: list[dict]) -> set[str]:
    tokens = {t.lower() for t in re.findall(r"@(\w+)", text)}
    return {m["bot_id"] for m in mems if m["bot_id"] in tokens or m["name"].split()[0].lower() in tokens}


async def _turn(gid: str, st: SendState, bot: dict, g: dict, mems: list[dict]) -> dict | None:
    """One bot turn. Returns the finished run row, or None when the bot had nothing new to read."""
    cur = await db.q1("select last_message_id from group_cursors where group_id = %s and bot_id = %s", gid, bot["bot_id"])
    new = await db.q("select gm.id, gm.author, gm.bot_id, gm.text, b.name, b.role from group_messages gm "
                     "left join bots b on b.id = gm.bot_id where gm.group_id = %s and gm.id > %s order by gm.id",
                     gid, cur["last_message_id"] if cur else 0)
    if not new:
        return None
    lines = [f"User: {m['text']}" if m["author"] == "user" else f"{m['name']} ({m['role']}): {m['text']}"
             for m in new if m["author"] != "system" and m["bot_id"] != bot["bot_id"]]
    await db.ex("insert into group_cursors (group_id, bot_id, last_message_id) values (%s, %s, %s) "
                "on conflict (group_id, bot_id) do update set last_message_id = excluded.last_message_id",
                gid, bot["bot_id"], new[-1]["id"])
    if not lines:
        return None
    hub.publish("*", "group_typing", {"group_id": gid, "bot_id": bot["bot_id"], "on": True, "phase": "thinking"})
    try:
        run = await engine.start_run(st.user_id, bot["bot_id"], f"grup-{gid}-{bot['bot_id']}", "\n".join(lines),
                                     "group", gid, _instructions(g["name"], mems))
        st.run_id, st.bot = str(run["id"]), bot["bot_id"]
        return await engine.wait_done(st.run_id)
    finally:
        st.run_id = st.bot = None
        hub.publish("*", "group_typing", {"group_id": gid, "bot_id": bot["bot_id"], "on": False})


async def _run_loop(gid: str, st: SendState, msgs: list[tuple[int, str]]) -> None:
    sid = st.send_id
    await db.ex("insert into group_sends (id, group_id, message_id, status) values (%s, %s, %s, 'running')",
                sid, gid, msgs[-1][0])
    _group_event(gid, "running")
    final = "done"
    try:
        stop_msg = await _loop_body(gid, st, msgs)
        if st.stopped:
            final = "stopped"
            await post(gid, "system", "Diskusi dihentikan.", send_id=sid)
        elif stop_msg:
            await post(gid, "system", stop_msg, send_id=sid)
    except ApiError as e:
        await post(gid, "system", f"Diskusi berhenti: {e.message}", send_id=sid)
    except Exception:
        await post(gid, "system", "Diskusi berhenti: terjadi kesalahan di server.", send_id=sid)
    await db.ex("update group_sends set status = %s, finished_at = now() where id = %s", final, sid)
    _group_event(gid, final)
    queued = [] if final == "stopped" else await db.q(
        "select gs.id, gs.message_id, gm.text from group_sends gs join group_messages gm "
        "on gm.id = gs.message_id where gs.group_id = %s and gs.status = 'queued' order by gs.created_at", gid)
    if not queued:
        ACTIVE.pop(gid, None)  # popped only after the queue check, so a new send cannot start a second loop
    else:
        # all queued user messages are already in the transcript: one loop covers them
        await db.ex("update group_sends set status = 'done', finished_at = now() where id = any(%s)",
                    [q["id"] for q in queued])
        _start_loop(st.user_id, gid, [(q["message_id"], q["text"]) for q in queued])


async def _loop_body(gid: str, st: SendState, msgs: list[tuple[int, str]]) -> str | None:
    """Rounds of bot turns. Returns the system message to post when a cap stopped the discussion."""
    g = await db.q1("select * from groups where id = %s", gid)
    mems = await members(gid)
    budget = (await engine.get_plan(st.user_id))["group_send_token_budget"]  # None = no limit
    by_id = {m["bot_id"]: m for m in mems}
    ment = set().union(*(_mentioned(t, mems) for _, t in msgs))
    responders = [m for m in mems if m["bot_id"] in ment] or list(mems)
    posted = tokens = 0
    for rnd in range(1, MAX_ROUNDS + 1):
        round_msgs: list[tuple[str, str]] = []  # (bot_id, text) in order
        for bot in responders:
            if st.stopped or st.cancel_round:
                return None
            if posted >= MAX_BOT_MESSAGES:
                return f"Diskusi berhenti: batas {MAX_BOT_MESSAGES} pesan bot tercapai."
            row = await _turn(gid, st, bot, g, mems)
            if row is None:
                continue
            tokens += row["total_tokens"]
            await db.ex("update group_sends set tokens_used = %s where id = %s", tokens, st.send_id)
            if row["status"] == "cancelled" or st.stopped:
                return None
            if row["status"] != "completed":
                return f"Diskusi berhenti: {bot['name']} gagal menjawab."
            text = (row["output"] or "").strip()
            if text.replace(SILENT, "").strip():
                text = text.replace(SILENT, "").strip()
                await post(gid, "bot", text, bot["bot_id"], row["id"], st.send_id)
                posted += 1
                round_msgs.append((bot["bot_id"], text))
            if budget is not None and tokens >= budget:
                return f"Diskusi berhenti: batas {budget} token per kiriman tercapai."
        # next round: members mentioned in this round who have not spoken after the mention
        nxt: set[str] = set()
        for i, (author, text) in enumerate(round_msgs):
            spoke_later = {b for b, _ in round_msgs[i + 1:]}
            nxt |= {b for b in _mentioned(text, mems) if b != author and b not in spoke_later}
        responders = [by_id[b] for b in by_id if b in nxt]
        if not responders:
            return None
        if rnd == MAX_ROUNDS:
            return f"Diskusi berhenti: batas {MAX_ROUNDS} ronde tercapai."
    return None


# ---------- startup ----------

async def recover() -> None:
    rows = await db.q("update group_sends set status = 'stopped', finished_at = now() "
                      "where status in ('queued', 'running') returning group_id, status")
    for gid in {str(r["group_id"]) for r in rows}:
        await post(gid, "system", "Diskusi terhenti karena server dimulai ulang.")
