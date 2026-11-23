"""Long-term memory of one Hermes profile: MEMORY.md (agent notes) and USER.md (user profile).

Hermes owns these files. We reuse its on-disk format and its lock so a BFF write never races a
running turn (tools/memory_tool_store.py in the installed Hermes):

- entries are joined by ``"\\n§\\n"``; each entry is stripped and empty entries are dropped;
- the file is replaced atomically (temp file + rename), so a reader sees the old or the new file;
- mutations hold an exclusive lock on ``<file>.lock`` (``fcntl.flock`` on Unix, ``msvcrt.locking``
  on Windows) and re-read the file under that lock before writing;
- limits are characters, not entries (defaults 2.200 for MEMORY.md and 1.375 for USER.md).

Reads need no lock: the rename makes them atomic. Deletes and clears do, and a stale item id is a
409 instead of a blind delete.
"""
import hashlib
import os
import re
import stat
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from . import config, hermes
from .errors import ApiError

ENTRY_DELIMITER = "\n§\n"
DEFAULT_MEMORY_LIMIT = 2200
DEFAULT_USER_LIMIT = 1375
STORE_FILES = {"memory": "MEMORY.md", "user": "USER.md"}
# Item ids carry their store so one id is never ambiguous between MEMORY.md and USER.md.
_ID_PREFIX = {"memory": "m", "user": "u"}

try:  # Unix
    import fcntl
except ImportError:  # Windows
    fcntl = None
    try:
        import msvcrt
    except ImportError:
        msvcrt = None


def _memory_dir(bot_id: str) -> Path:
    """Profile memories directory; profile_dir() rejects a bot id that is not a plain slug."""
    return hermes.profile_dir(bot_id) / "memories"


def path_for(bot_id: str, store: str) -> Path:
    if store not in STORE_FILES:
        raise ApiError(404, "Ingatan tidak ditemukan")
    return _memory_dir(bot_id) / STORE_FILES[store]


def parse_entries(raw: str) -> list[str]:
    """Hermes' parser: split on the full delimiter, strip every entry, drop empty ones."""
    return [e for e in (x.strip() for x in raw.split(ENTRY_DELIMITER)) if e]


def read_entries(path: Path) -> list[str]:
    """Entries of one store; a missing file is an empty store. utf-8-sig matches Hermes (BOM safe)."""
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return []
    except (OSError, UnicodeDecodeError):
        raise ApiError(502, "Ingatan tidak bisa dibaca. Coba lagi sebentar lagi.")
    return parse_entries(raw)


def item_id(store: str, text: str) -> str:
    """Stable id for one entry: the store plus a hash of the exact text Hermes stores."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{_ID_PREFIX[store]}-{digest}"


def _usage(entries: list[str]) -> int:
    return len(ENTRY_DELIMITER.join(entries))


def _limit_from(value, default: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return default
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return default
    return limit if 1 <= limit <= 100_000 else default


def _yaml_memory_section(path: Path) -> dict:
    try:
        from ruamel.yaml import YAML

        data = YAML(typ="safe").load(path.read_text(encoding="utf-8"))
    except Exception:  # missing/invalid YAML must never break the page
        return {}
    section = data.get("memory") if isinstance(data, dict) else None
    return section if isinstance(section, dict) else {}


def limits(bot_id: str) -> tuple[int, int]:
    """(MEMORY.md, USER.md) character limits.

    Hermes reads the profile's own config.yaml (defaults when absent). We check the profile first,
    then the installation config, then Hermes' documented defaults. Display only: Hermes enforces
    the same numbers when the agent writes.
    """
    profile = hermes.profile_dir(bot_id) / "config.yaml"
    section = _yaml_memory_section(profile)
    if not section:
        section = _yaml_memory_section(config.HERMES_HOME / "config.yaml")
    return (_limit_from(section.get("memory_char_limit"), DEFAULT_MEMORY_LIMIT),
            _limit_from(section.get("user_char_limit"), DEFAULT_USER_LIMIT))


def snapshot(bot_id: str) -> dict:
    """Everything the Ingatan tab shows. No lock: reads are atomic because writes rename."""
    memory_entries = read_entries(path_for(bot_id, "memory"))
    user_entries = read_entries(path_for(bot_id, "user"))
    memory_limit, user_limit = limits(bot_id)
    return {
        "items": [{"id": item_id("memory", e), "text": e} for e in memory_entries],
        "about_you": [{"id": item_id("user", e), "text": e} for e in user_entries],
        "limit": {"used": _usage(memory_entries), "max": memory_limit},
        "about_limit": {"used": _usage(user_entries), "max": user_limit},
    }


@contextmanager
def file_lock(path: Path):
    """Exclusive lock on ``<file>.lock``, the same protocol and byte range Hermes uses.

    Hermes locks one byte from offset 0 on the separate lock file. We do the same and fail as a
    conflict (409) when another writer holds it past the OS retry window, never as a lost write.
    """
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(lock_path, flags, 0o600)
    locked = False
    try:
        if hasattr(os, "fchmod"):
            try:
                os.fchmod(fd, 0o600)
            except OSError:
                pass
        try:
            if fcntl is not None:
                fcntl.flock(fd, fcntl.LOCK_EX)
            elif msvcrt is not None:
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            locked = True
        except OSError:
            raise ApiError(409, "Ingatan sedang dipakai. Coba lagi sebentar lagi.")
        yield
    finally:
        if locked:
            try:
                if fcntl is not None:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                elif msvcrt is not None:
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        os.close(fd)


def write_entries(path: Path, entries: list[str]) -> None:
    """Atomic replace with Hermes' exact byte format (no trailing newline). Caller holds the lock."""
    data = ENTRY_DELIMITER.join(entries).encode("utf-8")
    try:
        mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else None
    except OSError:
        mode = None
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".mem_")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        if mode is not None:
            try:
                os.chmod(tmp, mode)
            except OSError:
                pass
        # Windows refuses to replace a file another handle has open (a GET or Hermes reading it).
        # The window is milliseconds, so retry briefly instead of failing the user's delete.
        for attempt in range(10):
            try:
                os.replace(tmp, path)
                break
            except PermissionError:
                if attempt == 9:
                    raise
                time.sleep(0.05)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def delete_item(bot_id: str, item: str) -> None:
    """Remove one entry by its stable id. 404 for an unknown id, 409 when the entry changed."""
    prefix, _, digest = item.partition("-")
    store = next((name for name, p in _ID_PREFIX.items() if p == prefix), None)
    if not store or not re.fullmatch(r"[0-9a-f]{16}", digest):
        raise ApiError(404, "Ingatan tidak ditemukan")
    path = path_for(bot_id, store)
    if not path.exists():
        raise ApiError(409, "Ingatan ini sudah berubah. Muat ulang daftar, lalu coba lagi.")
    with file_lock(path):
        entries = read_entries(path)
        index = next((i for i, text in enumerate(entries) if item_id(store, text) == item), None)
        if index is None:
            raise ApiError(409, "Ingatan ini sudah berubah. Muat ulang daftar, lalu coba lagi.")
        del entries[index]
        try:
            write_entries(path, entries)
        except OSError:
            raise ApiError(502, "Ingatan gagal disimpan. Coba lagi sebentar lagi.")


def clear_all(bot_id: str) -> None:
    """Empty both long-term stores; each existing file is locked before it is replaced."""
    for store in ("memory", "user"):
        path = path_for(bot_id, store)
        if not path.exists():
            continue
        with file_lock(path):
            try:
                write_entries(path, [])
            except OSError:
                raise ApiError(502, "Ingatan gagal dihapus. Coba lagi sebentar lagi.")
