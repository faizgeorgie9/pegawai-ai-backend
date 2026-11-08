"""Version and configuration snapshot recorded on every run (for experiment repeatability).
Every value is read from a real source; anything that cannot be read becomes UNKNOWN. Nothing is guessed."""
import asyncio
import hashlib
import subprocess

from ruamel.yaml import YAML

from . import hermes
from .errors import ApiError

UNKNOWN = "tidak diketahui"
_cache: dict[str, str] = {}


async def hermes_version() -> str:
    """`version` of the gateway's GET /health. Cached after the first successful read."""
    if "hermes" in _cache:
        return _cache["hermes"]
    try:
        r = await hermes.client.get("/health", timeout=3)
        v = r.json().get("version") if r.status_code == 200 else None
    except Exception:
        v = None
    if isinstance(v, str) and v.strip():
        _cache["hermes"] = v.strip()[:40]
        return _cache["hermes"]
    return UNKNOWN


def bff_commit() -> str | None:
    """Short git commit of this BFF, read once. None when git or the repo is not available."""
    if "commit" not in _cache:
        try:
            out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=3,
                                 cwd=hermes.config.ROOT).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            out = ""
        _cache["commit"] = out
    return _cache["commit"] or None


def model_of(bot: str) -> tuple[str, str]:
    """(model, provider) from the profile config.yaml."""
    try:
        data = YAML(typ="safe").load((hermes.profile_dir(bot) / "config.yaml").read_text(encoding="utf-8")) or {}
        m = data.get("model")
    except Exception:
        return UNKNOWN, UNKNOWN
    if isinstance(m, str):
        return m or UNKNOWN, str(data.get("provider") or UNKNOWN)
    if isinstance(m, dict):
        return str(m.get("default") or m.get("name") or UNKNOWN), str(m.get("provider") or UNKNOWN)
    return UNKNOWN, UNKNOWN


def soul_hash(bot: str) -> str:
    """First 12 hex chars of the sha256 of the profile SOUL.md."""
    try:
        return hashlib.sha256((hermes.profile_dir(bot) / "SOUL.md").read_bytes()).hexdigest()[:12]
    except (OSError, ApiError):
        return UNKNOWN


async def toolsets_of(bot: str) -> list[str] | None:
    """Names of the toolsets the bot's API serves as enabled (same source as GET /api/tools). None when unreadable."""
    try:
        r = await hermes.call(bot, "GET", "/v1/toolsets", timeout=5)
        data = r.json()["data"] if r.status_code == 200 else None
        if not isinstance(data, list):
            return None
        return sorted(t["name"] for t in data if t.get("enabled") is True)
    except (ApiError, ValueError, KeyError, TypeError):
        return None


async def snapshot(bot: str, instructions: str | None) -> dict:
    ver, tools = await asyncio.gather(hermes_version(), toolsets_of(bot))
    model, provider = model_of(bot)
    snap = {"hermes_version": ver, "model": model, "provider": provider, "bot_id": bot, "soul_hash": soul_hash(bot),
            "toolsets": tools if tools is not None else UNKNOWN,
            "instructions_mode": "terstruktur" if instructions else "plain"}
    commit = bff_commit()
    if commit:
        snap["bff_commit"] = commit
    return snap
