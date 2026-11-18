"""Per-user Knowledge Base: files and links the user adds from chat (decision: stored in our Postgres, not a Hermes memory provider).
Flow: extract text -> split into chunks -> keyword search -> the best chunks go into the run instructions with the item name cited."""
import asyncio
import io
import ipaddress
import re
import socket
import uuid
import zipfile
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlsplit
from xml.etree import ElementTree

import httpx

from . import db
from .errors import ApiError

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_PAGE_BYTES = 5 * 1024 * 1024     # a fetched page or Drive file
MAX_TEXT_CHARS = 600_000             # extracted text kept per item
MAX_ITEMS = 100
MAX_URLS_PER_MESSAGE = 3
MAX_REDIRECTS = 5
FETCH_TIMEOUT = 15.0
CHUNK_CHARS = 1000
CONTEXT_CHUNKS = 5                   # search hits per run
CONTEXT_CHARS = 6000                 # whole KB block per run
ATTACHED_CHARS = 3000                # per attached item: its first chunks
FILE_TYPES = (".txt", ".md", ".csv", ".pdf", ".docx")
UA = "PegawaiAI-KnowledgeBase/1.0"

# ---------- text extraction ----------


def _clean(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+\n", "\n", text)).strip()


def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("latin-1", errors="replace")


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader
    try:
        r = PdfReader(io.BytesIO(data))
        if r.is_encrypted:
            raise ValueError("PDF ini dikunci dengan kata sandi.")
        out, n = [], 0
        for page in r.pages[:300]:
            t = page.extract_text() or ""
            out.append(t)
            n += len(t)
            if n > MAX_TEXT_CHARS:
                break
    except ValueError:
        raise
    except Exception:
        raise ValueError("PDF ini tidak bisa dibaca. Coba simpan ulang dari aplikasi asalnya.")
    return "\n\n".join(out)


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _docx_text(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            info = z.getinfo("word/document.xml")
            if info.file_size > 30 * 1024 * 1024:  # zip bomb guard
                raise ValueError("Dokumen Word ini terlalu besar untuk diproses.")
            root = ElementTree.fromstring(z.read(info))
    except ValueError:
        raise
    except (zipfile.BadZipFile, KeyError, ElementTree.ParseError):
        raise ValueError("Berkas Word ini tidak bisa dibaca. Pastikan formatnya .docx.")
    paras = []
    for p in root.iter(W + "p"):
        parts = []
        for e in p.iter():
            if e.tag == W + "t":
                parts.append(e.text or "")
            elif e.tag in (W + "tab", W + "br"):
                parts.append(" ")
        paras.append("".join(parts))
    return "\n".join(paras)


def extract(name: str, data: bytes) -> str:
    """Plain text of an uploaded file. Raises ValueError with a plain reason (shown to the user)."""
    ext = "." + name.lower().rsplit(".", 1)[-1] if "." in name else ""
    if ext == ".pdf":
        text = _pdf_text(data)
        if not _clean(text):
            raise ValueError("PDF ini tidak berisi teks yang bisa dibaca (mungkin hasil pindai berupa gambar).")
    elif ext == ".docx":
        text = _docx_text(data)
    elif ext in (".txt", ".md", ".csv"):
        text = _decode(data)
    else:
        raise ValueError("Jenis berkas tidak didukung.")
    text = _clean(text)
    if not text:
        raise ValueError("Berkas ini kosong.")
    return text[:MAX_TEXT_CHARS]


SKIP_TAGS = {"script", "style", "noscript", "svg", "template", "head", "iframe", "form", "nav", "footer"}
BLOCK_TAGS = {"p", "div", "br", "li", "tr", "section", "article", "main", "h1", "h2", "h3", "h4", "h5", "h6", "table",
              "ul", "ol", "blockquote", "pre", "hr", "header"}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.title = ""
        self._skip = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        if tag in SKIP_TAGS:
            self._skip += 1
        elif tag in BLOCK_TAGS:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in SKIP_TAGS:
            self._skip = max(0, self._skip - 1)
        elif tag in BLOCK_TAGS:
            self.out.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip:
            self.out.append(data)


def html_to_text(html: str) -> tuple[str, str]:
    """(title, readable text) of an HTML page. Scripts, styles, navigation and forms are dropped."""
    p = _Text()
    p.feed(html)
    p.close()
    lines = (re.sub(r"[ \t ]+", " ", ln).strip() for ln in "".join(p.out).split("\n"))
    return re.sub(r"\s+", " ", p.title).strip(), _clean("\n".join(lines))

# ---------- chunking and search query ----------


def chunk(text: str, size: int = CHUNK_CHARS) -> list[str]:
    """Paragraph-aware pieces of at most `size` characters (an overlong paragraph is cut at sentence or word ends)."""
    out, cur = [], ""
    for para in (p.strip() for p in re.split(r"\n\s*\n", text)):
        while len(para) > size:
            cut = max(para.rfind(". ", 0, size), para.rfind("\n", 0, size), para.rfind(" ", 0, size))
            cut = cut + 1 if cut > size // 2 else size
            if cur:
                out.append(cur)
                cur = ""
            out.append(para[:cut].strip())
            para = para[cut:].strip()
        if not para:
            continue
        if cur and len(cur) + len(para) + 2 > size:
            out.append(cur)
            cur = ""
        cur = f"{cur}\n\n{para}" if cur else para
    if cur:
        out.append(cur)
    return [c for c in out if c]


URL_RE = re.compile(r"https?://[^\s<>\"'`]+", re.I)
STOP = set("yang dan di ke dari untuk dengan ini itu atau pada adalah akan juga saya aku kamu anda tolong mohon bisa "
           "apa bagaimana kenapa tentang the and for with that this are was you your please can about what how why from have "
           "link url file simpan pelajari baca save read learn knowledge base".split())


def tsquery(text: str) -> str | None:
    """OR of the message's content words, as a to_tsquery string (words are \\w only, so it cannot be malformed)."""
    seen: list[str] = []
    for t in re.findall(r"\w+", URL_RE.sub(" ", text).lower()):
        if len(t) >= 3 and t not in STOP and t not in seen:
            seen.append(t)
    return " | ".join(seen[:12]) or None

# ---------- link intent ----------


INTENT_RE = re.compile(
    r"\b(simpan\w*|simpen\w*|pelajari\w*|baca\w*|bacain|jadikan|jadiin|masukkan|masukin|tambahkan|tambahin|"
    r"hafal\w*|ingat\w*|serap|save|read|learn|study|memorize|remember|store|ingest|index|knowledge)\b"
    r"|\badd\b.{0,30}\b(knowledge|kb)\b", re.I)


def urls_in(text: str) -> list[str]:
    """http(s) links in the text, in order, without trailing punctuation, deduplicated."""
    out: list[str] = []
    for m in URL_RE.findall(text):
        u = m.rstrip(".,;:!?)]}>")
        if u not in out:
            out.append(u)
    return out


def wants_save(text: str) -> bool:
    """The message asks to read / save / learn (Indonesian or English)."""
    return bool(INTENT_RE.search(URL_RE.sub(" ", text)))

# ---------- SSRF guard and fetch ----------


async def _resolve(host: str, port: int) -> list[str]:
    infos = await asyncio.get_running_loop().getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return [i[4][0] for i in infos]


def _public(addr: str) -> bool:
    ip = ipaddress.ip_address(addr.split("%")[0])
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast  # not private, loopback, link-local (169.254 metadata), CGNAT, reserved


class Blocked(Exception):
    """A URL we will not fetch (or a fetch that failed); the message is shown to the user."""


async def check_url(url: str) -> None:
    """http/https only, and every address the host resolves to must be public. Raises Blocked."""
    u = urlsplit(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise Blocked("Hanya alamat http atau https yang bisa dibaca.")
    if u.username or u.password:
        raise Blocked("Alamat yang memuat nama pengguna atau kata sandi tidak diizinkan.")
    try:
        addrs = await _resolve(u.hostname, u.port or (443 if u.scheme == "https" else 80))
    except (OSError, ValueError):
        raise Blocked("Alamat ini tidak ditemukan. Periksa kembali linknya.")
    if not addrs or not all(_public(a) for a in addrs):
        raise Blocked("Alamat ini mengarah ke jaringan internal dan tidak diizinkan.")


async def fetch(url: str, client: httpx.AsyncClient | None = None) -> tuple[httpx.Response, bytes]:
    """GET with manual redirects (each hop is checked), a size cap and a timeout.
    shortcut: the address is checked before connecting, not pinned to the connection (a DNS rebinding window remains),
    upgrade by pinning the validated IP in a custom httpx transport."""
    own = client is None
    client = client or httpx.AsyncClient(timeout=FETCH_TIMEOUT, follow_redirects=False, headers={"User-Agent": UA})
    try:
        for _ in range(MAX_REDIRECTS + 1):
            await check_url(url)
            async with client.stream("GET", url) as r:
                if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("location"):
                    url = urljoin(url, r.headers["location"])
                    continue
                body = bytearray()
                async for part in r.aiter_bytes():
                    body += part
                    if len(body) > MAX_PAGE_BYTES:
                        raise Blocked("Halaman ini terlalu besar (maksimal 5 MB).")
                return r, bytes(body)
        raise Blocked("Link ini dialihkan terlalu sering.")
    finally:
        if own:
            await client.aclose()


def _charset_text(r: httpx.Response, body: bytes) -> str:
    try:
        return body.decode(r.charset_encoding or "utf-8", errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


DRIVE_NEEDS_CONNECT = ("Dokumen ini tidak bisa dibuka tanpa login. Bagikan sebagai \"siapa saja yang memiliki link\" "
                       "atau hubungkan Google Drive di Aplikasi.")


def drive_target(url: str) -> tuple[str, str] | None:
    """(download URL, label) for a Google Docs / Sheets / Slides / Drive file link, or None for any other URL."""
    u = urlsplit(url)
    host = (u.hostname or "").lower()
    if host == "docs.google.com":
        m = re.search(r"/(document|spreadsheets|presentation)/d/([\w-]+)", u.path)
        if not m:
            return None
        kind, did = m.groups()
        if kind == "document":
            return f"https://docs.google.com/document/d/{did}/export?format=txt", "Google Docs"
        if kind == "presentation":
            return f"https://docs.google.com/presentation/d/{did}/export?format=txt", "Google Slides"
        gid = (parse_qs(u.query).get("gid") or parse_qs(u.fragment).get("gid") or [""])[0]
        return (f"https://docs.google.com/spreadsheets/d/{did}/export?format=csv" + (f"&gid={gid}" if gid.isdigit() else ""),
                "Google Sheets")
    if host == "drive.google.com":
        m = re.search(r"/file/d/([\w-]+)", u.path)
        fid = m.group(1) if m else (parse_qs(u.query).get("id") or [""])[0]
        if re.fullmatch(r"[\w-]+", fid):
            return f"https://drive.google.com/uc?export=download&id={fid}", "Google Drive"
        if "/folders/" in u.path:
            return "folder", "Google Drive"
    return None

# ---------- items ----------


def view(row: dict) -> dict:
    return {**{k: row[k] for k in ("kind", "name", "source", "status", "error", "size_bytes", "chars", "created_at")},
            "id": str(row["id"]), "refreshable": bool(row.get("ext_id")), "has_file": bool(row.get("has_file"))}


async def _new_item(user_id: str, kind: str, name: str, source: str | None, size: int | None) -> dict:
    if (await db.q1("select count(*)::int as n from kb_items where user_id = %s", user_id))["n"] >= MAX_ITEMS:
        raise ApiError(409, f"Knowledge Base penuh (maksimal {MAX_ITEMS} item). Hapus yang tidak dipakai.")
    return await db.q1("insert into kb_items (user_id, kind, name, source, size_bytes) values (%s, %s, %s, %s, %s) returning *",
                       user_id, kind, name[:200], source, size)


async def _fail(item: dict, error: str) -> dict:
    return view(await db.q1("update kb_items set status = 'failed', error = %s where id = %s returning *", error, item["id"]))


async def _ready(item: dict, text: str, name: str | None = None, kind: str | None = None) -> dict:
    pieces = chunk(text)
    async with db.pool.connection() as c:
        async with c.transaction():
            async with c.cursor() as cur:
                await cur.executemany("insert into kb_chunks (item_id, user_id, pos, text) values (%s, %s, %s, %s)",
                                      [(item["id"], item["user_id"], i, p) for i, p in enumerate(pieces)])
            cur = await c.execute("update kb_items set status = 'ready', error = null, chars = %s, "
                                  "name = coalesce(%s, name), kind = coalesce(%s, kind) where id = %s returning *",
                                  (len(text), name, kind, item["id"]))
            return view(await cur.fetchone())


# Content types an original may be served with (allowlist; the browser never sniffs, see main.py kb_file).
FILE_MIMES = {".pdf": "application/pdf", ".txt": "text/plain; charset=utf-8", ".md": "text/plain; charset=utf-8",
              ".csv": "text/csv; charset=utf-8",
              ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
MAX_VIEW_CHARS = 200_000             # stored text returned for preview


def file_mime(name: str) -> str:
    return FILE_MIMES["." + name.lower().rsplit(".", 1)[-1]]


def check_file(name: str, size: int) -> None:
    """Server-side type and size check; rejected files never become an item."""
    if not name.lower().endswith(FILE_TYPES):
        raise ApiError(415, f"Jenis berkas tidak didukung. Pakai: {', '.join(FILE_TYPES)}.")
    if size == 0:
        raise ApiError(400, "Berkas ini kosong.")
    if size > MAX_FILE_BYTES:
        raise ApiError(413, f"Berkas terlalu besar (maksimal {MAX_FILE_BYTES // (1024 * 1024)} MB).")


async def ingest_file(user_id: str, name: str, data: bytes) -> dict:
    name = re.sub(r"[\\/]", "_", name).strip() or "berkas"
    check_file(name, len(data))
    item = await _new_item(user_id, "file", name, None, len(data))
    try:
        text = await asyncio.to_thread(extract, name, data)
    except ValueError as e:
        return await _fail(item, str(e))
    except Exception:
        return await _fail(item, "Berkas ini tidak bisa diproses.")
    item = await _ready(item, text)
    await db.ex("insert into kb_files (item_id, mime, data) values (%s, %s, %s)", item["id"], file_mime(name), data)
    item["has_file"] = True
    return item


def _label(url: str) -> str:
    u = urlsplit(url)
    return (u.hostname or url) + (u.path if u.path not in ("", "/") else "")


async def _download(url: str) -> tuple[str, str, str]:
    """(kind, name, text) of a link. Raises Blocked with a plain reason."""
    drive = drive_target(url)
    if drive and drive[0] == "folder":
        raise Blocked("Folder Google Drive belum bisa dibaca. Kirim link ke satu dokumen.")
    try:
        r, body = await fetch(drive[0] if drive else url)
    except Blocked:
        raise
    except httpx.TimeoutException:
        raise Blocked("Situs ini terlalu lama menjawab.")
    except httpx.HTTPError:
        raise Blocked("Situs ini tidak bisa dihubungi.")
    ctype = r.headers.get("content-type", "").split(";")[0].strip().lower()
    if drive and ((r.url.host or "").endswith("accounts.google.com") or r.status_code in (301, 302, 303, 307, 308, 401, 403, 404)):
        raise Blocked(DRIVE_NEEDS_CONNECT)  # a redirect left here means the sign-in page
    if r.status_code >= 400:
        raise Blocked(f"Situs menjawab dengan kesalahan {r.status_code}.")
    if ctype == "text/html":
        if drive:  # a login page or a "cannot scan for viruses" page instead of the file
            raise Blocked(DRIVE_NEEDS_CONNECT)
        title, text = html_to_text(_charset_text(r, body))
        return "url", title or _label(url), text
    if ctype.startswith("text/") or ctype in ("application/csv", "application/json"):
        text = _clean(_charset_text(r, body))
    elif ctype == "application/pdf":
        text = _clean(await asyncio.to_thread(_pdf_text, body))
    elif ctype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = _clean(await asyncio.to_thread(_docx_text, body))
    else:
        raise Blocked("Jenis isi link ini belum didukung (bukan halaman web, teks, PDF, atau Word).")
    return ("gdrive", f"{drive[1]}: {_label(url)}", text) if drive else ("url", _label(url), text)


async def ingest_url(user_id: str, url: str) -> dict:
    """Fetch and store a link. A fetch problem never raises: the item is saved as failed with the reason."""
    u = urlsplit(url)
    if u.scheme not in ("http", "https") or not u.hostname or len(url) > 2000:
        raise ApiError(400, "Masukkan alamat web yang diawali http:// atau https://")
    drive = drive_target(url)
    if drive and drive[0] != "folder":  # a private Drive file opens through the user's connection when there is one
        from . import connections, integrations
        fid = integrations.drive_file_id(url)
        if fid and await connections.is_connected(user_id, "gdrive"):
            try:
                return await integrations.drive_import_one(user_id, fid)
            except ApiError as e:
                item = await _new_item(user_id, "gdrive", _label(url), url, None)
                return await _fail(item, e.message)
    await db.ex("delete from kb_items where user_id = %s and source = %s", user_id, url)  # adding again refreshes the item
    item = await _new_item(user_id, "gdrive" if drive_target(url) else "url", _label(url), url, None)
    try:
        kind, name, text = await _download(url)
    except Blocked as e:
        return await _fail(item, str(e))
    except ValueError as e:  # unreadable PDF / Word file
        return await _fail(item, str(e))
    except Exception:
        return await _fail(item, "Link ini tidak bisa diproses.")
    text = text[:MAX_TEXT_CHARS]
    if len(text) < 20:
        return await _fail(item, "Tidak ada teks yang bisa dibaca di link ini (mungkin halamannya dimuat dengan JavaScript).")
    await db.ex("update kb_items set size_bytes = %s where id = %s", len(text.encode()), item["id"])
    return await _ready(item, text, name[:200], kind)


async def list_items(user_id: str) -> list[dict]:
    return [view(r) for r in await db.q(
        "select i.*, exists(select 1 from kb_files f where f.item_id = i.id) as has_file "
        "from kb_items i where i.user_id = %s order by i.created_at desc", user_id)]


def _own_id(item_id: str) -> str:
    try:
        return str(uuid.UUID(item_id))
    except ValueError:
        raise ApiError(404, "Item tidak ditemukan")


async def get_file(user_id: str, item_id: str) -> tuple[str, str, bytes]:
    """(name, mime, bytes) of the original file of one of the user's items. 404 when the item or its original does not exist."""
    r = await db.q1("select i.name, f.mime, f.data from kb_items i join kb_files f on f.item_id = i.id "
                    "where i.id = %s and i.user_id = %s", _own_id(item_id), user_id)
    if not r:
        raise ApiError(404, "Berkas asli tidak tersimpan. Unggah ulang bila perlu.")
    return r["name"], r["mime"], bytes(r["data"])


async def get_text(user_id: str, item_id: str) -> dict:
    """The stored text (chunks in order) of one of the user's items, capped at MAX_VIEW_CHARS."""
    item = await db.q1("select * from kb_items where id = %s and user_id = %s", _own_id(item_id), user_id)
    if not item:
        raise ApiError(404, "Item tidak ditemukan")
    rows = await db.q("select text from kb_chunks where item_id = %s order by pos", item["id"])
    text = (chr(10) * 2).join(r["text"] for r in rows)
    return {"text": text[:MAX_VIEW_CHARS], "truncated": len(text) > MAX_VIEW_CHARS}


async def delete_item(user_id: str, item_id: str) -> None:
    try:
        uuid.UUID(item_id)
    except ValueError:
        raise ApiError(404, "Item tidak ditemukan")
    if not await db.q1("delete from kb_items where id = %s and user_id = %s returning 1 as x", item_id, user_id):
        raise ApiError(404, "Item tidak ditemukan")


async def recover() -> None:
    await db.ex("update kb_items set status = 'failed', error = 'Proses terhenti karena server dimulai ulang. Tambahkan lagi.' "
                "where status = 'processing'")

# ---------- retrieval ----------


async def search(user_id: str, text: str, limit: int = CONTEXT_CHUNKS) -> list[dict]:
    """Best matching chunks of the user's ready items for a message.
    shortcut: keyword search (Postgres full-text), upgrade to pgvector embeddings when an embedding provider is chosen."""
    q = tsquery(text)
    if not q:
        return []
    return await db.q(
        "select i.id as item_id, i.name, i.source, c.pos, c.text, ts_rank(c.tsv, query) as rank "
        "from kb_chunks c join kb_items i on i.id = c.item_id, to_tsquery('simple', %s) query "
        "where c.user_id = %s and i.status = 'ready' and c.tsv @@ query order by rank desc, c.id limit %s", q, user_id, limit)


async def attached(user_id: str, ids: list[str]) -> list[dict]:
    """The first chunks (about ATTACHED_CHARS) of each ready item the user attached to this message."""
    out = []
    for iid in ids:
        rows = await db.q("select i.id as item_id, i.name, i.source, c.pos, c.text from kb_chunks c join kb_items i on i.id = c.item_id "
                          "where i.id = %s and i.user_id = %s and i.status = 'ready' order by c.pos limit 6", iid, user_id)
        used = 0
        for r in rows:
            if used and used + len(r["text"]) > ATTACHED_CHARS:
                break
            used += len(r["text"])
            out.append(r)
    return out


async def owned_ids(user_id: str, ids) -> list[str]:
    """Validate the optional `kb_items` of a request: a list of at most 10 item ids, of this user's items only."""
    if ids is None:
        return []
    if not isinstance(ids, list) or len(ids) > 10 or not all(isinstance(i, str) for i in ids):
        raise ApiError(400, "kb_items harus berupa daftar id (maksimal 10)")
    try:
        ids = [str(uuid.UUID(i)) for i in ids]
    except ValueError:
        raise ApiError(400, "kb_items berisi id yang tidak valid")
    rows = await db.q("select id from kb_items where user_id = %s and id = any(%s::uuid[])", user_id, ids)
    mine = {str(r["id"]) for r in rows}
    return [i for i in ids if i in mine]


def block(saved: list[dict], chunks: list[dict]) -> str | None:
    """The instruction text for a run: what was just saved (or why not) and the relevant excerpts, each citing its item."""
    if not saved and not chunks:
        return None
    parts = ["# KNOWLEDGE BASE PENGGUNA"]
    if saved:
        parts.append("Pada pesan ini pengguna meminta menyimpan sumber berikut ke Knowledge Base. Sampaikan hasilnya dengan singkat:")
        for s in saved:
            if s["status"] == "ready":
                parts.append(f"- Tersimpan: {s['name']}" + (f" ({s['source']})" if s.get("source") else ""))
            else:
                parts.append(f"- GAGAL disimpan: {s.get('source') or s['name']}. Alasan: {s.get('error') or 'tidak diketahui'}. "
                             "Jangan mengarang isinya. Katakan apa adanya kepada pengguna.")
    if chunks:
        parts.append("Kutipan dari Knowledge Base pengguna yang mungkin relevan. Gunakan hanya jika cocok dengan pertanyaan, "
                     "dan sebutkan nama sumbernya (dalam tanda kurung siku) saat memakai fakta dari sana.")
        used = 0
        for c in chunks:
            piece = f"[{c['name']}]\n{c['text']}"
            if used + len(piece) > CONTEXT_CHARS:
                break
            used += len(piece)
            parts.append(piece)
    return "\n\n".join(parts)


async def _save_link(user_id: str, url: str) -> dict:
    try:
        return await ingest_url(user_id, url)
    except ApiError as e:  # e.g. the Knowledge Base is full: reported like any other failed item
        return {"id": None, "kind": "url", "name": _label(url), "source": url, "status": "failed", "error": e.message,
                "size_bytes": None, "chars": None, "created_at": None}


async def save_links(user_id: str, text: str) -> list[dict]:
    """Save the links of a message that asks to read / save / learn them. Nothing to do when it does not."""
    if not wants_save(text):
        return []
    return list(await asyncio.gather(*(_save_link(user_id, u) for u in urls_in(text)[:MAX_URLS_PER_MESSAGE])))


async def retrieve(user_id: str, text: str, attached_ids: list[str], saved: list[dict]) -> str | None:
    """The instruction block for a run: first chunks of attached and just-saved items, then the best keyword matches."""
    first = await attached(user_id, list(attached_ids) + [s["id"] for s in saved if s["status"] == "ready"])
    seen = {(h["item_id"], h["pos"]) for h in first}
    return block(saved, first + [h for h in await search(user_id, text) if (h["item_id"], h["pos"]) not in seen])


def saved_note(saved: list[dict]) -> str:
    """One system line for a group about what was saved from a message (also read by the bots)."""
    return "Knowledge Base: " + "; ".join(
        f"{s['name']} tersimpan" if s["status"] == "ready" else f"{s.get('source') or s['name']} gagal disimpan ({s.get('error')})"
        for s in saved)
