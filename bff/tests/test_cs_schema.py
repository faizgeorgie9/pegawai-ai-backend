import json

import pytest

from bff.cs_schema import extract_json, validate_cs

NO_ESC = {"recommended": False, "reason": None, "handoff_status": "recommendation_only"}
REFUND_ESC = {"recommended": True, "reason": "refund", "handoff_status": "recommendation_only"}


def sample(**over):
    d = {"primary_intent": "PRODUCT_AVAILABILITY", "secondary_intents": ["PRODUCT_INFO", "SIZE_FIT"],
         "classification_confidence": 0.9, "priority": "P2", "customer_reply_draft": "Halo, harga yang diamati Rp 239.900.",
         "ticket_summary": {"issue": "Harga dan stok", "customer_reported_facts": ["ukuran M"],
                            "publicly_verified_facts": ["IDR 239.900"], "unknowns": ["stok"],
                            "customer_provided_references": [], "requested_outcome": "info", "context_retained": []},
         "knowledge_refs": [{"knowledge_id": "CB-PRODUCT-001", "source_ids": ["SRC-01"], "source_url": "https://colorbox.co.id/",
                             "accessed_date": "2026-11-07", "used_for": "harga"}],
         "clarifying_question": None,
         "escalation": {"recommended": True, "reason": "stok butuh pengecekan langsung", "handoff_status": "recommendation_only"},
         "human_review_required": True, "simulation": {"is_simulated": False, "scenario_ids": []}}
    d.update(over)
    return d


def check(d):
    return validate_cs(json.dumps(d))


def test_valid_sample_passes_and_is_returned_as_dict():
    obj, v = check(sample())
    assert v == {"status": "valid", "errors": []} and obj["priority"] == "P2"
    assert obj["escalation"]["handoff_status"] == "recommendation_only"


def test_fenced_and_wrapped_json_is_extracted():
    raw = json.dumps(sample())
    assert extract_json("```json\n" + raw + "\n```")["priority"] == "P2"
    assert extract_json("Ini jawabannya:\n" + raw + "\nSemoga membantu")["priority"] == "P2"
    assert validate_cs("bukan json")[1]["status"] == "invalid"
    assert validate_cs("[1, 2]")[0] is None


@pytest.mark.parametrize("bad", [
    {"classification_confidence": 1.5},
    {"classification_confidence": -0.1},
    {"priority": "P4"},
    {"primary_intent": "BUKAN_INTENT"},
    {"human_review_required": False},
    {"escalation": {"recommended": True, "reason": "x", "handoff_status": "escalated"}},
    {"primary_intent": "RETURN_REFUND", "priority": "P2", "escalation": REFUND_ESC},  # refund must be P1
    {"primary_intent": "RETURN_REFUND", "priority": "P1", "escalation": NO_ESC},
    {"secondary_intents": ["RETURN_REFUND"], "priority": "P2", "escalation": NO_ESC},
    {"priority": "P1", "escalation": NO_ESC},
    {"escalation": {"recommended": True, "reason": "  ", "handoff_status": "recommendation_only"}},
])
def test_invariant_violations_are_rejected(bad):
    obj, v = check(sample(**bad))
    assert obj is None and v["status"] == "invalid" and v["errors"]


def test_missing_required_key_is_rejected():
    d = sample()
    del d["ticket_summary"]
    assert check(d)[1]["status"] == "invalid"


def test_refund_p1_with_escalation_is_valid():
    obj, v = check(sample(primary_intent="RETURN_REFUND", priority="P1", escalation=REFUND_ESC))
    assert v["status"] == "valid" and obj["primary_intent"] == "RETURN_REFUND"
