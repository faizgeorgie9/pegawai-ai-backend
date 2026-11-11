import pytest

from bff.bots import validate_edit
from bff.errors import ApiError
from bff.settings import clean_run_fields, clean_settings, merge_run_params
from bff import settings


def status(fn, *a):
    with pytest.raises(ApiError) as e:
        fn(*a)
    return e.value.status


def test_effort_values():
    for v in ("none", "minimal", "low", "medium", "high", "xhigh", None):
        assert clean_run_fields({"reasoning_effort": v}) == {"reasoning_effort": v}
    assert status(clean_run_fields, {"reasoning_effort": "ultra"}) == 400


def test_model_and_provider_travel_together():
    assert clean_run_fields({"model": "qwen3.8-flash", "provider": "opencode-go"}) == {"model": "qwen3.8-flash", "provider": "opencode-go"}
    assert clean_run_fields({"model": None, "provider": None}) == {"model": None, "provider": None}
    assert status(clean_run_fields, {"model": "qwen3.8-flash"}) == 400
    assert status(clean_run_fields, {"provider": "opencode-go"}) == 400
    assert status(clean_run_fields, {"model": "a b", "provider": "opencode-go"}) == 400
    assert status(clean_run_fields, {"model": "x", "provider": "Bad Provider"}) == 400


def test_builtin_bot_may_change_model_but_not_persona():
    assert validate_edit({"reasoning_effort": "low"}, True) == {"reasoning_effort": "low"}
    assert status(validate_edit, {"persona": "x"}, True) == 403


def test_run_params_only_what_the_bot_sets():
    own = {"model": "m-bot", "provider": "p-bot", "reasoning_effort": "low"}
    assert merge_run_params(own) == {"model": "m-bot", "provider": "p-bot", "model_options": {"reasoning_effort": "low"}}
    assert merge_run_params({"model": None, "provider": None, "reasoning_effort": "high"}) == {"model_options": {"reasoning_effort": "high"}}
    assert merge_run_params({}) == {}


def test_settings_patch_validation():
    assert clean_settings({"company_name": "  Colorbox   Co "}) == {"company_name": "Colorbox Co"}
    assert clean_settings({"notify": {"done": False}}) == {"notify": {"done": False}}
    assert status(clean_settings, {}) == 400
    assert status(clean_settings, {"company_name": " "}) == 400
    assert status(clean_settings, {"company_name": "x" * 41}) == 400
    assert status(clean_settings, {"language": "en"}) == 400
    assert status(clean_settings, {"timezone": "Mars/Base"}) == 400
    assert status(clean_settings, {"notify": {"done": "ya"}}) == 400
    assert status(clean_settings, {"bogus": 1}) == 400
    assert status(clean_settings, {"model": "x", "provider": "p"}) == 400  # model is per agent only


def test_profile_effort_reads_only_agent_reasoning_effort(monkeypatch):
    import tempfile
    from pathlib import Path

    tmp_path = Path(tempfile.mkdtemp())
    from bff import config

    monkeypatch.setattr(config, "HERMES_HOME", tmp_path)
    prof = tmp_path / "profiles" / "rian"
    prof.mkdir(parents=True)
    cfg = prof / "config.yaml"
    assert settings.profile_effort("rian") is None  # no file
    cfg.write_text("model: x\n", encoding="utf-8")
    assert settings.profile_effort("rian") == "medium"  # unset: Hermes documents medium
    cfg.write_text("agent:\n  reasoning_effort: ''\n", encoding="utf-8")
    assert settings.profile_effort("rian") == "medium"
    cfg.write_text("agent:\n  reasoning_effort: High\n", encoding="utf-8")
    assert settings.profile_effort("rian") == "high"
    cfg.write_text("agent:\n  reasoning_effort: bogus\n", encoding="utf-8")
    assert settings.profile_effort("rian") is None
