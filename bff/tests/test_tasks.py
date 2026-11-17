"""Papan Tugas (tasks.py): status transitions, cascade cancel, the drag rules, the board and its user scoping.
Every test needs TEST_DATABASE_URL (see test_scheduler.py): the rules are enforced by the real SQL."""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from test_scheduler import make_group, with_db

from bff import tasks
from bff.errors import ApiError


async def make_user(db):
    uid = f"u-{uuid.uuid4().hex[:8]}"
    await db.ex("insert into users (id, name, plan_id) values (%s, 'Uji', 'pro')", uid)
    await db.ex("insert into bots (id, user_id, name, role, team) values (%s, %s, 'Rian', 'Writer', 'marketing')", f"rian-{uid}", uid)
    return uid, f"rian-{uid}"


async def make(db, uid, bot, title="Tulis caption", **kw):
    t = await tasks.create(uid, {"title": title, "assignee_bot": bot, **kw})
    return t["id"]


async def force(db, tid, status, **cols):
    sets = {"status": status, **cols}
    await db.ex(f"update tasks set {', '.join(f'{k} = %s' for k in sets)} where id = %s", *sets.values(), tid)


async def status_of(db, tid):
    return (await db.q1("select status, outcome, attempts from tasks where id = %s", tid))


async def refuses(coro, status=409):
    with pytest.raises(ApiError) as e:
        await coro
    assert e.value.status == status


@with_db
async def test_user_verbs_walk_the_status_machine(db):
    uid, bot = await make_user(db)
    tid = await make(db, uid, bot)
    assert (await status_of(db, tid))["status"] == "todo"

    assert (await tasks.do(uid, tid, "start", {}))["status"] == "ready"
    await refuses(tasks.do(uid, tid, "stop", {}))  # only a running task can be stopped
    await refuses(tasks.do(uid, tid, "approve", {}))
    await refuses(tasks.do(uid, tid, "archive", {}))  # only done tasks are archived; others are cancelled

    await force(db, tid, "running", current_run_id=None)
    assert (await tasks.do(uid, tid, "stop", {}))["block_kind"] == "stopped"

    await refuses(tasks.do(uid, tid, "reply", {"text": "  "}), 400)  # an empty answer is not an answer
    d = await tasks.do(uid, tid, "reply", {"text": "Pakai gaya santai"})
    assert d["status"] == "ready" and [c["text"] for c in d["comments"]] == ["Pakai gaya santai"]

    await force(db, tid, "review", result="Caption siap")
    await refuses(tasks.do(uid, tid, "request_changes", {"note": ""}), 400)
    assert (await tasks.do(uid, tid, "request_changes", {"note": "Lebih pendek"}))["status"] == "ready"
    await force(db, tid, "review")
    d = await tasks.do(uid, tid, "approve", {})
    assert (d["status"], d["outcome"]) == ("done", "ok")

    await force(db, tid, "done", attempts=2)
    d = await tasks.do(uid, tid, "retry", {})
    assert d["status"] == "ready" and d["outcome"] is None and (await status_of(db, tid))["attempts"] == 0
    await force(db, tid, "done", outcome="ok")
    assert (await tasks.do(uid, tid, "archive", {}))["status"] == "archived"
    assert (await tasks.do(uid, tid, "restore", {}))["status"] == "todo"
    kinds = [e["kind"] for e in (await tasks.detail(uid, tid))["events"]]
    assert kinds[0] == "created" and {"start", "stop", "reply", "approve", "retry", "archive", "restore"} <= set(kinds)


@with_db
async def test_cancel_cascades_to_unfinished_children_only(db):
    uid, bot = await make_user(db)
    parent = await make(db, uid, bot, "Rencana konten")
    kids = [await make(db, uid, bot, f"Hari {i}") for i in range(3)]
    for k in kids:
        await db.ex("update tasks set parent_id = %s where id = %s", parent, k)
    await force(db, kids[0], "done", outcome="ok")
    await force(db, kids[1], "scheduled", scheduled_at=datetime.now(timezone.utc) + timedelta(days=1))
    await force(db, kids[2], "blocked", block_kind="needs_input")

    d = await tasks.do(uid, parent, "cancel", {})
    assert (d["status"], d["outcome"]) == ("archived", "cancelled")
    got = {k: await status_of(db, k) for k in kids}
    assert (got[kids[0]]["status"], got[kids[0]]["outcome"]) == ("done", "ok")
    assert all((got[k]["status"], got[k]["outcome"]) == ("archived", "cancelled") for k in kids[1:])
    await refuses(tasks.do(uid, parent, "cancel", {}))  # already archived


@with_db
async def test_drag_only_allows_needs_you_and_done_back_to_queue(db):
    uid, bot = await make_user(db)
    a, b, c = [await make(db, uid, bot) for _ in range(3)]
    await force(db, a, "review")
    await force(db, b, "done", outcome="ok", attempts=1)
    await force(db, c, "running")
    assert (await tasks.do(uid, a, "move", {"to": "queue"}))["column"] == "queue"
    assert (await tasks.do(uid, b, "move", {"to": "queue"}))["column"] == "queue"
    await refuses(tasks.do(uid, c, "move", {"to": "queue"}))
    await refuses(tasks.do(uid, a, "move", {"to": "running"}))  # Dikerjakan is never a drop target


@with_db
async def test_board_columns_filters_and_user_scoping(db):
    uid, bot = await make_user(db)
    other, other_bot = await make_user(db)
    todo = await make(db, uid, bot, "Antre satu")
    await make(db, other, other_bot, "Milik orang lain")
    waiting = await make(db, uid, bot, "Tunggu jawaban")
    old = await make(db, uid, bot, "Selesai lama")
    fresh = await make(db, uid, bot, "Selesai baru")
    await force(db, waiting, "blocked", block_kind="needs_input")
    await force(db, old, "done", outcome="ok", completed_at=datetime.now(timezone.utc) - timedelta(days=15))
    await force(db, fresh, "done", outcome="ok", completed_at=datetime.now(timezone.utc), result="# Hasil\nCaption jadi")

    b = await tasks.board(uid, None, None, None)
    cols = {c["id"]: [x["title"] for x in c["cards"]] for c in b["columns"]}
    assert cols == {"queue": ["Antre satu"], "running": [], "needs_you": ["Tunggu jawaban"], "done": ["Selesai baru"]}
    done = next(c for c in b["columns"] if c["id"] == "done")["cards"][0]
    assert done["line"] == "Hasil"
    assert done["primary_action"]["id"] == "open" and [m["id"] for m in done["more_actions"]] == ["retry", "archive"]
    assert [c["title"] for c in (await tasks.board(uid, None, None, "antre"))["columns"][0]["cards"]] == ["Antre satu"]
    assert (await tasks.board(uid, "nobody", None, None))["counts"] == {"queue": 0, "running": 0, "needs_you": 0, "done": 0}
    assert "Milik orang lain" not in str(await tasks.board(uid, None, None, None))
    await tasks.do(uid, todo, "cancel", {})
    arch = (await tasks.board(uid, None, None, None, archived=True))["columns"]
    assert [c["id"] for c in arch] == ["archived"] and [x["title"] for x in arch[0]["cards"]] == ["Antre satu"]
    await refuses(tasks.do(other, todo, "start", {}), 404)  # another user's task does not exist for you


@with_db
async def test_create_edit_and_comment_rules(db):
    uid, bot = await make_user(db)
    await refuses(tasks.create(uid, {"title": "x"}), 400)  # needs an agent or a team
    await refuses(tasks.create(uid, {"title": " ", "assignee_bot": bot}), 400)
    await refuses(tasks.create(uid, {"title": "x", "assignee_bot": "orang-lain"}), 404)
    await refuses(tasks.create(uid, {"title": "x", "assignee_bot": bot, "scheduled_at": "2020-01-01T00:00:00Z"}), 400)
    soon = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
    d = await tasks.create(uid, {"title": "Jadwal", "assignee_bot": bot, "scheduled_at": soon})
    assert d["status"] == "scheduled" and d["line"].startswith("Dijadwalkan")

    d = await tasks.edit(uid, d["id"], {"scheduled_at": None, "title": "Tanpa jadwal"})
    assert (d["status"], d["title"]) == ("todo", "Tanpa jadwal")
    d = await tasks.comment(uid, d["id"], "Catatan")
    assert d["status"] == "todo" and len(d["comments"]) == 1  # a note does not move the task
    await force(db, d["id"], "running")
    await refuses(tasks.edit(uid, d["id"], {"title": "Baru"}))  # not while it runs
    await force(db, d["id"], "review")
    await refuses(tasks.edit(uid, d["id"], {"scheduled_at": soon}))  # the time only matters in Antre


# ---------- stage B: dispatcher, run end, plans, recurring ----------

def test_prompt_has_task_parent_and_new_comments():
    t = {"title": "Caption hari 1", "body": "Tulis 3 opsi"}
    assert tasks.build_prompt(t, None, []) == "Tugas: Caption hari 1\n\nTulis 3 opsi"
    out = tasks.build_prompt(t, {"title": "Rencana Nov", "body": ""}, ["Lebih santai", "Tambah emoji"])
    assert "bagian dari: Rencana Nov" in out and out.endswith("- Lebih santai\n- Tambah emoji")


async def claim_mine(uid):
    mine = []
    while (t := await tasks.claim()):  # other tests' ready tasks may be taken too
        if t["user_id"] == uid:
            mine.append(t)
    return mine


async def walk(db, tid, *path):
    """Move a task along the statuses with transition(), as the dispatcher and the user's verbs do."""
    for to in path:
        await tasks.transition(await db.q1("select * from tasks where id = %s", tid), to, "system")


@with_db
async def test_dispatcher_picks_important_first_and_one_running_per_assignee(db):
    uid, bot = await make_user(db)
    other = f"viki-{uid}"
    await db.ex("insert into bots (id, user_id, name, role, team) values (%s, %s, 'Viki', 'Visual', 'marketing')", other, uid)
    normal, urgent = await make(db, uid, bot, "Biasa"), await make(db, uid, bot, "Penting", priority=1)
    elsewhere = await make(db, uid, other, "Agen lain")
    for tid in (normal, urgent, elsewhere):
        await tasks.do(uid, tid, "start", {})
    got = await claim_mine(uid)
    assert {g["title"] for g in got} == {"Penting", "Agen lain"}  # the same agent never has two running tasks
    assert all(g["status"] == "running" and g["attempts"] == 1 and g["started_at"] for g in got)
    first = next(g for g in got if g["title"] == "Penting")
    await tasks.finish(first, "done", None, "Caption jadi")
    assert [g["title"] for g in await claim_mine(uid)] == ["Biasa"]  # its agent is free again


@with_db
async def test_due_tasks_are_released_and_late_recurring_days_are_archived(db):
    uid, bot = await make_user(db)
    due, late, late_user = [await make(db, uid, bot, n) for n in ("Waktunya", "Terlewat", "Punya user")]
    now = datetime.now(timezone.utc)
    await force(db, due, "scheduled", scheduled_at=now - timedelta(minutes=1))
    await force(db, late, "scheduled", scheduled_at=now - timedelta(hours=3), source="recurring")
    await force(db, late_user, "scheduled", scheduled_at=now - timedelta(hours=3))
    await tasks.release_due()
    assert (await status_of(db, due))["status"] == "ready"
    assert (await status_of(db, late_user))["status"] == "ready"  # the user's own task still runs, late
    got = await status_of(db, late)
    assert (got["status"], got["outcome"]) == ("archived", "failed")


@with_db
async def test_run_end_moves_the_task_to_review_retry_or_blocked(db):
    uid, bot = await make_user(db)

    async def running():
        tid = await make(db, uid, bot)
        await force(db, tid, "running", started_at=datetime.now(timezone.utc), attempts=1)
        return await db.q1("select * from tasks where id = %s", tid)

    t = await running()
    await tasks.finish(t, "done", None, "# Caption\nSiap")
    d = await tasks.detail(uid, str(t["id"]))
    assert (d["status"], d["block_kind"], d["result"], d["line"]) == ("review", "review", "# Caption\nSiap", "Hasil siap ditinjau")

    t = await running()  # first failure: tried once, goes back in the queue
    await tasks.finish(t, "failed", "boom", None)
    assert (await status_of(db, t["id"]))["status"] == "ready"
    await force(db, t["id"], "running", started_at=t["started_at"], attempts=2)  # second failure: waits for the user
    await tasks.finish(t, "failed", "boom", None)
    d = await tasks.detail(uid, str(t["id"]))
    assert (d["status"], d["block_kind"], d["line"]) == ("blocked", "failed", tasks.FAILED_TEXT)

    t = await running()
    await tasks.finish(t, "skipped", "Batas biaya bulan ini tercapai.", None)
    assert (await tasks.detail(uid, str(t["id"])))["line"] == "Batas biaya bulan ini tercapai."

    t = await running()  # the user stopped it first: the late run end changes nothing
    await tasks.do(uid, str(t["id"]), "stop", {})
    await tasks.finish(t, "done", None, "terlambat")
    assert (await status_of(db, t["id"]))["status"] == "blocked"
    assert (await tasks.detail(uid, str(t["id"])))["result"] is None

    t = await running()  # a restart sends running tasks back to the queue
    await tasks.recover()
    assert (await status_of(db, t["id"]))["status"] == "ready"


def plan_text(days=2, start=2):
    from test_scheduler import DAY, fenced
    d = (datetime.now(timezone.utc) + timedelta(days=start)).date()
    return fenced({"plan": {"title": "Uji", "days": [{**DAY, "date": (d + timedelta(days=i)).isoformat()} for i in range(days)]}})


@with_db
async def test_plan_is_a_task_approved_once_with_days_and_replaced_by_a_revision(db):
    from bff import groups
    uid = "default"  # the builtin bots belong to this user
    gid = await make_group(db, uid)
    first = await groups.post(gid, "bot", plan_text(), "diana")
    assert first["plan"]["state"] == "pending" and first["plan"]["task_id"]
    plan = await tasks.detail(uid, first["plan"]["task_id"])
    assert (plan["kind"], plan["column"], plan["line"]) == ("plan", "needs_you", "Rencana menunggu persetujuan Anda")
    assert plan["primary_action"]["id"] == "approve"
    await refuses(tasks.do(uid, plan["id"], "start", {}))  # a plan is never worked on itself
    await refuses(tasks.do(uid, plan["id"], "move", {"to": "queue"}))

    second = await groups.post(gid, "bot", plan_text(3), "diana")  # a revision replaces the one still waiting
    states = [m["plan"]["state"] for m in await groups.list_messages(uid, gid, None, 50) if "plan" in m]
    assert states == ["replaced", "pending"]
    await refuses(tasks.approve_plan(uid, gid, first["id"]))  # replaced = cancelled

    a, b = await asyncio.gather(tasks.approve_plan(uid, gid, second["id"]), tasks.approve_plan(uid, gid, second["id"]))
    assert a == b and a["state"] == "approved"
    pid = second["plan"]["task_id"]
    days = await db.q("select * from tasks where parent_id = %s order by scheduled_at", pid)
    assert len(days) == 3 and all(d["status"] == "scheduled" and d["source_ref"]["targets"] == ["rian", "budi"] and d["assignee_group"] for d in days)
    parent = await tasks.detail(uid, pid)
    assert (parent["column"], parent["line"]) == ("queue", "0 dari 3 hari selesai")

    await walk(db, days[0]["id"], "ready", "running")  # the parent follows its days
    assert (await tasks.detail(uid, pid))["column"] == "running"
    for d in days:
        if d["id"] != days[0]["id"]:
            await walk(db, d["id"], "ready", "running")
        await walk(db, d["id"], "review", "done")
    done = await tasks.detail(uid, pid)
    assert (done["column"], done["outcome"], done["line"]) == ("done", "ok", "3 dari 3 hari selesai")

    third = await groups.post(gid, "bot", plan_text(2, 5), "diana")  # Batalkan on the chat card after approval stops what is left
    await tasks.approve_plan(uid, gid, third["id"])
    assert (await tasks.cancel_plan(uid, gid, third["id"]))["state"] == "cancelled"
    kids = await db.q("select status, outcome from tasks where parent_id = %s", third["plan"]["task_id"])
    assert len(kids) == 2 and all((k["status"], k["outcome"]) == ("archived", "cancelled") for k in kids)

    bad = await groups.post(gid, "bot", "Rencana: hari 1 posting.", "diana")
    assert "plan" not in bad
    await refuses(tasks.approve_plan(uid, gid, bad["id"]), 404)
    await refuses(tasks.approve_plan(f"u-{uuid.uuid4().hex[:8]}", gid, second["id"]), 404)  # another user's group


@with_db
async def test_recurring_schedule_creates_tasks_once_and_pause_delete_archive_the_unstarted(db):
    from bff import scheduler
    uid = "default"
    v = await scheduler.create(uid, {"title": "Pagi", "prompt": "halo", "days": [0, 1, 2, 3, 4, 5, 6], "time": "09:00", "bot_id": "rian"})
    sid = v["id"]

    async def rows(*statuses):
        return await db.q("select * from tasks where schedule_id = %s and status = any(%s) order by scheduled_at nulls last, created_at",
                          sid, list(statuses or tasks.MATRIX))

    first = await rows()
    assert len(first) >= 3 and all(r["source"] == "recurring" and r["status"] == "scheduled" and r["body"] == "halo" for r in first)
    assert v["next_at"] == first[0]["scheduled_at"]
    await scheduler.materialize()
    assert len(await rows()) == len(first)  # no duplicates

    await tasks.do(uid, str(first[0]["id"]), "cancel", {})  # a cancelled day does not come back
    await tasks.do(uid, str(first[1]["id"]), "start", {})  # nor does one started early
    await scheduler.materialize()
    assert len(await rows()) == len(first)

    await scheduler.pause(uid, sid)
    assert not await rows("scheduled", "ready")
    await scheduler.resume(uid, sid)
    assert len(await rows("scheduled")) == len(first) - 1  # the cancelled day stays out; the one that waited in the queue is back
    await scheduler.delete(uid, sid)
    assert not await rows("scheduled") and sid not in [x["id"] for x in await scheduler.views(uid)]
    await refuses(scheduler.delete(f"u-{uuid.uuid4().hex[:8]}", sid), 404)


# ---------- stage C: the agent's tools (tasks.agent_*, called by bridge.py) ----------

async def active_run(db, uid, bot, tid=None, **cols):
    rid = str(uuid.uuid4())
    cols = {"session_id": "web-x", **cols}
    await db.ex(f"insert into runs (id, user_id, bot_id, kind, status, task_id, {', '.join(cols)}) values (%s, %s, %s, 'chat', 'running', %s, "
                f"{', '.join('%s' for _ in cols)})", rid, uid, bot, tid, *cols.values())
    return rid


@with_db
async def test_agent_tools_follow_the_run_task_and_use_transition(db):
    uid, bot = await make_user(db)
    tid = await make(db, uid, bot)
    await force(db, tid, "running", started_at=datetime.now(timezone.utc), attempts=1)
    src = {"bot_id": bot, "run_id": await active_run(db, uid, bot, tid), "session_id": "web-x"}

    await tasks.agent_comment(uid, src, None, "Sedang riset")  # no task_id: the run's task
    assert [c["text"] for c in (await tasks.detail(uid, tid))["comments"]] == ["Sedang riset"]
    await tasks.agent_ask_user(uid, src, "Warna apa?", None)
    d = await tasks.detail(uid, tid)
    assert (d["status"], d["block_kind"], d["line"]) == ("blocked", "needs_input", "Warna apa?")

    await force(db, tid, "running", started_at=datetime.now(timezone.utc))
    await tasks.agent_request_review(uid, src, None, "Draf siap")
    d = await tasks.detail(uid, tid)
    assert (d["status"], d["block_kind"], d["result"]) == ("review", "review", "Draf siap")

    await force(db, tid, "running")
    await tasks.agent_complete(uid, src, tid, "Beres")
    assert (await status_of(db, tid))["outcome"] == "ok"
    await tasks.agent_cancel(uid, src, tid, "Atas permintaan pemilik")
    assert (await status_of(db, tid))["status"] == "archived"
    await refuses(tasks.agent_complete(uid, src, tid, "lagi"))  # an archived task cannot be finished
    await refuses(tasks.agent_cancel(uid, src, str(uuid.uuid4()), ""), 404)
    await refuses(tasks.agent_complete(uid, {"bot_id": bot}, None, "x"), 404)  # no active task and no id
    other, obot = await make_user(db)
    await refuses(tasks.agent_cancel(other, src, tid, ""), 404)  # another owner's task is not reachable

    made = await tasks.agent_create(uid, src, "Cek stok", "Hitung stok", "", "")  # for itself by default, waits in Antre
    t = await db.q1("select * from tasks where title = 'Cek stok' and user_id = %s", uid)
    assert (t["assignee_bot"], t["status"], t["source"]) == (bot, "todo", "agent") and str(t["id"]) in made
    gid = await make_group(db, uid)
    await tasks.agent_create(uid, src, "Kampanye", "", gid, "")
    assert (await db.q1("select assignee_group::text as g from tasks where title = 'Kampanye' and user_id = %s", uid))["g"] == gid
    assert "Cek stok" in await tasks.agent_list(uid, "")


@with_db
async def test_ask_user_without_a_task_makes_a_card_and_the_answer_goes_back_to_the_chat(db):
    uid, bot = await make_user(db)
    sent = []

    async def start_run(user, b, sid, text, kind, *a, **kw):
        sent.append(("chat", b, sid, text))

    async def group_send(user, gid, text, mode, *a, **kw):
        sent.append(("group", gid, text))
    real = tasks.engine.start_run, tasks.groups.send
    tasks.engine.start_run, tasks.groups.send = start_run, group_send  # with_db has no fixtures: restore by hand

    src = {"bot_id": bot, "run_id": await active_run(db, uid, bot), "session_id": "web-x"}
    await tasks.agent_ask_user(uid, src, "Mau diskon berapa persen untuk promo kaos oversize bulan ini?", None)
    await tasks.agent_ask_user(uid, src, "Mau diskon berapa persen untuk promo kaos oversize bulan ini?", None)  # asked twice: one card
    [c] = (await tasks.board(uid, None, None, None))["columns"][2]["cards"]
    assert c["title"] == "Mau diskon berapa persen untuk promo kaos oversize…" and c["assignee"]["bot"] == bot
    d = await tasks.do(uid, c["id"], "reply", {"text": "20 persen"})
    assert sent == [("chat", bot, "web-x", "20 persen")] and (d["status"], d["outcome"]) == ("done", "ok")

    gid = await make_group(db, uid)
    gsrc = {"bot_id": bot, "run_id": await active_run(db, uid, bot, group_id=gid), "group_id": gid, "session_id": "grup-x"}
    await tasks.agent_ask_user(uid, gsrc, "Pakai HEMATNOV?", None)
    [c] = (await tasks.board(uid, None, None, None))["columns"][2]["cards"]
    assert c["assignee"]["group"] == gid
    await tasks.do(uid, c["id"], "reply", {"text": "Ya"})
    assert sent[-1] == ("group", gid, "Ya")
    await refuses(tasks.agent_ask_user(uid, {"bot_id": bot}, "Halo?", None))  # no chat to answer into
    tasks.engine.start_run, tasks.groups.send = real


@with_db
async def test_run_end_keeps_the_status_a_tool_set(db):
    uid, bot = await make_user(db)
    for tool, want in ((lambda t: tasks.agent_request_review(uid, None, str(t["id"]), "Siap"), "review"),
                       (lambda t: tasks.agent_complete(uid, None, str(t["id"]), "Beres"), "done"),
                       (lambda t: tasks.agent_ask_user(uid, None, "Warna?", str(t["id"])), "blocked")):
        tid = await make(db, uid, bot)
        await force(db, tid, "running", started_at=datetime.now(timezone.utc), attempts=1)
        t = await db.q1("select * from tasks where id = %s", tid)
        await tool(t)
        await tasks.finish(t, "done", None, "ringkasan akhir agen")  # the run ends afterwards: nothing is overwritten
        row = await db.q1("select status, result, block_kind from tasks where id = %s", tid)
        assert row["status"] == want and row["result"] != "ringkasan akhir agen"
