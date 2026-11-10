from bff import catalog


def rows():
    return catalog.parse_catalog(catalog.CATALOG_FILE.read_text(encoding="utf-8"))


def test_parser_gives_1206_rows_with_categories_and_prices():
    r = rows()
    assert len(r) == 1206
    assert all(x["category"] and x["name"] and x["price"] > 0 and x["url"].startswith("https://") for x in r)
    assert min(x["price"] for x in r) == 19950 and max(x["price"] for x in r) == 379900
    cats = {x["category"] for x in r}
    assert "Tops (Atasan)" in cats and len(cats) == 9


def test_first_row_and_discount_row():
    r = rows()
    assert r[0] == {"category": "Tops (Atasan)", "name": "Regular Fit Short Sleeve Graphic T-Shirt", "price": 79900,
                    "price_original": None, "colors": ["DARK BROWN"], "sizes": ["L", "M", "S", "XL"],
                    "url": "https://colorbox.co.id/products/regular-fit-short-sleeve-graphic-t-shirt-dark-brown-26i-1"}
    d = next(x for x in r if x["url"].endswith("/contrast-rib-short-sleeve-crop-t-shirt-ecru-26i"))
    assert d["price"] == 95900 and d["price_original"] == 99900
    assert any(len(x["colors"]) > 1 for x in r)


def test_category_counts_match_the_catalog_summary():
    counts = {}
    for x in rows():
        counts[x["category"]] = counts.get(x["category"], 0) + 1
    assert counts["Tops (Atasan)"] == 567 and counts["Aksesoris & Tas"] == 1


def test_tsquery_is_safe_and_drops_filler():
    assert catalog._tsquery("Halo kak, graphic t-shirt; drop table!") == "graphic | shirt | drop | table"
    assert catalog._tsquery("halo kak ya") is None


def test_build_search_filters_and_param_order():
    sql, params = catalog.build_search("graphic", "tops", 100000, "pink", "m", limit=50)
    assert sql.count("%s") == len(params)
    assert params == ["graphic", "graphic", "%tops%", 100000, "%pink%", "m", 20]  # limit capped at 20
    assert "search @@ to_tsquery" in sql and "price <= %s" in sql and "= any(sizes)" in sql


def test_build_search_without_text_and_filler_only():
    sql, params = catalog.build_search(None, max_price=50000)
    assert "to_tsquery" not in sql and params == [50000, 5]
    sql, _ = catalog.build_search("halo kak")
    assert "where false" in sql
