"""Product photos: extract the main image from public colorbox.co.id pages, attach the 10 local photos, and serve them.
Photos live in `product_images` keyed by product url, so catalog.sync() (which reloads `products`) never loses them.
CLI (resumable, safe to re-run): `uv run python -m bff.product_images fetch [--limit N]` and `... local`."""
import argparse
import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.robotparser import RobotFileParser

import httpx

from . import catalog, db

IMAGES_DIR = Path(__file__).resolve().parent.parent / "assets" / "product-images"
LOCAL_PREFIX = "/api/product-images/"
SHOP = "https://colorbox.co.id"
UA = "Mozilla/5.0 (compatible; catalog-image-sync/1.0)"
DELAY = 0.6  # seconds between requests; one request at a time
_ALLOWED_HOSTS = ("https://cdn.shopify.com/", SHOP + "/")
_FILE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.jpg$")
_OG = re.compile(r"""<meta\s[^>]*?property=["']og:image(?::secure_url)?["'][^>]*?content=["']([^"']+)["']""", re.I)
_OG_REV = re.compile(r"""<meta\s[^>]*?content=["']([^"']+)["'][^>]*?property=["']og:image["']""", re.I)

# Ivanagita's 10 photos (product-images-gallery.md): product url slug -> local file.
LOCAL = {
    "contrast-stitch-chambray-shirt-dark-blue-26c": "cbx-01-contrast-stitch-chambray-shirt.jpg",
    "high-waist-barrel-denim-pants-black-26g-1": "cbx-02-high-waist-barrel-denim-black.jpg",
    "basic-barrel-denim-pants-dark-brown-26g-1": "cbx-03-basic-barrel-denim-dark-brown.jpg",
    "straight-denim-pants-dark-brown-26h-1": "cbx-04-straight-denim-pants-dark-brown.jpg",
    "double-pocket-flared-denim-pants-lt-grey-26c": "cbx-05-double-pocket-flared-denim-grey.jpg",
    "regular-fit-tailored-mini-skort-lt-grey-26e": "cbx-06-regular-fit-tailored-mini-skort-grey.jpg",
    "pleated-a-line-skirt-off-white-26c": "cbx-07-pleated-a-line-skirt-off-white.jpg",
    "embroidered-sleeveless-mini-dress-navy-26d": "cbx-08-embroidered-sleeveless-mini-dress-navy.jpg",
    "side-ruched-sleeveless-mini-dress-navy-26d": "cbx-09-side-ruched-sleeveless-mini-dress-navy.jpg",
    "colorbox-x-liunic-tote-bag-ecru-26e": "cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg",
}


def safe_image_path(name: str) -> Path | None:
    """Path of a bundled photo, or None for anything that is not a plain existing .jpg name inside IMAGES_DIR."""
    if not _FILE.match(name or ""):
        return None
    p = (IMAGES_DIR / name).resolve()
    return p if p.parent == IMAGES_DIR.resolve() and p.is_file() else None


def _clean(u: str | None) -> str | None:
    if not u:
        return None
    u = u.strip().replace("&amp;", "&")
    if u.startswith("//"):
        u = "https:" + u
    return u if u.startswith(_ALLOWED_HOSTS) else None  # only public Shopify/Colorbox https urls are stored


def image_from_js(text: str) -> str | None:
    """Main image from the Shopify product `.js` endpoint (featured_image, else first of images)."""
    try:
        d = json.loads(text)
    except ValueError:
        return None
    if not isinstance(d, dict):
        return None
    imgs = d.get("images")
    first = imgs[0] if isinstance(imgs, list) and imgs else None
    return _clean(d.get("featured_image") if isinstance(d.get("featured_image"), str) else first if isinstance(first, str) else None)


def image_from_html(html: str) -> str | None:
    """Fallback: the og:image meta tag of the product page."""
    m = _OG.search(html) or _OG_REV.search(html)
    return _clean(m.group(1)) if m else None


def local_rows() -> list[tuple[str, str]]:
    """(product url, image_url) for each bundled photo whose file exists."""
    return [(f"{SHOP}/products/{slug}", LOCAL_PREFIX + f) for slug, f in LOCAL.items() if safe_image_path(f)]


async def attach_local() -> int:
    rows = local_rows()
    for url, img in rows:  # local photos overwrite a CDN url for the same product
        await db.ex("insert into product_images (url, image_url, image_source) values (%s, %s, 'local') "
                    "on conflict (url) do update set image_url = excluded.image_url, image_source = 'local', image_fetched_at = now()",
                    url, img)
    return len(rows)


async def _get(client: httpx.AsyncClient, url: str, tries: int = 3) -> httpx.Response | None:
    for i in range(tries):
        await asyncio.sleep(DELAY * (2 ** i))
        try:
            r = await client.get(url)
        except httpx.HTTPError:
            continue
        if r.status_code == 404:
            return None
        if r.status_code == 200:
            return r
    return None


async def fetch_all(limit: int | None = None) -> dict:
    """Fetch the main image for catalog products that have none yet (resumable). Returns counts."""
    todo = await db.q("select p.url from products p left join product_images i on i.url = p.url where i.url is null order by p.id")
    if limit:
        todo = todo[:limit]
    ok = failed = 0
    async with httpx.AsyncClient(headers={"User-Agent": UA}, timeout=20, follow_redirects=True) as client:
        robots = RobotFileParser()
        r = await client.get(SHOP + "/robots.txt")
        robots.parse(r.text.splitlines() if r.status_code == 200 else [])
        for row in todo:
            url = row["url"]
            if not robots.can_fetch(UA, url):
                failed += 1
                continue
            img = None
            if (resp := await _get(client, url + ".js")):
                img = image_from_js(resp.text)
            if not img and (resp := await _get(client, url)):
                img = image_from_html(resp.text)
            if img:
                await db.ex("insert into product_images (url, image_url, image_source) values (%s, %s, 'colorbox.co.id') "
                            "on conflict (url) do nothing", url, img)
                ok += 1
            else:
                failed += 1
            if (ok + failed) % 50 == 0:
                print(f"{ok + failed}/{len(todo)} ok={ok} gagal={failed}", file=sys.stderr, flush=True)
    return {"diproses": ok + failed, "berhasil": ok, "gagal": failed}


async def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["fetch", "local"])
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    await db.open_pool()
    try:
        await catalog.sync()
        if a.cmd == "local":
            print({"foto_lokal": await attach_local()})
        else:
            print(await fetch_all(a.limit))
            print({"foto_lokal": await attach_local()})
    finally:
        await db.close_pool()


if __name__ == "__main__":
    asyncio.run(_main(), loop_factory=asyncio.SelectorEventLoop)  # psycopg async cannot use the Windows default loop
