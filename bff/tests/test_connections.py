"""Connections (Google Drive, Gmail, Notion): OAuth state and PKCE, encrypted token storage, refresh and revoked grants,
Drive / Notion import, Gmail draft shape, user scoping. Provider endpoints are mocked with respx; nothing leaves the machine.
The tests marked with_db need TEST_DATABASE_URL (see test_scheduler.py)."""
import asyncio
import base64
import email
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
import respx
from cryptography.fernet import Fernet
from test_scheduler import with_db

from bff import config, connections, integrations, kb
from bff.errors import ApiError


@pytest.fixture(autouse=True)
def creds(monkeypatch):
    monkeypatch.setattr(config, "GOOGLE_CLIENT_ID", "gid")
    monkeypatch.setattr(config, "GOOGLE_CLIENT_SECRET", "gsecret")
    monkeypatch.setattr(config, "NOTION_CLIENT_ID", "nid")
    monkeypatch.setattr(config, "NOTION_CLIENT_SECRET", "nsecret")
    monkeypatch.setattr(config, "CONNECTIONS_KEY", Fernet.generate_key().decode())
    monkeypatch.setattr(config, "PUBLIC_BASE_URL", "http://localhost:5173")


def uid():
    return f"u-{uuid.uuid4().hex[:8]}"


def qs(url):
    return {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}


async def consent(user, provider):
    """Start a consent and return (state, query of the callback redirect target is checked by callers)."""
    return qs((await connections.start(user, provider))["url"])["state"]


def google_ok(scope, refresh="rt-1", expires_in=3600):
    return {"access_token": "at-1", "refresh_token": refresh, "expires_in": expires_in, "scope": scope}


DRIVE_SCOPE = "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/drive.readonly"
GMAIL_SCOPE = "openid https://www.googleapis.com/auth/gmail.compose"


async def connect_google(user, provider="gdrive", scope=DRIVE_SCOPE):
    state = await consent(user, provider)
    with respx.mock:
        respx.post(connections.GOOGLE_TOKEN).respond(json=google_ok(scope))
        respx.get(connections.GOOGLE_USERINFO).respond(json={"email": "owner@example.com"})
        return await connections.callback(user, "google", {"code": "c1", "state": state})


# ---------- configuration ----------

def test_missing_env_means_not_configured(monkeypatch):
    monkeypatch.setattr(config, "GOOGLE_CLIENT_ID", "")
    assert not connections.configured("gdrive") and not connections.configured("gmail") and connections.configured("notion")
    monkeypatch.setattr(config, "CONNECTIONS_KEY", "")
    assert not connections.configured("notion")  # no key: no tokens are ever stored
    with pytest.raises(ApiError) as e:
        connections.encrypt("secret-token")
    assert e.value.status == 503


def test_invalid_key_is_refused(monkeypatch):
    monkeypatch.setattr(config, "CONNECTIONS_KEY", "not-a-fernet-key")
    with pytest.raises(ApiError):
        connections.encrypt("x")


def test_encryption_round_trip():
    enc = connections.encrypt("ya29.secret")
    assert "ya29" not in enc and connections.decrypt(enc) == "ya29.secret"


@with_db
async def test_list_states_and_start_refuses_when_not_configured(db):
    u = uid()
    config.GOOGLE_CLIENT_SECRET = ""  # the autouse fixture restores it
    got = {c["provider"]: c["status"] for c in await connections.list_all(u)}
    assert got == {"gdrive": "not_configured", "gmail": "not_configured", "notion": "disconnected"}
    with pytest.raises(ApiError) as e:
        await connections.start(u, "gdrive")
    assert e.value.status == 409 and "administrator" in e.value.message
    with pytest.raises(ApiError):
        await connections.start(u, "dropbox")


# ---------- start: consent address, state, PKCE ----------

@with_db
async def test_google_consent_url_has_state_pkce_and_exact_scopes(db):
    u = uid()
    q = qs((await connections.start(u, "gdrive"))["url"])
    assert q["client_id"] == "gid" and q["response_type"] == "code" and q["access_type"] == "offline"
    assert q["redirect_uri"] == "http://localhost:5173/bff/api/connections/google/callback"
    assert q["scope"].split() == ["openid", "email", "https://www.googleapis.com/auth/drive.readonly"]
    assert q["code_challenge_method"] == "S256" and len(q["state"]) >= 40
    row = await db.q1("select * from oauth_states where user_id = %s", u)
    assert row["state_hash"] != q["state"] and row["provider"] == "gdrive"  # only the hash is stored
    expected = base64.urlsafe_b64encode(hashlib.sha256(row["verifier"].encode()).digest()).rstrip(b"=").decode()
    assert q["code_challenge"] == expected
    gm = qs((await connections.start(u, "gmail"))["url"])
    assert gm["scope"].split() == ["openid", "email", "https://www.googleapis.com/auth/gmail.compose"]


@with_db
async def test_notion_consent_url(db):
    q = qs((await connections.start(uid(), "notion"))["url"])
    assert q["client_id"] == "nid" and q["owner"] == "user" and q["state"] and "code_challenge" not in q
    assert q["redirect_uri"] == "http://localhost:5173/bff/api/connections/notion/callback"


# ---------- callback: state ----------

@with_db
async def test_state_wrong_user_expired_reused_and_wrong_family(db):
    a, b = uid(), uid()
    # wrong user
    s = await consent(a, "gdrive")
    assert "reason=state" in await connections.callback(b, "google", {"code": "c", "state": s})
    # a consumed state cannot be used again, not even by the right user
    assert "reason=state" in await connections.callback(a, "google", {"code": "c", "state": s})
    # expired
    s = await consent(a, "gdrive")
    await db.ex("update oauth_states set expires_at = now() - interval '1 minute' where user_id = %s", a)
    assert "reason=state" in await connections.callback(a, "google", {"code": "c", "state": s})
    # a Google state does not finish a Notion callback
    s = await consent(a, "gdrive")
    assert "reason=state" in await connections.callback(a, "notion", {"code": "c", "state": s})
    # unknown or missing
    assert "reason=state" in await connections.callback(a, "google", {"code": "c", "state": "nope"})
    assert "reason=state" in await connections.callback(a, "google", {"code": "c"})
    assert not await db.q1("select 1 from connections where user_id in (%s, %s)", a, b)


@with_db
async def test_user_denying_consent_stores_nothing(db):
    u = uid()
    s = await consent(u, "gdrive")
    url = await connections.callback(u, "google", {"error": "access_denied", "state": s})
    assert "connect=error" in url and "reason=denied" in url and "app=gdrive" in url
    assert not await db.q1("select 1 from connections where user_id = %s", u)


# ---------- callback: exchange and storage ----------

@with_db
async def test_callback_stores_encrypted_tokens_with_pkce_verifier(db):
    u = uid()
    state = await consent(u, "gdrive")
    verifier = (await db.q1("select verifier from oauth_states where user_id = %s", u))["verifier"]
    with respx.mock:
        tok = respx.post(connections.GOOGLE_TOKEN).respond(json=google_ok(DRIVE_SCOPE))
        info = respx.get(connections.GOOGLE_USERINFO).respond(json={"email": "owner@example.com"})
        url = await connections.callback(u, "google", {"code": "the-code", "state": state})
    assert "connect=ok" in url and "app=gdrive" in url
    sent = parse_qs(tok.calls[0].request.content.decode())
    assert sent["code_verifier"] == [verifier] and sent["code"] == ["the-code"] and sent["grant_type"] == ["authorization_code"]
    assert info.calls[0].request.headers["authorization"] == "Bearer at-1"
    row = await db.q1("select * from connections where user_id = %s", u)
    assert "at-1" not in json.dumps(row, default=str) and "rt-1" not in json.dumps(row, default=str)  # no plaintext in the database
    assert connections.decrypt(row["access_enc"]) == "at-1" and connections.decrypt(row["refresh_enc"]) == "rt-1"
    assert row["account"] == "owner@example.com" and "https://www.googleapis.com/auth/drive.readonly" in row["scopes"]
    assert row["expires_at"] > datetime.now(timezone.utc) + timedelta(minutes=50)
    got = {c["provider"]: c for c in await connections.list_all(u)}
    assert got["gdrive"]["status"] == "connected" and got["gdrive"]["account"] == "owner@example.com"
    assert got["gmail"]["status"] == "disconnected"


@with_db
async def test_callback_without_the_needed_permission_stores_nothing(db):
    u = uid()
    url = await connect_google(u, "gdrive", scope="openid email")  # the person unticked the Drive permission
    assert "reason=scope" in url
    assert not await db.q1("select 1 from connections where user_id = %s", u)


@with_db
async def test_callback_token_failure_is_an_error_not_a_connection(db):
    u = uid()
    state = await consent(u, "gdrive")
    with respx.mock:
        respx.post(connections.GOOGLE_TOKEN).respond(400, json={"error": "invalid_grant"})
        url = await connections.callback(u, "google", {"code": "bad", "state": state})
    assert "reason=exchange" in url and not await db.q1("select 1 from connections where user_id = %s", u)


@with_db
async def test_notion_callback_uses_basic_auth_and_labels_workspace(db):
    u = uid()
    state = await consent(u, "notion")
    with respx.mock:
        tok = respx.post(connections.NOTION_TOKEN).respond(json={"access_token": "secret_n", "workspace_name": "Toko Kaos"})
        url = await connections.callback(u, "notion", {"code": "nc", "state": state})
    assert "connect=ok" in url
    req = tok.calls[0].request
    assert req.headers["authorization"] == "Basic " + base64.b64encode(b"nid:nsecret").decode()
    assert json.loads(req.content)["redirect_uri"].endswith("/bff/api/connections/notion/callback")
    row = await db.q1("select * from connections where user_id = %s", u)
    assert row["account"] == "Toko Kaos" and row["expires_at"] is None and "secret_n" not in json.dumps(row, default=str)
    assert await connections.access_token(u, "notion") == "secret_n"


# ---------- refresh, revoked, disconnect, scoping ----------

@with_db
async def test_expired_access_token_is_refreshed(db):
    u = uid()
    await connect_google(u)
    await db.ex("update connections set expires_at = now() - interval '1 minute' where user_id = %s", u)
    with respx.mock:
        r = respx.post(connections.GOOGLE_TOKEN).respond(json={"access_token": "at-2", "expires_in": 3600})
        assert await connections.access_token(u, "gdrive") == "at-2"
    assert parse_qs(r.calls[0].request.content.decode())["refresh_token"] == ["rt-1"]
    row = await db.q1("select * from connections where user_id = %s", u)
    assert connections.decrypt(row["access_enc"]) == "at-2" and connections.decrypt(row["refresh_enc"]) == "rt-1" and row["status"] == "connected"
    with respx.mock:  # still valid: no network call
        assert await connections.access_token(u, "gdrive") == "at-2"


@with_db
async def test_revoked_refresh_token_needs_reconnect(db):
    u = uid()
    await connect_google(u)
    await db.ex("update connections set expires_at = now() - interval '1 minute' where user_id = %s", u)
    with respx.mock:
        respx.post(connections.GOOGLE_TOKEN).respond(400, json={"error": "invalid_grant"})
        with pytest.raises(ApiError) as e:
            await connections.access_token(u, "gdrive")
    assert e.value.status == 409 and e.value.extra["needs"] == "reconnect" and "disambungkan ulang" in e.value.message
    assert {c["provider"]: c["status"] for c in await connections.list_all(u)}["gdrive"] == "reconnect"
    with respx.mock:  # marked: no more attempts against Google
        with pytest.raises(ApiError):
            await connections.access_token(u, "gdrive")
    state = await consent(u, "gdrive")  # connecting again fixes it
    with respx.mock:
        respx.post(connections.GOOGLE_TOKEN).respond(json=google_ok(DRIVE_SCOPE, refresh="rt-9"))
        respx.get(connections.GOOGLE_USERINFO).respond(json={"email": "owner@example.com"})
        await connections.callback(u, "google", {"code": "c", "state": state})
    assert {c["provider"]: c["status"] for c in await connections.list_all(u)}["gdrive"] == "connected"


@with_db
async def test_provider_401_marks_reconnect(db):
    u = uid()
    await connect_google(u)
    with respx.mock:
        respx.get(f"{integrations.DRIVE_API}/files").respond(401, json={})
        with pytest.raises(ApiError) as e:
            await integrations.drive_list(u)
    assert e.value.extra["needs"] == "reconnect"
    assert {c["provider"]: c["status"] for c in await connections.list_all(u)}["gdrive"] == "reconnect"


@with_db
async def test_disconnect_revokes_and_deletes_unless_the_other_google_connection_needs_the_grant(db):
    u = uid()
    await connect_google(u, "gdrive")
    await connect_google(u, "gmail", GMAIL_SCOPE)
    with respx.mock:
        revoke = respx.post(connections.GOOGLE_REVOKE).respond(200)
        await connections.disconnect(u, "gdrive")
        assert not revoke.called  # Gmail still uses the same Google grant
        await connections.disconnect(u, "gmail")
        assert revoke.called and parse_qs(revoke.calls[0].request.content.decode())["token"] == ["rt-1"]
    assert not await db.q1("select 1 from connections where user_id = %s", u)
    with respx.mock:  # unreachable provider: tokens are still deleted
        await connect_google(u)
        respx.post(connections.GOOGLE_REVOKE).mock(side_effect=httpx.ConnectError("down"))
        await connections.disconnect(u, "gdrive")
    assert not await db.q1("select 1 from connections where user_id = %s", u)


@with_db
async def test_connections_are_per_user(db):
    a, b = uid(), uid()
    await connect_google(a)
    assert await connections.access_token(a, "gdrive") == "at-1"
    with pytest.raises(ApiError) as e:
        await connections.access_token(b, "gdrive")
    assert e.value.extra["needs"] == "connect"
    assert {c["provider"]: c["status"] for c in await connections.list_all(b)}["gdrive"] == "disconnected"
    await connections.disconnect(b, "gdrive")  # B cannot delete A's connection
    assert await connections.is_connected(a, "gdrive")


# ---------- Drive ----------

def test_drive_type_mapping():
    assert integrations.drive_kind("application/vnd.google-apps.document") == "Google Docs"
    assert integrations.drive_kind("application/vnd.google-apps.spreadsheet") == "Google Sheets"
    assert integrations.drive_kind("application/pdf") == "PDF"
    assert integrations.drive_kind(integrations.DOCX) == "Word"
    assert integrations.drive_kind("application/vnd.google-apps.folder") is None
    assert integrations.drive_kind("image/png") is None
    assert integrations.drive_file_id("https://docs.google.com/document/d/AbC_123-x/edit") == "AbC_123-x"
    assert integrations.drive_file_id("https://drive.google.com/open?id=FILE-id_9") == "FILE-id_9"


@with_db
async def test_drive_list_query_and_filter(db):
    u = uid()
    await connect_google(u)
    with respx.mock:
        r = respx.get(f"{integrations.DRIVE_API}/files").respond(json={"nextPageToken": "n2", "files": [
            {"id": "f1", "name": "Katalog", "mimeType": "application/vnd.google-apps.document", "modifiedTime": "2026-11-10T01:00:00Z"},
            {"id": "f2", "name": "foto", "mimeType": "image/png"},
            {"id": "f3", "name": "Laporan.pdf", "mimeType": "application/pdf", "size": "2048"}]})
        out = await integrations.drive_list(u, "o'brien", None)
    q = qs(str(r.calls[0].request.url))
    assert "name contains 'o\\'brien'" in q["q"] and "trashed = false" in q["q"]
    assert r.calls[0].request.headers["authorization"] == "Bearer at-1"
    assert [f["id"] for f in out["files"]] == ["f1", "f3"] and out["next"] == "n2" and out["files"][1]["size"] == 2048


@with_db
async def test_drive_import_exports_google_files_and_replaces_on_reimport(db):
    u = uid()
    await connect_google(u)
    base = integrations.DRIVE_API
    with respx.mock:
        respx.get(f"{base}/files/doc11").respond(json={"id": "doc11", "name": "Katalog 2026", "mimeType": "application/vnd.google-apps.document",
                                                      "webViewLink": "https://docs.google.com/document/d/doc11/edit"})
        respx.get(f"{base}/files/sheet1").respond(json={"id": "sheet1", "name": "Harga", "mimeType": "application/vnd.google-apps.spreadsheet"})
        doc = respx.get(f"{base}/files/doc11/export").respond(text="﻿Kaos polos tersedia ukuran S M L.")
        sheet = respx.get(f"{base}/files/sheet1/export").respond(text="produk,harga\nKaos,75000")
        res = await integrations.drive_import(u, ["doc11", "sheet1"])
        assert qs(str(doc.calls[0].request.url))["mimeType"] == "text/plain"
        assert qs(str(sheet.calls[0].request.url))["mimeType"] == "text/csv"
        assert [r["status"] for r in res] == ["ready", "ready"] and res[0]["kind"] == "gdrive" and res[0]["refreshable"]
        assert res[0]["source"] == "https://docs.google.com/document/d/doc11/edit"
        again = await integrations.refresh_item(u, res[0]["id"])  # "Perbarui" replaces, never duplicates
    assert again["id"] != res[0]["id"]
    assert (await db.q1("select count(*)::int as n from kb_items where user_id = %s and ext_id = 'doc11'", u))["n"] == 1
    assert "Kaos polos" in (await db.q1("select text from kb_chunks where item_id = %s", again["id"]))["text"]


@with_db
async def test_drive_import_limits_and_types(db):
    u = uid()
    await connect_google(u)
    base = integrations.DRIVE_API
    with respx.mock:
        respx.get(f"{base}/files/big11").respond(json={"id": "big11", "name": "besar.pdf", "mimeType": "application/pdf", "size": str(kb.MAX_FILE_BYTES + 1)})
        media = respx.get(f"{base}/files/big11", params={"alt": "media"}).respond(content=b"%PDF")
        respx.get(f"{base}/files/img11").respond(json={"id": "img11", "name": "foto.png", "mimeType": "image/png"})
        respx.get(f"{base}/files/txt11").respond(json={"id": "txt11", "name": "catatan", "mimeType": "text/plain", "size": "20"})
        respx.get(f"{base}/files/txt11", params={"alt": "media"}).respond(content="Catatan rapat hari ini".encode())
        respx.get(f"{base}/files/hug11").respond(json={"id": "hug11", "name": "Dokumen", "mimeType": "application/vnd.google-apps.document"})
        respx.get(f"{base}/files/hug11/export").respond(content=b"x" * (kb.MAX_PAGE_BYTES + 1))
        res = await integrations.drive_import(u, ["big11", "img11", "txt11", "hug11"])
    assert not media.called  # rejected from the metadata, never downloaded
    by = {r["name"]: r for r in res}
    assert "terlalu besar" in by["big11"]["error"] and "belum didukung" in by["img11"]["error"] and "terlalu besar" in by["hug11"]["error"]
    assert by["catatan"]["status"] == "ready"  # name got the .txt extension for the shared extractor
    assert not await db.q1("select 1 from kb_items where user_id = %s and name in ('besar.pdf', 'foto.png')", u)


@with_db
async def test_import_requires_connection_and_scopes_refresh_to_the_owner(db):
    a, b = uid(), uid()
    with pytest.raises(ApiError) as e:
        await integrations.drive_import(a, ["doc1x"])
    assert e.value.extra["needs"] == "connect"
    with pytest.raises(ApiError):
        await integrations.drive_import(a, [])
    with pytest.raises(ApiError):
        await integrations.drive_import(a, ["../etc"])
    await connect_google(a)
    with respx.mock:
        respx.get(f"{integrations.DRIVE_API}/files/doc1x").respond(json={"id": "doc1x", "name": "A", "mimeType": "application/vnd.google-apps.document"})
        respx.get(f"{integrations.DRIVE_API}/files/doc1x/export").respond(text="isi dokumen A")
        item = (await integrations.drive_import(a, ["doc1x"]))[0]
    with pytest.raises(ApiError) as e:
        await integrations.refresh_item(b, item["id"])
    assert e.value.status == 404
    plain = await kb.ingest_file(a, "x.txt", b"hello world")
    with pytest.raises(ApiError):  # only imported items can be refreshed
        await integrations.refresh_item(a, plain["id"])


@with_db
async def test_private_drive_link_in_chat_uses_the_connection(db):
    u = uid()
    url = "https://docs.google.com/document/d/priv123/edit"
    await connect_google(u)
    with respx.mock:
        respx.get(f"{integrations.DRIVE_API}/files/priv123").respond(json={"id": "priv123", "name": "Rahasia", "mimeType": "application/vnd.google-apps.document"})
        respx.get(f"{integrations.DRIVE_API}/files/priv123/export").respond(text="isi pribadi")
        item = await kb.ingest_url(u, url)
    assert item["status"] == "ready" and item["name"] == "Rahasia" and item["kind"] == "gdrive"


def test_drive_needs_connect_message_is_kept():
    assert "tanpa login" in kb.DRIVE_NEEDS_CONNECT and "Google Drive" in kb.DRIVE_NEEDS_CONNECT


# ---------- Notion ----------

def rt(text):
    return [{"plain_text": text}]


def test_block_to_text():
    L = integrations.block_line
    assert L({"type": "heading_2", "heading_2": {"rich_text": rt("Harga")}}) == "## Harga"
    assert L({"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Halo "}, {"plain_text": "dunia"}]}}) == "Halo dunia"
    assert L({"type": "to_do", "to_do": {"rich_text": rt("Kirim"), "checked": True}}) == "- [x] Kirim"
    assert L({"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rt("a")}}) == "- a"
    assert L({"type": "code", "code": {"rich_text": rt("x=1"), "language": "python"}}) == "```python\nx=1\n```"
    assert L({"type": "table_row", "table_row": {"cells": [rt("A"), rt("B")]}}) == "A | B"
    assert L({"type": "divider", "divider": {}}) == "---"
    assert L({"type": "unsupported", "unsupported": {}}) is None


@with_db
async def test_notion_search_and_import_with_pagination_and_nesting(db):
    u = uid()
    state = await consent(u, "notion")
    with respx.mock:
        respx.post(connections.NOTION_TOKEN).respond(json={"access_token": "secret_n", "workspace_name": "Toko"})
        await connections.callback(u, "notion", {"code": "c", "state": state})
        s = respx.post(f"{integrations.NOTION_API}/search").respond(json={"has_more": False, "results": [
            {"object": "page", "id": "page-1111", "last_edited_time": "2026-11-12T00:00:00Z",
             "properties": {"Name": {"type": "title", "title": rt("Panduan Toko")}}},
            {"object": "database", "id": "db-2222"}]})
        found = await integrations.notion_pages(u, "panduan")
        body = json.loads(s.calls[0].request.content)
        assert body["query"] == "panduan" and body["filter"] == {"property": "object", "value": "page"}
        assert s.calls[0].request.headers["notion-version"] and s.calls[0].request.headers["authorization"] == "Bearer secret_n"
        assert [p["name"] for p in found["pages"]] == ["Panduan Toko"] and found["next"] is None

        respx.get(f"{integrations.NOTION_API}/pages/page-1111").respond(json={"id": "page-1111", "url": "https://notion.so/p", "properties": {
            "title": {"type": "title", "title": rt("Panduan Toko")}}})
        kids = respx.get(f"{integrations.NOTION_API}/blocks/page-1111/children")
        kids.side_effect = [
            httpx.Response(200, json={"has_more": True, "next_cursor": "cur2", "results": [
                {"id": "b1", "type": "heading_1", "heading_1": {"rich_text": rt("Jam buka")}},
                {"id": "b2", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rt("Senin")}, "has_children": True}]}),
            httpx.Response(200, json={"has_more": False, "results": [
                {"id": "b3", "type": "paragraph", "paragraph": {"rich_text": rt("Tutup hari Minggu")}}]})]
        respx.get(f"{integrations.NOTION_API}/blocks/b2/children").respond(json={"has_more": False, "results": [
            {"id": "b4", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rt("09.00 sampai 17.00")}}]})
        items = await integrations.notion_import(u, ["page-1111"])
    assert qs(str(kids.calls[1].request.url))["start_cursor"] == "cur2"
    assert items[0]["status"] == "ready" and items[0]["kind"] == "notion" and items[0]["name"] == "Panduan Toko" and items[0]["refreshable"]
    text = (await db.q1("select string_agg(text, E'\\n' order by pos) as t from kb_chunks where item_id = %s", items[0]["id"]))["t"]
    assert "# Jam buka" in text and "- Senin" in text and "  - 09.00 sampai 17.00" in text and "Tutup hari Minggu" in text


@with_db
async def test_notion_depth_and_request_caps(db):
    u = uid()
    state = await consent(u, "notion")
    integrations.NOTION_MAX_REQUESTS = 3
    with respx.mock:
        respx.post(connections.NOTION_TOKEN).respond(json={"access_token": "secret_n", "workspace_name": "Toko"})
        await connections.callback(u, "notion", {"code": "c", "state": state})
        respx.get(f"{integrations.NOTION_API}/pages/pp-1111").respond(json={"id": "pp-1111", "properties": {}})
        kids = respx.get(url__regex=rf"{integrations.NOTION_API}/blocks/.*/children").respond(json={"has_more": True, "next_cursor": "x", "results": [
            {"id": "bb-1111", "type": "paragraph", "paragraph": {"rich_text": rt("baris")}}]})
        name, _, text = await integrations.notion_read(u, "pp-1111")
    integrations.NOTION_MAX_REQUESTS = 60
    assert kids.call_count == 3 and "dipotong" in text and name == "Tanpa judul"


# ---------- Gmail ----------

def test_draft_message_shape():
    raw = integrations.build_draft("budi@example.com, siti@example.com", "Penawaran\r\nBcc: x@evil.com", "Halo Budi,\nIni draf. Terima kasih é")
    assert "=" not in raw and "+" not in raw and "/" not in raw  # base64url, no standard-alphabet characters
    msg = email.message_from_bytes(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)))
    assert msg["To"] == "budi@example.com, siti@example.com" and msg["Subject"] == "Penawaran Bcc: x@evil.com" and msg["Bcc"] is None
    assert msg.get_content_charset() == "utf-8" and "Terima kasih é" in msg.get_payload(decode=True).decode()
    assert "To" not in email.message_from_bytes(base64.urlsafe_b64decode(integrations.build_draft("", "S", "isi") + "==="))


@pytest.mark.parametrize("to", ["bukan-email", "a@b", "a@b.com c", "x@y.com;;;z"])
def test_draft_rejects_bad_recipients(to):
    with pytest.raises(ApiError):
        integrations.build_draft(to, "s", "b")


@with_db
async def test_gmail_draft_request(db):
    u = uid()
    await connect_google(u, "gmail", GMAIL_SCOPE)
    with respx.mock:
        r = respx.post(f"{integrations.GMAIL_API}/users/me/drafts").respond(json={"id": "r-123", "message": {"id": "m1"}})
        out = await integrations.gmail_draft(u, "budi@example.com", "Halo", "Isi pesan")
    req = r.calls[0].request
    assert req.headers["authorization"] == "Bearer at-1"
    raw = json.loads(req.content)["message"]["raw"]
    assert email.message_from_bytes(base64.urlsafe_b64decode(raw))["Subject"] == "Halo"
    assert out["draft_id"] == "r-123" and out["url"].endswith("#drafts") and "owner%40example.com" in out["url"]
    with respx.mock:  # nothing but the drafts endpoint is ever called: no send
        send = respx.post(url__regex=r".*/(messages/send|drafts/.*/send)").respond(200)
        respx.post(f"{integrations.GMAIL_API}/users/me/drafts").respond(json={"id": "r-124"})
        await integrations.gmail_draft(u, "", "", "isi")
    assert not send.called
    with pytest.raises(ApiError) as e:  # a Drive-only user has no Gmail connection
        await integrations.gmail_draft(uid(), "a@b.com", "s", "b")
    assert e.value.extra["needs"] == "connect"
