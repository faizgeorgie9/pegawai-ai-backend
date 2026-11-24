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

def test_complaint_general_without_details():
    # User says: "saya ingin komplain"
    bot_id, intent, priority = whatsapp.classify_and_route("saya ingin komplain")
    assert bot_id == "hendra"
    assert intent == "COMPLAINT_GENERAL"
    reply = whatsapp.generate_cs_reply(bot_id, "Doni", "saya ingin komplain", intent, priority)
    assert "Mau komplain" in reply or "komplain apa" in reply.lower()
    assert "siap membantu" in reply.lower()

    # English spelling with c: "saya ingin complain"
    bot_id_c, intent_c, _ = whatsapp.classify_and_route("saya ingin complain")
    assert bot_id_c == "hendra"
    assert intent_c == "COMPLAINT_GENERAL"

def test_complaint_missing_items():
    # User says: "Barang saya ada yang kurang"
    bot_id, intent, priority = whatsapp.classify_and_route("Barang saya ada yang kurang")
    assert bot_id == "hendra"
    assert intent == "COMPLAINT_MISSING"
    reply = whatsapp.generate_cs_reply(bot_id, "Siska", "Barang saya ada yang kurang", intent, priority)
    assert "apa ya yang kurang" in reply
    assert "bukti pembelian" in reply

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

@pytest.mark.anyio
async def test_human_agent_takeover_and_pause_flow():
    test_sender = "6289998887771"
    whatsapp.resume_sender(test_sender) # Ensure clean start
    
    # 1. Customer asks for human staff
    res1 = await whatsapp.route_and_process_message(
        user_id="default",
        sender=test_sender,
        customer_name="Rian",
        message="Saya mau bicara dengan staf manusia ya min"
    )
    assert res1["status"] == "needs_human"
    assert res1["intent"] == "HUMAN_TAKEOVER"
    assert "staf manusia" in res1["reply"].lower()
    assert whatsapp.is_sender_paused(test_sender) is True

    # 2. Customer sends follow-up while paused -> bot must NOT reply!
    res2 = await whatsapp.route_and_process_message(
        user_id="default",
        sender=test_sender,
        customer_name="Rian",
        message="Halo, kok lama belum dibalas ya?"
    )
    assert res2["status"] == "needs_human"
    assert res2["reply"] == ""
    assert res2["paused"] is True

    # 3. Customer reactivates bot using resume bot
    res3 = await whatsapp.route_and_process_message(
        user_id="default",
        sender=test_sender,
        customer_name="Rian",
        message="resume bot"
    )
    assert res3["status"] == "replied"
    assert res3["intent"] == "BOT_RESUME"
    assert "telah aktif kembali" in res3["reply"]
    assert whatsapp.is_sender_paused(test_sender) is False

    # 4. Customer pauses using pause bot
    res4 = await whatsapp.route_and_process_message(
        user_id="default",
        sender=test_sender,
        customer_name="Rian",
        message="pause bot"
    )
    assert res4["status"] == "needs_human"
    assert res4["intent"] == "HUMAN_TAKEOVER"
    assert whatsapp.is_sender_paused(test_sender) is True

def test_language_detection():
    # English tests
    assert whatsapp.detect_language("Do you have denim jacket in size L?") == "en"
    assert whatsapp.detect_language("Where is my order CBX-98214?") == "en"
    assert whatsapp.detect_language("I want to complain, my shirt has a hole") == "en"
    assert whatsapp.detect_language("Can I please speak to a real person or human agent?") == "en"
    assert whatsapp.detect_language("Hello, how much is the shipping cost to Bali?") == "en"
    assert whatsapp.detect_language("Is the oversize blazer available in stock?") == "en"

    # Indonesian tests
    assert whatsapp.detect_language("Gimana resep bikin kue bolu pandan?") == "id"
    assert whatsapp.detect_language("Barang saya ada yang kurang") == "id"
    assert whatsapp.detect_language("Saya ingin komplain min") == "id"
    assert whatsapp.detect_language("Min baju saya cacat robek nih!") == "id"
    assert whatsapp.detect_language("Boleh tahu ongkir ke Surabaya berapa ya kak?") == "id"

def test_english_customer_size_and_shipping():
    # Sizing query in English -> Siti
    bot_id, intent, priority = whatsapp.classify_and_route("Do you have denim jacket in size L?")
    assert bot_id == "siti"
    assert intent == "SIZE_FIT"
    reply = whatsapp.generate_cs_reply(bot_id, "Sarah", "Do you have denim jacket in size L?", intent, priority)
    assert "Siti" in reply
    assert "XS to XL" in reply
    assert "height & weight" in reply
    assert len(reply.split()) < 45

    # Shipping delivery query in English -> Siti
    bot_id_s, intent_s, priority_s = whatsapp.classify_and_route("Where is my order CBX-98214? When will it arrive?")
    assert bot_id_s == "siti"
    assert intent_s == "SHIPPING_DELIVERY"
    reply_s = whatsapp.generate_cs_reply(bot_id_s, "Michael", "Where is my order CBX-98214? When will it arrive?", intent_s, priority_s)
    assert "2-4 business days" in reply_s
    assert "tracking" in reply_s.lower() or "order" in reply_s.lower()
    assert len(reply_s.split()) < 45

def test_english_customer_complaints_flow():
    # 1. General complaint without details -> Hendra asks what the issue is
    bot_id_g, intent_g, prio_g = whatsapp.classify_and_route("I want to file a complaint")
    assert bot_id_g == "hendra"
    assert intent_g == "COMPLAINT_GENERAL"
    reply_g = whatsapp.generate_cs_reply(bot_id_g, "David", "I want to file a complaint", intent_g, prio_g)
    assert "Hendra" in reply_g
    assert "details of your issue" in reply_g or "ready to help" in reply_g

    # 2. Missing items complaint -> Hendra asks which items are missing & proof of purchase
    bot_id_m, intent_m, prio_m = whatsapp.classify_and_route("My package is missing an item")
    assert bot_id_m == "hendra"
    assert intent_m == "COMPLAINT_MISSING"
    reply_m = whatsapp.generate_cs_reply(bot_id_m, "Emily", "My package is missing an item", intent_m, prio_m)
    assert "Hendra" in reply_m
    assert "Which item is missing" in reply_m
    assert "proof of purchase" in reply_m or "order number" in reply_m

    # 3. Damaged item incomplete -> Proactive human CS checklist
    bot_id_d, intent_d, prio_d = whatsapp.classify_and_route("The jacket I received is defective and torn!")
    assert bot_id_d == "hendra"
    assert intent_d == "COMPLAINT_DAMAGED"
    reply_d = whatsapp.generate_cs_reply(bot_id_d, "Jessica", "The jacket I received is defective and torn!", intent_d, prio_d)
    assert "Order Number / Invoice" in reply_d
    assert "Clothing Item Name" in reply_d
    assert "Photo of the defect" in reply_d
    assert len(reply_d.split()) < 65

    # 4. Damaged item complete with order code
    bot_id_c, intent_c, prio_c = whatsapp.classify_and_route("The dress is torn, invoice code CBX-88321")
    assert bot_id_c == "hendra"
    assert intent_c == "COMPLAINT_DAMAGED"
    reply_c = whatsapp.generate_cs_reply(bot_id_c, "Amanda", "The dress is torn, invoice code CBX-88321", intent_c, prio_c)
    assert "verifying" in reply_c.lower() or "reviewing" in reply_c.lower()
    assert len(reply_c.split()) < 45

def test_english_customer_out_of_scope():
    bot_id, intent, priority = whatsapp.classify_and_route("How do I write a python function for binary search?")
    assert bot_id == "siti"
    assert intent == "OUT_OF_SCOPE"
    reply = whatsapp.generate_cs_reply(bot_id, "Alex", "How do I write a python function for binary search?", intent, priority)
    assert "outside of Siti's scope" in reply
    assert "casual outfits" in reply
    assert len(reply.split()) < 45

@pytest.mark.anyio
async def test_english_customer_human_takeover_and_routing():
    test_sender_en = "14155552671"
    whatsapp.resume_sender(test_sender_en)

    # 1. Customer asks for live human agent in English
    res1 = await whatsapp.route_and_process_message(
        user_id="default",
        sender=test_sender_en,
        customer_name="George",
        message="Can I please talk to a human agent?"
    )
    assert res1["status"] == "needs_human"
    assert res1["intent"] == "HUMAN_TAKEOVER"
    assert res1["language"] == "en"
    assert "transferred to our Customer Service team" in res1["reply"]
    assert whatsapp.is_sender_paused(test_sender_en) is True

    # 2. Customer chats while paused -> no bot reply
    res2 = await whatsapp.route_and_process_message(
        user_id="default",
        sender=test_sender_en,
        customer_name="George",
        message="Hello, is anyone there?"
    )
    assert res2["status"] == "needs_human"
    assert res2["reply"] == ""
    assert res2["paused"] is True

    # 3. Customer reactivates bot
    res3 = await whatsapp.route_and_process_message(
        user_id="default",
        sender=test_sender_en,
        customer_name="George",
        message="resume bot"
    )
    assert res3["status"] == "replied"
    assert res3["intent"] == "BOT_RESUME"
    assert "back active" in res3["reply"]
    assert whatsapp.is_sender_paused(test_sender_en) is False


