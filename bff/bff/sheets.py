"""Google Drive spreadsheets as the live stock and order store.

A connection is a spreadsheet URL per kind ("stock", "orders"). Reads work on a
public "anyone with the link" sheet through its CSV export. Writes (appending an
order) use either an Apps Script web app URL (no Google Cloud needed) or a
service account shared on the sheet; with neither the API says so instead of
pretending an order was saved.
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

from . import config, db
from .errors import ApiError

SCOPE = "https://www.googleapis.com/auth/spreadsheets"
KINDS = ("stock", "orders", "handover")
API = "https://sheets.googleapis.com/v4/spreadsheets"
EXPORT = "https://docs.google.com/spreadsheets/d/{sid}/export?format=csv"
MAX_ROWS = 5_000
_STOCK_INTENT = re.compile(r"\b(stok\w*|stock\w*|tersedia|availability|available|habis)\b|masih\s+ada", re.I)
_STOCK_STOP = {
    "stok", "stock", "tersedia", "availability", "available", "habis", "masih", "ada",
    "ukuran", "size", "warna", "color", "colour", "berapa", "produk", "product",
}

_ALIASES = {
    "sku": {"sku", "kode", "kode produk", "kode barang", "id produk", "product code", "item code"},
    "order_id": {"order id", "id pesanan", "nomor pesanan", "no pesanan", "order number"},
    "name": {"nama", "nama produk", "product", "product name", "item", "barang"},
    "stock": {"stok", "stock", "qty", "quantity", "jumlah", "sisa", "available"},
    "price": {"harga", "price", "harga jual", "price idr"},
    "size": {"ukuran", "size"},
    "color": {"warna", "color", "colour"},
}


def parse_url(value: str) -> tuple[str, str | None]:
    """(spreadsheet_id, gid) from a Google Sheets URL or a bare id."""
    text = (value or "").strip()
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]{20,})", text)
    if match:
        gid = None
        parsed = parse_qs(urlparse(text).query)
        if parsed.get("gid"):
            gid = parsed["gid"][0]
        elif "#gid=" in text:
            gid = text.split("#gid=", 1)[1].split("&", 1)[0]
        return match.group(1), gid
    if re.fullmatch(r"[a-zA-Z0-9_-]{20,}", text):
        return text, None
    raise ApiError(400, "Tautan spreadsheet tidak dikenali. Tempel tautan Google Sheets lengkap.")


def export_url(spreadsheet_id: str, gid: str | None) -> str:
    url = EXPORT.format(sid=spreadsheet_id)
    return f"{url}&gid={gid}" if gid else url


def csv_table(text: str) -> dict[str, Any]:
    """First row is the header; short rows are padded and blank trailing rows dropped."""
    rows = [[cell.strip() for cell in row] for row in csv.reader(io.StringIO(text))]
    rows = [row for row in rows if any(row)]
    if not rows:
        raise ApiError(422, "Spreadsheet kosong: tidak ada baris judul.")
    header = [cell or f"kolom_{i + 1}" for i, cell in enumerate(rows[0])]
    body = [(row + [""] * len(header))[: len(header)] for row in rows[1:]]
    return {"header": header, "rows": body[:MAX_ROWS]}


def column(header: list[str], field: str) -> int | None:
    names = _ALIASES[field]
    for index, label in enumerate(header):
        if re.sub(r"\s+", " ", label.strip().lower()) in names:
            return index
    return None


def stock_rows(table: dict[str, Any], query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Rows whose SKU, name, size or colour contains the query (case-insensitive)."""
    header = table["header"]
    sku, name = column(header, "sku"), column(header, "name")
    stock, price = column(header, "stock"), column(header, "price")
    needle = query.strip().lower()
    out = []
    for row in table["rows"]:
        haystack = " | ".join(row).lower()
        if needle and needle not in haystack:
            continue
        item = {"row": dict(zip(header, row))}
        if sku is not None:
            item["sku"] = row[sku]
        if name is not None:
            item["name"] = row[name]
        if stock is not None:
            item["stock"] = row[stock]
        if price is not None:
            item["price"] = row[price]
        out.append(item)
        if len(out) >= limit:
            break
    return out


def wants_stock_lookup(query: str) -> bool:
    return bool(_STOCK_INTENT.search(query))


def demo_stock_context(table: dict[str, Any], query: str) -> str | None:
    """Return matched demo-sheet rows as explicitly simulated prompt context."""
    if not wants_stock_lookup(query):
        return None

    terms = [term for term in re.findall(r"[a-z0-9]+", query.lower())
             if len(term) >= 3 and term not in _STOCK_STOP]
    matches: dict[tuple[str, ...], tuple[int, dict[str, Any]]] = {}
    for term in terms:
        for item in stock_rows(table, term, limit=MAX_ROWS):
            row = item["row"]
            key = tuple(row.values())
            text = " ".join(row.values()).lower()
            score = sum(1 for candidate in terms if candidate in text)
            if score:
                previous = matches.get(key)
                if previous is None or score > previous[0]:
                    matches[key] = (score, row)

    if not matches:
        return (
            "## Demo stock lookup (simulated)\n"
            "No matching row was found in the connected demo stock sheet. This does not mean the item is out of stock; "
            "do not claim availability or zero stock."
        )

    rows = sorted(matches.values(), key=lambda item: (-item[0], tuple(item[1].values())))[:5]
    lines = [
        "## Demo stock lookup (simulated)",
        "These are sample quantities from the connected demo spreadsheet, not verified business inventory. "
        "Describe them only as test data; a missing row does not mean zero stock.",
    ]
    for _, row in rows:
        lines.append("- " + " | ".join(f"{key}: {value}" for key, value in row.items() if value))
    return "\n".join(lines)


def order_row(table: dict[str, Any], values: dict[str, Any]) -> list[str]:
    """One append row in the sheet's own column order; unknown keys are refused."""
    header = table["header"]
    known = {}
    for index, label in enumerate(header):
        known.setdefault(re.sub(r"\s+", " ", label.strip().lower()), index)
    unknown = [k for k in values if k.strip().lower() not in known]
    if unknown:
        raise ApiError(409, f"Kolom tidak ada di spreadsheet: {', '.join(unknown)}. Kolom tersedia: {', '.join(header)}.")
    row = [""] * len(header)
    for key, value in values.items():
        row[known[key.strip().lower()]] = "" if value is None else str(value)
    if not any(cell.strip() for cell in row):
        raise ApiError(400, "Pesanan kosong.")
    return row


def credentials():
    from google.oauth2 import service_account

    raw = (config.GOOGLE_SERVICE_ACCOUNT_JSON or "").strip()
    if raw:
        try:
            return service_account.Credentials.from_service_account_info(json.loads(raw), scopes=[SCOPE])
        except (ValueError, KeyError) as exc:
            raise ApiError(503, "Kredensial Google service account tidak valid.") from exc
    path = (config.GOOGLE_SERVICE_ACCOUNT_FILE or "").strip()
    if path:
        try:
            return service_account.Credentials.from_service_account_file(path, scopes=[SCOPE])
        except (OSError, ValueError) as exc:
            raise ApiError(503, "Berkas kredensial Google service account tidak terbaca.") from exc
    return None


def has_credentials() -> bool:
    return bool((config.GOOGLE_SERVICE_ACCOUNT_JSON or "").strip() or (config.GOOGLE_SERVICE_ACCOUNT_FILE or "").strip())


async def write_ready(user_id: str) -> bool:
    """True when an order can actually be appended: service account or a web app URL."""
    if has_credentials():
        return True
    row = await db.q1(
        "select webhook_url from data_connections where user_id = %s and kind = 'orders'", user_id)
    return bool(row and (row.get("webhook_url") or "").strip())


async def _token() -> str:
    creds = credentials()
    if creds is None:
        raise ApiError(503, "Tulis pesanan butuh kredensial Google service account yang dibagikan ke spreadsheet.")
    from google.auth.transport.requests import Request

    try:
        await asyncio.to_thread(creds.refresh, Request())
    except Exception as exc:
        raise ApiError(502, "Google menolak kredensial service account.") from exc
    return creds.token


async def _api(method: str, path: str, *, params: dict[str, str] | None = None,
               body: dict[str, Any] | None = None) -> dict[str, Any]:
    token = await _token()
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.request(
                method, f"{API}/{path}", params=params, json=body,
                headers={"Authorization": f"Bearer {token}"})
    except httpx.HTTPError as exc:
        raise ApiError(502, "Google Sheets tidak bisa dihubungi.") from exc
    if response.status_code in (401, 403):
        raise ApiError(403, "Service account belum diberi akses ke spreadsheet ini. Bagikan sheet ke alamat service account.")
    if response.status_code >= 400:
        raise ApiError(502, f"Google Sheets menolak permintaan (HTTP {response.status_code}).")
    return response.json()


async def _tabs(spreadsheet_id: str) -> list[dict[str, Any]]:
    data = await _api("GET", f"{spreadsheet_id}", params={"fields": "sheets.properties"})
    return [sheet.get("properties", {}) for sheet in data.get("sheets", [])]


async def _tab_title(connection: dict[str, Any]) -> str:
    if connection.get("tab"):
        return connection["tab"]
    try:
        tabs = await _tabs(connection["spreadsheet_id"])
    except ApiError:
        raise
    gid = str(connection.get("gid") or "")
    for tab in tabs:
        if gid and str(tab.get("sheetId")) == gid:
            return tab.get("title") or "Sheet1"
    return (tabs[0].get("title") if tabs else None) or "Sheet1"


async def _read_public(connection: dict[str, Any]) -> dict[str, Any]:
    url = export_url(connection["spreadsheet_id"], connection.get("gid"))
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            response = await client.get(url)
    except httpx.HTTPError as exc:
        raise ApiError(502, "Spreadsheet tidak bisa diambil dari Google.") from exc
    if response.status_code == 404:
        raise ApiError(404, "Spreadsheet tidak ditemukan atau belum dibagikan.")
    if response.status_code in (401, 403) or "text/html" in response.headers.get("content-type", ""):
        raise ApiError(403, "Spreadsheet tidak bisa dibaca publik. Bagikan sebagai 'siapa saja yang punya tautan' "
                            "atau pasang kredensial service account.")
    if response.status_code >= 400:
        raise ApiError(502, f"Google menolak permintaan (HTTP {response.status_code}).")
    return csv_table(response.text)


async def read_table(connection: dict[str, Any]) -> dict[str, Any]:
    """Header and rows from the connected sheet (public CSV or Sheets API)."""
    if has_credentials():
        title = await _tab_title(connection)
        quoted = "'" + title.replace("'", "''") + "'"
        data = await _api("GET", f"{connection['spreadsheet_id']}/values/{quoted}!A1:Z{MAX_ROWS}",
                          params={"majorDimension": "ROWS"})
        values = data.get("values") or []
        if not values:
            raise ApiError(422, "Spreadsheet kosong: tidak ada baris judul.")
        header = [str(c).strip() or f"kolom_{i + 1}" for i, c in enumerate(values[0])]
        rows = [[str(c) for c in (row + [""] * len(header))[: len(header)]] for row in values[1:]]
        return {"header": header, "rows": rows, "tab": title}
    table = await _read_public(connection)
    table["tab"] = None
    return table


async def _post_webhook(webhook: str, row: list[str]) -> dict[str, Any]:
    """Send one row to an Apps Script web app. Google answers 302 to a result URL."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(webhook, json={"row": row}, follow_redirects=False)
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("location")
                if not location:
                    raise ApiError(502, "Aplikasi web spreadsheet tidak mengembalikan tujuan.")
                response = await client.get(location, follow_redirects=True)
    except httpx.HTTPError as exc:
        raise ApiError(502, "Aplikasi web spreadsheet pesanan tidak bisa dihubungi.") from exc
    if response.status_code >= 400:
        raise ApiError(502, f"Aplikasi web spreadsheet menolak permintaan (HTTP {response.status_code}).")
    try:
        data = response.json()
    except ValueError as exc:
        raise ApiError(502, "Balasan aplikasi web spreadsheet tidak dikenali.") from exc
    if not data.get("ok"):
        raise ApiError(502, f"Aplikasi web spreadsheet gagal menulis: {data.get('error') or 'tidak diketahui'}.")
    return {"tab": None, "updated_rows": 1, "row": row, "via": "apps_script"}


async def append_row_to_webhook(webhook: str, values: list[str]) -> dict[str, Any]:
    """Append one prepared row through an Apps Script web app."""
    return await _post_webhook(webhook, values)


async def append_order(connection: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    table = await read_table(connection)
    row = order_row(table, values)
    webhook = (connection.get("webhook_url") or "").strip()
    if webhook:
        return await _post_webhook(webhook, row)
    title = table.get("tab") or await _tab_title(connection)
    quoted = "'" + title.replace("'", "''") + "'"
    data = await _api("POST", f"{connection['spreadsheet_id']}/values/{quoted}!A1:append",
                      params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"},
                      body={"values": [row]})
    updates = data.get("updates", {})
    return {"tab": title, "updated_range": updates.get("updatedRange"), "updated_rows": updates.get("updatedRows", 0),
            "row": row}


async def connection(user_id: str, kind: str) -> dict[str, Any] | None:
    if kind not in KINDS:
        raise ApiError(404, "Jenis koneksi tidak dikenal.")
    return await db.q1(
        "select id, kind, url, spreadsheet_id, gid, tab, header, status, detail, webhook_url, "
        "created_at, updated_at from data_connections where user_id = %s and kind = %s", user_id, kind)


async def connections(user_id: str) -> list[dict[str, Any]]:
    return await db.q(
        "select id, kind, url, spreadsheet_id, gid, tab, header, status, detail, webhook_url, "
        "created_at, updated_at from data_connections where user_id = %s order by kind", user_id)


async def save(user_id: str, kind: str, url: str, tab: str | None, webhook_url: str | None = None) -> dict[str, Any]:
    if kind not in KINDS:
        raise ApiError(404, "Jenis koneksi tidak dikenal.")
    spreadsheet_id, gid = parse_url(url)
    row = await db.q1(
        "insert into data_connections (user_id, kind, url, spreadsheet_id, gid, tab, webhook_url, status, detail) "
        "values (%s, %s, %s, %s, %s, %s, %s, 'unverified', null) "
        "on conflict (user_id, kind) do update set url = excluded.url, spreadsheet_id = excluded.spreadsheet_id, "
        "gid = excluded.gid, tab = excluded.tab, webhook_url = excluded.webhook_url, status = 'unverified', "
        "detail = null, header = null, updated_at = now() "
        "returning id, kind, url, spreadsheet_id, gid, tab, header, status, detail, webhook_url, created_at, updated_at",
        user_id, kind, url.strip(), spreadsheet_id, gid, (tab or "").strip() or None,
        (webhook_url or "").strip() or None)
    return row or {}


async def verify(user_id: str, kind: str) -> dict[str, Any]:
    conn = await connection(user_id, kind)
    if not conn:
        raise ApiError(404, "Hubungkan spreadsheet dulu.")
    try:
        table = await read_table(conn)
    except ApiError as exc:
        await db.ex("update data_connections set status = 'error', detail = %s, updated_at = now() "
                    "where id = %s", exc.message, conn["id"])
        return {**conn, "status": "error", "detail": exc.message}
    detail = f"{len(table['rows'])} baris, {len(table['header'])} kolom"
    row = await db.q1(
        "update data_connections set status = 'verified', detail = %s, header = %s, updated_at = now() "
        "where id = %s returning id, kind, url, spreadsheet_id, gid, tab, header, status, detail, webhook_url, "
        "created_at, updated_at",
        detail, json.dumps(table["header"]), conn["id"])
    return {**(row or conn), "sample": table["rows"][:3]}


async def remove(user_id: str, kind: str) -> None:
    await db.ex("delete from data_connections where user_id = %s and kind = %s", user_id, kind)
