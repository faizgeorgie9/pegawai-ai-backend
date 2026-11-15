"""Token and USD usage views (side panel): totals, per-bot split and turn list for one conversation, per-bot totals and the
monthly account view. Cost math lives in costs.py (see its docstring for the estimate rule)."""
from decimal import Decimal

from . import costs, db

TURNS_LIMIT = 50
_COLS = ("r.id, r.bot_id, r.created_at, r.input_tokens, r.output_tokens, r.cache_read_tokens, r.total_tokens, r.status, "
         f"r.meta->>'provider' as provider, r.meta->>'model' as model, {costs.PEAK_SQL} as peak")


def _cost(r: dict, pricer: costs.Pricer) -> dict:
    return pricer.cost(r["bot_id"], r.get("provider"), r.get("model"), r.get("peak", False), r["input_tokens"],
                       r["output_tokens"], r["cache_read_tokens"])


def aggregate(rows: list[dict], names: dict[str, str], pricer: costs.Pricer | None = None) -> dict:
    """rows: runs of one conversation (any order). Turns come back newest first, limited to TURNS_LIMIT. With a pricer every
    total, bot and turn also carries its USD cost, and the result says whether it is measured or estimated."""
    total = {"input": 0, "output": 0, "cache_read": 0, "total": 0, "runs": 0}
    by_bot: dict[str, dict] = {}
    spent, reasons, cost_of = costs.ZERO, {}, {}
    for r in rows:
        if pricer:
            c = cost_of[r["id"]] = _cost(r, pricer)
            spent += c["usd"]
            if c["why"]:
                reasons.setdefault(c["why"], set()).add(c["model"])
        total["input"] += r["input_tokens"]
        total["output"] += r["output_tokens"]
        total["cache_read"] += r["cache_read_tokens"]
        total["total"] += r["total_tokens"]
        total["runs"] += 1
        b = by_bot.setdefault(r["bot_id"], {"bot_id": r["bot_id"], "name": names.get(r["bot_id"], r["bot_id"]),
                                            "input": 0, "output": 0, "total": 0, "runs": 0})
        b["input"] += r["input_tokens"]
        b["output"] += r["output_tokens"]
        b["total"] += r["total_tokens"]
        b["runs"] += 1
        if pricer:
            b["_usd"] = b.get("_usd", costs.ZERO) + c["usd"]
            b["estimated"] = b.get("estimated", False) or c["estimated"]
    turns = sorted(rows, key=lambda r: r["created_at"], reverse=True)[:TURNS_LIMIT]
    out = {"total": total,
           "by_bot": sorted(by_bot.values(), key=lambda b: b["total"], reverse=True),
           "turns": [{"run_id": r["id"], "bot_id": r["bot_id"], "created_at": r["created_at"],
                      "input": r["input_tokens"], "output": r["output_tokens"], "total": r["total_tokens"],
                      "status": r["status"], **({"cost": costs.money(cost_of[r["id"]]["usd"]), "estimated": cost_of[r["id"]]["estimated"]}
                                                if pricer else {})} for r in turns]}
    if pricer:
        for b in out["by_bot"]:
            b["cost"] = costs.money(b.pop("_usd"))
        out.update(currency="USD", cost=costs.money(spent), **costs._basis(reasons))
    return out


async def conversation(user_id: str, session_id: str | None, group_id: str | None, limit: Decimal | None) -> dict:
    col, val = ("r.group_id", group_id) if group_id else ("r.session_id", session_id)
    rows = await db.q(f"select {_COLS} from runs r where r.user_id = %s and {col} = %s", user_id, val)
    names = {b["id"]: b["name"] for b in await db.q("select id, name from bots where user_id = %s", user_id)}
    d = aggregate(rows, names, await costs.pricer_for(r["bot_id"] for r in rows))
    m = await costs.month(user_id, limit)  # the month block lets the panel show the limit next to this conversation
    d["month"] = {k: m[k] for k in ("cost", "limit", "remaining", "percent", "state", "basis")}
    return d


async def per_bot(user_id: str, period: str) -> list[dict]:
    """Per-bot token totals plus USD cost (and whether it is an estimate), biggest first."""
    if period == "month":
        p = await costs.period(user_id)
        rows = await costs.grouped(user_id, p["tz"], p["start"], p["end"])
    else:
        rows = await costs.grouped(user_id, "UTC", "-infinity", "infinity")
    names = {b["id"]: b["name"] for b in await db.q("select id, name from bots where user_id = %s", user_id)}
    pricer = await costs.pricer_for(r["bot_id"] for r in rows)
    out: dict[str, dict] = {}
    for r in rows:
        if r["bot_id"] not in names:  # runs of a bot that no longer exists have no row to show
            continue
        c = pricer.cost(r["bot_id"], r["provider"], r["model"], r["peak"], r["input"], r["output"], r["cache_read"])
        b = out.setdefault(r["bot_id"], {"bot_id": r["bot_id"], "name": names[r["bot_id"]], "input": 0, "output": 0, "total": 0,
                                         "runs": 0, "_usd": costs.ZERO, "estimated": False})
        b["input"] += r["input"]
        b["output"] += r["output"]
        b["total"] += r["total"]
        b["runs"] += r["runs"]
        b["_usd"] += c["usd"]
        b["estimated"] |= c["estimated"]
    return [{**{k: v for k, v in b.items() if k != "_usd"}, "cost": costs.money(b["_usd"])}
            for b in sorted(out.values(), key=lambda b: b["total"], reverse=True)]
