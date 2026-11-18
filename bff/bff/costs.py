"""USD cost of token usage, the monthly USD limit and its states.

cost of a run = (input x input price + output x output price + cache_read x cache price) / 1,000,000, with the prices of the
model that run used (table model_prices). input_tokens do NOT include cache reads (Hermes sends them separately; total = input +
output + cache read). Reasoning tokens: Hermes' run usage has no reasoning field, so they are inside output_tokens and billed at
the output price. Cache-write tokens are not stored (no listed model prices them here).

Money is Decimal end to end and summed exactly; rounding happens only when a label is made (usd_label): 0 is "$0", anything
under one cent is "< $0.01", the rest is rounded half up to cents. The API sends both the exact value (`usd`, a decimal string)
and the label.

A cost is an *estimate* ("perkiraan", basis "estimated") when any run in it used a price that is not verified, a model that was not
recorded on the run (resolved to the profile default instead), or a model with no price at all (counted as $0 and reported in
`unpriced_tokens`). Otherwise the basis is "measured".

Periods are calendar months in the user's workspace timezone."""
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from . import db, settings, versions

PEAK_HOURS = (1, 2, 3, 6, 7, 8, 9)  # UTC, Monday to Friday: the peak window of the price source
# Same rule in SQL, for grouping runs by price tier.
PEAK_SQL = ("(extract(isodow from r.created_at at time zone 'UTC') < 6 and "
            f"extract(hour from r.created_at at time zone 'UTC') in ({','.join(map(str, PEAK_HOURS))}))")
WARN_AT = Decimal("0.8")
ZERO = Decimal(0)
_PER = 6  # prices are per 10^6 tokens


def is_peak(at: datetime) -> bool:
    u = at.astimezone(timezone.utc)
    return u.weekday() < 5 and u.hour in PEAK_HOURS


def usd_label(x: Decimal) -> str:
    if x <= 0:
        return "$0"
    if x < Decimal("0.01"):
        return "< $0.01"
    return f"${x.quantize(Decimal('0.01'), ROUND_HALF_UP):,.2f}"


def money(x: Decimal | None) -> dict | None:
    return None if x is None else {"usd": format(x.normalize(), "f") if x else "0", "label": usd_label(x)}


def token_cost(inp: int, out: int, cache: int, price: dict, peak: bool) -> Decimal:
    off = not peak and price.get("off_peak_input_usd") is not None
    pi, po, pc = (price["off_peak_input_usd"], price["off_peak_output_usd"], price["off_peak_cache_read_usd"]) if off else \
        (price["input_usd"], price["output_usd"], price["cache_read_usd"])
    return (inp * Decimal(pi) + out * Decimal(po) + cache * Decimal(pc)).scaleb(-_PER)


class Pricer:
    """Prices token counts. prices: rows of model_prices. defaults: bot_id -> (model, provider) of the profile, used for runs
    that never recorded their model."""

    def __init__(self, prices: list[dict], defaults: dict[str, tuple[str, str]]):
        self.prices = {(p["provider"], p["model"]): p for p in prices}
        self.defaults = defaults

    def cost(self, bot_id: str, provider: str | None, model: str | None, peak: bool, inp: int, out: int, cache: int) -> dict:
        """{usd, model, provider, priced, estimated, why} where why is one of unverified_price, model_not_recorded, no_price, None."""
        recorded = bool(model and provider)
        if recorded:
            key = (provider, model)
        else:
            m, p = self.defaults.get(bot_id, (None, None))
            key = (p, m)
        price = self.prices.get(key)
        if price is None and key[0] == "opencode":
            price = self.prices.get(("opencode-go", key[1]))
        if price is None:
            return {"usd": ZERO, "model": key[1] or "tidak diketahui", "provider": key[0], "priced": False, "estimated": True,
                    "why": "no_price"}
        why = "unverified_price" if not price["verified"] else None if recorded else "model_not_recorded"
        return {"usd": token_cost(inp, out, cache, price, peak), "model": key[1], "provider": key[0], "priced": True,
                "estimated": why is not None, "why": why}


def limit_state(spent: Decimal, limit: Decimal | None) -> dict:
    """normal / warning (>= 80% of the limit) / exceeded (>= the limit). No limit: always normal, no remaining or percent."""
    if limit is None:
        return {"limit": None, "remaining": None, "percent": None, "state": "normal"}
    state = "exceeded" if spent >= limit else "warning" if spent >= limit * WARN_AT else "normal"
    return {"limit": money(limit), "remaining": money(max(ZERO, limit - spent)),
            "percent": 100 if limit <= 0 else int(spent * 100 / limit), "state": state}


def _basis(reasons: dict[str, set]) -> dict:
    return {"basis": "estimated" if reasons else "measured",
            "estimate_reasons": [{"code": c, "models": sorted(m)} for c, m in sorted(reasons.items())]}


def summarize(rows: list[dict], pricer: Pricer, names: dict[str, str], limit: Decimal | None) -> dict:
    """rows: runs grouped by (bot_id, provider, model, peak, day) with input/output/cache_read/total/runs sums."""
    tot = {"input": 0, "output": 0, "cache_read": 0, "total": 0, "runs": 0}
    spent, unpriced = ZERO, 0
    reasons: dict[str, set] = {}
    by_agent: dict[str, dict] = {}
    by_model: dict[tuple, dict] = {}
    by_day: dict = {}
    for r in rows:
        c = pricer.cost(r["bot_id"], r["provider"], r["model"], r["peak"], r["input"], r["output"], r["cache_read"])
        for k in tot:
            tot[k] += r[k]
        spent += c["usd"]
        if not c["priced"]:
            unpriced += r["total"]
        if c["why"]:
            reasons.setdefault(c["why"], set()).add(c["model"])
        a = by_agent.setdefault(r["bot_id"], {"bot_id": r["bot_id"], "name": names.get(r["bot_id"], r["bot_id"]), "usd": ZERO,
                                              "tokens": 0, "runs": 0, "estimated": False})
        m = by_model.setdefault((c["provider"], c["model"]), {"provider": c["provider"], "model": c["model"], "usd": ZERO,
                                                              "tokens": 0, "runs": 0, "estimated": False, "priced": c["priced"]})
        d = by_day.setdefault(r["day"], {"day": r["day"].isoformat(), "usd": ZERO, "tokens": 0, "runs": 0})
        for g in (a, m, d):
            g["usd"] += c["usd"]
            g["tokens"] += r["total"]
            g["runs"] += r["runs"]
        a["estimated"] |= c["estimated"]
        m["estimated"] |= c["estimated"]

    def out(g: dict) -> dict:
        return {k: v for k, v in g.items() if k != "usd"} | {"cost": money(g["usd"])}
    return {"currency": "USD", "cost": money(spent), "tokens": tot, "unpriced_tokens": unpriced,
            **limit_state(spent, limit), **_basis(reasons),
            "by_agent": [out(g) for g in sorted(by_agent.values(), key=lambda g: g["usd"], reverse=True)],
            "by_model": [out(g) for g in sorted(by_model.values(), key=lambda g: g["usd"], reverse=True)],
            "by_day": [out(by_day[k]) for k in sorted(by_day)]}


# ---------- database side ----------

_GROUPED = ("select r.bot_id, r.meta->>'provider' as provider, r.meta->>'model' as model, " + PEAK_SQL + " as peak, "
            "(r.created_at at time zone %s)::date as day, coalesce(sum(r.input_tokens), 0)::bigint as input, "
            "coalesce(sum(r.output_tokens), 0)::bigint as output, coalesce(sum(r.cache_read_tokens), 0)::bigint as cache_read, "
            "coalesce(sum(r.total_tokens), 0)::bigint as total, count(*)::int as runs "
            "from runs r where r.user_id = %s and r.created_at >= %s::timestamptz and r.created_at < %s::timestamptz "
            "group by 1, 2, 3, 4, 5")


async def pricer_for(bot_ids) -> Pricer:
    prices = await db.q("select * from model_prices")
    return Pricer(prices, {b: versions.model_of(b) for b in set(bot_ids)})


async def period(user_id: str) -> dict:
    """Start/end of the current month in the user's timezone, and now."""
    tz = (await settings.get(user_id))["timezone"]
    row = await db.q1("with l as (select date_trunc('month', now() at time zone %s) as s) "
                      "select l.s at time zone %s as start, (l.s + interval '1 month') at time zone %s as \"end\", now() as now from l",
                      tz, tz, tz)
    return {**row, "tz": tz}


async def grouped(user_id: str, tz: str, start, end) -> list[dict]:
    return await db.q(_GROUPED, tz, user_id, start, end)


async def month(user_id: str, limit: Decimal | None) -> dict:
    """The monthly view: cost, limit, remaining, percent, state, basis and the breakdowns by agent, model and day."""
    p = await period(user_id)
    rows = await grouped(user_id, p["tz"], p["start"], p["end"])
    names = {b["id"]: b["name"] for b in await db.q("select id, name from bots where user_id = %s", user_id)}
    s = summarize(rows, await pricer_for(r["bot_id"] for r in rows), names, limit)
    s["period"] = {"start": p["start"].isoformat(), "end": p["end"].isoformat(), "timezone": p["tz"]}
    s["updated_at"] = p["now"].isoformat()
    return s
