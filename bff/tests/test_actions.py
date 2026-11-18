"""Drive write tools and the approval mechanism (actions.py). Google is mocked with respx; the token and scope come from stubs.
The tests marked with_db need TEST_DATABASE_URL (see test_scheduler.py)."""
import asyncio
import contextlib
import json
import uuid
from unittest import mock

import pytest
import respx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from test_bridge import KEY, URL, app, call_tool, client_for, run_with_manager  # noqa: F401  (app is a fixture)
from test_scheduler import with_db

from bff import actions, bridge, connections, integrations
from bff.errors import ApiError

FILES = f"{integrations.DRIVE_API}/files"
UPLOAD = f"{integrations.DRIVE_UPLOAD}/files"
READONLY = "https://www.googleapis.com/auth/drive.readonly"


@contextlib.contextmanager
def granted(scope):
    """Stub the Drive token and the saved consent scope."""
    async def token(user_id, provider):
        return "at-secret"

    async def has_scope(user_id, provider, wanted):
        return wanted == scope
    with mock.patch.object(connections, "access_token", token), mock.patch.object(connections, "has_scope", has_scope):
        yield


@pytest.fixture
def writer():
    with granted(integrations.DRIVE_WRITE_SCOPE):
        yield


@pytest.fixture
def old_scope():
    """A connection made before the change: drive.readonly only."""
    with granted(READONLY):
        yield


def writes(fn):
    """with_db tests cannot take fixtures: run the body with a full-scope Drive connection."""
    async def body(db):
        with granted(integrations.DRIVE_WRITE_SCOPE):
            await fn(db)
    body.__name__ = fn.__name__
    return body


# ---------- Drive write tools (no database needed) ----------

def test_create_doc_uploads_multipart_as_google_doc(app, writer):
    with respx.mock:
        r = respx.post(UPLOAD).respond(json={"id": "new12345", "name": "Catatan", "webViewLink": "https://docs.google.com/document/d/new12345"})
        out = call_tool(app, "drive_create", {"name": "Catatan", "content": "Halo dunia", "folder_id": "fold12345"})
    req = r.calls[0].request
    assert req.url.params["uploadType"] == "multipart" and req.headers["content-type"].startswith("multipart/related; boundary=")
    body = req.content.decode()
    assert '"mimeType": "application/vnd.google-apps.document"' in body and '"parents": ["fold12345"]' in body and "Halo dunia" in body
    assert out == "Dibuat: Catatan | id: new12345 | link: https://docs.google.com/document/d/new12345"


def test_create_text_file_and_validation(app, writer):
    with respx.mock:
        r = respx.post(UPLOAD).respond(json={"id": "txt12345", "name": "a.txt"})
        call_tool(app, "drive_create", {"name": "a.txt", "content": "x", "kind": "text"})
        assert '"mimeType": "text/plain"' in r.calls[0].request.content.decode()
        before = r.call_count
        assert "kind harus" in call_tool(app, "drive_create", {"name": "a", "content": "x", "kind": "pdf"})
        assert "1 sampai 200" in call_tool(app, "drive_create", {"name": "  ", "content": "x"})
        assert "maksimal 1 MB" in call_tool(app, "drive_create", {"name": "a", "content": "x" * 1_000_001})
        assert "Id folder tidak valid" in call_tool(app, "drive_create", {"name": "a", "content": "x", "folder_id": "../x"})
        assert r.call_count == before


def test_update_replaces_doc_text_and_refuses_pdf(app, writer):
    with respx.mock:
        respx.get(f"{FILES}/doc12345").respond(json={"id": "doc12345", "name": "Doc", "mimeType": "application/vnd.google-apps.document"})
        respx.get(f"{FILES}/pdf12345").respond(json={"id": "pdf12345", "name": "Laporan.pdf", "mimeType": "application/pdf"})
        patch = respx.patch(f"{UPLOAD}/doc12345").respond(json={"id": "doc12345", "name": "Doc"})
        out = call_tool(app, "drive_update", {"file_id": "doc12345", "content": "Baru"})
        pdf = call_tool(app, "drive_update", {"file_id": "pdf12345", "content": "Baru"})
    assert patch.calls[0].request.url.params["uploadType"] == "media" and patch.calls[0].request.content == b"Baru"
    assert out.startswith("Isi diganti: Doc | id: doc12345")
    assert "tidak bisa diganti" in pdf and patch.call_count == 1


def test_rename_and_move(app, writer):
    with respx.mock:
        ren = respx.patch(f"{FILES}/doc12345").respond(json={"id": "doc12345", "name": "Baru"})
        respx.get(f"{FILES}/doc12345").respond(json={"id": "doc12345", "name": "Baru", "parents": ["old11111", "old22222"]})
        assert call_tool(app, "drive_rename", {"file_id": "doc12345", "new_name": "Baru"}).startswith("Nama diganti: Baru")
        assert json.loads(ren.calls[0].request.content) == {"name": "Baru"}
        assert call_tool(app, "drive_move", {"file_id": "doc12345", "folder_id": "fold12345"}).startswith("Dipindahkan: Baru")
    q = ren.calls[1].request.url.params
    assert q["addParents"] == "fold12345" and q["removeParents"] == "old11111,old22222"


def test_write_tools_ask_to_reconnect_with_old_scope_and_read_still_works(app, old_scope):
    msg = f"Error: {integrations.DRIVE_NEED_WRITE}"
    with respx.mock:
        any_google = respx.route(url__startswith="https://www.googleapis.com")
        for name, args in [("drive_create", {"name": "a", "content": "b"}), ("drive_update", {"file_id": "doc12345", "content": "b"}),
                           ("drive_rename", {"file_id": "doc12345", "new_name": "b"}), ("drive_move", {"file_id": "doc12345", "folder_id": "fold12345"}),
                           ("drive_trash", {"file_id": "doc12345"})]:
            assert call_tool(app, name, args) == msg
        assert any_google.call_count == 0
    with respx.mock:
        respx.get(FILES).respond(json={"files": []})
        assert "No matching files" in call_tool(app, "drive_search", {"query": "x"})


def test_tool_list_has_write_tools_and_hides_the_context_argument(app):
    async def call():
        http = client_for(app, headers={"Authorization": f"Bearer {KEY}"})
        async with streamable_http_client(URL, http_client=http) as (r, w, _):
            async with ClientSession(r, w) as s:
                await s.initialize()
                return {t.name: t for t in (await s.list_tools()).tools}
    tools = run_with_manager(app, call)
    assert {"drive_create", "drive_update", "drive_rename", "drive_move", "drive_trash", "action_status"} <= set(tools)
    assert set(tools["drive_trash"].inputSchema["properties"]) == {"file_id", "file_name"}  # the request context is injected, not asked of the agent


# ---------- approval mechanism (real SQL) ----------

def uid():
    return f"u-{uuid.uuid4().hex[:8]}"


REAL_META = {"id": "doc12345", "name": "Laporan Q3.pdf", "trashed": False, "owners": [{"displayName": "Budi", "emailAddress": "budi@x.com"}], "parents": ["fold12345"]}


async def trash_request(user, file_id="doc12345", name="Laporan Q3.pdf", meta=REAL_META):
    """The agent's request. Drive answers the read-only metadata call with `meta` (None = Drive cannot answer)."""
    old, bridge._user = bridge._user, lambda: user
    try:
        with respx.mock(assert_all_called=False) as router:
            if meta is None:
                router.get(f"{FILES}/{file_id}").respond(500)
            else:
                router.get(f"{FILES}/{file_id}").respond(json=meta)
            router.get(f"{FILES}/fold12345").respond(json={"id": "fold12345", "name": "Laporan 2026"})
            out = await bridge.drive_trash(file_id, name)
            assert all(c.request.method == "GET" for c in router.calls)  # asking only reads
            return out
    finally:
        bridge._user = old


@with_db
@writes
async def test_trash_card_shows_the_real_name_owner_and_folder_not_the_agents(db):
    user = uid()
    await trash_request(user, name="Berkas Biasa.txt")  # the agent says one thing, Drive says another
    [a] = await actions.list_actions(user, "pending")
    assert a["summary"] == "Pindahkan 'Laporan Q3.pdf' ke Sampah Drive"
    assert a["payload"]["file_name"] == "Laporan Q3.pdf" and "name_from_agent" not in a["payload"]
    assert a["payload"]["preview"] == "Pemilik: Budi\nFolder: Laporan 2026"


@with_db
@writes
async def test_trash_card_marks_the_agents_name_when_drive_cannot_answer(db):
    user = uid()
    await trash_request(user, name="Dari Agen.txt", meta=None)
    [a] = await actions.list_actions(user, "pending")
    assert a["summary"] == "Pindahkan 'Dari Agen.txt' (nama dari agen) ke Sampah Drive" and a["payload"]["name_from_agent"] is True
    assert a["payload"]["file_id"] == "doc12345"


@with_db
@writes
async def test_trash_already_in_trash_creates_no_card(db):
    user = uid()
    out = await trash_request(user, meta={**REAL_META, "trashed": True})
    assert "sudah ada di Sampah" in out and await actions.list_actions(user, "pending") == []


@with_db
@writes
async def test_trash_tool_only_creates_a_pending_row(db):
    user = uid()
    out = await trash_request(user)  # trash_request asserts that asking only made read-only (GET) calls
    again = await trash_request(user)  # an agent that asks twice does not stack cards
    rows = await db.q("select * from pending_actions where user_id = %s", user)
    assert len(rows) == 1 and rows[0]["status"] == "pending" and rows[0]["kind"] == "drive_trash"
    assert rows[0]["summary"] == "Pindahkan 'Laporan Q3.pdf' ke Sampah Drive" and rows[0]["payload"]["file_id"] == "doc12345"
    short = actions.short(rows[0]["id"])
    assert out == again == f"Menunggu persetujuan pengguna (#{short}). Jangan ulangi permintaan ini; pengguna akan menyetujui atau menolak di aplikasi."
    assert (await actions.status_text(user, short)).endswith("Menunggu persetujuan pengguna.")


@with_db
@writes
async def test_approve_trashes_once_and_second_approve_is_409(db):
    user = uid()
    await trash_request(user)
    [a] = await actions.list_actions(user, "pending")
    with respx.mock:
        patch = respx.patch(f"{FILES}/doc12345").respond(json={"id": "doc12345", "name": "Laporan Q3.pdf"})
        done = await actions.approve(user, a["id"])
        with pytest.raises(ApiError) as e:
            await actions.approve(user, a["id"])
        with pytest.raises(ApiError) as e2:
            await actions.reject(user, a["id"])
        assert not [c for c in respx.calls if c.request.method == "DELETE"]
    assert e.value.status == 409 and e2.value.status == 409 and patch.call_count == 1
    assert json.loads(patch.calls[0].request.content) == {"trashed": True}  # trash, never a permanent delete
    assert done["status"] == "done" and "Sampah Drive" in done["result"] and done["decided_at"]
    assert "Disetujui dan sudah dijalankan" in await actions.status_text(user, a["short_id"])


@with_db
@writes
async def test_concurrent_approves_run_the_action_once(db):
    user = uid()
    await trash_request(user)
    [a] = await actions.list_actions(user, "pending")
    with respx.mock:
        patch = respx.patch(f"{FILES}/doc12345").respond(json={"id": "doc12345", "name": "x"})
        got = await asyncio.gather(*[actions.approve(user, a["id"]) for _ in range(4)], return_exceptions=True)
    assert patch.call_count == 1 and sum(isinstance(g, dict) for g in got) == 1 and all(isinstance(g, ApiError) for g in got if not isinstance(g, dict))


@with_db
@writes
async def test_reject_does_not_call_google(db):
    user = uid()
    await trash_request(user)
    [a] = await actions.list_actions(user, "pending")
    with respx.mock:
        google = respx.route(url__startswith="https://www.googleapis.com")
        r = await actions.reject(user, a["id"])
        assert google.call_count == 0
    assert r["status"] == "rejected" and "Ditolak" in r["result"]
    assert await actions.list_actions(user, "pending") == []
    assert "Ditolak oleh pengguna" in await actions.status_text(user, a["short_id"])


@with_db
@writes
async def test_expired_cannot_be_approved(db):
    user = uid()
    await trash_request(user)
    await db.ex("update pending_actions set created_at = now() - interval '25 hours' where user_id = %s", user)
    [old] = await db.q("select id from pending_actions where user_id = %s", user)
    with respx.mock:
        google = respx.route(url__startswith="https://www.googleapis.com")
        with pytest.raises(ApiError) as e:
            await actions.approve(user, str(old["id"]))
        assert google.call_count == 0
    assert e.value.status == 409 and "kedaluwarsa" in e.value.message
    assert (await db.q1("select status from pending_actions where id = %s", old["id"]))["status"] == "expired"


@with_db
@writes
async def test_approve_with_old_scope_fails_with_reconnect_message(db):
    user = uid()
    await trash_request(user)
    [a] = await actions.list_actions(user, "pending")
    with granted(READONLY), respx.mock:  # the connection is read-only by the time the user approves
        google = respx.route(url__startswith="https://www.googleapis.com")
        r = await actions.approve(user, a["id"])
        assert google.call_count == 0
    assert r["status"] == "failed" and r["result"] == integrations.DRIVE_NEED_WRITE


@with_db
@writes
async def test_actions_are_scoped_to_their_user_and_unknown_ids_are_404(db):
    user, other = uid(), uid()
    await trash_request(user)
    [a] = await actions.list_actions(user, "pending")
    assert await actions.list_actions(other) == []
    for fn in (actions.approve, actions.reject):
        with pytest.raises(ApiError) as e:
            await fn(other, a["id"])
        assert e.value.status == 404
    with pytest.raises(ApiError):
        await actions.approve(user, "not-an-id")
    assert (await actions.status_text(other, a["short_id"])).startswith("Error")
    assert (await actions.status_text(user, "zz")).startswith("Error")


@with_db
async def test_new_kinds_plug_in_and_source_is_kept(db):
    user = uid()
    ran = []

    async def fake_send(user_id, payload):
        ran.append(payload)
        return "Terkirim."
    actions.register("fake_send", fake_send)
    try:
        src = {"bot_id": "mira", "session_id": "s1", "group_id": None}
        a = await actions.create(user, "fake_send", "Kirim email ke a@b.com", {"to": "a@b.com"}, src)
        assert a["source"] == src
        assert (await actions.approve(user, a["id"]))["result"] == "Terkirim." and ran == [{"to": "a@b.com"}]
        with pytest.raises(ApiError):
            await actions.create(user, "unknown_kind", "x", {})
    finally:
        actions.EXECUTORS.pop("fake_send")


# ---------- Gmail tools (tahap B) ----------

GM = integrations.GMAIL_API
ALL_GMAIL = {integrations.GMAIL_READ_SCOPE, integrations.GMAIL_MODIFY_SCOPE, integrations.GMAIL_SEND_SCOPE}


@contextlib.contextmanager
def gmail_scopes(*scopes):
    """Stub the Gmail token and the saved consent: only `scopes` are granted."""
    async def token(user_id, provider):
        return "at-secret"

    async def has_scope(user_id, provider, wanted):
        return wanted in scopes
    with mock.patch.object(connections, "access_token", token), mock.patch.object(connections, "has_scope", has_scope):
        yield


def gmail_writes(fn):
    async def body(db):
        with gmail_scopes(*ALL_GMAIL):
            await fn(db)
    body.__name__ = fn.__name__
    return body


async def as_user(user, tool, *args):
    old, bridge._user = bridge._user, lambda: user
    try:
        return await tool(*args)
    finally:
        bridge._user = old


def b64_decode(raw):
    import base64
    return base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)).decode()


def test_gmail_label_and_trash_call_the_right_endpoints(app):
    with gmail_scopes(*ALL_GMAIL), respx.mock:
        mod = respx.post(f"{GM}/users/me/messages/msg12345/modify").respond(json={"id": "msg12345"})
        trash = respx.post(f"{GM}/users/me/messages/msg12345/trash").respond(json={"id": "msg12345"})
        assert call_tool(app, "gmail_label", {"message_id": "msg12345", "add": ["STARRED"], "remove": ["UNREAD", "INBOX"]}) == "Label email diperbarui."
        assert call_tool(app, "gmail_trash", {"message_id": "msg12345"}) == "Email dipindahkan ke Sampah Gmail."
        assert [c.request.method for c in respx.calls] == ["POST", "POST"]  # trash, never a permanent delete
        for bad in ({"message_id": "../x", "add": ["STARRED"]}, {"message_id": "msg12345"}, {"message_id": "msg12345", "add": ["a b"]}):
            assert call_tool(app, "gmail_label", bad).startswith("Error:")
    assert json.loads(mod.calls[0].request.content) == {"addLabelIds": ["STARRED"], "removeLabelIds": ["UNREAD", "INBOX"]} and trash.call_count == 1


def test_gmail_write_tools_ask_to_reconnect_without_the_new_scope(app):
    with gmail_scopes(integrations.GMAIL_READ_SCOPE), respx.mock:  # a connection made before: no modify or send
        google = respx.route(url__startswith="https://gmail.googleapis.com")
        assert call_tool(app, "gmail_label", {"message_id": "msg12345", "add": ["STARRED"]}) == f"Error: {integrations.GMAIL_NEED_MODIFY}"
        assert call_tool(app, "gmail_trash", {"message_id": "msg12345"}) == f"Error: {integrations.GMAIL_NEED_MODIFY}"
        assert call_tool(app, "gmail_send", {"to": "a@b.com", "subject": "s", "body": "b"}) == f"Error: {integrations.GMAIL_NEED_SEND}"
        assert call_tool(app, "gmail_send_draft", {"draft_id": "dr12345"}) == f"Error: {integrations.GMAIL_NEED_SEND}"
        assert google.call_count == 0


def test_gmail_send_validates_recipients_subject_and_body(app):
    with gmail_scopes(*ALL_GMAIL), respx.mock:
        google = respx.route(url__startswith="https://gmail.googleapis.com")
        many = ",".join(f"u{i}@example.com" for i in range(11))
        assert "maksimal 10" in call_tool(app, "gmail_send", {"to": many, "subject": "s", "body": "b"})
        assert "tidak valid" in call_tool(app, "gmail_send", {"to": "bukan-email", "subject": "s", "body": "b"})
        assert "Isi alamat" in call_tool(app, "gmail_send", {"to": " ", "subject": "s", "body": "b"})
        assert "Subjek harus" in call_tool(app, "gmail_send", {"to": "a@b.com", "subject": " ", "body": "b"})
        assert "Isi email harus" in call_tool(app, "gmail_send", {"to": "a@b.com", "subject": "s", "body": " "})
        assert google.call_count == 0


@with_db
@gmail_writes
async def test_gmail_send_only_creates_pending_with_the_exact_payload_then_approve_sends_once(db):
    user = uid()
    body = "Halo Ani,\n\nRapat jadi jam 3.\n\nSalam"
    with respx.mock:
        google = respx.route(url__startswith="https://gmail.googleapis.com")
        out = await as_user(user, bridge.gmail_send, "ani@example.com, budi@example.com", "Rapat jam 3", body)
        again = await as_user(user, bridge.gmail_send, "ani@example.com, budi@example.com", "Rapat jam 3", body)
        assert google.call_count == 0  # asking sends nothing and does not even read Gmail
    [a] = await actions.list_actions(user, "pending")
    assert out == again == actions.WAITING.format(id=a["short_id"])
    assert a["kind"] == "gmail_send" and a["summary"] == "Kirim email ke ani@example.com, budi@example.com — Subjek: Rapat jam 3"
    assert a["payload"] == {"to": ["ani@example.com", "budi@example.com"], "subject": "Rapat jam 3", "body": body}  # what the card shows
    with respx.mock:
        send = respx.post(f"{GM}/users/me/messages/send").respond(json={"id": "sent1", "threadId": "t1"})
        done = await actions.approve(user, a["id"])
        with pytest.raises(ApiError) as e:
            await actions.approve(user, a["id"])
    assert e.value.status == 409 and send.call_count == 1 and done["status"] == "done" and "ani@example.com" in done["result"]
    sent = json.loads(send.calls[0].request.content)
    assert set(sent) == {"raw"}
    mime = b64_decode(sent["raw"])
    assert "To: ani@example.com, budi@example.com" in mime and "Subject: Rapat jam 3" in mime and "In-Reply-To" not in mime
    assert "Halo Ani," in mime and "Rapat jadi jam 3." in mime and "Salam" in mime


@with_db
@gmail_writes
async def test_gmail_reply_sends_thread_id_and_reply_headers(db):
    user = uid()
    with respx.mock:
        respx.get(f"{GM}/users/me/messages/msg12345").respond(json={"id": "msg12345", "threadId": "thr777", "payload": {"headers": [
            {"name": "Message-ID", "value": "<orig@mail.example>"}, {"name": "References", "value": "<first@mail.example>"},
            {"name": "Subject", "value": "Pertanyaan"}, {"name": "From", "value": "Ani <ani@example.com>"}]}})
        await as_user(user, bridge.gmail_send, "ani@example.com", "Re: Pertanyaan", "Jawabannya ya.", "msg12345")
    [a] = await actions.list_actions(user, "pending")
    assert a["payload"]["thread_id"] == "thr777" and a["payload"]["reply_to"] == {"from": "Ani <ani@example.com>", "subject": "Pertanyaan"}
    with respx.mock:
        send = respx.post(f"{GM}/users/me/messages/send").respond(json={"id": "sent1"})
        await actions.approve(user, a["id"])
    sent = json.loads(send.calls[0].request.content)
    mime = b64_decode(sent["raw"])
    assert sent["threadId"] == "thr777" and "In-Reply-To: <orig@mail.example>" in mime and "References: <first@mail.example> <orig@mail.example>" in mime


@with_db
@gmail_writes
async def test_gmail_send_reject_sends_nothing(db):
    user = uid()
    await as_user(user, bridge.gmail_send, "ani@example.com", "Hai", "Isi")
    [a] = await actions.list_actions(user, "pending")
    with respx.mock:
        google = respx.route(url__startswith="https://gmail.googleapis.com")
        r = await actions.reject(user, a["id"])
        assert google.call_count == 0
    assert r["status"] == "rejected"


@with_db
@gmail_writes
async def test_gmail_approve_without_send_scope_fails_with_reconnect_message(db):
    user = uid()
    await as_user(user, bridge.gmail_send, "ani@example.com", "Hai", "Isi")
    [a] = await actions.list_actions(user, "pending")
    with gmail_scopes(integrations.GMAIL_READ_SCOPE), respx.mock:
        google = respx.route(url__startswith="https://gmail.googleapis.com")
        r = await actions.approve(user, a["id"])
        assert google.call_count == 0
    assert r["status"] == "failed" and r["result"] == integrations.GMAIL_NEED_SEND


def draft_json(mid="m1", to="ani@example.com", subject="Halo", text="Isi draf"):
    import base64
    data = base64.urlsafe_b64encode(text.encode()).decode()
    return {"id": "dr12345", "message": {"id": mid, "payload": {"mimeType": "text/plain", "body": {"data": data},
                                                                  "headers": [{"name": "To", "value": to}, {"name": "Subject", "value": subject}]}}}


@with_db
@gmail_writes
async def test_send_draft_card_holds_the_real_draft_and_approve_sends_it_once(db):
    user = uid()
    with respx.mock:
        respx.get(f"{GM}/users/me/drafts/dr12345").respond(json=draft_json(text="Isi asli draf"))
        send = respx.post(f"{GM}/users/me/drafts/send")
        out = await as_user(user, bridge.gmail_send_draft, "dr12345")
        assert send.call_count == 0
    [a] = await actions.list_actions(user, "pending")
    assert out == actions.WAITING.format(id=a["short_id"])
    assert a["summary"] == "Kirim draf ke ani@example.com — Subjek: Halo" and a["payload"]["body"] == "Isi asli draf" and a["payload"]["to"] == "ani@example.com"
    with respx.mock:
        respx.get(f"{GM}/users/me/drafts/dr12345").respond(json=draft_json())
        send = respx.post(f"{GM}/users/me/drafts/send").respond(json={"id": "sent1"})
        done = await actions.approve(user, a["id"])
    assert done["status"] == "done" and send.call_count == 1 and json.loads(send.calls[0].request.content) == {"id": "dr12345"}


@with_db
@gmail_writes
async def test_send_draft_refuses_when_the_draft_changed_after_the_request(db):
    user = uid()
    with respx.mock:
        respx.get(f"{GM}/users/me/drafts/dr12345").respond(json=draft_json(mid="m1"))
        await as_user(user, bridge.gmail_send_draft, "dr12345")
    [a] = await actions.list_actions(user, "pending")
    with respx.mock:
        respx.get(f"{GM}/users/me/drafts/dr12345").respond(json=draft_json(mid="m2", text="Diubah"))
        send = respx.post(f"{GM}/users/me/drafts/send").respond(json={})
        r = await actions.approve(user, a["id"])
    assert r["status"] == "failed" and "berubah" in r["result"] and send.call_count == 0
