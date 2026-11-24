import pytest
from httpx import ASGITransport, AsyncClient

from bff import config, telegram, memory_blueprint
from bff.main import app

HEADERS = {"X-Pegawai-AI-Key": config.BFF_API_KEY}

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


def test_telegram_command_handling():
    chat_id = 123456789
    telegram.reset_chat_session(chat_id)

    # /start
    is_cmd, text = telegram.handle_telegram_command("/start", "", chat_id)
    assert is_cmd is True
    assert "Selamat datang di Pegawai AI" in text
    assert "Siti" in text
    assert "Bram" in text

    # /help
    is_cmd, text_help = telegram.handle_telegram_command("/help", "", chat_id)
    assert is_cmd is True
    assert "Panduan Penggunaan" in text_help

    # /status
    is_cmd, text_status = telegram.handle_telegram_command("/status", "", chat_id)
    assert is_cmd is True
    assert str(chat_id) in text_status
    assert "siti" in text_status.lower()

    # /agent bram
    is_cmd, text_agent = telegram.handle_telegram_command("/agent", "bram", chat_id)
    assert is_cmd is True
    assert "Bram" in text_agent
    assert telegram.get_chat_active_bot(chat_id) == "bram"

    # /reset
    is_cmd, text_reset = telegram.handle_telegram_command("/reset", "", chat_id)
    assert is_cmd is True
    assert "direset" in text_reset
    assert telegram.get_chat_active_bot(chat_id) == "siti"


@pytest.mark.anyio
async def test_process_telegram_update_routing_and_cs_knowledge():
    chat_id = 987654321
    telegram.reset_chat_session(chat_id)

    # Test CS SOP: Penukaran Ukuran (Size Exchange)
    update = {
        "update_id": 9901,
        "message": {
            "message_id": 101,
            "chat": {"id": chat_id},
            "from": {"id": chat_id, "first_name": "Rina"},
            "text": "Halo kak, kalau baju saya kebesaran bisa tukar ukuran langsung gak?"
        }
    }
    res = await telegram.process_telegram_update(update, telegram.TELEGRAM_WEBHOOK_SECRET)
    assert res["ok"] is True
    assert res["status"] == "message_routed"
    assert res["bot_id"] == "siti"
    assert "tidak dapat melayani penukaran ukuran" in res["agent_reply"]
    assert "retur" in res["agent_reply"]

    # Test duplicate update is ignored
    dup_res = await telegram.process_telegram_update(update, telegram.TELEGRAM_WEBHOOK_SECRET)
    assert dup_res["status"] == "duplicate_ignored"


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
async def test_api_telegram_and_memory_blueprint_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. GET /api/telegram/status
        r_tg_stat = await ac.get("/api/telegram/status", headers=HEADERS)
        assert r_tg_stat.status_code == 200
        tg_stat = r_tg_stat.json()
        assert "supported_commands" in tg_stat
        assert "/start" in tg_stat["supported_commands"]

        # 2. POST /api/telegram/simulate
        sim_payload = {
            "text": "Halo, bagaimana syarat retur barang?",
            "sender_name": "Andi",
            "chat_id": 999111222
        }
        r_sim = await ac.post("/api/telegram/simulate", json=sim_payload, headers=HEADERS)
        assert r_sim.status_code == 200
        sim_data = r_sim.json()
        assert sim_data["ok"] is True
        assert sim_data["status"] == "message_routed"
        assert "retur" in sim_data["agent_reply"].lower()

        # 3. GET /api/memory/blueprint
        r_blue = await ac.get("/api/memory/blueprint", headers=HEADERS)
        assert r_blue.status_code == 200
        blue_data = r_blue.json()
        assert "layers" in blue_data
        assert "candidates_benchmark" in blue_data
        assert len(blue_data["candidates_benchmark"]) == 7

        # 4. GET /api/memory/layers
        r_layers = await ac.get("/api/memory/layers", headers=HEADERS)
        assert r_layers.status_code == 200
        l_data = r_layers.json()
        assert l_data["status_summary"]["layer_1_session"] == "AVAILABLE"
        assert l_data["status_summary"]["layer_5_long_term"] == "PLANNED"

        # 5. POST /api/memory/tenant/validate-isolation
        r_iso = await ac.post("/api/memory/tenant/validate-isolation", json={}, headers=HEADERS)
        assert r_iso.status_code == 200
        iso_data = r_iso.json()
        assert iso_data["isolation_verified"] is True
        assert iso_data["scenarios_tested"] == 5
