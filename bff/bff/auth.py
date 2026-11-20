"""Authentication, password hashing, and JWT token management for Pegawai AI."""
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


def _get_secret() -> str:
    # Use BFF_API_KEY as HMAC signing key
    return config.BFF_API_KEY or "pegawai_ai_default_secret_key_minimum_32_bytes_length!"


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


def create_token(user_id: str, email: str, role: str = "member", name: str = "") -> str:
    """Creates a signed JWT access token."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "name": name,
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
        raise ApiError(401, "Token autentikasi tidak valid atau rusak.")


async def get_user_by_id(user_id: str) -> dict | None:
    """Fetches user record by ID (sanitizing password hash and salt)."""
    row = await db.q1("SELECT id, name, email, role, company, plan_id, created_at, is_active FROM users WHERE id = %s", user_id)
    if not row:
        return None
    d = dict(row)
    if d.get("created_at") and hasattr(d["created_at"], "isoformat"):
        d["created_at"] = d["created_at"].isoformat()
    return d


async def authenticate(email: str, password: str) -> dict:
    """Verifies user credentials and returns (token, user_dict)."""
    if not email or not password:
        raise ApiError(400, "Email dan kata sandi wajib diisi")

    email = email.strip().lower()
    user = await db.q1("SELECT id, name, email, salt, password_hash, role, company, plan_id, is_active FROM users WHERE LOWER(email) = %s", email)
    if not user:
        raise ApiError(401, "Email atau kata sandi tidak cocok")

    if not user.get("is_active", True):
        raise ApiError(403, "Akun ini telah dinonaktifkan")

    if not user.get("salt") or not user.get("password_hash"):
        raise ApiError(401, "Akun belum memiliki kata sandi yang dikonfigurasi")

    if not verify_password(password, user["salt"], user["password_hash"]):
        raise ApiError(401, "Email atau kata sandi tidak cocok")

    token = create_token(user["id"], user["email"], user["role"], user["name"])
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

    token = create_token(user_id, email, "member", name)
    user_data = {
        "id": user_id,
        "name": name,
        "email": email,
        "role": "member",
        "company": company,
        "plan_id": "pro"
    }
    return {"token": token, "user": user_data}
