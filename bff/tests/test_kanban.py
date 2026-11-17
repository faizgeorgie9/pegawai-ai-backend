"""Kanban board: state -> column mapping, the read-only Hermes adapter, linking group runs to an occurrence, user scoping.
The tests marked `db` need TEST_DATABASE_URL (see test_scheduler.py)."""
import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from test_scheduler import with_db

from bff import config, kanban, scheduler


# ---------- status mapping ----------

@pytest.mark.parametrize("table, status, col, outcome", [
    (kanban.RUN, "queued", "todo", None), (kanban.RUN, "running", "running", None),
    (kanban.RUN, "completed", "done", "ok"), (kanban.RUN, "failed", "done", "failed"),
    (kanban.RUN, "cancelled", "done", "cancelled"), (kanban.RUN, "interrupted", "done", "failed"),
    (kanban.OCC, "planned", "todo", None), (kanban.OCC, "running", "running", None), (kanban.OCC, "done", "done", "ok"),
    (kanban.OCC, "skipped", "blocked", None), (kanban.OCC, "failed", "done", "failed"), (kanban.OCC, "cancelled", "done", "cancelled"),
    (kanban.SEQ, "queued", "todo", None), (kanban.SEQ, "running", "running", None), (kanban.SEQ, "completed", "done", "ok"),
    (kanban.SEQ, "failed", "done", "failed"), (kanban.SEQ, "stopped", "done", "cancelled"),
])
def test_state_maps_to_column(table, status, col, outcome):
    assert kanban.place(table, status)[:2] == (col, outcome)


def test_waiting_for_the_user_is_blocked():
    assert kanban.place(kanban.RUN, "running", "clarify") == ("blocked", None, "Menunggu jawaban Anda")
    assert kanban.place(kanban.SEQ, "running", "approval")[0] == "blocked"
    assert kanban.place(kanban.RUN, "completed", "clarify")[0] == "done"  # only a running item can wait
    assert kanban.place(kanban.OCC, "planned", None, paused=True) == ("blocked", None, "Jadwal dijeda")
    assert kanban.place(kanban.OCC, "planned", None, paused=False)[0] == "todo"


def test_board_orders_and_caps_columns():
    t = datetime(2026, 11, 16, tzinfo=timezone.utc)
    mk = lambda i, col: {"column": col, "at": t + timedelta(hours=i)}  # noqa: E731
    cols = {c["id"]: c for c in kanban.board([mk(i, "todo") for i in range(3)] + [mk(i, "done") for i in range(kanban.PER_COLUMN + 5)])}
    assert [c["at"] for c in cols["todo"]["cards"]] == sorted(c["at"] for c in cols["todo"]["cards"])  # soonest first
    assert cols["done"]["total"] == kanban.PER_COLUMN + 5 and len(cols["done"]["cards"]) == kanban.PER_COLUMN
    assert cols["done"]["cards"][0]["at"] > cols["done"]["cards"][1]["at"] and cols["running"]["total"] == 0


# ---------- Hermes adapter ----------

HERMES_JSON = json.dumps([
    {"id": "t1", "title": "Tulis brief", "status": "ready", "tenant": "u1", "assignee": "rian", "created_at": 1763251200},
    {"id": "t2", "title": "Cek stok", "status": "review", "tenant": "u1"},
    {"id": "t3", "title": "Selesai", "status": "done", "tenant": "u1", "completed_at": "2026-11-15T10:00:00Z"},
    {"id": "t4", "title": "Arsip", "status": "archived", "tenant": "u1"},
    {"id": "t5", "title": "Milik orang lain", "status": "running", "tenant": "u2"},
    {"id": "t6", "title": "Tanpa pemilik", "status": "running"},
])


def test_hermes_cards_are_scoped_to_the_user_and_labeled():
    cards = kanban.parse_hermes(HERMES_JSON, "u1")
    assert [(c["key"], c["column"], c["source"]) for c in cards] == [("hermes:t1", "todo", "hermes"), ("hermes:t2", "blocked", "hermes"),
                                                                     ("hermes:t3", "done", "hermes")]
    assert cards[0]["agents"][0]["name"] == "rian" and cards[2]["at"].year == 2026
    assert kanban.parse_hermes(json.dumps({"tasks": []}), "u1") == [] and kanban.parse_hermes('{"x": 1}', "u1") == []


def test_missing_cli_gives_an_empty_section_not_an_error(monkeypatch):
    monkeypatch.setattr(config, "HERMES_KANBAN_CMD", ["definitely-not-a-real-hermes-binary", "kanban", "list", "--json"])
    kanban._CACHE.clear()
    kanban._REFRESH.clear()
    h = asyncio.run(kanban.hermes_section("u1"))
    assert h["state"] == "unavailable" and h["cards"] == []


def test_garbage_output_is_unavailable_and_slow_cli_does_not_block(monkeypatch):
    monkeypatch.setattr(kanban, "_run_cli", lambda uid: "not json")
    kanban._CACHE.clear()
    assert asyncio.run(kanban.hermes_section("u1"))["state"] == "unavailable"

    import time
    monkeypatch.setattr(kanban, "_run_cli", lambda uid: time.sleep(0.6) or HERMES_JSON)
    monkeypatch.setattr(kanban, "HERMES_WAIT", 0.05)
    kanban._CACHE.clear()

    async def go():
        first = await kanban.hermes_section("u1")  # the CLI is still running: pending, quickly
        await asyncio.sleep(0.9)
        return first, await kanban.hermes_section("u1")
    first, later = asyncio.run(go())
    assert first["state"] == "pending" and later["state"] == "ok" and len(later["cards"]) == 3


# ---------- recurring schedule on a group: following its runs ----------

def follow(polls, busy_after=1, stopped_at=None):
    saved, halted, n = [], [], {"i": 0}

    async def poll():
        n["i"] += 1
        return polls[min(n["i"], len(polls)) - 1]

    async def save(ids):
        saved.append(ids)

    async def halt():
        halted.append(1)

    async def sleep(_):
        pass
    res = asyncio.run(scheduler.follow_group(poll, lambda: n["i"] <= busy_after, lambda: stopped_at is not None and n["i"] >= stopped_at,
                                             halt, save, sleep))
    return res, saved, halted


def test_group_runs_are_linked_to_the_occurrence_and_status_follows_them():
    ok = {"id": uuid.uuid4(), "status": "completed", "error": None}
    ok2 = {"id": uuid.uuid4(), "status": "completed", "error": None}
    res, saved, _ = follow([[ok], [ok, ok2]], busy_after=2)
    assert res == {"status": "done", "reason": None, "run_ids": [str(ok["id"]), str(ok2["id"])]}
    assert saved == [[str(ok["id"])], [str(ok["id"]), str(ok2["id"])]]
    bad = {"id": uuid.uuid4(), "status": "failed", "error": "Hermes menjawab 500"}
    assert follow([[ok, bad]])[0]["status"] == "failed" and follow([[ok, bad]])[0]["reason"] == "Hermes menjawab 500"
    assert follow([[]])[0] == {"status": "done", "reason": None, "run_ids": []}  # nobody answered: nothing to link


def test_stopping_the_occurrence_stops_the_group():
    res, _, halted = follow([[{"id": uuid.uuid4(), "status": "running", "error": None}]], busy_after=3, stopped_at=2)
    assert res["status"] == "cancelled" and halted == [1]


# ---------- database ----------

async def add_run(db, uid, status, text, group=None, error=None):
    rid = str(uuid.uuid4())
    await db.ex("insert into runs (id, user_id, bot_id, session_id, group_id, kind, status, input, error) "
                "values (%s, %s, 'rian', 's1', %s, %s, %s, %s, %s)", rid, uid, group, "group" if group else "chat", status, text, error)
    return rid


@with_db
async def test_board_is_built_from_real_rows_and_scoped_to_the_user(db):
    me, other = (f"u-{uuid.uuid4().hex[:8]}" for _ in range(2))
    for uid in (me, other):
        await add_run(db, uid, "running", f"sedang jalan {uid}")
    for st in ("queued", "completed", "failed", "cancelled"):
        await add_run(db, me, st, f"tugas {st}\nbaris dua", error="boom" if st == "failed" else None)
    sid = str(uuid.uuid4())
    await db.ex("insert into schedules (id, user_id, kind, title, bot_id, prompt, days, time_of_day, timezone) "
                "values (%s, %s, 'recurring', 'Rangkuman harian', 'rian', 'halo', '{0}', '09:00', 'Asia/Jakarta')", sid, me)
    now = datetime.now(timezone.utc)
    done_run = await add_run(db, me, "completed", "dari jadwal")
    for status, at, reason, runs in (("planned", now + timedelta(hours=3), None, []), ("skipped", now - timedelta(hours=1), "Batas biaya", []),
                                     ("done", now - timedelta(hours=2), None, [done_run])):
        await db.ex("insert into schedule_occurrences (schedule_id, user_id, planned_at, brief, status, skip_reason, run_ids, finished_at) "
                    "values (%s, %s, %s, 'halo', %s, %s, %s, %s)", sid, me, at, status, reason, json.dumps(runs), at)

    cards = await kanban.own_cards(me, 7, None, None)
    by = {c["key"]: c for c in cards}
    col = lambda title: next(c for c in cards if c["title"] == title)  # noqa: E731
    assert col("tugas queued")["column"] == "todo" and col("tugas completed")["column"] == "done"
    assert (col("tugas failed")["column"], col("tugas failed")["outcome"], col("tugas failed")["note"]) == ("done", "failed", "boom")
    assert col("tugas cancelled")["outcome"] == "cancelled" and col("tugas completed")["cost"] is not None
    assert col(f"sedang jalan {me}")["column"] == "running" and col("tugas queued")["title"] == "tugas queued"  # first line only
    occ = [c for c in cards if c["source"] == "schedule"]
    assert sorted((c["column"], c["outcome"]) for c in occ) == [("blocked", None), ("done", "ok"), ("todo", None)]
    assert next(c for c in occ if c["column"] == "blocked")["note"] == "Batas biaya"
    assert all(c["ref"]["schedule_id"] == sid and c["ref"]["occurrence_id"] for c in occ)  # the board can act on its cards
    assert next(c for c in cards if c["title"] == "tugas queued")["ref"]["run_id"]
    assert next(c for c in occ if c["column"] == "done")["cost"] is not None
    assert "dari jadwal" not in {c["title"] for c in cards if c["source"] == "chat"}  # the run shows through its occurrence
    assert not any(other in c["title"] for c in cards) and len(by) == len(cards)
    assert all(other not in c["title"] for c in await kanban.own_cards(other, 7, None, None) if c["source"] == "schedule")
    assert [c["title"] for c in await kanban.own_cards(other, 7, None, None)] == [f"sedang jalan {other}"]
    assert await kanban.own_cards(me, 7, "diana", None) == []  # agent filter
