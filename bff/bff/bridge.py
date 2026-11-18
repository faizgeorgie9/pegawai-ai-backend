"""Internal MCP server ("pegawai") for the Hermes agents: BFF-provided tools, served as Streamable HTTP at /mcp.

Tools: `ping`, Google Drive search/read/create/update/rename/move, `drive_trash` (only asks the user: see actions.py), `action_status`, and Gmail search/read/create-draft/label/trash plus send and send-draft (these only ask, see actions.py), through the workspace owner's connections, the Knowledge Base tools kb_add_link/kb_add_note/kb_search (kb.py; reversible, no approval), and the board tools task_* (tasks.agent_*: list, create, comment, ask_user, request_review, complete, cancel). Add tools inside build().
A tool that is risky does not act: it stores a pending action (actions.ask) for the user to approve in the app. Each Hermes profile sends `X-Pegawai-Bot: <slug>` so the card can find the chat it came from. Auth: `Authorization: Bearer <MCP_BRIDGE_KEY>`, loopback clients only.
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

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from ruamel.yaml import YAML
from starlette.responses import JSONResponse
from starlette.routing import Route

from . import actions, config, db, integrations, kb
from .errors import ApiError

log = logging.getLogger("bff.bridge")
NAME = "pegawai"
URL = os.environ.get("MCP_BRIDGE_URL", "http://127.0.0.1:8090/mcp")
ENV_KEY = "MCP_BRIDGE_KEY"
BOT_HEADER = "X-Pegawai-Bot"
PROFILE_ENV_KEY = "MCP_PEGAWAI_API_KEY"  # where the key sits in each profile .env (the name `hermes mcp add --auth header` uses)

DRIVE_MAX_CHARS = 50_000
DRIVE_MAX_RESULTS = 10
DRIVE_NOT_CONNECTED = "Google Drive belum disambungkan. Minta pengguna menyambungkannya di halaman Aplikasi."

GMAIL_NOT_CONNECTED = "Gmail belum disambungkan. Minta pengguna menyambungkannya di halaman Aplikasi."
GMAIL_MAX_RESULTS = 10
GMAIL_BODY_MAX = integrations.GMAIL_MAX_BODY

KB_NOTE_MAX = 20_000   # chars of one note; longer text belongs in a file or link
KB_SEARCH_MAX = 5
KB_SNIPPET = 400


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


def _link(name: str, d: dict) -> str:
    return f"{name}: {d['name']} | id: {d['id']} | link: {d['link'] or '-'}"


async def drive_create(name: str, content: str, folder_id: str = "", kind: str = "doc") -> str:
    try:
        return _link("Dibuat", await integrations.drive_create(_user(), name, content, folder_id, kind))
    except ApiError as e:
        return _drive_error(e)


async def drive_update(file_id: str, content: str) -> str:
    try:
        return _link("Isi diganti", await integrations.drive_update(_user(), file_id, content))
    except ApiError as e:
        return _drive_error(e)


async def drive_rename(file_id: str, new_name: str) -> str:
    try:
        return _link("Nama diganti", await integrations.drive_rename(_user(), file_id, new_name))
    except ApiError as e:
        return _drive_error(e)


async def drive_move(file_id: str, folder_id: str) -> str:
    try:
        return _link("Dipindahkan", await integrations.drive_move(_user(), file_id, folder_id))
    except ApiError as e:
        return _drive_error(e)


async def _source(ctx: Context | None) -> dict | None:
    """Where the agent is asking: the profile's bot (header) and the run it is busy with now, so the card can show up in that chat or team."""
    from .engine import ACTIVE  # late import: engine imports harden, which imports this module
    try:
        bot = ctx.request_context.request.headers.get(BOT_HEADER, "") if ctx else ""
        if not re.fullmatch(r"[\w-]{1,64}", bot):
            return None
        run = await db.q1("select id, session_id, group_id from runs where user_id = %s and bot_id = %s and status = any(%s) "
                          "order by created_at desc limit 1", _user(), bot, list(ACTIVE))
        return {"bot_id": bot, **({"run_id": str(run["id"]), "session_id": run["session_id"],
                                  "group_id": str(run["group_id"]) if run["group_id"] else None} if run else {})}
    except Exception:
        log.warning("could not tell where the approval request came from", exc_info=True)
        return None


async def drive_trash(file_id: str, file_name: str = "", ctx: Context = None) -> str:  # type: ignore[assignment]
    """Does not trash anything: asks the user (card in the app). The real call happens in actions after Setujui.
    The card shows the name and owner/folder read from Drive now; file_name (from the agent) is only a marked fallback."""
    file_id = file_id.strip()
    if not integrations.ID_RE.fullmatch(file_id):
        return "Error: invalid file_id (use the id from drive_search)."
    try:
        await integrations.drive_can_write(_user())
    except ApiError as e:
        return _drive_error(e)
    agent_name = re.sub(r"\s+", " ", file_name).strip()[:120]
    try:
        info = await integrations.drive_card_info(_user(), file_id)
    except ApiError as e:
        if e.extra.get("needs"):
            return _drive_error(e)
        info = None  # Drive could not tell now: fall back to the agent's name, marked as such
    if info and info["trashed"]:
        return "Error: berkas ini sudah ada di Sampah Drive."
    payload: dict = {"file_id": file_id, "link": f"https://drive.google.com/open?id={file_id}"}
    if info and info["name"]:
        payload.update(file_name=info["name"], owner=info["owner"], folder=info["folder"])
        summary = f"Pindahkan '{info['name']}' ke Sampah Drive"
        payload["preview"] = "\n".join(x for x in (f"Pemilik: {info['owner']}" if info["owner"] else "", f"Folder: {info['folder']}" if info["folder"] else "") if x)
    else:
        payload.update(file_name=agent_name, name_from_agent=True, preview="Nama ini dari agen; Drive belum bisa memastikannya.")
        summary = f"Pindahkan '{agent_name}' (nama dari agen) ke Sampah Drive" if agent_name else f"Pindahkan berkas Drive (id {file_id}) ke Sampah Drive"
    if not payload["preview"]:
        del payload["preview"]
    a = await actions.ask(_user(), "drive_trash", summary, payload, await _source(ctx))
    return actions.WAITING.format(id=a["short_id"])


async def action_status(id: str) -> str:
    return await actions.status_text(_user(), id)


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


async def gmail_label(message_id: str, add: list[str] | None = None, remove: list[str] | None = None) -> str:
    try:
        return await integrations.gmail_label(_user(), message_id, add, remove)
    except ApiError as e:
        return _gmail_error(e)


async def gmail_trash(message_id: str) -> str:
    try:
        return await integrations.gmail_trash(_user(), message_id)
    except ApiError as e:
        return _gmail_error(e)


async def gmail_send(to: str, subject: str, body: str, reply_to_message_id: str = "", ctx: Context = None) -> str:  # type: ignore[assignment]
    """Does not send anything: stores what would be sent and asks the user. The card shows this stored payload; approve sends exactly it."""
    try:
        p = await integrations.gmail_prepare_send(_user(), to, subject, body, reply_to_message_id)
    except ApiError as e:
        return _gmail_error(e)
    a = await actions.ask(_user(), "gmail_send", f"Kirim email ke {', '.join(p['to'])} — Subjek: {p['subject']}", p, await _source(ctx))
    return actions.WAITING.format(id=a["short_id"])


async def gmail_send_draft(draft_id: str, ctx: Context = None) -> str:  # type: ignore[assignment]
    """Does not send anything: reads the draft from Gmail now and asks the user to approve sending that content."""
    try:
        p = await integrations.gmail_prepare_send_draft(_user(), draft_id)
    except ApiError as e:
        return _gmail_error(e)
    a = await actions.ask(_user(), "gmail_send_draft", f"Kirim draf ke {p['to']} — Subjek: {p['subject'] or '(tanpa subjek)'}", p, await _source(ctx))
    return actions.WAITING.format(id=a["short_id"])


async def _task_tool(fn, *args, ctx: Context | None = None, with_source: bool = True) -> str:
    """Runs a tasks.agent_* function for the calling bot and its active run; an ApiError becomes the tool's error text."""
    from . import tasks  # late import: tasks imports engine, which imports harden, which imports this module
    try:
        return await getattr(tasks, fn)(_user(), *([await _source(ctx)] if with_source else []), *args)
    except ApiError as e:
        return f"Error: {e.message}"


async def task_list(status: str = "") -> str:
    return await _task_tool("agent_list", status, with_source=False)


async def task_create(title: str, instructions: str = "", assignee: str = "", when: str = "", ctx: Context = None) -> str:  # type: ignore[assignment]
    return await _task_tool("agent_create", title, instructions, assignee, when, ctx=ctx)


async def task_comment(text: str, task_id: str = "", ctx: Context = None) -> str:  # type: ignore[assignment]
    return await _task_tool("agent_comment", task_id, text, ctx=ctx)


async def task_ask_user(question: str, task_id: str = "", ctx: Context = None) -> str:  # type: ignore[assignment]
    return await _task_tool("agent_ask_user", question, task_id, ctx=ctx)


async def task_request_review(summary: str, task_id: str = "", ctx: Context = None) -> str:  # type: ignore[assignment]
    return await _task_tool("agent_request_review", task_id, summary, ctx=ctx)


async def task_complete(summary: str, task_id: str = "", ctx: Context = None) -> str:  # type: ignore[assignment]
    return await _task_tool("agent_complete", task_id, summary, ctx=ctx)


async def task_cancel(task_id: str, reason: str = "", ctx: Context = None) -> str:  # type: ignore[assignment]
    return await _task_tool("agent_cancel", task_id, reason, ctx=ctx)


async def kb_add_link(url: str) -> str:
    """Same import path as "Tambah link" on the Pengetahuan page (kb.ingest_url: websites and Google Drive links)."""
    try:
        item = await kb.ingest_url(_user(), url.strip())
    except ApiError as e:
        return f"Error: {e.message}"
    if item["status"] != "ready":
        return f"Gagal disimpan: {item['name']}. Alasan: {item.get('error') or 'tidak diketahui'}"
    return f"Tersimpan di Knowledge Base: {item['name']} (status: siap). Terlihat di halaman Pengetahuan."


async def kb_add_note(title: str, text: str) -> str:
    title, text = re.sub(r"\s+", " ", title).strip()[:80], text.strip()
    if not title or not text:
        return "Error: title and text must not be empty."
    if len(text) > KB_NOTE_MAX:
        return f"Error: catatan terlalu panjang (maksimal {KB_NOTE_MAX} karakter)."
    try:  # a note is a small text file item, so it previews and searches like an upload
        item = await kb.ingest_file(_user(), f"{title}.txt", text.encode())
    except ApiError as e:
        return f"Error: {e.message}"
    if item["status"] != "ready":
        return f"Gagal disimpan: {item['name']}. Alasan: {item.get('error') or 'tidak diketahui'}"
    return f"Catatan tersimpan di Knowledge Base: {item['name']}. Terlihat di halaman Pengetahuan."


async def kb_search(query: str, limit: int = KB_SEARCH_MAX) -> str:
    if not query.strip():
        return "Error: query must not be empty."
    if not 1 <= limit <= KB_SEARCH_MAX:
        return f"Error: limit must be between 1 and {KB_SEARCH_MAX}."
    hits = await kb.search(_user(), query, limit)
    if not hits:
        return "Tidak ada yang cocok di Knowledge Base."
    return "\n".join(f"- [{h['name']}] {' '.join(h['text'].split())[:KB_SNIPPET]}" for h in hits)


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
    mcp.tool(description="Create a new Google Doc (kind='doc', from plain text) or a plain text file (kind='text') in the user's Drive; optional folder_id. Max 1 MB of text. Returns name, id, link.")(drive_create)
    mcp.tool(description="Replace the whole content of a Google Doc or plain text file by id (not PDF or binary files). Max 1 MB of text.")(drive_update)
    mcp.tool(description="Rename a Drive file by id.")(drive_rename)
    mcp.tool(description="Move a Drive file by id into another folder (folder_id, or 'root' for My Drive).")(drive_move)
    mcp.tool(description="Ask to move a Drive file to the Drive trash (restorable for 30 days). Nothing happens until the user approves in the app: the tool only returns a waiting message with an id; do not repeat the request. Pass file_name (from drive_search) so the user sees which file.")(drive_trash)
    mcp.tool(description="Check what happened to a request that waited for the user's approval (id from the 'Menunggu persetujuan' message): waiting, rejected, done or failed.")(action_status)
    mcp.tool(description="Search the user's Gmail with a Gmail search query, e.g. 'from:ani newer_than:7d' (read-only). Returns up to 10 emails: id, from, subject, date, short snippet.")(gmail_search)
    mcp.tool(description="Read one Gmail email by id from gmail_search (read-only): from, to, subject, date and plain-text body; long bodies are truncated.")(gmail_read)
    mcp.tool(description="Create a DRAFT email in the user's Gmail. Creating a draft sends nothing; to send it use gmail_send_draft, which asks the user first.")(gmail_create_draft)
    mcp.tool(description="Add and/or remove labels on one Gmail email by id from gmail_search. Use label ids: system ones such as UNREAD (remove it to mark as read, add it for unread), INBOX (remove it to archive), STARRED, IMPORTANT, or a user label id. Happens at once and is reversible.")(gmail_label)
    mcp.tool(description="Move one Gmail email to the Gmail trash by id (restorable for 30 days; never a permanent delete). Happens at once.")(gmail_trash)
    mcp.tool(description="Ask to send an email (to: up to 10 addresses separated by commas; subject; plain-text body; optional reply_to_message_id from gmail_search to reply in that thread). Nothing is sent until the user approves in the app: the tool only returns a waiting message with an id; do not repeat the request. Write the final text in body: the user sees and approves exactly it.")(gmail_send)
    mcp.tool(description="Ask to send an existing Gmail draft by draft id. Nothing is sent until the user approves the draft content shown in the app; the tool only returns a waiting message with an id; do not repeat the request.")(gmail_send_draft)
    mcp.tool(description="List the owner's tasks on the task board (Papan Tugas): id, title, status, who. Optional status filter (todo, scheduled, ready, running, blocked, review, done, archived). Use it to find a task_id.")(task_list)
    mcp.tool(description="Create a task on the board for work that takes more than one reply or should happen later. instructions = what to do; assignee = a bot id or team name (default: yourself); when = optional future ISO 8601 time with timezone, else the task waits for the owner to start it.")(task_create)
    mcp.tool(description="Add a progress note to a task (task_id defaults to the task you are working on).")(task_comment)
    mcp.tool(description="Ask the owner a question and wait for the answer: it shows in their 'Perlu Anda' list, and the answer comes back as a new message. Use it whenever you need information or a decision, in a task or in a normal chat, instead of guessing. Then stop; do not repeat the question. Always end a task with task_complete, task_request_review or task_ask_user.")(task_ask_user)
    mcp.tool(description="Finish a task by handing the result to the owner to review (summary = the result, in plain language). Use it when the owner should check or approve the work. Always end a task with task_complete, task_request_review or task_ask_user.")(task_request_review)
    mcp.tool(description="Mark a task done with a short summary of the result (use it only when nothing needs the owner's check). Always end a task with task_complete, task_request_review or task_ask_user.")(task_complete)
    mcp.tool(description="Cancel (archive) a task by task_id, with a short reason. Use it when the owner asks to cancel or drop a task or plan; it also cancels its unfinished sub-tasks and can be restored by the owner.")(task_cancel)
    mcp.tool(description="Save a website or Google Drive link into the user's Knowledge Base (reads and stores its text). Use it when the user asks to save/remember a link in the knowledge base. Reversible: the user can delete it on the Pengetahuan page. Afterwards tell the user it is saved and visible on the Pengetahuan page; if it fails, relay the reason.")(kb_add_link)
    mcp.tool(description="Save a short text note (title + text, max 20000 chars) into the user's Knowledge Base. Use it when the user asks to save/remember something in the knowledge base. Reversible: the user can delete it on the Pengetahuan page. Afterwards tell the user it is saved and visible on the Pengetahuan page.")(kb_add_note)
    mcp.tool(description="Search the user's Knowledge Base by keywords (read-only). Returns up to 5 snippets, each with its source name in brackets.")(kb_search)
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
    want = {"url": url, "headers": {"Authorization": f"Bearer ${{{PROFILE_ENV_KEY}}}", BOT_HEADER: profile.name}, "enabled": True}
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
