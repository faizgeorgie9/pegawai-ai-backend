import pytest

from bff.errors import ApiError
from bff.evaluations import clean

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
