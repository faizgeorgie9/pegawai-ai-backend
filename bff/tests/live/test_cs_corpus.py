"""Live CS corpus V01-V06 through a running BFF (port 8090) and Hermes gateway. Costs tokens: skipped by default.
Run: LIVE_EMAIL=... LIVE_PASSWORD=... uv run pytest -m live
(one case: uv run pytest -m live -k V01)"""
import json
import os
import time

import httpx
import pytest

from bff import knowledge

pytestmark = pytest.mark.live
BASE = "http://127.0.0.1:8090/api"
CASES = json.loads((knowledge.CS_DIR / "COLORBOX_CS_Test_Corpus_v2.json").read_text(encoding="utf-8"))["cases"]


@pytest.fixture(scope="module")
def headers() -> dict[str, str]:
    """The live BFF only accepts a real user session now; credentials come from the environment, never the repo."""
    email, password = os.environ.get("LIVE_EMAIL"), os.environ.get("LIVE_PASSWORD")
    if not email or not password:
        pytest.skip("set LIVE_EMAIL and LIVE_PASSWORD to run the live corpus")
    r = httpx.post(f"{BASE}/auth/login", json={"email": email, "password": password}, timeout=15)
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['token']}"}


def run_turn(c: httpx.Client, text: str, session_id: str | None, test_mode: bool) -> dict:
    body = {"input": text, "workflow": "cs", "test_mode": test_mode, **({"session_id": session_id} if session_id else {})}
    r = c.post("/bots/siti/runs", json=body)
    assert r.status_code == 202, r.text
    rid, sid = r.json()["run"]["id"], r.json()["session_id"]
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        d = c.get(f"/runs/{rid}").json()
        if d["status"] not in ("queued", "running"):
            return {**d, "session_id": sid}
        time.sleep(3)
    pytest.fail("run tidak selesai dalam 300 detik")


@pytest.mark.parametrize("case", CASES, ids=[c["test_id"][-3:] for c in CASES])
def test_case(case, headers):
    with httpx.Client(base_url=BASE, headers=headers, timeout=30) as c:
        sid = None
        for turn in case["turns"]:
            exp = turn["expected"]
            d = run_turn(c, turn["customer_input"], sid, bool(turn["simulation_ids"]))
            sid = d["session_id"]
            assert d["status"] == "completed", d.get("error")
            meta = d["meta"]
            assert meta["validation"]["status"] in ("valid", "repaired"), meta["validation"]
            s = meta["structured"]
            assert s["primary_intent"] in exp["accepted_primary_intents"], (turn["turn_id"], s["primary_intent"])
            assert s["priority"] == exp["priority"]
            assert s["escalation"]["recommended"] == exp["escalation_recommended"]
