"""What the connections do: Google Drive files become Knowledge Base items and agent tools (read, write, trash after approval), Gmail gets drafts, labels, trash and sending after approval.
Provider calls go through _request: it adds the user's token and turns provider failures into plain Indonesian errors."""
import asyncio
import base64
import html
import json as jsonlib
import logging
import re
import secrets
import time
from email.message import EmailMessage
from urllib.parse import quote

import httpx

from . import connections, db, kb
from .errors import ApiError

log = logging.getLogger("bff.integrations")

DRIVE_API = "https://www.googleapis.com/drive/v3"
GMAIL_API = "https://gmail.googleapis.com/gmail/v1"

# Google-native files are exported; uploaded files are downloaded and read like uploads (same types as the KB file picker).
GOOGLE_EXPORT = {
    "application/vnd.google-apps.document": ("text/plain", "Google Docs"),
    "application/vnd.google-apps.spreadsheet": ("text/csv", "Google Sheets"),  # Drive exports the first sheet only
    "application/vnd.google-apps.presentation": ("text/plain", "Google Slides"),
}
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
UPLOADED = {"application/pdf": (".pdf", "PDF"), DOCX: (".docx", "Word"), "text/plain": (".txt", "Teks"),
            "text/markdown": (".md", "Markdown"), "text/x-markdown": (".md", "Markdown"), "text/csv": (".csv", "CSV")}
DRIVE_PAGE = 25
MAX_IMPORT_IDS = 10
ID_RE = re.compile(r"[\w-]{5,200}")

# ---------- shared request ----------


def _reasons(body: bytes) -> set[str]:
    """Machine reasons inside a Google error body (e.g. accessNotConfigured, SERVICE_DISABLED). Never the message or any data."""
    try:
        d = jsonlib.loads(body)
    except ValueError:
        return set()
    e = d.get("error") if isinstance(d, dict) else None
    out = {str(d.get("code"))} if isinstance(d, dict) and d.get("code") else set()
    if isinstance(e, dict):
        out |= {str(x.get("reason")) for x in [*(e.get("errors") or []), *(e.get("details") or [])] if isinstance(x, dict) and x.get("reason")}
        if e.get("status"):
            out.add(str(e["status"]))
    return out


def _denied(provider: str, name: str, body: bytes) -> ApiError:
    """403 from the provider -> a plain message and what the user can do. The provider's own body is only logged (reasons, no data)."""
    reasons = _reasons(body)
    log.warning("%s answered 403: %s", provider, ", ".join(sorted(reasons)) or "no reason given")
    if reasons & {"accessNotConfigured", "SERVICE_DISABLED"}:
        return ApiError(503, f"Layanan {name} belum diaktifkan oleh admin. Hubungi admin Anda.", needs="admin")
    if reasons & {"insufficientPermissions", "ACCESS_TOKEN_SCOPE_INSUFFICIENT"}:
        return ApiError(403, f"Izin {name} kurang. Sambungkan ulang dan centang semua izin.", needs="reconnect")
    return ApiError(403, f"{name} menolak permintaan ini. Periksa izin akun Anda atau hubungkan ulang.")


async def _request(user_id: str, provider: str, method: str, url: str, *, params=None, json=None, content=None, headers=None, cap: int = kb.MAX_PAGE_BYTES,
                   client: httpx.AsyncClient | None = None) -> httpx.Response:
    """Call the provider as the user. The body is read up to `cap` bytes (r.content)."""
    name = connections.NAMES[provider]
    token = await connections.access_token(user_id, provider)
    own = client is None
    client = client or httpx.AsyncClient(timeout=30.0)
    try:
        async with client.stream(method, url, params=params, json=json, content=content, headers={"Authorization": f"Bearer {token}", **(headers or {})}) as r:
            body = bytearray()
            async for part in r.aiter_bytes():
                body += part
                if len(body) > cap:
                    raise ApiError(413, "Berkas ini terlalu besar untuk dibaca (maksimal 5 MB).")
            status = r.status_code
    except httpx.TimeoutException:
        raise ApiError(504, f"{name} terlalu lama menjawab. Coba lagi.")
    except httpx.HTTPError:
        raise ApiError(502, f"{name} belum bisa dihubungi. Coba lagi sebentar.")
    finally:
        if own:
            await client.aclose()
    if status == 401:
        await connections.mark_reconnect(user_id, provider)
        raise ApiError(409, connections.RECONNECT_MSG.format(name=name), needs="reconnect")
    if status == 403:
        raise _denied(provider, name, bytes(body))
    if status == 404:
        raise ApiError(404, f"Item tidak ditemukan di {name}. Mungkin sudah dihapus atau belum dibagikan ke aplikasi ini.")
    if status == 429:
        raise ApiError(429, f"{name} sedang membatasi permintaan. Coba lagi sebentar.")
    if status >= 400:
        raise ApiError(502, f"{name} menjawab dengan kesalahan {status}.")
    return httpx.Response(status, content=bytes(body))


def _ids(raw) -> list[str]:
    if not isinstance(raw, list) or not raw or len(raw) > MAX_IMPORT_IDS or not all(isinstance(i, str) and ID_RE.fullmatch(i) for i in raw):
        raise ApiError(400, f"Pilih 1 sampai {MAX_IMPORT_IDS} item.")
    return list(dict.fromkeys(raw))


async def _store(user_id: str, kind: str, ext_id: str, name: str, source: str | None, text: str) -> dict:
    """Replace any earlier import of the same source with a fresh item (this is what 'Perbarui' does)."""
    text = kb._clean(text)[:kb.MAX_TEXT_CHARS]
    if not text:
        raise ApiError(422, "Isinya kosong, jadi tidak ada yang bisa disimpan.")
    await db.ex("delete from kb_items where user_id = %s and kind = %s and ext_id = %s", user_id, kind, ext_id)
    item = await kb._new_item(user_id, kind, name, source, len(text.encode()))
    await db.ex("update kb_items set ext_id = %s where id = %s", ext_id, item["id"])
    return await kb._ready(item, text)


async def _import_many(user_id: str, ids: list[str], one) -> list[dict]:
    out = []
    for i in ids:
        try:
            out.append(await one(user_id, i))
        except ApiError as e:
            if e.extra.get("needs"):  # the connection itself is broken: stop and tell the user
                raise
            out.append({"id": None, "name": i, "status": "failed", "error": e.message})
    return out

# ---------- honest connection status ----------

CHECK_TTL = 60.0
_CHECKS = {
    "gdrive": ("GET", f"{DRIVE_API}/files", {"pageSize": 1, "fields": "files(id)"}, None),
    "gmail": ("GET", f"{GMAIL_API}/users/me/profile", None, None),
}
_cache: dict[tuple, tuple[float, dict]] = {}  # shortcut: per process, lost on restart; fine for a 60 s cache


async def check(user_id: str, provider: str) -> dict:
    """One light call to the provider: {"ok": True} or {"ok": False, "reason", "needs"}. needs: reconnect | admin | retry."""
    method, url, params, headers = _CHECKS[provider]
    try:
        await _request(user_id, provider, method, url, params=params, headers=headers, cap=64 * 1024)
    except ApiError as e:
        return {"ok": False, "reason": e.message, "needs": e.extra.get("needs") if e.extra.get("needs") in ("reconnect", "admin") else "retry",
                "revoked": e.status == 409}  # 409: the grant itself is gone (status 'reconnect', already saved by _request)
    return {"ok": True}


async def list_checked(user_id: str, fresh: bool = False) -> list[dict]:
    """connections.list_all, where every 'connected' entry has been checked at the provider (cached ~60 s).
    A failed check turns it into status 'broken' with a friendly `reason`; green means the last check worked."""
    items = await connections.list_all(user_id)

    async def one(c: dict) -> None:
        if c["status"] != "connected":
            return
        key = (user_id, c["provider"], str(c["connected_at"]))  # a new consent changes connected_at, so it is checked again
        hit = _cache.get(key)
        if hit and not fresh and time.monotonic() - hit[0] < CHECK_TTL:
            res = hit[1]
        else:
            res = await check(user_id, c["provider"])
            if res.get("needs") != "retry":  # a timeout is not a verdict: ask again next time
                _cache[key] = (time.monotonic(), res)
        if not res["ok"]:
            c["status"] = "reconnect" if res.get("revoked") else "broken"
            c["reason"], c["needs"] = res["reason"], res["needs"]

    await asyncio.gather(*(one(c) for c in items))
    return items

# ---------- Google Drive ----------


def drive_kind(mime: str) -> str | None:
    """Short type label for a file we can import, None for anything else."""
    if mime in GOOGLE_EXPORT:
        return GOOGLE_EXPORT[mime][1]
    return UPLOADED[mime][1] if mime in UPLOADED else None


def _q_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


async def drive_list(user_id: str, query: str = "", page: str | None = None, *, size: int = DRIVE_PAGE, content: bool = False) -> dict:
    """`content` also matches inside the files (fullText, which includes the name); default is the name only."""
    mimes = " or ".join(f"mimeType = '{m}'" for m in [*GOOGLE_EXPORT, *UPLOADED])
    q = f"trashed = false and ({mimes})" + (f" and {'fullText' if content else 'name'} contains '{_q_escape(query.strip()[:100])}'" if query.strip() else "")
    r = await _request(user_id, "gdrive", "GET", f"{DRIVE_API}/files", params={
        "q": q, "pageSize": size, "orderBy": "modifiedTime desc", **({"pageToken": page} if page else {}),
        "fields": "nextPageToken,files(id,name,mimeType,modifiedTime,size,webViewLink)"})
    d = r.json()
    files = [{"id": f["id"], "name": f.get("name") or "Tanpa nama", "type": drive_kind(f.get("mimeType", "")),
              "modified": f.get("modifiedTime"), "link": f.get("webViewLink"), "size": int(f["size"]) if str(f.get("size", "")).isdigit() else None}
             for f in d.get("files", []) if drive_kind(f.get("mimeType", ""))]
    return {"files": files, "next": d.get("nextPageToken")}


async def drive_read(user_id: str, file_id: str) -> tuple[str, str | None, str]:
    """(name, link, text) of one Drive file. Google files are exported, uploaded files are downloaded; same size and type limits as uploads."""
    if not ID_RE.fullmatch(file_id):
        raise ApiError(400, "Berkas Drive tidak dikenal.")
    meta = (await _request(user_id, "gdrive", "GET", f"{DRIVE_API}/files/{file_id}",
                           params={"fields": "id,name,mimeType,size,webViewLink,trashed"})).json()
    mime, name = meta.get("mimeType", ""), meta.get("name") or "Tanpa nama"
    if meta.get("trashed"):
        raise ApiError(404, "Berkas ini ada di tempat sampah Drive.")
    if mime in GOOGLE_EXPORT:
        r = await _request(user_id, "gdrive", "GET", f"{DRIVE_API}/files/{file_id}/export", params={"mimeType": GOOGLE_EXPORT[mime][0]})
        text = kb._clean(kb._decode(r.content))
    elif mime in UPLOADED:
        ext = UPLOADED[mime][0]
        fname = name if name.lower().endswith(ext) else name + ext
        size = int(meta["size"]) if str(meta.get("size", "")).isdigit() else 0
        if size > kb.MAX_FILE_BYTES:
            raise ApiError(413, f"Berkas terlalu besar (maksimal {kb.MAX_FILE_BYTES // (1024 * 1024)} MB).")
        r = await _request(user_id, "gdrive", "GET", f"{DRIVE_API}/files/{file_id}", params={"alt": "media"}, cap=kb.MAX_FILE_BYTES)
        try:
            text = await asyncio.to_thread(kb.extract, fname, r.content)
        except ValueError as e:
            raise ApiError(422, str(e))
    else:
        raise ApiError(415, "Jenis berkas ini belum didukung (pakai Docs, Sheets, Slides, PDF, Word, TXT, MD, atau CSV).")
    return name, meta.get("webViewLink"), text


async def drive_import_one(user_id: str, file_id: str) -> dict:
    name, link, text = await drive_read(user_id, file_id)
    return await _store(user_id, "gdrive", file_id, name, link, text)


async def drive_import(user_id: str, ids) -> list[dict]:
    return await _import_many(user_id, _ids(ids), drive_import_one)


def drive_file_id(url: str) -> str | None:
    """File id inside a Google Docs / Sheets / Slides / Drive link, None when the link has none."""
    m = re.search(r"/(?:document|spreadsheets|presentation|file)/d/([\w-]+)", url)
    return m.group(1) if m else (re.search(r"[?&]id=([\w-]+)", url) or [None, None])[1]

# ---------- Google Drive write (agents; needs the full drive scope) ----------

DRIVE_WRITE_SCOPE = "https://www.googleapis.com/auth/drive"
DRIVE_NEED_WRITE = "Sambungkan ulang Google Drive di halaman Aplikasi untuk memberi izin mengubah berkas."
DRIVE_UPLOAD = "https://www.googleapis.com/upload/drive/v3"
DRIVE_MAX_BYTES = 1_000_000
DRIVE_FIELDS = "id,name,mimeType,webViewLink"
DOC_MIME = "application/vnd.google-apps.document"
TEXT_MIMES = {"text/plain", "text/markdown", "text/x-markdown", "text/csv"}  # files whose content can be replaced with text


async def drive_can_write(user_id: str) -> None:
    """Raises the friendly reconnect error when the saved consent is the old read-only one (not connected errors come first)."""
    await connections.access_token(user_id, "gdrive")
    if not await connections.has_scope(user_id, "gdrive", DRIVE_WRITE_SCOPE):
        raise ApiError(403, DRIVE_NEED_WRITE, needs="reconnect")


def _file_id(value: str, what: str = "berkas") -> str:
    value = (value or "").strip()
    if value != "root" and not ID_RE.fullmatch(value):
        raise ApiError(400, f"Id {what} tidak valid (pakai id dari drive_search).")
    return value


def _drive_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name or "").strip()
    if not name or len(name) > 200:
        raise ApiError(400, "Nama berkas harus 1 sampai 200 karakter.")
    return name


def _drive_text(content: str) -> bytes:
    if not isinstance(content, str):
        raise ApiError(400, "Isi berkas harus berupa teks.")
    data = content.encode("utf-8")
    if len(data) > DRIVE_MAX_BYTES:
        raise ApiError(413, "Isi terlalu panjang (maksimal 1 MB teks).")
    return data


async def _drive_json(user_id: str, method: str, url: str, **kw) -> dict:
    r = await _request(user_id, "gdrive", method, url, **kw)
    try:
        return r.json()
    except ValueError:
        raise ApiError(502, "Google Drive menjawab dengan format yang tidak dikenal.")


async def _drive_meta(user_id: str, file_id: str, fields: str = "id,name,mimeType,trashed,parents") -> dict:
    return await _drive_json(user_id, "GET", f"{DRIVE_API}/files/{file_id}", params={"fields": fields})


async def drive_create(user_id: str, name: str, content: str, folder_id: str | None = None, kind: str = "doc") -> dict:
    if kind not in ("doc", "text"):
        raise ApiError(400, "kind harus 'doc' atau 'text'.")
    await drive_can_write(user_id)
    name, data = _drive_name(name), _drive_text(content)
    meta = {"name": name, "mimeType": DOC_MIME if kind == "doc" else "text/plain"}
    if folder_id and folder_id.strip():
        meta["parents"] = [_file_id(folder_id, "folder")]
    boundary = "pegawai" + secrets.token_hex(12)
    head = f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{jsonlib.dumps(meta)}\r\n--{boundary}\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n"
    body = head.encode() + data + f"\r\n--{boundary}--".encode()
    f = await _drive_json(user_id, "POST", f"{DRIVE_UPLOAD}/files", params={"uploadType": "multipart", "fields": DRIVE_FIELDS},
                          content=body, headers={"Content-Type": f"multipart/related; boundary={boundary}"})
    return {"id": f.get("id"), "name": f.get("name") or name, "link": f.get("webViewLink")}


async def drive_update(user_id: str, file_id: str, content: str) -> dict:
    file_id = _file_id(file_id)
    await drive_can_write(user_id)
    data = _drive_text(content)
    meta = await _drive_meta(user_id, file_id)
    if meta.get("trashed"):
        raise ApiError(404, "Berkas ini ada di tempat sampah Drive.")
    if meta.get("mimeType") != DOC_MIME and meta.get("mimeType") not in TEXT_MIMES:
        raise ApiError(415, "Isi berkas jenis ini tidak bisa diganti. Hanya Google Docs dan berkas teks yang didukung (bukan PDF, gambar, atau berkas biner).")
    f = await _drive_json(user_id, "PATCH", f"{DRIVE_UPLOAD}/files/{file_id}", params={"uploadType": "media", "fields": DRIVE_FIELDS},
                          content=data, headers={"Content-Type": "text/plain; charset=UTF-8"})
    return {"id": file_id, "name": f.get("name") or meta.get("name"), "link": f.get("webViewLink")}


async def drive_rename(user_id: str, file_id: str, new_name: str) -> dict:
    file_id, new_name = _file_id(file_id), _drive_name(new_name)
    await drive_can_write(user_id)
    f = await _drive_json(user_id, "PATCH", f"{DRIVE_API}/files/{file_id}", params={"fields": DRIVE_FIELDS}, json={"name": new_name})
    return {"id": file_id, "name": f.get("name") or new_name, "link": f.get("webViewLink")}


async def drive_move(user_id: str, file_id: str, folder_id: str) -> dict:
    file_id, folder_id = _file_id(file_id), _file_id(folder_id, "folder")
    await drive_can_write(user_id)
    meta = await _drive_meta(user_id, file_id, "id,name,parents")
    params = {"addParents": folder_id, "fields": DRIVE_FIELDS}
    if meta.get("parents"):
        params["removeParents"] = ",".join(meta["parents"])
    f = await _drive_json(user_id, "PATCH", f"{DRIVE_API}/files/{file_id}", params=params, json={})
    return {"id": file_id, "name": f.get("name") or meta.get("name"), "link": f.get("webViewLink")}


async def drive_trash(user_id: str, file_id: str) -> str:
    """Move to the Drive trash (trashed=true; restorable for 30 days). Called only after the user approved. Returns the file name."""
    file_id = _file_id(file_id)
    await drive_can_write(user_id)
    f = await _drive_json(user_id, "PATCH", f"{DRIVE_API}/files/{file_id}", params={"fields": "id,name"}, json={"trashed": True})
    return f.get("name") or "Berkas"

def _clean_line(text: str, limit: int = 120) -> str:
    return re.sub(r"\s+", " ", text or "").strip()[:limit]


async def drive_card_info(user_id: str, file_id: str) -> dict:
    """What the approval card shows about a file, read from Drive (read-only): real name, owner, folder, already trashed or not.
    The first read raises when Drive cannot answer; the folder name is best effort (a second read)."""
    file_id = _file_id(file_id)
    meta = await _drive_meta(user_id, file_id, "id,name,trashed,owners(displayName,emailAddress),parents")
    owner = next(iter(meta.get("owners") or []), {}) or {}
    folder = ""
    if meta.get("parents"):
        try:
            folder = _clean_line((await _drive_meta(user_id, str(meta["parents"][0]), "name")).get("name") or "")
        except ApiError:
            pass
    return {"name": _clean_line(meta.get("name") or ""), "trashed": bool(meta.get("trashed")), "folder": folder,
            "owner": _clean_line(owner.get("displayName") or owner.get("emailAddress") or "")}

# ---------- re-import ----------


async def refresh_item(user_id: str, item_id: str) -> dict:
    """'Perbarui': fetch the source again. The old item stays untouched when fetching fails."""
    item = await db.q1("select kind, ext_id from kb_items where id::text = %s and user_id = %s", item_id, user_id)
    if not item or not item["ext_id"]:
        raise ApiError(404, "Item ini tidak punya sumber yang bisa diperbarui.")
    if item["kind"] != "gdrive":  # older items imported from our former Notion connection have no source we can reach any more
        raise ApiError(404, "Item ini tidak punya sumber yang bisa diperbarui.")
    return await drive_import_one(user_id, item["ext_id"])

# ---------- Gmail ----------

EMAIL_RE = re.compile(r"[^@\s,;<>]+@[^@\s,;<>]+\.[^@\s,;<>]+")


def build_draft(to: str, subject: str, body: str) -> str:
    """RFC 2822 message, base64url encoded as the Gmail API wants it (field `raw`). No From: Gmail fills in the account."""
    addrs = [a for a in re.split(r"[,;]\s*|\s+", to.strip()) if a]
    if len(addrs) > 20 or not all(EMAIL_RE.fullmatch(a) for a in addrs):
        raise ApiError(400, "Alamat email penerima tidak valid.")
    subject = re.sub(r"[\r\n]+", " ", subject).strip()
    if len(subject) > 300:
        raise ApiError(400, "Subjek terlalu panjang (maksimal 300 karakter).")
    if len(body) > 50_000:
        raise ApiError(400, "Isi email terlalu panjang (maksimal 50.000 karakter).")
    msg = EmailMessage()
    if addrs:
        msg["To"] = ", ".join(addrs)
    msg["Subject"] = subject
    msg.set_content(body or " ", charset="utf-8")
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


async def gmail_draft(user_id: str, to, subject, body) -> dict:
    """Create a DRAFT in the user's Gmail. Nothing is ever sent."""
    if not all(isinstance(x, str) for x in (to or "", subject or "", body or "")):
        raise ApiError(400, "Isi draf tidak valid.")
    raw = build_draft(to or "", subject or "", body or "")
    r = await _request(user_id, "gmail", "POST", f"{GMAIL_API}/users/me/drafts", json={"message": {"raw": raw}})
    d = r.json()
    account = await connections.account_of(user_id, "gmail")
    url = "https://mail.google.com/mail/" + (f"?authuser={quote(account)}" if account else "u/0/") + "#drafts"
    return {"draft_id": d.get("id"), "url": url, "account": account}


# ---------- Gmail read (agents; needs the gmail.readonly scope) ----------

GMAIL_READ_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_NEED_READ = "Sambungkan ulang Gmail di halaman Aplikasi untuk memberi izin membaca."
GMAIL_MAX_BODY = 20_000


async def _gmail_get(user_id: str, path: str, params=None) -> dict:
    await connections.access_token(user_id, "gmail")  # not connected / reconnect errors first
    if not await connections.has_scope(user_id, "gmail", GMAIL_READ_SCOPE):
        raise ApiError(403, GMAIL_NEED_READ, needs="reconnect")
    r = await _request(user_id, "gmail", "GET", f"{GMAIL_API}/users/me/{path}", params=params)
    try:
        return r.json()
    except ValueError:
        raise ApiError(502, "Gmail menjawab dengan format yang tidak dikenal.")


def _header(msg: dict, name: str) -> str:
    for h in (msg.get("payload") or {}).get("headers") or []:
        if str(h.get("name", "")).lower() == name:
            return re.sub(r"\s+", " ", str(h.get("value", ""))).strip()
    return ""


async def gmail_search(user_id: str, query: str, limit: int = 10) -> list[dict]:
    found = await _gmail_get(user_id, "messages", {"q": query, "maxResults": limit})
    out = []
    for m in (found.get("messages") or [])[:limit]:
        d = await _gmail_get(user_id, f"messages/{quote(str(m['id']), safe='')}",
                             [("format", "metadata"), ("metadataHeaders", "From"), ("metadataHeaders", "Subject"), ("metadataHeaders", "Date")])
        out.append({"id": d.get("id") or m["id"], "from": _header(d, "from"), "subject": _header(d, "subject"),
                    "date": _header(d, "date"), "snippet": html.unescape(d.get("snippet") or "")[:160]})
    return out


def _walk(part: dict):
    yield part
    for p in part.get("parts") or []:
        yield from _walk(p)


def _decode(part: dict) -> str:
    data = (part.get("body") or {}).get("data") or ""
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", "replace") if data else ""


def _html_to_text(s: str) -> str:
    s = re.sub(r"(?is)<(script|style|head)\b.*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|li|h[1-6])>", "\n", s)
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    return re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t\r\f\v]+", " ", s)).strip()


def _message_view(d: dict) -> dict:
    parts = [p for p in _walk(d.get("payload") or {}) if not p.get("filename")]
    plain = "\n".join(_decode(p) for p in parts if p.get("mimeType") == "text/plain")
    body = plain.strip() or _html_to_text("\n".join(_decode(p) for p in parts if p.get("mimeType") == "text/html"))
    return {"from": _header(d, "from"), "to": _header(d, "to"), "subject": _header(d, "subject"), "date": _header(d, "date"), "body": body}


async def gmail_read(user_id: str, message_id: str) -> dict:
    return _message_view(await _gmail_get(user_id, f"messages/{quote(message_id, safe='')}", {"format": "full"}))


# ---------- Gmail write (agents): labels and trash at once, sending only after the user approved ----------

GMAIL_MODIFY_SCOPE = "https://www.googleapis.com/auth/gmail.modify"
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
GMAIL_NEED_MODIFY = "Sambungkan ulang Gmail di halaman Aplikasi untuk memberi izin mengubah email."
GMAIL_NEED_SEND = "Sambungkan ulang Gmail di halaman Aplikasi untuk memberi izin mengirim email."
GMAIL_MAX_RECIPIENTS = 10
GMAIL_MAX_LABELS = 10
LABEL_RE = re.compile(r"[A-Za-z0-9_-]{1,100}")
MSGID_RE = re.compile(r"<[^<>\s]{1,300}>")


async def _gmail_need(user_id: str, scope: str, message: str) -> None:
    await connections.access_token(user_id, "gmail")  # not connected / reconnect errors first
    if not await connections.has_scope(user_id, "gmail", scope):
        raise ApiError(403, message, needs="reconnect")


async def _gmail_json(user_id: str, method: str, path: str, *, params=None, body: dict | None = None) -> dict:
    r = await _request(user_id, "gmail", method, f"{GMAIL_API}/users/me/{path}", params=params, json=body)
    try:
        return r.json()
    except ValueError:
        raise ApiError(502, "Gmail menjawab dengan format yang tidak dikenal.")


def _gmail_id(value, what: str = "email") -> str:
    value = value.strip() if isinstance(value, str) else ""
    if not ID_RE.fullmatch(value):
        raise ApiError(400, f"Id {what} tidak valid (pakai id dari gmail_search).")
    return value


def _labels(raw, what: str) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list) or len(raw) > GMAIL_MAX_LABELS or not all(isinstance(x, str) and LABEL_RE.fullmatch(x.strip()) for x in raw):
        raise ApiError(400, f"Daftar label '{what}' tidak valid (maksimal {GMAIL_MAX_LABELS} id label, mis. UNREAD, INBOX, STARRED).")
    return list(dict.fromkeys(x.strip() for x in raw))


async def gmail_label(user_id: str, message_id: str, add=None, remove=None) -> str:
    """Add/remove labels (system ones too: UNREAD = unread, INBOX = archive). Reversible, so it runs at once."""
    message_id, add, remove = _gmail_id(message_id), _labels(add, "add"), _labels(remove, "remove")
    if not add and not remove:
        raise ApiError(400, "Isi label yang ditambah atau dihapus.")
    await _gmail_need(user_id, GMAIL_MODIFY_SCOPE, GMAIL_NEED_MODIFY)
    await _gmail_json(user_id, "POST", f"messages/{quote(message_id, safe='')}/modify", body={"addLabelIds": add, "removeLabelIds": remove})
    return "Label email diperbarui."


async def gmail_trash(user_id: str, message_id: str) -> str:
    """Move to Gmail's Trash (restorable for 30 days; never a permanent delete)."""
    message_id = _gmail_id(message_id)
    await _gmail_need(user_id, GMAIL_MODIFY_SCOPE, GMAIL_NEED_MODIFY)
    await _gmail_json(user_id, "POST", f"messages/{quote(message_id, safe='')}/trash", body={})
    return "Email dipindahkan ke Sampah Gmail."


def parse_recipients(to) -> list[str]:
    if not isinstance(to, str):
        raise ApiError(400, "Alamat email penerima tidak valid.")
    addrs = list(dict.fromkeys(a for a in re.split(r"[,;]\s*|\s+", to.strip()) if a))
    if not addrs:
        raise ApiError(400, "Isi alamat email penerima.")
    if len(addrs) > GMAIL_MAX_RECIPIENTS:
        raise ApiError(400, f"Terlalu banyak penerima (maksimal {GMAIL_MAX_RECIPIENTS}).")
    if not all(EMAIL_RE.fullmatch(a) for a in addrs):
        raise ApiError(400, "Alamat email penerima tidak valid.")
    return addrs


def _raw_message(p: dict) -> str:
    """The exact message from a stored payload: to, subject, body and, for a reply, In-Reply-To / References."""
    msg = EmailMessage()
    msg["To"] = ", ".join(p["to"])
    msg["Subject"] = p["subject"]
    if p.get("in_reply_to"):
        msg["In-Reply-To"] = p["in_reply_to"]
        msg["References"] = p.get("references") or p["in_reply_to"]
    msg.set_content(p["body"], charset="utf-8")
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


async def gmail_prepare_send(user_id: str, to, subject, body, reply_to_message_id: str | None = None) -> dict:
    """Validate and build the payload of a send request (the approval card shows it as it is; approve sends exactly it).
    For a reply the original is read now: thread id and Message-ID headers go into the payload."""
    if not isinstance(subject, str) or not isinstance(body, str):
        raise ApiError(400, "Subjek dan isi email harus berupa teks.")
    addrs = parse_recipients(to)
    subject = re.sub(r"[\r\n]+", " ", subject).strip()
    if not subject or len(subject) > 300:
        raise ApiError(400, "Subjek harus 1 sampai 300 karakter.")
    if not body.strip() or len(body) > 50_000:
        raise ApiError(400, "Isi email harus ada dan maksimal 50.000 karakter.")
    payload = {"to": addrs, "subject": subject, "body": body}
    await _gmail_need(user_id, GMAIL_SEND_SCOPE, GMAIL_NEED_SEND)
    if reply_to_message_id and reply_to_message_id.strip():
        mid = _gmail_id(reply_to_message_id, "email yang dibalas")
        d = await _gmail_get(user_id, f"messages/{quote(mid, safe='')}",
                             [("format", "metadata")] + [("metadataHeaders", h) for h in ("Message-ID", "References", "Subject", "From")])
        orig = _header(d, "message-id")
        if not d.get("threadId") or not MSGID_RE.fullmatch(orig):
            raise ApiError(422, "Email yang dibalas tidak punya penanda percakapan, jadi balasan tidak bisa disambungkan.")
        refs = [t for t in _header(d, "references").split() if MSGID_RE.fullmatch(t)] + [orig]
        payload.update(thread_id=str(d["threadId"]), in_reply_to=orig, references=" ".join(refs),
                       reply_to={"from": _header(d, "from")[:200], "subject": _header(d, "subject")[:200]})
    return payload


async def gmail_send_now(user_id: str, payload: dict) -> str:
    """Called only after the user approved: sends exactly the stored payload."""
    await _gmail_need(user_id, GMAIL_SEND_SCOPE, GMAIL_NEED_SEND)
    body = {"raw": _raw_message(payload)}
    if payload.get("thread_id"):
        body["threadId"] = payload["thread_id"]
    await _gmail_json(user_id, "POST", "messages/send", body=body)
    return f"Email terkirim ke {', '.join(payload['to'])}."


async def gmail_prepare_send_draft(user_id: str, draft_id: str) -> dict:
    """Payload of a draft send request: the draft as Gmail holds it now (recipients, subject, body) and the id of its message,
    so approve can refuse when the draft was edited in between."""
    draft_id = _gmail_id(draft_id, "draf")
    await _gmail_need(user_id, GMAIL_SEND_SCOPE, GMAIL_NEED_SEND)
    m = (await _gmail_json(user_id, "GET", f"drafts/{quote(draft_id, safe='')}", params={"format": "full"})).get("message") or {}
    v = _message_view(m)
    if not m.get("id") or not v["to"].strip():
        raise ApiError(422, "Draf ini belum punya penerima, jadi tidak bisa dikirim.")
    return {"draft_id": draft_id, "message_id": str(m["id"]), "to": v["to"], "subject": v["subject"], "body": v["body"][:50_000]}


async def gmail_send_draft_now(user_id: str, payload: dict) -> str:
    """Called only after the user approved: sends the draft only if it is still the one the user saw."""
    await _gmail_need(user_id, GMAIL_SEND_SCOPE, GMAIL_NEED_SEND)
    now = ((await _gmail_json(user_id, "GET", f"drafts/{quote(payload['draft_id'], safe='')}", params={"format": "minimal"})).get("message") or {}).get("id")
    if now != payload["message_id"]:
        raise ApiError(409, "Draf ini berubah sejak diminta, jadi tidak dikirim. Minta agen mengajukan ulang.")
    await _gmail_json(user_id, "POST", "drafts/send", body={"id": payload["draft_id"]})
    return f"Draf terkirim ke {payload['to']}."
