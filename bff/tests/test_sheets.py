import asyncio

import pytest

from bff import config, sheets
from bff.errors import ApiError


def test_parse_url_variants():
    sid = "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789"
    assert sheets.parse_url(f"https://docs.google.com/spreadsheets/d/{sid}/edit#gid=123") == (sid, "123")
    assert sheets.parse_url(f"https://docs.google.com/spreadsheets/d/{sid}/edit?usp=sharing&gid=45") == (sid, "45")
    assert sheets.parse_url(f"  {sid} ") == (sid, None)
    with pytest.raises(ApiError):
        sheets.parse_url("https://example.com/laporan")


def test_export_url_only_adds_gid_when_known():
    assert sheets.export_url("abc", "9").endswith("format=csv&gid=9")
    assert sheets.export_url("abc", None).endswith("format=csv")


def test_csv_table_pads_short_rows_and_names_blank_headers():
    table = sheets.csv_table("SKU,Nama,Stok\nA-1,Kaos,4\nB-2\n")
    assert table["header"] == ["SKU", "Nama", "Stok"]
    assert table["rows"] == [["A-1", "Kaos", "4"], ["B-2", "", ""]]


def test_csv_table_refuses_empty_sheet():
    with pytest.raises(ApiError):
        sheets.csv_table("\n\n")


def test_columns_understand_indonesian_and_english_headers():
    header = ["Kode Produk", "Nama", "Ukuran", "Warna", "Stok", "Harga"]
    assert sheets.column(header, "sku") == 0
    assert sheets.column(header, "name") == 1
    assert sheets.column(header, "stock") == 4
    assert sheets.column(header, "price") == 5


def test_stock_rows_filters_by_any_cell_and_keeps_values():
    table = sheets.csv_table("SKU,Nama,Ukuran,Stok\nA-1,Kaos Polos,M,4\nA-1,Kaos Polos,L,0\nB-9,Denim,M,7\n")
    items = sheets.stock_rows(table, "kaos")
    assert [i["stock"] for i in items] == ["4", "0"]
    assert items[0]["sku"] == "A-1" and items[0]["name"] == "Kaos Polos"
    assert len(sheets.stock_rows(table, "kaos", limit=1)) == 1
    assert len(sheets.stock_rows(table, "")) == 3


def test_demo_stock_context_marks_values_as_sample_and_does_not_infer_zero_stock():
    table = sheets.csv_table("SKU,Nama,Ukuran,Stok\nA-1,Leather Jacket,M,4\nA-2,Leather Jacket,L,0\n")

    context = sheets.demo_stock_context(table, "Is Leather Jacket masih ada stok?")
    missing = sheets.demo_stock_context(table, "Is Raincoat available?")

    assert context is not None
    assert "sample quantities" in context
    assert "Leather Jacket" in context and "Stok: 0" in context
    assert missing is not None
    assert "No matching row" in missing
    assert "does not mean the item is out of stock" in missing


def test_demo_stock_context_is_not_added_for_non_stock_questions():
    table = sheets.csv_table("SKU,Nama,Stok\nA-1,Leather Jacket,4\n")

    assert sheets.demo_stock_context(table, "Recommend a leather jacket") is None


def test_order_row_follows_sheet_column_order():
    table = sheets.csv_table("Tanggal,Nama Produk,SKU,Jumlah,Alamat\n")
    row = sheets.order_row(table, {"SKU": "A-1", "Nama Produk": "Kaos", "Jumlah": 2, "Tanggal": "2026-11-13"})
    assert row == ["2026-11-13", "Kaos", "A-1", "2", ""]


def test_order_row_refuses_unknown_columns_and_empty_values():
    table = sheets.csv_table("SKU,Jumlah\n")
    with pytest.raises(ApiError) as e:
        sheets.order_row(table, {"sku": "A-1", "Diskon": "10%"})
    assert e.value.status == 409 and "Diskon" in e.value.message
    with pytest.raises(ApiError):
        sheets.order_row(table, {})


def test_append_order_posts_to_webhook_when_configured(monkeypatch):
    table = sheets.csv_table("Tanggal,Order ID,Nama,SKU,Qty,Total\n")
    captured = {}

    async def fake_read(_conn):
        return table

    async def fake_post(webhook, row):
        captured["webhook"], captured["row"] = webhook, row
        return {"via": "apps_script", "row": row}

    monkeypatch.setattr(sheets, "read_table", fake_read)
    monkeypatch.setattr(sheets, "_post_webhook", fake_post)
    out = asyncio.run(sheets.append_order(
        {"spreadsheet_id": "x", "webhook_url": "https://script.google.com/x/exec"},
        {"Nama": "Budi", "SKU": "A-1", "Qty": 1}))
    assert out["via"] == "apps_script"
    assert captured["webhook"].endswith("/exec")
    assert captured["row"] == ["", "", "Budi", "A-1", "1", ""]


def test_append_order_without_webhook_or_credentials_refuses(monkeypatch):
    table = sheets.csv_table("SKU,Qty\n")

    async def fake_read(_conn):
        return table

    monkeypatch.setattr(sheets, "read_table", fake_read)
    monkeypatch.setattr(config, "GOOGLE_SERVICE_ACCOUNT_FILE", "")
    monkeypatch.setattr(config, "GOOGLE_SERVICE_ACCOUNT_JSON", "")
    with pytest.raises(ApiError) as e:
        asyncio.run(sheets.append_order({"spreadsheet_id": "x", "webhook_url": None}, {"SKU": "A-1", "Qty": 1}))
    assert e.value.status == 503
