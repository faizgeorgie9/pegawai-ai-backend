"""
test_agent_management.py - Test Suite for Agent Management, Configuration and Routing
Sprint 3 Day 2 (November 6, 2026) - Intern 1 (Backend & Platform Lead)
"""

import sys
import os
import json
import time
from pathlib import Path

# Add backend_template to path
BACKEND_DIR = Path(__file__).parent / "backend_template"
sys.path.insert(0, str(BACKEND_DIR))

from agent_manager import AgentManager

def run_tests():
    print("=" * 70)
    print("RUNNING AGENT MANAGEMENT, CONFIGURATION & ROUTING TEST SUITE (S3-02B)")
    print("=" * 70)

    # Use a dedicated test storage file to avoid corrupting prototype seed data
    test_storage = BACKEND_DIR / "agents_test_temp.json"
    if test_storage.exists():
        os.remove(test_storage)

    manager = AgentManager(storage_path=test_storage)
    test_results = []

    # -------------------------------------------------------------
    # TEST 1: List Agents (GET /api/v1/agents)
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Agent List Operation...")
    agents = manager.list_agents()
    print(f"Total Agents Loaded: {len(agents)}")
    for a in agents:
        print(f"  - [{a['id']}] {a['name']} ({a['department']}) | Tone: {a['tone']}")

    t1_pass = len(agents) >= 2 and any(a["id"] == "ag_cbx_marketing_01" for a in agents)
    print(f"Status: {'PASS [OK]' if t1_pass else 'FAIL [X]'}")
    test_results.append(("List Prototype Agents", t1_pass))

    # -------------------------------------------------------------
    # TEST 2: Create Agent (POST /api/v1/agents)
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Agent Create Operation...")
    new_agent_payload = {
        "id": "ag_cbx_ambassador_01",
        "name": "Colorbox Youth Ambassador & Stylist",
        "department": "marketing",
        "role": "Gen-Z Community Stylist & Influencer Liaison",
        "tone": "cheerful_genz",
        "avatar": "✨",
        "max_tokens": 2200,
        "timeout_sec": 150,
        "system_instruction": "Bertindaklah sebagai Brand Ambassador muda Colorbox.",
        "tools_assigned": ["banner_generator", "knowledge_retriever"]
    }
    created_agent, err = manager.create_agent(new_agent_payload)
    print(f"Create Result: {created_agent['id'] if created_agent else 'Error'}")
    if err:
        print(f"Error: {err}")

    t2_pass = created_agent is not None and created_agent["id"] == "ag_cbx_ambassador_01"
    print(f"Status: {'PASS [OK]' if t2_pass else 'FAIL [X]'}")
    test_results.append(("Create New Agent", t2_pass))

    # -------------------------------------------------------------
    # TEST 3: View Agent Detail (GET /api/v1/agents/{id})
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Agent View Detail Operation...")
    viewed_agent, err = manager.get_agent("ag_cbx_ambassador_01")
    t3_pass = viewed_agent is not None and viewed_agent["name"] == "Colorbox Youth Ambassador & Stylist"
    print(f"Viewed Agent Name: {viewed_agent.get('name') if viewed_agent else 'None'}")
    print(f"Role: {viewed_agent.get('role') if viewed_agent else 'None'}")
    print(f"Status: {'PASS [OK]' if t3_pass else 'FAIL [X]'}")
    test_results.append(("View Agent Detail", t3_pass))

    # -------------------------------------------------------------
    # TEST 4: Update Agent Configuration (PUT /api/v1/agents/{id})
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Agent Configuration Update Operation...")
    updates = {
        "tone": "grounded_persuasive",
        "max_tokens": 3000,
        "role": "Lead Senior Youth Stylist"
    }
    updated_agent, err = manager.update_agent("ag_cbx_ambassador_01", updates)
    t4_pass = (
        updated_agent is not None and
        updated_agent["tone"] == "grounded_persuasive" and
        updated_agent["max_tokens"] == 3000 and
        updated_agent["role"] == "Lead Senior Youth Stylist"
    )
    print(f"Updated Tone: {updated_agent.get('tone') if updated_agent else 'None'}")
    print(f"Updated Max Tokens: {updated_agent.get('max_tokens') if updated_agent else 'None'}")
    print(f"Updated Timestamp: {updated_agent.get('updated_at') if updated_agent else 'None'}")
    print(f"Status: {'PASS [OK]' if t4_pass else 'FAIL [X]'}")
    test_results.append(("Update Agent Configuration", t4_pass))

    # -------------------------------------------------------------
    # TEST 5: Input Validation & Unknown Agent Errors (400 / 404)
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Validation Rules & Unknown Agent Error Semantics...")
    # 5a: Unknown Agent
    unknown_agent, err_unknown = manager.get_agent("ag_unknown_999")
    pass_5a = unknown_agent is None and "not found" in err_unknown.lower()
    print(f"5a. Unknown Agent Error: \"{err_unknown}\" -> {'PASS' if pass_5a else 'FAIL'}")

    # 5b: Missing Name
    _, err_name = manager.create_agent({"department": "marketing"})
    pass_5b = "mandatory" in err_name.lower()
    print(f"5b. Missing Name Error: \"{err_name}\" -> {'PASS' if pass_5b else 'FAIL'}")

    # 5c: Invalid Department
    _, err_dept = manager.create_agent({"name": "Test", "department": "space_exploration"})
    pass_5c = "invalid department" in err_dept.lower()
    print(f"5c. Invalid Department Error: \"{err_dept}\" -> {'PASS' if pass_5c else 'FAIL'}")

    t5_pass = pass_5a and pass_5b and pass_5c
    print(f"Status: {'PASS [OK]' if t5_pass else 'FAIL [X]'}")
    test_results.append(("Input Validation & Error Handling", t5_pass))

    # -------------------------------------------------------------
    # TEST 6: Execution Routing to Selected Agent & Knowledge
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing Execution Routing Logic...")
    # Route by ID
    routed_mkt, err = manager.route_request(agent_id="ag_cbx_marketing_01")
    pass_6a = routed_mkt is not None and routed_mkt["department"] == "marketing"

    # Route by Department
    routed_cs, err = manager.route_request(department="customer_service")
    pass_6b = routed_cs is not None and routed_cs["id"] == "ag_cbx_cs_01"

    # Verify no secrets exposed in agent config
    secrets_leaked = any(
        "sk-" in str(a) or "oc_sk_" in str(a) or "password" in str(a)
        for a in manager.list_agents()
    )
    pass_6c = not secrets_leaked

    print(f"6a. Route by Explicit ID: {routed_mkt['id'] if routed_mkt else 'Error'} -> {'PASS' if pass_6a else 'FAIL'}")
    print(f"6b. Route by Department: {routed_cs['id'] if routed_cs else 'Error'} -> {'PASS' if pass_6b else 'FAIL'}")
    print(f"6c. Zero Secret Leaks: {'PASS (No credentials exposed)' if pass_6c else 'FAIL (Leak detected)'}")

    t6_pass = pass_6a and pass_6b and pass_6c
    print(f"Status: {'PASS [OK]' if t6_pass else 'FAIL [X]'}")
    test_results.append(("Execution Routing & Security", t6_pass))

    # Clean up test storage
    if test_storage.exists():
        os.remove(test_storage)

    # -------------------------------------------------------------
    # SUMMARY & EVIDENCE RECORDING
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
    print(f"OVERALL RESULT: {'ALL TESTS PASSED (6/6)' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 70)

    # Save test evidence
    evidence_file = Path(__file__).parent / "evidence" / "s3_02b_agent_management_test_results.json"
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_file, "w", encoding="utf-8") as ef:
        json.dump({
            "test_suite": "S3-02B Agent Management, Configuration and Routing",
            "date": "2026-11-06",
            "overall_status": "SUCCESS" if all_passed else "FAILED",
            "tests": [
                {"name": name, "passed": passed} for name, passed in test_results
            ],
            "sample_created_agent": created_agent,
            "sample_updated_agent": updated_agent,
            "sample_error_unknown": err_unknown,
            "sample_error_invalid_dept": err_dept
        }, ef, indent=2)
    print(f"Saved test evidence to: {evidence_file}")
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

