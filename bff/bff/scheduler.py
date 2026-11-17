"""Scheduler: recurring schedules owned by a user (days of the week + time, on one agent or a group) and the loop inside the BFF that
runs the Papan Tugas (not Hermes' cronjob tool, which harden.py removes).
A recurring schedule is a template: every time of it becomes a task (source recurring, scheduled_at = the time) created up to
HORIZON_DAYS ahead. Each tick: create those tasks, release the ones whose time came (scheduled -> ready), and start ready tasks
(tasks.claim: one running task per agent or team). Every run goes through engine.start_run, so it is recorded in `runs` (runs.task_id),
priced, counted by check_quota and stoppable. A content plan's days are tasks too (tasks.py)."""
import asyncio
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable
from zoneinfo import ZoneInfo

from psycopg.types.json import Jsonb

from . import bots, db, engine, groups, plan_schema, settings, tasks
from .errors import ApiError

TICK_SECONDS = 30
HORIZON_DAYS = 3  # recurring schedules get their tasks created this far ahead (each is a card in Antre: a short horizon keeps the board calm)
MAX_SCHEDULES = 30
_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
TASKS: dict[str, asyncio.Task] = {}  # running coroutines by task id (a reference keeps them alive)


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


def slots(days: list[int], hhmm: str, tz: str, now: datetime, horizon: int = HORIZON_DAYS) -> list[datetime]:
    """The future times (UTC) of a recurring schedule within `horizon` days. Day 0 = Monday, in the schedule's timezone."""
    today = now.astimezone(ZoneInfo(tz)).date()
    out = [plan_schema.local_to_utc(today + timedelta(n), hhmm, tz) for n in range(horizon + 1)
           if (today + timedelta(n)).weekday() in days]
    return [t for t in out if t > now]


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


async def follow_group(poll: Callable[[], Awaitable[list[dict]]], busy: Callable[[], bool], stopped: Callable[[], bool],
                       halt: Callable[[], Awaitable[object]], save: Callable[[list[str]], Awaitable[None]],
                       sleep: Callable[[float], Awaitable[None]] = asyncio.sleep, every: float = 2.0) -> dict:
    """Wait for the group discussion a message started, linking the group's runs to the task as they appear.
    poll() = runs of the group since the message (oldest first, {id, status, error}); busy() = the group loop is still going.
    Same result shape as drive(). shortcut: runs are matched by group and time, so a user chatting in the same group at the
    same moment is counted too (the loop is shared then); tag the runs with the task if that ever matters."""
    asked, ids, rows = False, [], []
    while True:
        rows = await poll()
        if [str(r["id"]) for r in rows] != ids:
            ids = [str(r["id"]) for r in rows]
            await save(ids)
        if stopped() and not asked:
            asked = True
            await halt()
        if not busy():
            break
        await sleep(every)
    if asked:
        return {"status": "cancelled", "reason": "Dihentikan", "run_ids": ids}
    bad = rows[-1] if rows and rows[-1]["status"] in ("failed", "interrupted") else None
    if bad:
        return {"status": "failed", "reason": bad.get("error") or "Tidak selesai", "run_ids": ids}
    return {"status": "done", "reason": None, "run_ids": ids}


# ---------- recurring schedules (templates) ----------

async def _owned(uid: str, sid: str) -> dict:
    row = await db.q1("select * from schedules where id = %s and user_id = %s and kind = 'recurring' and status <> 'cancelled'", sid, uid)
    if not row:
        raise ApiError(404, "Jadwal tidak ditemukan")
    return row


async def create(uid: str, body: dict) -> dict:
    v = clean_recurring(body)
    if v["bot_id"]:
        await bots.get_bot(uid, v["bot_id"])
    else:
        await groups.get_group(uid, v["group_id"])
    n = (await db.q1("select count(*)::int as n from schedules where user_id = %s and kind = 'recurring' and status <> 'cancelled'", uid))["n"]
    if n >= MAX_SCHEDULES:
        raise ApiError(409, f"Maksimal {MAX_SCHEDULES} tugas berulang. Hapus yang tidak dipakai.")
    tz = (await settings.get(uid))["timezone"]
    sid = str(uuid.uuid4())
    await db.ex("insert into schedules (id, user_id, kind, title, bot_id, group_id, prompt, days, time_of_day, timezone) "
                "values (%s, %s, 'recurring', %s, %s, %s, %s, %s, %s, %s)",
                sid, uid, v["title"], v["bot_id"], v["group_id"], v["prompt"], v["days"], v["time"], tz)
    await materialize()
    return await get_view(uid, sid)


async def pause(uid: str, sid: str) -> dict:
    if (await _owned(uid, sid))["status"] != "active":
        raise ApiError(409, "Tugas berulang tidak sedang aktif")
    await db.ex("update schedules set status = 'paused' where id = %s", sid)
    await tasks.end_schedule_tasks(sid, paused=True)
    return await get_view(uid, sid)


async def resume(uid: str, sid: str) -> dict:
    if (await _owned(uid, sid))["status"] != "paused":
        raise ApiError(409, "Tugas berulang tidak sedang dijeda")
    await tasks.drop_paused_tasks(sid)  # the days archived by the pause come back through materialize
    await db.ex("update schedules set status = 'active' where id = %s", sid)
    await materialize()
    return await get_view(uid, sid)


async def delete(uid: str, sid: str) -> None:
    await _owned(uid, sid)
    if await db.q1("select 1 from tasks where schedule_id = %s and status = 'running'", sid):
        raise ApiError(409, "Ada tugas berulang yang sedang berjalan. Hentikan atau tunggu selesai.")
    await tasks.end_schedule_tasks(sid, paused=False)
    await db.ex("delete from schedules where id = %s", sid)  # finished tasks stay on the board, without the link


async def views(uid: str, only: str | None = None) -> list[dict]:
    rows = await db.q("select * from schedules where user_id = %s and kind = 'recurring' and status <> 'cancelled' "
                      "and (%s::uuid is null or id = %s) order by created_at desc", uid, only, only)
    names = {b["id"]: b["name"] for b in await db.q("select id, name from bots where user_id = %s", uid)}
    gnames = {str(g["id"]): g["name"] for g in await db.q("select id, name from groups where user_id = %s", uid)}
    nxt = {str(r["schedule_id"]): r["at"] for r in await db.q(
        "select schedule_id, min(scheduled_at) as at from tasks where user_id = %s and status = 'scheduled' and schedule_id is not null "
        "group by schedule_id", uid)}
    return [{"id": str(s["id"]), "title": s["title"], "status": s["status"], "bot_id": s["bot_id"],
             "group_id": str(s["group_id"]) if s["group_id"] else None,
             "target": names.get(s["bot_id"]) if s["bot_id"] else gnames.get(str(s["group_id"]), "Grup"),
             "prompt": s["prompt"], "days": s["days"], "time": s["time_of_day"], "timezone": s["timezone"],
             "created_at": s["created_at"], "next_at": nxt.get(str(s["id"]))} for s in rows]


async def get_view(uid: str, sid: str) -> dict:
    return (await views(uid, sid))[0]


# ---------- the loop ----------

def _slot_key(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # migration 018 writes the same format


async def materialize() -> None:
    """Create the next HORIZON_DAYS of tasks of every active recurring schedule (no backfill of past times). A time is created
    once: the slot is part of the task's identity, so a cancelled or started-early one does not come back."""
    now = datetime.now(timezone.utc)
    for s in await db.q("select * from schedules where kind = 'recurring' and status = 'active'"):
        for t in slots(s["days"], s["time_of_day"], s["timezone"], now):
            await db.ex("insert into tasks (user_id, title, body, assignee_bot, assignee_group, status, scheduled_at, source, source_ref, schedule_id) "
                        "values (%s, %s, %s, %s, %s, 'scheduled', %s, 'recurring', %s, %s) "
                        "on conflict (schedule_id, (source_ref->>'slot')) where source = 'recurring' do nothing",
                        s["user_id"], s["title"], s["prompt"], s["bot_id"], s["group_id"], t,
                        Jsonb({"schedule_id": str(s["id"]), "slot": _slot_key(t)}), s["id"])


async def run_task(t: dict) -> None:
    """Run one claimed task and record how it ended (tasks.finish). Never raises."""
    tid, run_ids, outs = str(t["id"]), [], []
    res, result = {"status": "failed", "reason": "Kesalahan internal", "run_ids": []}, None
    tasks.STOPS.discard(tid)
    try:
        uid, ref = t["user_id"], t["source_ref"]
        text = await tasks.prompt_for(t)
        targets = ref.get("targets")  # a plan day: [writer, visual] of the group
        origin = {"type": "marketing" if targets else "chat", "task_id": tid}
        stopped = lambda: tid in tasks.STOPS  # noqa: E731

        async def link(ids: list[str]) -> None:
            await db.ex("update runs set task_id = %s where id = any(%s::uuid[])", tid, ids)

        async def start_with(bot, text, session, kind, gid, ins):
            run = await engine.start_run(uid, bot, session, text, kind, gid, ins, origin=origin)
            run_ids.append(str(run["id"]))
            await link([str(run["id"])])
            await db.ex("update tasks set current_run_id = %s where id = %s", run["id"], tid)
            return run

        async def collect(bot, row):
            outs.append((row["output"] or "").strip())

        if t["assignee_bot"]:
            sid = f"web-task-{tid[:12]}"  # one conversation per task: a reply continues it
            await db.ex("insert into chat_sessions (session_id, user_id, bot_id) values (%s, %s, %s) on conflict do nothing",
                        sid, uid, t["assignee_bot"])
            res = await drive([t["assignee_bot"]], lambda i, o: text, lambda bot, x: start_with(bot, x, sid, "chat", None, None),
                              engine.wait_done, collect, stopped)
            result = outs[-1] if outs else None
        elif targets:
            gid = str(t["assignee_group"])
            g, mems = await groups.get_group(uid, gid), await groups.members(gid)
            ins = groups._instructions(g["name"], mems)
            await groups.post(gid, "system", f"Jadwal berjalan: {t['title']}")

            async def done(bot, row):
                await collect(bot, row)
                if outs[-1]:
                    await groups.post(gid, "bot", outs[-1], bot, row["id"])
            res = await drive(targets, lambda i, o: text if i == 0 else f"{text}\n\nNaskah dari Writer:\n{o[-1]}",
                              lambda bot, x: start_with(bot, x, f"grup-{gid}-{bot}", "group", gid, ins),
                              engine.wait_done, done, stopped)
            result = "\n\n---\n\n".join(o for o in outs if o) or None
        else:  # a team: a normal message to the group; the task follows the runs the group loop starts for it
            gid = str(t["assignee_group"])
            try:
                sent = (await groups.send(uid, gid, text, "queue"))["message"]
            except ApiError as e:
                res = {"status": "skipped" if e.status == 402 else "failed", "reason": e.message, "run_ids": []}
            else:
                async def poll():
                    return await db.q("select id, status, error from runs where user_id = %s and group_id = %s and created_at >= %s "
                                      "order by created_at", uid, gid, sent["created_at"])

                res = await follow_group(poll, lambda: gid in groups.ACTIVE, stopped, lambda: groups.stop(uid, gid), link)
                last = await db.q1("select text from group_messages where group_id = %s and author = 'bot' and id > %s order by id desc limit 1",
                                   gid, sent["id"])
                result = last["text"] if last else None
    except Exception as e:
        res = {"status": "failed", "reason": e.message if isinstance(e, ApiError) else f"Kesalahan internal: {type(e).__name__}",
               "run_ids": run_ids}
    finally:
        tasks.STOPS.discard(tid)
        TASKS.pop(tid, None)
    await tasks.finish(t, res["status"], res["reason"], result)


async def tick() -> None:
    await materialize()
    await tasks.release_due()
    while (t := await tasks.claim()):
        TASKS[str(t["id"])] = asyncio.create_task(run_task(t))


async def loop() -> None:
    while True:
        tasks.WAKE.clear()
        try:
            await tick()
        except asyncio.CancelledError:
            raise
        except Exception:
            pass  # a database hiccup must not end the scheduler; the next tick retries
        try:
            await asyncio.wait_for(tasks.WAKE.wait(), TICK_SECONDS)  # a task that became ready wakes us early
        except asyncio.TimeoutError:
            pass


async def recover() -> None:
    await tasks.recover()
