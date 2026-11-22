import json

import pytest
from test_scheduler import with_db

from bff import catalog, product_images as pi

CDN = "https://cdn.shopify.com/s/files/1/0001/products/a.jpg?v=1"


def test_image_from_js_prefers_featured_and_fixes_protocol_relative_urls():
    assert pi.image_from_js(json.dumps({"featured_image": "//cdn.shopify.com/s/a.jpg", "images": ["//cdn.shopify.com/s/b.jpg"]})) == "https://cdn.shopify.com/s/a.jpg"
    assert pi.image_from_js(json.dumps({"images": [CDN]})) == CDN


def test_image_from_js_rejects_bad_input_and_foreign_hosts():
    assert pi.image_from_js("not json") is None
    assert pi.image_from_js("[]") is None
    assert pi.image_from_js(json.dumps({"featured_image": "https://evil.example/x.jpg"})) is None
    assert pi.image_from_js(json.dumps({"featured_image": "javascript:alert(1)"})) is None


def test_image_from_html_reads_og_image_in_either_attribute_order():
    a = f'<head><meta property="og:image" content="{CDN.replace("&", "&amp;")}"></head>'
    b = f'<meta content="{CDN}" property="og:image" />'
    assert pi.image_from_html(a) == CDN and pi.image_from_html(b) == CDN
    assert pi.image_from_html("<html></html>") is None


@pytest.mark.parametrize("name", ["../main.py", "..%2fmain.py", "a/b.jpg", "a\b.jpg", ".env", "x.png", "", "nope.jpg", "cbx-01.jpg\x00.png"])
def test_safe_image_path_blocks_traversal_and_unknown_files(name):
    assert pi.safe_image_path(name) is None


def test_bundled_photos_exist_and_match_catalog_urls():
    urls = {r["url"] for r in catalog.parse_catalog(catalog.CATALOG_FILE.read_text(encoding="utf-8"))}
    rows = pi.local_rows()
    assert len(rows) == 10
    assert all(u in urls for u, _ in rows)
    assert all(i.startswith(pi.LOCAL_PREFIX) and pi.safe_image_path(i.removeprefix(pi.LOCAL_PREFIX)) for _, i in rows)


@with_db
async def test_sync_keeps_photos_and_search_returns_image_url(db):
    await db.ex("delete from products")
    await db.ex("delete from knowledge_meta where key = %s", catalog.META_KEY)
    await catalog.sync()
    assert await pi.attach_local() == 10
    await db.ex("insert into product_images (url, image_url, image_source) values (%s, %s, 'colorbox.co.id') on conflict do nothing",
                catalog.parse_catalog(catalog.CATALOG_FILE.read_text(encoding="utf-8"))[0]["url"], CDN)
    await db.ex("delete from knowledge_meta where key = %s", catalog.META_KEY)  # force a reload
    assert await catalog.sync() == 1206
    rows = await catalog.search_products("chambray", limit=20)
    hit = next(r for r in rows if r["name"] == "Contrast Stitch Chambray Shirt")
    assert hit["image_url"] == pi.LOCAL_PREFIX + "cbx-01-contrast-stitch-chambray-shirt.jpg"
    first = (await catalog.search_products("graphic short sleeve regular fit", limit=20))
    assert any(r["image_url"] == CDN for r in first)
    assert (await catalog.search_products(category="Denim", limit=1))[0].keys() >= {"image_url"}


def test_image_route_serves_local_photo_and_404s_others():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from bff.main import public
    app = FastAPI()
    app.include_router(public)
    c = TestClient(app)
    r = c.get("/api/product-images/cbx-01-contrast-stitch-chambray-shirt.jpg")
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg" and r.content[:3] == b"\xff\xd8\xff"
    assert c.get("/api/product-images/..%2fmain.py").status_code in (404, 422)
