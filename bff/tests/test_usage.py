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
