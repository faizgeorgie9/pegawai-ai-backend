import pytest
from bff import whatsapp

def test_out_of_scope_detection():
    bot_id, intent, priority = whatsapp.classify_and_route("Gimana resep bikin kue bolu pandan?")
    assert bot_id == "siti"
    assert intent == "OUT_OF_SCOPE"
    reply = whatsapp.generate_cs_reply(bot_id, "Budi", "Gimana resep bikin kue bolu pandan?", intent, priority)
    assert "di luar ranah dan scope" in reply
    assert "Siti" in reply
    # Must be concise
    assert len(reply.split()) < 40

def test_incomplete_complaint_human_cs_followup():
    bot_id, intent, priority = whatsapp.classify_and_route("Min baju saya cacat robek nih!")
    assert bot_id == "hendra"
    assert intent == "COMPLAINT_DAMAGED"
    reply = whatsapp.generate_cs_reply(bot_id, "Anita", "Min baju saya cacat robek nih!", intent, priority)
    # Check that Hendra proactively asks for the 3 missing details:
    assert "Hendra" in reply
    assert "Nomor Pesanan / Invoice" in reply
    assert "Nama Item" in reply
    assert "Foto barcode tag produk" in reply
    # Concise and structured
    assert len(reply.split()) < 65

def test_complete_complaint_verification():
    bot_id, intent, priority = whatsapp.classify_and_route("Baju robek min, nomor invoice CBX-98214")
    assert bot_id == "hendra"
    assert intent == "COMPLAINT_DAMAGED"
    reply = whatsapp.generate_cs_reply(bot_id, "Citra", "Baju robek min, nomor invoice CBX-98214", intent, priority)
    assert "Hendra" in reply
    assert "verifikasi" in reply
    assert len(reply.split()) < 45

def test_duplicate_message_prevention():
    test_id = "test_msg_dup_99999"
    # First time: not duplicate
    assert whatsapp.is_duplicate_message(test_id) is False
    # Second time within TTL: duplicate
    assert whatsapp.is_duplicate_message(test_id) is True

def test_evolution_webhook_filters_non_upsert():
    # Only messages.upsert should be parsed, not messages.update or ack
    update_payload = {
        "event": "messages.update",
        "data": {
            "key": {"id": "123", "fromMe": False, "remoteJid": "628123@s.whatsapp.net"},
            "message": {"conversation": "Halo"}
        }
    }
    assert len(whatsapp.parse_webhook_payload(update_payload)) == 0

    upsert_payload = {
        "event": "messages.upsert",
        "data": {
            "key": {"id": "124", "fromMe": False, "remoteJid": "628123@s.whatsapp.net"},
            "message": {"conversation": "Halo"}
        }
    }
    res = whatsapp.parse_webhook_payload(upsert_payload)
    assert len(res) == 1
    assert res[0]["message"] == "Halo"
