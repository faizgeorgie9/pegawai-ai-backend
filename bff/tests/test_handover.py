import asyncio

import pytest

from bff import config, handover
from bff.errors import ApiError


@pytest.fixture(autouse=True)
def no_sheet(monkeypatch):
    async def fake_connection(user_id, kind):
        return None

    monkeypatch.setattr(handover.sheets, "connection", fake_connection)
    monkeypatch.setattr(config, "HANDOVER_OWNERS", "")


def fake_insert(monkeypatch, captured):
    async def fake_q1(sql, *params):
        captured['params'] = params
        return None

    monkeypatch.setattr(handover.db, "q1", fake_q1)


def test_ticket_id_and_acknowledgement_are_honest(monkeypatch):
    captured = {}
    fake_insert(monkeypatch, captured)
    result = asyncio.run(handover.create("default", "refund", "  Barang rusak,   minta refund  "))
    assert result["ticket_id"].startswith("HW-") and len(result["ticket_id"]) == 18
    assert result["owner"] is None and result["owner_assigned"] is False
    assert "belum ada penerima" in result["acknowledgement"].lower()
    assert "diteruskan ke" not in result["acknowledgement"].lower()
    assert "Barang rusak, minta refund" == result["summary"]
    assert result["sla"] == "1x24 jam"
    assert result["customer_contacted"] is False


def test_named_owner_changes_the_wording(monkeypatch):
    captured = {}
    fake_insert(monkeypatch, captured)
    monkeypatch.setattr(config, "HANDOVER_OWNERS", '{"refund": "Tim Finance"}')
    result = asyncio.run(handover.create("default", "REFUND", "Refund belum masuk"))
    assert result["owner"] == "Tim Finance" and result["owner_assigned"] is True
    assert "diteruskan ke Tim Finance" in result["acknowledgement"]


@pytest.mark.parametrize("category", ["", "vip", "refund; drop table"])
def test_unknown_category_is_refused(category):
    with pytest.raises(ApiError):
        asyncio.run(handover.create("default", category, "kasus"))


def test_summary_and_contact_are_validated(monkeypatch):
    fake_insert(monkeypatch, {})
    with pytest.raises(ApiError):
        asyncio.run(handover.create("default", "refund", "  "))
    with pytest.raises(ApiError):
        asyncio.run(handover.create("default", "refund", "x" * 601))
    with pytest.raises(ApiError):
        asyncio.run(handover.create("default", "refund", "barang rusak", contact="bukan nomor"))


def test_unknown_ticket_format_is_refused(monkeypatch):
    async def fake_q1(sql, *params):
        return None

    monkeypatch.setattr(handover.db, "q1", fake_q1)
    with pytest.raises(ApiError):
        asyncio.run(handover.get("default", "../../etc/passwd"))
    assert asyncio.run(handover.get("default", "HW-20261115-ABC123")) == {
        "found": False, "ticket_id": "HW-20261115-ABC123"}
