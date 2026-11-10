"""
test_platform_capabilities.py - Test Suite for Supported Platform Capabilities & Handoffs
Sprint 3 Day 3 (November 9, 2026) - Intern 1 (Backend & Platform Lead)
"""

import sys
import os
import json
import time
import uuid
from pathlib import Path

# Add backend_template to path
BACKEND_DIR = Path(__file__).parent / "backend_template"
sys.path.insert(0, str(BACKEND_DIR))

# Automatically load environment variables
from server import load_env_file
load_env_file()
os.environ["FAST_CONTRACT_TEST"] = "1"

from platform_adapters import (
    tool_registry,
    integration_monitor,
    computer_use_inspector,
    scheduler_service,
    activity_tracker
)
from chat_orchestrator import chat_orchestrator

def run_tests():
    print("=" * 70)
    print("RUNNING SUPPORTED PLATFORM CAPABILITIES & HANDOFFS TEST SUITE (S3-03A)")
    print("=" * 70)

    test_results = []

    # -------------------------------------------------------------
    # TEST 1: Tools & Plugins Registry & Tool Assignment
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Tools/Plugins Registry & Tool Assignment...")
    tools = tool_registry.list_tools()
    print(f"Total Tools Registered: {len(tools)}")
    for t in tools:
        print(f"  - [{t['id']}] {t['name']} | Status: {t['status'].upper()} | Type: {t['type']}")

    # Assign safe working tool
    ok_assign, msg_assign = tool_registry.assign_tool("ag_cbx_marketing_01", "tool_banner_generator")
    # Attempt to assign unsupported tool (should fail safely)
    bad_assign, msg_bad = tool_registry.assign_tool("ag_cbx_marketing_01", "plugin_shopee_mall_erp")

    t1_pass = len(tools) >= 5 and ok_assign and not bad_assign
    print(f"Assign Safe Tool: {'PASS [OK]' if ok_assign else 'FAIL'}")
    print(f"Reject Unsupported Tool: {'PASS [OK]' if not bad_assign else 'FAIL'}")
    print(f"Status: {'PASS [OK]' if t1_pass else 'FAIL [X]'}")
    test_results.append(("Tools/Plugins Registry & Safe Assignment", t1_pass))

    # -------------------------------------------------------------
    # TEST 2: Integration Connection States
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Integration Connection States Monitor...")
    status_report = integration_monitor.get_status()
    summary = status_report.get("summary", {})
    integrations = status_report.get("integrations", {})

    print(f"Summary Counts: Connected={summary.get('connected')}, Mocked={summary.get('mocked')}, Unsupported={summary.get('unsupported')}")
    for k, v in integrations.items():
        print(f"  - {v['name']}: [{v['status'].upper()}] - {v['detail'][:60]}...")

    t2_pass = (
        status_report["status"] == "success" and
        summary.get("mocked", 0) >= 1 and
        summary.get("unsupported", 0) >= 2 and
        "hermes_agent_cli" in integrations
    )
    print(f"Status: {'PASS [OK]' if t2_pass else 'FAIL [X]'}")
    test_results.append(("Integration Connection States Classification", t2_pass))

    # -------------------------------------------------------------
    # TEST 3: Computer Use Capability Boundary & Investigation
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Computer Use Capability Investigation...")
    cu_report = computer_use_inspector.get_capability_report()
    t3_pass = (
        cu_report["status"] == "unsupported" and
        cu_report["supported"] is False and
        "NOT_REQUIRED" in cu_report["investigation_findings"]["business_relevance"]
    )
    print(f"Capability Status: {cu_report['status'].upper()}")
    print(f"Investigation Reason: {cu_report['investigation_findings']['reason'][:100]}...")
    print(f"Business Relevance: {cu_report['investigation_findings']['business_relevance']}")
    print(f"Status: {'PASS [OK]' if t3_pass else 'FAIL [X]'}")
    test_results.append(("Computer Use Investigation & Safe Boundary", t3_pass))

    # -------------------------------------------------------------
    # TEST 4: Scheduler Job Management
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Scheduler Job Management...")
    initial_jobs = scheduler_service.list_jobs()
    print(f"Pre-configured Jobs: {len(initial_jobs)}")

    # Create safe prototype dummy job
    dummy_job_data = {
        "job_id": f"job_test_dummy_{int(time.time()) % 1000}",
        "name": "Daily Morning Content Sync Reminder",
        "cron_expression": "0 7 * * *",
        "target_agent": "ag_cbx_marketing_01"
    }
    new_job, err_job = scheduler_service.create_job(dummy_job_data)
    print(f"Created Dummy Job: {new_job['job_id'] if new_job else 'Error'}")

    # Update job status
    updated_job, err_up = scheduler_service.update_job_status(new_job["job_id"], "paused")
    print(f"Updated Status: {updated_job['status'] if updated_job else 'Error'}")

    t4_pass = new_job is not None and updated_job is not None and updated_job["status"] == "paused"
    print(f"Status: {'PASS [OK]' if t4_pass else 'FAIL [X]'}")
    test_results.append(("Scheduler Job Listing, Creation & Status Management", t4_pass))

    # -------------------------------------------------------------
    # TEST 5: Activity & Execution Status Lifecycle Tracking
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Activity & Execution Lifecycle Tracker...")
    # Record a test run
    activity_tracker.record_run(
        run_id=f"run_test_{uuid.uuid4().hex[:6]}",
        agent_id="ag_cbx_cs_01",
        workflow="colorbox_cs_v1",
        duration_sec=22.5,
        tokens=1420,
        status="completed"
    )

    activity_status = activity_tracker.get_activity_status()
    print(f"Total Recorded Runs: {activity_status['total_runs']}")
    print(f"Successful Runs: {activity_status['successful_runs']}")
    print(f"Total Tokens: {activity_status['total_tokens_consumed']}")
    print(f"Average Latency: {activity_status['average_latency_sec']}s")

    t5_pass = (
        activity_status["status"] == "success" and
        activity_status["total_runs"] >= 2 and
        activity_status["total_tokens_consumed"] > 0
    )
    print(f"Status: {'PASS [OK]' if t5_pass else 'FAIL [X]'}")
    test_results.append(("Activity Status & Execution Lifecycle Tracking", t5_pass))

    # -------------------------------------------------------------
    # TEST 6: Core Business Workflows Focused Regression
    # -------------------------------------------------------------
    print("\n[TEST 6] Running Focused Regression on Core Business Workflows...")
    # 6a. Marketing
    reg_mkt = chat_orchestrator.execute_marketing_workflow(
        brief="Koleksi Denim & Knitwear Colorbox Musim Gugur",
        content_type="instagram_carousel"
    )
    pass_6a = reg_mkt["status"] == "success" and "brand_review" in reg_mkt["data"]

    # 6b. CS 2-Turn
    reg_sess = f"sess_reg_{int(time.time())}"
    reg_cs_1 = chat_orchestrator.execute_cs_chat(reg_sess, "Mau tanya cara retur baju yang cacat produksi")
    reg_cs_2 = chat_orchestrator.execute_cs_chat(reg_sess, "Pesanan #CBX-2026-4401 ada robek di bagian lengan baju")
    pass_6b = reg_cs_1["status"] == "success" and reg_cs_2["turn_number"] == 2

    # 6c. Controlled Error / Missing Knowledge
    lookup_missing = chat_orchestrator.execute_cs_chat(reg_sess, "Apakah bisa servis velg motor dan knalpot racing?")
    pass_6c = lookup_missing["ticket_management"]["requires_human_escalation"] is True

    t6_pass = pass_6a and pass_6b and pass_6c
    print(f"Marketing Regression: {'PASS' if pass_6a else 'FAIL'}")
    print(f"CS 2-Turn Regression: {'PASS' if pass_6b else 'FAIL'}")
    print(f"Controlled Missing Data Escalation: {'PASS' if pass_6c else 'FAIL'}")
    print(f"Status: {'PASS [OK]' if t6_pass else 'FAIL [X]'}")
    test_results.append(("Core Business Workflows Focused Regression", t6_pass))

    # -------------------------------------------------------------
    # SUMMARY & EVIDENCE RECORDING
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("TEST SUMMARY:")
    all_passed = True
    for name, passed in test_results:
        status_str = "PASS [OK]" if passed else "FAIL [X]"
        print(f"  - {name.ljust(48)}: {status_str}")
        if not passed:
            all_passed = False

    print("=" * 70)
    print(f"OVERALL RESULT: {'ALL TESTS PASSED (6/6)' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 70)

    # Save test evidence JSON
    evidence_file = Path(__file__).parent / "evidence" / "s3_03a_platform_capabilities_test_results.json"
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_file, "w", encoding="utf-8") as ef:
        json.dump({
            "test_suite": "S3-03A Supported Platform Capabilities and Frontend API Handoffs",
            "date": "2026-11-09",
            "overall_status": "SUCCESS" if all_passed else "FAILED",
            "tests": [
                {"name": name, "passed": passed} for name, passed in test_results
            ],
            "tools_summary": tools,
            "integrations_status": status_report,
            "computer_use_investigation": cu_report,
            "activity_status": activity_status
        }, ef, indent=2)
    print(f"Saved test evidence to: {evidence_file}")
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
