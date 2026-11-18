"""Scheduler and plan helpers. The pure parts always run; `with_db` (used by test_tasks.py too) needs a throwaway Postgres: set
TEST_DATABASE_URL (e.g. postgresql://postgres@127.0.0.1:5433/pegawai_test, an empty database) and the tests run the real SQL."""
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
    out = plan_schema.plan_slots(plan, "Asia/Jakarta", JKT_NOW)
    assert out[0][0] == datetime(2026, 11, 17, 2, 0, tzinfo=timezone.utc) and out[0][1].startswith("Hari 1 dari 2")
    with pytest.raises(ApiError) as e:
        plan_schema.plan_slots(plan, "Asia/Jakarta", datetime(2026, 11, 18, 5, 0, tzinfo=timezone.utc))
    assert e.value.status == 400


def test_find_executors_by_role():
    mems = [{"bot_id": "pm", "role": "Project Manager", "name": "Bimo"}, {"bot_id": "w", "role": "Content Writer", "name": "Bram"},
            {"bot_id": "v", "role": "Visual Designer", "name": "Vina"}]
    assert plan_schema.find_executors(mems) == ["w", "v"]
    with pytest.raises(ApiError) as e:
        plan_schema.find_executors(mems[:2])
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


async def make_group(db, uid):
    gid = str(uuid.uuid4())
    await db.ex("insert into groups (id, user_id, name) values (%s, %s, 'Tim')", gid, uid)
    for i, b in enumerate(("diana", "rian", "budi")):  # lead, copywriting (writer), visual designer
        await db.ex("insert into group_members (group_id, bot_id, position) values (%s, %s, %s)", gid, b, i)
    return gid
