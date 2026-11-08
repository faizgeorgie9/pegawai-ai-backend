"""
test_chat_execution.py - Test Suite for Chat Execution, Multi-Turn Context & Structured Outputs
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

from chat_orchestrator import ChatOrchestrator

def run_tests():
    print("=" * 70)
    print("RUNNING CHAT EXECUTION, CONTEXT & STRUCTURED OUTPUTS TEST SUITE (S3-02C)")
    print("=" * 70)

    orchestrator = ChatOrchestrator()
    test_results = []

    # -------------------------------------------------------------
    # TEST 1: Marketing 5-Stage Structured Output Execution
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Colorbox Marketing 5-Stage Workflow...")
    brief = "Promo Koleksi Casual Linen untuk Remaja Menghadapi Liburan Semester"
    mkt_res = orchestrator.execute_marketing_workflow(brief=brief, content_type="instagram_carousel", include_visual=True)

    data = mkt_res.get("data", {})
    t1_pass = (
        mkt_res["status"] == "success" and
        "planning" in data and
        "generation" in data and
        "brand_review" in data and
        "visual_concept" in data and
        data["brand_review"]["compliance_score"] >= 80 and
        len(data["generation"]["hashtags"]) >= 2
    )

    print(f"Status: {mkt_res['status']} | Execution Duration: {mkt_res['execution_duration_sec']}s")
    print(f"Campaign Theme: {data.get('planning', {}).get('campaign_theme')}")
    print(f"Pillar: {data.get('planning', {}).get('content_pillar')}")
    print(f"Primary Copy Hook: {data.get('generation', {}).get('primary_copy')[:100]}...")
    print(f"Compliance Score: {data.get('brand_review', {}).get('compliance_score')}/100")
    print(f"Palette: {data.get('visual_concept', {}).get('color_palette')}")
    print(f"Status: {'PASS [OK]' if t1_pass else 'FAIL [X]'}")
    test_results.append(("Marketing 5-Stage Structured Workflow", t1_pass))

    # -------------------------------------------------------------
    # TEST 2: Customer Service Multi-Turn Context (Turn 1 & Turn 2)
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing CS Multi-Turn Context Continuity (2 Turns)...")
    sess_id = f"sess_test_cbx_{int(time.time())}"

    # Turn 1
    t1_msg = "Kak, baju yang kemarin saya beli di Colorbox PIM kekecilan, apakah bisa ditukar ukurannya?"
    turn1_res = orchestrator.execute_cs_chat(
        session_id=sess_id,
        message=t1_msg,
        customer_name="Nadia",
        channel="whatsapp_simulation"
    )
    pass_t1 = (
        turn1_res["status"] == "success" and
        turn1_res["turn_number"] == 1 and
        turn1_res["classification"]["intent"] == "SIZE_EXCHANGE"
    )
    print(f"Turn 1 Intent: {turn1_res['classification']['intent']} | SOP: {turn1_res['knowledge_applied']['sop_source']}")
    print(f"Turn 1 Draft: {turn1_res['response'][:110]}...")

    # Turn 2 (Context dependent)
    t2_msg = "Nomor pesanan saya #CBX-2026-9812 baru dibeli kemarin tanggal 5 November, struk dan tag harga masih utuh terpasang ya Kak."
    turn2_res = orchestrator.execute_cs_chat(
        session_id=sess_id,
        message=t2_msg,
        customer_name="Nadia",
        channel="whatsapp_simulation"
    )
    pass_t2 = (
        turn2_res["status"] == "success" and
        turn2_res["turn_number"] == 2 and
        len(orchestrator.sessions.get_session(sess_id)["history"]) == 4
    )
    print(f"Turn 2 Turn Number: {turn2_res['turn_number']} (Confirmed history retained)")
    print(f"Turn 2 Ticket ID: {turn2_res['ticket_management']['ticket_id']}")
    print(f"Turn 2 Priority: {turn2_res['ticket_management']['priority']}")

    t2_pass = pass_t1 and pass_t2
    print(f"Status: {'PASS [OK]' if t2_pass else 'FAIL [X]'}")
    test_results.append(("CS Multi-Turn Context Continuity", t2_pass))

    # -------------------------------------------------------------
    # TEST 3: Session Reset Semantics
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Session Reset Semantics...")
    reset_ok = orchestrator.sessions.reset_session(sess_id)
    history_immediately_after_reset = len(orchestrator.sessions.get_session(sess_id)["history"])

    # Subsequent message after reset should be turn 1
    turn_after_reset = orchestrator.execute_cs_chat(
        session_id=sess_id,
        message="Halo mau tanya jam buka toko Colorbox GI hari ini",
        customer_name="Nadia"
    )
    history_after_new_turn = len(orchestrator.sessions.get_session(sess_id)["history"])

    t3_pass = (
        reset_ok and
        history_immediately_after_reset == 0 and
        history_after_new_turn == 2 and
        turn_after_reset["turn_number"] == 1
    )
    print(f"Reset Succeeded: {reset_ok} (History cleared to 0)")
    print(f"Turn Number After Reset: {turn_after_reset['turn_number']} (Fresh Turn 1 confirmed)")
    print(f"Status: {'PASS [OK]' if t3_pass else 'FAIL [X]'}")
    test_results.append(("Session History Reset Semantics", t3_pass))

    # -------------------------------------------------------------
    # TEST 4: Critical Complaint Escalation Trigger
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Critical Complaint & Automatic Escalation Trigger...")
    crit_msg = "Saya sangat kecewa barang cacat parah! Saya mau viralkan ke TikTok dan lapor polisi jika tidak ada ganti rugi sekarang!"
    crit_sess = f"sess_crit_{int(time.time())}"
    crit_res = orchestrator.execute_cs_chat(
        session_id=crit_sess,
        message=crit_msg,
        customer_name="Rina"
    )

    ticket = crit_res.get("ticket_management", {})
    t4_pass = (
        ticket.get("priority") == "CRITICAL" and
        ticket.get("status") == "ESCALATED_TO_SUPERVISOR" and
        ticket.get("requires_human_escalation") is True
    )
    print(f"Priority Detected: {ticket.get('priority')}")
    print(f"Status Ticket: {ticket.get('status')}")
    print(f"Requires Escalation: {ticket.get('requires_human_escalation')}")
    print(f"Reason: {ticket.get('escalation_reason')}")
    print(f"Status: {'PASS [OK]' if t4_pass else 'FAIL [X]'}")
    test_results.append(("Critical Complaint Auto-Escalation", t4_pass))

    # -------------------------------------------------------------
    # TEST 5: Security & Zero Secret Leaks
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Security & Credential Hygiene...")
    combined_dump = json.dumps([mkt_res, turn1_res, turn2_res, crit_res])
    has_leak = any(k in combined_dump for k in ["sk-", "oc_sk_", "password", "SECRET_KEY"])
    t5_pass = not has_leak
    print(f"Zero Credential Leakage: {'PASS [OK]' if t5_pass else 'FAIL [X]'}")
    test_results.append(("Security & Zero Secret Leaks", t5_pass))

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
    print(f"OVERALL RESULT: {'ALL TESTS PASSED (5/5)' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 70)

    # Save test evidence JSON
    evidence_file = Path(__file__).parent / "evidence" / "s3_02c_chat_execution_test_results.json"
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_file, "w", encoding="utf-8") as ef:
        json.dump({
            "test_suite": "S3-02C Chat Execution, Context and Structured Agent Outputs",
            "date": "2026-11-06",
            "overall_status": "SUCCESS" if all_passed else "FAILED",
            "tests": [
                {"name": name, "passed": passed} for name, passed in test_results
            ],
            "sample_marketing_output": mkt_res,
            "sample_cs_turn1": turn1_res,
            "sample_cs_turn2": turn2_res,
            "sample_critical_escalation": crit_res
        }, ef, indent=2)
    print(f"Saved test evidence to: {evidence_file}")
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
