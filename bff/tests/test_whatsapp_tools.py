import asyncio

import pytest

from bff import main, sheets
from bff.errors import ApiError


def test_order_id_column_is_recognized():
    assert sheets.column(["Tanggal", "Order ID", "Nama", "SKU", "Qty", "Total"], "order_id") == 1


def test_test_order_readback_is_restricted_to_test_wa_ids(monkeypatch):
    async def fake_connection(user_id, kind):
        assert user_id == "default" and kind == "orders"
        return {"kind": "orders"}

    async def fake_read(_connection):
        return {"header": ["Tanggal", "Order ID", "Nama", "SKU", "Qty", "Total"],
                "rows": [["2026-11-13", "TEST-WA-20261113-ABC123", "SIMULASI", "SKU-1", "1", "100"]]}

    monkeypatch.setattr(sheets, "connection", fake_connection)
    monkeypatch.setattr(sheets, "read_table", fake_read)

    found = asyncio.run(main.verify_test_order("TEST-WA-20261113-ABC123"))
    missing = asyncio.run(main.verify_test_order("TEST-WA-20261113-FFFF00"))
    assert found["found"] is True and found["data_kind"] == "simulated_test_order"
    assert found["row"]["SKU"] == "SKU-1"
    assert missing == {"found": False, "order_id": "TEST-WA-20261113-FFFF00"}
    with pytest.raises(ApiError):
        asyncio.run(main.verify_test_order("REAL-CUSTOMER-123"))
