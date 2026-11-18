"""Queued group messages: 'Kirim sekarang' (steer) and the x (cancel). The tests marked `db` need TEST_DATABASE_URL (see test_scheduler.py)."""
import uuid

import pytest
from test_scheduler import make_group, with_db

from bff import engine, groups
from bff.errors import ApiError


@pytest.mark.parametrize("bad", [0, -3, "7", None, True, 1.5])
def test_message_id_must_be_a_positive_integer(bad):
    with pytest.raises(ApiError) as e:
        groups._check_message_id(bad)
    assert e.value.status == 404


async def queue_one(db, gid, text, status="queued"):
    m = await groups.post(gid, "user", text)
    await db.ex("insert into group_sends (id, group_id, message_id, status) values (%s, %s, %s, %s)", str(uuid.uuid4()), gid, m["id"], status)
    return m["id"]


@with_db
async def test_cancel_only_while_queued_and_only_for_the_owner(db):
    me, other = (f"u-{uuid.uuid4().hex[:8]}" for _ in range(2))
    gid = await make_group(db, me)
    mid, started = await queue_one(db, gid, "tunggu"), await queue_one(db, gid, "sudah jalan", "running")
    with pytest.raises(ApiError) as e:  # someone else's group is not found, nothing is deleted
        await groups.cancel_queued(other, gid, mid)
    assert e.value.status == 404
    assert await groups.cancel_queued(me, gid, mid) == {"deleted": True}
    assert not await db.q1("select 1 from group_messages where id = %s", mid)  # gone from the transcript too
    for m in (mid, started):  # already removed, or already picked up: friendly 409
        with pytest.raises(ApiError) as e:
            await groups.cancel_queued(me, gid, m)
        assert e.value.status == 409
    assert await db.q1("select 1 from group_messages where id = %s", started)


@with_db
async def test_steer_queued_reuses_the_steer_path(db):
    me = f"u-{uuid.uuid4().hex[:8]}"
    gid = await make_group(db, me)
    mid = await queue_one(db, gid, "arahkan ke teh")
    with pytest.raises(ApiError) as e:  # nothing is running: it will go out with the queue instead
        await groups.steer_queued(me, gid, mid)
    assert e.value.status == 409
    seen = []

    async def fake_steer(user_id, run_id, text):
        seen.append((run_id, text))
    orig = engine.steer
    engine.steer = fake_steer
    st = groups.SendState("s", me, run_id="run-1", bot="rian")
    groups.ACTIVE[gid] = st
    try:
        assert await groups.steer_queued(me, gid, mid) == {"steered": True}
    finally:
        engine.steer = orig
        groups.ACTIVE.pop(gid, None)
    assert seen == [("run-1", "User: arahkan ke teh")] and st.cancel_round
    cur = await db.q1("select last_message_id from group_cursors where group_id = %s and bot_id = 'rian'", gid)
    assert cur["last_message_id"] == mid
