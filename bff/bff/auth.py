"""Authentication, password hashing, and JWT token management for Pegawai AI.

The signing secret is JWT_SECRET, never BFF_API_KEY: rotating the dev proxy key must not let anyone mint
a session. Each token carries `tv` (the user's token_version); /auth/logout bumps that column, so every
token issued before the logout stops working without keeping a denylist.
"""
import hashlib
import hmac
import secrets
import time
import uuid

import jwt

from . import config, db
from .errors import ApiError

ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 7 * 86400  # 7 days
MIN_SECRET_CHARS = 32

_MISSING_SECRET = ("JWT_SECRET belum diatur. Isi bff/.env dengan JWT_SECRET=<acak 32+ karakter, "
                   "berbeda dari BFF_API_KEY>, lalu nyalakan ulang BFF.")


def validate_config() -> None:
    """Called at startup: an installation without its own signing secret must fail loudly, not fall back."""
    if not config.JWT_SECRET:
        raise RuntimeError(_MISSING_SECRET)
    if len(config.JWT_SECRET) < MIN_SECRET_CHARS:
        raise RuntimeError(f"JWT_SECRET terlalu pendek (minimal {MIN_SECRET_CHARS} karakter). Buat nilai acak baru.")
    if config.BFF_API_KEY and config.JWT_SECRET == config.BFF_API_KEY:
        raise RuntimeError("JWT_SECRET tidak boleh sama dengan BFF_API_KEY. Buat nilai acak terpisah untuk JWT_SECRET.")


def _get_secret() -> str:
    validate_config()
    return config.JWT_SECRET


def bearer_token(authorization: str | None) -> str | None:
    """The token from `Authorization: Bearer <token>`, or None when there is no usable header."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    return token or None


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hashes a password with PBKDF2-HMAC-SHA256 (100,000 iterations). Returns (password_hash, salt)."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return hashed, salt


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """Verifies a password against the stored salt and hash using timing-safe comparison."""
    if not salt or not password_hash:
        return False
    computed_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return hmac.compare_digest(computed_hash, password_hash)


def create_token(user_id: str, email: str, role: str = "member", name: str = "", token_version: int = 0) -> str:
    """Creates a signed JWT access token. `tv` ties it to the user's current token_version."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "name": name,
        "tv": int(token_version or 0),
        "iat": now,
        "exp": now + TOKEN_EXPIRY_SECONDS
    }
    return jwt.encode(payload, _get_secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Validates and decodes a JWT token. Raises ApiError(401) on failure."""
    try:
        return jwt.decode(token, _get_secret(), algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "Sesi login telah kedaluwarsa. Silakan login kembali.")
    except Exception:
        raise ApiError(401, "Token autentikasi tidak valid atau rusak. Silakan login kembali.")


def _public_user(row: dict) -> dict:
    d = dict(row)
    d.pop("token_version", None)
    d.pop("salt", None)
    d.pop("password_hash", None)
    if d.get("created_at") and hasattr(d["created_at"], "isoformat"):
        d["created_at"] = d["created_at"].isoformat()
    return d


async def get_user_by_id(user_id: str) -> dict | None:
    """Fetches user record by ID (sanitizing password hash and salt)."""
    row = await db.q1("SELECT id, name, email, role, company, plan_id, created_at, is_active FROM users WHERE id = %s", user_id)
    return _public_user(row) if row else None


async def load_user_for_token(payload: dict) -> dict:
    """The account behind a signed token, after checking it still exists, is active, and its version matches.

    Raises ApiError(401) for every case: an old token after logout must behave like no session at all.
    """
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise ApiError(401, "Token autentikasi tidak valid atau rusak. Silakan login kembali.")
    row = await db.q1(
        "SELECT id, name, email, role, company, plan_id, created_at, is_active, token_version FROM users WHERE id = %s",
        user_id)
    if not row:
        raise ApiError(401, "Akun Anda tidak ditemukan. Silakan login kembali.")
    if row.get("is_active") is False:
        raise ApiError(401, "Akun ini telah dinonaktifkan. Hubungi administrator perusahaan Anda.")
    if int(payload.get("tv", 0)) != int(row.get("token_version") or 0):
        raise ApiError(401, "Sesi Anda sudah berakhir. Silakan login kembali.")
    return _public_user(row)


async def authenticate_header(authorization: str | None) -> dict:
    """Identity for one API request. Missing, broken, expired, logged-out tokens all raise 401."""
    token = bearer_token(authorization)
    if not token:
        raise ApiError(401, "Silakan login terlebih dahulu untuk membuka halaman ini.")
    return await load_user_for_token(decode_token(token))


async def revoke_session(authorization: str | None) -> bool:
    """Logout: bump the user's token_version so every token issued before now stops working.

    Best effort for an already-invalid token: there is no session left to revoke, so it returns False.
    """
    token = bearer_token(authorization)
    if not token:
        return False
    try:
        payload = decode_token(token)
    except ApiError:
        return False
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        return False
    row = await db.q1("UPDATE users SET token_version = token_version + 1 WHERE id = %s RETURNING token_version", user_id)
    return bool(row)


async def bot_owner(bot_id: str | None) -> str | None:
    """The workspace user that owns this bot, when the bot exists and is not deleted."""
    if not bot_id:
        return None
    row = await db.q1("select user_id from bots where id = %s and deleted_at is null", bot_id)
    return row["user_id"] if row else None


async def service_user(bot_id: str | None = None) -> str:
    """Identity for a caller that has no user token (webhooks, scheduled work started outside a request).

    Order: the bot's owner in the database, then SERVICE_USER_ID, then the oldest active admin/owner.
    Never a hardcoded tenant: an installation with no owner at all is a configuration error, not 'default'.
    """
    owner = await bot_owner(bot_id)
    if owner:
        return owner
    if config.SERVICE_USER_ID:
        row = await db.q1("select id from users where id = %s and is_active", config.SERVICE_USER_ID)
        if row:
            return row["id"]
        raise ApiError(500, f"Pengguna layanan '{config.SERVICE_USER_ID}' tidak ditemukan atau tidak aktif.")
    row = await db.q1("select id from users where is_active order by (role in ('admin', 'owner')) desc, created_at asc limit 1")
    if row:
        return row["id"]
    raise ApiError(500, "Belum ada pengguna aktif yang dapat menjadi pemilik pekerjaan ini.")


async def authenticate(email: str, password: str) -> dict:
    """Verifies user credentials and returns (token, user_dict)."""
    if not email or not password:
        raise ApiError(400, "Email dan kata sandi wajib diisi")

    email = email.strip().lower()
    user = await db.q1("SELECT id, name, email, salt, password_hash, role, company, plan_id, is_active, token_version FROM users WHERE LOWER(email) = %s", email)
    if not user:
        raise ApiError(401, "Email atau kata sandi tidak cocok")

    if not user.get("is_active", True):
        raise ApiError(403, "Akun ini telah dinonaktifkan")

    if not user.get("salt") or not user.get("password_hash"):
        raise ApiError(401, "Akun belum memiliki kata sandi yang dikonfigurasi")

    if not verify_password(password, user["salt"], user["password_hash"]):
        raise ApiError(401, "Email atau kata sandi tidak cocok")

    token = create_token(user["id"], user["email"], user["role"], user["name"], user.get("token_version") or 0)
    user_data = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "company": user.get("company") or "Colorbox",
        "plan_id": user["plan_id"]
    }
    return {"token": token, "user": user_data}


async def register(name: str, email: str, password: str, company: str = "Colorbox") -> dict:
    """Registers a new user account with hashed password and generates an initial JWT token."""
    if not config.ALLOW_REGISTER:
        raise ApiError(403, "Pendaftaran akun baru belum dibuka. Hubungi administrator perusahaan Anda untuk dibuatkan akun.")

    if not email or not password or not name:
        raise ApiError(400, "Nama, email, dan kata sandi wajib diisi")

    if len(password) < 6:
        raise ApiError(400, "Kata sandi minimal 6 karakter")

    email = email.strip().lower()
    name = name.strip()

    existing = await db.q1("SELECT id FROM users WHERE LOWER(email) = %s", email)
    if existing:
        raise ApiError(400, "Email sudah terdaftar. Silakan gunakan email lain atau login.")

    user_id = f"user_{uuid.uuid4().hex[:10]}"
    pw_hash, salt = hash_password(password)

    await db.ex(
        "INSERT INTO users (id, name, email, salt, password_hash, role, company, plan_id) VALUES (%s, %s, %s, %s, %s, 'member', %s, 'pro')",
        user_id, name, email, salt, pw_hash, company
    )

    token = create_token(user_id, email, "member", name, 0)
    user_data = {
        "id": user_id,
        "name": name,
        "email": email,
        "role": "member",
        "company": company,
        "plan_id": "pro"
    }
    return {"token": token, "user": user_data}
