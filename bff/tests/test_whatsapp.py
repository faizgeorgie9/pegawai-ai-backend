import pytest
from httpx import ASGITransport, AsyncClient

from bff.main import app
from bff.whatsapp import WHATSAPP_VERIFY_TOKEN, classify_and_route, generate_cs_reply, parse_webhook_payload

@pytest.fixture
def anyio_backend():
    return "asyncio"

def test_classify_and_route_frontline():
    bot, intent, priority = classify_and_route("Halo, apakah ada promo diskon untuk denim hari ini?")
    assert bot == "siti"
    assert intent == "PRODUCT_INFO"
    assert priority == "P3"

def test_classify_and_route_sizing():
    bot, intent, priority = classify_and_route("Permisi kak, mau tanya lingkar dada untuk size L berapa ya?")
    assert bot == "siti"
    assert intent == "SIZE_FIT"
    assert priority == "P2"

def test_classify_and_route_escalation():
    bot, intent, priority = classify_and_route("Saya kecewa sekali barang yang sampai robek dan cacat! Saya mau komplain ke manajer!")
    assert bot == "hendra"
    assert intent in ("COMPLAINT_DAMAGED", "RETURN_REFUND")
    assert priority == "P1"

def test_generate_cs_reply_siti():
    reply = generate_cs_reply("siti", "Rina", "Berapa lama estimasi pengiriman?", "SHIPPING_DELIVERY", "P2")
    assert "Halo Rina" in reply
    assert "Siti" in reply
    assert "Colorbox" in reply

def test_generate_cs_reply_hendra():
    reply = generate_cs_reply("hendra", "Budi", "Barang saya rusak robek!", "COMPLAINT_DAMAGED", "P1")
    assert "Hendra" in reply
    assert "Customer Service Team Lead" in reply
    assert "1x24 jam" in reply

def test_parse_meta_cloud_webhook():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123456",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "contacts": [{"wa_id": "628111222333", "profile": {"name": "Maya"}}],
                    "messages": [{
                        "from": "628111222333",
                        "id": "wamid.123",
                        "timestamp": "1731900000",
                        "type": "text",
                        "text": {"body": "Halo Colorbox, apakah jaket corduroy masih ada?"}
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    parsed = parse_webhook_payload(payload)
    assert len(parsed) == 1
    assert parsed[0]["sender"] == "628111222333"
    assert parsed[0]["customer_name"] == "Maya"
    assert "jaket corduroy" in parsed[0]["message"]

@pytest.mark.anyio
async def test_whatsapp_webhook_verification():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Success verification
        r = await ac.get(f"/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token={WHATSAPP_VERIFY_TOKEN}&hub.challenge=test_challenge_123")
        assert r.status_code == 200
        assert r.text == "test_challenge_123"

        # Invalid token
        r2 = await ac.get("/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=wrong_token&hub.challenge=test_challenge_123")
        assert r2.status_code == 403

@pytest.mark.anyio
async def test_whatsapp_simulate_endpoint(signed_in):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Standard query -> routes to Siti
        payload = {
            "sender": "628999888777",
            "customer_name": "Nadia",
            "message": "Halo kak, koleksi Colorbox x Liunic masih ready gak ya?"
        }
        r = await ac.post("/api/whatsapp/simulate", json=payload, headers=signed_in)
        assert r.status_code == 200
        data = r.json()
        assert data["routed_bot"] == "siti"
        assert data["bot_name"] == "Siti"
        assert "Liunic" in data["reply"] or "Colorbox" in data["reply"]

        # Severe complaint -> escalates to Hendra
        payload_esc = {
            "sender": "628999888777",
            "customer_name": "Agus",
            "message": "Barang cacat dan robek parah, saya minta ganti rugi dan mau bicara dengan atasan!"
        }
        r2 = await ac.post("/api/whatsapp/simulate", json=payload_esc, headers=signed_in)
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2["routed_bot"] == "hendra"
        assert data2["bot_name"] == "Hendra"
        assert "Team Lead" in data2["bot_role"]
        assert data2["priority"] == "P1"

@pytest.mark.anyio
async def test_whatsapp_status_and_messages(signed_in):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/whatsapp/status", headers=signed_in)
        assert r.status_code == 200
        st = r.json()
        assert st["status"] == "ready"
        assert st["primary_agent"]["id"] == "siti"
        assert st["escalation_agent"]["id"] == "hendra"

        r_msgs = await ac.get("/api/whatsapp/messages", headers=signed_in)
        assert r_msgs.status_code == 200
        assert isinstance(r_msgs.json(), list)

@pytest.mark.anyio
async def test_tools_integrations_overview(signed_in):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/tools/integrations", headers=signed_in)
        assert r.status_code == 200
        data = r.json()
        assert "tools" in data
        tool_ids = [t["id"] for t in data["tools"]]
        assert "gdrive" in tool_ids
        assert "gmail" in tool_ids
        assert "notion" in tool_ids
        assert "whatsapp" in tool_ids

def test_colorbox_kb_size_exchange_grounding():
    bot, intent, _ = classify_and_route("Halo kak, kalau baju saya kekecilan apakah bisa tukar ukuran?")
    assert bot == "siti"
    assert intent == "RETURN_REFUND"
    reply = generate_cs_reply(bot, "Dian", "baju kekecilan mau tukar ukuran", intent, "P2")
    assert "belum melayani penukaran ukuran" in reply or "size exchange" in reply
    assert "7 hari" in reply
    assert "refund" in reply

def test_colorbox_kb_shipping_sla_grounding():
    bot, intent, _ = classify_and_route("Berapa lama estimasi pengiriman ke luar jawa?")
    assert bot == "siti"
    assert intent == "SHIPPING_DELIVERY"
    reply = generate_cs_reply(bot, "Dian", "Berapa lama estimasi pengiriman?", intent, "P2")
    assert "Jabodetabek" in reply
    assert "Pulau Jawa" in reply
    assert "Luar Pulau Jawa" in reply

def test_colorbox_kb_payment_methods_grounding():
    bot, intent, _ = classify_and_route("Metode pembayaran apa saja yang bisa digunakan di website?")
    assert bot == "siti"
    assert intent == "PAYMENT"
    reply = generate_cs_reply(bot, "Dian", "metode pembayaran apa saja", intent, "P2")
    assert "Virtual Account" in reply
    assert "QRIS" in reply
    assert "COD" in reply

def test_colorbox_kb_cancellation_grounding():
    bot, intent, _ = classify_and_route("Kak saya mau batalkan pesanan saya apakah masih bisa?")
    assert bot == "siti"
    assert intent == "CANCELLATION"
    reply = generate_cs_reply(bot, "Dian", "mau batalkan pesanan", intent, "P2")
    assert "kurir" in reply or "ekspedisi" in reply
    assert "7 hari" in reply
