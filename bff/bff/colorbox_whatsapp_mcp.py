"""Narrow, test-only Colorbox data tools for the Siti WhatsApp profile.

The server calls the existing BFF over loopback. It reads BFF_API_KEY from the
project's bff/.env file in-process; the key is never returned to an MCP caller.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import httpx
from dotenv import dotenv_values
from mcp.server.fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV = dotenv_values(PROJECT_ROOT / "bff" / ".env")
API_KEY = ENV.get("BFF_API_KEY", "")
BFF_URL = "http://127.0.0.1:8090"
STOCK_URL = "https://docs.google.com/spreadsheets/d/1q5qri13EvnWywYvXwEdHElhOreOazfXvYDID-gm8FfI/edit?usp=sharing"
mcp = FastMCP("Colorbox CS demo tools")


def _request(method: str, path: str, **kwargs) -> dict:
    if not API_KEY:
        raise RuntimeError("BFF_API_KEY tidak tersedia di konfigurasi proyek.")
    try:
        response = httpx.request(method, BFF_URL + path, headers={"x-pegawai-ai-key": API_KEY},
                                 timeout=20, **kwargs)
    except httpx.HTTPError as exc:
        raise RuntimeError("BFF lokal tidak dapat dijangkau. Pastikan backend proyek berjalan.") from exc
    if response.status_code >= 400:
        try:
            message = response.json().get("error", "permintaan gagal")
        except ValueError:
            message = "permintaan gagal"
        raise RuntimeError(f"BFF menolak permintaan (HTTP {response.status_code}): {message}")
    return response.json()


@mcp.tool()
def find_colorbox_products(query: str, limit: int = 5) -> str:
    """Search the dated Colorbox catalog and return product names, prices, options, dates, and source links."""
    if not query.strip():
        return json.dumps({"error": "Kata kunci produk wajib diisi."}, ensure_ascii=False)
    result = _request("GET", "/api/products/search", params={"q": query, "limit": max(1, min(limit, 10))})
    return json.dumps({"source": "SRC-02", "count": result["count"], "items": result["data"]},
                      ensure_ascii=False)


@mcp.tool()
def lookup_demo_stock(query: str) -> str:
    """Search the connected sample stock sheet. Results are simulated, not live Colorbox inventory."""
    if not query.strip():
        return json.dumps({"error": "Kata kunci SKU atau produk wajib diisi."}, ensure_ascii=False)
    result = _request("GET", "/api/data/stock", params={"q": query})
    return json.dumps({"data_kind": "simulated_sample_stock", "live_inventory_verified": False,
                       "sheet_url": STOCK_URL, "row_count": result["rows"], "items": result["items"]},
                      ensure_ascii=False)


@mcp.tool()
def append_simulated_test_order(sku: str, quantity: int, scenario_id: str = "WA-ORDER-01") -> str:
    """Append a clearly labeled, non-fulfillable WhatsApp test row; never use for a customer order."""
    if scenario_id != "WA-ORDER-01":
        return json.dumps({"error": "Tool ini hanya untuk skenario uji WA-ORDER-01."}, ensure_ascii=False)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,24}", sku.strip()):
        return json.dumps({"error": "SKU tidak valid."}, ensure_ascii=False)
    if not 1 <= quantity <= 5:
        return json.dumps({"error": "Jumlah uji harus 1 sampai 5."}, ensure_ascii=False)
    stock_result = _request("GET", "/api/data/stock", params={"q": sku.strip()})
    exact = [item for item in stock_result["items"] if item.get("sku") == sku.strip()]
    if len(exact) != 1:
        return json.dumps({"created": False, "reason": "SKU tidak ditemukan secara persis di lembar stok contoh.",
                           "data_kind": "simulated_sample_stock"}, ensure_ascii=False)
    item = exact[0]
    try:
        price, available = int(str(item["price"])), int(str(item["stock"]))
    except (KeyError, ValueError):
        return json.dumps({"created": False, "reason": "Harga atau jumlah stok contoh tidak valid."}, ensure_ascii=False)
    if available < quantity:
        return json.dumps({"created": False, "reason": "Jumlah uji melebihi stok yang tertulis di lembar contoh.",
                           "data_kind": "simulated_sample_stock"}, ensure_ascii=False)
    connections = _request("GET", "/api/data/connections")
    if not connections.get("write_ready"):
        return json.dumps({"created": False, "reason": "Lembar pesanan belum siap ditulis."}, ensure_ascii=False)
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    order_id = f"TEST-WA-{now:%Y%m%d}-{uuid4().hex[:6].upper()}"
    values = {"Tanggal": now.strftime("%Y-%m-%d"), "Order ID": order_id,
              "Nama": "SIMULASI WHATSAPP TEST - DO NOT FULFILL", "SKU": sku.strip(),
              "Qty": quantity, "Total": price * quantity}
    write = _request("POST", "/api/data/orders", json={"values": values})
    verified = _request("GET", f"/api/data/orders/test/{order_id}")
    return json.dumps({"created": bool(write.get("updated_rows")), "verified_readback": verified.get("found", False),
                       "order_id": order_id, "data_kind": "simulated_test_order", "fulfillment_allowed": False,
                       "row": verified.get("row"), "write_via": write.get("via")}, ensure_ascii=False)


@mcp.tool()
def check_order_status(order_id: str) -> str:
    """Look up one order's status from the orders sheet. Returns the stage verbatim from the sheet.

    ``status_available`` is false when the row has no status value: then never state a status.
    """
    cleaned = (order_id or "").strip()
    if not cleaned:
        return json.dumps({"status_available": False, "reason": "Nomor pesanan kosong."}, ensure_ascii=False)
    record = _request("GET", f"/api/data/orders/lookup/{cleaned}")
    if not record.get("found"):
        return json.dumps({"status_available": False, "order_found": False, "order_id": cleaned,
                           "reason": "Nomor pesanan tidak ditemukan di lembar pesanan.",
                           }, ensure_ascii=False)
    stage = record.get("status")
    if not stage:
        return json.dumps({"status_available": False, "order_found": True, "order_id": cleaned,
                           "reason": "Pesanan ditemukan, tetapi kolom statusnya masih kosong.",
                           "date": record.get("date", "")}, ensure_ascii=False)
    return json.dumps({
        "status_available": True,
        "order_found": True,
        "order_id": cleaned,
        "status": stage,
        "status_as_written": record.get("status_raw", ""),
        "date": record.get("date", ""),
        "can_cancel": stage in {"baru", "diproses"},
        "reason": ("Status menunjukkan pesanan belum diserahkan ke ekspedisi, jadi pembatalan masih dapat diajukan untuk ditinjau."
                   if stage in {"baru", "diproses"} else
                   "Status menunjukkan pesanan sudah melewati tahap penyerahan ke ekspedisi, jadi pembatalan tidak dapat diajukan; arahkan ke retur."),
    }, ensure_ascii=False)


@mcp.tool()
def policy_blockers(scenario: str) -> str:
    """Return configured limits for cancellation and human review; this tool does not claim to hand off a case."""
    mapping = {
        "cancellation": {"available": True, "policy": "Ketentuan Layanan Colorbox (2026-11-15): pembatalan hanya selama pesanan belum diserahkan ke ekspedisi; setelah dikirim tidak bisa dibatalkan, gunakan retur.",
                         "agent_limit": "Status pesanan tidak dapat diverifikasi, jadi catat tiket handover kategori cancellation; jangan menyatakan pembatalan disetujui."},
        "discount": {"available": False, "reason": "Tidak ada alur persetujuan diskon yang dikonfigurasi; catat tiket handover kategori discount."},
        "refund": {"available": True, "policy": "Retur maksimal 7 hari kalender sejak diterima, wajib video unboxing, refund setelah QC ke metode pembayaran awal.",
                    "agent_limit": "Refund tidak disetujui di percakapan; catat tiket handover kategori refund."},
        "serious_dispute": {"available": True, "policy": "Sengketa yang tidak selesai musyawarah 30 hari kalender masuk yurisdiksi PN Tangerang; konsumen dapat mengadu ke Ditjen PKTN Kemendag (WA +62 812-1111-1101, simawas.kemendag.go.id).",
                             "agent_limit": "Catat tiket handover kategori dispute; jangan mengklaim sudah diteruskan ke pihak luar."},
    }
    result = mapping.get(scenario.strip().lower())
    return json.dumps(result or {"available": False, "reason": "Skenario tidak dikenal."}, ensure_ascii=False)


@mcp.tool()
def find_handover_tickets(order_id: str = "", category: str = "") -> str:
    """List earlier handover tickets for one order (and optionally one category) so a repeat request reuses the open ticket.

    Call this before ``create_handover_ticket`` whenever the customer mentions an order number.
    If an open ticket with the same order and category exists, quote that ticket id and do not create a duplicate.
    """
    params = {"limit": 20, "open_only": "true"}
    if order_id.strip():
        params["order_id"] = order_id.strip()
    if category.strip():
        params["category"] = category.strip().lower()
    result = _request("GET", "/api/data/handover", params=params)
    tickets = result.get("tickets", [])
    return json.dumps({"count": len(tickets), "tickets": tickets,
                       "instruction": ("Tiket terbuka dengan pesanan dan kategori yang sama sudah ada; sebut nomor tiket itu, jangan buat tiket baru."
                                       if tickets else "Belum ada tiket terbuka untuk pesanan ini; tiket baru boleh dibuat."),
                       }, ensure_ascii=False)


@mcp.tool()
def create_handover_ticket(category: str, summary: str, order_id: str = "", contact: str = "") -> str:
    """Record a human handover ticket (discount, refund, dispute, cancellation) and return its ticket number.

    Call this only after the customer has described the problem. ``contact`` is required whenever the
    conversation shows the sender's number as ``(+62...)``: copy those digits with the leading ``+``.
    The reply to the customer must use the returned acknowledgement and ticket id; never promise a
    decision, refund, discount, or a response time beyond the returned SLA. The acknowledgement ends
    with a ``follow_up`` paragraph asking the customer to stay in the chat; always send that paragraph
    as its own short paragraph after the ticket paragraph.
    """
    payload = {"category": category, "summary": summary}
    if order_id.strip():
        payload["order_id"] = order_id.strip()
    if contact.strip():
        payload["contact"] = contact.strip()
    try:
        result = _request("POST", "/api/data/handover", json=payload)
    except RuntimeError as exc:
        return json.dumps({"created": False, "reason": str(exc),
                           "instruction": "Katakan kasus belum bisa dicatat dan minta maaf; jangan mengarang nomor tiket."},
                          ensure_ascii=False)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def check_handover_ticket(ticket_id: str) -> str:
    """Look up a previously recorded handover ticket by its number; returns status and owner, never a promise."""
    if not ticket_id.strip():
        return json.dumps({"found": False, "reason": "Nomor tiket wajib diisi."}, ensure_ascii=False)
    result = _request("GET", f"/api/data/handover/{ticket_id.strip()}")
    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
