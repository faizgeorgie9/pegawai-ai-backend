"""Test setup shared by the BFF suite.

`JWT_SECRET` is set before bff.config is imported, so token signing works in tests without a .env value
(the value below is obviously a test fixture, never a deployment secret). `signed_in` gives endpoint tests
a real signed token; it replaces only the database session lookup, which these tests do not have.
"""
import os

os.environ["JWT_SECRET"] = "uji-jwt-secret-0123456789abcdef0123456789abcdef"

import pytest  # noqa: E402

from bff import auth, bridge  # noqa: E402

TEST_USER = {
    "id": "default",
    "name": "Pengguna Uji",
    "email": "uji@pegawai.ai",
    "role": "admin",
    "company": "Colorbox",
    "plan_id": "pro",
    "is_active": True,
}


@pytest.fixture(autouse=True)
def bridge_owner(monkeypatch):
    """MCP tool calls resolve an owner from the bot table. Unit tests have no database, so they stub it."""
    async def owner(_bot=None):
        return "default"

    monkeypatch.setattr(bridge, "resolve_owner", owner)


@pytest.fixture
def signed_in(monkeypatch):
    """Authorization header of a valid token, with the session row stubbed (no PostgreSQL in unit tests)."""
    async def load(_payload: dict) -> dict:
        return dict(TEST_USER)

    monkeypatch.setattr(auth, "load_user_for_token", load)
    token = auth.create_token(TEST_USER["id"], TEST_USER["email"], TEST_USER["role"], TEST_USER["name"])
    return {"Authorization": f"Bearer {token}"}
