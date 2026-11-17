"""Internal MCP server ("pegawai") for the Hermes agents: BFF-provided tools, served as Streamable HTTP at /mcp.

Tools: `ping`, read-only Google Drive search/read, and Gmail search/read/create-draft (never send), through the workspace owner's connections. Add tools inside build(). Auth: `Authorization: Bearer <MCP_BRIDGE_KEY>`, loopback clients only.
ensure_registered() makes every Hermes profile list this server (mcp_servers.pegawai) at BFF startup, idempotently.
"""
import hmac
import io
import ipaddress
import logging
import os
import re
import secrets
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from ruamel.yaml import YAML
from starlette.responses import JSONResponse
from starlette.routing import Route

from . import config, integrations
from .errors import ApiError

log = logging.getLogger("bff.bridge")
NAME = "pegawai"
URL = os.environ.get("MCP_BRIDGE_URL", "http://127.0.0.1:8090/mcp")
ENV_KEY = "MCP_BRIDGE_KEY"
PROFILE_ENV_KEY = "MCP_PEGAWAI_API_KEY"  # where the key sits in each profile .env (the name `hermes mcp add --auth header` uses)

DRIVE_MAX_CHARS = 50_000
DRIVE_MAX_RESULTS = 10
DRIVE_NOT_CONNECTED = "Google Drive belum disambungkan. Minta pengguna menyambungkannya di halaman Aplikasi."

GMAIL_NOT_CONNECTED = "Gmail belum disambungkan. Minta pengguna menyambungkannya di halaman Aplikasi."
GMAIL_MAX_RESULTS = 10
GMAIL_BODY_MAX = integrations.GMAIL_MAX_BODY


def _user() -> str:
    from .main import current_user  # late import: main imports this module
    return current_user()


def _drive_error(e: ApiError) -> str:
    """Tool error text: the friendly message only (integrations never puts tokens or provider bodies in it)."""
    return DRIVE_NOT_CONNECTED if e.extra.get("needs") == "connect" else f"Error: {e.message}"


async def drive_search(query: str, limit: int = DRIVE_MAX_RESULTS) -> str:
    if not query.strip():
        return "Error: query must not be empty."
    if not 1 <= limit <= DRIVE_MAX_RESULTS:
        return f"Error: limit must be between 1 and {DRIVE_MAX_RESULTS}."
    try:
        found = await integrations.drive_list(_user(), query, size=limit, content=True)
    except ApiError as e:
        return _drive_error(e)
    if not found["files"]:
        return "No matching files found in Google Drive."
    return "\n".join(f"- {f['name']} | id: {f['id']} | type: {f['type']} | modified: {(f['modified'] or '-')[:10]} | link: {f['link'] or '-'}"
                     for f in found["files"])


async def drive_read(file_id: str) -> str:
    file_id = file_id.strip()
    if not integrations.ID_RE.fullmatch(file_id):
        return "Error: invalid file_id (use the id from drive_search)."
    try:
        name, _link, text = await integrations.drive_read(_user(), file_id)
    except ApiError as e:
        return _drive_error(e)
    if len(text) > DRIVE_MAX_CHARS:
        text = text[:DRIVE_MAX_CHARS] + f"\n[dipotong: hanya {DRIVE_MAX_CHARS} karakter pertama]"
    return f"# {name}\n\n{text}"


def _gmail_error(e: ApiError) -> str:
    return GMAIL_NOT_CONNECTED if e.extra.get("needs") == "connect" else f"Error: {e.message}"


async def gmail_search(query: str, limit: int = GMAIL_MAX_RESULTS) -> str:
    if not query.strip():
        return "Error: query must not be empty."
    if not 1 <= limit <= GMAIL_MAX_RESULTS:
        return f"Error: limit must be between 1 and {GMAIL_MAX_RESULTS}."
    try:
        found = await integrations.gmail_search(_user(), query.strip(), limit)
    except ApiError as e:
        return _gmail_error(e)
    if not found:
        return "No matching emails found in Gmail."
    return "\n".join(f"- id: {m['id']} | from: {m['from'] or '-'} | subject: {m['subject'] or '-'} | date: {m['date'] or '-'} | {m['snippet']}" for m in found)


async def gmail_read(message_id: str) -> str:
    message_id = message_id.strip()
    if not integrations.ID_RE.fullmatch(message_id):
        return "Error: invalid message_id (use the id from gmail_search)."
    try:
        m = await integrations.gmail_read(_user(), message_id)
    except ApiError as e:
        return _gmail_error(e)
    body = m["body"]
    if len(body) > GMAIL_BODY_MAX:
        body = body[:GMAIL_BODY_MAX] + f"\n[dipotong: hanya {GMAIL_BODY_MAX} karakter pertama]"
    return f"From: {m['from']}\nTo: {m['to']}\nSubject: {m['subject']}\nDate: {m['date']}\n\n{body}"


async def gmail_create_draft(to: str, subject: str, body: str) -> str:
    to = to.strip()
    if not to:
        return "Error: to must not be empty."
    try:
        d = await integrations.gmail_draft(_user(), to, subject, body)
    except ApiError as e:
        return _gmail_error(e)
    return f"Draf dibuat di Gmail pengguna (belum terkirim; pengguna mengirimnya sendiri). Buka: {d['url']}"


def build() -> FastMCP:
    """The tool server. Register new tools here."""
    # shortcut: DNS-rebinding protection is off because the loopback check in BridgeApp already limits callers; revisit with a non-loopback bind
    mcp = FastMCP(NAME, stateless_http=True, json_response=True, streamable_http_path="/mcp",
                  transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))

    @mcp.tool()
    def ping() -> str:
        """Connectivity check for the Pegawai AI bridge: returns "ok" and the server time (UTC, ISO 8601)."""
        return f"ok {datetime.now(timezone.utc).isoformat(timespec='seconds')}"

    mcp.tool(description="Search the user's Google Drive by file name or content (read-only). Returns up to 10 files: name, id, type, modified date, link.")(drive_search)
    mcp.tool(description="Read the plain text of one Google Drive file by id (read-only; Docs, Sheets, Slides, PDF, Word, TXT, MD, CSV). Long files are truncated.")(drive_read)
    mcp.tool(description="Search the user's Gmail with a Gmail search query, e.g. 'from:ani newer_than:7d' (read-only). Returns up to 10 emails: id, from, subject, date, short snippet.")(gmail_search)
    mcp.tool(description="Read one Gmail email by id from gmail_search (read-only): from, to, subject, date and plain-text body; long bodies are truncated.")(gmail_read)
    mcp.tool(description="Create a DRAFT email in the user's Gmail. It is never sent: there is no send tool, the user reviews and sends it themselves.")(gmail_create_draft)
    return mcp


# ---------- auth ----------

def ensure_key(env_path: Path | None = None) -> str:
    """MCP_BRIDGE_KEY from the environment; when missing, generate one, store it in bff/.env and the environment."""
    key = os.environ.get(ENV_KEY, "").strip()
    if key:
        return key
    path = env_path or config.ROOT / ".env"
    key = secrets.token_urlsafe(32)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    line = f"{ENV_KEY}={key}"
    if re.search(rf"^{ENV_KEY}=\s*$", text, re.M):  # the empty line from .env.example: fill it, no duplicate
        text = re.sub(rf"^{ENV_KEY}=\s*$", line, text, count=1, flags=re.M)
    else:
        text += ("" if not text or text.endswith("\n") else "\n") + line + "\n"
    path.write_text(text, encoding="utf-8")
    os.environ[ENV_KEY] = key
    return key


def _loopback(scope) -> bool:
    client = scope.get("client")
    try:
        return bool(client) and ipaddress.ip_address(client[0]).is_loopback
    except ValueError:
        return False


class BridgeApp:
    """ASGI app: loopback + shared key check in front of the MCP Streamable HTTP app.
    shortcut: loopback + one shared key, upgrade to per-profile keys when Hermes and BFF run on different hosts"""

    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self.inner = mcp.streamable_http_app()  # creates mcp.session_manager; run it in the BFF lifespan: `async with app.mcp.session_manager.run()`

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            expected = os.environ.get(ENV_KEY, "").strip()
            got = {k.lower(): v for k, v in scope["headers"]}.get(b"authorization", b"").decode("latin-1")
            ok = bool(expected) and hmac.compare_digest(got.encode(), f"Bearer {expected}".encode())
            if not _loopback(scope) or not ok:
                status, msg = (403, "Forbidden") if not _loopback(scope) else (401, "Unauthorized")
                await JSONResponse({"error": msg}, status_code=status)(scope, receive, send)
                return
        await self.inner(scope, receive, send)

    def route(self) -> Route:
        return Route("/mcp", endpoint=self)


# ---------- registration in Hermes ----------

def _yaml() -> YAML:
    y = YAML()  # round-trip: keeps other keys and comments
    y.preserve_quotes = True
    return y


def _toolset_for(data) -> bool:
    """Keep `pegawai` selectable on api_server. A platform list that names some configured MCP server is an allowlist
    for MCP servers in Hermes, so then `pegawai` must be named too; otherwise every enabled server is on already.
    Returns True when data changed. Used by harden.harden() as well."""
    servers = data.get("mcp_servers") or {}
    api = (data.get("platform_toolsets") or {}).get("api_server")
    if NAME in servers and isinstance(api, list) and NAME not in api and any(t in servers or t == f"mcp-{s}" for t in api for s in servers):
        api.append(NAME)
        return True
    return False


def _set_profile_env(path: Path, value: str) -> bool:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    line = f"{PROFILE_ENV_KEY}={value}"
    if re.search(rf"^{PROFILE_ENV_KEY}={re.escape(value)}\s*$", text, re.M):
        return False
    if re.search(rf"^{PROFILE_ENV_KEY}=", text, re.M):
        text = re.sub(rf"^{PROFILE_ENV_KEY}=.*$", lambda _: line, text, count=1, flags=re.M)
    else:
        text += ("" if not text or text.endswith("\n") else "\n") + line + "\n"
    path.write_text(text, encoding="utf-8")
    return True


def register_profile(profile: Path, key: str, url: str = URL) -> bool:
    """Make <profile>/config.yaml hold mcp_servers.pegawai (url + Bearer header from the profile .env). True when changed.
    Same shape as `hermes mcp add pegawai --url ... --auth header`; other MCP servers are untouched."""
    path = profile / "config.yaml"
    y = _yaml()
    data = y.load(path.read_text(encoding="utf-8")) or {}
    servers = data.get("mcp_servers")
    if servers is None:
        servers = data["mcp_servers"] = {}
    want = {"url": url, "headers": {"Authorization": f"Bearer ${{{PROFILE_ENV_KEY}}}"}, "enabled": True}
    cur = servers.get(NAME)
    changed = False
    if cur is None:
        servers[NAME] = want
        changed = True
    else:  # only our own fields; a tools filter or timeout someone set stays
        for k, v in want.items():
            if cur.get(k) != v:
                cur[k] = v
                changed = True
    changed |= _toolset_for(data)
    changed |= _set_profile_env(profile / ".env", key)  # the key may have changed even when config.yaml did not
    buf = io.StringIO()
    y.dump(data, buf)
    if buf.getvalue() != path.read_text(encoding="utf-8"):
        backup = path.with_name(f"config.yaml.bak-{date.today():%Y%m%d}")
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_text(buf.getvalue(), encoding="utf-8")
    return changed


def ensure_registered(home: Path | None = None, key: str | None = None) -> list[str]:
    """Register the server in every profile under <hermes home>/profiles. Returns the slugs that changed. Never raises per profile."""
    root = (home or config.HERMES_HOME) / "profiles"
    key = key or os.environ.get(ENV_KEY, "")
    changed = []
    for p in sorted(root.glob("*/")) if root.is_dir() else []:
        if not (p / "config.yaml").is_file():
            continue
        try:
            if register_profile(p, key):
                changed.append(p.name)
        except Exception:
            log.exception("could not register %s in profile %s", NAME, p.name)
    return changed
