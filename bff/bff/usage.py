"""Token usage views (side panel): totals, per-bot split and turn list for one conversation, and per-bot totals."""
from . import db

TURNS_LIMIT = 50
_COLS = "r.id, r.bot_id, r.created_at, r.input_tokens, r.output_tokens, r.cache_read_tokens, r.total_tokens, r.status"


def aggregate(rows: list[dict], names: dict[str, str]) -> dict:
    """rows: runs of one conversation (any order). Turns come back newest first, limited to TURNS_LIMIT."""
    total = {"input": 0, "output": 0, "cache_read": 0, "total": 0, "runs": 0}
    by_bot: dict[str, dict] = {}
    for r in rows:
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
    turns = sorted(rows, key=lambda r: r["created_at"], reverse=True)[:TURNS_LIMIT]
    return {"total": total,
            "by_bot": sorted(by_bot.values(), key=lambda b: b["total"], reverse=True),
            "turns": [{"run_id": r["id"], "bot_id": r["bot_id"], "created_at": r["created_at"],
                       "input": r["input_tokens"], "output": r["output_tokens"], "total": r["total_tokens"],
                       "status": r["status"]} for r in turns]}


async def conversation(user_id: str, session_id: str | None, group_id: str | None) -> dict:
    col, val = ("r.group_id", group_id) if group_id else ("r.session_id", session_id)
    rows = await db.q(f"select {_COLS} from runs r where r.user_id = %s and {col} = %s", user_id, val)
    names = {b["id"]: b["name"] for b in await db.q("select id, name from bots where user_id = %s", user_id)}
    return aggregate(rows, names)


async def per_bot(user_id: str, period: str) -> list[dict]:
    since = "and r.created_at >= date_trunc('month', now())" if period == "month" else ""
    return await db.q(
        "select b.id as bot_id, b.name, coalesce(sum(r.input_tokens), 0)::bigint as input, "
        "coalesce(sum(r.output_tokens), 0)::bigint as output, coalesce(sum(r.total_tokens), 0)::bigint as total, "
        f"count(r.id)::int as runs from bots b join runs r on r.bot_id = b.id and r.user_id = b.user_id {since} "
        "where b.user_id = %s group by b.id, b.name order by total desc", user_id)
