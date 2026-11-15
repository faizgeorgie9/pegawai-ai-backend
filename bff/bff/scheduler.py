"""Scheduler: schedules owned by a user, run by a loop inside the BFF (not Hermes' cronjob tool, which harden.py removes).
Two kinds: a recurring schedule (days of the week + time, on one agent or a group) and a plan (explicit dated occurrences, made
when the user approves a content plan in a group chat). Every occurrence runs through engine.start_run, so it is recorded in
`runs`, priced, counted by check_quota (a 402 marks that occurrence skipped) and stoppable.
An occurrence starts at most once: claim() flips planned -> running in one UPDATE ... FOR UPDATE SKIP LOCKED."""
import asyncio
import re
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Awaitable, Callable
from zoneinfo import ZoneInfo

from psycopg.types.json import Jsonb

from . import bots, costs, db, engine, groups, plan_schema, settings, usage
from .errors import ApiError

TICK_SECONDS = 30
LATE = timedelta(hours=2)  # an occurrence this far past its time is skipped, not run (server was down, schedule paused)
HORIZON_DAYS = 14  # recurring schedules get their occurrences created this far ahead
MAX_SCHEDULES = 30
_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
LATE_REASON = "Terlewat: waktunya sudah lewat saat jadwal tidak berjalan"
WRITER_WORDS, VISUAL_WORDS = ("writer", "copywrit", "penulis"), ("visual", "designer", "desainer")
STOPS: set[str] = set()  # occurrence ids asked to stop
TASKS: dict[str, asyncio.Task] = {}


# ---------- pure helpers ----------

def clean_recurring(b: dict) -> dict:
    """Validate the POST /schedules body of a recurring schedule. Exactly one of bot_id / group_id."""
    title, prompt = b.get("title"), b.get("prompt")
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 80:
        raise ApiError(400, "Nama jadwal wajib diisi (maksimal 80 karakter)")
    if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 4000:
        raise ApiError(400, "Perintah wajib diisi (maksimal 4000 karakter)")
    days = b.get("days")
    if not isinstance(days, list) or not days or any(not isinstance(d, int) or isinstance(d, bool) or not 0 <= d <= 6 for d in days):
        raise ApiError(400, "Pilih minimal satu hari")
    hhmm = b.get("time")
    if not isinstance(hhmm, str) or not _HHMM.match(hhmm):
        raise ApiError(400, "Jam harus berformat HH:MM")
    bot_id, group_id = b.get("bot_id"), b.get("group_id")
    if (bot_id is None) == (group_id is None) or not isinstance(bot_id or group_id, str):
        raise ApiError(400, "Isi salah satu: bot_id atau group_id")
    return {"title": title.strip(), "prompt": prompt.strip(), "days": sorted(set(days)), "time": hhmm,
            "bot_id": bot_id, "group_id": group_id}


def local_to_utc(d: date, hhmm: str, tz: str) -> datetime:
    return datetime.combine(d, time.fromisoformat(hhmm), tzinfo=ZoneInfo(tz)).astimezone(timezone.utc)


def slots(days: list[int], hhmm: str, tz: str, now: datetime, horizon: int = HORIZON_DAYS) -> list[datetime]:
    """The future times (UTC) of a recurring schedule within `horizon` days. Day 0 = Monday, in the schedule's timezone."""
    today = now.astimezone(ZoneInfo(tz)).date()
    out = [local_to_utc(today + timedelta(n), hhmm, tz) for n in range(horizon + 1)
           if (today + timedelta(n)).weekday() in days]
    return [t for t in out if t > now]


def plan_slots(plan: dict, tz: str, now: datetime) -> list[tuple[datetime, str, str]]:
    """(planned_at UTC, title, brief) per plan day. A day already in the past cannot be scheduled (400)."""
    n, out = len(plan["days"]), []
    for i, d in enumerate(plan["days"], 1):
        at = local_to_utc(date.fromisoformat(d["date"]), d["time"], tz)
        if at <= now:
            raise ApiError(400, f"Tanggal {d['date']} sudah lewat. Minta revisi agar tanggalnya dimulai dari besok.")
        prods = f" Produk: {', '.join(d['products'])}." if d["products"] else ""
        out.append((at, f"Hari {i} dari {n}: {d['theme']}", f"Hari {i} dari {n}. Tema: {d['theme']}.{prods}\nBrief: {d['brief']}"))
    return out


def find_executors(mems: list[dict]) -> list[str]:
    """[writer, visual] bot ids of a group, found by role (then name). ApiError 409 when one is missing."""
    def pick(words, skip=()):
        for m in mems:
            if m["bot_id"] not in skip and any(w in f"{m['role']} {m['name']}".lower() for w in words):
                return m["bot_id"]
        return None
    w = pick(WRITER_WORDS)
    v = pick(VISUAL_WORDS, (w,))
    if not w or not v:
        raise ApiError(409, "Grup ini perlu anggota berperan Writer dan Visual untuk menjalankan rencana")
    return [w, v]


async def drive(targets: list[str], make_input: Callable[[int, list[str]], str],
                start: Callable[[str, str], Awaitable[dict]], wait: Callable[[str], Awaitable[dict]],
                done: Callable[[str, dict], Awaitable[None]], stopped: Callable[[], bool]) -> dict:
    """Run the targets one after the other (each gets the earlier outputs through make_input). Returns
    {status: done|skipped|failed|cancelled, reason, run_ids}. A 402 before anything ran is `skipped` with its message."""
    run_ids, outputs = [], []
    for i, bot in enumerate(targets):
        if stopped():
            return {"status": "cancelled", "reason": "Dihentikan", "run_ids": run_ids}
        try:
            run = await start(bot, make_input(i, outputs))
        except ApiError as e:
            if e.status == 402 and not run_ids:
                return {"status": "skipped", "reason": e.message, "run_ids": run_ids}
            return {"status": "failed", "reason": e.message, "run_ids": run_ids}
        run_ids.append(str(run["id"]))
        row = await wait(str(run["id"]))
        if row["status"] != "completed":
            gone = row["status"] == "cancelled" or stopped()
            return {"status": "cancelled" if gone else "failed", "reason": row.get("error") or ("Dihentikan" if gone else "Tidak selesai"),
                    "run_ids": run_ids}
        await done(bot, row)
        outputs.append((row["output"] or "").strip())
    return {"status": "done", "reason": None, "run_ids": run_ids}


# ---------- database side ----------

async def _owned(uid: str, sid: str) -> dict:
    row = await db.q1("select * from schedules where id = %s and user_id = %s", sid, uid)
    if not row:
        raise ApiError(404, "Jadwal tidak ditemukan")
    return row


async def _insert_occurrences(sid: str, uid: str, rows: list[tuple[datetime, str | None, str, list[str] | None]]) -> None:
    for at, title, brief, targets in rows:
        await db.ex("insert into schedule_occurrences (schedule_id, user_id, planned_at, title, brief, targets) "
                    "values (%s, %s, %s, %s, %s, %s) on conflict (schedule_id, planned_at) do nothing",
                    sid, uid, at, title, brief, Jsonb(targets) if targets else None)


async def create(uid: str, body: dict) -> dict:
    v = clean_recurring(body)
    if v["bot_id"]:
        await bots.get_bot(uid, v["bot_id"])
    else:
        await groups.get_group(uid, v["group_id"])
    n = (await db.q1("select count(*)::int as n from schedules where user_id = %s and status <> 'cancelled'", uid))["n"]
    if n >= MAX_SCHEDULES:
        raise ApiError(409, f"Maksimal {MAX_SCHEDULES} jadwal aktif. Batalkan jadwal yang tidak dipakai.")
    tz = (await settings.get(uid))["timezone"]
    sid = str(uuid.uuid4())
    await db.ex("insert into schedules (id, user_id, kind, title, bot_id, group_id, prompt, days, time_of_day, timezone) "
                "values (%s, %s, 'recurring', %s, %s, %s, %s, %s, %s, %s)",
                sid, uid, v["title"], v["bot_id"], v["group_id"], v["prompt"], v["days"], v["time"], tz)
    await materialize()
    return await get_view(uid, sid)


async def approve_plan(uid: str, gid: str, message_id: int) -> dict:
    """Approve the plan of a group message once: one plan schedule, one occurrence per day (writer, then visual).
    Approving again returns the same schedule."""
    g = await groups.get_group(uid, gid)
    msg = await db.q1("select id, author, text from group_messages where id = %s and group_id = %s", message_id, gid)
    plan, _ = plan_schema.parse(msg["text"]) if msg and msg["author"] == "bot" else (None, [])
    if not plan:
        raise ApiError(404, "Rencana tidak ditemukan atau tidak valid")
    existing = await db.q1("select id from schedules where source_message_id = %s", message_id)
    if existing:
        return await get_view(uid, str(existing["id"]))
    targets = find_executors(await groups.members(gid))
    tz = (await settings.get(uid))["timezone"]
    rows = [(at, title, brief, targets) for at, title, brief in plan_slots(plan, tz, datetime.now(timezone.utc))]
    # the unique index on source_message_id decides a race: only the insert that wins creates the occurrences
    # shortcut: schedule row and occurrences are separate statements; a crash between leaves an empty plan, cancel and re-approve.
    won = await db.q1("insert into schedules (user_id, kind, title, group_id, timezone, source_message_id) "
                      "values (%s, 'plan', %s, %s, %s, %s) on conflict (source_message_id) where source_message_id is not null "
                      "do nothing returning id", uid, f"{plan['title']} ({g['name']})", gid, tz, message_id)
    if not won:
        return await get_view(uid, str((await db.q1("select id from schedules where source_message_id = %s", message_id))["id"]))
    await _insert_occurrences(str(won["id"]), uid, rows)
    await groups.post(gid, "system", f"Rencana disetujui: {len(rows)} hari terjadwal.")
    return await get_view(uid, str(won["id"]))


async def request_revision(uid: str, gid: str, message_id: int, feedback) -> dict:
    """The user's feedback goes back into the group as a normal message to the plan's author, who revises it."""
    await groups.get_group(uid, gid)
    if not isinstance(feedback, str) or not 1 <= len(feedback.strip()) <= 3000:
        raise ApiError(400, "Catatan revisi wajib diisi (maksimal 3000 karakter)")
    msg = await db.q1("select author, bot_id, text from group_messages where id = %s and group_id = %s", message_id, gid)
    if not msg or msg["author"] != "bot" or not plan_schema.parse(msg["text"])[0]:
        raise ApiError(404, "Rencana tidak ditemukan atau tidak valid")
    if await db.q1("select 1 from schedules where source_message_id = %s", message_id):
        raise ApiError(409, "Rencana ini sudah disetujui")
    return await groups.send(uid, gid, f"@{msg['bot_id']} Mohon revisi rencana ini: {feedback.strip()}", "queue")


async def _set_status(uid: str, sid: str, allowed: tuple[str, ...], status: str, why: str) -> dict:
    row = await _owned(uid, sid)
    if row["status"] not in allowed:
        raise ApiError(409, why)
    await db.ex("update schedules set status = %s where id = %s", status, sid)
    if status == "cancelled":
        await db.ex("update schedule_occurrences set status = 'cancelled', finished_at = now() "
                    "where schedule_id = %s and status = 'planned'", sid)
    return await get_view(uid, sid)


async def pause(uid: str, sid: str) -> dict:
    return await _set_status(uid, sid, ("active",), "paused", "Jadwal tidak sedang aktif")


async def resume(uid: str, sid: str) -> dict:
    return await _set_status(uid, sid, ("paused",), "active", "Jadwal tidak sedang dijeda")


async def cancel(uid: str, sid: str) -> dict:
    return await _set_status(uid, sid, ("active", "paused"), "cancelled", "Jadwal sudah dibatalkan")


async def delete(uid: str, sid: str) -> None:
    await _owned(uid, sid)
    if await db.q1("select 1 from schedule_occurrences where schedule_id = %s and status = 'running'", sid):
        raise ApiError(409, "Ada tugas jadwal yang sedang berjalan. Hentikan atau tunggu selesai.")
    await db.ex("delete from schedules where id = %s", sid)  # occurrences go with it; the runs stay in the history


async def stop(uid: str, occ_id: str) -> dict:
    occ = await db.q1("select * from schedule_occurrences where id = %s and user_id = %s", occ_id, uid)
    if not occ:
        raise ApiError(404, "Jadwal tidak ditemukan")
    if occ["status"] != "running":
        raise ApiError(409, "Tugas ini tidak sedang berjalan")
    STOPS.add(occ_id)
    if occ["run_ids"]:
        try:
            await engine.stop(uid, occ["run_ids"][-1])
        except ApiError:
            pass
    return {"status": "stopping"}


# ---------- views ----------

async def _run_costs(run_ids: list[str]) -> dict[str, dict]:
    if not run_ids:
        return {}
    rows = await db.q(f"select {usage._COLS} from runs r where r.id = any(%s::uuid[])", run_ids)
    pricer = await costs.pricer_for(r["bot_id"] for r in rows)
    return {str(r["id"]): usage._cost(r, pricer) for r in rows}


def _occ_view(o: dict, run_info: dict[str, dict], names: dict[str, str]) -> dict:
    runs = [run_info[r] for r in o["run_ids"] if r in run_info]
    usd = sum((r["usd"] for r in runs), costs.ZERO)
    return {"id": str(o["id"]), "schedule_id": str(o["schedule_id"]), "planned_at": o["planned_at"], "title": o["title"],
            "brief": o["brief"], "status": o["status"], "skip_reason": o["skip_reason"],
            "agents": [names.get(b, b) for b in (o["targets"] or [])] or None,
            "run_ids": o["run_ids"], "run_id": o["run_ids"][-1] if o["run_ids"] else None,
            "cost": costs.money(usd) if runs and o["status"] != "running" else None,
            "estimated": any(r["estimated"] for r in runs), "started_at": o["started_at"], "finished_at": o["finished_at"]}


async def views(uid: str, only: str | None = None) -> list[dict]:
    rows = await db.q("select * from schedules where user_id = %s and (%s::uuid is null or id = %s) "
                      "order by created_at desc", uid, only, only)
    if not rows:
        return []
    ids = [str(r["id"]) for r in rows]
    # upcoming + running always; finished ones of the last 14 days, newest 10 per schedule
    occs = await db.q("select * from (select o.*, row_number() over (partition by schedule_id order by "
                      "(status in ('planned', 'running')) desc, planned_at desc) as rn from schedule_occurrences o "
                      "where schedule_id = any(%s::uuid[]) and (status in ('planned', 'running') or "
                      "planned_at > now() - interval '14 days')) t where status in ('planned', 'running') or rn <= 10 "
                      "order by planned_at", ids)
    names = {b["id"]: b["name"] for b in await db.q("select id, name from bots where user_id = %s", uid)}
    info = await _run_costs([r for o in occs for r in o["run_ids"]])
    gnames = {str(g["id"]): g["name"] for g in await db.q("select id, name from groups where user_id = %s", uid)}
    out = []
    for s in rows:
        mine = [_occ_view(o, info, names) for o in occs if o["schedule_id"] == s["id"]]
        nxt = next((o["planned_at"] for o in mine if o["status"] == "planned"), None)
        out.append({"id": str(s["id"]), "kind": s["kind"], "title": s["title"], "status": s["status"],
                    "bot_id": s["bot_id"], "group_id": str(s["group_id"]) if s["group_id"] else None,
                    "target": names.get(s["bot_id"]) if s["bot_id"] else gnames.get(str(s["group_id"]), "Grup"),
                    "prompt": s["prompt"], "days": s["days"], "time": s["time_of_day"], "timezone": s["timezone"],
                    "source_message_id": s["source_message_id"], "created_at": s["created_at"],
                    "next_at": nxt, "occurrences": mine})
    return out


async def get_view(uid: str, sid: str) -> dict:
    return (await views(uid, sid))[0]


# ---------- the loop ----------

async def materialize() -> None:
    """Create the next HORIZON_DAYS of occurrences of every active recurring schedule (no backfill of past times)."""
    now = datetime.now(timezone.utc)
    for s in await db.q("select * from schedules where kind = 'recurring' and status = 'active'"):
        await _insert_occurrences(str(s["id"]), s["user_id"],
                                  [(t, s["title"], s["prompt"], None) for t in slots(s["days"], s["time_of_day"], s["timezone"], now)])


async def expire_late() -> None:
    await db.ex("update schedule_occurrences set status = 'skipped', skip_reason = %s, finished_at = now() "
                "where status = 'planned' and planned_at < now() - make_interval(secs => %s)", LATE_REASON, LATE.total_seconds())


async def claim() -> dict | None:
    """Take one due occurrence of an active schedule. The UPDATE is the claim: a second loop (or a restart) cannot get it."""
    return await db.q1("update schedule_occurrences set status = 'running', started_at = now() where id = ("
                       "select o.id from schedule_occurrences o join schedules s on s.id = o.schedule_id "
                       "where o.status = 'planned' and o.planned_at <= now() and s.status = 'active' "
                       "order by o.planned_at limit 1 for update of o skip locked) returning *")


async def _finish(occ_id: str, res: dict) -> None:
    await db.ex("update schedule_occurrences set status = %s, skip_reason = %s, run_ids = %s, finished_at = now() where id = %s",
                res["status"], res["reason"], Jsonb(res["run_ids"]), occ_id)


async def run_occurrence(occ: dict) -> dict:
    """Run one claimed occurrence and record its end state. Never raises."""
    oid, run_ids = str(occ["id"]), []
    try:
        s = await db.q1("select * from schedules where id = %s", occ["schedule_id"])
        uid, brief = s["user_id"], occ["brief"]

        async def start_with(bot, text, session, kind, gid, ins, origin):
            run = await engine.start_run(uid, bot, session, text, kind, gid, ins, origin=origin)
            run_ids.append(str(run["id"]))
            await db.ex("update schedule_occurrences set run_ids = %s where id = %s", Jsonb(run_ids), oid)
            return run

        async def nothing(bot, row):
            pass

        origin = {"type": "marketing" if occ["targets"] else "chat", "schedule_id": str(s["id"]), "occurrence_id": oid}
        if s["bot_id"]:
            sid = f"web-sch-{str(s['id'])[:12]}"
            await db.ex("insert into chat_sessions (session_id, user_id, bot_id) values (%s, %s, %s) on conflict do nothing",
                        sid, uid, s["bot_id"])
            res = await drive([s["bot_id"]], lambda i, outs: brief,
                              lambda bot, text: start_with(bot, text, sid, "chat", None, None, origin),
                              engine.wait_done, nothing, lambda: oid in STOPS)
        elif occ["targets"]:  # a plan day: writer, then visual, in the group
            gid = str(s["group_id"])
            g, mems = await groups.get_group(uid, gid), await groups.members(gid)
            ins = groups._instructions(g["name"], mems)
            await groups.post(gid, "system", f"Jadwal berjalan: {occ['title']}")

            async def done(bot, row):
                if (row["output"] or "").strip():
                    await groups.post(gid, "bot", row["output"].strip(), bot, row["id"])
            res = await drive(occ["targets"],
                              lambda i, outs: brief if i == 0 else f"{brief}\n\nNaskah dari Writer:\n{outs[-1]}",
                              lambda bot, text: start_with(bot, text, f"grup-{gid}-{bot}", "group", gid, ins, origin),
                              engine.wait_done, done, lambda: oid in STOPS)
        else:  # recurring on a group: a normal message to the group (the group loop answers it)
            try:
                await groups.send(uid, str(s["group_id"]), brief, "queue")
                res = {"status": "done", "reason": None, "run_ids": []}
            except ApiError as e:
                res = {"status": "skipped" if e.status == 402 else "failed", "reason": e.message, "run_ids": []}
    except Exception as e:
        res = {"status": "failed", "reason": e.message if isinstance(e, ApiError) else f"Kesalahan internal: {type(e).__name__}",
               "run_ids": run_ids}
    finally:
        STOPS.discard(oid)
        TASKS.pop(oid, None)
    await _finish(oid, res)
    return res


async def tick() -> None:
    await materialize()
    await expire_late()
    while (occ := await claim()):
        TASKS[str(occ["id"])] = asyncio.create_task(run_occurrence(occ))


async def loop() -> None:
    while True:
        try:
            await tick()
        except asyncio.CancelledError:
            raise
        except Exception:
            pass  # a database hiccup must not end the scheduler; the next tick retries
        await asyncio.sleep(TICK_SECONDS)


async def recover() -> None:
    """A restart loses the tasks of running occurrences: say so instead of pretending they continue."""
    await db.ex("update schedule_occurrences set status = 'failed', skip_reason = 'Dihentikan karena server dimulai ulang', "
                "finished_at = now() where status = 'running'")
