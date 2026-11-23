import pytest
from bff import kb, mcp_privileges, whatsapp
from bff.errors import ApiError

# ==============================================================================
# 1. PER-AGENT KB ISOLATION TESTS
# ==============================================================================

def test_kb_access_matrix_structure():
    matrix = kb.get_kb_access_matrix()
    assert "categories" in matrix
    assert "agents" in matrix
    assert "finance" in matrix["categories"]
    assert "cs" in matrix["categories"]

    # CS agents must not have finance in allowed_categories
    assert "finance" not in matrix["agents"]["siti"]["allowed_categories"]
    assert "finance" not in matrix["agents"]["diana"]["allowed_categories"]
    assert matrix["agents"]["siti"]["can_access_finance"] is False
    assert matrix["agents"]["diana"]["can_access_finance"] is False

    # Management agents must have finance
    assert "finance" in matrix["agents"]["bimo"]["allowed_categories"]
    assert "finance" in matrix["agents"]["admin"]["allowed_categories"]
    assert "finance" in matrix["agents"]["owner"]["allowed_categories"]
    assert matrix["agents"]["bimo"]["can_access_finance"] is True


def test_cs_agent_denied_finance_files():
    # Siti and Diana attempting to access finance category
    assert kb.can_agent_access_item("siti", "finance", "Laporan_Keuangan_Q3.pdf") is False
    assert kb.can_agent_access_item("diana", "finance", "Rekap_Gaji_Karyawan.xlsx") is False
    assert kb.can_agent_access_item("siti", {"category": "finance", "name": "Financial_Report.pdf"}) is False

    # Also denied if filename contains finance patterns even if category says general
    assert kb.can_agent_access_item("siti", "general", "Laporan_Keuangan_Tahunan.pdf") is False
    assert kb.can_agent_access_item("diana", "general", "Slip_Gaji_November.pdf") is False

    # Assert raises 403 ApiError
    with pytest.raises(ApiError) as exc_siti:
        kb.assert_agent_access("siti", "finance", "Laporan_Keuangan_Q3.pdf")
    assert exc_siti.value.status == 403
    assert "Akses ditolak" in exc_siti.value.message

    with pytest.raises(ApiError) as exc_diana:
        kb.assert_agent_access("diana", "finance", "Rekap_Gaji_2026.docx")
    assert exc_diana.value.status == 403


def test_cs_agent_allowed_cs_and_catalog():
    # CS agents allowed for CS SOP and Catalog files
    assert kb.can_agent_access_item("siti", "cs", "SOP_Pelayanan_CS_Colorbox.md") is True
    assert kb.can_agent_access_item("siti", "catalog", "Katalog_Produk_Liunic.pdf") is True
    assert kb.can_agent_access_item("siti", "general", "Kebijakan_Toko_Colorbox.txt") is True

    assert kb.can_agent_access_item("diana", "cs", "Panduan_Retur_Barang.md") is True
    assert kb.can_agent_access_item("diana", "catalog", "Daftar_Ukuran_Baju.pdf") is True


def test_authorized_agents_allowed_finance():
    # Bimo (PM), Admin, and Owner allowed to access finance files
    assert kb.can_agent_access_item("bimo", "finance", "Laporan_Keuangan_Q3.pdf") is True
    assert kb.can_agent_access_item("admin", "finance", "Rekap_Gaji_Karyawan.xlsx") is True
    assert kb.can_agent_access_item("owner", "finance", "Laporan_Laba_Rugi.pdf") is True


def test_category_auto_detection():
    assert kb.detect_category("Laporan_Keuangan_2026.pdf") == "finance"
    assert kb.detect_category("Rekap_Gaji_Staf.xlsx") == "finance"
    assert kb.detect_category("SOP_Customer_Support.md") == "cs"
    assert kb.detect_category("Katalog_Baju_Denim.pdf") == "catalog"
    assert kb.detect_category("Panduan_Social_Media_Marketing.docx") == "marketing"
    assert kb.detect_category("Company_Overview.txt") == "general"


# ==============================================================================
# 2. MCP MULTI-ACCOUNT PRIVILEGE TESTS
# ==============================================================================

def test_mcp_read_account_privileges():
    # Siti has READ privilege
    assert mcp_privileges.get_agent_privilege("siti") == mcp_privileges.MCPPrivilege.READ

    # READ tools allowed
    allowed, _ = mcp_privileges.check_mcp_privilege("siti", "drive_search")
    assert allowed is True
    allowed, _ = mcp_privileges.check_mcp_privilege("siti", "gmail_read")
    assert allowed is True
    allowed, _ = mcp_privileges.check_mcp_privilege("siti", "kb_search")
    assert allowed is True

    # WRITE tools denied
    allowed, reason = mcp_privileges.check_mcp_privilege("siti", "drive_create")
    assert allowed is False
    assert "insufficient" in reason.lower()
    assert "requires 'write'" in reason.lower()

    # ADMIN tools denied
    allowed, reason = mcp_privileges.check_mcp_privilege("siti", "drive_trash")
    assert allowed is False
    assert "insufficient" in reason.lower()
    assert "requires 'admin'" in reason.lower()


def test_mcp_write_account_privileges():
    # Bram has WRITE privilege
    assert mcp_privileges.get_agent_privilege("bram") == mcp_privileges.MCPPrivilege.WRITE

    # READ tools allowed
    allowed, _ = mcp_privileges.check_mcp_privilege("bram", "drive_search")
    assert allowed is True

    # WRITE tools allowed
    allowed, _ = mcp_privileges.check_mcp_privilege("bram", "drive_create")
    assert allowed is True
    allowed, _ = mcp_privileges.check_mcp_privilege("bram", "gmail_create_draft")
    assert allowed is True
    allowed, _ = mcp_privileges.check_mcp_privilege("bram", "task_create")
    assert allowed is True

    # ADMIN tools denied
    allowed, reason = mcp_privileges.check_mcp_privilege("bram", "drive_trash")
    assert allowed is False
    assert "requires 'admin'" in reason.lower()

    allowed, reason = mcp_privileges.check_mcp_privilege("bram", "gmail_send")
    assert allowed is False
    assert "requires 'admin'" in reason.lower()


def test_mcp_admin_account_privileges():
    # Bimo & Super Admin have ADMIN privilege
    assert mcp_privileges.get_agent_privilege("bimo") == mcp_privileges.MCPPrivilege.ADMIN
    assert mcp_privileges.get_agent_privilege("admin") == mcp_privileges.MCPPrivilege.ADMIN

    # All tools allowed
    for tool in ["drive_search", "drive_create", "drive_trash", "gmail_send", "task_cancel"]:
        allowed, _ = mcp_privileges.check_mcp_privilege("bimo", tool)
        assert allowed is True, f"Bimo should be allowed for {tool}"

        allowed, _ = mcp_privileges.check_mcp_privilege("admin", tool)
        assert allowed is True, f"Admin should be allowed for {tool}"


def test_mcp_cross_account_isolation():
    # Siti owns acc_cs_siti_01
    siti_acc = mcp_privileges.get_agent_account_id("siti")
    assert siti_acc == "acc_cs_siti_01"

    # Siti using her own account -> OK for read
    allowed, _ = mcp_privileges.check_mcp_privilege("siti", "drive_search", account_id="acc_cs_siti_01")
    assert allowed is True

    # Siti attempting to use Bimo's admin account -> REJECTED
    allowed, reason = mcp_privileges.check_mcp_privilege("siti", "drive_search", account_id="acc_pm_bimo_01")
    assert allowed is False
    assert "Cross-account access denied" in reason


# ==============================================================================
# 3. WHATSAPP CS ROUTING TESTS
# ==============================================================================

def test_whatsapp_routing_frontline_vs_escalation():
    # 1. Frontline inquiry (stock/catalog/sizing) -> routes to Siti
    bot_id, intent, priority = whatsapp.classify_and_route("Halo kak, produk denim jacket ukuran M apakah ready stok?")
    assert bot_id == "siti"
    assert priority in ("P2", "P3")
    assert intent in ("PRODUCT_AVAILABILITY", "SIZE_FIT", "PRODUCT_INFO")

    reply_siti = whatsapp.generate_cs_reply(bot_id, "Kak Anita", "ready stok?", intent, priority)
    assert "Siti" in reply_siti or "Colorbox" in reply_siti

    # 2. Defect / Complaint / Refund inquiry -> routes to Hendra (Lead / Escalation)
    bot_id2, intent2, priority2 = whatsapp.classify_and_route("Baju yang saya terima jahitan ketiaknya robek dan kotor! Saya minta ganti rugi atau refund!")
    assert bot_id2 == "hendra"
    assert priority2 == "P1"
    assert intent2 in ("COMPLAINT_DAMAGED", "RETURN_REFUND")

    reply_hendra = whatsapp.generate_cs_reply(bot_id2, "Pak Hendrawan", "robek dan refund", intent2, priority2)
    assert "Hendra" in reply_hendra
    assert "Team Lead" in reply_hendra or "Manajemen" in reply_hendra
