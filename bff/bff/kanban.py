"""Kanban board: our own real work (runs, sequences, scheduler occurrences, plans waiting for approval) mapped to four columns
that reuse Hermes' status words: todo (Antre), running (Berjalan), blocked (Perlu tindakan), done (Selesai). Failed and cancelled
work stays in `done` with an `outcome` tag. Nothing is stored: every card is built from existing tables at request time.
Hermes' own Kanban is an optional, read-only second source (`hermes kanban list --json`); we never enable its dispatcher or tools
(workers it spawns would run outside the BFF, so their cost and stop would not be tracked)."""
import asyncio
import json
import re
import subprocess
import time
from datetime import datetime, timezone

from . import config, costs, db, engine, plan_schema, usage

COLUMNS = [("todo", "Menunggu"), ("running", "Berjalan"), ("blocked", "Perlu tindakan"), ("done", "Selesai")]
PERIOD_DAYS = {"today": 1, "7d": 7, "30d": 30}
PER_COLUMN = 40  # cards sent per column; `total` says how many matched
AHEAD_DAYS = 7  # planned occurrences further away are not on the board yet
HERMES_TTL, HERMES_WAIT, HERMES_CLI_TIMEOUT = 20.0, 1.5, 30.0  # seconds: cache life, how long a request waits for the CLI, CLI limit

# (column, outcome) per state. outcome: ok | failed | cancelled | None (not finished)
RUN = {"queued": ("todo", None), "running": ("running", None), "completed": ("done", "ok"), "failed": ("done", "failed"),
       "cancelled": ("done", "cancelled"), "interrupted": ("done", "failed")}
OCC = {"planned": ("todo", None), "running": ("running", None), "done": ("done", "ok"), "skipped": ("blocked", None),
       "failed": ("done", "failed"), "cancelled": ("done", "cancelled")}
SEQ = {"queued": ("todo", None), "running": ("running", None), "completed": ("done", "ok"), "failed": ("done", "failed"),
       "stopped": ("done", "cancelled")}
HERMES = {"triage": "todo", "todo": "todo", "ready": "todo", "scheduled": "todo", "running": "running", "blocked": "blocked",
          "review": "blocked", "done": "done"}  # archived is not shown
WAITING = {"clarify": "Menunggu jawaban Anda", "approval": "Menunggu persetujuan Anda"}


def place(table: dict, status: str, waiting: str | None = None, paused: bool = False) -> tuple[str, str | None, str | None]:
    """(column, outcome, note) for a state. A running item that waits on the user, and a planned occurrence of a paused schedule,
    need the user: they go to `blocked`."""
    col, outcome = table.get(status, ("done", "failed"))
    if col == "running" and waiting:
        return "blocked", None, WAITING[waiting]
    if table is OCC and status == "planned" and paused:
        return "blocked", None, "Jadwal dijeda"
    return col, outcome, None


def waiting_of(run_id) -> str | None:
    lv = engine.LIVE.get(str(run_id)) if run_id else None
    return "clarify" if lv and lv.clarify else "approval" if lv and lv.approval else None


def first_line(text: str | None, n: int = 90) -> str:
    line = next((x.strip() for x in (text or "").splitlines() if x.strip()), "")
    line = re.sub(r"^User:\s*", "", line)
    return line if len(line) <= n else line[: n - 1].rstrip() + "…"


def _link(r: dict) -> str:
    o = r.get("origin") or {}
    if r["group_id"]:
        return f"/grup/{r['group_id']}"
    if o.get("type") == "evaluasi":
        return "/uji" + (f"?case={o['case_id']}" if o.get("case_id") else "")
    if o.get("type") in ("cs", "marketing"):
        return "/cs" if o["type"] == "cs" else "/marketing"
    return f"/chat/{r['bot_id']}/{r['session_id']}"


def card(key: str, source: str, title: str, col: tuple, at, agents: list, group: dict | None, link: str | None,
         cost: tuple = (None, False), note: str | None = None) -> dict:
    column, outcome, wait_note = col
    return {"key": key, "source": source, "title": title or "(tanpa judul)", "column": column, "outcome": outcome,
            "note": wait_note or note, "agents": agents, "group": group, "at": at, "link": link, "cost": cost[0],
            "estimated": cost[1]}


# ---------- our own work ----------

async def _costs(rows: list[dict]) -> dict[str, dict]:
    ids = list({str(i) for r in rows for i in r["run_ids"]})
    if not ids:
        return {}
    runs = await db.q(f"select {usage._COLS} from runs r where r.id = any(%s::uuid[])", ids)
    pricer = await costs.pricer_for(r["bot_id"] for r in runs)
    return {str(r["id"]): usage._cost(r, pricer) for r in runs}


def _cost(run_ids, info: dict[str, dict], finished: bool) -> tuple[dict | None, bool]:
    cs = [info[str(i)] for i in run_ids if str(i) in info]
    if not cs or not finished:
        return None, False
    return costs.money(sum((c["usd"] for c in cs), costs.ZERO)), any(c["estimated"] for c in cs)


async def own_cards(uid: str, days: int, agent: str | None, group: str | None) -> list[dict]:
    bots = {b["id"]: {"id": b["id"], "name": b["name"], "color": b["color"]} for b in await db.q("select id, name, color from bots where user_id = %s", uid)}
    groups = {str(g["id"]): {"id": str(g["id"]), "name": g["name"]} for g in await db.q("select id, name from groups where user_id = %s", uid)}

    def who(ids):
        return [bots.get(b) or {"id": b, "name": b, "color": "slate"} for b in ids]

    cards: list[dict] = []

    # runs that belong to a sequence or an occurrence are shown through that card, not on their own
    runs = await db.q(f"select {usage._COLS}, r.group_id, r.session_id, r.kind, r.started_at, r.finished_at, r.error, "
                      "left(r.input, 400) as input, r.meta->'origin' as origin from runs r where r.user_id = %s "
                      "and r.meta->'origin'->>'sequence_id' is null and not exists (select 1 from schedule_occurrences o "
                      "where o.user_id = r.user_id and o.run_ids ? r.id::text) "
                      "and (r.created_at >= now() - make_interval(days => %s) or r.status = any(%s)) "
                      "and (%s::text is null or r.bot_id = %s) and (%s::uuid is null or r.group_id = %s) "
                      "order by r.created_at desc limit 300", uid, days, list(engine.ACTIVE), agent, agent, group, group)
    pricer = await costs.pricer_for(r["bot_id"] for r in runs)
    for r in runs:
        col = place(RUN, r["status"], waiting_of(r["id"]))
        gid = str(r["group_id"]) if r["group_id"] else None
        c = usage._cost(r, pricer)
        note = r["error"] if col[1] == "failed" and r["error"] else "Terputus karena server dimulai ulang" if r["status"] == "interrupted" else None
        cards.append(card(f"run:{r['id']}", "group" if gid else "chat", first_line(r["input"]), col,
                          r["finished_at"] or r["started_at"] or r["created_at"], who([r["bot_id"]]),
                          groups.get(gid) if gid else None, _link(r),
                          (costs.money(c["usd"]), c["estimated"]) if col[0] == "done" else (None, False), note))

    occs = await db.q("select o.id, o.planned_at, o.title, o.brief, o.status, o.skip_reason, o.targets, o.run_ids, o.started_at, o.finished_at, "
                      "s.title as stitle, s.bot_id as sbot, s.group_id as sgroup, s.status as sstatus from schedule_occurrences o "
                      "join schedules s on s.id = o.schedule_id where o.user_id = %s and ((o.status = 'planned' and o.planned_at < "
                      "now() + make_interval(days => %s)) or o.status = 'running' or coalesce(o.finished_at, o.planned_at) >= "
                      "now() - make_interval(days => %s)) and (%s::text is null or s.bot_id = %s or o.targets ? %s) "
                      "and (%s::uuid is null or s.group_id = %s) order by o.planned_at desc limit 400",
                      uid, AHEAD_DAYS, days, agent, agent, agent, group, group)
    info = await _costs(occs)
    for o in occs:
        gid = str(o["sgroup"]) if o["sgroup"] else None
        col = place(OCC, o["status"], waiting_of(o["run_ids"][-1] if o["run_ids"] else None), o["sstatus"] == "paused")
        waiting_for_time = o["status"] == "planned"
        at = o["planned_at"] if waiting_for_time else o["finished_at"] or o["started_at"] or o["planned_at"]
        cards.append(card(f"occ:{o['id']}", "schedule", o["title"] or o["stitle"], col, at,
                          who(o["targets"] or ([o["sbot"]] if o["sbot"] else [])), groups.get(gid) if gid else None, "/scheduler",
                          _cost(o["run_ids"], info, o["status"] != "running"),
                          o["skip_reason"] if o["status"] in ("skipped", "failed", "cancelled") else None))

    seqs = await db.q("select id, bot_id, origin, turns, status, error, run_ids, created_at, updated_at from sequences where user_id = %s "
                      "and (status in ('queued', 'running') or updated_at >= now() - make_interval(days => %s)) "
                      "and (%s::text is null or bot_id = %s) and %s::uuid is null order by created_at desc limit 100",
                      uid, days, agent, agent, group)
    sinfo = await _costs(seqs)
    for s in seqs:
        col = place(SEQ, s["status"], waiting_of(s["run_ids"][-1] if s["run_ids"] else None))
        case = (s["origin"] or {}).get("case_id")
        first = first_line(s["turns"][0], 70)
        cards.append(card(f"seq:{s['id']}", "sequence", f"Evaluasi {case}: {first}" if case else first, col, s["updated_at"],
                          who([s["bot_id"]]), None, "/uji" + (f"?case={case}" if case else ""),
                          _cost(s["run_ids"], sinfo, s["status"] not in ("queued", "running")), s["error"]))

    # the newest plan of each group, when nobody approved it yet, waits for the user
    if not agent:
        msgs = await db.q("select m.id, m.group_id, m.text, m.created_at from group_messages m join groups g on g.id = m.group_id "
                          "where g.user_id = %s and g.deleted_at is null and m.author = 'bot' and m.text like '%%\"plan\"%%' "
                          "and m.created_at >= now() - make_interval(days => %s) and (%s::uuid is null or m.group_id = %s) "
                          "order by m.id desc limit 100", uid, days, group, group)
        approved = {r["source_message_id"] for r in await db.q(
            "select source_message_id from schedules where user_id = %s and source_message_id is not null", uid)}
        seen: set = set()
        for m in msgs:
            if m["group_id"] in seen:
                continue
            plan, _ = plan_schema.parse(m["text"])
            if not plan:
                continue
            seen.add(m["group_id"])
            if m["id"] not in approved:
                cards.append(card(f"plan:{m['id']}", "plan", plan["title"], ("blocked", None, "Rencana menunggu persetujuan Anda"),
                                  m["created_at"], [], groups.get(str(m["group_id"])), f"/grup/{m['group_id']}",
                                  note=f"{len(plan['days'])} hari"))
    return cards


# ---------- Hermes' own Kanban (read-only, optional) ----------

def _when(v) -> datetime | None:
    if isinstance(v, (int, float)) and v > 0:
        return datetime.fromtimestamp(v / 1000 if v > 1e12 else v, timezone.utc)
    if isinstance(v, str):
        try:
            d = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def parse_hermes(text: str, uid: str) -> list[dict]:
    """Cards from the JSON of `hermes kanban list --json`. Strict on the owner: only tasks whose `tenant` is this user are shown
    (the CLI is asked to filter too, but the board never trusts that). Unknown shapes give no cards."""
    data = json.loads(text)
    items = data.get("tasks", []) if isinstance(data, dict) else data
    out = []
    for t in items if isinstance(items, list) else []:
        if not isinstance(t, dict) or t.get("tenant") != uid or t.get("status") not in HERMES or not isinstance(t.get("title"), str):
            continue
        col = HERMES[t["status"]]
        at = next((w for w in (_when(t.get(k)) for k in ("completed_at", "updated_at", "created_at")) if w), None)
        who = t.get("assignee") if isinstance(t.get("assignee"), str) and t["assignee"] else None
        out.append(card(f"hermes:{t.get('id')}", "hermes", first_line(t["title"]), (col, "ok" if col == "done" else None, None), at,
                        [{"id": who, "name": who, "color": "slate"}] if who else [], None, None))
    return out


def _run_cli(uid: str) -> str:
    # a thread, not asyncio.create_subprocess_exec: the Windows selector loop the BFF runs on has no subprocess support
    r = subprocess.run([*config.HERMES_KANBAN_CMD, "--tenant", uid], capture_output=True, text=True, timeout=HERMES_CLI_TIMEOUT, check=True)
    return r.stdout


_CACHE: dict[str, dict] = {}  # user id -> {at, state, cards}
_REFRESH: dict[str, asyncio.Task] = {}


async def _refresh(uid: str) -> None:
    """Never raises: a missing CLI, a timeout or odd output is state `unavailable` with no cards."""
    try:
        cards = parse_hermes(await asyncio.to_thread(_run_cli, uid), uid)
        _CACHE[uid] = {"at": time.monotonic(), "state": "ok", "cards": cards}
    except Exception:
        _CACHE[uid] = {"at": time.monotonic(), "state": "unavailable", "cards": []}


async def hermes_section(uid: str) -> dict:
    """{state: ok|unavailable|pending, cards}. Cached for HERMES_TTL; a request waits at most HERMES_WAIT for a fresh read
    (the CLI starts slowly) and otherwise answers with what it has while the CLI finishes in the background."""
    c = _CACHE.get(uid)
    if c and time.monotonic() - c["at"] < HERMES_TTL:
        return c
    t = _REFRESH.get(uid)
    if not t or t.done():
        t = _REFRESH[uid] = asyncio.create_task(_refresh(uid))
    try:
        await asyncio.wait_for(asyncio.shield(t), HERMES_WAIT)
    except asyncio.TimeoutError:
        pass
    return _CACHE.get(uid) or {"state": "pending", "cards": []}


# ---------- the board ----------

def board(cards: list[dict]) -> list[dict]:
    """Group cards into the columns: Antre soonest first, the others newest first, at most PER_COLUMN each."""
    floor = datetime.min.replace(tzinfo=timezone.utc)
    out = []
    for cid, label in COLUMNS:
        mine = sorted((c for c in cards if c["column"] == cid), key=lambda c: c["at"] or floor, reverse=cid != "todo")
        out.append({"id": cid, "label": label, "total": len(mine), "cards": mine[:PER_COLUMN]})
    return out


async def get(uid: str, agent: str | None, group: str | None, period: str) -> dict:
    cards = await own_cards(uid, PERIOD_DAYS[period], agent, group)
    h = await hermes_section(uid)
    # Hermes tasks have no group; its assignee is a profile name, which is our agent id
    hc = [] if group else [c for c in h["cards"] if not agent or any(a["id"] == agent for a in c["agents"])]
    return {"columns": board(cards + hc), "hermes": {"state": h["state"], "count": len(hc)}, "period": period}
