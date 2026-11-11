import pytest

from bff.bots import validate_edit
from bff.errors import ApiError
from bff.settings import clean_run_fields, clean_settings, merge_run_params


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


def test_run_params_bot_wins_then_workspace_then_nothing():
    ws = {"model": "m-ws", "provider": "p-ws", "reasoning_effort": "high"}
    own = {"model": "m-bot", "provider": "p-bot", "reasoning_effort": "low"}
    assert merge_run_params(own, ws) == {"model": "m-bot", "provider": "p-bot", "model_options": {"reasoning_effort": "low"}}
    assert merge_run_params({}, ws) == {"model": "m-ws", "provider": "p-ws", "model_options": {"reasoning_effort": "high"}}
    # model from the bot, effort falls back to the workspace
    assert merge_run_params({"model": "m-bot", "provider": "p-bot", "reasoning_effort": None}, ws)["model_options"] == {"reasoning_effort": "high"}
    assert merge_run_params({}, {"model": None, "provider": None, "reasoning_effort": None}) == {}


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
