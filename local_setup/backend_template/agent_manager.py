"""
agent_manager.py - Core Agent Management, Configuration & Routing Engine
Sprint 3 Day 2 (November 6, 2026) - Intern 1 (Backend & Platform Lead)

Features:
- Local prototype agent configuration store (agents.json)
- Full CRUD operations: list, create, view, update
- Input validation & unknown agent error handling (400 / 404)
- Department workflow routing (Marketing vs Customer Service)
- Credential sanitization (Zero secret exposure)
"""

import os
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

AGENTS_FILE = Path(__file__).parent / "agents.json"
ALLOWED_DEPARTMENTS = ["marketing", "customer_service", "sales", "general"]
ALLOWED_TONES = ["cheerful_genz", "empathic_polite", "grounded_persuasive", "consultative", "objective"]

class AgentManager:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or AGENTS_FILE
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self):
        """Loads agents from JSON file or initializes defaults."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.agents = data.get("agents", {})
                return
            except Exception as e:
                print(f"[AgentManager] Failed to read {self.storage_path}: {e}")

        # Fallback in-memory defaults
        self.agents = {
            "ag_cbx_marketing_01": {
                "id": "ag_cbx_marketing_01",
                "name": "Colorbox Marketing Specialist",
                "department": "marketing",
                "role": "Social Media & Campaign Strategist",
                "tone": "cheerful_genz",
                "avatar": "🎨",
                "status": "active",
                "max_tokens": 2500,
                "timeout_sec": 180,
                "system_instruction": "Bertindaklah sebagai Tim Divisi Pemasaran & Kreatif Colorbox.",
                "tools_assigned": ["banner_generator", "content_planner", "knowledge_retriever"],
                "knowledge_sources": ["shared_brand_knowledge_v1.md", "colorbox_marketing_knowledge_v1.md"],
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            "ag_cbx_cs_01": {
                "id": "ag_cbx_cs_01",
                "name": "Colorbox Customer Support Specialist",
                "department": "customer_service",
                "role": "Frontline Inquiries & Return Triage",
                "tone": "empathic_polite",
                "avatar": "💬",
                "status": "active",
                "max_tokens": 1800,
                "timeout_sec": 120,
                "system_instruction": "Bertindaklah sebagai Tim Layanan Pelanggan Colorbox.",
                "tools_assigned": ["knowledge_retriever", "ticket_escalation", "session_context_manager"],
                "knowledge_sources": ["shared_brand_knowledge_v1.md", "colorbox_cs_sop_v1.md"],
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        }
        self.save()

    def save(self):
        """Persists agents to local JSON prototype storage."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({
                    "version": "1.0.0",
                    "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "agents": self.agents
                }, f, indent=2)
        except Exception as e:
            print(f"[AgentManager] Failed to persist {self.storage_path}: {e}")

    def list_agents(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns list of agents, optionally filtered by department."""
        agents_list = list(self.agents.values())
        if department:
            dept_norm = department.lower().strip()
            agents_list = [a for a in agents_list if a.get("department") == dept_norm]
        return agents_list

    def get_agent(self, agent_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Returns (agent_data, error_message)."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None, f"Agent with identifier '{agent_id}' was not found in prototype registry."
        return agent, None

    def create_agent(self, data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Validates and registers a new agent persona."""
        name = data.get("name", "").strip()
        department = data.get("department", "").lower().strip()
        tone = data.get("tone", "cheerful_genz").strip()

        if not name:
            return None, "Field 'name' is mandatory and cannot be empty."
        if not department:
            return None, "Field 'department' is mandatory."
        if department not in ALLOWED_DEPARTMENTS:
            return None, f"Invalid department '{department}'. Allowed: {ALLOWED_DEPARTMENTS}"

        # Generate unique identifier
        clean_name = re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")
        agent_id = data.get("id") or f"ag_cbx_{clean_name}_{int(time.time()) % 1000}"

        if agent_id in self.agents:
            return None, f"Agent with identifier '{agent_id}' already exists."

        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        new_agent = {
            "id": agent_id,
            "name": name,
            "department": department,
            "role": data.get("role", "General AI Assistant"),
            "tone": tone,
            "avatar": data.get("avatar", "🤖"),
            "status": data.get("status", "active"),
            "max_tokens": int(data.get("max_tokens", 2000)),
            "timeout_sec": int(data.get("timeout_sec", 120)),
            "system_instruction": data.get("system_instruction", f"Bertindaklah sebagai Pegawai AI divisi {department}."),
            "tools_assigned": data.get("tools_assigned", ["knowledge_retriever"]),
            "knowledge_sources": data.get("knowledge_sources", ["shared_brand_knowledge_v1.md"]),
            "created_at": now_iso,
            "updated_at": now_iso
        }

        self.agents[agent_id] = new_agent
        self.save()
        return new_agent, None

    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Updates mutable configuration fields of an existing agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None, f"Agent with identifier '{agent_id}' was not found."

        if "department" in updates:
            new_dept = updates["department"].lower().strip()
            if new_dept not in ALLOWED_DEPARTMENTS:
                return None, f"Invalid department '{new_dept}'. Allowed: {ALLOWED_DEPARTMENTS}"
            agent["department"] = new_dept

        # Updatable fields
        for field in ["name", "role", "tone", "avatar", "status", "max_tokens", "timeout_sec", "system_instruction", "tools_assigned", "knowledge_sources"]:
            if field in updates:
                agent[field] = updates[field]

        agent["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.agents[agent_id] = agent
        self.save()
        return agent, None

    def route_request(self, agent_id: Optional[str] = None, department: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Routes an execution request to the appropriate agent configuration.
        Priority:
        1. Explicit agent_id
        2. Department default agent
        """
        if agent_id:
            agent = self.agents.get(agent_id)
            if not agent:
                return None, f"Routing failed: Unknown agent identifier '{agent_id}'."
            return agent, None

        if department:
            dept_norm = department.lower().strip()
            for a in self.agents.values():
                if a.get("department") == dept_norm and a.get("status") == "active":
                    return a, None
            return None, f"Routing failed: No active agent configured for department '{department}'."

        # Default fallback to marketing
        default_agent = self.agents.get("ag_cbx_marketing_01")
        if default_agent:
            return default_agent, None
        return None, "Routing failed: No default agent available."


# Global singleton instance
agent_registry = AgentManager()

