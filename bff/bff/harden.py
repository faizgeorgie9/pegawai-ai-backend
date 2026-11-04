"""Hardening for bots served over the API (section 8).

Usage: uv run python -m bff.harden [--profile X]   (default: the five builtin bots)

Removes terminal, file, code_execution, browser, computer_use, cronjob and delegation (no scheduled jobs or
sub-agents that keep working after a stop) from platform_toolsets.api_server and sets
approvals.mode: manual in the profile config.yaml. Idempotent; config.yaml is backed up before the first change.
Only the API server is affected: Hermes Desktop Bot Mode uses other platforms and keeps its tools.
"""
import argparse
import shutil
import sys
import time
from datetime import date

import httpx
from ruamel.yaml import YAML

from . import config, hermes

DENY = {"terminal", "file", "code_execution", "browser", "computer_use", "cronjob", "delegation"}
BUILTIN = ["rian", "diana", "budi", "siti", "hendra"]


def _toolsets_from_gateway(slug: str) -> list[dict]:
    r = httpx.get(f"{config.HERMES_API_URL}/p/{slug}/v1/toolsets",
                  headers={"Authorization": f"Bearer {hermes.bot_key(slug)}"}, timeout=10)
    r.raise_for_status()
    return r.json()["data"]


def enabled_toolsets(slug: str) -> list[str]:
    return [t["name"] for t in _toolsets_from_gateway(slug) if t["enabled"]]


def harden(slug: str) -> bool:
    """Edit the profile config.yaml. Returns True when the file changed."""
    path = hermes.profile_dir(slug) / "config.yaml"
    yaml = YAML()  # round-trip: keeps other keys and comments
    yaml.preserve_quotes = True
    data = yaml.load(path.read_text(encoding="utf-8")) or {}
    current = (data.get("platform_toolsets") or {}).get("api_server")
    if not isinstance(current, list):
        current = enabled_toolsets(slug)  # not set yet: start from what the API serves now
    wanted = [t for t in current if t not in DENY]
    changed = False
    if data.get("platform_toolsets") is None:
        data["platform_toolsets"] = {}
        changed = True
    if list(data["platform_toolsets"].get("api_server") or []) != wanted or "api_server" not in data["platform_toolsets"]:
        data["platform_toolsets"]["api_server"] = wanted
        changed = True
    if data.get("approvals") is None:
        data["approvals"] = {}
        changed = True
    if data["approvals"].get("mode") != "manual":
        data["approvals"]["mode"] = "manual"
        changed = True
    if changed:
        backup = path.with_name(f"config.yaml.bak-{date.today():%Y%m%d}")
        if not backup.exists():
            shutil.copy2(path, backup)
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f)
    return changed


def verify(slug: str, wait: int = 0) -> list[str]:
    """Names of denied toolsets still enabled (empty list = hardened). Polls up to `wait` seconds."""
    end = time.monotonic() + wait
    while True:
        left = sorted(set(enabled_toolsets(slug)) & DENY)
        if not left or time.monotonic() >= end:
            return left
        time.sleep(2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", help="harden only this profile")
    args = ap.parse_args()
    bad = 0
    for slug in [args.profile] if args.profile else BUILTIN:
        changed = harden(slug)
        left = verify(slug, wait=0 if not changed else 10)
        print(f"{slug}: {'diubah' if changed else 'sudah aman'}"
              + (f", MASIH AKTIF: {', '.join(left)} (jalankan: hermes gateway restart)" if left else ", terminal dan sejenisnya nonaktif"))
        bad += bool(left)
    print("Catatan: hanya API server yang dibatasi. Hermes Desktop Bot Mode memakai platform lain dan tidak terpengaruh.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
