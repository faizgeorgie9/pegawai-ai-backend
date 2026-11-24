"""Local, deterministic retrieval for Siti's approved Colorbox product and size data."""

from __future__ import annotations

import difflib
import json
import re
import unicodedata
from typing import Any

from . import config
from .errors import ApiError

CATALOGUE_FILE = "colorbox_product_catalogue_snapshot_2026-11-12.json"
SIZE_CHART_FILE = "colorbox_size_chart_snapshot_2026-11-12.json"
PRODUCT_SOP_FILE = "sop_colorbox_product_recommendation_v1.md"

_CATEGORY_PHRASES = {
    "tops": ("top", "tops", "baju", "atasan", "shirt", "shirts", "blouse", "blouses", "kaos", "kemeja"),
    "dresses": ("dress", "dresses", "gaun"),
    "bottoms": ("bottom", "bawahan", "celana", "rok", "jeans", "pants", "skirt", "skirts", "skort", "trousers", "shorts"),
    "outerwear": ("outerwear", "outer", "jaket", "jacket", "jackets", "blazer", "hoodie", "sweater", "sweaters", "cardigan", "cardigans"),
    "sleepwear": ("sleepwear", "piyama", "pajama", "pajamas"),
    "underwear": ("underwear", "bra", "panty", "bralette", "brallete"),
    "accessories": ("accessories", "aksesoris", "tas", "bag", "bags", "sepatu", "shoes", "flatshoes", "belt", "belts", "sabuk", "topi", "cap"),
}
_PRODUCT_INTENT = {
    "recommend", "recommendation", "rekomendasi", "rekomendasikan", "saran", "cari", "mencari",
    "produk", "product", "harga", "price", "warna", "color", "bandingkan", "compare",
}
_SIZE_INTENT = {
    "size", "ukuran", "fit", "muat", "pas", "lingkar", "dada", "pinggang", "pinggul", "panggul",
    "bust", "chest", "waist", "hip", "inseam", "cm",
}
_STOP_WORDS = {
    "aku", "saya", "mau", "ingin", "butuh", "untuk", "yang", "dan", "atau", "dengan", "di",
    "ke", "ini", "itu", "ada", "apakah", "bisa", "tolong", "dong", "please", "the", "a", "an",
    "for", "and", "or", "with", "some", "recommend", "recommendation", "rekomendasi",
    "rekomendasikan", "saran", "cari", "mencari", "produk", "product", "harga", "price",
    "warna", "color", "size", "ukuran", "fit", "muat", "pas", "di", "under", "below", "max",
    "maks", "maksimal", "budget", "budgetnya", "rp", "ribu", "rb", "k",
}
_MEASUREMENT_PATTERNS = {
    "bust": re.compile(r"(?:lingkar\s+dada|dada|bust|chest)\s*(?:saya)?\s*[:=]?\s*(\d{2,3}(?:[.,]\d+)?)\s*(cm)?\b", re.I),
    "waist": re.compile(r"(?:lingkar\s+pinggang|pinggang|waist)\s*(?:saya)?\s*[:=]?\s*(\d{2,3}(?:[.,]\d+)?)\s*(cm)?\b", re.I),
    "hip": re.compile(r"(?:lingkar\s+(?:pinggul|panggul)|pinggul|panggul|hip)\s*(?:saya)?\s*[:=]?\s*(\d{2,3}(?:[.,]\d+)?)\s*(cm)?\b", re.I),
}
_BUDGET_PATTERN = re.compile(
    r"(?:di\s+bawah|maks(?:imal)?|max(?:imum)?|under|below|budget(?:nya)?)\s*"
    r"(?:rp\s*)?(\d[\d.,]*)\s*(k|rb|ribu|jt|juta)?\b",
    re.I,
)
_REQUIRED_MEASUREMENTS = {
    "tops": ("bust",),
    "outerwear": ("bust",),
    "dresses": ("bust", "waist", "hip"),
    "bottoms": ("waist", "hip"),
    "sleepwear": ("bust", "waist", "hip"),
}
_MEASUREMENT_LABELS = {
    "bust": "lingkar dada",
    "waist": "lingkar pinggang",
    "hip": "lingkar pinggul",
}


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def _tokens(value: str) -> set[str]:
    return {token for token in _normalize(value).split() if token not in _STOP_WORDS}


def _category_hits(query: str) -> set[str]:
    tokens = _normalize(query).split()

    def matches(token: str, phrase: str) -> bool:
        target = _normalize(phrase)
        if not target:
            return False
        if token == target or (token.endswith("s") and token[:-1] == target):
            return True
        if len(token) >= 5 and len(target) >= 5:
            return difflib.SequenceMatcher(None, token, target).ratio() >= 0.82
        return False

    return {
        category
        for category, phrases in _CATEGORY_PHRASES.items()
        if any(matches(token, phrase) for token in tokens for phrase in phrases)
    }


def _read_json(filename: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads((config.CS_KNOWLEDGE_DIR / filename).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ApiError(503, f"Data {label} CS belum tersedia atau tidak valid") from exc
    if not isinstance(value, dict):
        raise ApiError(503, f"Data {label} CS belum tersedia atau tidak valid")
    return value


def _load_catalogue() -> dict[str, Any]:
    catalogue = _read_json(CATALOGUE_FILE, "katalog")
    if not isinstance(catalogue.get("categories"), list):
        raise ApiError(503, "Data katalog CS belum tersedia atau tidak valid")
    return catalogue


def _budget_limit(query: str) -> int | None:
    match = _BUDGET_PATTERN.search(query)
    if not match:
        return None
    amount = int(match.group(1).replace(".", "").replace(",", ""))
    multiplier = match.group(2)
    if multiplier and multiplier.lower() in {"k", "rb", "ribu"}:
        amount *= 1000
    elif multiplier and multiplier.lower() in {"jt", "juta"}:
        amount *= 1_000_000
    return amount


def _product_sizes(product: dict[str, Any]) -> list[str]:
    values = product.get("sizes_listed", [])
    return [str(value) for value in values] if isinstance(values, list) else []


def _fuzzy_overlap(query_tokens: set[str], field_tokens: set[str]) -> int:
    """Count query words that exactly match, lose a plural, or are one typo away from a field word."""
    hits = 0
    for token in query_tokens:
        if token in field_tokens or (token.endswith("s") and token[:-1] in field_tokens):
            hits += 1
            continue
        if len(token) >= 5 and any(
            len(word) >= 5 and difflib.SequenceMatcher(None, token, word).ratio() >= 0.82
            for word in field_tokens
        ):
            hits += 1
    return hits


def retrieve_products(query: str, catalogue: dict[str, Any] | None = None, limit: int = 4) -> list[dict[str, Any]]:
    """Return the highest-scoring catalog records without treating snapshot sizes as stock."""
    data = catalogue or _load_catalogue()
    query_tokens = _tokens(query)
    categories = _category_hits(query)
    budget = _budget_limit(query)
    scored: list[tuple[int, str, dict[str, Any], bool]] = []

    for category in data["categories"]:
        if not isinstance(category, dict):
            continue
        category_id = str(category.get("id", ""))
        if categories and category_id not in categories:
            continue
        category_products = category.get("products", [])
        if not isinstance(category_products, list):
            continue
        for product in category_products:
            if not isinstance(product, dict):
                continue
            title = str(product.get("title", ""))
            details = str(product.get("details", ""))
            title_tokens = _tokens(title)
            detail_tokens = _tokens(details)
            color_tokens = _tokens(str(product.get("colorway", "")))
            if isinstance(product.get("colorways"), list):
                for colorway in product["colorways"]:
                    if isinstance(colorway, dict):
                        color_tokens |= _tokens(str(colorway.get("color", "")))
            price = product.get("price_idr")
            if budget is not None and isinstance(price, (int, float)) and price > budget:
                continue

            score = 4 * _fuzzy_overlap(query_tokens, title_tokens) + 2 * _fuzzy_overlap(query_tokens, detail_tokens)
            score += 3 * _fuzzy_overlap(query_tokens, color_tokens)
            if category_id in categories:
                score += 6
            if isinstance(price, (int, float)) and budget is not None:
                score += 2
            if any(size.lower() in query_tokens for size in _product_sizes(product)):
                score += 1
            normalized_title = _normalize(title)
            exact_title = bool(normalized_title and normalized_title in _normalize(query))
            if exact_title:
                score += 20
            if score:
                scored.append((score, title.casefold(), {**product, "_category_id": category_id}, exact_title))

    scored.sort(key=lambda item: (-item[0], item[1]))
    exact_matches = [product for _, _, product, exact in scored if exact]
    if exact_matches:
        return exact_matches[:limit]
    return [product for _, _, product, _ in scored[:limit]]


_CATEGORY_TITLES = {
    "tops": "Tops (Atasan)",
    "dresses": "Dresses",
    "bottoms": "Bottoms (Bawahan)",
    "outerwear": "Outerwear & Jackets",
    "sleepwear": "Pajamas & Sleepwear",
    "underwear": "Underwear & Loungewear",
    "accessories": "Aksesoris",
}


def _product_colors(product: dict[str, Any]) -> list[str]:
    colors = []
    colorway = str(product.get("colorway") or "").strip()
    if colorway:
        colors.append(colorway)
    if isinstance(product.get("colorways"), list):
        for item in product["colorways"]:
            if isinstance(item, dict):
                color = str(item.get("color") or "").strip()
                if color and color not in colors:
                    colors.append(color)
    return colors


def catalog_products(query: str, limit: int = 5, catalogue: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Local snapshot records in the same shape the Postgres catalog returns (for prompt injection)."""
    data = catalogue or _load_catalogue()
    out = []
    for product in retrieve_products(query, data, limit=limit):
        price = product.get("price_idr")
        url = product.get("url")
        if not isinstance(price, (int, float)) or not url:
            continue
        category_id = str(product.get("_category_id", ""))
        out.append({
            "id": str(product.get("product_id")),
            "name": str(product.get("title", "")),
            "category": _CATEGORY_TITLES.get(category_id, category_id.replace("_", " ").title()),
            "price": int(price),
            "price_original": product.get("compare_at_price_idr"),
            "colors": _product_colors(product),
            "sizes": _product_sizes(product),
            "url": str(url),
            "source": "SRC-02",
            "accessed_date": data.get("captured_on"),
            "details": str(product.get("details", "")).strip(),
        })
    return out


def _measurements(query: str) -> tuple[dict[str, float], set[str]]:
    values: dict[str, float] = {}
    missing_units: set[str] = set()
    for dimension, pattern in _MEASUREMENT_PATTERNS.items():
        match = pattern.search(query)
        if match:
            values[dimension] = float(match.group(1).replace(",", "."))
            if not match.group(2):
                missing_units.add(dimension)
    return values, missing_units


def _has_size_intent(query: str) -> bool:
    return bool(set(_normalize(query).split()) & _SIZE_INTENT)


def product_recommendation_guidance(query: str) -> str | None:
    tokens = set(_normalize(query).split())
    if not tokens & _PRODUCT_INTENT and not _category_hits(query):
        return None
    try:
        sop = (config.CS_SOPS_DIR / PRODUCT_SOP_FILE).read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ApiError(503, "Panduan rekomendasi produk CS belum tersedia") from exc
    return f"## Panduan respons rekomendasi produk\n{sop}"


def _size_match(
    product: dict[str, Any],
    measurements: dict[str, float],
    missing_units: set[str],
    chart: dict[str, Any],
) -> str:
    category_id = str(product.get("_category_id", ""))
    required = _REQUIRED_MEASUREMENTS.get(category_id)
    if required is None:
        return "Tidak ada chart terverifikasi untuk menentukan ukuran produk ini."

    product_text = _normalize(
        " ".join(str(product.get(field, "")) for field in ("title", "details", "product_type"))
    )
    if any(f" {term} " in f" {product_text} " for term in ("bra", "bralette", "brallete", "panty", "underwear")):
        return "Produk intim tidak memiliki chart khusus yang terverifikasi; jangan menebak ukuran."

    sizes = set(_product_sizes(product))
    if any(size.isdigit() for size in sizes):
        return "Ukuran denim tercantum, tetapi dasar pengukuran tabel denim belum jelas; jangan menebak ukuran."
    alpha = chart.get("alpha_sizes")
    rows = alpha.get("sizes", []) if isinstance(alpha, dict) else []
    matching_rows = [row for row in rows if isinstance(row, dict) and str(row.get("size")) in sizes]
    if not matching_rows:
        return "Ukuran produk tidak tercakup dalam chart alpha terverifikasi."
    if not measurements:
        needed = ", ".join(_MEASUREMENT_LABELS[name] for name in required)
        return f"Belum ada ukuran tubuh dalam cm. Minta {needed}; jangan menyimpulkan dari berat atau tinggi."
    if missing_units:
        return "Satuan pengukuran belum dipastikan cm; konfirmasikan satuan sebelum mencocokkan."
    missing = [name for name in required if name not in measurements]
    if missing:
        needed = ", ".join(_MEASUREMENT_LABELS[name] for name in missing)
        return f"Data belum lengkap. Minta {needed} dalam cm sebelum mencocokkan."
    if any(not 30 <= measurements[name] <= 200 for name in required):
        return "Ada ukuran di luar rentang yang dapat dicocokkan; konfirmasikan pengukurannya."

    matches = []
    for row in matching_rows:
        if all(
            isinstance(row.get(name), list)
            and len(row[name]) == 2
            and all(isinstance(value, (int, float)) for value in row[name])
            and row[name][0] <= measurements[name] <= row[name][1]
            for name in required
        ):
            matches.append(str(row["size"]))
    if len(matches) == 1:
        return f"Ukuran chart yang cocok: {matches[0]} (berdasarkan ukuran tubuh dan kategori produk; bukan jaminan fit)."
    if matches:
        return f"Hasil ambigu pada batas chart: {', '.join(matches)}. Jangan pilih satu; tanyakan preferensi fit atau eskalasi ke human CS."
    return "Ukuran tubuh tidak seluruhnya berada dalam satu baris chart. Jangan memberi ukuran pasti; jelaskan keterbatasan dan eskalasi ke human CS."


def size_matching_context(
    query: str, products: list[dict[str, Any]]
) -> tuple[str | None, dict[str, Any] | None]:
    """Apply the local verified size chart to products already retrieved by the BFF."""
    if not _has_size_intent(query):
        return None, None

    chart = _read_json(SIZE_CHART_FILE, "size chart")
    alpha = chart.get("alpha_sizes")
    if (
        not isinstance(alpha, dict)
        or alpha.get("measurement_basis") != "body"
        or alpha.get("units") != "cm"
        or not isinstance(alpha.get("sizes"), list)
    ):
        raise ApiError(503, "Data size chart CS belum tersedia atau tidak valid")

    lines = [
        "## Addendum size guide Colorbox terverifikasi",
        "Panduan ini ditranskripsikan dari gambar resmi dan menggantikan catatan lama "
        "CB-SIZE-UNKNOWN-001 serta instruksi bahwa chart belum ditranskripsikan.",
        f"Sumber {chart.get('chart_id')}: {chart.get('source_url')} "
        f"(gambar {chart.get('image_url')}; direkam {chart.get('captured_on')}).",
        "Rentang berikut adalah ukuran tubuh dalam cm; ini bukan jaminan fit. Chart denim "
        "tidak menjelaskan dasar pengukuran, jadi jangan mencocokkan ukuran denim otomatis.",
    ]
    for row in alpha["sizes"]:
        if isinstance(row, dict):
            lines.append(
                f"- {row.get('size')}: dada {row.get('bust')} cm; pinggang "
                f"{row.get('waist')} cm; pinggul {row.get('hip')} cm."
            )

    if products:
        measurements, missing_units = _measurements(query)
        lines.append("### Hasil matching per produk (ikuti hasil ini; jangan menebak ulang)")
        for product in products:
            category_ids = _category_hits(str(product.get("category", "")))
            category_id = next(iter(sorted(category_ids)), "")
            match_product = {
                **product,
                "_category_id": category_id,
                "title": product.get("name", ""),
                "product_type": product.get("category", ""),
                "sizes_listed": product.get("sizes", []),
            }
            lines.append(
                f"- {product.get('name', 'Produk tanpa nama')} "
                f"(ID {product.get('id', 'tidak tercatat')}): "
                f"{_size_match(match_product, measurements, missing_units, chart)}"
            )
    else:
        lines.append(
            "- Belum ada produk yang teridentifikasi di katalog. Minta nama produk atau "
            "kategori sebelum mencocokkan ukuran."
        )
    lines.append(
        "Jika batas rentang menghasilkan beberapa ukuran, jangan pilih satu. Minta klarifikasi; "
        "jangan memakai berat atau tinggi sebagai pengganti lingkar tubuh."
    )
    reference = {
        "type": "knowledge",
        "id": chart.get("chart_id"),
        "title": "Verified Colorbox size guide",
        "classification": "Public Data",
        "source_id": "SRC-05",
        "url": chart.get("source_url"),
        "accessed_date": chart.get("captured_on"),
    }
    return "\n".join(lines), reference


def _format_price(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "tidak tercatat"
    return f"Rp {int(value):,}".replace(",", ".")


def recommendation_context(query: str) -> str | None:
    """Build compact evidence and matching notes only for product/size-related turns."""
    normalized = _normalize(query)
    tokens = set(normalized.split())
    product_intent = bool(tokens & _PRODUCT_INTENT) or bool(_category_hits(query))
    size_intent = _has_size_intent(query)
    if not product_intent and not size_intent:
        return None

    catalogue = _load_catalogue()
    products = retrieve_products(query, catalogue)
    lines = [
        "## Data katalog Colorbox yang ditemukan",
        f"Snapshot katalog {catalogue.get('captured_on', 'tanggal tidak tercatat')}; bukan feed live.",
    ]
    if products:
        for product in products:
            sizes = ", ".join(_product_sizes(product)) or "tidak tercatat"
            colorway = product.get("colorway")
            if not colorway and isinstance(product.get("colorways"), list):
                colorway = ", ".join(
                    str(item.get("color")) for item in product["colorways"] if isinstance(item, dict)
                )
            details = str(product.get("details", "")).strip()
            lines.append(
                f"- Sumber CB-PRODUCT-{product.get('product_id')}: {product.get('title')} "
                f"({product.get('_category_id')}); warna tercatat: {colorway or 'tidak tercatat'}; "
                f"harga snapshot: {_format_price(product.get('price_idr'))}; "
                f"opsi ukuran listing: {sizes}. Detail: {details} "
                f"URL resmi: {product.get('url')}"
            )
    else:
        lines.append(
            "- Tidak ada item katalog yang cocok secara cukup spesifik. Tanyakan kategori, "
            "nama produk, atau preferensi yang relevan; jangan mengarang rekomendasi."
        )
    lines.append(
        "Harga dan opsi ukuran hanya rekaman listing tanggal snapshot; jangan menyebutnya harga "
        "atau stok saat ini. Arahkan pelanggan ke URL resmi untuk memeriksa informasi terbaru."
    )

    if size_intent:
        chart = _read_json(SIZE_CHART_FILE, "size chart")
        alpha = chart.get("alpha_sizes")
        if not isinstance(alpha, dict) or not isinstance(alpha.get("sizes"), list):
            raise ApiError(503, "Data size chart CS belum tersedia atau tidak valid")
        lines.extend([
            "",
            "## Size chart resmi dan batas pencocokan",
            f"Sumber {chart.get('chart_id')}: {chart.get('source_url')} "
            f"(gambar chart: {chart.get('image_url')}; direkam {chart.get('captured_on')}).",
            "Chart ukuran XS-XL menyatakan ukuran tubuh dalam cm. Chart denim numerik tidak "
            "menjelaskan dengan tegas apakah angkanya ukuran tubuh atau pakaian; jangan gunakan "
            "untuk rekomendasi otomatis.",
        ])
        for row in alpha["sizes"]:
            if isinstance(row, dict):
                lines.append(
                    f"- {row.get('size')}: dada {row.get('bust')} cm; pinggang "
                    f"{row.get('waist')} cm; pinggul {row.get('hip')} cm; "
                    f"panjang kaki bagian dalam {row.get('inseam_cm')} cm."
                )
        if products:
            measurements, missing_units = _measurements(query)
            lines.append("### Hasil matching per produk (ikuti hasil ini; jangan menebak ulang)")
            for product in products:
                lines.append(
                    f"- CB-PRODUCT-{product.get('product_id')}: "
                    f"{_size_match(product, measurements, missing_units, chart)}"
                )
        else:
            lines.append(
                "- Produk spesifik belum teridentifikasi; minta nama produk atau kategori "
                "sebelum memberikan ukuran."
            )
        lines.append(
            "Ukuran pada batas dua rentang dapat menghasilkan lebih dari satu kandidat. "
            "Sebutkan ukuran hanya jika hasilnya tunggal; selain itu minta klarifikasi atau "
            "eskalasi. Jangan memakai berat/tinggi sebagai pengganti lingkar tubuh."
        )
    return "\n".join(lines)
