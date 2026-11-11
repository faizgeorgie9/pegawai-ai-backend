"""Live CS corpus V01-V06 through a running BFF (port 8090) and Hermes gateway. Costs tokens: skipped by default.
Run: uv run pytest -m live            (one case: uv run pytest -m live -k V01)"""
import json
import time

import httpx
import pytest

from bff import config, knowledge

pytestmark = pytest.mark.live
BASE = "http://127.0.0.1:8090/api"
CASES = json.loads((knowledge.CS_DIR / "COLORBOX_CS_Test_Corpus_v2.json").read_text(encoding="utf-8"))["cases"]


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
def test_case(case):
    with httpx.Client(base_url=BASE, headers={"X-Pegawai-AI-Key": config.BFF_API_KEY}, timeout=30) as c:
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
