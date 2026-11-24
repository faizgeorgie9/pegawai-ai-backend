import asyncio
import json

from bff import config, engine
from bff.retrieval import (
    catalog_products,
    product_recommendation_guidance,
    recommendation_context,
    retrieve_products,
    size_matching_context,
)


def product(product_id, title, *, category="tops", color="WHITE", price=150000, sizes=None, details=""):
    return {
        "product_id": product_id,
        "title": title,
        "details": details,
        "colorway": color,
        "price_idr": price,
        "sizes_listed": sizes or ["S", "M", "L"],
        "sizes_available_online": ["S"],
        "url": f"https://colorbox.co.id/products/{product_id}",
        "_category_id": category,
    }


def write_knowledge(tmp_path, monkeypatch, products):
    catalogue = {
        "captured_on": "2026-11-12",
        "categories": [
            {"id": category, "products": items}
            for category, items in products.items()
        ],
    }
    chart = {
        "chart_id": "CB-SIZE-GUIDE-001",
        "captured_on": "2026-11-12",
        "source_url": "https://colorbox.co.id/pages/size-guide",
        "image_url": "https://colorbox.co.id/size-guide.png",
        "alpha_sizes": {
            "measurement_basis": "body",
            "units": "cm",
            "sizes": [
                {"size": "S", "bust": [82, 86], "waist": [64, 68], "hip": [92, 96], "inseam_cm": 69},
                {"size": "M", "bust": [86, 90], "waist": [68, 72], "hip": [96, 100], "inseam_cm": 69},
                {"size": "L", "bust": [90, 94], "waist": [72, 76], "hip": [100, 104], "inseam_cm": 69},
            ]
        },
        "denim_sizes": {"sizes": [{"size": "27", "waist_cm": 69.5, "hip_cm": 93.5}]},
    }
    (tmp_path / "colorbox_product_catalogue_snapshot_2026-11-12.json").write_text(
        json.dumps(catalogue), encoding="utf-8"
    )
    (tmp_path / "colorbox_size_chart_snapshot_2026-11-12.json").write_text(
        json.dumps(chart), encoding="utf-8"
    )
    (tmp_path / "sop_colorbox_product_recommendation_v1.md").write_text(
        "Rekomendasikan dulu, lalu ajukan satu pertanyaan opsional.", encoding="utf-8"
    )
    monkeypatch.setattr(config, "CS_SOPS_DIR", tmp_path)
    monkeypatch.setattr(config, "CS_KNOWLEDGE_DIR", tmp_path)


def test_retrieval_uses_category_color_and_budget():
    white_top = product(1, "Basic Knit Top")
    black_top = product(2, "Basic Knit Top", color="BLACK", price=250000)
    dress = product(3, "Printed Mini Dress", category="dresses")
    catalogue = {
        "categories": [
            {"id": "tops", "products": [white_top, black_top]},
            {"id": "dresses", "products": [dress]},
        ]
    }

    results = retrieve_products("recommend a white top under Rp 200.000", catalogue)

    assert [item["product_id"] for item in results] == [1]


def test_product_queries_get_direct_first_guidance_and_other_queries_do_not():
    guidance = product_recommendation_guidance("Recommend a T-shirt for work")

    assert guidance.startswith("## Panduan respons rekomendasi produk\n")
    assert "Recommend up to three matching options immediately" in guidance
    assert "the first sentence of the reply is a recommendation or a shortlist" in guidance
    assert "Never open with a questionnaire" in guidance
    assert "Do not volunteer size-chart or fit limitations" in guidance
    assert product_recommendation_guidance("How do I return my order?") is None


def test_context_injects_unique_chart_match_and_snapshot_limits(tmp_path, monkeypatch):
    item = product(1, "Basic Knit Top", details="Sleeveless top; cotton.")
    write_knowledge(tmp_path, monkeypatch, {"tops": [item]})

    context = recommendation_context("size Basic Knit Top, bust 88 cm")

    assert "CB-PRODUCT-1" in context
    assert "CB-SIZE-GUIDE-001" in context
    assert "Ukuran chart yang cocok: M" in context
    assert "bukan feed live" in context
    assert "stok saat ini" in context
    assert "sizes_available_online" not in context


def test_boundary_measurement_is_not_forced_into_one_size(tmp_path, monkeypatch):
    item = product(1, "Basic Knit Top")
    write_knowledge(tmp_path, monkeypatch, {"tops": [item]})

    context = recommendation_context("ukuran Basic Knit Top, lingkar dada 86 cm")

    assert "Hasil ambigu pada batas chart: S, M" in context
    assert "jangan pilih satu" in context.lower()


def test_missing_measurement_units_require_confirmation(tmp_path, monkeypatch):
    item = product(1, "Basic Knit Top")
    write_knowledge(tmp_path, monkeypatch, {"tops": [item]})

    context = recommendation_context("size Basic Knit Top, bust 88")

    assert "Satuan pengukuran belum dipastikan cm" in context


def test_weight_does_not_replace_required_body_measurement(tmp_path, monkeypatch):
    item = product(1, "Basic Knit Top")
    write_knowledge(tmp_path, monkeypatch, {"tops": [item]})

    context = recommendation_context("ukuran Basic Knit Top, berat saya 55 kg")

    assert "jangan menyimpulkan dari berat atau tinggi" in context
    assert "lingkar dada" in context


def test_denim_and_bra_sizes_are_not_guessed(tmp_path, monkeypatch):
    jeans = product(2, "Regular Fit Jeans", category="bottoms", sizes=["26", "27", "28"])
    bra_top = product(3, "Square Neck Bra Top", category="tops")
    write_knowledge(tmp_path, monkeypatch, {"bottoms": [jeans], "tops": [bra_top]})

    denim_context = recommendation_context(
        "size Regular Fit Jeans, waist 70 cm, hip 94 cm"
    )
    bra_context = recommendation_context("size Square Neck Bra Top, bust 88 cm")

    assert "dasar pengukuran tabel denim belum jelas" in denim_context
    assert "Produk intim tidak memiliki chart khusus" in bra_context


def test_non_product_questions_do_not_load_catalogue(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CS_KNOWLEDGE_DIR", tmp_path)

    assert recommendation_context("Terima kasih, ada pertanyaan tentang pesanan saya") is None


def test_checked_in_catalogue_and_chart_match_a_real_product(monkeypatch):
    monkeypatch.setattr(
        config,
        "CS_KNOWLEDGE_DIR",
        config.ROOT.parent / "local_setup" / "backend_template" / "context" / "knowledge",
    )

    context = recommendation_context(
        "size Long Sleeve Stripes Embroidery Shirt, bust 88 cm"
    )

    assert "CB-PRODUCT-10445658259714" in context
    assert "Ukuran chart yang cocok: M" in context
    assert context.count("- Sumber CB-PRODUCT-") == 1


def test_workflow_size_matching_uses_database_products_and_adds_source_reference(tmp_path, monkeypatch):
    write_knowledge(tmp_path, monkeypatch, {})
    products = [{
        "id": 42,
        "name": "Basic Knit Top",
        "category": "Tops (Atasan)",
        "sizes": ["S", "M", "L"],
    }]

    context, reference = size_matching_context("size Basic Knit Top, bust 88 cm", products)

    assert "CB-SIZE-GUIDE-001" in context
    assert "Ukuran chart yang cocok: M" in context
    assert "menggantikan catatan lama CB-SIZE-UNKNOWN-001" in context
    assert reference == {
        "type": "knowledge",
        "id": "CB-SIZE-GUIDE-001",
        "title": "Verified Colorbox size guide",
        "classification": "Public Data",
        "source_id": "SRC-05",
        "url": "https://colorbox.co.id/pages/size-guide",
        "accessed_date": "2026-11-12",
    }


def test_workflow_size_matching_keeps_denim_and_boundary_results_ambiguous(tmp_path, monkeypatch):
    write_knowledge(tmp_path, monkeypatch, {})
    denim = [{"id": 7, "name": "Straight Jeans", "category": "Bottoms (Bawahan)", "sizes": ["26", "27"]}]
    boundary = [{"id": 8, "name": "Knit Top", "category": "Tops (Atasan)", "sizes": ["S", "M"]}]

    denim_context, _ = size_matching_context("ukuran jeans waist 70 cm hip 94 cm", denim)
    boundary_context, _ = size_matching_context("ukuran knit top bust 86 cm", boundary)

    assert "dasar pengukuran tabel denim belum jelas" in denim_context
    assert "Hasil ambigu pada batas chart: S, M" in boundary_context


def test_cs_workflow_context_injects_size_matching_and_audit_reference(tmp_path, monkeypatch):
    write_knowledge(tmp_path, monkeypatch, {})
    products = [{"id": 42, "name": "Basic Knit Top", "category": "Tops (Atasan)", "sizes": ["S", "M", "L"]}]

    async def search_products(query, limit):
        return products

    monkeypatch.setattr(engine.catalog, "search_products", search_products)
    monkeypatch.setattr(
        engine.knowledge,
        "build_context",
        lambda *args: ("CS instructions", [], {"workflow": "cs"}),
    )

    instructions, context = asyncio.run(
        engine.workflow_context(
            {"team": "customer_support"},
            "cs",
            None,
            False,
            "size Basic Knit Top, bust 88 cm",
            None,
        )
    )

    assert "Ukuran chart yang cocok: M" in instructions
    assert "Rekomendasikan dulu, lalu ajukan satu pertanyaan opsional." in instructions
    assert context["context_refs"] == [{
        "type": "knowledge",
        "id": "CB-SIZE-GUIDE-001",
        "title": "Verified Colorbox size guide",
        "classification": "Public Data",
        "source_id": "SRC-05",
        "url": "https://colorbox.co.id/pages/size-guide",
        "accessed_date": "2026-11-12",
    }]


def test_cs_test_workflow_injects_demo_stock_with_simulation_reference(tmp_path, monkeypatch):
    write_knowledge(tmp_path, monkeypatch, {})

    async def search_products(query, limit):
        return []

    async def connection(user_id, kind):
        assert (user_id, kind) == ("default", "stock")
        return {"id": "stock-connection", "url": "https://docs.google.com/spreadsheets/d/demo/edit"}

    async def read_table(_connection):
        from bff.sheets import csv_table

        return csv_table("SKU,Nama,Stok\nA-1,Leather Jacket,4\n")

    async def context_for(user_id, query, scope):
        return "", []

    monkeypatch.setattr(engine.catalog, "search_products", search_products)
    monkeypatch.setattr(engine.knowledge, "build_context",
                        lambda *args: ("CS instructions", [], {"workflow": "cs"}))
    monkeypatch.setattr(engine.sheets, "connection", connection)
    monkeypatch.setattr(engine.sheets, "read_table", read_table)
    monkeypatch.setattr(engine.kb, "context_for", context_for)

    instructions, context = asyncio.run(engine.workflow_context(
        {"team": "customer_support", "user_id": "default"},
        "cs",
        None,
        True,
        "Is Leather Jacket masih ada stok?",
        None,
    ))

    assert "Demo stock lookup (simulated)" in instructions
    assert "SKU: A-1 | Nama: Leather Jacket | Stok: 4" in instructions
    reference = context["context_refs"][0]
    assert {key: value for key, value in reference.items() if key != "accessed_date"} == {
        "type": "spreadsheet",
        "id": "stock-connection",
        "title": "Demo stock spreadsheet",
        "classification": "Simulated Data",
        "source_id": None,
        "url": "https://docs.google.com/spreadsheets/d/demo/edit",
    }
    assert len(reference["accessed_date"]) == 10


def test_plural_and_typo_queries_still_reach_the_category():
    shirt = product(1, "Long Sleeve Shirt", details="Cotton shirt.")
    jacket = product(2, "Denim Jacket")
    catalogue = {"captured_on": "2026-11-12", "categories": [{"id": "tops", "products": [shirt, jacket]}]}

    for query in ("recommend me shirts to buy", "recommend me shirst to buy"):
        results = retrieve_products(query, catalogue)
        assert results[0]["product_id"] == 1


def test_local_catalog_products_use_the_database_product_shape():
    item = product(1, "Long Sleeve Shirt", details="Cotton shirt.", color="WHITE")
    catalogue = {"captured_on": "2026-11-12", "categories": [{"id": "tops", "products": [item]}]}

    [record] = catalog_products("recommend a shirt", catalogue=catalogue)

    assert record["id"] == "1"
    assert record["name"] == "Long Sleeve Shirt"
    assert record["category"] == "Tops (Atasan)"
    assert record["price"] == 150000
    assert record["colors"] == ["WHITE"]
    assert record["sizes"] == ["S", "M", "L"]
    assert record["details"] == "Cotton shirt."
    assert record["source"] == "SRC-02"
    assert record["accessed_date"] == "2026-11-12"


def test_merge_puts_curated_items_first_for_browsing_and_db_hit_first_for_a_named_product():
    curated = [{"name": "Curated Knit Top", "id": "c1", "price": 1, "price_original": None,
                "colors": [], "sizes": [], "url": "u", "source": "SRC-02", "accessed_date": None}]
    named = [{"name": "Exact Shirt", "id": "d1", "price": 2, "price_original": None,
              "colors": [], "sizes": [], "url": "u", "source": "SRC-02", "accessed_date": None}]

    def fake_catalog_products(text, limit=5):
        return list(curated)

    original = engine.retrieval.catalog_products
    engine.retrieval.catalog_products = fake_catalog_products
    try:
        browse = engine._merge_local_products("recommend a top", named)
        named_hit = engine._merge_local_products("I want Exact Shirt", named)
    finally:
        engine.retrieval.catalog_products = original

    assert [p["name"] for p in browse][:2] == ["Curated Knit Top", "Exact Shirt"]
    assert [p["name"] for p in named_hit][:2] == ["Exact Shirt", "Curated Knit Top"]


def test_uploaded_knowledge_is_appended_after_official_evidence(tmp_path, monkeypatch):
    write_knowledge(tmp_path, monkeypatch, {})

    async def search_products(query, limit):
        return []

    async def context_for(user_id, query, scope):
        assert (user_id, scope) == ("default", "cs")
        return "## Dokumen pengetahuan tambahan (unggahan)\nRetur 14 hari.", [
            {"type": "knowledge", "id": "KB-abcdef12", "title": "Kebijakan retur"}
        ]

    monkeypatch.setattr(engine.catalog, "search_products", search_products)
    monkeypatch.setattr(engine.knowledge, "build_context",
                        lambda *args: ("CS instructions", [], {"workflow": "cs"}))
    monkeypatch.setattr(engine.kb, "context_for", context_for)

    instructions, context = asyncio.run(engine.workflow_context(
        {"team": "customer_support", "user_id": "default"}, "cs", None, False, "boleh retur?", None))

    assert instructions.startswith("CS instructions") and instructions.endswith("Retur 14 hari.")
    assert context["context_refs"] == [{"type": "knowledge", "id": "KB-abcdef12", "title": "Kebijakan retur"}]
