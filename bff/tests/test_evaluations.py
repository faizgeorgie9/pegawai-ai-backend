import pytest

from bff.errors import ApiError
from bff.evaluations import clean, summarize

OK = {"case_id": "TC-01", "bot_id": "rian", "verdict": "pass",
      "scores": {"accuracy": {"score": 4, "reason": ""}, "brand": {"score": None, "reason": "Tidak relevan"}}}


def test_valid_create():
    v = clean(OK)
    assert v["verdict"] == "pass" and v["scores"]["brand"]["score"] is None


@pytest.mark.parametrize("bad", [
    {**OK, "verdict": "maybe"},
    {**OK, "case_id": ""},
    {**OK, "scores": {"accuracy": {"score": 6, "reason": ""}}},
    {**OK, "scores": {"accuracy": {"score": 0, "reason": ""}}},
    {**OK, "scores": {"accuracy": {"score": True, "reason": ""}}},
    {**OK, "scores": {"accuracy": {"score": None, "reason": "  "}}},  # N/A needs a reason
    {**OK, "scores": {"bogus": {"score": 3, "reason": ""}}},
    {**OK, "reviewer": "x" * 100},
])
def test_rejects(bad):
    with pytest.raises(ApiError) as e:
        clean(bad)
    assert e.value.status == 400


def test_patch_partial():
    assert clean({"verdict": "fail"}, partial=True) == {"verdict": "fail"}
    with pytest.raises(ApiError):
        clean({}, partial=True)
    with pytest.raises(ApiError):
        clean({"verdict": "x"}, partial=True)


def run(i, bot="rian", **kw):
    return {"run_id": f"r{i}", "bot_id": bot, "session_id": f"s{i}", "output": "teks", "tokens": 10, **kw}


CMP = {"mode": "repeat", "consistency": "konsisten", "note": "mirip", "runs": [run(1), run(2)]}


def test_comparison_valid():
    c = clean({**OK, "comparison": CMP})["comparison"]
    assert c["mode"] == "repeat" and len(c["runs"]) == 2 and c["runs"][0]["meta"] == {}
    assert clean({**OK, "comparison": {**CMP, "mode": "agents", "runs": [run(1), run(2, "diana")]}})["comparison"]["mode"] == "agents"
    assert clean({"comparison": None}, partial=True) == {"comparison": None}


@pytest.mark.parametrize("bad", [
    {**CMP, "mode": "x"},
    {**CMP, "consistency": "mungkin"},
    {**CMP, "runs": [run(1)]},
    {**CMP, "runs": [run(1), run(2), run(3), run(4)]},
    {**CMP, "runs": [run(1), run(1)]},  # same run twice
    {**CMP, "runs": [run(1), run(2, "diana")]},  # repeat needs one agent
    {**CMP, "mode": "agents"},  # agents needs two different agents
    {**CMP, "runs": [run(1), run(2, tokens=-1)]},
    {**CMP, "runs": [run(1), run(2, tokens=True)]},
    {**CMP, "runs": [run(1), run(2, run_id="")]},
    {**CMP, "runs": [run(1), run(2, meta="x")]},
    {**CMP, "note": "x" * 2001},
    "bukan objek",
])
def test_comparison_rejects(bad):
    with pytest.raises(ApiError) as e:
        clean({**OK, "comparison": bad})
    assert e.value.status == 400


def test_meta_must_be_object():
    assert clean({**OK, "meta": {"model": "m"}})["meta"] == {"model": "m"}
    with pytest.raises(ApiError):
        clean({**OK, "meta": "x"})


def test_summary_uses_latest_per_case():
    def ev(case, verdict, score, t):
        return {"case_id": case, "verdict": verdict, "created_at": t, "scores": {"accuracy": {"score": score, "reason": ""}, "brand": {"score": None, "reason": "x"}}}
    s = summarize([ev("TC-01", "fail", 2, 1), ev("TC-01", "pass", 4, 2), ev("CS-01", "blocked", 5, 3)])
    assert s["counts"] == {"pass": 1, "fail": 0, "blocked": 1}
    assert s["total_evaluations"] == 3 and s["latest_at"] == 3
    assert [c["case_id"] for c in s["cases"]] == ["CS-01", "TC-01"]
    assert s["dimensions"]["accuracy"] == {"avg": 4.5, "n": 2}
    assert s["dimensions"]["brand"] == {"avg": None, "n": 0}


def test_cs_rubric_keys_accepted():
    cs = {k: {"score": 4, "reason": ""} for k in ("accuracy", "relevance", "brand", "knowledge", "anti_hallucination", "escalation")}
    assert set(clean({**OK, "scores": cs})["scores"]) == set(cs)
    s = summarize([{"case_id": "V01", "verdict": "pass", "created_at": 1, "scores": cs}])
    assert s["dimensions"]["escalation"] == {"avg": 4.0, "n": 1}


def test_summary_empty():
    s = summarize([])
    assert s["cases"] == [] and s["latest_at"] is None and s["counts"] == {"pass": 0, "fail": 0, "blocked": 0}
