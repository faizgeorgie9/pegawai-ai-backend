"""Approval of risky agent actions. A risky tool (bridge.py) does not act: it stores a `pending` row here and tells the agent to wait.
The user approves or rejects it in the app; approving runs the executor registered for the row's kind, once.
New kinds (e.g. gmail_send) plug in with register(kind, executor); nothing else here changes."""
import json
import logging
from typing import Awaitable, Callable

from . import db, integrations
from .errors import ApiError

log = logging.getLogger("bff.actions")

EXPIRY = "24 hours"
LIST_LIMIT = 50
Executor = Callable[[str, dict], Awaitable[str]]  # (user_id, payload) -> sentence for the card
EXECUTORS: dict[str, Executor] = {}


def register(kind: str, executor: Executor) -> None:
    EXECUTORS[kind] = executor


async def _drive_trash(user_id: str, payload: dict) -> str:
    name = await integrations.drive_trash(user_id, payload["file_id"])
    return f"'{name}' sudah dipindahkan ke Sampah Drive. Berkas bisa dipulihkan dari sana dalam 30 hari."


register("drive_trash", _drive_trash)
register("gmail_send", integrations.gmail_send_now)
register("gmail_send_draft", integrations.gmail_send_draft_now)


def short(aid: str) -> str:
    return str(aid)[:8]


def _view(r: dict) -> dict:
    return {"id": str(r["id"]), "short_id": short(r["id"]), "kind": r["kind"], "summary": r["summary"], "payload": r["payload"],
            "status": r["status"], "result": r["result"], "source": r["source"],
            "created_at": r["created_at"], "decided_at": r["decided_at"]}


async def _expire() -> None:
    await db.ex("update pending_actions set status = 'expired', decided_at = now(), result = 'Kedaluwarsa: tidak diputuskan dalam 24 jam.' "
                f"where status = 'pending' and created_at < now() - interval '{EXPIRY}'")


def _announce(r: dict) -> None:
    from .engine import hub  # late import: engine imports harden, which imports bridge, which imports this module
    hub.publish("*", "action", {"id": str(r["id"]), "status": r["status"]})


WAITING = "Menunggu persetujuan pengguna (#{id}). Jangan ulangi permintaan ini; pengguna akan menyetujui atau menolak di aplikasi."


async def ask(user_id: str, kind: str, summary: str, payload: dict, source: dict | None = None) -> dict:
    """What a risky tool calls: the same request still waiting is returned as it is, so an agent that asks twice does not stack cards."""
    await _expire()
    same = await db.q1("select * from pending_actions where user_id = %s and kind = %s and status = 'pending' and payload = %s::jsonb limit 1",
                       user_id, kind, json.dumps(payload))
    return _view(same) if same else await create(user_id, kind, summary, payload, source)


async def create(user_id: str, kind: str, summary: str, payload: dict, source: dict | None = None) -> dict:
    if kind not in EXECUTORS:
        raise ApiError(400, "Jenis aksi tidak dikenal.")
    row = await db.q1("insert into pending_actions (user_id, kind, summary, payload, source) values (%s, %s, %s, %s::jsonb, %s::jsonb) returning *",
                      user_id, kind, summary, json.dumps(payload), json.dumps(source) if source else None)
    _announce(row)
    return _view(row)


async def list_actions(user_id: str, status: str | None = None) -> list[dict]:
    """status 'pending' = what waits; None = the latest ones of any status (so decided cards can show their result)."""
    if status not in (None, "pending"):
        raise ApiError(400, "Status tidak dikenal.")
    await _expire()
    rows = await db.q("select * from pending_actions where user_id = %s and (%s::text is null or status = %s) order by created_at desc limit %s",
                      user_id, status, status, LIST_LIMIT)
    return [_view(r) for r in rows]


async def _decide(user_id: str, aid: str, run: bool) -> dict:
    """One transaction: lock the row, check it is still pending, then reject, or run the executor and store the outcome.
    A second decision waits for the lock and then finds the row decided (409), so an action never runs twice."""
    await _expire()
    async with db.pool.connection() as c:
        async with c.transaction():
            row = await (await c.execute("select * from pending_actions where id::text = %s and user_id = %s for update", (aid, user_id))).fetchone()
            if not row:
                raise ApiError(404, "Permintaan ini tidak ditemukan.")
            if row["status"] != "pending":
                raise ApiError(409, "Permintaan ini sudah kedaluwarsa." if row["status"] == "expired" else "Permintaan ini sudah diputuskan.")
            if not run:
                status, result = "rejected", "Ditolak. Tidak ada yang diubah."
            else:
                try:
                    status, result = "done", await EXECUTORS[row["kind"]](user_id, row["payload"])
                except ApiError as e:
                    status, result = "failed", e.message
                except KeyError:
                    status, result = "failed", "Jenis aksi ini tidak didukung lagi."
                except Exception:
                    log.exception("action %s failed", row["kind"])
                    status, result = "failed", "Aksi gagal dijalankan. Coba minta agen mengulanginya."
            row = await (await c.execute("update pending_actions set status = %s, result = %s, decided_at = now() where id = %s returning *",
                                         (status, result, row["id"]))).fetchone()
    _announce(row)
    return _view(row)


async def approve(user_id: str, aid: str) -> dict:
    return await _decide(user_id, aid, True)


async def reject(user_id: str, aid: str) -> dict:
    return await _decide(user_id, aid, False)


async def status_text(user_id: str, ref: str) -> str:
    """What the agent reads from action_status: the id from the 'waiting' message (short or full)."""
    ref = ref.strip().lower()
    if not ref or len(ref) > 36 or not all(ch in "0123456789abcdef-" for ch in ref):
        return "Error: id tidak valid (pakai id dari pesan 'Menunggu persetujuan')."
    await _expire()
    r = await db.q1("select * from pending_actions where id::text like %s and user_id = %s order by created_at desc limit 1", ref + "%", user_id)
    if not r:
        return "Error: permintaan tidak ditemukan."
    label = {"pending": "Menunggu persetujuan pengguna.", "rejected": "Ditolak oleh pengguna. Jangan ulangi kecuali pengguna memintanya.",
             "done": "Disetujui dan sudah dijalankan.", "failed": "Disetujui, tetapi gagal dijalankan.",
             "expired": "Kedaluwarsa tanpa keputusan pengguna.", "approved": "Disetujui."}[r["status"]]
    return f"#{short(r['id'])}: {label} {r['result'] or ''}".strip() if r["status"] != "pending" else f"#{short(r['id'])}: {label}"
