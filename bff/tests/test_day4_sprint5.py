import pytest
from httpx import ASGITransport, AsyncClient

from bff import telegram, memory_blueprint
from bff.main import app

@pytest.fixture
def anyio_backend():
    return "asyncio"

# ==============================================================================
# 1. TELEGRAM WEBHOOK SECURITY & COMMAND TESTS
# ==============================================================================

def test_telegram_webhook_secret_verification():
    assert telegram.verify_webhook_secret(telegram.TELEGRAM_WEBHOOK_SECRET) is True
    assert telegram.verify_webhook_secret("wrong_secret_token") is False
    assert telegram.verify_webhook_secret(None) is False


def test_telegram_message_splitting_under_4096_chars():
    # 1. Short text
    short_text = "Halo ini pesan singkat dari bot Telegram Pegawai AI."
    chunks = telegram.split_telegram_message(short_text)
    assert len(chunks) == 1
    assert chunks[0] == short_text

    # 2. Long text exceeding 4096 chars (5000 chars)
    paragraph = "Baris informasi kebijakan operasional karyawan AI Colorbox dan Pegawai AI.\n\n"
    long_text = paragraph * 80  # ~5920 characters
    assert len(long_text) > 4096

    chunks_long = telegram.split_telegram_message(long_text, max_chars=4096)
    assert len(chunks_long) > 1
    for chunk in chunks_long:
        assert len(chunk) <= 4096
    # Verify parts annotation
    assert "(1/" in chunks_long[0]
    assert f"({len(chunks_long)}/{len(chunks_long)})" in chunks_long[-1]


@pytest.mark.anyio
async def test_telegram_command_handling(monkeypatch):
    """Commands read and write the persisted chat state; /agent only accepts the owner's existing bots."""
    state = telegram.ChatState(123456789, "user_owner",
                               {"id": "siti", "name": "Siti", "team": "customer_support"}, "tg-123-abc")

    async def list_bots(_owner):
        return [{"id": "siti", "name": "Siti"}, {"id": "bram", "name": "Bram"}]

    async def get_bot(_owner, bot_id):
        return {"id": bot_id, "name": bot_id.title(), "team": "marketing"}

    saves = []

    async def save_chat(*args):
        saves.append(args)

    monkeypatch.setattr(telegram.bots, "list_bots", list_bots)
    monkeypatch.setattr(telegram.bots, "get_bot", get_bot)
    monkeypatch.setattr(telegram, "_save_chat", save_chat)

    is_cmd, text = await telegram.handle_telegram_command("/start", "", state)
    assert is_cmd is True
    assert "Siti" in text and "Bram" in text

    is_cmd, text_help = await telegram.handle_telegram_command("/help", "", state)
    assert is_cmd is True
    assert "Panduan" in text_help

    is_cmd, text_status = await telegram.handle_telegram_command("/status", "", state)
    assert is_cmd is True
    assert "Siti" in text_status

    is_cmd, text_agent = await telegram.handle_telegram_command("/agent", "bram", state)
    assert is_cmd is True
    assert "Bram" in text_agent
    assert state.bot_id == "bram"
    assert state.session_id is None  # another employee starts a fresh conversation
    assert saves[-1][1:] == ("user_owner", "bram", None)

    is_cmd, text_invalid = await telegram.handle_telegram_command("/agent", "tidak-ada", state)
    assert is_cmd is True
    assert "tidak tersedia" in text_invalid
    assert state.bot_id == "bram"

    is_cmd, text_reset = await telegram.handle_telegram_command("/reset", "", state)
    assert is_cmd is True
    assert "Percakapan baru" in text_reset
    assert saves[-1][1:] == ("user_owner", "bram", None)


# ==============================================================================
# 2. SEVEN MEMORY CANDIDATES BENCHMARK TESTS
# ==============================================================================

def test_seven_memory_candidates_complete_benchmark():
    candidates = memory_blueprint.MEMORY_CANDIDATES
    assert len(candidates) == 7

    expected_keys = ["obsidian", "hindsight", "memo", "honcho", "openviking", "cognee", "agentmemory"]
    for key in expected_keys:
        assert key in candidates
        cand = candidates[key]
        assert "name" in cand
        assert "vendor_or_repo" in cand
        assert "license" in cand
        assert "architecture_and_setup" in cand
        assert "tested_status" in cand
        assert "hermes_integration_method" in cand
        assert "layer_fit" in cand
        assert "permissions_and_scoping" in cand
        assert "retention_and_deletion" in cand
        assert "tradeoffs" in cand
        assert "recommendation" in cand
        # Verify tested labels are explicit and not fabricated
        assert ("UNTESTED" in cand["tested_status"] or "ANALYZED" in cand["tested_status"])

    # Specific candidate decisions
    assert "REJECT" in candidates["obsidian"]["recommendation"]
    assert "RECOMMENDED PRIMARY CANDIDATE" in candidates["memo"]["recommendation"]
    assert "PILOT FOR UI" in candidates["agentmemory"]["recommendation"]


# ==============================================================================
# 3. FIVE-LAYER MEMORY BLUEPRINT & TENANT ISOLATION TESTS
# ==============================================================================

def test_five_memory_layers_spec():
    layers = memory_blueprint.MEMORY_LAYERS_SPEC
    assert len(layers) == 5

    assert layers["layer_1_session"]["status"] == "AVAILABLE"
    assert layers["layer_2_employee"]["status"] == "AVAILABLE_AND_PARTIAL"
    assert layers["layer_3_customer"]["status"] == "PLANNED"
    assert layers["layer_4_project"]["status"] == "PLANNED"
    assert layers["layer_5_long_term"]["status"] == "PLANNED"

    for k, layer in layers.items():
        assert "layer_number" in layer
        assert "name" in layer
        assert "scope" in layer
        assert "storage_engine" in layer
        assert "ux_label" in layer
        assert "isolation_enforcement" in layer


def test_tenant_memory_isolation_and_threat_scenarios():
    report = memory_blueprint.validate_tenant_isolation("tenant_alpha_corp", "tenant_beta_ltd")
    assert report["status"] == "success"
    assert report["isolation_verified"] is True
    assert report["scenarios_tested"] == 5

    for s in report["scenarios"]:
        assert s["outcome"] == "PASSED_PROTECTED"

    # Direct unit checks on cross-tenant leaks
    mem_alpha = memory_blueprint.get_tenant_memories("tenant_alpha_corp")
    assert len(mem_alpha) >= 2
    for r in mem_alpha:
        assert "Beta" not in r["content"]

    mem_beta = memory_blueprint.get_tenant_memories("tenant_beta_ltd")
    assert len(mem_beta) >= 2
    for r in mem_beta:
        assert "Alpha Corp" not in r["content"]

    # Verify cross-tenant search leaks 0 items
    search_leak = memory_blueprint.search_tenant_memory("tenant_beta_ltd", "wholesale discount")
    assert len(search_leak) == 0


# ==============================================================================
# 4. FASTAPI ENDPOINTS INTEGRATION
# ==============================================================================

@pytest.mark.anyio
async def test_api_telegram_and_memory_blueprint_endpoints(signed_in, monkeypatch):
    async def fake_state(chat_id, _forced_bot_id=None):
        return telegram.ChatState(chat_id, "user_owner",
                                  {"id": "siti", "name": "Siti", "team": "customer_support"}, None)

    async def fake_turn(_state, _text):
        return "Balasan agen untuk pengujian."

    monkeypatch.setattr(telegram, "_resolve_chat", fake_state)
    monkeypatch.setattr(telegram, "_agent_turn", fake_turn)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. GET /api/telegram/status
        r_tg_stat = await ac.get("/api/telegram/status", headers=signed_in)
        assert r_tg_stat.status_code == 200
        tg_stat = r_tg_stat.json()
        assert "supported_commands" in tg_stat
        assert "/start" in tg_stat["supported_commands"]

        # 2. POST /api/telegram/simulate (agent path stubbed: this checks the endpoint plumbing)
        sim_payload = {
            "text": "Halo, bagaimana syarat retur barang?",
            "sender_name": "Andi",
            "chat_id": 999111222
        }
        r_sim = await ac.post("/api/telegram/simulate", json=sim_payload, headers=signed_in)
        assert r_sim.status_code == 200
        sim_data = r_sim.json()
        assert sim_data["ok"] is True
        assert sim_data["status"] == "message_routed"
        assert sim_data["bot_id"] == "siti"
        assert sim_data["agent_reply"] == "Balasan agen untuk pengujian."

        # 3. GET /api/memory/blueprint
        r_blue = await ac.get("/api/memory/blueprint", headers=signed_in)
        assert r_blue.status_code == 200
        blue_data = r_blue.json()
        assert "layers" in blue_data
        assert "candidates_benchmark" in blue_data
        assert len(blue_data["candidates_benchmark"]) == 7

        # 4. GET /api/memory/layers
        r_layers = await ac.get("/api/memory/layers", headers=signed_in)
        assert r_layers.status_code == 200
        l_data = r_layers.json()
        assert l_data["status_summary"]["layer_1_session"] == "AVAILABLE"
        assert l_data["status_summary"]["layer_5_long_term"] == "PLANNED"

        # 5. POST /api/memory/tenant/validate-isolation
        r_iso = await ac.post("/api/memory/tenant/validate-isolation", json={}, headers=signed_in)
        assert r_iso.status_code == 200
        iso_data = r_iso.json()
        assert iso_data["isolation_verified"] is True
        assert iso_data["scenarios_tested"] == 5
