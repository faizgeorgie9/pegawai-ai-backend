"""MCP bridge: auth (key + loopback), ping through a real MCP client, idempotent registration in Hermes profiles, harden keeps `pegawai`."""
import asyncio
import base64

import httpx
import pytest
import respx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from ruamel.yaml import YAML

from bff import bridge, connections, harden, integrations, kb
from bff.errors import ApiError

KEY = "test-bridge-key"
URL = "http://127.0.0.1/mcp"
INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
    "protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}}
HDRS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv(bridge.ENV_KEY, KEY)
    return bridge.BridgeApp(bridge.build())


@pytest.fixture(autouse=True)
def bridge_owner(monkeypatch):
    """The bridge resolves each MCP request to a bot owner; unit tests have no bot table."""
    async def owner(_bot=None):
        return "default"
    monkeypatch.setattr(bridge, "resolve_owner", owner)


def client_for(app, host="127.0.0.1", **kw):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=(host, 5000)), **kw)


def run_with_manager(app, coro_fn):
    async def go():
        async with app.mcp.session_manager.run():
            return await coro_fn()
    return asyncio.run(go())


@pytest.mark.parametrize("auth, host, status", [
    (None, "127.0.0.1", 401), ("Bearer wrong", "127.0.0.1", 401), (f"Bearer {KEY}x", "127.0.0.1", 401),
    (f"Bearer {KEY}", "10.1.2.3", 403), (f"Bearer {KEY}", "127.0.0.1", 200)])
def test_auth(app, auth, host, status):
    async def call():
        async with client_for(app, host) as c:
            return (await c.post(URL, json=INIT, headers={**HDRS, **({"Authorization": auth} if auth else {})})).status_code
    assert run_with_manager(app, call) == status


def test_empty_server_key_rejects_everything(app, monkeypatch):
    monkeypatch.setenv(bridge.ENV_KEY, "")
    async def call():
        async with client_for(app) as c:
            return (await c.post(URL, json=INIT, headers={**HDRS, "Authorization": "Bearer "})).status_code
    assert run_with_manager(app, call) == 401


def test_ping_through_mcp_client(app):
    async def call():
        http = client_for(app, headers={"Authorization": f"Bearer {KEY}"})
        async with streamable_http_client(URL, http_client=http) as (r, w, _):
            async with ClientSession(r, w) as s:
                await s.initialize()
                assert sorted(t.name for t in (await s.list_tools()).tools) == ["action_status", "drive_create", "drive_move", "drive_read", "drive_rename", "drive_search", "drive_trash", "drive_update", "gmail_create_draft", "gmail_label", "gmail_read", "gmail_search", "gmail_send", "gmail_send_draft", "gmail_trash", "kb_add_link", "kb_add_note", "kb_search", "ping", "task_ask_user", "task_cancel", "task_comment", "task_complete", "task_create", "task_list", "task_request_review"]
                return (await s.call_tool("ping", {})).content[0].text
    out = run_with_manager(app, call)
    assert out.startswith("ok 20")


def test_ensure_key_fills_empty_line_and_is_stable(tmp_path, monkeypatch):
    monkeypatch.delenv(bridge.ENV_KEY, raising=False)
    env = tmp_path / ".env"
    env.write_text("A=1\nMCP_BRIDGE_KEY=\nB=2\n", encoding="utf-8")
    key = bridge.ensure_key(env)
    assert env.read_text(encoding="utf-8") == f"A=1\nMCP_BRIDGE_KEY={key}\nB=2\n"
    assert bridge.ensure_key(env) == key
    monkeypatch.delenv(bridge.ENV_KEY)
    env.write_text("A=1", encoding="utf-8")
    key2 = bridge.ensure_key(env)
    assert env.read_text(encoding="utf-8") == f"A=1\nMCP_BRIDGE_KEY={key2}\n"


def _profile(tmp_path, text):
    p = tmp_path / "profiles" / "mira"
    p.mkdir(parents=True)
    (p / "config.yaml").write_text(text, encoding="utf-8")
    return p


def _load(p):
    return YAML().load((p / "config.yaml").read_text(encoding="utf-8"))


BASE = "model: x\nmcp_servers:\n  other:\n    url: http://x/mcp\nplatform_toolsets:\n  api_server:\n  - web\n"


def test_registration_idempotent_and_keeps_other_servers(tmp_path):
    p = _profile(tmp_path, BASE)
    assert bridge.ensure_registered(tmp_path, KEY) == ["mira"]
    first = (p / "config.yaml").read_text(encoding="utf-8")
    d = _load(p)
    assert d["mcp_servers"]["pegawai"]["url"] == bridge.URL
    assert d["mcp_servers"]["pegawai"]["headers"]["Authorization"] == "Bearer ${MCP_PEGAWAI_API_KEY}"
    assert d["mcp_servers"]["pegawai"]["headers"]["X-Pegawai-Bot"] == "mira"  # lets an approval card find the chat it came from
    assert d["mcp_servers"]["other"]["url"] == "http://x/mcp"
    assert f"MCP_PEGAWAI_API_KEY={KEY}" in (p / ".env").read_text(encoding="utf-8")
    assert bridge.ensure_registered(tmp_path, KEY) == []
    assert (p / "config.yaml").read_text(encoding="utf-8") == first
    assert bridge.ensure_registered(tmp_path, "rotated") == ["mira"]  # a new key only touches the profile .env
    assert (p / "config.yaml").read_text(encoding="utf-8") == first
    assert (p / ".env").read_text(encoding="utf-8").count("MCP_PEGAWAI_API_KEY=") == 1


def test_harden_keeps_pegawai(tmp_path, monkeypatch):
    p = _profile(tmp_path, BASE.replace("- web", "- web\n  - terminal\n  - other"))  # api_server already names an MCP server: an allowlist
    bridge.ensure_registered(tmp_path, KEY)
    assert "pegawai" in _load(p)["platform_toolsets"]["api_server"]
    monkeypatch.setattr(harden.hermes, "profile_dir", lambda slug: p)
    monkeypatch.setattr(harden, "cli_enabled_toolsets", lambda slug: ["web", "terminal"])
    assert harden.harden("mira") is True
    d = _load(p)
    assert list(d["platform_toolsets"]["api_server"]) == ["web", "other", "pegawai", "clarify"]
    assert d["mcp_servers"]["pegawai"]["enabled"] is True
    assert harden.harden("mira") is False


# ---------- Drive tools (Google mocked with respx; the token comes from a stub) ----------

def call_tool(app, name, args, extra_headers=None):
    app = bridge.BridgeApp(bridge.build())  # a session manager runs once per app, so each call gets its own
    async def call():
        http = client_for(app, headers={"Authorization": f"Bearer {KEY}", **(extra_headers or {})})
        async with streamable_http_client(URL, http_client=http) as (r, w, _):
            async with ClientSession(r, w) as s:
                await s.initialize()
                return (await s.call_tool(name, args)).content[0].text
    return run_with_manager(app, call)


def test_tool_runs_as_the_bot_owner_not_the_default_tenant(monkeypatch, app):
    """X-Pegawai-Bot names the profile; the bridge must use that bot's owner for Drive/KB/task tools."""
    seen = []

    async def resolve(bot=None):
        seen.append(bot)
        return "user_owner"

    async def search(user_id, text, limit, bot_id=None):
        return [{"name": "katalog.md", "text": f"pemilik={user_id}"}]

    monkeypatch.setattr(bridge, "resolve_owner", resolve)
    monkeypatch.setattr(kb, "search", search)
    app = bridge.BridgeApp(bridge.build())
    out = call_tool(app, "kb_search", {"query": "kaos"}, {"X-Pegawai-Bot": "mira"})
    assert seen and set(seen) == {"mira"}
    assert "pemilik=user_owner" in out


@pytest.fixture
def drive(monkeypatch):
    async def token(user_id, provider):
        assert (user_id, provider) == ("default", "gdrive")
        return "at-secret"
    monkeypatch.setattr(connections, "access_token", token)


def test_drive_search_maps_files(app, drive):
    with respx.mock:
        r = respx.get(f"{integrations.DRIVE_API}/files").respond(json={"files": [
            {"id": "doc12345", "name": "Proposal Q4", "mimeType": "application/vnd.google-apps.document",
             "modifiedTime": "2026-11-10T08:00:00Z", "webViewLink": "https://docs.google.com/document/d/doc12345"},
            {"id": "img12345", "name": "Foto", "mimeType": "image/png"}]})
        out = call_tool(app, "drive_search", {"query": "proposal", "limit": 3})
    q = r.calls[0].request.url.params
    assert q["pageSize"] == "3" and "fullText contains 'proposal'" in q["q"]
    assert out == "- Proposal Q4 | id: doc12345 | type: Google Docs | modified: 2026-11-10 | link: https://docs.google.com/document/d/doc12345"
    assert "at-secret" not in out


def test_drive_search_rejects_bad_limit(app, drive):
    assert "limit must be between 1 and 10" in call_tool(app, "drive_search", {"query": "x", "limit": 11})
    assert "limit must be between" in call_tool(app, "drive_search", {"query": "x", "limit": 0})


def test_drive_read_truncates(app, drive):
    with respx.mock:
        respx.get(f"{integrations.DRIVE_API}/files/doc12345").respond(json={"id": "doc12345", "name": "Panjang", "mimeType": "application/vnd.google-apps.document"})
        respx.get(f"{integrations.DRIVE_API}/files/doc12345/export").respond(text="a" * 60_000)
        out = call_tool(app, "drive_read", {"file_id": "doc12345"})
    assert out.startswith("# Panjang") and "[dipotong" in out and out.split("\n")[2] == "a" * bridge.DRIVE_MAX_CHARS


def test_drive_not_connected_message(app, monkeypatch):
    async def token(user_id, provider):
        raise ApiError(409, "Google Drive belum tersambung. Buka Aplikasi untuk menghubungkannya.", needs="connect")
    monkeypatch.setattr(connections, "access_token", token)
    msg = "Google Drive belum disambungkan. Minta pengguna menyambungkannya di halaman Aplikasi."
    assert call_tool(app, "drive_search", {"query": "x"}) == msg
    assert call_tool(app, "drive_read", {"file_id": "doc12345"}) == msg


def test_drive_read_rejects_invalid_id_and_hides_provider_errors(app, drive):
    with respx.mock:
        r = respx.get(url__startswith=integrations.DRIVE_API).respond(500, text="at-secret raw body")
        assert "invalid file_id" in call_tool(app, "drive_read", {"file_id": "../x?y"})
        assert r.call_count == 0
        out = call_tool(app, "drive_read", {"file_id": "doc12345"})
    assert out == "Error: Google Drive menjawab dengan kesalahan 500." and "secret" not in out



# ---------- Gmail tools ----------

def b64(s):
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")


@pytest.fixture
def gmail(monkeypatch):
    async def token(user_id, provider):
        assert (user_id, provider) == ("default", "gmail")
        return "at-secret"
    async def has_scope(user_id, provider, scope):
        return True
    async def account_of(user_id, provider):
        return "me@example.com"
    monkeypatch.setattr(connections, "access_token", token)
    monkeypatch.setattr(connections, "has_scope", has_scope)
    monkeypatch.setattr(connections, "account_of", account_of)


def test_gmail_search_maps_messages(app, gmail):
    with respx.mock:
        lst = respx.get(f"{integrations.GMAIL_API}/users/me/messages").respond(json={"messages": [{"id": "msg12345"}]})
        respx.get(f"{integrations.GMAIL_API}/users/me/messages/msg12345").respond(json={
            "id": "msg12345", "snippet": "Halo &amp; selamat", "payload": {"headers": [
                {"name": "From", "value": "Ani <ani@example.com>"}, {"name": "Subject", "value": "Rapat"}, {"name": "Date", "value": "Mon, 16 Nov 2026"}]}})
        out = call_tool(app, "gmail_search", {"query": "from:ani", "limit": 3})
    q = lst.calls[0].request.url.params
    assert q["q"] == "from:ani" and q["maxResults"] == "3"
    assert out == "- id: msg12345 | from: Ani <ani@example.com> | subject: Rapat | date: Mon, 16 Nov 2026 | Halo & selamat"
    assert "at-secret" not in out
    assert "limit must be between" in call_tool(app, "gmail_search", {"query": "x", "limit": 11})


def test_gmail_read_html_to_text_and_truncates(app, gmail):
    html_body = "<html><head><style>p{}</style></head><body><p>Halo Budi</p><p>" + "a" * 25_000 + "</p></body></html>"
    msg = {"id": "msg12345", "payload": {"mimeType": "multipart/mixed", "headers": [
        {"name": "From", "value": "ani@example.com"}, {"name": "To", "value": "me@example.com"},
        {"name": "Subject", "value": "Laporan"}, {"name": "Date", "value": "Mon, 16 Nov 2026"}],
        "parts": [{"mimeType": "text/html", "body": {"data": b64(html_body)}},
                  {"mimeType": "text/plain", "filename": "x.txt", "body": {"data": b64("lampiran")}}]}}
    with respx.mock:
        r = respx.get(f"{integrations.GMAIL_API}/users/me/messages/msg12345").respond(json=msg)
        out = call_tool(app, "gmail_read", {"message_id": "msg12345"})
    assert r.calls[0].request.url.params["format"] == "full"
    head, body = out.split("\n\n", 1)
    assert head == "From: ani@example.com\nTo: me@example.com\nSubject: Laporan\nDate: Mon, 16 Nov 2026"
    assert body.startswith("Halo Budi\naaa") and "<" not in body and "lampiran" not in body
    assert body.index("\n[dipotong") == bridge.GMAIL_BODY_MAX


def test_gmail_draft_only_calls_drafts_endpoint(app, gmail):
    with respx.mock:
        r = respx.post(f"{integrations.GMAIL_API}/users/me/drafts").respond(json={"id": "dr1"})
        out = call_tool(app, "gmail_create_draft", {"to": "ani@example.com", "subject": "Hai", "body": "Isi"})
        assert [c.request.url.path for c in respx.calls] == ["/gmail/v1/users/me/drafts"]
    assert r.call_count == 1 and "belum terkirim" in out and "#drafts" in out


def test_gmail_missing_read_scope(app, monkeypatch):
    async def token(user_id, provider):
        return "at-secret"
    async def no_scope(user_id, provider, scope):
        return False
    monkeypatch.setattr(connections, "access_token", token)
    monkeypatch.setattr(connections, "has_scope", no_scope)
    msg = "Error: Sambungkan ulang Gmail di halaman Aplikasi untuk memberi izin membaca."
    with respx.mock:
        r = respx.route(url__startswith=integrations.GMAIL_API)
        assert call_tool(app, "gmail_search", {"query": "x"}) == msg
        assert call_tool(app, "gmail_read", {"message_id": "msg12345"}) == msg
    assert r.call_count == 0


def test_gmail_not_connected_message(app, monkeypatch):
    async def token(user_id, provider):
        raise ApiError(409, "Gmail belum tersambung. Buka Aplikasi untuk menghubungkannya.", needs="connect")
    monkeypatch.setattr(connections, "access_token", token)
    msg = "Gmail belum disambungkan. Minta pengguna menyambungkannya di halaman Aplikasi."
    assert call_tool(app, "gmail_search", {"query": "x"}) == msg
    assert call_tool(app, "gmail_read", {"message_id": "msg12345"}) == msg
    assert call_tool(app, "gmail_create_draft", {"to": "ani@example.com", "subject": "s", "body": "b"}) == msg


def test_gmail_rejects_invalid_id_and_address_and_hides_provider_errors(app, gmail):
    with respx.mock:
        r = respx.route(url__startswith=integrations.GMAIL_API).respond(500, text="at-secret raw body")
        assert "invalid message_id" in call_tool(app, "gmail_read", {"message_id": "../x?y"})
        assert "tidak valid" in call_tool(app, "gmail_create_draft", {"to": "bukan-email", "subject": "s", "body": "b"})
        assert r.call_count == 0
        out = call_tool(app, "gmail_read", {"message_id": "msg12345"})
    assert out == "Error: Gmail menjawab dengan kesalahan 500." and "secret" not in out


# ---------- Knowledge Base tools (kb.py DB functions replaced; the tools only wrap them) ----------

def test_kb_add_link_reports_item_and_friendly_failure(app, monkeypatch):
    async def ingest(user_id, url):
        assert user_id == "default"
        if "drive" in url:
            return {"name": "drive.google.com/x", "status": "failed", "error": kb.DRIVE_NEEDS_CONNECT}
        return {"name": "toko.id/harga", "status": "ready"}
    monkeypatch.setattr(kb, "ingest_url", ingest)
    ok = call_tool(app, "kb_add_link", {"url": " https://toko.id/harga "})
    assert "toko.id/harga" in ok and "halaman Pengetahuan" in ok
    bad = call_tool(app, "kb_add_link", {"url": "https://drive.google.com/x"})
    assert bad.startswith("Gagal disimpan") and kb.DRIVE_NEEDS_CONNECT in bad

    async def invalid(user_id, url):
        raise ApiError(400, "Masukkan alamat web yang diawali http:// atau https://")
    monkeypatch.setattr(kb, "ingest_url", invalid)
    assert call_tool(app, "kb_add_link", {"url": "toko"}) == "Error: Masukkan alamat web yang diawali http:// atau https://"


def test_kb_add_note_saves_text_file_and_limits_size(app, monkeypatch):
    saved = []
    async def ingest(user_id, name, data):
        saved.append((name, data))
        return {"name": name, "status": "ready"}
    monkeypatch.setattr(kb, "ingest_file", ingest)
    out = call_tool(app, "kb_add_note", {"title": "Jam CS", "text": "Sabtu tutup"})
    assert saved == [("Jam CS.txt", b"Sabtu tutup")] and "Jam CS.txt" in out and "halaman Pengetahuan" in out
    assert "terlalu panjang" in call_tool(app, "kb_add_note", {"title": "x", "text": "a" * (bridge.KB_NOTE_MAX + 1)})
    assert "must not be empty" in call_tool(app, "kb_add_note", {"title": " ", "text": "a"})
    assert len(saved) == 1


def test_kb_search_snippets_with_source_and_limit(app, monkeypatch):
    seen = {}
    async def search(user_id, text, limit):
        seen["limit"] = limit
        return [{"name": "katalog.md", "text": "Kaos\n\npolos " + "x" * 600}]
    monkeypatch.setattr(kb, "search", search)
    out = call_tool(app, "kb_search", {"query": "harga kaos", "limit": 2})
    assert seen["limit"] == 2 and out.startswith("- [katalog.md] Kaos polos x") and len(out) < 450
    assert "limit must be between 1 and 5" in call_tool(app, "kb_search", {"query": "x", "limit": 6})

    async def none(user_id, text, limit):
        return []
    monkeypatch.setattr(kb, "search", none)
    assert call_tool(app, "kb_search", {"query": "zzz"}) == "Tidak ada yang cocok di Knowledge Base."
