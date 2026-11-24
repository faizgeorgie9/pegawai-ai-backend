"""Human handover tickets for the Colorbox CS agent.

A ticket is recorded locally so the agent can point at a real case instead of
saying it cannot forward anything. When a Handover sheet is connected, the same
row is mirrored there through the Apps Script web app used for orders.

Nothing in this module messages a customer, contacts an owner, or closes a case.
A ticket with no owner is honestly reported as unassigned.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from . import config, db, sheets
from .errors import ApiError

CATEGORIES: dict[str, dict[str, str]] = {
    "discount": {"label": "Diskon khusus", "priority": "P1"},
    "refund": {"label": "Refund", "priority": "P1"},
    "dispute": {"label": "Sengketa serius", "priority": "P1"},
    "cancellation": {"label": "Pembatalan pesanan", "priority": "P2"},
}
SLA = {"P1": "1x24 jam", "P2": "2x24 jam"}
FOLLOW_UP = ("Petugas customer service akan segera menghubungi Anda. "
             "Mohon tetap di chat ini, ya.")
OPEN_STATUSES = ("open", "acknowledged", "in_review", "waiting_customer")
MAX_SUMMARY = 600
_ORDER_ID = re.compile(r"^[A-Za-z0-9._-]{3,40}$")
_CONTACT = re.compile(r"^\+?[0-9][0-9\s\-]{6,20}$")
_TICKET = re.compile(r"^HW-\d{8}-[A-Z0-9]{6}$")


def owners() -> dict[str, str]:
    """Category -> owner name, from HANDOVER_OWNERS (JSON object) when configured."""
    raw = (config.HANDOVER_OWNERS or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except ValueError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(k).strip().lower(): str(v).strip() for k, v in parsed.items() if str(v).strip()}


def _acknowledgement(ticket: str, label: str, priority: str, owner: str | None) -> str:
    if owner:
        body = (f"Kasus {label} sudah dicatat dengan nomor tiket {ticket} dan diteruskan ke {owner}. "
                f"Perkiraan tanggapan {SLA[priority]}.")
    else:
        body = (f"Kasus {label} sudah dicatat dengan nomor tiket {ticket} dan masuk antrean tinjauan tim. "
                f"Belum ada penerima yang ditetapkan, jadi saya belum bisa memastikan waktu tanggapan. "
                f"Perkiraan awal {SLA[priority]} setelah ada penerima.")
    return f"{body}\n\n{FOLLOW_UP}"


async def _mirror(user_id: str, row: dict[str, Any]) -> str:
    """Append to the Handover sheet when connected; never fail the ticket over this."""
    try:
        conn = await sheets.connection(user_id, "handover")
    except ApiError:
        return "error"
    if not conn:
        return "not_configured"
    webhook = (conn.get("webhook_url") or "").strip()
    if not webhook:
        return "no_webhook"
    contact = row["contact"] or ""
    if contact:
        contact = "'" + contact
    values = [row["created_at"], row["ticket_id"], row["category_label"], row["priority"],
              row["order_id"] or "", contact, row["summary"],
              row["owner"] or "belum ditugaskan", row["status"]]
    try:
        await sheets.append_row_to_webhook(webhook, values)
    except ApiError:
        return "failed"
    return "ok"


async def create(user_id: str, category: str, summary: str, *, order_id: str | None = None,
                 contact: str | None = None) -> dict[str, Any]:
    key = (category or "").strip().lower()
    if key not in CATEGORIES:
        raise ApiError(422, "Kategori handover harus salah satu: " + ", ".join(sorted(CATEGORIES)) + ".")
    text = " ".join((summary or "").split())
    if len(text) < 3:
        raise ApiError(422, "Ringkasan kasus wajib diisi minimal 3 karakter.")
    if len(text) > MAX_SUMMARY:
        raise ApiError(422, f"Ringkasan kasus maksimal {MAX_SUMMARY} karakter.")
    if order_id is not None:
        order_id = order_id.strip() or None
        if order_id and not _ORDER_ID.match(order_id):
            raise ApiError(422, "Nomor pesanan tidak valid.")
    if contact is not None:
        contact = " ".join(contact.split()) or None
        if contact and not _CONTACT.match(contact):
            raise ApiError(422, "Kontak harus berupa nomor telepon.")
    meta = CATEGORIES[key]
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    ticket = f"HW-{now:%Y%m%d}-{uuid4().hex[:6].upper()}"
    owner = owners().get(key)
    acknowledgement = _acknowledgement(ticket, meta["label"], meta["priority"], owner)
    record = {
        "ticket_id": ticket,
        "category": key,
        "category_label": meta["label"],
        "priority": meta["priority"],
        "order_id": order_id,
        "contact": contact,
        "summary": text,
        "owner": owner,
        "status": "open",
        "acknowledgement": acknowledgement,
        "created_at": now.strftime("%Y-%m-%d %H:%M"),
    }
    mirror = await _mirror(user_id, record)
    row = await db.q1(
        "insert into handover_tickets (user_id, ticket_id, category, order_id, contact, summary, priority, "
        "owner, status, acknowledgement, sheet_mirror) values (%s, %s, %s, %s, %s, %s, %s, %s, 'open', %s, %s) "
        "returning ticket_id, category, priority, order_id, contact, summary, owner, status, "
        "acknowledgement, sheet_mirror, created_at",
        user_id, ticket, key, order_id, contact, text, meta["priority"], owner, acknowledgement, mirror)
    result = dict(row or record)
    result.update({"category_label": meta["label"], "recorded": True, "owner_assigned": bool(owner),
                   "sla": SLA[meta["priority"]], "ticket_record": "demo_local_store",
                   "follow_up": FOLLOW_UP, "customer_contacted": False})
    return result


async def get(user_id: str, ticket_id: str) -> dict[str, Any]:
    if not _TICKET.match(ticket_id or ""):
        raise ApiError(422, "Format nomor tiket handover tidak dikenali.")
    row = await db.q1(
        "select ticket_id, category, priority, order_id, contact, summary, owner, status, acknowledgement, "
        "sheet_mirror, created_at, updated_at from handover_tickets where user_id = %s and ticket_id = %s",
        user_id, ticket_id)
    if not row:
        return {"found": False, "ticket_id": ticket_id}
    meta = CATEGORIES.get(row["category"], {"label": row["category"]})
    return {"found": True, **row, "category_label": meta["label"],
            "sla": SLA.get(row["priority"], ""), "owner_assigned": bool(row["owner"])}


async def listing(user_id: str, limit: int = 50, *, order_id: str | None = None,
                  category: str | None = None, open_only: bool = False) -> dict[str, Any]:
    clauses = ["user_id = %s"]
    params: list[Any] = [user_id]
    if order_id:
        clauses.append("order_id = %s")
        params.append(order_id.strip())
    if category:
        clauses.append("category = %s")
        params.append(category.strip().lower())
    if open_only:
        clauses.append("status = 'open'")
    params.append(max(1, min(limit, 200)))
    rows = await db.q(
        "select ticket_id, category, priority, order_id, owner, status, created_at "
        "from handover_tickets where " + " and ".join(clauses) +
        " order by created_at desc limit %s", *params)
    return {"count": len(rows), "tickets": rows}
