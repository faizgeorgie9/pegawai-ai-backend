"""Product catalog: parse product-catalog.md into Postgres and search it (structured filters + text search)."""
import hashlib
import re
from datetime import date

from . import db
from .knowledge import COLORBOX_DIR

CATALOG_FILE = COLORBOX_DIR / "product-catalog.md"
SOURCE, ACCESSED = "SRC-02", date(2026, 11, 9)
META_KEY = "product-catalog.sha256"

_CATEGORY = re.compile(r"^##\s+\d+\.\s+(.+?)\s+\(\d+\s+Produk\)\s*$")
_ROW = re.compile(r"^\|\s*\d+\s*\|(.+)\|\s*$")
_RP = re.compile(r"Rp\s*([\d.]+)")
_ORIG = re.compile(r"~~\s*Rp\s*([\d.]+)\s*~~")
_URL = re.compile(r"\]\((https?://[^)\s]+)\)")
# Words that carry no product meaning; the rest of a customer message is matched against the catalog text.
_STOP = {"the", "and", "for", "with", "yang", "dan", "atau", "ada", "itu", "ini", "apa", "apakah", "saya", "aku", "mau",
         "bisa", "kak", "min", "halo", "hai", "tapi", "kalau", "untuk", "dari", "yg", "di", "ke", "nya", "stok", "harga",
         "ukuran", "warna", "masih", "berapa", "ya"}


def _rupiah(s: str) -> int:
    return int(s.replace(".", ""))


def parse_catalog(text: str) -> list[dict]:
    """Rows of every markdown table; a `## n. Category (N Produk)` heading gives the category of the rows below it."""
    rows, category = [], None
    for line in text.splitlines():
        m = _CATEGORY.match(line)
        if m:
            category = m.group(1)
            continue
        m = _ROW.match(line)
        if not m or category is None:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if len(cells) != 5:
            continue  # shortcut: a malformed row is skipped; the 1,206 row-count test catches it, add a loud error if it ever matters
        name, price_cell, colors, sizes, link = cells
        p, url = _RP.search(price_cell), _URL.search(link)
        if not p or not url:
            continue
        orig = _ORIG.search(price_cell)
        rows.append({"category": category, "name": name, "price": _rupiah(p.group(1)),
                     "price_original": _rupiah(orig.group(1)) if orig else None,
                     "colors": [c.strip() for c in colors.split(",") if c.strip()],
                     "sizes": [s.strip() for s in sizes.split(",") if s.strip()], "url": url.group(1)})
    return rows


def file_hash() -> str:
    return hashlib.sha256(CATALOG_FILE.read_bytes()).hexdigest()


async def sync() -> int:
    """Load the catalog into `products` when the file hash changed (or the table is empty). Returns the row count."""
    digest = file_hash()
    stored = await db.q1("select value from knowledge_meta where key = %s", META_KEY)
    count = (await db.q1("select count(*)::int as n from products"))["n"]
    if stored and stored["value"] == digest and count:
        return count
    rows = parse_catalog(CATALOG_FILE.read_text(encoding="utf-8"))
    async with db.pool.connection() as c:
        async with c.transaction():
            await c.execute("delete from products")
            async with c.cursor() as cur:
                await cur.executemany(
                    "insert into products (category, name, price, price_original, colors, sizes, url, source, accessed_date, search) "
                    "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, to_tsvector('simple', %s))",
                    [(r["category"], r["name"], r["price"], r["price_original"], r["colors"], r["sizes"], r["url"],
                      SOURCE, ACCESSED, " ".join([r["name"], r["category"], *r["colors"]])) for r in rows])
            await c.execute("insert into knowledge_meta (key, value) values (%s, %s) "
                            "on conflict (key) do update set value = excluded.value, updated_at = now()", (META_KEY, digest))
    return len(rows)


def _tsquery(text: str) -> str | None:
    """OR of the meaningful words (letters and digits only, so the string is safe for to_tsquery)."""
    words = dict.fromkeys(w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 3 and w not in _STOP)
    return " | ".join(list(words)[:40]) or None


def build_search(query: str | None, category: str | None = None, max_price: int | None = None,
                 color: str | None = None, size: str | None = None, limit: int = 5) -> tuple[str, list]:
    cols = "id, category, name, price, price_original, colors, sizes, url, source, accessed_date"
    where, params, rank = [], [], "0"
    tsq = _tsquery(query) if query else None
    if query and query.strip() and not tsq:
        where.append("false")  # a query made only of filler words matches nothing
    if tsq:
        where.append("search @@ to_tsquery('simple', %s)")
        rank = "ts_rank(search, to_tsquery('simple', %s))"
        params = [tsq]
    if category:
        where.append("category ilike %s")
        params.append(f"%{category}%")
    if max_price is not None:
        where.append("price <= %s")
        params.append(max_price)
    if color:
        where.append("exists (select 1 from unnest(colors) c where c ilike %s)")
        params.append(f"%{color}%")
    if size:
        where.append("upper(%s) = any(sizes)")
        params.append(size.strip())
    sql = f"select {cols}, {rank} as rank from products"
    if tsq:
        params = [tsq] + params  # the rank placeholder comes first in the select list
    if where:
        sql += " where " + " and ".join(where)
    sql += " order by rank desc, price, id limit %s"
    params.append(max(1, min(limit, 20)))
    return sql, params


async def search_products(query: str | None = None, category: str | None = None, max_price: int | None = None,
                          color: str | None = None, size: str | None = None, limit: int = 5) -> list[dict]:
    sql, params = build_search(query, category, max_price, color, size, limit)
    rows = await db.q(sql, *params)
    for r in rows:
        r.pop("rank", None)
        r["accessed_date"] = r["accessed_date"].isoformat()
    return rows
