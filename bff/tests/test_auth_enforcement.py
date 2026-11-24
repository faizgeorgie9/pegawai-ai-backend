"""Auth enforcement: /api requires a live user session, logout invalidates, internal callers get a real owner.

These tests use a tiny in-memory stand-in for db.q1/db.ex (no PostgreSQL), so they also run in CI without
TEST_DATABASE_URL. Each test states the exact failure mode it covers.
"""
import time

import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from bff import auth, config, db
from bff.errors import ApiError
from bff.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _row(user_id="user_a", role="member", tv=0, active=True):
    return {
        "id": user_id,
        "name": "Pengguna A",
        "email": f"{user_id}@pegawai.ai",
        "role": role,
        "company": "Colorbox",
        "plan_id": "pro",
        "created_at": None,
        "is_active": active,
        "token_version": tv,
    }


def _token(user_id="user_a", role="member", tv=0):
    return {"Authorization": f"Bearer {auth.create_token(user_id, f'{user_id}@pegawai.ai', role, 'Pengguna', tv)}"}


@pytest.mark.anyio
async def test_api_without_token_is_401_everywhere_representative(monkeypatch):
    """Kritis 1: no bearer token must never fall back to the `default` tenant."""
    async def no_db(*_a, **_k):
        raise AssertionError("auth must refuse before touching the database")

    monkeypatch.setattr(db, "q1", no_db)
    monkeypatch.setattr(db, "q", no_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        for method, path in [("GET", "/api/bots"), ("GET", "/api/settings"), ("GET", "/api/groups"),
                             ("GET", "/api/me"), ("GET", "/api/auth/me"), ("GET", "/api/events"),
                             ("GET", "/api/tasks/board"), ("POST", "/api/whatsapp/simulate")]:
            r = await c.request(method, path, json={} if method == "POST" else None)
            assert r.status_code == 401, (path, r.status_code, r.text)
            body = r.json()
            assert set(body) == {"error"} and "login" in body["error"].lower()


@pytest.mark.anyio
async def test_garbage_expired_and_foreign_signed_tokens_are_401(monkeypatch):
    """Kritis 2: a token is only valid when our JWT_SECRET signed it and it has not expired."""
    async def no_db(*_a, **_k):
        raise AssertionError("token decoding must fail before the database lookup")

    monkeypatch.setattr(db, "q1", no_db)
    transport = ASGITransport(app=app)
    expired = jwt.encode({"sub": "user_a", "tv": 0, "exp": int(time.time()) - 5}, config.JWT_SECRET, algorithm=auth.ALGORITHM)
    foreign = jwt.encode({"sub": "user_a", "tv": 0, "exp": int(time.time()) + 60}, config.BFF_API_KEY or "some-other-key", algorithm=auth.ALGORITHM)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        for token in ("not-a-jwt", expired, foreign):
            r = await c.get("/api/bots", headers={"Authorization": f"Bearer {token}"})
            assert r.status_code == 401, (token, r.status_code)
            assert "error" in r.json()


@pytest.mark.anyio
async def test_unknown_user_and_logged_out_version_are_401(monkeypatch):
    """A signed token still fails when the account is gone, inactive, or its version was bumped."""
    state = {"row": None}

    async def q1(_sql, *_params):
        return state["row"]

    monkeypatch.setattr(db, "q1", q1)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/api/bots", headers=_token())
        assert r.status_code == 401 and "tidak ditemukan" in r.json()["error"].lower()

        state["row"] = _row(tv=3)
        r = await c.get("/api/bots", headers=_token(tv=2))
        assert r.status_code == 401 and "berakhir" in r.json()["error"].lower()

        state["row"] = _row(active=False)
        r = await c.get("/api/bots", headers=_token(tv=0))
        assert r.status_code == 401 and "dinonaktifkan" in r.json()["error"].lower()


@pytest.mark.anyio
async def test_other_users_bot_is_404_not_403_with_data(monkeypatch):
    """Ownership lives in the SQL filter: a valid member token never reaches another tenant's bot."""
    async def q1(sql, *params):
        if "from bots where id = %s and user_id = %s" in sql:
            # this bot belongs to user_a; the token is user_b
            return None
        if "FROM users WHERE id = %s" in sql:
            return _row("user_b", role="member", tv=0)
        return None

    monkeypatch.setattr(db, "q1", q1)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/api/bots/bimo", headers=_token("user_b"))
        assert r.status_code == 404
        assert r.json() == {"error": "Bot tidak ditemukan"}


@pytest.mark.anyio
async def test_logout_bumps_token_version_and_the_old_token_is_dead(monkeypatch):
    """Requirement 3: /auth/logout makes every earlier token 401, including /auth/me."""
    state = {"tv": 4}

    async def q1(sql, *_params):
        if "UPDATE users SET token_version" in sql:
            state["tv"] += 1
            return {"token_version": state["tv"]}
        if "FROM users WHERE id = %s" in sql:
            return _row(tv=state["tv"])
        return None

    monkeypatch.setattr(db, "q1", q1)
    old = _token(tv=4)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        assert (await c.get("/api/auth/me", headers=old)).status_code == 200
        r = await c.post("/api/auth/logout", headers=old)
        assert r.status_code == 200 and r.json()["ok"] is True
        assert state["tv"] == 5

        for path in ("/api/auth/me", "/api/bots"):
            r = await c.get(path, headers=old)
            assert r.status_code == 401, path
            assert "berakhir" in r.json()["error"].lower()

        # Logout with no token is harmless and public (the browser may have already dropped it).
        assert (await c.post("/api/auth/logout")).status_code == 200


@pytest.mark.anyio
async def test_registration_is_closed_by_default(monkeypatch):
    """Requirement 4: 403 with a plain Indonesian message unless ALLOW_REGISTER=true."""
    monkeypatch.setattr(config, "ALLOW_REGISTER", False)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.post("/api/auth/register", json={"name": "Baru", "email": "baru@pegawai.ai", "password": "rahasia123"})
        assert r.status_code == 403
        assert r.json() == {"error": "Pendaftaran akun baru belum dibuka. Hubungi administrator perusahaan Anda untuk dibuatkan akun."}

        monkeypatch.setattr(config, "ALLOW_REGISTER", True)

        async def q1(_sql, *_params):
            return None  # email unused

        async def ex(*_a, **_k):
            return None

        monkeypatch.setattr(db, "q1", q1)
        monkeypatch.setattr(db, "ex", ex)
        r = await c.post("/api/auth/register", json={"name": "Baru", "email": "baru@pegawai.ai", "password": "rahasia123"})
        assert r.status_code == 200 and r.json()["user"]["role"] == "member"


@pytest.mark.anyio
async def test_service_identity_uses_bot_owner_then_explicit_user_then_oldest_admin(monkeypatch):
    """Internal callers (WhatsApp webhook, MCP bridge) resolve a real owner instead of `default`."""
    async def q1(sql, *params):
        if "from bots where id = %s" in sql:
            return {"user_id": "user_owner"} if params[0] == "bimo" else None
        if "where id = %s and is_active" in sql:
            return {"id": params[0]} if params[0] == "user_service" else None
        if "role in ('admin', 'owner')" in sql:
            return {"id": "user_admin_tertua"}
        return None

    monkeypatch.setattr(db, "q1", q1)
    assert await auth.service_user("bimo") == "user_owner"
    monkeypatch.setattr(config, "SERVICE_USER_ID", "user_service")
    assert await auth.service_user("tanpa-profil") == "user_service"
    monkeypatch.setattr(config, "SERVICE_USER_ID", "")
    assert await auth.service_user(None) == "user_admin_tertua"


@pytest.mark.anyio
async def test_service_identity_refuses_an_empty_database(monkeypatch):
    async def q1(_sql, *_params):
        return None

    monkeypatch.setattr(db, "q1", q1)
    monkeypatch.setattr(config, "SERVICE_USER_ID", "")
    with pytest.raises(ApiError) as e:
        await auth.service_user("tidak-ada")
    assert e.value.status == 500 and "Belum ada pengguna aktif" in e.value.message


def test_jwt_secret_is_required_and_must_differ_from_the_proxy_key(monkeypatch):
    """Kritis 2: no fallback to BFF_API_KEY, no short secret, no identical key."""
    monkeypatch.setattr(config, "JWT_SECRET", "")
    with pytest.raises(RuntimeError, match="JWT_SECRET belum diatur"):
        auth.validate_config()

    monkeypatch.setattr(config, "JWT_SECRET", "pendek")
    with pytest.raises(RuntimeError, match="terlalu pendek"):
        auth.validate_config()

    monkeypatch.setattr(config, "BFF_API_KEY", "kunci-proxy-yang-dipakai-bersama-0123456789")
    monkeypatch.setattr(config, "JWT_SECRET", "kunci-proxy-yang-dipakai-bersama-0123456789")
    with pytest.raises(RuntimeError, match="tidak boleh sama"):
        auth.validate_config()

    monkeypatch.setattr(config, "JWT_SECRET", "jwt-rahasia-terpisah-0123456789abcdef")
    assert auth.validate_config() is None
