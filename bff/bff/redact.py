"""Redaction for tool previews and approval descriptions (stage 5). Applied before storing and returning."""
import re

MASK = "[disensor]"
MAX_LEN = 2048

_JWT = re.compile(r"eyJ[\w-]+\.[\w-]+\.[\w-]+")
_SK = re.compile(r"sk-[A-Za-z0-9_-]{16,}")
_BEARER = re.compile(r"Bearer\s+\S+", re.I)
_KV = re.compile(r"""((?:api[_-]?key|token|secret|password)["']?\s*[:=]\s*)\S+""", re.I)
_EMAIL = re.compile(r"\b([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
_PHONE = re.compile(r"(?<![\w+])(?:\+62|08)\d{8,12}\b")
# shortcut: paths with spaces are cut at the first space; upgrade if previews show such paths.
_WIN_PATH = re.compile(r"""[A-Za-z]:[\\/](?:[^\\/\s"'<>|]+[\\/])*[^\\/\s"'<>|]+""")
_NIX_PATH = re.compile(r"""(?<![\w/:.])/(?:home|Users|root|var|etc|opt|tmp|mnt)/(?:[^/\s"']+/)*[^/\s"']+""")
# hex/base64-like runs of 32+ chars; must contain a digit so long plain words survive
_LONG = re.compile(r"(?<![\w+/=-])(?=[A-Za-z0-9+_-]*\d)[A-Za-z0-9+/_-]{32,}={0,2}(?![\w+/=-])")


def _mask_phone(m: re.Match) -> str:
    s = m.group(0)
    return "*" * (len(s) - 3) + s[-3:]


def _short_path(m: re.Match) -> str:
    return "…/" + re.split(r"[\\/]",m.group(0))[-1]


def redact(text: str | None, limit: int = MAX_LEN) -> str:
    if not text:
        return ""
    s = str(text)
    s = _JWT.sub(MASK, s)
    s = _SK.sub(MASK, s)
    s = _BEARER.sub(MASK, s)
    s = _KV.sub(lambda m: m.group(1) + MASK, s)
    s = _EMAIL.sub(lambda m: f"{m.group(1)}***@{m.group(2)}", s)
    s = _PHONE.sub(_mask_phone, s)
    s = _WIN_PATH.sub(_short_path, s)
    s = _NIX_PATH.sub(_short_path, s)
    s = _LONG.sub(MASK, s)
    return s if len(s) <= limit else s[: limit - 1] + "…"
