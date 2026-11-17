"""Per-user connections to Google Drive and Gmail: OAuth 2.0 authorization-code flow run by the BFF.
Tokens are encrypted (Fernet, key CONNECTIONS_KEY) before they reach the database and are never logged.
What the connections are used for lives in integrations.py."""
import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet, InvalidToken

from . import config, db
from .errors import ApiError

STATE_TTL = timedelta(minutes=10)
HTTP_TIMEOUT = 15.0
GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE = "https://oauth2.googleapis.com/revoke"
GOOGLE_USERINFO = "https://openidconnect.googleapis.com/v1/userinfo"

# provider -> (OAuth family, scopes asked, scope that must be granted)
PROVIDERS = {
    "gdrive": ("google", ["openid", "email", "https://www.googleapis.com/auth/drive"], "https://www.googleapis.com/auth/drive"),  # connections made with the old drive.readonly still read (import, drive_read); only writes ask to reconnect
    "gmail": ("google", ["openid", "email", "https://www.googleapis.com/auth/gmail.compose", "https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/gmail.send"], "https://www.googleapis.com/auth/gmail.compose"),
}
NAMES = {"gdrive": "Google Drive", "gmail": "Gmail"}
RECONNECT_MSG = "Sambungan {name} perlu disambungkan ulang. Buka Aplikasi, lalu pilih Hubungkan ulang."


def _client_creds(provider: str) -> tuple[str, str]:
    return config.GOOGLE_CLIENT_ID, config.GOOGLE_CLIENT_SECRET


def configured(provider: str) -> bool:
    """The administrator set the client credentials and the encryption key."""
    cid, secret = _client_creds(provider)
    return bool(cid and secret and config.CONNECTIONS_KEY)


# What the administrator must fill in, per OAuth family: (env name, plain label). Only "filled or not" is ever reported, never a value.
SETUP = {
    "google": [("GOOGLE_CLIENT_ID", "ID klien Google"), ("GOOGLE_CLIENT_SECRET", "Rahasia klien Google")],
}
KEY_SETUP = ("CONNECTIONS_KEY", "Kunci enkripsi penyimpanan akun")


def setup_items(provider: str) -> list[dict]:
    """Each value the provider needs and whether it is filled (True/False only; no values, no validity check)."""
    items = SETUP[PROVIDERS[provider][0]] + [KEY_SETUP]
    return [{"env": env, "label": label, "filled": bool(getattr(config, env))} for env, label in items]


def redirect_uri(provider: str) -> str:
    return f"{config.PUBLIC_BASE_URL}/bff/api/connections/{PROVIDERS[provider][0]}/callback"


def app_url(query: dict) -> str:
    return f"{config.PUBLIC_BASE_URL}/#/aplikasi?{urlencode(query)}"


def _fernet() -> Fernet:
    if not config.CONNECTIONS_KEY:
        raise ApiError(503, "Sambungan akun belum diatur oleh administrator, jadi data akses tidak disimpan.")
    try:
        return Fernet(config.CONNECTIONS_KEY.encode())
    except ValueError:
        raise ApiError(503, "Kunci penyimpanan sambungan akun tidak valid. Hubungi administrator.")


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        raise ApiError(409, "Data sambungan tidak bisa dibuka (kunci penyimpanan berubah). Hubungkan ulang akunnya.")


def _hash(state: str) -> str:
    return hashlib.sha256(state.encode()).hexdigest()


def _provider(provider: str) -> str:
    if provider not in PROVIDERS:
        raise ApiError(404, "Aplikasi ini tidak dikenal")
    return provider


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _challenge(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()

# ---------- list / start ----------


async def list_all(user_id: str) -> list[dict]:
    rows = {r["provider"]: r for r in await db.q("select * from connections where user_id = %s", user_id)}
    out = []
    for p in PROVIDERS:
        r = rows.get(p)
        status = ("reconnect" if r["status"] == "reconnect" else "connected") if r else "disconnected"
        if not configured(p) and not r:
            status = "not_configured"
        out.append({"provider": p, "name": NAMES[p], "status": status, "configured": configured(p),
                    "account": r["account"] if r else None, "connected_at": r["created_at"] if r else None,
                    "redirect_uri": redirect_uri(p), "setup": setup_items(p)})
    return out


async def start(user_id: str, provider: str) -> dict:
    """The consent address to send the browser to. Needs the client credentials and the encryption key."""
    _provider(provider)
    if not configured(provider):
        raise ApiError(409, f"{NAMES[provider]} belum diatur oleh administrator.")
    _, scopes, _ = PROVIDERS[provider]
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)  # PKCE (S256)
    await db.ex("delete from oauth_states where expires_at < now()")
    await db.ex("insert into oauth_states (state_hash, user_id, provider, verifier, expires_at) values (%s, %s, %s, %s, %s)",
                _hash(state), user_id, provider, verifier, _now() + STATE_TTL)
    cid, _ = _client_creds(provider)
    q = {"client_id": cid, "redirect_uri": redirect_uri(provider), "response_type": "code", "scope": " ".join(scopes),
         "state": state, "code_challenge": _challenge(verifier), "code_challenge_method": "S256",
         "access_type": "offline", "prompt": "consent"}
    return {"url": f"{GOOGLE_AUTH}?{urlencode(q)}"}

# ---------- callback ----------


async def _take_state(user_id: str, family: str, state: str | None) -> dict | None:
    """Single use: the row is deleted whether or not it is valid. Valid = known, not expired, this user, this OAuth family."""
    if not state:
        return None
    row = await db.q1("delete from oauth_states where state_hash = %s returning *", _hash(state))
    if not row or row["expires_at"] < _now() or row["user_id"] != user_id or PROVIDERS.get(row["provider"], ("",))[0] != family:  # .get: a pending state from the removed Notion flow
        return None
    return row


async def callback(user_id: str, family: str, params: dict) -> str:
    """Finish a consent and return the app address to send the browser back to (query: connect=ok|error, app, reason)."""
    row = await _take_state(user_id, family, params.get("state"))
    if not row:
        return app_url({"connect": "error", "reason": "state"})
    provider = row["provider"]
    fail = lambda reason: app_url({"connect": "error", "app": provider, "reason": reason})  # noqa: E731
    if params.get("error") or not params.get("code"):
        return fail("denied")
    try:
        tokens = await _exchange_google(provider, params["code"], row["verifier"])
    except ApiError as e:
        return fail(e.extra.get("reason", "exchange"))
    except httpx.HTTPError:
        return fail("exchange")
    scopes, need = tokens["scopes"], PROVIDERS[provider][2]
    if need and need not in scopes:  # the consent screen lets people untick a permission
        return fail("scope")
    await db.ex(
        "insert into connections (user_id, provider, access_enc, refresh_enc, expires_at, scopes, account, status) "
        "values (%s, %s, %s, %s, %s, %s, %s, 'connected') on conflict (user_id, provider) do update set "
        "access_enc = excluded.access_enc, refresh_enc = excluded.refresh_enc, expires_at = excluded.expires_at, "
        "scopes = excluded.scopes, account = excluded.account, status = 'connected', created_at = now(), updated_at = now()",
        user_id, provider, encrypt(tokens["access"]), encrypt(tokens["refresh"]) if tokens["refresh"] else None,
        tokens["expires_at"], scopes, tokens["account"])
    return app_url({"connect": "ok", "app": provider})


def _expiry(data: dict) -> datetime | None:
    try:
        return _now() + timedelta(seconds=int(data["expires_in"]))
    except (KeyError, TypeError, ValueError):
        return None


async def _exchange_google(provider: str, code: str, verifier: str) -> dict:
    cid, secret = _client_creds(provider)
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as c:
        r = await c.post(GOOGLE_TOKEN, data={"code": code, "client_id": cid, "client_secret": secret, "redirect_uri": redirect_uri(provider),
                                             "grant_type": "authorization_code", "code_verifier": verifier})
        if r.status_code != 200 or not r.json().get("access_token"):
            raise ApiError(502, "exchange", reason="exchange")
        d = r.json()
        u = await c.get(GOOGLE_USERINFO, headers={"Authorization": f"Bearer {d['access_token']}"})
        account = u.json().get("email") if u.status_code == 200 else None
    return {"access": d["access_token"], "refresh": d.get("refresh_token"), "expires_at": _expiry(d),
            "scopes": (d.get("scope") or "").split(), "account": account}

# ---------- use ----------


async def access_token(user_id: str, provider: str) -> str:
    """A valid access token for the provider; Google tokens are refreshed when (nearly) expired.
    Raises 409 'perlu disambungkan ulang' when the user is not connected or the grant was revoked.
    shortcut: two parallel requests may both refresh; harmless, upgrade to a row lock if refresh tokens ever rotate."""
    _provider(provider)
    row = await db.q1("select * from connections where user_id = %s and provider = %s", user_id, provider)
    if not row:
        raise ApiError(409, f"{NAMES[provider]} belum tersambung. Buka Aplikasi untuk menghubungkannya.", needs="connect")
    if row["status"] == "reconnect":
        raise ApiError(409, RECONNECT_MSG.format(name=NAMES[provider]), needs="reconnect")
    if not row["expires_at"] or row["expires_at"] - _now() > timedelta(seconds=60):
        return decrypt(row["access_enc"])
    return await _refresh_google(user_id, provider, row)


async def _needs_reconnect(user_id: str, provider: str) -> ApiError:
    await db.ex("update connections set status = 'reconnect', updated_at = now() where user_id = %s and provider = %s", user_id, provider)
    return ApiError(409, RECONNECT_MSG.format(name=NAMES[provider]), needs="reconnect")


async def _refresh_google(user_id: str, provider: str, row: dict) -> str:
    if not row["refresh_enc"]:
        raise await _needs_reconnect(user_id, provider)
    cid, secret = _client_creds(provider)
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as c:
            r = await c.post(GOOGLE_TOKEN, data={"client_id": cid, "client_secret": secret, "grant_type": "refresh_token",
                                                 "refresh_token": decrypt(row["refresh_enc"])})
    except httpx.HTTPError:
        raise ApiError(502, f"{NAMES[provider]} belum bisa dihubungi. Coba lagi sebentar.")
    if r.status_code in (400, 401):  # invalid_grant: revoked, expired in Testing mode, or password changed
        raise await _needs_reconnect(user_id, provider)
    d = r.json() if r.status_code == 200 else {}
    if not d.get("access_token"):
        raise ApiError(502, f"{NAMES[provider]} belum bisa dihubungi. Coba lagi sebentar.")
    await db.ex("update connections set access_enc = %s, expires_at = %s, refresh_enc = coalesce(%s, refresh_enc), updated_at = now() "
                "where user_id = %s and provider = %s",
                encrypt(d["access_token"]), _expiry(d), encrypt(d["refresh_token"]) if d.get("refresh_token") else None, user_id, provider)
    return d["access_token"]


async def mark_reconnect(user_id: str, provider: str) -> None:
    """The provider answered 401 with a token we thought valid."""
    await db.ex("update connections set status = 'reconnect', updated_at = now() where user_id = %s and provider = %s", user_id, provider)


async def account_of(user_id: str, provider: str) -> str | None:
    row = await db.q1("select account from connections where user_id = %s and provider = %s", user_id, provider)
    return row["account"] if row else None


async def has_scope(user_id: str, provider: str, scope: str) -> bool:
    row = await db.q1("select scopes from connections where user_id = %s and provider = %s", user_id, provider)
    return bool(row) and scope in (row["scopes"] or [])


async def missing_scopes(user_id: str, provider: str) -> list[str]:
    """Permissions the provider asks for today that this saved consent lacks (empty when none, or when not connected)."""
    row = await db.q1("select scopes from connections where user_id = %s and provider = %s", user_id, provider)
    if not row:
        return []
    have = set(row["scopes"] or [])
    return [s for s in PROVIDERS[provider][1] if s.startswith("https://") and s not in have]


async def is_connected(user_id: str, provider: str) -> bool:
    return bool(await db.q1("select 1 as x from connections where user_id = %s and provider = %s and status = 'connected'", user_id, provider))

# ---------- disconnect ----------


async def disconnect(user_id: str, provider: str) -> None:
    """Revoke at the provider (best effort) and delete the stored tokens. Never fails because the provider is unreachable."""
    _provider(provider)
    row = await db.q1("delete from connections where user_id = %s and provider = %s returning *", user_id, provider)
    if not row:
        return
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as c:
            # Google keeps one grant per client and user, so revoking would also cut the other Google connection.
            other = await db.q1("select 1 as x from connections where user_id = %s and provider in ('gdrive', 'gmail')", user_id)
            if not other:
                await c.post(GOOGLE_REVOKE, data={"token": decrypt(row["refresh_enc"] or row["access_enc"])})
    except (httpx.HTTPError, ApiError):
        pass
