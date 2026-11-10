"""
test_e2e_final_validation.py - Master End-to-End Testing & Readiness Validation Suite
Sprint 3 Day 4 (November 10, 2026) - Intern 1 (Backend & Platform Lead)

Covers all 7 validation categories for Final Demonstration Gate:
- Category A: Agent Management CRUD Lifecycle (List, Create, View, Update, Errors)
- Category B: Knowledge Loading, Grounding & Truthful Missing Data Behavior
- Category C: Colorbox Marketing 5-Stage Structured Workflow Execution
- Category D: Colorbox Customer Service 2-Turn Context & Complaint Simulation
- Category E: Chat Session Context Continuity & Reset Semantics
- Category F: Supported Platform Capability Adapters (Tools, Integrations, Scheduler, Activity)
- Category G: Controlled Error Semantics & Zero Credential Leakage
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

# Load environment and set fast test flag for reliable regression execution
from server import load_env_file
load_env_file()
os.environ["FAST_CONTRACT_TEST"] = "1"

from agent_manager import AgentManager
from knowledge_retriever import KnowledgeRetriever
from chat_orchestrator import ChatOrchestrator
from platform_adapters import (
    tool_registry,
    integration_monitor,
    computer_use_inspector,
    scheduler_service,
    activity_tracker
)

def run_master_validation():
    print("=" * 80)
    print("SPRINT 3 DAY 4: MASTER FINAL BACKEND VALIDATION & READINESS TEST (S3-04A)")
    print("=" * 80)
    start_time = time.time()

    agent_mgr = AgentManager()
    knowledge_eng = KnowledgeRetriever()
    orchestrator = ChatOrchestrator()

    categories_results = {}
    total_checks = 0
    passed_checks = 0

    # --------------------------------------------------------------------------
    # CATEGORY A: Agent Management CRUD Lifecycle
    # --------------------------------------------------------------------------
    print("\n[CATEGORY A] Testing Agent Management CRUD Lifecycle...")
    a_results = []
    
    # A1: List
    agents = agent_mgr.list_agents()
    pass_a1 = len(agents) >= 2 and any(a["id"] == "ag_cbx_marketing_01" for a in agents)
    a_results.append(("Agent List (GET /agents)", pass_a1))

    # A2: Create
    new_agent_data = {
        "id": "ag_cbx_validation_temp",
        "name": "Colorbox Brand Quality Evaluator",
        "department": "marketing",
        "role": "Brand Quality Assurance Specialist",
        "tone": "grounded_persuasive",
        "max_tokens": 2000
    }
    created_ag, err_create = agent_mgr.create_agent(new_agent_data)
    pass_a2 = created_ag is not None and created_ag["id"] == "ag_cbx_validation_temp"
    a_results.append(("Agent Create (POST /agents)", pass_a2))

    # A3: View
    viewed_ag, err_view = agent_mgr.get_agent("ag_cbx_validation_temp")
    pass_a3 = viewed_ag is not None and viewed_ag["role"] == "Brand Quality Assurance Specialist"
    a_results.append(("Agent View Detail (GET /agents/{id})", pass_a3))

    # A4: Update
    updated_ag, err_up = agent_mgr.update_agent("ag_cbx_validation_temp", {"max_tokens": 2800, "tone": "cheerful_genz"})
    pass_a4 = updated_ag is not None and updated_ag["max_tokens"] == 2800 and updated_ag["tone"] == "cheerful_genz"
    a_results.append(("Agent Update (PUT /agents/{id})", pass_a4))

    # A5: Unknown agent error
    _, err_unknown = agent_mgr.get_agent("ag_non_existent_999")
    pass_a5 = "not found" in err_unknown.lower()
    a_results.append(("Unknown Agent Error Handling (404)", pass_a5))

    # Clean up temp agent
    if "ag_cbx_validation_temp" in agent_mgr.agents:
        del agent_mgr.agents["ag_cbx_validation_temp"]
        agent_mgr.save()

    categories_results["Category A: Agent Management CRUD"] = a_results

    # --------------------------------------------------------------------------
    # CATEGORY B: Knowledge Loading & Grounded Retrieval
    # --------------------------------------------------------------------------
    print("\n[CATEGORY B] Testing Knowledge Loading & Grounded Retrieval...")
    b_results = []

    # B1: Registry verification
    reg_keys = list(knowledge_eng.registry.keys())
    pass_b1 = (
        "shared_brand_knowledge_v1" in reg_keys and
        "colorbox_marketing_knowledge_v1" in reg_keys and
        "colorbox_cs_sop_v1" in reg_keys
    )
    b_results.append(("Versioned Knowledge Ingestion (3 files)", pass_b1))

    # B2: Grounded CS Retrieval
    cs_hit = knowledge_eng.retrieve("tukar ukuran celana kebesaran", department="cs")
    pass_b2 = cs_hit["status"] == "KNOWLEDGE_FOUND" and "SOP-CBX-RET-01" in str(cs_hit["results"])
    b_results.append(("Grounded CS Policy Retrieval (SOP-CBX-RET-01)", pass_b2))

    # B3: Truthful Missing Data Behavior
    missing_hit = knowledge_eng.retrieve("layanan perbaikan knalpot dan ganti oli mesin motor", department="cs")
    pass_b3 = (
        missing_hit["status"] == "KNOWLEDGE_ABSENT" and
        missing_hit["grounded"] is False and
        missing_hit["fallback_action"] == "ESCALATE_TO_SUPERVISOR"
    )
    b_results.append(("Truthful Missing Data Behavior (Zero Hallucination)", pass_b3))

    # B4: Department Isolation
    mkt_text = knowledge_eng.get_agent_knowledge("marketing")
    cs_text = knowledge_eng.get_agent_knowledge("cs")
    pass_b4 = "SOP-CBX-ESC-04" not in mkt_text and "MKT-PIL-01" not in cs_text
    b_results.append(("Strict Departmental Knowledge Isolation", pass_b4))

    categories_results["Category B: Knowledge Retrieval Engine"] = b_results

    # --------------------------------------------------------------------------
    # CATEGORY C: Colorbox Marketing 5-Stage Structured Workflow
    # --------------------------------------------------------------------------
    print("\n[CATEGORY C] Testing Colorbox Marketing 5-Stage Workflow...")
    c_results = []
    brief = "Koleksi Pastel Chic Musim Panas untuk Remaja Gen-Z"
    mkt_exec = orchestrator.execute_marketing_workflow(brief, content_type="instagram_carousel")

    mkt_data = mkt_exec.get("data", {})
    pass_c1 = mkt_exec["status"] == "success" and mkt_exec["workflow"] == "colorbox_marketing_v1"
    pass_c2 = "planning" in mkt_data and mkt_data["planning"]["content_pillar"] is not None
    pass_c3 = "generation" in mkt_data and len(mkt_data["generation"]["hashtags"]) >= 2
    pass_c4 = "brand_review" in mkt_data and mkt_data["brand_review"]["compliance_score"] >= 80
    pass_c5 = "visual_concept" in mkt_data and len(mkt_data["visual_concept"]["color_palette"]) >= 2

    c_results.append(("Marketing Execution Success Status", pass_c1))
    c_results.append(("Stage 1 Planning Schema Conformance", pass_c2))
    c_results.append(("Stage 2 & 3 Generation & Alternatives Schema", pass_c3))
    c_results.append(("Stage 4 Brand Review & Score Compliance", pass_c4))
    c_results.append(("Stage 5 Visual Concept & Color Palette", pass_c5))

    categories_results["Category C: Marketing Structured Workflow"] = c_results

    # --------------------------------------------------------------------------
    # CATEGORY D: Colorbox Customer Service 2-Turn Context & Complaint
    # --------------------------------------------------------------------------
    print("\n[CATEGORY D] Testing CS 2-Turn Context & Complaint Simulation...")
    d_results = []
    cs_sess = f"sess_e2e_master_{int(time.time())}"

    # Turn 1
    t1_res = orchestrator.execute_cs_chat(
        session_id=cs_sess,
        message="Kak mau tanya cara tukar baju yang ukurannya kekecilan",
        customer_name="Siti"
    )
    pass_d1 = t1_res["status"] == "success" and t1_res["turn_number"] == 1 and t1_res["classification"]["intent"] == "SIZE_EXCHANGE"
    d_results.append(("CS Turn 1 Inquiry Classification & Grounding", pass_d1))

    # Turn 2
    t2_res = orchestrator.execute_cs_chat(
        session_id=cs_sess,
        message="Nomor pesanan saya #CBX-2026-9812 baru dibeli kemarin di store PIM, struk dan tag masih ada.",
        customer_name="Siti"
    )
    pass_d2 = t2_res["status"] == "success" and t2_res["turn_number"] == 2 and "ticket_management" in t2_res
    d_results.append(("CS Turn 2 Context Retention & Grounded Resolution", pass_d2))

    # Critical Complaint Escalation
    crit_sess = f"sess_crit_master_{int(time.time())}"
    crit_res = orchestrator.execute_cs_chat(
        session_id=crit_sess,
        message="Barang cacat parah! Saya mau viralkan ke TikTok sekarang juga!",
        customer_name="Anita"
    )
    pass_d3 = (
        crit_res["ticket_management"]["priority"] == "CRITICAL" and
        crit_res["ticket_management"]["requires_human_escalation"] is True
    )
    d_results.append(("CS High-Risk Complaint Auto-Escalation", pass_d3))

    categories_results["Category D: Customer Service Multi-Turn"] = d_results

    # --------------------------------------------------------------------------
    # CATEGORY E: Chat Session Context Continuity & Reset Semantics
    # --------------------------------------------------------------------------
    print("\n[CATEGORY E] Testing Session Reset Semantics...")
    e_results = []

    # Reset existing session
    reset_ok = orchestrator.sessions.reset_session(cs_sess)
    history_after_reset = len(orchestrator.sessions.get_session(cs_sess)["history"])

    # Subsequent message must start fresh at turn 1
    fresh_turn = orchestrator.execute_cs_chat(
        session_id=cs_sess,
        message="Halo selamat sore min",
        customer_name="Siti"
    )
    pass_e1 = reset_ok and history_after_reset == 0 and fresh_turn["turn_number"] == 1
    e_results.append(("Session Context Reset & Fresh Turn 1 Semantics", pass_e1))

    categories_results["Category E: Session Memory & Reset"] = e_results

    # --------------------------------------------------------------------------
    # CATEGORY F: Supported Platform Capability Adapters
    # --------------------------------------------------------------------------
    print("\n[CATEGORY F] Testing Platform Capability Adapters...")
    f_results = []

    # Tools
    tools = tool_registry.list_tools()
    pass_f1 = len(tools) >= 5 and any(t["id"] == "tool_banner_generator" and t["status"] == "working" for t in tools)
    f_results.append(("Tools Registry (Working Local Tools)", pass_f1))

    # Integrations
    int_status = integration_monitor.get_status()
    pass_f2 = (
        int_status["summary"]["connected"] >= 1 and
        int_status["summary"]["mocked"] >= 2 and
        int_status["summary"]["unsupported"] >= 2
    )
    f_results.append(("Integration States (Connected/Mocked/Unsupported)", pass_f2))

    # Computer Use
    cu_rep = computer_use_inspector.get_capability_report()
    pass_f3 = cu_rep["status"] == "unsupported" and cu_rep["supported"] is False
    f_results.append(("Computer Use Investigation & Safe Boundary", pass_f3))

    # Scheduler
    jobs = scheduler_service.list_jobs()
    pass_f4 = len(jobs) >= 2 and any(j["job_id"] == "job_cbx_mkt_weekly" for j in jobs)
    f_results.append(("Scheduler Job Management (Safe Dummy Prototype)", pass_f4))

    # Activity
    act_status = activity_tracker.get_activity_status()
    pass_f5 = act_status["status"] == "success" and act_status["total_runs"] >= 1
    f_results.append(("Activity Status & Execution Lifecycle Metrics", pass_f5))

    categories_results["Category F: Platform Capability Adapters"] = f_results

    # --------------------------------------------------------------------------
    # CATEGORY G: Controlled Error Semantics & Zero Credential Leakage
    # --------------------------------------------------------------------------
    print("\n[CATEGORY G] Testing Security, Validation & Controlled Errors...")
    g_results = []

    # Missing name error
    _, err_bad_create = agent_mgr.create_agent({"department": "marketing"})
    pass_g1 = "mandatory" in err_bad_create.lower()
    g_results.append(("Missing Field Validation Error (400)", pass_g1))

    # Invalid department error
    _, err_bad_dept = agent_mgr.create_agent({"name": "Test", "department": "space_crypto"})
    pass_g2 = "invalid department" in err_bad_dept.lower()
    g_results.append(("Illegal Department Validation Error (400)", pass_g2))

    # Zero secret leak
    all_dumps = json.dumps([mkt_exec, t1_res, t2_res, crit_res, int_status, cu_rep])
    pass_g3 = not any(k in all_dumps for k in ["sk-", "oc_sk_", "password", "PEGAWAI_AI_SECRET_KEY"])
    g_results.append(("Zero Credential Leakage in Output Payloads", pass_g3))

    categories_results["Category G: Security & Error Handling"] = g_results

    # --------------------------------------------------------------------------
    # MASTER SCORECARD & EVIDENCE EXPORT
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("FINAL BACKEND VALIDATION MASTER SCORECARD:")
    print("=" * 80)

    overall_pass = True
    for cat_name, tests in categories_results.items():
        print(f"\n{cat_name}:")
        for test_name, passed in tests:
            total_checks += 1
            if passed:
                passed_checks += 1
            status_text = "PASS [OK]" if passed else "FAIL [X]"
            print(f"  - {test_name.ljust(54)}: {status_text}")
            if not passed:
                overall_pass = False

    elapsed_total = round(time.time() - start_time, 2)
    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed_checks}/{total_checks} CHECKS PASSED ({round(passed_checks/total_checks*100, 1)}%) in {elapsed_total}s")
    print(f"FINAL TECHNICAL READINESS DECISION: {'READY FOR R&D DEMONSTRATION' if overall_pass else 'NOT READY / REVISIONS REQUIRED'}")
    print("=" * 80)

    evidence_file = Path(__file__).parent / "evidence" / "s3_04a_final_e2e_validation_results.json"
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_file, "w", encoding="utf-8") as ef:
        json.dump({
            "validation_suite": "S3-04A Final Master Backend Testing and Validation",
            "date": "2026-11-10",
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "pass_rate_pct": round(passed_checks/total_checks*100, 1),
            "technical_readiness": "READY" if overall_pass else "NOT_READY",
            "categories": categories_results,
            "runtime_reference": {
                "hermes_version": "v0.22.2+3291.gbf0203a",
                "target_model": "deepseek-v4.1-flash",
                "provider": "opencode"
            },
            "sample_traces": {
                "marketing": mkt_exec,
                "cs_turn_1": t1_res,
                "cs_turn_2": t2_res,
                "cs_critical_escalation": crit_res,
                "integrations_status": int_status
            }
        }, ef, indent=2)

    print(f"Master evidence archived at: {evidence_file}")
    return overall_pass

if __name__ == "__main__":
    success = run_master_validation()
    sys.exit(0 if success else 1)

