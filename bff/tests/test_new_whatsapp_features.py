import pytest
from bff import whatsapp

def test_out_of_scope_detection():
    bot_id, intent, priority = whatsapp.classify_and_route("Gimana resep bikin kue bolu pandan?")
    assert bot_id == "siti"
    assert intent == "OUT_OF_SCOPE"
    reply = whatsapp.generate_cs_reply(bot_id, "Budi", "Gimana resep bikin kue bolu pandan?", intent, priority)
    assert "di luar ranah dan scope" in reply
    assert "Siti" in reply

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

def test_complete_complaint_verification():
    bot_id, intent, priority = whatsapp.classify_and_route("Baju robek min, nomor invoice CBX-98214")
    assert bot_id == "hendra"
    assert intent == "COMPLAINT_DAMAGED"
    reply = whatsapp.generate_cs_reply(bot_id, "Citra", "Baju robek min, nomor invoice CBX-98214", intent, priority)
    assert "Hendra" in reply
    assert "verifikasi" in reply
