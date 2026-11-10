"""
test_knowledge_retrieval.py - Test suite for Colorbox Knowledge Loading & Simple Retrieval
Sprint 3 Day 2 (November 6, 2026) - Intern 1 (Backend & Platform Lead)
"""

import sys
import os
import json
from pathlib import Path

# Add backend_template to path
BACKEND_DIR = Path(__file__).parent / "backend_template"
sys.path.insert(0, str(BACKEND_DIR))

from knowledge_retriever import KnowledgeRetriever

def run_tests():
    print("=" * 70)
    print("RUNNING COLORBOX KNOWLEDGE LOADING & RETRIEVAL TEST SUITE (S3-02A)")
    print("=" * 70)

    retriever = KnowledgeRetriever()
    test_results = []

    # -------------------------------------------------------------
    # TEST 1: Knowledge Registry Loading & Version Verification
    # -------------------------------------------------------------
    print("\n[TEST 1] Verifying Incremental Versioned File Loading...")
    registry_keys = list(retriever.registry.keys())
    print(f"Loaded Files: {registry_keys}")

    t1_pass = (
        "shared_brand_knowledge_v1" in registry_keys and
        "colorbox_marketing_knowledge_v1" in registry_keys and
        "colorbox_cs_sop_v1" in registry_keys
    )
    print(f"Status: {'PASS [OK]' if t1_pass else 'FAIL [X]'}")
    test_results.append(("Versioned File Loading", t1_pass))

    for k, v in retriever.registry.items():
        print(f"  - {v['filename']} | Version: {v['version']} | Code: {v['ref_code']} | Sections: {len(v['sections'])}")

    # -------------------------------------------------------------
    # TEST 2: Grounded CS Retrieval with Exact Source Reference
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Grounded Customer Service Retrieval (Size Exchange)...")
    cs_query = "Kak, baju yang kemarin saya beli di Colorbox kekecilan, apakah bisa ditukar ukurannya?"
    res_cs = retriever.retrieve(cs_query, department="cs")
    
    t2_pass = (
        res_cs["status"] == "KNOWLEDGE_FOUND" and
        res_cs["grounded"] is True and
        len(res_cs["results"]) > 0 and
        "SOP-CBX-RET-01" in str(res_cs["results"])
    )
    print(f"Query: \"{cs_query}\"")
    print(f"Found Status: {res_cs['status']}")
    print(f"Primary Source: {res_cs.get('primary_source')}")
    if res_cs["results"]:
        top = res_cs["results"][0]
        print(f"Top Match Title: {top['title']}")
        print(f"Labels Detected: {top['labels']}")
        print(f"Excerpt: {top['content'][:150]}...")
    print(f"Status: {'PASS [OK]' if t2_pass else 'FAIL [X]'}")
    test_results.append(("Grounded CS Retrieval (SOP-CBX-RET-01)", t2_pass))

    # -------------------------------------------------------------
    # TEST 3: Grounded Marketing Retrieval with Tone & Palette
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Grounded Marketing Retrieval (Summer Pastel Campaign)...")
    mkt_query = "Rancangan konten promosi summer pastel remaja untuk Instagram"
    res_mkt = retriever.retrieve(mkt_query, department="marketing")

    t3_pass = (
        res_mkt["status"] == "KNOWLEDGE_FOUND" and
        res_mkt["grounded"] is True and
        len(res_mkt["results"]) > 0
    )
    print(f"Query: \"{mkt_query}\"")
    print(f"Found Status: {res_mkt['status']}")
    print(f"Primary Source: {res_mkt.get('primary_source')}")
    if res_mkt["results"]:
        print(f"Top Match Title: {res_mkt['results'][0]['title']}")
    print(f"Status: {'PASS [OK]' if t3_pass else 'FAIL [X]'}")
    test_results.append(("Grounded Marketing Retrieval", t3_pass))

    # -------------------------------------------------------------
    # TEST 4: Truthful Absent Knowledge Detection (Zero Hallucination)
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Truthful Absent / Missing Knowledge Behavior...")
    missing_query = "Apakah Colorbox menerima gadai emas murni atau jual ban mobil second?"
    res_missing = retriever.retrieve(missing_query, department="cs")

    t4_pass = (
        res_missing["status"] == "KNOWLEDGE_ABSENT" and
        res_missing["grounded"] is False and
        res_missing["fallback_action"] == "ESCALATE_TO_SUPERVISOR" and
        len(res_missing["results"]) == 0
    )
    print(f"Out-of-Scope Query: \"{missing_query}\"")
    print(f"Status Returned: {res_missing['status']}")
    print(f"Grounded: {res_missing['grounded']}")
    print(f"Fallback Action: {res_missing['fallback_action']}")
    print(f"Suggested Response: \"{res_missing['suggested_response'][:120]}...\"")
    print(f"Status: {'PASS [OK]' if t4_pass else 'FAIL [X]'}")
    test_results.append(("Truthful Missing Knowledge Fallback", t4_pass))

    # -------------------------------------------------------------
    # TEST 5: Strict Department Knowledge Isolation
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Strict Departmental Knowledge Isolation...")
    mkt_context = retriever.get_agent_knowledge("marketing")
    cs_context = retriever.get_agent_knowledge("customer_service")

    # Marketing must NOT have CS internal escalation thresholds
    mkt_isolated = "SOP-CBX-ESC-04" not in mkt_context and "Human Takeover" not in mkt_context
    # CS must NOT have Marketing internal campaign pillars
    cs_isolated = "MKT-PIL-01" not in cs_context and "OOTD Inspiration" not in cs_context

    t5_pass = mkt_isolated and cs_isolated
    print(f"Marketing Context Excludes CS Escalation Matrix: {mkt_isolated}")
    print(f"CS Context Excludes Marketing Strategy Pillars: {cs_isolated}")
    print(f"Both Share Colorbox Brand Tone: {'Babes' in mkt_context and 'Kak' in cs_context}")
    print(f"Status: {'PASS [OK]' if t5_pass else 'FAIL [X]'}")
    test_results.append(("Department Knowledge Isolation", t5_pass))

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("TEST SUMMARY:")
    all_passed = True
    for name, passed in test_results:
        status_str = "PASS [OK]" if passed else "FAIL [X]"
        print(f"  - {name.ljust(45)}: {status_str}")
        if not passed:
            all_passed = False

    print("=" * 70)
    print(f"OVERALL RESULT: {'ALL TESTS PASSED (5/5)' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 70)

    # Save test results to JSON
    evidence_file = Path(__file__).parent / "evidence" / "s3_02a_knowledge_test_results.json"
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_file, "w", encoding="utf-8") as ef:
        json.dump({
            "test_suite": "S3-02A Knowledge Loading and Retrieval",
            "date": "2026-11-06",
            "overall_status": "SUCCESS" if all_passed else "FAILED",
            "tests": [
                {"name": name, "passed": passed} for name, passed in test_results
            ],
            "sample_cs_retrieval": res_cs,
            "sample_missing_retrieval": res_missing
        }, ef, indent=2)
    print(f"Saved test evidence to: {evidence_file}")
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

