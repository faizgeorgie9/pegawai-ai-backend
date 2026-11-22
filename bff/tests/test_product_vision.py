import pytest
from test_scheduler import with_db

from bff import catalog, knowledge, product_images as pi, product_vision as pv

P = {"name": "Pleated A-Line Skirt", "category": "Bottoms", "price": 209930, "price_original": 299900, "colors": ["OFF WHITE"],
     "sizes": ["S"], "url": "https://colorbox.co.id/products/x", "accessed_date": "2026-11-09"}


def test_product_lines_include_photo_and_trimmed_description_only_when_present():
    plain = knowledge._product_lines([P])
    assert "foto:" not in plain and "bentuk" not in plain
    rich = knowledge._product_lines([{**P, "image_url": "/api/product-images/a.jpg", "image_description": "x" * 1000}])
    assert "foto: /api/product-images/a.jpg" in rich and "bentuk (dari foto resmi): " + "x" * knowledge.DESC_MAX in rich
    assert "x" * (knowledge.DESC_MAX + 1) not in rich


def test_product_note_forbids_inventing_shape():
    assert "foto resmi" in knowledge.PRODUCT_NOTE and "jangan mengarang" in knowledge.PRODUCT_NOTE


def test_local_photo_becomes_data_uri_and_cdn_url_passes_through(monkeypatch):
    assert pv._image_ref(pi.LOCAL_PREFIX + "cbx-07-pleated-a-line-skirt-off-white.jpg").startswith("data:image/jpeg;base64,/9j/")
    assert pv._image_ref("https://cdn.shopify.com/a.jpg") == "https://cdn.shopify.com/a.jpg"
    with pytest.raises(ValueError):
        pv._image_ref(pi.LOCAL_PREFIX + "../x.jpg")


@with_db
async def test_describe_is_idempotent_respects_limit_and_dry_run(db):
    await db.ex("delete from knowledge_meta where key = %s", catalog.META_KEY)
    await catalog.sync()
    await pi.attach_local()
    await db.ex("update product_images set image_description = null, described_at = null, describer_model = null")
    calls = []

    async def fake(ref, name, bot):
        calls.append(name)
        return f"deskripsi {name}", "fake-model"

    dry = await pv.describe_all(dry_run=True)
    assert dry["akan_diproses"] >= 10 and not calls
    first = await pv.describe_all(limit=3, describer=fake)
    assert first["berhasil"] == 3 and len(calls) == 3
    rest = await pv.describe_all(limit=1000, describer=fake)
    again = await pv.describe_all(describer=fake)
    assert again == {"diproses": 0, "berhasil": 0, "gagal": 0} and len(calls) == 3 + rest["berhasil"]
    row = await db.q1("select image_description, describer_model, described_at from product_images where url like %s",
                      "%pleated-a-line-skirt-off-white-26c")
    assert row["image_description"] == "deskripsi Pleated A-Line Skirt" and row["describer_model"] == "fake-model" and row["described_at"]
    hit = [r for r in await catalog.search_products("pleated skirt", limit=20) if r["name"] == "Pleated A-Line Skirt"][0]
    assert hit["image_description"].startswith("deskripsi")


@with_db
async def test_failed_photo_does_not_stop_batch_or_store_anything(db):
    await db.ex("update product_images set image_description = null, described_at = null, describer_model = null")

    async def boom(ref, name, bot):
        raise RuntimeError("Hermes menjawab 500")

    res = await pv.describe_all(limit=2, describer=boom)
    assert res == {"diproses": 2, "berhasil": 0, "gagal": 2}
    assert not await db.q1("select 1 from product_images where image_description is not null")
