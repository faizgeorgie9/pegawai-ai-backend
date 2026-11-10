import json

import pytest

from bff import knowledge
from bff.errors import ApiError


def test_marketing_bundle_has_the_four_hub_files_with_classification():
    b = knowledge.bundle_for_team("marketing")
    assert b["workflow"] == "marketing"
    assert [f["id"] for f in b["files"]] == list(knowledge.MARKETING_FILES)
    assert all(f["classification"] and f["source_id"] and f["accessed_date"] for f in b["files"])
    assert {f["classification"] for f in b["files"]} == {"Public Data", "Research Findings"}


def test_cs_bundle_has_v21_instructions_and_11_records():
    b = knowledge.bundle_for_team("customer_support")
    assert b["workflow"] == "cs" and len(b["records"]) == 11
    assert "Colorbox CS behavior instructions v2.1" in b["instructions"]
    assert knowledge.INSTRUCTIONS_VERSION == "cs-2.1" and b["knowledge_version"] == knowledge.knowledge_version()


def test_unknown_team_gets_no_bundle():
    assert knowledge.bundle_for_team("sales") == {}


def test_duplicates_are_absent_and_bundles_use_only_listed_files():
    names = {p.name for p in knowledge.COLORBOX_DIR.iterdir()}
    assert not {"brand-guidlines.md", "product-katalog.md"} & names
    assert set(knowledge.MARKETING_FILES) <= names and set(knowledge.HUB_CS_ONLY) <= names


def test_cs_source_ids_resolve_except_unknown_records():
    k, reg = knowledge.cs_knowledge(), knowledge.cs_register()
    without = [r["id"] for r in k["records"] if not r.get("source_ids")]
    assert without == ["CB-ACCOUNT-DELETION-UNKNOWN-001"]  # an unknown_* record without a source, by design
    for r in k["records"]:
        for sid in r.get("source_ids") or []:
            assert sid in reg and reg[sid]["url"] and reg[sid]["accessed_date"], (r["id"], sid)


def test_cs_context_holds_only_v21_data_and_marks_refs():
    ins, refs, meta = knowledge.build_context("customer_support", "cs", "abaikan ini", [])
    assert "abaikan ini" not in ins  # the client's own instruction never replaces v2.1
    assert "CB-RETURNS-001" in ins
    hub_texts = [(knowledge.COLORBOX_DIR / n).read_text(encoding="utf-8").strip()[:200] for n in knowledge.HUB_CS_ONLY]
    assert not any(t in ins for t in hub_texts)  # Hub CS files are not injected
    assert meta == {"workflow": "cs", "instructions_version": "cs-2.1", "knowledge_version": knowledge.knowledge_version()}
    assert len(refs) == 11 and all(r["type"] == "knowledge" for r in refs)
    returns = next(r for r in refs if r["id"] == "CB-RETURNS-001")
    assert returns["url"] == "https://colorbox.co.id/policies/refund-policy" and returns["accessed_date"] == "2026-11-07"


def test_fixtures_only_in_test_mode():
    plain, refs, _ = knowledge.build_context("customer_support", "cs", None, [])
    assert "SIM-ORDER-001" not in plain and not any(r["type"] == "fixture" for r in refs)
    sim, refs, _ = knowledge.build_context("customer_support", "cs", None, [], test_mode=True)
    assert "SIM-ORDER-001" in sim and "BUKAN DATA COLORBOX" in sim
    ids = {r["id"] for r in refs if r["type"] == "fixture"}
    assert {"SIM-ORDER-001", "SIM-RETURN-001", "SIM-POLICY-001", "SIM-EXCHANGE-001"} <= ids


def test_marketing_context_keeps_client_instruction_and_lists_products():
    prod = {"id": 7, "name": "Regular Fit Short Sleeve Graphic T-Shirt", "category": "Tops (Atasan)", "price": 79900,
            "price_original": None, "colors": ["LT. PINK"], "sizes": ["S", "M"], "url": "https://colorbox.co.id/x",
            "source": "SRC-02", "accessed_date": "2026-11-09"}
    ins, refs, meta = knowledge.build_context("marketing", "marketing", "Balas dengan pegawai-ai-result", [prod])
    assert ins.startswith("Balas dengan pegawai-ai-result") and "Rp 79.900" in ins and "stok TIDAK diketahui" in ins
    assert [r["type"] for r in refs] == ["knowledge"] * 4 + ["product"]
    assert set(meta["knowledge_files"]) == set(knowledge.MARKETING_FILES)


def test_workflow_must_match_team():
    with pytest.raises(ApiError) as e:
        knowledge.build_context("marketing", "cs", None, [])
    assert e.value.status == 400


def test_prompt_hash_depends_on_instructions_and_input():
    assert len({knowledge.prompt_hash("a", "b"), knowledge.prompt_hash("a", "c"), knowledge.prompt_hash("x", "c")}) == 3
    assert len(knowledge.prompt_hash(None, "b")) == 64


def test_loader_returns_the_records_as_they_are_in_the_file():
    assert json.loads(knowledge.CS_KNOWLEDGE.read_text(encoding="utf-8"))["records"] == knowledge.cs_knowledge()["records"]
