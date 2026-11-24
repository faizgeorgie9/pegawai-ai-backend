"""Knowledge base for uploaded documents (PDF, DOCX, text, CSV) and websites.

Uploaded sources are extra evidence for a run: they never replace the CS v2.1
instructions or the approved SOPs. Retrieval is local and deterministic so the
same question gets the same excerpts, and every excerpt keeps its source label.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import ipaddress
import re
import socket
import unicodedata
from datetime import date
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

import httpx

from . import db
from .errors import ApiError

MAX_BYTES = 10 * 1024 * 1024
MAX_STORED_CHARS = 400_000
CHUNK_CHARS = 1_400
CHUNK_OVERLAP = 200
CONTEXT_CHARS = 4_000
MAX_MATCHES = 4
SCOPES = ("cs", "marketing", "all")
FILE_KINDS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".json": "application/json",
}

_STOP = {
    "aku", "saya", "mau", "ingin", "butuh", "untuk", "yang", "dan", "atau", "dengan", "di",
    "ke", "ini", "itu", "ada", "apakah", "bisa", "tolong", "dong", "please", "the", "a", "an",
    "for", "and", "or", "with", "some", "kak", "ya", "nya", "dari", "pada", "juga", "akan",
}


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def tokens(value: str) -> set[str]:
    return {t for t in normalize(value).split() if t not in _STOP and len(t) > 1}


class _Text(HTMLParser):
    """Collect visible text, skipping script, style and navigation chrome."""

    SKIP = {"script", "style", "noscript", "svg", "iframe", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title = ""
        self._skip = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self.SKIP:
            self._skip += 1
        elif tag == "title":
            self._in_title = True
        elif tag in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "section", "article"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        elif tag == "title":
            self._in_title = False
        elif tag in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        value = re.sub(r"\s+", " ", data).strip()
        if not value:
            return
        if self._in_title:
            self.title = (self.title + " " + value).strip()
        self.parts.append(value + " ")

    def text(self) -> str:
        raw = "".join(self.parts)
        lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in raw.splitlines()]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(ln for ln in lines if ln)).strip()


def html_to_text(data: bytes) -> tuple[str, str]:
    """(title, text) from an HTML page."""
    parser = _Text()
    parser.feed(data.decode("utf-8", "replace"))
    parser.close()
    return parser.title, parser.text()


def extract(filename: str, data: bytes) -> tuple[str, str | None]:
    """(text, page_count) from an uploaded file. Raises ApiError for unusable input."""
    suffix = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    if suffix not in FILE_KINDS:
        raise ApiError(400, "Jenis berkas tidak didukung. Pakai PDF, DOCX, TXT, MD, CSV, atau JSON.")
    if not data:
        raise ApiError(400, "Berkas kosong.")
    if len(data) > MAX_BYTES:
        raise ApiError(413, "Berkas terlalu besar (maksimal 10 MB).")

    if suffix == ".pdf":
        from pypdf import PdfReader

        try:
            reader = PdfReader(io.BytesIO(data))
            pages = [(page.extract_text() or "").strip() for page in reader.pages]
        except Exception as exc:  # pypdf raises many different errors
            raise ApiError(400, "PDF tidak bisa dibaca. Pastikan berkas tidak terkunci atau rusak.") from exc
        text = "\n\n".join(p for p in pages if p)
        return _clean(text, "PDF tidak berisi teks yang bisa dibaca (mungkin hasil pindai)."), len(pages)

    if suffix == ".docx":
        import docx

        try:
            document = docx.Document(io.BytesIO(data))
        except Exception as exc:
            raise ApiError(400, "DOCX tidak bisa dibaca. Pastikan berkas tidak rusak.") from exc
        parts = [p.text for p in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells]
                if any(cells):
                    parts.append(" | ".join(cells))
        return _clean("\n".join(parts), "DOCX tidak berisi teks yang bisa dibaca."), None

    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ApiError(400, "Teks berkas tidak bisa dibaca.")
    return _clean(text, "Berkas tidak berisi teks yang bisa dibaca."), None


def _clean(text: str, empty_message: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise ApiError(400, empty_message)
    return text[:MAX_STORED_CHARS]


def chunks(text: str, size: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split on paragraph/sentence boundaries where possible, with a small overlap."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    out: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind("\n\n"), window.rfind(". "), window.rfind("\n"))
            if cut >= int(size * 0.6):
                end = start + cut + 1
        piece = text[start:end].strip()
        if piece:
            out.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return out


def _hits(query_tokens: set[str], chunk_tokens: set[str]) -> int:
    hits = 0
    for token in query_tokens:
        if token in chunk_tokens or (token.endswith("s") and token[:-1] in chunk_tokens):
            hits += 1
    return hits


def rank(query: str, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Best matching chunks, only when at least two query words (or one long word) occur."""
    query_tokens = tokens(query)
    if not query_tokens:
        return []
    need = 2 if len(query_tokens) >= 2 else 1
    found: list[dict[str, Any]] = []
    for source in sources:
        title_hit = _hits(query_tokens, tokens(source.get("title") or ""))
        for index, chunk in enumerate(chunks(source["content"])):
            hit = _hits(query_tokens, tokens(chunk))
            if hit + title_hit < (1 if title_hit else need):
                continue
            found.append({
                "source_id": source["id"],
                "title": source["title"],
                "kind": source["kind"],
                "url": source.get("url"),
                "created_at": source.get("created_at"),
                "chunk": index,
                "score": hit + title_hit,
                "text": chunk,
            })
    found.sort(key=lambda item: (-item["score"], item["title"], item["chunk"]))
    out: list[dict[str, Any]] = []
    used = 0
    for item in found:
        if len(out) >= MAX_MATCHES or used + len(item["text"]) > CONTEXT_CHARS:
            continue
        out.append(item)
        used += len(item["text"])
    return out


def _date(value: Any) -> str | None:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and value:
        return value[:10]
    return None


def compose(matches: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    """Prompt section and context refs for the matched excerpts."""
    if not matches:
        return "", []
    lines = [
        "## Dokumen pengetahuan tambahan (unggahan)",
        "Kutipan berikut berasal dari dokumen yang diunggah pengguna dan hanya berlaku untuk permintaan ini. "
        "Gunakan sebagai bukti tambahan; jika bertentangan dengan instruksi CS v2.1, SOP, atau data resmi, "
        "sebutkan konfliknya dan jangan mengarang. Harga/stok dalam dokumen bukan data live kecuali berasal "
        "dari spreadsheet yang terhubung.",
    ]
    refs = []
    seen = set()
    for item in matches:
        moment = _date(item.get("created_at")) or "tanggal tidak tercatat"
        lines.append(f"\n### {item['title']} ({item['kind']}, {moment})\n{item['text']}")
        if item["source_id"] in seen:
            continue
        seen.add(item["source_id"])
        refs.append({
            "type": "knowledge",
            "id": f"KB-{str(item['source_id'])[:8]}",
            "title": item["title"],
            "classification": "Uploaded Document",
            "source_id": None,
            "url": item.get("url"),
            "accessed_date": _date(item.get("created_at")),
        })
    return "\n".join(lines), refs


async def search(user_id: str, query: str, scope: str = "cs") -> list[dict[str, Any]]:
    rows = await db.q(
        "select id, kind, title, url, created_at, content from knowledge_sources "
        "where user_id = %s and scope in (%s, 'all')", user_id, scope)
    return rank(query, rows)


async def context_for(user_id: str, query: str, scope: str = "cs") -> tuple[str, list[dict[str, Any]]]:
    """Prompt section for a run; empty when nothing relevant is uploaded."""
    if not query.strip():
        return "", []
    return compose(await search(user_id, query, scope))


async def list_sources(user_id: str, scope: str | None = None) -> list[dict[str, Any]]:
    if scope in (None, "all"):
        return await db.q(
            "select id, scope, kind, title, url, filename, mime, size_bytes, sha256, created_at "
            "from knowledge_sources where user_id = %s order by created_at desc, title", user_id)
    return await db.q(
        "select id, scope, kind, title, url, filename, mime, size_bytes, sha256, created_at "
        "from knowledge_sources where user_id = %s and scope in (%s, 'all') order by created_at desc, title",
        user_id, scope)


async def add(user_id: str, scope: str, kind: str, title: str, content: str, *, url: str | None = None,
              filename: str | None = None, mime: str | None = None, size_bytes: int | None = None) -> dict[str, Any]:
    scope = scope if scope in SCOPES else "cs"
    title = re.sub(r"\s+", " ", title).strip()[:160]
    if not title:
        raise ApiError(400, "Judul dokumen wajib diisi.")
    if not content.strip():
        raise ApiError(400, "Dokumen tidak berisi teks.")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    row = await db.q1(
        "insert into knowledge_sources (user_id, scope, kind, title, url, filename, mime, size_bytes, sha256, content) "
        "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "returning id, scope, kind, title, url, filename, mime, size_bytes, sha256, created_at",
        user_id, scope, kind, title, url, filename, mime, size_bytes, digest, content)
    return row or {}


async def delete(user_id: str, source_id: str) -> None:
    import uuid

    try:
        key = str(uuid.UUID(source_id))
    except ValueError:
        raise ApiError(404, "Dokumen tidak ditemukan")
    if not await db.q1("select 1 as x from knowledge_sources where id = %s and user_id = %s", key, user_id):
        raise ApiError(404, "Dokumen tidak ditemukan")
    await db.ex("delete from knowledge_sources where id = %s and user_id = %s", key, user_id)


def _private_host(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return True
    for info in infos:
        address = info[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return True
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return True
    return False


async def fetch_website(raw_url: str) -> dict[str, str]:
    """Fetch an http(s) page and return {title, text, url}."""
    url = raw_url.strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ApiError(400, "Alamat situs tidak valid.")
    if await asyncio.to_thread(_private_host, parsed.hostname):
        raise ApiError(400, "Alamat situs tidak diizinkan.")
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15,
                                     headers={"User-Agent": "PegawaiAI-KnowledgeBot/1.0"}) as client:
            response = await client.get(url)
    except httpx.HTTPError as exc:
        raise ApiError(502, "Situs tidak bisa diambil. Periksa alamat atau koneksi.") from exc
    if response.status_code >= 400:
        raise ApiError(502, f"Situs menolak permintaan (HTTP {response.status_code}).")
    if len(response.content) > MAX_BYTES:
        raise ApiError(413, "Halaman terlalu besar (maksimal 10 MB).")
    ctype = response.headers.get("content-type", "").lower()
    if "html" not in ctype and "text" not in ctype:
        raise ApiError(400, "Alamat bukan halaman teks atau HTML.")
    title, text = html_to_text(response.content)
    text = _clean(text, "Halaman tidak berisi teks yang bisa dibaca.")
    final = str(response.url)
    return {"title": title or parsed.hostname, "text": text, "url": final}
