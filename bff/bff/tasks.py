"""Papan Tugas: a task is one piece of work delegated to an agent or a team, tracked until it is done.
Status words and the move rules copy Hermes' Kanban (kanban_workflow.py), but the data lives in our Postgres (per user, priced,
run through the BFF). ALL status changes go through transition(), which checks the matrix and writes task_events; the verbs
below (start, stop, reply, ...) are the user's actions and each one only picks the target status and its fields.
Columns for the user: Antre = todo|scheduled|ready, Dikerjakan = running, Perlu Anda = blocked|review, Selesai = done
(hidden after 14 days), archived is shown only in the Arsip view."""
import asyncio
import re
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from psycopg.types.json import Jsonb

from . import bots, costs, db, engine, groups, plan_schema, settings, usage
from .errors import ApiError

COLUMNS = [("queue", "Antre", "Akan dikerjakan sesuai giliran dan jadwal"), ("running", "Dikerjakan", "Agen sedang mengerjakan"),
           ("needs_you", "Perlu Anda", "Agen menunggu persetujuan atau jawaban Anda"), ("done", "Selesai", "Sudah dikerjakan")]
ARCHIVE = ("archived", "Arsip", "Tugas yang sudah dibereskan. Bisa dipulihkan.")
STATUSES = {"queue": ("todo", "scheduled", "ready"), "running": ("running",), "needs_you": ("blocked", "review"),
            "done": ("done",), "archived": ("archived",)}
COLUMN_OF = {s: c for c, ss in STATUSES.items() for s in ss}
ORDER = {"queue": "t.priority desc, t.scheduled_at asc nulls last, t.created_at", "running": "t.started_at desc nulls last",
         "needs_you": "t.priority desc, t.updated_at desc", "done": "t.completed_at desc nulls last", "archived": "t.updated_at desc"}
PER_COLUMN = 40  # cards sent per column; `total` says how many matched
DONE_VISIBLE_DAYS = 14
EDITABLE = ("todo", "scheduled", "ready", "blocked", "review")  # a task can be changed (title, instructions, who) only here
TITLE_MAX, BODY_MAX, COMMENT_MAX = 120, 4000, 4000
STATUS_WORD = {"todo": "belum dimulai", "scheduled": "terjadwal", "ready": "sedang mengantre", "running": "sedang dikerjakan",
               "blocked": "menunggu Anda", "review": "menunggu tinjauan Anda", "done": "sudah selesai", "archived": "sudah diarsipkan"}

# allowed status changes (from -> to). The dispatcher adds claim (ready -> running) and the run's end (running -> review, ready,
# blocked); todo/running/done among themselves and review -> todo are for a plan (parent) that follows its children.
MATRIX = {
    "todo": {"scheduled", "ready", "archived", "running", "done"},
    "scheduled": {"todo", "ready", "archived"},
    "ready": {"scheduled", "running", "archived"},
    "running": {"blocked", "archived", "review", "ready", "todo", "done"},
    "blocked": {"ready", "archived", "done"},  # done: the answer to a question the agent asked outside a task (_answer_in_chat)
    "review": {"ready", "done", "archived", "todo"},
    "done": {"ready", "archived", "todo"},
    "archived": {"todo"},
}
MAX_ATTEMPTS = 2  # automatic tries of one task before it waits for the user (Perlu Anda, block_kind failed)
LATE = timedelta(hours=2)  # a scheduled recurring/plan task this far past its time is archived, not run (server was down)
LATE_REASON = "Terlewat: waktunya sudah lewat saat jadwal tidak berjalan"
STOPS: set[str] = set()  # ids of tasks the user asked to stop: the running coroutine checks it between steps
WAKE = asyncio.Event()  # set when a task becomes ready, so the scheduler loop dispatches it now instead of at the next tick
MONTH = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
DAY = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]

# the card's columns (SQL): the task plus its parent's title and how many sub-tasks it has
SELECT = ("select t.*, p.title as parent_title, (select count(*)::int from tasks c where c.parent_id = t.id and c.status <> 'archived') "
          "as children_total, (select count(*)::int from tasks c where c.parent_id = t.id and c.status = 'done') as children_done "
          "from tasks t left join tasks p on p.id = t.parent_id")


# ---------- pure helpers ----------

def first_line(text: str | None, n: int = 110) -> str:
    line = next((x.strip() for x in (text or "").splitlines() if x.strip()), "")
    line = re.sub(r"^[#>*\-\s]+", "", line)
    return line if len(line) <= n else line[: n - 1].rstrip() + "…"


def when_label(at: datetime, tz: str) -> str:
    d = at.astimezone(ZoneInfo(tz))
    return f"{DAY[d.weekday()]}, {d.day} {MONTH[d.month - 1]} {d:%H:%M}"


def line_of(t: dict, tz: str) -> str:
    """One plain sentence about where the task stands."""
    s, bk = t["status"], t["block_kind"]
    if t["kind"] == "plan" and s in ("todo", "running", "done"):
        return f"{t['children_done']} dari {t['children_total']} hari selesai"
    if s == "scheduled" and t["scheduled_at"]:
        return f"Dijadwalkan {when_label(t['scheduled_at'], tz)}"
    if s == "todo":
        return "Belum dikerjakan"
    if s == "ready":
        return "Menunggu giliran"
    if s == "running":
        return "Agen sedang mengerjakan"
    if s == "blocked":
        return t["block_reason"] or {"stopped": "Dihentikan. Anda bisa melanjutkannya", "failed": "Gagal dikerjakan",
                                     "needs_input": "Agen menunggu jawaban Anda"}.get(bk or "", "Agen menunggu jawaban Anda")
    if s == "review":
        return "Rencana menunggu persetujuan Anda" if bk == "plan_approval" else "Hasil siap ditinjau"
    if s in ("done", "archived"):
        if t["outcome"] == "cancelled":
            return "Dibatalkan"
        if t["outcome"] == "failed":
            return t["block_reason"] or "Gagal dikerjakan"
        return first_line(t["result"]) or "Selesai"
    return ""


def actions_of(t: dict, link: str | None) -> tuple[dict | None, list[dict]]:
    """(primary action, the rest for the ⋯ menu). At most one visible button per card. `id` is a verb of the API or, for
    `open`/`edit`/`chat`, something the screen does itself."""
    cancel = {"id": "cancel", "label": "Batalkan", "confirm": f"Batalkan \"{t['title']}\"? Tugas ini dan bagian-bagiannya yang belum selesai tidak akan dikerjakan."}
    s, bk = t["status"], t["block_kind"]
    if t["kind"] == "plan":  # a plan is never worked on itself: approve, revise or cancel it; its days are the sub-tasks
        if s == "review":
            return {"id": "approve", "label": "Setujui rencana"}, [{"id": "open", "label": "Minta revisi"}, cancel]
        if s == "archived":
            return None, []
        return {"id": "open", "label": "Lihat rencana"}, [{"id": "archive", "label": "Arsipkan"}] if s == "done" else [cancel]
    if s in ("todo", "scheduled"):
        return {"id": "start", "label": "Kerjakan sekarang"}, [{"id": "edit", "label": "Ubah"}, cancel]
    if s == "ready":
        return None, [{"id": "edit", "label": "Ubah"}, cancel]
    if s == "running":
        stop = {"id": "stop", "label": "Hentikan", "confirm": f"Hentikan \"{t['title']}\"? Pekerjaan yang sedang berjalan akan berhenti."}
        return stop, [{"id": "chat", "label": "Buka obrolan"}] if link else []
    if s == "blocked":
        if bk in ("stopped", "failed"):
            return {"id": "start", "label": "Coba lagi"}, [cancel]
        return {"id": "open", "label": "Jawab"}, [cancel]
    if s == "review":
        return {"id": "approve", "label": "Setujui"}, [{"id": "open", "label": "Minta revisi"}, cancel]
    if s == "done":
        return {"id": "open", "label": "Lihat hasil"}, [{"id": "retry", "label": "Ulangi"}, {"id": "archive", "label": "Arsipkan"}]
    return {"id": "restore", "label": "Pulihkan"}, []


def _text(v, what: str, limit: int, required: bool = True) -> str:
    if not isinstance(v, str) or (required and not v.strip()) or len(v.strip()) > limit:
        raise ApiError(400, f"{what} wajib diisi (maksimal {limit} karakter)" if required else f"{what} maksimal {limit} karakter")
    return v.strip()


def _when(v) -> datetime | None:
    if v is None:
        return None
    try:
        d = datetime.fromisoformat(v.replace("Z", "+00:00")) if isinstance(v, str) else None
    except ValueError:
        d = None
    if d is None or d.tzinfo is None:
        raise ApiError(400, "Jadwal tidak valid")
    if d <= datetime.now(timezone.utc):
        raise ApiError(400, "Jadwal harus di waktu yang akan datang")
    return d


def _task_uuid(v: str, what: str = "Tugas") -> str:
    try:
        return str(uuid.UUID(v))
    except ValueError:
        raise ApiError(404, f"{what} tidak ditemukan")


# ---------- changing status ----------

async def event(task_id, kind: str, **payload) -> None:
    await db.ex("insert into task_events (task_id, kind, payload) values (%s, %s, %s)", task_id, kind, Jsonb(payload))


async def transition(task: dict, to: str, actor: str, kind: str | None = None, **fields) -> dict:
    """The only place that changes `status`. Checks the matrix, updates the row only if it still has the status we saw (a
    double click or the dispatcher cannot slip past), and records the event. `fields` are extra columns set in the same update."""
    frm = task["status"]
    if to not in MATRIX.get(frm, ()):
        raise ApiError(409, f"Tugas yang {STATUS_WORD[frm]} tidak bisa dipindah ke sana")
    sets = {"status": to, **fields}
    row = await db.q1(f"update tasks set {', '.join(f'{k} = %s' for k in sets)}, updated_at = now() where id = %s and status = %s returning *",
                      *sets.values(), task["id"], frm)
    if not row:
        raise ApiError(409, "Tugas ini baru saja berubah. Muat ulang papan.")
    await event(task["id"], kind or to, actor=actor, **{"from": frm, "to": to})
    if to == "ready":
        WAKE.set()
    if row["parent_id"]:
        await _sync_parent(row["parent_id"])
    return row


async def _sync_parent(pid) -> None:
    """An approved plan follows its days: running while one runs, done when all are done, else waiting in Antre."""
    p = await db.q1("select * from tasks where id = %s and kind = 'plan' and status in ('todo', 'running', 'done')", pid)
    kids = [r["status"] for r in await db.q("select status from tasks where parent_id = %s and status <> 'archived'", pid)] if p else []
    if not kids:
        return
    to = "running" if "running" in kids else "done" if all(k == "done" for k in kids) else "todo"
    if to == p["status"]:
        return
    ended = {"outcome": "ok", "completed_at": datetime.now(timezone.utc)} if to == "done" else {"outcome": None, "completed_at": None}
    try:
        await transition(p, to, "system", "children", **ended)
    except ApiError:
        pass  # it changed meanwhile; the next child change syncs it again


CLEAR = {"block_kind": None, "block_reason": None, "outcome": None, "completed_at": None, "attempts": 0}  # a task that goes back to work (fresh tries)


async def _owned(uid: str, tid: str) -> dict:
    row = await db.q1("select * from tasks where id = %s and user_id = %s", tid, uid)
    if not row:
        raise ApiError(404, "Tugas tidak ditemukan")
    return row


def _need(t: dict, allowed: tuple[str, ...], why: str) -> None:
    if t["status"] not in allowed:
        raise ApiError(409, why)


async def _halt(uid: str, t: dict) -> None:
    """Stop the work of a running task with the paths that exist: the run, or the team's discussion."""
    if t["status"] != "running":
        return
    STOPS.add(str(t["id"]))
    try:
        if t["current_run_id"]:
            await engine.stop(uid, str(t["current_run_id"]))
        elif t["assignee_group"]:
            await groups.stop(uid, str(t["assignee_group"]))
    except ApiError:
        pass  # it had already ended


def _not_plan(t: dict) -> None:
    if t["kind"] == "plan":
        raise ApiError(409, "Rencana tidak dikerjakan langsung. Setujui, minta revisi, atau batalkan.")


async def _verb_start(uid, t, actor, **_):
    _not_plan(t)
    _need(t, ("todo", "scheduled", "blocked", "review", "done"), "Tugas ini tidak bisa dikerjakan sekarang")
    return await transition(t, "ready", actor, "start", scheduled_at=None, **CLEAR)


async def _verb_stop(uid, t, actor, **_):
    _need(t, ("running",), "Hanya tugas yang sedang dikerjakan yang bisa dihentikan")
    await _halt(uid, t)
    return await transition(t, "blocked", actor, "stop", block_kind="stopped", block_reason="Dihentikan. Anda bisa melanjutkannya",
                            current_run_id=None)


async def _verb_reply(uid, t, actor, text=None, **_):
    _need(t, ("blocked", "review"), "Tugas ini tidak sedang menunggu jawaban Anda")
    text = _text(text, "Jawaban", COMMENT_MAX)
    if t["kind"] == "plan":  # an answer about a plan is a revision request to the team
        return await _revise_plan(uid, t, text)
    if t["source_ref"].get("ask"):  # a question the agent asked in a chat or team: the answer goes back there, where the agent continues
        return await _answer_in_chat(uid, t, actor, text)
    row = await transition(t, "ready", actor, "reply", scheduled_at=None, **CLEAR)
    await _comment(t["id"], "user", text)
    return row


async def _verb_request_changes(uid, t, actor, note=None, text=None, **_):
    _need(t, ("review",), "Revisi hanya bisa diminta untuk hasil yang menunggu tinjauan")
    note = _text(note if note is not None else text, "Catatan revisi", COMMENT_MAX)
    if t["kind"] == "plan":
        return await _revise_plan(uid, t, note)
    row = await transition(t, "ready", actor, "request_changes", scheduled_at=None, **CLEAR)
    await _comment(t["id"], "user", note)
    return row


async def _verb_approve(uid, t, actor, **_):
    _need(t, ("review",), "Hanya hasil yang menunggu tinjauan yang bisa disetujui")
    if t["kind"] == "plan":
        return await _approve_plan(uid, t)
    return await transition(t, "done", actor, "approve", outcome="ok", completed_at=datetime.now(timezone.utc), block_kind=None, block_reason=None)


async def _verb_cancel(uid, t, actor, **_):
    """Archive with outcome cancelled, the same for every sub-task that is not done yet; running work is stopped."""
    _need(t, tuple(s for s in MATRIX if s != "archived"), "Tugas ini sudah diarsipkan")
    kids = await db.q("with recursive d as (select id from tasks where parent_id = %s union select t.id from tasks t join d on t.parent_id = d.id) "
                      "select t.* from tasks t join d on d.id = t.id where t.status not in ('done', 'archived')", t["id"])
    end = {"outcome": "cancelled", "completed_at": datetime.now(timezone.utc), "block_kind": None, "block_reason": None, "scheduled_at": None,
           "current_run_id": None}
    for x in [t, *kids]:
        await _halt(uid, x)
    row = await transition(t, "archived", actor, "cancel", **end)
    for x in kids:
        try:
            await transition(x, "archived", actor, "cancel", **end)
        except ApiError:
            pass  # a sub-task that changed in the meantime is already out of the way
    return row


async def _verb_retry(uid, t, actor, **_):
    _not_plan(t)
    _need(t, ("done",), "Hanya tugas yang sudah selesai yang bisa diulangi")
    return await transition(t, "ready", actor, "retry", scheduled_at=None, **CLEAR)


async def _verb_archive(uid, t, actor, **_):
    _need(t, ("done",), "Hanya tugas yang sudah selesai yang bisa diarsipkan")
    return await transition(t, "archived", actor, "archive")


async def _verb_restore(uid, t, actor, **_):
    _not_plan(t)
    _need(t, ("archived",), "Tugas ini tidak sedang diarsipkan")
    return await transition(t, "todo", actor, "restore", scheduled_at=None, **CLEAR)


async def _verb_move(uid, t, actor, to=None, **kw):
    """Drag and drop: only Perlu Anda -> Antre (= start) and Selesai -> Antre (= retry). Dikerjakan is never a target."""
    col = COLUMN_OF[t["status"]]
    if to == "queue" and col == "needs_you":
        return await _verb_start(uid, t, actor)
    if to == "queue" and col == "done":
        return await _verb_retry(uid, t, actor)
    raise ApiError(409, "Tugas ini tidak bisa dipindah ke sana. Pakai tombol di kartu.")


VERBS = {"start": _verb_start, "stop": _verb_stop, "reply": _verb_reply, "request_changes": _verb_request_changes,
         "approve": _verb_approve, "cancel": _verb_cancel, "retry": _verb_retry, "archive": _verb_archive,
         "restore": _verb_restore, "move": _verb_move}


async def do(uid: str, tid: str, verb: str, body: dict) -> dict:
    fn = VERBS.get(verb)
    if not fn:
        raise ApiError(404, "Tindakan tidak dikenal")
    t = await _owned(uid, _task_uuid(tid))
    await fn(uid, t, "user", text=body.get("text"), note=body.get("note"), to=body.get("to"))
    return await detail(uid, tid)


# ---------- create, edit, comment ----------

async def _comment(tid, author: str, text: str, bot_id: str | None = None) -> dict:
    return await db.q1("insert into task_comments (task_id, author, bot_id, text) values (%s, %s, %s, %s) returning *", tid, author, bot_id, text)


async def _assignee(uid: str, b: dict) -> tuple[str | None, str | None]:
    bot, grp = b.get("assignee_bot"), b.get("assignee_group")
    if (bot is None) == (grp is None) or not isinstance(bot or grp, str):
        raise ApiError(400, "Pilih satu agen atau satu tim yang mengerjakan")
    if bot:
        await bots.get_bot(uid, bot)
    else:
        await groups.get_group(uid, _task_uuid(grp, "Grup"))
    return bot, grp


def _priority(v) -> int:
    if v not in (0, 1) or isinstance(v, bool):
        raise ApiError(400, "Prioritas harus 0 (biasa) atau 1 (penting)")
    return v


async def create(uid: str, b: dict, source: str = "user", source_ref: dict | None = None) -> dict:
    title, body = _text(b.get("title"), "Judul", TITLE_MAX), _text(b.get("body", ""), "Instruksi", BODY_MAX, required=False)
    bot, grp = await _assignee(uid, b)
    at = _when(b.get("scheduled_at"))
    status = "scheduled" if at else "todo"
    row = await db.q1("insert into tasks (user_id, title, body, assignee_bot, assignee_group, status, priority, scheduled_at, source, source_ref) "
                      "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning id", uid, title, body, bot, grp, status,
                      _priority(b.get("priority", 0)), at, source, Jsonb(source_ref or {}))
    await event(row["id"], "created", actor="agent" if source == "agent" else "user", to=status)
    return await detail(uid, str(row["id"]))


async def edit(uid: str, tid: str, b: dict) -> dict:
    t = await _owned(uid, _task_uuid(tid))
    _need(t, EDITABLE, "Tugas yang sedang dikerjakan atau sudah selesai tidak bisa diubah")
    sets: dict = {}
    if "title" in b:
        sets["title"] = _text(b["title"], "Judul", TITLE_MAX)
    if "body" in b:
        sets["body"] = _text(b["body"], "Instruksi", BODY_MAX, required=False)
    if "priority" in b:
        sets["priority"] = _priority(b["priority"])
    if "assignee_bot" in b or "assignee_group" in b:
        sets["assignee_bot"], sets["assignee_group"] = await _assignee(uid, b)
    to = None
    if "scheduled_at" in b:
        at = _when(b["scheduled_at"])
        if t["status"] in ("blocked", "review"):
            raise ApiError(409, "Jadwal hanya bisa diubah untuk tugas di Antre")
        sets["scheduled_at"] = at
        if at and t["status"] != "scheduled":
            to = "scheduled"
        elif not at and t["status"] == "scheduled":
            to = "todo"
    if not sets:
        raise ApiError(400, "Tidak ada yang diubah")
    if to:
        await transition(t, to, "user", "edit", **sets)
    else:
        row = await db.q1(f"update tasks set {', '.join(f'{k} = %s' for k in sets)}, updated_at = now() where id = %s and status = %s returning id",
                          *sets.values(), t["id"], t["status"])
        if not row:
            raise ApiError(409, "Tugas ini baru saja berubah. Muat ulang papan.")
        await event(t["id"], "edit", actor="user", fields=sorted(sets))
    return await detail(uid, tid)


async def comment(uid: str, tid: str, text) -> dict:
    """A plain note from the user; it does not move the task (replying to a waiting agent is the `reply` verb)."""
    t = await _owned(uid, _task_uuid(tid))
    _need(t, tuple(s for s in MATRIX if s != "archived"), "Tugas yang diarsipkan tidak bisa diberi komentar")
    await _comment(t["id"], "user", _text(text, "Komentar", COMMENT_MAX))
    return await detail(uid, tid)


# ---------- views ----------

async def _context(uid: str, rows: list[dict]) -> dict:
    names = {b["id"]: b for b in await db.q("select id, name, color from bots where user_id = %s", uid)}
    gnames = {str(g["id"]): g["name"] for g in await db.q("select id, name from groups where user_id = %s", uid)}
    tz = (await settings.get(uid))["timezone"]
    ids = [str(r["id"]) for r in rows if r["status"] in ("done", "archived")]
    spent: dict[str, dict] = {}
    if ids:
        runs = await db.q(f"select {usage._COLS}, r.task_id from runs r where r.task_id = any(%s::uuid[])", ids)
        pricer = await costs.pricer_for(r["bot_id"] for r in runs)
        for r in runs:
            c = usage._cost(r, pricer)
            s = spent.setdefault(str(r["task_id"]), {"usd": costs.ZERO, "estimated": False})
            s["usd"] += c["usd"]
            s["estimated"] = s["estimated"] or c["estimated"]
    links = {}
    for r in await db.q("select distinct on (task_id) task_id, bot_id, session_id, group_id from runs where task_id = any(%s::uuid[]) "
                        "order by task_id, created_at desc", [str(r["id"]) for r in rows]):
        links[str(r["task_id"])] = f"/grup/{r['group_id']}" if r["group_id"] else f"/chat/{r['bot_id']}/{r['session_id']}"
    return {"bots": names, "groups": gnames, "tz": tz, "spent": spent, "links": links}


def card(t: dict, cx: dict) -> dict:
    link = cx["links"].get(str(t["id"])) or (f"/grup/{t['assignee_group']}" if t["assignee_group"] else None)
    main, more = actions_of(t, link)
    if t["assignee_bot"]:
        b = cx["bots"].get(t["assignee_bot"])
        who = {"bot": t["assignee_bot"], "name": b["name"] if b else t["assignee_bot"], "color": b["color"] if b else "slate"}
    elif t["assignee_group"]:
        who = {"group": str(t["assignee_group"]), "name": cx["groups"].get(str(t["assignee_group"]), "Tim"), "color": "slate"}
    else:
        who = None
    sp = cx["spent"].get(str(t["id"]))
    return {"id": str(t["id"]), "title": t["title"], "column": COLUMN_OF[t["status"]], "status": t["status"], "kind": t["kind"],
            "priority": t["priority"], "assignee": who, "parent": {"id": str(t["parent_id"]), "title": t["parent_title"]} if t["parent_id"] else None,
            "scheduled_at": t["scheduled_at"], "block_kind": t["block_kind"], "outcome": t["outcome"], "line": line_of(t, cx["tz"]),
            "cost": costs.money(sp["usd"]) if sp else None, "estimated": bool(sp and sp["estimated"]), "link": link,
            "children_done": t["children_done"] if t["kind"] == "plan" else None,
            "children_total": t["children_total"] if t["kind"] == "plan" else None,
            "updated_at": t["updated_at"], "primary_action": main, "more_actions": more}


async def board(uid: str, agent: str | None, group: str | None, q: str | None, archived: bool = False) -> dict:
    where = "t.user_id = %s and (%s::text is null or t.assignee_bot = %s) and (%s::uuid is null or t.assignee_group = %s) and (%s::text is null or t.title ilike %s or t.body ilike %s)"
    like = "%" + q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%" if q and q.strip() else None
    args = (uid, agent, agent, group, group, like, like, like)
    cols = [ARCHIVE] if archived else COLUMNS
    out, found = [], []
    for cid, label, hint in cols:
        extra = " and (t.status <> 'done' or coalesce(t.completed_at, t.updated_at) >= now() - make_interval(days => %s))" if cid == "done" else ""
        rows = await db.q(f"{SELECT} where {where} and t.status = any(%s){extra} order by {ORDER[cid]} limit %s",
                          *args, list(STATUSES[cid]), *([DONE_VISIBLE_DAYS] if extra else []), PER_COLUMN)
        total = (await db.q1(f"select count(*)::int as n from tasks t where {where} and t.status = any(%s){extra}",
                             *args, list(STATUSES[cid]), *([DONE_VISIBLE_DAYS] if extra else [])))["n"]
        out.append({"id": cid, "label": label, "hint": hint, "total": total})
        found.append(rows)
    cx = await _context(uid, [r for rows in found for r in rows])
    for c, rows in zip(out, found):
        c["cards"] = [card(r, cx) for r in rows]
    return {"columns": out, "counts": {c["id"]: c["total"] for c in out}}


async def detail(uid: str, tid: str) -> dict:
    row = await db.q1(f"{SELECT} where t.id = %s and t.user_id = %s", _task_uuid(tid), uid)
    if not row:
        raise ApiError(404, "Tugas tidak ditemukan")
    kids = await db.q(f"{SELECT} where t.parent_id = %s and t.status <> 'archived' order by t.scheduled_at nulls last, t.created_at", row["id"])
    cx = await _context(uid, [row, *kids])
    runs = await db.q(f"select {usage._COLS}, r.started_at, r.finished_at from runs r where r.task_id = %s order by r.created_at desc limit 20", row["id"])
    pricer = await costs.pricer_for(r["bot_id"] for r in runs)
    comments = await db.q("select id, author, bot_id, text, created_at from task_comments where task_id = %s order by id", row["id"])
    events = await db.q("select kind, payload, created_at from task_events where task_id = %s order by id desc limit 30", row["id"])
    return {**card(row, cx), "body": row["body"], "result": row["result"], "block_reason": row["block_reason"], "attempts": row["attempts"],
            "source": row["source"], "created_at": row["created_at"],
            "editable": row["status"] in EDITABLE,
            "comments": [{**c, "id": str(c["id"])} for c in comments], "events": events[::-1],
            "runs": [{"id": str(r["id"]), "status": r["status"], "bot_id": r["bot_id"], "at": r["started_at"] or r["created_at"],
                      "cost": costs.money(usage._cost(r, pricer)["usd"])} for r in runs],
            "children": [card(k, cx) for k in kids]}


# ---------- dispatching (the scheduler loop calls these) ----------

FAILED_TEXT = "Gagal dikerjakan dua kali. Coba lagi nanti atau ubah instruksinya."


def build_prompt(t: dict, parent: dict | None, comments: list[str]) -> str:
    """What the agent is asked: the task, the plan it belongs to, and what the owner wrote since the last run."""
    out = [f"Tugas: {t['title']}"]
    if t["body"]:
        out.append(t["body"])
    if parent:
        out.append(f"Tugas ini bagian dari: {parent['title']}" + (f"\n{parent['body']}" if parent["body"] else ""))
    if comments:
        out.append("Pesan terbaru dari pemilik bisnis:\n" + "\n".join(f"- {c}" for c in comments))
    if t.get("id"):
        out.append(f"(id tugas: {t['id']}. Akhiri selalu dengan alat task_complete, task_request_review atau task_ask_user; "
                   "task_comment untuk catatan.)")
    return "\n\n".join(out)


async def prompt_for(t: dict) -> str:
    parent = await db.q1("select title, body from tasks where id = %s", t["parent_id"]) if t["parent_id"] else None
    last = (await db.q1("select max(created_at) as at from runs where task_id = %s", t["id"]))["at"]
    rows = await db.q("select text from task_comments where task_id = %s and author = 'user' and (%s::timestamptz is null or created_at > %s) "
                      "order by id", t["id"], last, last)
    return build_prompt(t, parent, [r["text"] for r in rows])


async def release_due() -> None:
    """scheduled -> ready when the time has come; a recurring or plan day that is long past is archived instead of run late."""
    now = datetime.now(timezone.utc)
    for t in await db.q("select * from tasks where kind = 'task' and status = 'scheduled' and scheduled_at <= now()"):
        try:
            if t["source"] in ("recurring", "plan") and t["scheduled_at"] < now - LATE:
                await transition(t, "archived", "system", "late", outcome="failed", block_reason=LATE_REASON, completed_at=now)
            else:
                await transition(t, "ready", "system", "due")
        except ApiError:
            pass  # the user changed it meanwhile


async def claim() -> dict | None:
    """Take the next ready task (important first, then oldest). An assignee, agent or team, works on one task at a time."""
    rows = await db.q("select t.* from tasks t where t.kind = 'task' and t.status = 'ready' and not exists (select 1 from tasks r "
                      "where r.kind = 'task' and r.status = 'running' and r.user_id = t.user_id and "
                      "(r.assignee_bot = t.assignee_bot or r.assignee_group = t.assignee_group)) "
                      "order by t.priority desc, t.created_at limit 10")
    for t in rows:
        try:
            return await transition(t, "running", "system", "claim", started_at=datetime.now(timezone.utc), attempts=t["attempts"] + 1,
                                    current_run_id=None)
        except ApiError:
            continue  # taken or changed by someone else
    return None


async def finish(t: dict, status: str, reason: str | None, result: str | None) -> None:
    """Where a task goes when its run ended. `status` is drive()/follow_group()'s: done | skipped | cancelled | failed. `t` is the
    row as claimed: if the task is no longer that running attempt (the user stopped or cancelled it), nothing changes."""
    row = await db.q1("select * from tasks where id = %s", t["id"])
    if not row or row["status"] != "running" or row["started_at"] != t["started_at"]:
        return
    end = {"current_run_id": None}
    try:
        if status == "done":
            await transition(row, "review", "system", "run_done", block_kind="review", block_reason=None,
                             result=result or "Agen selesai tanpa hasil tertulis.", **end)
        elif status == "skipped":  # quota: waiting would not help, tell the user why
            await transition(row, "blocked", "system", "skipped", block_kind="failed", block_reason=reason, **end)
        elif status == "cancelled":
            await transition(row, "blocked", "system", "stop", block_kind="stopped", block_reason="Dihentikan. Anda bisa melanjutkannya", **end)
        else:
            await event(row["id"], "run_failed", reason=reason)
            if row["attempts"] < MAX_ATTEMPTS:
                await transition(row, "ready", "system", "auto_retry", **end)
            else:
                await transition(row, "blocked", "system", "failed", block_kind="failed", block_reason=FAILED_TEXT, **end)
    except ApiError:
        pass  # changed in the meantime


async def recover() -> None:
    """A restart loses the coroutines of running tasks: they go back to the queue (the interrupted try counts)."""
    for t in await db.q("select * from tasks where kind = 'task' and status = 'running'"):
        try:
            await transition(t, "ready", "system", "recover", current_run_id=None)
        except ApiError:
            pass


async def end_schedule_tasks(schedule_id: str, paused: bool) -> None:
    """Pause or delete of a recurring schedule: its days that have not started are archived (a pause marks them, resume removes them)."""
    for t in await db.q("select * from tasks where schedule_id = %s and status in ('scheduled', 'todo', 'ready')", schedule_id):
        fields = {"outcome": "cancelled", "completed_at": datetime.now(timezone.utc), "scheduled_at": None}
        if paused:
            fields["source_ref"] = Jsonb({**t["source_ref"], "paused": True})
        try:
            await transition(t, "archived", "system", "schedule_paused" if paused else "schedule_deleted", **fields)
        except ApiError:
            pass


async def drop_paused_tasks(schedule_id: str) -> None:
    await db.ex("delete from tasks where schedule_id = %s and status = 'archived' and source_ref->>'paused' = 'true'", schedule_id)


# ---------- content plans (kind = plan: the parent; its days are the sub-tasks) ----------

async def _new_plan(uid: str, gid: str, message_id: int, plan: dict) -> dict:
    g = await groups.get_group(uid, gid)
    body = "\n".join(f"- {d['date']} {d['time']}: {d['theme']}" for d in plan["days"])
    row = await db.q1("insert into tasks (user_id, title, body, assignee_group, status, kind, source, source_ref, block_kind) "
                      "values (%s, %s, %s, %s, 'review', 'plan', 'plan', %s, 'plan_approval') "
                      "on conflict ((source_ref->>'message_id')) where kind = 'plan' do nothing returning *",
                      uid, f"{plan['title']} ({g['name']})"[:TITLE_MAX], body[:BODY_MAX], gid, Jsonb({"group_id": gid, "message_id": message_id}))
    if not row:  # the same message was handled a moment ago
        return await db.q1("select * from tasks where kind = 'plan' and source_ref->>'message_id' = %s", str(message_id))
    await event(row["id"], "created", actor="system", to="review")
    return row


async def plan_posted(gid: str, msg: dict) -> None:
    """A valid plan was just posted in a group: it becomes a task waiting for approval, and an older plan of the group that
    still waits is replaced (archived) by it."""
    g = await db.q1("select user_id from groups where id = %s", gid)
    if not g:
        return
    new = await _new_plan(g["user_id"], gid, msg["id"], msg["plan"])
    for old in await db.q("select * from tasks where kind = 'plan' and assignee_group = %s and status = 'review' and id <> %s", gid, new["id"]):
        try:
            await transition(old, "archived", "system", "replaced", outcome="cancelled", completed_at=datetime.now(timezone.utc),
                             block_kind=None, block_reason=None, source_ref=Jsonb({**old["source_ref"], "replaced": True}))
        except ApiError:
            pass


async def _plan_task(uid: str, gid: str, message_id: int) -> dict:
    """The plan task of a group message with a valid plan (a plan posted before tasks existed gets its task now)."""
    await groups.get_group(uid, gid)
    t = await db.q1("select * from tasks where kind = 'plan' and user_id = %s and source_ref->>'message_id' = %s", uid, str(message_id))
    if t:
        return t
    msg = await db.q1("select author, text from group_messages where id = %s and group_id = %s", message_id, gid)
    plan = plan_schema.parse(msg["text"])[0] if msg and msg["author"] == "bot" else None
    if not plan:
        raise ApiError(404, "Rencana tidak ditemukan atau tidak valid")
    return await _new_plan(uid, gid, message_id, plan)


def _plan_view(t: dict) -> dict:
    return {"task_id": str(t["id"]), "state": groups.plan_state(t)}


async def _approve_plan(uid: str, t: dict) -> dict:
    """The one place a plan is approved (board or chat card): the plan becomes a summary card and each day a scheduled sub-task
    (writer, then visual, in the group). shortcut: the parent's move and the days are separate statements; a crash between them
    leaves an approved plan without days: cancel it and ask the team again."""
    gid, mid = t["source_ref"]["group_id"], int(t["source_ref"]["message_id"])
    msg = await db.q1("select text from group_messages where id = %s and group_id = %s", mid, gid)
    plan = plan_schema.parse(msg["text"])[0] if msg else None
    if not plan:
        raise ApiError(404, "Rencana tidak ditemukan atau tidak valid")
    targets = plan_schema.find_executors(await groups.members(gid))
    rows = plan_schema.plan_slots(plan, (await settings.get(uid))["timezone"], datetime.now(timezone.utc))
    row = await transition(t, "todo", "user", "approve", block_kind=None, block_reason=None)  # its status guard decides a double click
    for at, title, brief in rows:
        await db.ex("insert into tasks (user_id, title, body, assignee_group, status, scheduled_at, source, source_ref, parent_id) "
                    "values (%s, %s, %s, %s, 'scheduled', %s, 'plan', %s, %s)",
                    uid, title[:TITLE_MAX], brief, gid, at, Jsonb({**t["source_ref"], "targets": targets}), t["id"])
    await groups.post(gid, "system", f"Rencana disetujui: {len(rows)} hari terjadwal.")
    return row


async def approve_plan(uid: str, gid: str, message_id: int) -> dict:
    """The chat card's Setujui. Approving twice is fine: the second call just reports the state."""
    t = await _plan_task(uid, gid, message_id)
    if t["status"] == "review":
        try:
            await _approve_plan(uid, t)
        except ApiError as e:
            t = await _owned(uid, str(t["id"]))
            if e.status != 409 or t["status"] == "review":
                raise
    t = await _owned(uid, str(t["id"]))
    if groups.plan_state(t) in ("cancelled", "replaced"):
        raise ApiError(409, "Rencana ini sudah dibatalkan")
    return _plan_view(t)


async def cancel_plan(uid: str, gid: str, message_id: int) -> dict:
    """The chat card's Batalkan: the plan and the days that are not done are archived."""
    t = await _plan_task(uid, gid, message_id)
    if t["status"] != "archived":
        t = await _verb_cancel(uid, t, "user")
    return _plan_view(t)


async def _revise_plan(uid: str, t: dict, note: str) -> dict:
    """The user's feedback goes back into the group as a normal message to the plan's author, who posts a new plan; that one
    replaces this one (plan_posted)."""
    msg = await db.q1("select bot_id from group_messages where id = %s", int(t["source_ref"]["message_id"]))
    await _comment(t["id"], "user", note)
    return await groups.send(uid, str(t["assignee_group"]), f"@{msg['bot_id']} Mohon revisi rencana ini: {note}", "queue")


async def revise_plan(uid: str, gid: str, message_id: int, feedback) -> dict:
    t = await _plan_task(uid, gid, message_id)
    if t["status"] != "review":
        raise ApiError(409, "Rencana ini sudah disetujui atau dibatalkan")
    return await _revise_plan(uid, t, _text(feedback, "Catatan revisi", 3000))


# ---------- the agent's own tools (bridge.py: task_list, task_create, task_comment, task_ask_user, ...) ----------
# `src` is bridge._source(): {bot_id, run_id?, session_id?, group_id?} for the bot calling and the run it is busy with now.

ASK_TITLE_WORDS = 8


def first_words(text: str, n: int = ASK_TITLE_WORDS) -> str:
    w = text.split()
    return " ".join(w[:n]) + ("…" if len(w) > n else "")


async def _agent_task(uid: str, src: dict | None, task_id: str | None) -> dict | None:
    """The task a tool call is about: the id the agent gave, else the task of the run it is busy with (None when there is none)."""
    if task_id and task_id.strip():
        return await _owned(uid, _task_uuid(task_id.strip()))
    run = await db.q1("select task_id from runs where id = %s", src["run_id"]) if src and src.get("run_id") else None
    return await db.q1("select * from tasks where id = %s and user_id = %s", run["task_id"], uid) if run and run["task_id"] else None


async def _need_task(uid: str, src, task_id) -> dict:
    t = await _agent_task(uid, src, task_id)
    if not t:
        raise ApiError(404, "Tidak ada tugas aktif. Berikan task_id (lihat task_list) atau buat tugas dengan task_create.")
    return t


def _line(t: dict) -> str:
    who = t["assignee_bot"] or (f"team {t['assignee_group']}" if t["assignee_group"] else "-")
    return f"- {t['id']} | {t['title']} | status: {t['status']} | for: {who}" + (f" | scheduled: {t['scheduled_at']:%Y-%m-%d %H:%M} UTC" if t["scheduled_at"] else "")


async def agent_list(uid: str, status: str | None) -> str:
    """The owner's tasks, newest change first (archived ones only when asked for): max 30."""
    st = (status or "").strip()
    want = [st] if st in MATRIX else list(STATUSES.get(st, ())) or [s for s in MATRIX if s != "archived"]
    rows = await db.q("select * from tasks where user_id = %s and status = any(%s) order by updated_at desc limit 30", uid, want)
    return "\n".join(_line(t) for t in rows) or "No tasks."


async def agent_create(uid: str, src: dict | None, title: str, instructions: str = "", assignee: str = "", when: str = "") -> str:
    """A task made by an agent: for itself by default; `assignee` is a bot id or a team name/id; `when` an ISO time (then it runs at that
    time, else it waits in Antre until the owner presses Kerjakan sekarang)."""
    who = (assignee or "").strip()
    b: dict = {"title": title, "body": instructions or "", "scheduled_at": (when or "").strip() or None}
    if not who and src:
        b["assignee_bot"] = src["bot_id"]
    elif who and await db.q1("select 1 from bots where id = %s and user_id = %s", who, uid):
        b["assignee_bot"] = who
    elif who:
        g = await db.q1("select id from groups where user_id = %s and (id::text = %s or lower(name) = lower(%s))", uid, who, who)
        if not g:
            raise ApiError(404, f"Agen atau tim '{who}' tidak ditemukan")
        b["assignee_group"] = str(g["id"])
    else:
        raise ApiError(400, "Sebutkan assignee (agen atau tim)")
    ref = {k: src[k] for k in ("run_id", "session_id", "group_id") if src and src.get(k)}
    t = await create(uid, b, "agent", ref)
    return f"Tugas dibuat: {t['id']} | {t['title']} | status: {t['status']}"


async def agent_comment(uid: str, src, task_id: str | None, text: str) -> str:
    t = await _need_task(uid, src, task_id)
    _need(t, tuple(s for s in MATRIX if s != "archived"), "Tugas yang diarsipkan tidak bisa diberi komentar")
    await _comment(t["id"], "bot", _text(text, "Komentar", COMMENT_MAX), (src or {}).get("bot_id"))
    return "Komentar ditambahkan."


async def agent_ask_user(uid: str, src: dict | None, question: str, task_id: str | None) -> str:
    """The question waits in Perlu Anda. On the task of the run it blocks that task; with no task (a normal chat or team
    discussion) a new task is made for it, remembering the chat so the answer can be posted back there."""
    q = _text(question, "Pertanyaan", COMMENT_MAX)
    t = await _agent_task(uid, src, task_id)
    if t:
        _need(t, ("running",), "Hanya tugas yang sedang dikerjakan yang bisa menunggu jawaban")
        await _comment(t["id"], "bot", q, (src or {}).get("bot_id"))
        await transition(t, "blocked", "agent", "ask_user", block_kind="needs_input", block_reason=first_line(q, 300), current_run_id=None)
        return "Question sent to the owner (card in Perlu Anda). Stop now and wait: the answer arrives as a new message."
    if not src or not (src.get("session_id") or src.get("group_id")):
        raise ApiError(409, "Tidak ada obrolan aktif untuk menaruh pertanyaan ini.")
    run = src.get("run_id")
    if run and (old := await db.q1("select id from tasks where user_id = %s and status = 'blocked' and source_ref->>'run_id' = %s", uid, run)):
        return f"Question already waiting in Perlu Anda (task {old['id']}). Wait for the owner's answer."
    gid = src.get("group_id")
    ref = {"ask": True, "bot_id": src["bot_id"], "run_id": run, **({"group_id": gid} if gid else {"session_id": src["session_id"]})}
    row = await db.q1("insert into tasks (user_id, title, body, assignee_bot, assignee_group, status, source, source_ref, block_kind, block_reason) "
                      "values (%s, %s, %s, %s, %s, 'blocked', 'chat', %s, 'needs_input', %s) returning id", uid, first_words(q), q,
                      None if gid else src["bot_id"], gid, Jsonb(ref), first_line(q, 300))
    await event(row["id"], "created", actor="agent", to="blocked")
    await _comment(row["id"], "bot", q, src["bot_id"])
    return f"Question sent to the owner (card in Perlu Anda, task {row['id']}). Stop now and wait: the answer arrives in this chat as a new message."


async def _answer_in_chat(uid: str, t: dict, actor: str, text: str) -> dict:
    """The owner's answer on an ask card: posted into the chat or team the question came from (the agent continues there),
    then the card is done. Posted first: if that fails (quota, busy), the card stays as it was."""
    ref = t["source_ref"]
    if ref.get("group_id"):
        await groups.send(uid, ref["group_id"], text, "queue")
    else:
        await engine.start_run(uid, ref["bot_id"], ref["session_id"], text, "chat")
    await _comment(t["id"], "user", text)
    return await transition(t, "done", actor, "reply", outcome="ok", completed_at=datetime.now(timezone.utc), block_kind=None,
                            block_reason=None, result=f"Dijawab: {text}")


async def _end(uid: str, src, task_id, to: str, summary: str, **fields) -> dict:
    t = await _need_task(uid, src, task_id)
    if t["kind"] == "plan":
        raise ApiError(409, "Rencana tidak diselesaikan lewat alat ini. Pakai task_cancel atau minta pemilik menyetujuinya.")
    return await transition(t, to, "agent", result=_text(summary, "Ringkasan", BODY_MAX), **fields)


async def agent_request_review(uid: str, src, task_id: str | None, summary: str) -> str:
    await _end(uid, src, task_id, "review", summary, block_kind="review", block_reason=None, current_run_id=None)
    return "Result sent to the owner for review."


async def agent_complete(uid: str, src, task_id: str | None, summary: str) -> str:
    await _end(uid, src, task_id, "done", summary, outcome="ok", completed_at=datetime.now(timezone.utc), block_kind=None, block_reason=None,
               current_run_id=None)
    return "Task marked done."


async def agent_cancel(uid: str, src, task_id: str, reason: str) -> str:
    """Archive (the owner can restore it): the owner asked for it in chat, so it needs no confirmation."""
    t = await _owned(uid, _task_uuid((task_id or "").strip()))
    await _verb_cancel(uid, t, "agent")
    if reason and reason.strip():
        await _comment(t["id"], "bot", _text(reason, "Alasan", COMMENT_MAX), (src or {}).get("bot_id"))
    return f"Task '{t['title']}' cancelled and archived."
