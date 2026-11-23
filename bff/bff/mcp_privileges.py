"""MCP Multi-Account Privileges & Access Enforcement (Sprint 5 Day 2).
Enforces Read / Write / Admin privilege tiers per agent and connected account.
Prevents privilege escalation and cross-account access leakage.
"""
from enum import Enum
import logging
from typing import Optional, Tuple

from .errors import ApiError

log = logging.getLogger("bff.mcp_privileges")

class MCPPrivilege(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

PRIVILEGE_HIERARCHY = {
    MCPPrivilege.READ: 1,
    MCPPrivilege.WRITE: 2,
    MCPPrivilege.ADMIN: 3,
}

# Tool classification by required privilege tier
TOOL_PRIVILEGES: dict[str, MCPPrivilege] = {
    # READ tools (Level 1)
    "ping": MCPPrivilege.READ,
    "drive_search": MCPPrivilege.READ,
    "drive_read": MCPPrivilege.READ,
    "gmail_search": MCPPrivilege.READ,
    "gmail_read": MCPPrivilege.READ,
    "kb_search": MCPPrivilege.READ,
    "task_list": MCPPrivilege.READ,

    # WRITE tools (Level 2)
    "drive_create": MCPPrivilege.WRITE,
    "drive_update": MCPPrivilege.WRITE,
    "drive_rename": MCPPrivilege.WRITE,
    "drive_move": MCPPrivilege.WRITE,
    "gmail_create_draft": MCPPrivilege.WRITE,
    "gmail_label": MCPPrivilege.WRITE,
    "kb_add_link": MCPPrivilege.WRITE,
    "kb_add_note": MCPPrivilege.WRITE,
    "task_create": MCPPrivilege.WRITE,
    "task_comment": MCPPrivilege.WRITE,
    "task_ask_user": MCPPrivilege.WRITE,
    "task_request_review": MCPPrivilege.WRITE,
    "task_complete": MCPPrivilege.WRITE,

    # ADMIN tools (Level 3 - Destructive, Direct Sending, Cancellation)
    "drive_trash": MCPPrivilege.ADMIN,
    "gmail_trash": MCPPrivilege.ADMIN,
    "gmail_send": MCPPrivilege.ADMIN,
    "gmail_send_draft": MCPPrivilege.ADMIN,
    "task_cancel": MCPPrivilege.ADMIN,
}

# Registered Agent Accounts & Default Privilege Tiers
AGENT_MCP_REGISTRY: dict[str, dict] = {
    "siti": {
        "account_id": "acc_cs_siti_01",
        "privilege": MCPPrivilege.READ,
        "name": "Siti",
        "role": "Frontline Support Specialist",
        "team": "customer_support",
        "description": "Read-only access to customer resources, KB, and communication history."
    },
    "diana": {
        "account_id": "acc_cs_diana_02",
        "privilege": MCPPrivilege.READ,
        "name": "Diana",
        "role": "CS Quality Lead",
        "team": "customer_support",
        "description": "Read-only access for QA review and response evaluation."
    },
    "bram": {
        "account_id": "acc_mkt_bram_01",
        "privilege": MCPPrivilege.WRITE,
        "name": "Bram",
        "role": "Senior Copywriter",
        "team": "marketing",
        "description": "Write access to create drafts, campaign copy, and marketing notes."
    },
    "vina": {
        "account_id": "acc_mkt_vina_02",
        "privilege": MCPPrivilege.WRITE,
        "name": "Vina",
        "role": "Visual & Layout Designer",
        "team": "marketing",
        "description": "Write access to generate visual wireframes and notes."
    },
    "hendra": {
        "account_id": "acc_mkt_hendra_03",
        "privilege": MCPPrivilege.WRITE,
        "name": "Hendra",
        "role": "Marketing & CS Escalation Lead",
        "team": "management",
        "description": "Write access to manage campaign briefs and handle customer escalations."
    },
    "bimo": {
        "account_id": "acc_pm_bimo_01",
        "privilege": MCPPrivilege.ADMIN,
        "name": "Bimo",
        "role": "Project Manager & Supervisor",
        "team": "management",
        "description": "Full administrative control over all workspace tools and operations."
    },
    "admin": {
        "account_id": "acc_super_admin_01",
        "privilege": MCPPrivilege.ADMIN,
        "name": "Super Admin",
        "role": "System Administrator",
        "team": "infrastructure",
        "description": "Unrestricted administrative privileges."
    },
    "owner": {
        "account_id": "acc_owner_01",
        "privilege": MCPPrivilege.ADMIN,
        "name": "Hendrawan (Owner)",
        "role": "Business Owner",
        "team": "executive",
        "description": "Executive ownership privileges across all tools."
    },
}

def get_agent_privilege(bot_id: str | None) -> MCPPrivilege:
    """Resolve an agent's assigned MCP privilege tier.
    Unassigned direct client calls (no agent header or 'default') default to ADMIN.
    When a specific agent profile is executing, their configured tier is strictly enforced."""
    if not bot_id or bot_id == "default":
        return MCPPrivilege.ADMIN
    bot_key = bot_id.lower().strip()
    entry = AGENT_MCP_REGISTRY.get(bot_key)
    if entry:
        return entry["privilege"]
    return MCPPrivilege.READ

def get_agent_account_id(bot_id: str | None) -> str:
    """Resolve the authorized MCP account_id for a given bot_id."""
    if not bot_id or bot_id == "default":
        return "acc_default_01"
    bot_key = bot_id.lower().strip()
    entry = AGENT_MCP_REGISTRY.get(bot_key)
    if entry:
        return entry["account_id"]
    return f"acc_{bot_key}_default"

def check_mcp_privilege(bot_id: str | None, tool_name: str, account_id: Optional[str] = None) -> Tuple[bool, str]:
    """Validate whether an agent/account has sufficient privileges to call a given MCP tool.
    
    Returns:
        (allowed: bool, reason: str)
    """
    bot = (bot_id or "default").lower().strip()
    tool = tool_name.strip()
    
    # Check if tool is recognized
    required_privilege = TOOL_PRIVILEGES.get(tool)
    if not required_privilege:
        # Unknown tool default to requiring WRITE for safety
        required_privilege = MCPPrivilege.WRITE

    # Multi-account boundary check: verify caller is not impersonating another account
    expected_account = get_agent_account_id(bot)
    if account_id and account_id != expected_account:
        # Cross-account usage attempted
        log.warning("MCP Cross-Account Violation: Agent '%s' attempted to use account '%s' (expected '%s')",
                    bot, account_id, expected_account)
        return False, (f"Error 403: Forbidden - Cross-account access denied. Agent '{bot}' "
                      f"cannot execute tools using account '{account_id}' (bound to '{expected_account}').")

    # Privilege hierarchy check
    current_privilege = get_agent_privilege(bot)
    current_level = PRIVILEGE_HIERARCHY[current_privilege]
    required_level = PRIVILEGE_HIERARCHY[required_privilege]

    if current_level < required_level:
        log.warning("MCP Privilege Violation: Agent '%s' (%s) denied tool '%s' (requires %s)",
                    bot, current_privilege.value, tool, required_privilege.value)
        return False, (f"Error 403: Forbidden - Account privilege '{current_privilege.value}' is insufficient "
                      f"for tool '{tool}' (requires '{required_privilege.value}').")

    return True, f"Authorized: Agent '{bot}' granted {required_privilege.value} access to tool '{tool}'."

def assert_mcp_privilege(bot_id: str | None, tool_name: str, account_id: Optional[str] = None) -> None:
    """Raise ApiError(403) if privilege is insufficient or account mismatch."""
    allowed, reason = check_mcp_privilege(bot_id, tool_name, account_id)
    if not allowed:
        raise ApiError(403, reason)

def list_mcp_privileges() -> dict:
    """Return the complete, structured MCP privilege & account enforcement directory."""
    return {
        "hierarchy": [p.value for p in PRIVILEGE_HIERARCHY.keys()],
        "tools": {t: p.value for t, p in TOOL_PRIVILEGES.items()},
        "accounts": AGENT_MCP_REGISTRY
    }
