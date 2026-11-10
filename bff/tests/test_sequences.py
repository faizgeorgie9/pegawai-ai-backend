import asyncio

import pytest

from bff.engine import clean_origin, infer_origin
from bff.errors import ApiError
from bff.sequences import clean, drive

OK = {"turns": ["halo", "lanjut"], "origin": {"type": "evaluasi", "case_id": "V02"}}


def test_valid_body_is_trimmed():
    v = clean({**OK, "turns": ["  halo "], "workflow": "cs", "stage": "uji", "test_mode": True})
    assert v["turns"] == ["halo"] and v["workflow"] == "cs" and v["test_mode"] is True
    assert v["origin"] == {"type": "evaluasi", "case_id": "V02"}


@pytest.mark.parametrize("bad", [
    {**OK, "turns": []},
    {**OK, "turns": ["x"] * 11},
    {**OK, "turns": ["ok", "  "]},
    {**OK, "turns": ["ok", 5]},
    {**OK, "turns": ["x" * 20001]},
    {**OK, "turns": "halo"},
    {**OK, "workflow": "sales"},
    {**OK, "stage": ""},
    {**OK, "test_mode": "ya"},
    {**OK, "origin": None},
    {**OK, "origin": {"type": "chat"}},
    {**OK, "origin": {"type": "evaluasi"}},  # a sequence needs its case
    {**OK, "origin": {"type": "evaluasi", "case_id": 7}},
])
def test_rejects(bad):
    with pytest.raises(ApiError) as e:
        clean(bad)
    assert e.value.status == 400


def test_origin_rules():
    assert clean_origin(None) is None
    assert clean_origin({"type": "cs"}) == {"type": "cs"}
    assert clean_origin({"type": "evaluasi", "case_id": " V02 "}) == {"type": "evaluasi", "case_id": "V02"}
    for bad in ("cs", {"type": "group"}, {"type": "chat", "case_id": "x" * 41}):
        with pytest.raises(ApiError):
            clean_origin(bad)


def test_infer_origin():
    assert infer_origin("g1", "cs") == {"type": "group"}
    assert infer_origin(None, "cs") == {"type": "cs"}
    assert infer_origin(None, "marketing") == {"type": "marketing"}
    assert infer_origin(None, None) == {"type": "chat"}


class Fake:
    """Stands in for the engine and the database: runs finish with the given statuses, no Hermes calls."""

    def __init__(self, statuses, stop_after=None):
        self.statuses, self.stop_after = statuses, stop_after
        self.started, self.saved, self.flag = [], [], False

    async def start(self, i, text):
        self.started.append((i, text))
        return {"id": f"run{i}"}

    async def wait(self, rid):
        i = int(rid[3:])
        if self.stop_after == i:
            self.flag = True
        st = self.statuses[i]
        return {"status": st, "error": "boom" if st == "failed" else None}

    async def save(self, **f):
        self.saved.append(f)

    def last(self, key):
        return [f[key] for f in self.saved if key in f][-1]

    def go(self, turns):
        asyncio.run(drive(turns, self.start, self.wait, self.save, lambda: self.flag))


def test_all_turns_run_in_order_and_complete():
    f = Fake(["completed"] * 3)
    f.go(["a", "b", "c"])
    assert f.started == [(0, "a"), (1, "b"), (2, "c")]
    assert f.last("status") == "completed" and f.last("current_turn") == 3
    assert f.last("run_ids") == ["run0", "run1", "run2"]


def test_stops_at_first_failed_turn():
    f = Fake(["completed", "failed", "completed"])
    f.go(["a", "b", "c"])
    assert len(f.started) == 2  # turn 3 never starts
    assert f.last("status") == "failed" and "Giliran 2 dari 3" in f.last("error") and "boom" in f.last("error")


def test_cancelled_turn_is_stopped_not_failed():
    f = Fake(["cancelled", "completed"])
    f.go(["a", "b"])
    assert len(f.started) == 1 and f.last("status") == "stopped"


def test_stop_request_between_turns():
    f = Fake(["completed"] * 3, stop_after=0)
    f.go(["a", "b", "c"])
    assert len(f.started) == 1
    assert f.last("status") == "stopped" and "sebelum giliran 2 dari 3" in f.last("error")


def test_start_error_fails_with_reason():
    async def boom(i, text):
        raise ApiError(402, "Kuota habis")
    f = Fake([])
    asyncio.run(drive(["a"], boom, f.wait, f.save, lambda: False))
    assert f.last("status") == "failed" and "Kuota habis" in f.last("error")


def test_unexpected_error_never_leaves_running():
    async def boom(i, text):
        raise KeyError("x")
    f = Fake([])
    asyncio.run(drive(["a"], boom, f.wait, f.save, lambda: False))
    assert f.last("status") == "failed" and "KeyError" in f.last("error")
