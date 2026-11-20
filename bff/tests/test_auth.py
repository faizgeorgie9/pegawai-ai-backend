import pytest
from httpx import ASGITransport, AsyncClient

from bff import auth, db
from bff.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_hash_and_verify_password():
    pwd = "SecretPassword123!"
    hashed, salt = auth.hash_password(pwd)
    assert hashed != pwd
    assert len(salt) == 32
    assert auth.verify_password(pwd, salt, hashed) is True
    assert auth.verify_password("WrongPassword!", salt, hashed) is False


def test_create_and_decode_token():
    token = auth.create_token("usr_test_1", "test@colorbox.co.id", role="owner", name="Test Owner")
    assert isinstance(token, str)
    payload = auth.decode_token(token)
    assert payload["sub"] == "usr_test_1"
    assert payload["email"] == "test@colorbox.co.id"
    assert payload["role"] == "owner"
    assert payload["name"] == "Test Owner"


@pytest.mark.anyio
async def test_auth_login_endpoints(monkeypatch):
    test_user = {
        "id": "usr_test_owner",
        "name": "Owner Colorbox",
        "email": "owner@colorbox.co.id",
        "salt": "a1b2c3d4e5f607182930415263748596",
        "password_hash": "4f9e13cb3321b5dd3c2496f4ed8979cc566876a9467672a0e80aa73de1a5e76e",
        "role": "owner",
        "company": "Colorbox",
        "plan_id": "bisnis",
        "is_active": True
    }

    async def mock_q1(sql, *params):
        if "LOWER(email)" in sql:
            email_param = params[0]
            if email_param == "owner@colorbox.co.id":
                return test_user
            return None
        if "WHERE id =" in sql:
            return test_user
        return None

    monkeypatch.setattr(db, "q1", mock_q1)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login with bad credentials -> 401
        bad_res = await client.post("/api/auth/login", json={"email": "nonexistent@test.com", "password": "wrong"})
        assert bad_res.status_code == 401
        assert "Email atau kata sandi tidak cocok" in bad_res.json()["error"]

        # 2. Login with wrong password -> 401
        bad_pwd = await client.post("/api/auth/login", json={"email": "owner@colorbox.co.id", "password": "WrongPassword!"})
        assert bad_pwd.status_code == 401
        assert "Email atau kata sandi tidak cocok" in bad_pwd.json()["error"]

        # 3. Login missing fields -> 400
        bad_req = await client.post("/api/auth/login", json={"email": ""})
        assert bad_req.status_code == 400

        # 4. Login success -> 200 + token
        good_res = await client.post("/api/auth/login", json={"email": "owner@colorbox.co.id", "password": "Admin1234!"})
        assert good_res.status_code == 200
        data = good_res.json()
        assert "token" in data
        assert data["user"]["email"] == "owner@colorbox.co.id"
        assert data["user"]["role"] == "owner"
        token = data["token"]

        # 5. Call /api/auth/me without token -> 401
        unauth = await client.get("/api/auth/me")
        assert unauth.status_code == 401

        # 6. Call /api/auth/me with fake token -> 401
        fake_token = await client.get("/api/auth/me", headers={"Authorization": "Bearer fake.jwt.token"})
        assert fake_token.status_code == 401

        # 7. Call /api/auth/me with valid token -> 200 + user profile
        me_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["ok"] is True
        assert me_data["user"]["id"] == "usr_test_owner"
        assert me_data["user"]["name"] == "Owner Colorbox"

        # 8. Call /api/auth/logout -> 200
        logout = await client.post("/api/auth/logout")
        assert logout.status_code == 200
        assert logout.json()["ok"] is True
