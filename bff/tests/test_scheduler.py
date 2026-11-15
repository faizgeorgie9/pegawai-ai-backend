"""Scheduler and plan approval. The pure parts always run; the tests marked `db` need a throwaway Postgres: set
TEST_DATABASE_URL (e.g. postgresql://postgres@127.0.0.1:5433/pegawai_ai_test, an empty database) and they run the real SQL."""
import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from bff import plan_schema, scheduler
from bff.errors import ApiError

JKT_NOW = datetime(2026, 11, 16, 3, 0, tzinfo=timezone.utc)  # Monday 10:00 in Jakarta

DAY = {"date": "2026-11-17", "theme": "Kaos baru", "products": ["Kaos A"], "brief": "Satu post feed dan satu story"}
PLAN = {"plan": {"title": "Konten 2 hari", "days": [DAY, {**DAY, "date": "2026-11-18", "theme": "Diskon"}]}}


def fenced(obj, pre="Ini rencananya.\n"):
    import json
    return f"{pre}```json\n{json.dumps(obj)}\n```"


# ---------- plan JSON ----------

def test_valid_plan_parses_and_strips():
    plan, errs = plan_schema.parse(fenced(PLAN))
    assert errs == [] and [d["date"] for d in plan["days"]] == ["2026-11-17", "2026-11-18"]
    assert plan["days"][0]["time"] == "09:00" and plan["title"] == "Konten 2 hari"
    assert plan_schema.strip(fenced(PLAN)) == "Ini rencananya."


@pytest.mark.parametrize("bad", [
    {"plan": {"days": []}},
    {"plan": {"days": [{**DAY, "brief": " "}]}},
    {"plan": {"days": [{**DAY, "date": "17-11-2026"}]}},
    {"plan": {"days": [{**DAY, "time": "9am"}]}},
    {"plan": {"days": [{**DAY, "products": [3]}]}},
    {"plan": {"days": [DAY, DAY]}},  # duplicate date
    {"plan": {"days": [{**DAY, "date": "2026-11-18"}, DAY]}},  # not in order
    {"plan": {"days": [{**DAY, "date": f"2026-12-{d:02d}"} for d in range(1, 16)]}},  # 15 days
])
def test_invalid_plan_is_not_a_plan(bad):
    plan, errs = plan_schema.parse(fenced(bad))
    assert plan is None and errs


def test_text_without_plan_or_with_broken_json():
    assert plan_schema.parse("Halo semuanya") == (None, [])
    assert plan_schema.parse("```json\n{not json}\n```") == (None, [])
    assert plan_schema.parse(fenced({"other": 1})) == (None, [])


# ---------- times ----------

def test_slots_are_future_local_times():
    s = scheduler.slots([0, 2], "09:00", "Asia/Jakarta", JKT_NOW)  # Mon and Wed, 09:00 WIB = 02:00 UTC
    assert s[0] == datetime(2026, 11, 18, 2, 0, tzinfo=timezone.utc)  # Monday 09:00 already passed at 10:00
    assert all(t > JKT_NOW and t.weekday() in (0, 2) for t in s)
    assert scheduler.slots([0], "11:00", "Asia/Jakarta", JKT_NOW)[0] == datetime(2026, 11, 16, 4, 0, tzinfo=timezone.utc)


def test_plan_slots_reject_past_day():
    plan = plan_schema.parse(fenced(PLAN))[0]
    out = scheduler.plan_slots(plan, "Asia/Jakarta", JKT_NOW)
    assert out[0][0] == datetime(2026, 11, 17, 2, 0, tzinfo=timezone.utc) and out[0][1].startswith("Hari 1 dari 2")
    with pytest.raises(ApiError) as e:
        scheduler.plan_slots(plan, "Asia/Jakarta", datetime(2026, 11, 18, 5, 0, tzinfo=timezone.utc))
    assert e.value.status == 400


def test_find_executors_by_role():
    mems = [{"bot_id": "pm", "role": "Project Manager", "name": "Bimo"}, {"bot_id": "w", "role": "Content Writer", "name": "Bram"},
            {"bot_id": "v", "role": "Visual Designer", "name": "Vina"}]
    assert scheduler.find_executors(mems) == ["w", "v"]
    with pytest.raises(ApiError) as e:
        scheduler.find_executors(mems[:2])
    assert e.value.status == 409


@pytest.mark.parametrize("bad", [
    {"title": "", "prompt": "x", "days": [1], "time": "09:00", "bot_id": "rian"},
    {"title": "t", "prompt": "x", "days": [], "time": "09:00", "bot_id": "rian"},
    {"title": "t", "prompt": "x", "days": [7], "time": "09:00", "bot_id": "rian"},
    {"title": "t", "prompt": "x", "days": [True], "time": "09:00", "bot_id": "rian"},
    {"title": "t", "prompt": "x", "days": [1], "time": "25:00", "bot_id": "rian"},
    {"title": "t", "prompt": "x", "days": [1], "time": "09:00"},  # no target
    {"title": "t", "prompt": "x", "days": [1], "time": "09:00", "bot_id": "rian", "group_id": "g"},  # two targets
])
def test_recurring_body_rejected(bad):
    with pytest.raises(ApiError) as e:
        scheduler.clean_recurring(bad)
    assert e.value.status == 400


# ---------- running an occurrence ----------

def run_drive(targets, start, statuses=None, stopped=lambda: False):
    posted = []

    async def wait(rid):
        st = (statuses or {}).get(rid, "completed")
        return {"status": st, "output": f"out-{rid}", "error": "boom" if st == "failed" else None}

    async def done(bot, row):
        posted.append(bot)

    res = asyncio.run(scheduler.drive(targets, lambda i, outs: f"in{i}:{outs[-1] if outs else ''}", start, wait, done, stopped))
    return res, posted


def test_quota_refusal_marks_skipped_with_reason():
    async def start(bot, text):
        raise ApiError(402, "Batas biaya bulan ini tercapai.", upgrade=True)
    res, posted = run_drive(["w", "v"], start)
    assert res == {"status": "skipped", "reason": "Batas biaya bulan ini tercapai.", "run_ids": []} and posted == []


def test_quota_refusal_after_first_run_is_failed_not_skipped():
    calls = []

    async def start(bot, text):
        calls.append(text)
        if len(calls) == 2:
            raise ApiError(402, "Batas")
        return {"id": "r1"}
    res, posted = run_drive(["w", "v"], start)
    assert res["status"] == "failed" and res["run_ids"] == ["r1"] and posted == ["w"]


def test_writer_output_feeds_visual_and_done():
    seen = []

    async def start(bot, text):
        seen.append(text)
        return {"id": f"r{len(seen)}"}
    res, posted = run_drive(["w", "v"], start)
    assert res["status"] == "done" and res["run_ids"] == ["r1", "r2"] and posted == ["w", "v"]
    assert seen == ["in0:", "in1:out-r1"]


def test_failed_cancelled_and_stopped():
    async def start(bot, text):
        return {"id": "r1"}
    assert run_drive(["w"], start, {"r1": "failed"})[0]["status"] == "failed"
    assert run_drive(["w"], start, {"r1": "cancelled"})[0]["status"] == "cancelled"
    res, _ = run_drive(["w"], start, stopped=lambda: True)
    assert res["status"] == "cancelled" and res["run_ids"] == []


# ---------- database ----------

DSN = os.environ.get("TEST_DATABASE_URL")
db_only = pytest.mark.skipif(not DSN, reason="TEST_DATABASE_URL not set (needs a throwaway Postgres)")


def with_db(fn):
    """Run an async test body against the migrated throwaway database, in one event loop."""
    def wrapper():
        from bff import config, db

        async def go():
            config.DATABASE_URL = DSN
            await db.open_pool()
            try:
                await fn(db)
            finally:
                await db.close_pool()
        asyncio.run(go(), loop_factory=asyncio.SelectorEventLoop)  # psycopg async cannot use the Windows Proactor loop
    wrapper.__name__ = fn.__name__
    return db_only(wrapper)


async def make_sched(db, uid, at, kind="recurring"):
    sid = str(uuid.uuid4())
    await db.ex("insert into schedules (id, user_id, kind, title, bot_id, prompt, days, time_of_day, timezone) "
                "values (%s, %s, %s, 't', 'rian', 'halo', '{0}', '09:00', 'Asia/Jakarta')", sid, uid, kind)
    await db.ex("insert into schedule_occurrences (schedule_id, user_id, planned_at, brief) values (%s, %s, %s, 'halo')",
                sid, uid, at)
    return sid


@with_db
async def test_claim_is_idempotent_across_concurrent_loops(db):
    uid = f"u-{uuid.uuid4().hex[:8]}"
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    await make_sched(db, uid, past)
    got = await asyncio.gather(*[scheduler.claim() for _ in range(8)])
    mine = [g for g in got if g and g["user_id"] == uid]
    assert len(mine) == 1 and mine[0]["status"] == "running"
    assert not await db.q1("select 1 from schedule_occurrences where user_id = %s and status = 'planned'", uid)


@with_db
async def test_claim_skips_future_paused_and_late(db):
    uid = f"u-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    future = await make_sched(db, uid, now + timedelta(hours=1))
    paused = await make_sched(db, uid, now - timedelta(minutes=1))
    late = await make_sched(db, uid, now - timedelta(hours=3))
    await db.ex("update schedules set status = 'paused' where id = %s", paused)
    await scheduler.expire_late()
    while (c := await scheduler.claim()):  # other tests' rows may be due too
        assert c["user_id"] != uid
    rows = {str(r["schedule_id"]): r for r in await db.q("select * from schedule_occurrences where user_id = %s", uid)}
    assert rows[future]["status"] == rows[paused]["status"] == "planned"
    assert rows[late]["status"] == "skipped" and rows[late]["skip_reason"] == scheduler.LATE_REASON


@with_db
async def test_run_occurrence_quota_refusal_is_recorded_not_raised(db):
    from bff import engine
    uid = f"u-{uuid.uuid4().hex[:8]}"
    await make_sched(db, uid, datetime.now(timezone.utc) - timedelta(minutes=1))
    occ = next(c for c in iter(lambda: asyncio.run_coroutine_threadsafe(scheduler.claim(), asyncio.get_running_loop()), None)) \
        if False else None
    orig = engine.start_run

    async def refuse(*a, **k):
        raise ApiError(402, "Batas biaya bulan ini tercapai.", upgrade=True)
    engine.start_run = refuse
    try:
        while (c := await scheduler.claim()):
            if c["user_id"] == uid:
                occ = c
                break
        res = await scheduler.run_occurrence(occ)
    finally:
        engine.start_run = orig
    row = await db.q1("select * from schedule_occurrences where id = %s", occ["id"])
    assert res["status"] == "skipped" and row["status"] == "skipped" and "Batas biaya" in row["skip_reason"]


async def make_group(db, uid):
    gid = str(uuid.uuid4())
    await db.ex("insert into groups (id, user_id, name) values (%s, %s, 'Tim')", gid, uid)
    for i, b in enumerate(("diana", "rian", "budi")):  # lead, copywriting (writer), visual designer
        await db.ex("insert into group_members (group_id, bot_id, position) values (%s, %s, %s)", gid, b, i)
    return gid


def tomorrow_plan():
    d = (datetime.now(timezone.utc) + timedelta(days=2)).date()
    return fenced({"plan": {"title": "Uji", "days": [{**DAY, "date": d.isoformat()},
                                                      {**DAY, "date": (d + timedelta(days=1)).isoformat()}]}})


@with_db
async def test_approve_twice_creates_one_schedule_and_scoping(db):
    from bff import groups
    uid = "default"
    gid = await make_group(db, uid)
    msg = await groups.post(gid, "bot", tomorrow_plan(), "diana")
    assert msg["plan"]["schedule_id"] is None
    a, b = await asyncio.gather(scheduler.approve_plan(uid, gid, msg["id"]), scheduler.approve_plan(uid, gid, msg["id"]))
    again = await scheduler.approve_plan(uid, gid, msg["id"])
    assert a["id"] == b["id"] == again["id"]
    assert (await db.q1("select count(*)::int as n from schedules where source_message_id = %s", msg["id"]))["n"] == 1
    occs = await db.q("select * from schedule_occurrences where schedule_id = %s", a["id"])
    assert len(occs) == 2 and all(o["targets"] == ["rian", "budi"] for o in occs)  # writer, then visual
    listed = (await groups.list_messages(uid, gid, None, 50))
    assert [m["plan"]["schedule_id"] for m in listed if "plan" in m] == [a["id"]]
    with pytest.raises(ApiError):  # approved plans cannot be sent back for revision
        await scheduler.request_revision(uid, gid, msg["id"], "ubah")
    # another user sees and touches nothing
    other = f"u-{uuid.uuid4().hex[:8]}"
    assert await scheduler.views(other) == []
    for call in (scheduler.pause, scheduler.cancel, scheduler.delete):
        with pytest.raises(ApiError) as e:
            await call(other, a["id"])
        assert e.value.status == 404
    with pytest.raises(ApiError):
        await scheduler.approve_plan(other, gid, msg["id"])


@with_db
async def test_invalid_plan_message_cannot_be_approved(db):
    from bff import groups
    gid = await make_group(db, "default")
    msg = await groups.post(gid, "bot", "Rencana: hari 1 posting.", "diana")
    assert "plan" not in msg
    with pytest.raises(ApiError) as e:
        await scheduler.approve_plan("default", gid, msg["id"])
    assert e.value.status == 404


@with_db
async def test_cancel_marks_planned_occurrences_and_recurring_materializes(db):
    uid = "default"  # the builtin bots belong to this user
    v = await scheduler.create(uid, {"title": "Pagi", "prompt": "halo", "days": [0, 1, 2, 3, 4, 5, 6], "time": "09:00", "bot_id": "rian"})
    n = len([o for o in v["occurrences"] if o["status"] == "planned"])
    assert n >= 14 and v["next_at"] is not None
    await scheduler.materialize()  # idempotent: no duplicates
    assert len((await scheduler.get_view(uid, v["id"]))["occurrences"]) == len(v["occurrences"])
    c = await scheduler.cancel(uid, v["id"])
    assert c["status"] == "cancelled" and all(o["status"] == "cancelled" for o in c["occurrences"])
    await scheduler.delete(uid, v["id"])
    assert v["id"] not in [x["id"] for x in await scheduler.views(uid)]
