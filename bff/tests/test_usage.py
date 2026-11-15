from datetime import datetime, timedelta

from bff.usage import TURNS_LIMIT, aggregate


def run(i, bot, inp, out, cache=0, status="completed"):
    return {"id": f"r{i}", "bot_id": bot, "created_at": datetime(2026, 11, 4) + timedelta(minutes=i),
            "input_tokens": inp, "output_tokens": out, "cache_read_tokens": cache,
            "total_tokens": inp + out, "status": status}


def test_totals_and_split_per_bot():
    rows = [run(1, "rian", 100, 20, 50), run(2, "diana", 300, 40), run(3, "rian", 10, 5)]
    d = aggregate(rows, {"rian": "Rian", "diana": "Diana"})
    assert d["total"] == {"input": 410, "output": 65, "cache_read": 50, "total": 475, "runs": 3}
    assert [b["bot_id"] for b in d["by_bot"]] == ["diana", "rian"]  # biggest first
    assert d["by_bot"][1] == {"bot_id": "rian", "name": "Rian", "input": 110, "output": 25, "total": 135, "runs": 2}


def test_turns_newest_first_and_limited():
    rows = [run(i, "rian", 1, 1) for i in range(TURNS_LIMIT + 5)]
    d = aggregate(rows, {})
    assert len(d["turns"]) == TURNS_LIMIT
    assert d["turns"][0]["run_id"] == f"r{TURNS_LIMIT + 4}"
    assert d["total"]["runs"] == TURNS_LIMIT + 5  # totals cover every run, not only the listed turns


def test_empty():
    d = aggregate([], {})
    assert d["total"]["total"] == 0 and d["by_bot"] == [] and d["turns"] == []


# ---------- USD cost and limit ----------
from datetime import date, timezone
from decimal import Decimal as D

import pytest

from bff import costs
from bff.costs import Pricer, is_peak, limit_state, money, summarize, token_cost, usd_label

FLASH = {"provider": "opencode-go", "model": "deepseek-v4.1-flash", "verified": True,
         "input_usd": D("0.30"), "output_usd": D("1.20"), "cache_read_usd": D("0.006"),
         "off_peak_input_usd": D("0.15"), "off_peak_output_usd": D("0.60"), "off_peak_cache_read_usd": D("0.003")}
TIERED = {"provider": "opencode-go", "model": "grok-4.7", "verified": False, "input_usd": D("2"), "output_usd": D("6"),
          "cache_read_usd": D("0.5"), "off_peak_input_usd": None, "off_peak_output_usd": None, "off_peak_cache_read_usd": None}
PRICER = Pricer([FLASH, TIERED], {"rian": ("deepseek-v4.1-flash", "opencode-go")})


def test_cost_is_exact_and_cache_is_priced_separately():
    # 274 in x 0.30 + 26 out x 1.20 + 22144 cache x 0.006, per 1M tokens (the real shape of a Hermes run: total = in + out + cache)
    assert token_cost(274, 26, 22144, FLASH, peak=True) == D("0.0000822") + D("0.0000312") + D("0.000132864")
    assert token_cost(274, 26, 22144, FLASH, peak=True) == D("0.000246264")
    assert token_cost(1_000_000, 0, 0, FLASH, peak=True) == D("0.30")  # no float noise


def test_off_peak_rate_and_peak_window():
    assert token_cost(1_000_000, 1_000_000, 1_000_000, FLASH, peak=False) == D("0.753")
    assert token_cost(1_000_000, 1_000_000, 1_000_000, TIERED, peak=False) == D("8.5")  # no off-peak rate: same price
    mon = lambda h: datetime(2026, 11, 16, h, 30, tzinfo=timezone.utc)  # a Monday
    assert [is_peak(mon(h)) for h in (0, 1, 3, 4, 5, 6, 9, 10)] == [False, True, True, False, False, True, True, False]
    assert not is_peak(datetime(2026, 11, 15, 2, 0, tzinfo=timezone.utc))  # Sunday


def test_display_rounding_rule():
    assert usd_label(D(0)) == "$0"
    assert usd_label(D("0.000246")) == "< $0.01"
    assert usd_label(D("0.01")) == "$0.01"
    assert usd_label(D("0.0149")) == "$0.01" and usd_label(D("0.015")) == "$0.02"  # half up to cents
    assert usd_label(D("1234.5")) == "$1,234.50"
    assert money(D("0.0000820")) == {"usd": "0.000082", "label": "< $0.01"}  # the exact value is never rounded
    assert money(None) is None


def test_estimated_when_price_unverified_unrecorded_or_missing():
    ok = PRICER.cost("rian", "opencode-go", "deepseek-v4.1-flash", True, 1000, 100, 0)
    assert ok["priced"] and not ok["estimated"] and ok["why"] is None
    assert PRICER.cost("rian", "opencode-go", "grok-4.7", True, 1, 1, 0)["why"] == "unverified_price"
    unrec = PRICER.cost("rian", None, None, True, 1000, 100, 0)  # model never recorded: the profile default, as an estimate
    assert unrec["model"] == "deepseek-v4.1-flash" and unrec["usd"] == ok["usd"] and unrec["why"] == "model_not_recorded"
    gone = PRICER.cost("rian", "opencode-go", "mystery-1", True, 1000, 100, 0)
    assert not gone["priced"] and gone["usd"] == 0 and gone["estimated"] and gone["why"] == "no_price"


def grp(bot, model, day, inp, out, cache=0, peak=True, runs=1, provider="opencode-go"):
    return {"bot_id": bot, "provider": provider, "model": model, "peak": peak, "day": day, "input": inp, "output": out,
            "cache_read": cache, "total": inp + out + cache, "runs": runs}


def test_summary_breakdowns_basis_and_limit():
    rows = [grp("rian", "deepseek-v4.1-flash", date(2026, 11, 4), 1_000_000, 0),
            grp("diana", "deepseek-v4.1-flash", date(2026, 11, 5), 0, 1_000_000, peak=False),
            grp("diana", "mystery-1", date(2026, 11, 5), 500, 500)]
    s = summarize(rows, PRICER, {"rian": "Rian", "diana": "Diana"}, D("2"))
    assert s["cost"]["usd"] == "0.9" and s["currency"] == "USD"  # 0.30 + 0.60
    assert s["percent"] == 45 and s["state"] == "normal" and s["remaining"]["usd"] == "1.1"
    assert s["unpriced_tokens"] == 1000
    assert s["basis"] == "estimated" and s["estimate_reasons"] == [{"code": "no_price", "models": ["mystery-1"]}]
    assert [a["name"] for a in s["by_agent"]] == ["Diana", "Rian"] and s["by_agent"][0]["cost"]["usd"] == "0.6"
    assert [d["day"] for d in s["by_day"]] == ["2026-11-04", "2026-11-05"]
    assert {m["model"] for m in s["by_model"]} == {"deepseek-v4.1-flash", "mystery-1"}
    assert s["tokens"]["runs"] == 3


def test_summary_empty_is_measured_zero_and_no_limit():
    s = summarize([], PRICER, {}, None)
    assert s["cost"] == {"usd": "0", "label": "$0"} and s["basis"] == "measured"
    assert s["limit"] is None and s["remaining"] is None and s["percent"] is None and s["state"] == "normal"
    assert s["by_agent"] == s["by_model"] == s["by_day"] == []


@pytest.mark.parametrize("spent,state,pct", [("0", "normal", 0), ("7.99", "normal", 79), ("8", "warning", 80),
                                             ("9.99", "warning", 99), ("10", "exceeded", 100), ("12.5", "exceeded", 125)])
def test_limit_states(spent, state, pct):
    s = limit_state(D(spent), D("10"))
    assert (s["state"], s["percent"]) == (state, pct)
    assert D(s["remaining"]["usd"]) == max(D(0), D("10") - D(spent))


def test_limit_zero_is_exceeded_and_none_is_unlimited():
    assert limit_state(D(0), D(0))["state"] == "exceeded"
    assert limit_state(D("1000000"), None) == {"limit": None, "remaining": None, "percent": None, "state": "normal"}


def test_conversation_aggregate_with_cost():
    r = run(1, "rian", 1_000_000, 0)
    r.update(provider="opencode-go", model="deepseek-v4.1-flash", peak=True)
    d = aggregate([r], {"rian": "Rian"}, PRICER)
    assert d["cost"]["usd"] == "0.3" and d["basis"] == "measured"
    assert d["by_bot"][0]["cost"]["usd"] == "0.3" and d["turns"][0]["cost"]["usd"] == "0.3"
