"""Master AI Employee Template Architecture, Hermes Configuration Mapping,
and Unified Model/Skill/Tool/Permission Management (Sprint 5 Day 3).

Aligned with Frontend (Kevin) and Master Template v1.0 Framework:
- Fixed Immutable Agent Engine (SOUL.md, SKILL.md, ROLE.md)
- Pluggable Dynamic Client Context ({{brand_name}}, {{industry}}, etc.)
- Hermes Native Mapping vs Documented Architecture Gaps (user.md, agents.md)
- Unified Permissions (Model, Reasoning Effort, FastMCP Tier, KB Isolation)
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config, db, harden, hermes, kb, mcp_privileges, settings
from .errors import ApiError

log = logging.getLogger("bff.master_template")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POSSIBLE_TEMPLATE_DIRS = [
    PROJECT_ROOT / "templates" / "agents",
    Path(__file__).resolve().parents[1] / "templates" / "agents",
    Path("/home/ubuntu/pegawai-ai/templates/agents"),
    Path("/home/ubuntu/pegawai-ai/bff/templates/agents"),
]

def get_template_root() -> Path:
    for p in POSSIBLE_TEMPLATE_DIRS:
        if p.is_dir():
            return p
    return POSSIBLE_TEMPLATE_DIRS[0]

# ==============================================================================
# 1. HERMES FILE CONFIGURATION MECHANISM & GAP ALIGNMENT
# ==============================================================================

HERMES_CONFIG_SPEC = {
    "framework": "Hermes Agent CLI & Gateway",
    "version": "53",
    "profile_base_path": "~/.hermes/profiles/{bot_id}",
    "supported_native_files": {
        "config.yaml": {
            "status": "supported_native",
            "description": "Profile configuration: model selection, provider, reasoning effort, toolsets hardening (DENY list), approvals mode, display platforms.",
            "source_of_truth": "Backend DB (bots + settings) compiled to profile config.yaml",
            "client_editable_keys": ["model", "provider", "reasoning_effort", "approvals.mode"],
            "protected_core_keys": ["database", "runtime", "toolsets", "display"]
        },
        ".env": {
            "status": "supported_native",
            "description": "Environment variables, profile API server key (API_SERVER_KEY), and provider credentials.",
            "source_of_truth": "System provisioning & secrets manager (never exposed to client or logged)",
            "client_editable": False
        },
        "SOUL.md": {
            "status": "supported_native",
            "description": "Agent persona, tone of voice, professional character, zero-hallucination mandate, and compliance limits.",
            "source_of_truth": "Master Template SOUL.md with dynamic client variables injected at onboarding/runtime",
            "client_editable": "Dynamic variable slots only; core ethical and safety rules remain locked"
        },
        "skills/": {
            "status": "supported_native",
            "description": "Modular skill directories containing SKILL.md and executable action scripts.",
            "source_of_truth": "Master Template SKILL.md mapped to FastMCP tools & Hermes skill manifests",
            "client_editable": False
        },
        "state.db": {
            "status": "supported_native",
            "description": "Hermes SQLite runtime state for session events, turn history, and tool execution status.",
            "source_of_truth": "Hermes internal runtime engine",
            "client_editable": False
        }
    },
    "documented_architecture_gaps": {
        "user.md": {
            "status": "unsupported_gap",
            "reason": "Hermes CLI does not natively parse a standalone 'user.md' file per profile. User context, preferences, and company settings are injected into system prompts by BFF middleware or passed in session start requests.",
            "mitigation": "BFF acts as source-of-truth; injects user context directly into Hermes session instructions."
        },
        "agents.md": {
            "status": "unsupported_gap",
            "reason": "Hermes CLI uses filesystem-isolated profile directories (~/.hermes/profiles/<id>) rather than an in-profile 'agents.md' orchestrator file. Group chat orchestration and agent handoffs are coordinated by BFF engine (groups.py & engine.py).",
            "mitigation": "BFF coordinates multi-agent group execution and state tracking; individual agents remain pure single-profile Hermes instances."
        }
    }
}

# ==============================================================================
# 2. MASTER ROLE CATALOG DEFINITIONS
# ==============================================================================

MASTER_ROLES: Dict[str, Dict[str, Any]] = {
    "CRE-01": {
        "id": "CRE-01",
        "folder_name": "CRE-01_Content_Strategist",
        "code": "MKT-STRAT",
        "name": "Content Strategist & Omnichannel Lead",
        "alias": "bimo",
        "team": "marketing",
        "division": "Content & Creative",
        "icon": "compass",
        "color": "indigo",
        "description": "Merancang arah pilar konten, riset audiens, dan perencanaan kalender editorial multi-platform terpadu.",
        "default_model": "deepseek/deepseek-chat",
        "default_provider": "deepseek",
        "default_reasoning_effort": "medium",
        "mcp_tier": "WRITE",
        "allowed_kb": ["marketing", "catalog", "general"],
        "denied_kb": ["finance", "hr", "legal", "cs"],
        "approvals_mode": "manual",
        "dynamic_variables": [
            "brand_name", "industry", "target_audience", "content_pillars",
            "knowledge_catalog", "official_cta", "official_hashtag", "tone_of_voice"
        ]
    },
    "CRE-02": {
        "id": "CRE-02",
        "folder_name": "CRE-02_Content_and_Copywriter",
        "code": "MKT-COPY",
        "name": "Content & Social Media Copywriter",
        "alias": "bram",
        "team": "marketing",
        "division": "Content & Creative",
        "icon": "pen-tool",
        "color": "sky",
        "description": "Menulis naskah konten persuasif, caption media sosial, hook retensi, dan deskripsi produk berorientasi konversi.",
        "default_model": "deepseek/deepseek-chat",
        "default_provider": "deepseek",
        "default_reasoning_effort": "low",
        "mcp_tier": "WRITE",
        "allowed_kb": ["marketing", "catalog", "general"],
        "denied_kb": ["finance", "hr", "legal", "cs"],
        "approvals_mode": "manual",
        "dynamic_variables": [
            "brand_name", "industry", "target_audience", "content_pillars",
            "knowledge_catalog", "official_cta", "official_hashtag", "tone_of_voice"
        ]
    },
    "CRE-03": {
        "id": "CRE-03",
        "folder_name": "CRE-03_Graphic_and_Motion_Designer",
        "code": "MKT-DESIGN",
        "name": "Graphic & Motion Visual Designer",
        "alias": "vina",
        "team": "marketing",
        "division": "Content & Creative",
        "icon": "image",
        "color": "rose",
        "description": "Merancang konsep visual, tata letak carousel, panduan safe-zone 4:5, dan prompt generator gambar berkualitas tinggi.",
        "default_model": "deepseek/deepseek-chat",
        "default_provider": "deepseek",
        "default_reasoning_effort": "low",
        "mcp_tier": "READ",
        "allowed_kb": ["marketing", "catalog", "general"],
        "denied_kb": ["finance", "hr", "legal", "cs"],
        "approvals_mode": "manual",
        "dynamic_variables": [
            "brand_name", "industry", "target_audience", "content_pillars",
            "knowledge_catalog", "official_cta", "official_hashtag"
        ]
    },
    "CRE-04": {
        "id": "CRE-04",
        "folder_name": "CRE-04_Video_and_UGC_Creator",
        "code": "MKT-VIDEO",
        "name": "Video & UGC Creative Specialist",
        "alias": "raka",
        "team": "marketing",
        "division": "Content & Creative",
        "icon": "video",
        "color": "amber",
        "description": "Menyusun storyboard video pendek (Reels/TikTok), naskah dialog UGC, ritme transisi, dan arahan visual audio.",
        "default_model": "deepseek/deepseek-chat",
        "default_provider": "deepseek",
        "default_reasoning_effort": "low",
        "mcp_tier": "READ",
        "allowed_kb": ["marketing", "catalog", "general"],
        "denied_kb": ["finance", "hr", "legal", "cs"],
        "approvals_mode": "manual",
        "dynamic_variables": [
            "brand_name", "industry", "target_audience", "content_pillars",
            "knowledge_catalog", "official_cta", "official_hashtag"
        ]
    },
    "CS-01": {
        "id": "CS-01",
        "folder_name": "CS-01_Omnichannel_Customer_Service",
        "code": "CS-FRONT",
        "name": "Omnichannel Frontline Support Specialist",
        "alias": "siti",
        "team": "cs",
        "division": "Customer Support",
        "icon": "message-circle",
        "color": "teal",
        "description": "Melayani pesan dan pertanyaan pelanggan via WhatsApp/Omnichannel dengan cepat, empatik, dan sesuai SOP resmi.",
        "default_model": "deepseek/deepseek-chat",
        "default_provider": "deepseek",
        "default_reasoning_effort": "medium",
        "mcp_tier": "READ",
        "allowed_kb": ["cs", "catalog", "general"],
        "denied_kb": ["finance", "hr", "legal", "marketing"],
        "approvals_mode": "auto",
        "dynamic_variables": [
            "brand_name", "industry", "target_audience", "knowledge_catalog",
            "tone_of_voice", "support_email", "shipping_sla", "return_policy_summary"
        ]
    },
    "CS-02": {
        "id": "CS-02",
        "folder_name": "CS-02_Customer_Service_Lead",
        "code": "CS-LEAD",
        "name": "CS Quality Auditor & Escalation Lead",
        "alias": "hendra",
        "team": "cs",
        "division": "Customer Support",
        "icon": "shield-check",
        "color": "green",
        "description": "Menangani komplain prioritas P1 (barang rusak/retur/refund), audit mutu balasan CS, dan koordinasi eskalasi manusia.",
        "default_model": "deepseek/deepseek-chat",
        "default_provider": "deepseek",
        "default_reasoning_effort": "high",
        "mcp_tier": "WRITE",
        "allowed_kb": ["cs", "catalog", "general"],
        "denied_kb": ["finance", "hr", "legal", "marketing"],
        "approvals_mode": "manual",
        "dynamic_variables": [
            "brand_name", "industry", "target_audience", "knowledge_catalog",
            "tone_of_voice", "support_email", "return_policy_summary"
        ]
    },
    "MGT-01": {
        "id": "MGT-01",
        "folder_name": "MGT-01_Project_Manager",
        "code": "MGT-LEAD",
        "name": "Workspace Project Manager & Supervisor",
        "alias": "bimo",
        "team": "management",
        "division": "Operations",
        "icon": "users",
        "color": "slate",
        "description": "Mengkoordinasi workflow multi-agen, mendelegasikan tugas harian, dan mengawasi target penyelesaian.",
        "default_model": "deepseek/deepseek-chat",
        "default_provider": "deepseek",
        "default_reasoning_effort": "high",
        "mcp_tier": "ADMIN",
        "allowed_kb": ["finance", "cs", "marketing", "catalog", "general", "hr", "legal"],
        "denied_kb": [],
        "approvals_mode": "manual",
        "dynamic_variables": [
            "brand_name", "industry", "workspace_goals", "team_members"
        ]
    }
}

# In-memory fallback templates if disk files are missing
FALLBACK_TEMPLATES = {
    "CS-01": {
        "soul": """# SOUL: Omnichannel Customer Service Specialist (CS-01)
Kamu adalah **Frontline Support Specialist** untuk `{{brand_name}}` di industri `{{industry}}`.
Kamu bertugas menyusun respons layanan pelanggan yang ramah, sopan, empatik, jelas, dan akurat.

## Aturan Utama (Zero Hallucination & Compliance)
1. **Grounded Knowledge:** Seluruh informasi produk, harga, dan ketentuan retur mengacu pada `{{knowledge_catalog}}`. Jangan pernah mengarang ketersediaan stok atau kebijakan baru.
2. **Kebijakan Retur 7 Hari:** Mengikuti ketentuan resmi maksimal 7 hari kalender. Tidak melayani penukaran ukuran (size exchange) langsung; arahkan refund dan beli ulang.
3. **Eskalasi Terarah:** Jika pelanggan komplain barang rusak atau meminta staf manusia, tawarkan bantuan dengan sopan dan aktifkan eskalasi ke tim terkait.
""",
        "skill": """# SKILL: Customer Support Workflow (CS-01)
1. Analisis pesan pelanggan dan deteksi intent utama.
2. Cek basis data pengetahuan resmi (Katalog & FAQ).
3. Susun draf jawaban ringkas dan bersahabat.
4. Sertakan tautan resmi jika relevan.
5. Bila komplain P1 terdeteksi, tawarkan penanganan lanjutan.
""",
        "role": """# ROLE SPECIFICATION: CS-01 Frontline Support
- Divisi: Customer Support
- KPI: Respon < 2 menit, kepuasan pelanggan > 90%, zero false policy claims.
- Batasan: Dilarang menjanjikan diskon mandiri atau memproses refund tanpa QC.
"""
    },
    "CS-02": {
        "soul": """# SOUL: CS Quality & Escalation Lead (CS-02)
Kamu adalah **Customer Service Team Lead & Quality Auditor** untuk `{{brand_name}}`.
Bertanggung jawab atas penyelesaian sengketa, komplain produk rusak/cacat, refund, dan jaminan mutu layanan.

## Prinsip Kerja
- Sikap tenang, solutif, adil, dan mengutamakan retensi pelanggan.
- Respons komplain dalam kurun waktu 1x24 jam kerja.
""",
        "skill": """# SKILL: Escalation & Quality Audit (CS-02)
1. Verifikasi nomor resi, foto bukti kerusakan, dan barcode tag.
2. Koordinasi dengan logistik & finance untuk instruksi refund/penggantian.
3. Evaluasi mutu draf jawaban agen frontline.
""",
        "role": """# ROLE SPECIFICATION: CS-02 Escalation Lead
- Divisi: Customer Support Lead
- Wewenang: Merekomendasikan retur/refund dan jeda bot untuk human handover.
"""
    },
    "MGT-01": {
        "soul": """# SOUL: Project Manager & Workspace Orchestrator (MGT-01)
Kamu adalah **Project Manager & Workspace Lead** di `{{brand_name}}`.
Bertugas memimpin alur kerja multi-agent, memecah brief proyek, dan mengontrol eksekusi otomatis.
""",
        "skill": """# SKILL: Multi-Agent Orchestration (MGT-01)
1. Breakdown brief klien menjadi tugas terstruktur.
2. Delegasikan ke tim kreatif atau CS.
3. Review hasil dan rangkum status milestone.
""",
        "role": """# ROLE SPECIFICATION: MGT-01 Project Manager
- Divisi: Operations
- Wewenang: Akses admin untuk task scheduling dan audit tim.
"""
    }
}

# ==============================================================================
# 3. CORE SERVICE METHODS
# ==============================================================================

def list_master_templates() -> List[Dict[str, Any]]:
    """Return catalog of all available master agent templates."""
    results = []
    root = get_template_root()
    for role_id, meta in MASTER_ROLES.items():
        folder = root / meta["folder_name"]
        has_disk = folder.is_dir()
        results.append({
            **meta,
            "has_disk_template": has_disk,
            "protected_core": ["SOUL.md", "SKILL.md", "ROLE.md"],
            "schema_version": "v3.0",
            "provenance": "AI Top Trends B2B Multi-Industry Master Library"
        })
    return results


def get_template_detail(role_id: str) -> Dict[str, Any]:
    """Retrieve full master template files and schema for a specific role."""
    role_key = role_id.upper().strip()
    # Normalize aliases
    for k, v in MASTER_ROLES.items():
        if role_key in (k, v["code"], v["alias"].upper()):
            role_key = k
            break
            
    if role_key not in MASTER_ROLES:
        raise ApiError(404, f"Master template '{role_id}' tidak ditemukan")
        
    meta = MASTER_ROLES[role_key]
    root = get_template_root()
    folder = root / meta["folder_name"]
    
    soul_content = ""
    skill_content = ""
    role_content = ""
    
    if folder.is_dir():
        soul_file = folder / "SOUL.md"
        skill_file = folder / "SKILL.md"
        role_file = folder / "ROLE.md"
        if soul_file.exists():
            soul_content = soul_file.read_text(encoding="utf-8")
        if skill_file.exists():
            skill_content = skill_file.read_text(encoding="utf-8")
        if role_file.exists():
            role_content = role_file.read_text(encoding="utf-8")
            
    if not soul_content and role_key in FALLBACK_TEMPLATES:
        soul_content = FALLBACK_TEMPLATES[role_key]["soul"]
        skill_content = FALLBACK_TEMPLATES[role_key]["skill"]
        role_content = FALLBACK_TEMPLATES[role_key]["role"]
        
    return {
        **meta,
        "files": {
            "SOUL.md": soul_content,
            "SKILL.md": skill_content,
            "ROLE.md": role_content
        },
        "hermes_mapping": {
            "SOUL.md": "~/.hermes/profiles/{bot_id}/SOUL.md (Persona & Instructions)",
            "SKILL.md": "~/.hermes/profiles/{bot_id}/skills/ (Registered FastMCP Tools)",
            "ROLE.md": "BFF Master Schema & Contract Spec (Read-only reference)"
        },
        "immutability": {
            "is_core_locked": True,
            "editable_boundary": "client_variables only"
        }
    }


def render_template(role_id: str, client_variables: Dict[str, Any]) -> Dict[str, str]:
    """Render template files by replacing {{variable_name}} with client-provided values.
    Core ethical and safety rules remain locked.
    """
    detail = get_template_detail(role_id)
    files = detail.get("files", {})
    
    rendered = {}
    for filename, content in files.items():
        res = content
        for var_name in detail.get("dynamic_variables", []):
            val = str(client_variables.get(var_name, f"[{var_name}]"))
            res = re.sub(rf"\{{\{{\s*{re.escape(var_name)}\s*\}}\}}", val, res)
        rendered[filename] = res
        
    return {
        "role_id": detail["id"],
        "rendered_files": rendered,
        "variables_applied": client_variables
    }


def get_hermes_config_mapping() -> Dict[str, Any]:
    """Return the formal joint alignment specification between Hermes installed configuration
    and the AI Employee Master Template architecture.
    """
    return {
        "spec": HERMES_CONFIG_SPEC,
        "master_roles_count": len(MASTER_ROLES),
        "integration_status": "aligned_and_verified",
        "summary": "Hermes config.yaml, .env, and SOUL.md are natively integrated. user.md and agents.md are documented as architecture targets/gaps handled at BFF orchestration layer."
    }


# In-memory overrides cache for runtime/test flexibility
_bot_overrides: Dict[str, Dict[str, Any]] = {}

# ==============================================================================
# 4. UNIFIED MODEL / SKILL / TOOL / PERMISSIONS SERVICE
# ==============================================================================

async def get_bot_permissions(bot_id: str, user_id: str = "default") -> Dict[str, Any]:
    """Retrieve full unified configuration: Model, Provider, Reasoning Effort,
    FastMCP Tool Tier, KB Category Boundaries, and Approvals Mode for an agent.
    """
    bot = None
    if getattr(db, "pool", None) is not None:
        try:
            bot = await db.q1("SELECT * FROM bots WHERE id = %s AND deleted_at IS NULL", bot_id)
        except Exception:
            pass

    overrides = _bot_overrides.get(bot_id, {})

    if not bot:
        # Check if it matches a template or builtin
        for role_id, meta in MASTER_ROLES.items():
            if bot_id.lower() in (meta["alias"], role_id.lower()):
                mcp_t = overrides.get("mcp_tier", meta["mcp_tier"])
                return {
                    "bot_id": bot_id,
                    "name": meta["name"],
                    "model": overrides.get("model", meta["default_model"]),
                    "provider": overrides.get("provider", meta["default_provider"]),
                    "reasoning_effort": overrides.get("reasoning_effort", meta["default_reasoning_effort"]),
                    "mcp_tier": mcp_t,
                    "mcp_tools_allowed": mcp_privileges.TIER_TOOLS.get(mcp_t, []),
                    "allowed_kb": meta["allowed_kb"],
                    "denied_kb": meta["denied_kb"],
                    "can_access_finance": "finance" in meta["allowed_kb"],
                    "approvals_mode": meta["approvals_mode"],
                    "source": "master_template_default"
                }
        raise ApiError(404, f"Bot '{bot_id}' tidak ditemukan")
        
    # Get current Hermes profile config
    approvals = settings._approval_mode(bot_id) or "manual"
    reasoning = overrides.get("reasoning_effort") or bot.get("reasoning_effort") or settings.profile_effort(bot_id) or "medium"
    
    # Get MCP tier
    matrix = mcp_privileges.get_agent_privilege_matrix()
    agent_mcp = matrix.get("agents", {}).get(bot_id, {})
    mcp_tier = overrides.get("mcp_tier") or agent_mcp.get("tier", "READ")
    
    # Get KB boundaries
    kb_matrix = kb.get_kb_access_matrix()
    agent_kb = kb_matrix.get("agents", {}).get(bot_id, {})
    allowed_kb = agent_kb.get("allowed_categories", ["general"])
    can_finance = agent_kb.get("can_access_finance", False)
    
    return {
        "bot_id": bot_id,
        "name": bot.get("name"),
        "role": bot.get("role"),
        "team": bot.get("team"),
        "model": overrides.get("model") or bot.get("model") or "deepseek/deepseek-chat",
        "provider": overrides.get("provider") or bot.get("provider") or "deepseek",
        "reasoning_effort": reasoning,
        "mcp_tier": mcp_tier,
        "mcp_tools_allowed": mcp_privileges.TIER_TOOLS.get(mcp_tier, []),
        "allowed_kb": allowed_kb,
        "can_access_finance": can_finance,
        "approvals_mode": approvals,
        "source": "database_and_runtime"
    }


async def update_bot_permissions(bot_id: str, updates: Dict[str, Any], user_id: str = "default") -> Dict[str, Any]:
    """Update agent's Model, Provider, Reasoning Effort, and MCP/KB permissions."""
    bot = None
    if getattr(db, "pool", None) is not None:
        try:
            bot = await db.q1("SELECT * FROM bots WHERE id = %s AND deleted_at IS NULL", bot_id)
        except Exception:
            pass

    if not bot:
        # Check if it matches a template or builtin alias
        found_role = None
        for role_id, meta in MASTER_ROLES.items():
            if bot_id.lower() in (meta["alias"], role_id.lower()):
                found_role = meta
                break
        if not found_role:
            raise ApiError(404, f"Bot '{bot_id}' tidak ditemukan")
        bot = {"id": bot_id, "name": found_role["name"], "team": found_role["team"], "role": found_role["name"]}
        
    if bot_id not in _bot_overrides:
        _bot_overrides[bot_id] = {}

    # 1. Update Model & Provider if specified
    model = updates.get("model")
    provider = updates.get("provider")
    reasoning_effort = updates.get("reasoning_effort")
    
    if model is not None or provider is not None:
        if (model is not None) != (provider is not None):
            raise ApiError(400, "Model dan provider harus diubah bersamaan")
        if model is not None:
            if not isinstance(model, str) or not re.match(r"^[\w.:/@+-]{1,120}$", model):
                raise ApiError(400, "Format nama model tidak valid")
            if not isinstance(provider, str) or not re.match(r"^[a-z0-9][a-z0-9._-]{0,63}$", provider):
                raise ApiError(400, "Format provider tidak valid")
            _bot_overrides[bot_id]["model"] = model
            _bot_overrides[bot_id]["provider"] = provider
            if getattr(db, "pool", None) is not None:
                try:
                    await db.ex("UPDATE bots SET model = %s, provider = %s WHERE id = %s", model, provider, bot_id)
                except Exception:
                    pass
            
    if reasoning_effort is not None:
        if reasoning_effort not in settings.EFFORTS:
            raise ApiError(400, f"Tingkat berpikir harus salah satu dari: {', '.join(settings.EFFORTS)}")
        _bot_overrides[bot_id]["reasoning_effort"] = reasoning_effort
        if getattr(db, "pool", None) is not None:
            try:
                await db.ex("UPDATE bots SET reasoning_effort = %s WHERE id = %s", reasoning_effort, bot_id)
            except Exception:
                pass
        
    # 2. Update MCP tier if specified
    mcp_tier = updates.get("mcp_tier")
    if mcp_tier:
        mcp_tier_upper = str(mcp_tier).upper()
        if mcp_tier_upper not in ("READ", "WRITE", "ADMIN"):
            raise ApiError(400, "MCP tier harus salah satu dari: READ, WRITE, ADMIN")
        _bot_overrides[bot_id]["mcp_tier"] = mcp_tier_upper
        # Update or register in mcp_privileges
        acc_id = f"acc_{bot.get('team', 'gen')}_{bot_id}_01"
        mcp_privileges.register_account(acc_id, bot_id, mcp_tier_upper)
        
    log.info("Updated permissions for bot %s: %s", bot_id, updates)
    return await get_bot_permissions(bot_id, user_id)
