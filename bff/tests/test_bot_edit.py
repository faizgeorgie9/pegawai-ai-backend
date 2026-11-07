import pytest

from bff.bots import validate_edit
from bff.errors import ApiError


def status(body, builtin=False):
    with pytest.raises(ApiError) as e:
        validate_edit(body, builtin)
    return e.value.status


def test_returns_only_given_fields_trimmed():
    assert validate_edit({"role": "  Analis   data "}, False) == {"role": "Analis data"}
    assert validate_edit({"name": "Tes Edit", "color": "teal", "persona": " Teliti. "}, False) == {
        "name": "Tes Edit", "color": "teal", "persona": "Teliti."}


def test_same_limits_as_create():
    assert status({"name": ""}) == 400
    assert status({"role": "x" * 41}) == 400
    assert status({"team": 5}) == 400
    assert status({"name": "!!!"}) == 400  # no letters or digits: no slug
    assert status({"color": "pink"}) == 400
    assert status({"persona": "   "}) == 400
    assert status({"persona": "x" * 2001}) == 400


def test_empty_and_unknown_fields():
    assert status({}) == 400
    assert status({"id": "x"}) == 400
    assert status({"builtin": True}) == 400


def test_builtin_only_colour():
    assert validate_edit({"color": "sky"}, True) == {"color": "sky"}
    assert status({"name": "Baru"}, True) == 403
    assert status({"color": "sky", "role": "Lain"}, True) == 403
    assert status({"color": "pink"}, True) == 400
