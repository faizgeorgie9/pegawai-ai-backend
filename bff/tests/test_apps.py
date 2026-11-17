"""Aplikasi: connector catalog parsing and names, id validation, per-agent skills (deny list stays enforced).
The Hermes CLI and gateway are mocked; nothing leaves the machine and no DB is needed."""
import asyncio

import pytest
from ruamel.yaml import YAML

from bff import apps, bots, harden, hermes
from bff.errors import ApiError

LIST_OUT = "clickup_mcp                not connected\nnotion                     connected\nzz_new_thing               not connected\nsentry_mcp                 not connected\n"
ACC_OUT = "notion  Kantor  active\nnotion  Pribadi (unnamed)  active\n"


def test_parse_list_and_accounts():
    assert apps.parse_list(LIST_OUT)[:2] == [("clickup_mcp", False), ("notion", True)]
    assert apps.parse_list("You have no connected accounts.\nbad line\n") == []
    assert apps.parse_accounts(ACC_OUT) == [("notion", "Kantor", "active"), ("notion", "Pribadi", "active")]
    assert apps.parse_accounts("You have no connected accounts.") == []


def test_names_categories_and_fallback():
    v = apps.app_view("clickup_mcp", False, [])
    assert (v["name"], v["category_name"], v["technical"]) == ("ClickUp", "Proyek & tugas", False)
    n = apps.app_view("notion", True, ["Kantor"])
    assert n["status"] == "connected" and n["accounts"] == ["Kantor"]
    z = apps.app_view("zz_new_thing", False, [])
    assert (z["name"], z["category"]) == ("Zz New Thing", "other")
    assert apps.app_view("sentry_mcp", False, [])["technical"] is True


def test_catalog_uses_cli_and_caches(monkeypatch):
    calls = []

    def fake(args, timeout=0):
        calls.append(args[1])
        return 0, (LIST_OUT if args[1] == "list" else ACC_OUT), ""
    monkeypatch.setattr(apps, "_run", fake)
    apps.invalidate()
    apps._cache["rows"] = None
    rows = asyncio.run(apps.catalog())
    assert [r["id"] for r in rows][:2] == ["clickup_mcp", "notion"]
    asyncio.run(apps.catalog())
    assert sorted(calls) == ["accounts", "list"]  # second call served from the cache


@pytest.mark.parametrize("bad", ["", "../x", "a b", "Notion", "x;rm", "a" * 70])
def test_bad_ids_rejected(bad):
    with pytest.raises(ApiError) as e:
        apps._check_id(bad)
    assert e.value.status == 404


def test_visible_skills_hides_blocked_toolsets():
    rows = [{"name": n, "label": n, "description": "", "enabled": True} for n in
            ["web", "terminal", "file", "code_execution", "browser", "computer_use", "cronjob", "delegation", "clarify", "discord", "skills", "memory"]]
    out = {s["name"]: s for s in apps.visible_skills(rows)}
    assert set(out) == {"web", "skills", "memory"}
    assert out["skills"]["technical"] and not out["web"]["technical"]
    assert not set(out) & harden.DENY


def test_apply_toolset_keeps_deny_out_and_clarify_in():
    assert apps.apply_toolset(["web", "terminal"], "memory", True) == ["web", "memory", "clarify"]
    assert apps.apply_toolset(["web", "memory", "clarify"], "web", False) == ["memory", "clarify"]


def test_set_skill_writes_config_and_refuses_blocked(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("model: x\nplatform_toolsets:\n  api_server:\n  - web\n  - clarify\n", encoding="utf-8")
    state = {"rows": [{"name": n, "enabled": n in ("web", "clarify")} for n in ("web", "memory", "terminal", "clarify")]}

    async def get_bot(u, s):
        return {"id": s}

    async def rows(slug):
        t = YAML().load(cfg.read_text(encoding="utf-8"))["platform_toolsets"]["api_server"]
        return [{"name": r["name"], "enabled": r["name"] in t} for r in state["rows"]]
    monkeypatch.setattr(bots, "get_bot", get_bot)
    monkeypatch.setattr(hermes, "profile_dir", lambda s: tmp_path)
    monkeypatch.setattr(apps, "_gateway_rows", rows)
    out = asyncio.run(apps.set_skill("u", "budi", "memory", True))
    assert {s["name"]: s["enabled"] for s in out} == {"web": True, "memory": True}
    assert YAML().load(cfg.read_text(encoding="utf-8"))["model"] == "x"
    out = asyncio.run(apps.set_skill("u", "budi", "memory", False))
    assert {s["name"]: s["enabled"] for s in out}["memory"] is False
    for blocked in ("terminal", "clarify", "../x"):
        with pytest.raises(ApiError) as e:
            asyncio.run(apps.set_skill("u", "budi", blocked, True))
        assert e.value.status == 400
    with pytest.raises(ApiError) as e:
        asyncio.run(apps.set_skill("u", "budi", "nonexistent", True))
    assert e.value.status == 404
