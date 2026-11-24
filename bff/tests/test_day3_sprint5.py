import pytest
from httpx import ASGITransport, AsyncClient

from bff import master_template, kb, mcp_privileges
from bff.main import app

@pytest.fixture
def anyio_backend():
    return "asyncio"

# ==============================================================================
# 1. MASTER TEMPLATE CATALOG & SCHEMA TESTS
# ==============================================================================

def test_master_template_catalog_listing():
    catalog = master_template.list_master_templates()
    assert len(catalog) >= 7
    
    role_ids = [t["id"] for t in catalog]
    assert "CRE-01" in role_ids
    assert "CRE-02" in role_ids
    assert "CRE-03" in role_ids
    assert "CRE-04" in role_ids
    assert "CS-01" in role_ids
    assert "CS-02" in role_ids
    assert "MGT-01" in role_ids
    
    for t in catalog:
        assert "name" in t
        assert "team" in t
        assert "default_model" in t
        assert "mcp_tier" in t
        assert "allowed_kb" in t
        assert "denied_kb" in t
        assert "dynamic_variables" in t
        assert "protected_core" in t
        assert t["protected_core"] == ["SOUL.md", "SKILL.md", "ROLE.md"]


def test_master_template_detail_and_immutability():
    detail = master_template.get_template_detail("CRE-01")
    assert detail["id"] == "CRE-01"
    assert "SOUL.md" in detail["files"]
    assert "SKILL.md" in detail["files"]
    assert "ROLE.md" in detail["files"]
    
    soul = detail["files"]["SOUL.md"]
    assert "{{brand_name}}" in soul
    assert "{{industry}}" in soul
    # Must NOT have hardcoded company name in universal master template
    assert "Colorbox" not in soul
    
    assert detail["immutability"]["is_core_locked"] is True


def test_cs_master_template_boundaries():
    cs_detail = master_template.get_template_detail("CS-01")
    assert cs_detail["id"] == "CS-01"
    assert cs_detail["mcp_tier"] == "READ"
    assert "finance" in cs_detail["denied_kb"]
    assert "cs" in cs_detail["allowed_kb"]
    
    soul = cs_detail["files"]["SOUL.md"]
    assert "Retur 7 Hari" in soul or "7 hari" in soul.lower()


# ==============================================================================
# 2. DYNAMIC CLIENT VARIABLE INJECTION & RENDERING
# ==============================================================================

def test_template_variable_rendering():
    variables = {
        "brand_name": "Kopi Sore Hari",
        "industry": "Food & Beverage (Coffee Shop)",
        "target_audience": "Pekerja kantoran WFC usia 22-35 tahun",
        "content_pillars": "Sensory, Work Space, Promo",
        "knowledge_catalog": "Menu Kopi & Croissant v1.0",
        "official_cta": "Pesan langsung di outlet atau GoFood",
        "official_hashtag": "#KopiSoreHari"
    }
    
    rendered = master_template.render_template("CRE-01", variables)
    assert rendered["role_id"] == "CRE-01"
    assert "SOUL.md" in rendered["rendered_files"]
    
    rendered_soul = rendered["rendered_files"]["SOUL.md"]
    assert "Kopi Sore Hari" in rendered_soul
    assert "Food & Beverage (Coffee Shop)" in rendered_soul
    assert "Pekerja kantoran WFC" in rendered_soul
    assert "{{brand_name}}" not in rendered_soul
    assert "{{industry}}" not in rendered_soul


# ==============================================================================
# 3. HERMES CONFIG MECHANISM & GAP ALIGNMENT
# ==============================================================================

def test_hermes_config_mapping_spec():
    mapping = master_template.get_hermes_config_mapping()
    spec = mapping["spec"]
    
    # Supported native files
    assert "config.yaml" in spec["supported_native_files"]
    assert "SOUL.md" in spec["supported_native_files"]
    assert ".env" in spec["supported_native_files"]
    assert spec["supported_native_files"]["config.yaml"]["status"] == "supported_native"
    
    # Documented architecture gaps (explicitly not faked)
    assert "user.md" in spec["documented_architecture_gaps"]
    assert "agents.md" in spec["documented_architecture_gaps"]
    assert spec["documented_architecture_gaps"]["user.md"]["status"] == "unsupported_gap"
    assert spec["documented_architecture_gaps"]["agents.md"]["status"] == "unsupported_gap"


# ==============================================================================
# 4. UNIFIED MODEL / SKILL / TOOL / PERMISSIONS
# ==============================================================================

@pytest.mark.anyio
async def test_get_bot_permissions():
    perms = await master_template.get_bot_permissions("siti")
    assert perms["bot_id"] == "siti"
    assert perms["mcp_tier"] == "READ"
    assert perms["can_access_finance"] is False
    assert "cs" in perms["allowed_kb"]
    assert "model" in perms
    assert "reasoning_effort" in perms


@pytest.mark.anyio
async def test_update_bot_permissions_round_trip():
    # Update reasoning effort and MCP tier
    updated = await master_template.update_bot_permissions("siti", {
        "reasoning_effort": "high",
        "mcp_tier": "WRITE"
    })
    assert updated["reasoning_effort"] == "high"
    assert updated["mcp_tier"] == "WRITE"
    
    # Revert back to maintain system state
    reverted = await master_template.update_bot_permissions("siti", {
        "reasoning_effort": "medium",
        "mcp_tier": "READ"
    })
    assert reverted["reasoning_effort"] == "medium"
    assert reverted["mcp_tier"] == "READ"


# ==============================================================================
# 5. FASTAPI ENDPOINTS INTEGRATION
# ==============================================================================

@pytest.mark.anyio
async def test_api_master_templates_endpoints(signed_in):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # GET /api/templates/master
        r = await ac.get("/api/templates/master", headers=signed_in)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 7
        
        # GET /api/templates/master/CRE-01
        r_det = await ac.get("/api/templates/master/CRE-01", headers=signed_in)
        assert r_det.status_code == 200
        det = r_det.json()
        assert det["id"] == "CRE-01"
        assert "SOUL.md" in det["files"]
        
        # POST /api/templates/render
        render_payload = {
            "role_id": "CRE-02",
            "variables": {
                "brand_name": "GlowLab Aesthetic",
                "industry": "Skincare & Klinik Kecantikan",
                "target_audience": "Pasien acne & anti-aging"
            }
        }
        r_render = await ac.post("/api/templates/render", json=render_payload, headers=signed_in)
        assert r_render.status_code == 200
        rend = r_render.json()
        assert "GlowLab Aesthetic" in rend["rendered_files"]["SOUL.md"]
        
        # GET /api/hermes/config-mapping
        r_map = await ac.get("/api/hermes/config-mapping", headers=signed_in)
        assert r_map.status_code == 200
        m = r_map.json()
        assert "spec" in m
        assert "user.md" in m["spec"]["documented_architecture_gaps"]
        
        # GET /api/bots/siti/permissions
        r_perm = await ac.get("/api/bots/siti/permissions", headers=signed_in)
        assert r_perm.status_code == 200
        p = r_perm.json()
        assert p["bot_id"] == "siti"
        assert p["can_access_finance"] is False
