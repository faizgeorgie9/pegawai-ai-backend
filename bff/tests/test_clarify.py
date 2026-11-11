import asyncio

import pytest

from bff import engine
from bff.errors import ApiError


class FakeResp:
    def __init__(self, code=200):
        self.status_code = code


def _live():
    lv = engine.Live("r1", "rian", "hrun1", "chat", None, "s1")
    engine.LIVE["r1"] = lv
    return lv


@pytest.fixture
def setup(monkeypatch):
    sent, published = [], []

    async def noop(*a, **k):
        return None

    async def owned(uid, rid):
        return {"status": "running"}, engine.LIVE[rid]

    monkeypatch.setattr(engine.db, "ex", noop)
    monkeypatch.setattr(engine, "_owned_active", owned)
    monkeypatch.setattr(engine.hub, "publish", lambda key, t, d: published.append((t, d)))

    async def call(bot, method, path, json_body=None):
        sent.append((path, json_body))
        return FakeResp()

    monkeypatch.setattr(engine.hermes, "call", call)
    yield sent, published
    engine.LIVE.pop("r1", None)


def test_request_is_kept_and_answer_uses_hermes_identity(setup):
    sent, published = setup
    lv = _live()
    ev = {"event": "clarify.request", "kind": "clarify", "prompt_id": "c-9", "execution_generation": 3,
          "question": "Warna favorit?", "choices": ["Biru", "Merah"], "multi_select": False}
    asyncio.run(engine._handle(lv, 5, ev))
    assert published == [("clarify", {"request_id": "c-9", "execution_generation": 3,
                                      "question": "Warna favorit?", "choices": ["Biru", "Merah"]})]
    asyncio.run(engine.clarify("u", "r1", "  Biru "))
    # Hermes accepts exactly these three fields (api_server_authority_runs.py respond_run)
    assert sent == [("/v1/runs/hrun1/clarify", {"request_id": "c-9", "execution_generation": 3, "answer": "Biru"})]
    assert lv.clarify is None and published[-1][0] == "clarify_done"


def test_answer_without_pending_question_or_blank_is_refused(setup):
    _live()
    for bad in ("", "   ", None, 5):
        with pytest.raises(ApiError) as e:
            asyncio.run(engine.clarify("u", "r1", bad))
        assert e.value.status == 400
    with pytest.raises(ApiError) as e:
        asyncio.run(engine.clarify("u", "r1", "Biru"))
    assert e.value.status == 409


def test_approval_uses_hermes_identity(setup):
    sent, published = setup
    lv = _live()
    with pytest.raises(ApiError) as e:  # nothing is waiting: nothing is forwarded
        asyncio.run(engine.approval("u", "r1", "once"))
    assert e.value.status == 409 and sent == []
    ev = {"event": "approval.request", "prompt_id": "a-7", "execution_generation": 2, "description": "rm -rf x",
          "choices": ["once", "deny"]}
    asyncio.run(engine._handle(lv, 4, ev))
    assert published[-1][1]["request_id"] == "a-7"  # browser-facing event keeps its name
    asyncio.run(engine.approval("u", "r1", "once"))
    assert sent == [("/v1/runs/hrun1/approval", {"request_id": "a-7", "execution_generation": 2, "choice": "once"})]
    assert lv.approval is None
