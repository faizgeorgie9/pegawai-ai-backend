"""
platform_adapters.py - Supported Platform Capabilities & Integration Adapters
Sprint 3 Day 3 (November 9, 2026) - Intern 1 (Backend & Platform Lead)

Features:
- Tools/Plugins Registry and Agent Tool Assignment (Working local tools vs Mocked vs Unsupported)
- Integration Connection State Monitor (Hermes, DeepSeek, Meta WA, Shopee, Instagram)
- Computer Use Capability Investigation (Explicit Unsupported State & Rationale)
- Scheduler Prototype Job Management (Listing, Creation, Pause/Resume with safe dummy jobs)
- Activity & Execution Status Lifecycle Tracker (Runs, tokens, latency, status)
"""

import os
import sys
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Local dependencies
try:
    from agent_manager import agent_registry
except ImportError:
    try:
        from local_setup.backend_template.agent_manager import agent_registry
    except Exception:
        agent_registry = None

HERMES_BIN = os.path.expandvars(r"%LOCALAPPDATA%\hermes\bin\hermes.exe")

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {
            "tool_banner_generator": {
                "id": "tool_banner_generator",
                "name": "Local Banner & Image Generator",
                "category": "creative",
                "status": "working",
                "type": "local_python_pillow",
                "description": "Generates 1200x630 promotional banner graphics locally using Pillow.",
                "safe_mode": True,
                "version": "1.0.0"
            },
            "tool_knowledge_retriever": {
                "id": "tool_knowledge_retriever",
                "name": "Colorbox Knowledge & SOP Retriever",
                "category": "knowledge",
                "status": "working",
                "type": "local_file_index",
                "description": "Searches versioned Colorbox brand guidelines and CS SOPs with source citations.",
                "safe_mode": True,
                "version": "1.0.0"
            },
            "tool_content_planner": {
                "id": "tool_content_planner",
                "name": "AIDA Content & Calendar Planner",
                "category": "marketing",
                "status": "working",
                "type": "prompt_template",
                "description": "Structures campaign briefs into AIDA marketing copy and publication calendars.",
                "safe_mode": True,
                "version": "1.0.0"
            },
            "plugin_meta_whatsapp": {
                "id": "plugin_meta_whatsapp",
                "name": "Meta WhatsApp Business Cloud API",
                "category": "channel_messaging",
                "status": "mocked",
                "type": "external_webhook",
                "description": "Two-way WhatsApp messaging. In simulation sandbox; live Meta credentials omitted.",
                "safe_mode": True,
                "version": "0.9.0-sandbox"
            },
            "plugin_shopee_mall_erp": {
                "id": "plugin_shopee_mall_erp",
                "name": "Shopee Mall Order & Inventory Sync",
                "category": "ecommerce",
                "status": "unsupported",
                "type": "external_api",
                "description": "Direct ERP integration to live marketplace inventory. Out of prototype scope.",
                "safe_mode": False,
                "version": "N/A"
            },
            "plugin_instagram_graph": {
                "id": "plugin_instagram_graph",
                "name": "Instagram Graph API Auto-Publish",
                "category": "social_publishing",
                "status": "unsupported",
                "type": "external_oauth",
                "description": "Automatic posting to Instagram account. Prohibited by Human-in-the-Loop policy.",
                "safe_mode": False,
                "version": "N/A"
            }
        }

    def list_tools(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        tools_list = list(self.tools.values())
        if status:
            tools_list = [t for t in tools_list if t.get("status") == status]
        return tools_list

    def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        return self.tools.get(tool_id)

    def assign_tool(self, agent_id: str, tool_id: str) -> Tuple[bool, str]:
        if tool_id not in self.tools:
            return False, f"Tool with identifier '{tool_id}' is not registered."
        tool = self.tools[tool_id]
        if tool["status"] == "unsupported":
            return False, f"Tool '{tool_id}' is unsupported and cannot be assigned to agents."

        if agent_registry:
            agent, err = agent_registry.get_agent(agent_id)
            if err:
                return False, err
            tools = agent.get("tools_assigned", [])
            if tool_id not in tools:
                tools.append(tool_id)
                agent_registry.update_agent(agent_id, {"tools_assigned": tools})
            return True, f"Tool '{tool['name']}' successfully assigned to agent '{agent_id}'."
        return False, "Agent registry unavailable."


class IntegrationMonitor:
    def __init__(self):
        pass

    def get_status(self) -> Dict[str, Any]:
        """Inspects connection states across all platform integrations."""
        hermes_exists = os.path.exists(HERMES_BIN)
        has_deepseek_key = bool(
            os.environ.get("OPENCODE_ZEN_API_KEY") or
            os.environ.get("OPENCODE_API_KEY") or
            os.environ.get("DEEPSEEK_API_KEY")
        )

        integrations = {
            "hermes_agent_cli": {
                "name": "Hermes Agent Local Binary",
                "status": "connected" if hermes_exists else "blocked",
                "version": "v0.22.2+3291.gbf0203a",
                "verified": hermes_exists,
                "detail": HERMES_BIN if hermes_exists else "Binary not found at specified path"
            },
            "deepseek_v4_1_flash": {
                "name": "DeepSeek V4.1 Flash (Inference Provider)",
                "status": "connected" if has_deepseek_key else "blocked",
                "provider": "opencode" if os.environ.get("OPENCODE_ZEN_API_KEY") else "deepseek",
                "verified": has_deepseek_key,
                "detail": "Opencode Zen API Key Active" if has_deepseek_key else "Missing API Key"
            },
            "whatsapp_business_simulation": {
                "name": "WhatsApp Simulation Gateway",
                "status": "mocked",
                "verified": False,
                "detail": "Synthetic customer messages routed locally without live Meta charges."
            },
            "email_outbound_simulation": {
                "name": "Email Proposal Outbound Gateway",
                "status": "mocked",
                "verified": False,
                "detail": "Draft proposal preview generated locally without live SMTP relay."
            },
            "shopee_mall_erp": {
                "name": "Shopee Mall Order/Inventory Live Access",
                "status": "unsupported",
                "verified": False,
                "detail": "Strict boundary: Live ERP/Order DB connections are disabled for safety."
            },
            "instagram_graph_api": {
                "name": "Instagram Direct Auto-Publishing",
                "status": "unsupported",
                "verified": False,
                "detail": "Strict boundary: All marketing outputs require Human-in-the-Loop review."
            }
        }

        # Calculate counts
        counts = {"connected": 0, "mocked": 0, "unsupported": 0, "blocked": 0}
        for item in integrations.values():
            st = item.get("status", "unsupported")
            counts[st] = counts.get(st, 0) + 1

        return {
            "status": "success",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "summary": counts,
            "integrations": integrations
        }


class ComputerUseCapability:
    @staticmethod
    def get_capability_report() -> Dict[str, Any]:
        """Provides official investigation findings on Computer Use for Hermes."""
        return {
            "status": "unsupported",
            "supported": False,
            "capability": "os_desktop_computer_use",
            "platform_runtime": "Hermes Agent CLI v0.22.2 on Windows x64",
            "investigation_findings": {
                "is_available_in_cli": False,
                "reason": "Hermes Agent CLI operates as a text-first subprocess engine without native OS mouse/keyboard coordinate interaction drivers on Windows.",
                "business_relevance": "NOT_REQUIRED. Colorbox Fashion AI Employees operate strictly on marketing copywriting, graphic banner asset generation, and CS text inquiries.",
                "security_boundary": "Prevented unapproved OS-level desktop automation to maintain sandboxed execution controls."
            },
            "safe_prototype_action": "EXCLUDED_FROM_PRODUCTION_GATE"
        }


class SchedulerService:
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {
            "job_cbx_mkt_weekly": {
                "job_id": "job_cbx_mkt_weekly",
                "name": "Weekly Colorbox Marketing Campaign Draft",
                "cron_expression": "0 8 * * 1",  # Every Monday at 08:00 WIB
                "target_agent": "ag_cbx_marketing_01",
                "task_payload": {
                    "brief": "Weekly Trend & OOTD Inspiration for Gen-Z Teenagers",
                    "content_type": "instagram_carousel"
                },
                "status": "active",
                "safe_mode": True,
                "last_run": "2026-11-03T08:00:00Z",
                "next_run": "2026-11-10T08:00:00Z"
            },
            "job_cbx_cs_sla_audit": {
                "job_id": "job_cbx_cs_sla_audit",
                "name": "Daily Return SLA & Escalation Audit Check",
                "cron_expression": "0 18 * * *",  # Every day at 18:00 WIB
                "target_agent": "ag_cbx_cs_01",
                "task_payload": {
                    "audit_type": "7_day_return_policy_compliance"
                },
                "status": "active",
                "safe_mode": True,
                "last_run": "2026-11-05T18:00:00Z",
                "next_run": "2026-11-06T18:00:00Z"
            }
        }

    def list_jobs(self) -> List[Dict[str, Any]]:
        return list(self.jobs.values())

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)

    def create_job(self, data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        name = data.get("name", "").strip()
        cron = data.get("cron_expression", "").strip()
        target_agent = data.get("target_agent", "ag_cbx_marketing_01")

        if not name:
            return None, "Field 'name' is mandatory."
        if not cron:
            return None, "Field 'cron_expression' is mandatory."

        job_id = data.get("job_id") or f"job_cbx_{int(time.time()) % 10000}"
        if job_id in self.jobs:
            return None, f"Job with ID '{job_id}' already exists."

        new_job = {
            "job_id": job_id,
            "name": name,
            "cron_expression": cron,
            "target_agent": target_agent,
            "task_payload": data.get("task_payload", {}),
            "status": "active",
            "safe_mode": True,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "last_run": None,
            "next_run": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        self.jobs[job_id] = new_job
        return new_job, None

    def update_job_status(self, job_id: str, new_status: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        if job_id not in self.jobs:
            return None, f"Job with ID '{job_id}' was not found."
        if new_status not in ["active", "paused", "disabled"]:
            return None, f"Invalid status '{new_status}'. Allowed: ['active', 'paused', 'disabled']"

        self.jobs[job_id]["status"] = new_status
        self.jobs[job_id]["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        return self.jobs[job_id], None


class ActivityTracker:
    def __init__(self, max_records: int = 50):
        self.max_records = max_records
        self.runs: List[Dict[str, Any]] = []

    def record_run(self, run_id: str, agent_id: str, workflow: str, duration_sec: float, tokens: int, status: str = "completed", error: Optional[str] = None):
        entry = {
            "run_id": run_id,
            "agent_id": agent_id,
            "workflow": workflow,
            "duration_sec": duration_sec,
            "tokens": tokens,
            "status": status,
            "error": error,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        self.runs.insert(0, entry)
        if len(self.runs) > self.max_records:
            self.runs = self.runs[:self.max_records]

    def get_activity_status(self) -> Dict[str, Any]:
        total_runs = len(self.runs)
        successful_runs = len([r for r in self.runs if r["status"] == "completed"])
        failed_runs = len([r for r in self.runs if r["status"] == "failed"])
        total_tokens = sum(r.get("tokens", 0) for r in self.runs)
        avg_duration = round(sum(r.get("duration_sec", 0.0) for r in self.runs) / max(total_runs, 1), 2)

        return {
            "status": "success",
            "server_status": "healthy",
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "total_tokens_consumed": total_tokens,
            "average_latency_sec": avg_duration,
            "recent_runs": self.runs[:10]
        }


# Global singleton instances
tool_registry = ToolRegistry()
integration_monitor = IntegrationMonitor()
computer_use_inspector = ComputerUseCapability()
scheduler_service = SchedulerService()
activity_tracker = ActivityTracker()

# Seed an initial activity run so dashboard has data
activity_tracker.record_run(
    run_id="run_cbx_seed_001",
    agent_id="ag_cbx_marketing_01",
    workflow="colorbox_marketing_v1",
    duration_sec=38.45,
    tokens=1810,
    status="completed"
)

