"""WhatsApp Business API & Routing for Customer Support (Stage 4 Day 4).
Supports Meta WhatsApp Cloud API webhooks (verification and incoming messages)
and direct CS routing between Siti (Frontline Support) and Hendra (CS Team Lead / Escalation).
"""
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
import time
from pathlib import Path
from typing import Any, Optional, Tuple

from . import config, db
from .errors import ApiError

log = logging.getLogger("bff.whatsapp")

WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "pegawai_ai_wa_verify_secret")
WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")

# Evolution API (Baileys without browser - Ultra Lightweight)
EVOLUTION_API_URL = os.environ.get("EVOLUTION_API_URL", "http://127.0.0.1:8080").rstrip("/")
EVOLUTION_API_KEY = os.environ.get("EVOLUTION_API_KEY", "pegawai_ai_evolution_secret_key_2026")
EVOLUTION_INSTANCE = os.environ.get("EVOLUTION_INSTANCE", "colorbox")

# Deduplication cache for incoming WhatsApp messages (message_id -> timestamp)
_seen_message_ids: dict[str, float] = {}

def is_duplicate_message(message_id: Optional[str]) -> bool:
    """Return True if message_id was already processed recently within 5 minutes."""
    if not message_id:
        return False
    now = time.time()
    # Evict expired entries older than 300 seconds
    expired = [k for k, ts in list(_seen_message_ids.items()) if now - ts > 300]
    for k in expired:
        _seen_message_ids.pop(k, None)
    
    if message_id in _seen_message_ids:
        return True
    _seen_message_ids[message_id] = now
    return False

# Language Detection Stopwords (Zero-dependency, fast & accurate)
ENGLISH_STOPWORDS = {
    "the", "is", "are", "am", "was", "were", "i", "you", "we", "they", "he", "she", "it",
    "my", "your", "our", "their", "this", "that", "these", "those", "can", "could", "would",
    "should", "will", "do", "does", "did", "have", "has", "had", "what", "where", "when",
    "how", "why", "who", "which", "want", "need", "please", "help", "thank", "thanks",
    "hello", "hi", "good", "morning", "afternoon", "evening", "with", "from", "about",
    "for", "in", "on", "at", "to", "not", "any", "some", "there", "an", "a", "much", "many",
    "item", "items", "order", "package", "shipping", "delivery", "track", "tracking", "received"
}

INDONESIAN_STOPWORDS = {
    "yang", "di", "ke", "dari", "ini", "itu", "dan", "atau", "saya", "aku", "kamu", "kami",
    "kita", "mereka", "dia", "kak", "min", "kakak", "halo", "hai", "mau", "ingin", "bisa",
    "tolong", "bantu", "ada", "tidak", "nggak", "gak", "ya", "nih", "dong", "saja", "apa",
    "kenapa", "gimana", "kapan", "siapa", "mana", "sudah", "udah", "belum", "lagi", "baju",
    "celana", "pesanan", "barang", "kirim", "ongkir", "resi", "kurang", "cacat", "rusak",
    "robek", "retur", "tukar", "staf", "manusia", "kok", "kan", "lah", "deh", "punya", "sama"
}

# Sender language preference memory cache: {clean_sender: "en" | "id"}
_sender_languages: dict[str, str] = {}

def get_sender_language(sender: str) -> str:
    """Retrieve saved language preference for sender, default to 'id'."""
    clean_sender = "".join(filter(str.isdigit, sender)) or sender
    return _sender_languages.get(clean_sender, "id")

def set_sender_language(sender: str, lang: str) -> None:
    """Persist language preference for sender."""
    clean_sender = "".join(filter(str.isdigit, sender)) or sender
    _sender_languages[clean_sender] = lang

def detect_language(message: str, fallback_lang: str = "id") -> str:
    """Detect whether message is primarily in English ('en') or Indonesian ('id').
    Defaults to fallback_lang for fashion store context if ambiguous.
    """
    if not message:
        return fallback_lang
    words = re.findall(r"\b[a-zA-Z]+\b", message.lower())
    if not words:
        return fallback_lang
    
    en_score = sum(1 for w in words if w in ENGLISH_STOPWORDS)
    id_score = sum(1 for w in words if w in INDONESIAN_STOPWORDS)
    
    # Check distinct English multi-word starters or phrases
    lower = message.lower().strip()
    english_starters = (
        "hello", "hi there", "good morning", "good afternoon", "good evening",
        "do you have", "where is", "i want", "can i", "is there", "how much",
        "i need", "please help", "my order", "i would like", "what is", "can you"
    )
    if any(lower.startswith(starter) for starter in english_starters):
        en_score += 2
        
    if en_score > id_score:
        return "en"
    elif id_score > en_score:
        return "id"
    return fallback_lang

# Human Agent Takeover cache: {clean_sender: expiration_timestamp}
_paused_senders: dict[str, float] = {}

def pause_sender(sender: str, duration_seconds: int = 7200) -> None:
    """Pause automatic bot replies for a specific customer to allow human agent takeover."""
    clean_sender = "".join(filter(str.isdigit, sender)) or sender
    _paused_senders[clean_sender] = time.time() + duration_seconds
    log.info("Sender %s paused for %ds (Human Agent Takeover active)", clean_sender, duration_seconds)

def resume_sender(sender: str) -> None:
    """Resume automatic bot replies for a specific customer."""
    clean_sender = "".join(filter(str.isdigit, sender)) or sender
    _paused_senders.pop(clean_sender, None)
    log.info("Sender %s resumed (Bot replies reactivated)", clean_sender)

def is_sender_paused(sender: str) -> bool:
    """Check if automatic bot replies are currently paused for a specific customer."""
    clean_sender = "".join(filter(str.isdigit, sender)) or sender
    exp = _paused_senders.get(clean_sender)
    if not exp:
        return False
    if time.time() > exp:
        _paused_senders.pop(clean_sender, None)
        return False
    return True

def get_paused_senders() -> list[dict]:
    """List all currently paused senders."""
    now = time.time()
    results = []
    expired = []
    for s_id, exp in list(_paused_senders.items()):
        if now > exp:
            expired.append(s_id)
        else:
            results.append({
                "sender": s_id,
                "remaining_seconds": int(exp - now),
                "expires_at": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()
            })
    for s in expired:
        _paused_senders.pop(s, None)
    return results

# Triggers for Human Agent Takeover (Handover to live human CS staff)
HUMAN_TAKEOVER_KEYWORDS = {
    # Indonesian
    "bicara dengan staf manusia", "bicara dengan manusia", "minta cs asli", "mau ngomong sama manusia",
    "hubungkan ke manusia", "mau cs asli", "admin manusia", "cs asli", "staf asli", "orang asli",
    "bukan bot", "bicara dengan orang", "jangan bot", "oper ke manusia", "transfer ke manusia",
    "sambungkan ke manusia", "mau manusia", "ngomong sama orang", "staf manusia",
    "pause bot", "stop bot", "matikan bot", "jeda bot",
    # English
    "live agent", "human agent", "talk to human", "speak with human", "speak to human",
    "talk to a person", "speak to a person", "real person", "human support", "human staff",
    "human representative", "talk to agent", "speak to agent", "connect to agent", "connect to human",
    "speak to someone", "talk to someone"
}

# Triggers to reactivate the bot
BOT_RESUME_KEYWORDS = {
    "aktifkan bot", "resume bot", "mulai bot", "kembali ke bot", "hidupkan bot", "unpause bot", "start bot", "reactivate bot"
}

# Escalation triggers that route directly to Hendra (CS Team Lead)
ESCALATION_KEYWORDS = {
    # Indonesian
    "cacat", "rusak", "robek", "reject", "kecewa", "tuntut", "kasus", "somasi",
    "refund", "kembalikan uang", "ganti rugi", "tipu", "penipuan",
    "manajer", "manager", "supervisor", "atasan", "lead", "bos", "pimpinan",
    "lapor", "konsumen", "perlindungan konsumen", "bpom", "polisi",
    "komplain", "complain", "komplen", "keluhan", "complaint", "kendala", "masalah",
    "kurang", "ketinggalan", "hilang", "salah kirim",
    # English
    "damaged", "defective", "torn", "broken", "scam", "fraud", "lawyer",
    "missing", "lost item", "wrong item", "wrong order", "dissatisfied"
}

# General intents
INTENT_KEYWORDS = {
    "RETURN_REFUND": [
        "retur", "tukar", "kembali", "pengembalian", "salah ukuran", "kebesaran", "kekecilan",
        "return", "refund", "exchange", "too big", "too small", "wrong size"
    ],
    "SHIPPING_DELIVERY": [
        "ongkir", "resi", "lacak", "ekspedisi", "kapan sampai", "pengiriman", "jne", "sicepat",
        "shipping", "delivery", "track", "tracking", "courier", "when will it arrive",
        "where is my order", "where is my package", "shipping fee", "shipping cost"
    ],
    "SIZE_FIT": [
        "ukuran", "size", "ld", "lingkar dada", "panjang", "cm", "fitting", "bb", "tb",
        "sizing", "measurement", "fit", "fits", "bust", "waist", "chest", "chart"
    ],
    "PRODUCT_AVAILABILITY": [
        "ready", "stok", "tersedia", "ada gak", "restok", "habis",
        "available", "in stock", "stock", "sold out", "restock", "is it ready"
    ],
    "PRODUCT_INFO": [
        "bahan", "koleksi", "warna", "katalog", "liunic", "denim", "blazer", "dress", "promo", "diskon",
        "material", "fabric", "collection", "color", "catalogue", "catalog", "discount", "sale", "price", "how much"
    ],
}

# Retail & Fashion context keywords (In-scope for Colorbox / Pegawai AI CS)
RETAIL_FASHION_KEYWORDS = {
    "halo", "hai", "hi", "p", "oi", "tes", "test", "siang", "pagi", "sore", "malam",
    "assalamualaikum", "permisi", "admin", "cs", "kak", "min", "tanya", "mau tanya",
    "bisa bantu", "tolong", "bantuan", "info", "informasi",
    "baju", "celana", "kemeja", "dress", "rok", "jaket", "blazer", "kaos", "tshirt", "t-shirt",
    "crop", "oversized", "oversize", "denim", "jeans", "linen", "katun", "cotton", "knit",
    "rajut", "bahan", "warna", "katalog", "liunic", "koleksi", "outfit", "ootd", "model",
    "diskon", "promo", "sale", "voucher", "kupon", "harga", "berapa", "rp", "murah",
    "ukuran", "size", "chart", "ld", "lingkar", "dada", "panjang", "cm", "bb", "tb",
    "fitting", "muat", "kebesaran", "kekecilan", "sempit", "longgar",
    "ready", "stok", "stock", "ada", "tersedia", "restock", "restok", "habis",
    "order", "pesanan", "pesan", "beli", "checkout", "co", "bayar", "pembayaran", "transfer",
    "rekening", "qris", "cod", "invoice", "struk", "nota",
    "ongkir", "ongkos", "kirim", "pengiriman", "ekspedisi", "resi", "lacak", "jne", "sicepat",
    "jnt", "j&t", "anteraja", "pos", "kapan sampai", "estimasi",
    "cacat", "rusak", "robek", "sobek", "kotor", "noda", "reject", "retur", "tukar", "kembali",
    "pengembalian", "refund", "salah kirim", "kurang", "ganti", "komplain", "kecewa",
    "toko", "store", "offline", "mall", "outlet", "cabang", "buka", "tutup", "lokasi", "alamat",
    # English terms
    "hello", "hey", "good morning", "good afternoon", "good evening", "clothing", "clothes",
    "shirt", "pants", "skirt", "jacket", "fabric", "material", "available", "shipping",
    "delivery", "courier", "damaged", "torn", "defective", "return", "exchange", "complaint"
}

# Explicit out-of-scope triggers (Not relevant to fashion store / retail CS)
OUT_OF_SCOPE_EXPLICIT_KEYWORDS = {
    "resep", "masak", "masakan", "makanan", "kuliner", "kue", "goreng", "minuman", "kopi",
    "cuaca", "hujan", "gempa", "bmkg", "suhu",
    "crypto", "bitcoin", "btc", "eth", "saham", "trading", "investasi", "forex", "binance",
    "politik", "presiden", "pemilu", "pilpres", "partai", "dpr", "menteri", "pemerintah",
    "coding", "python", "javascript", "php", "golang", "java", "c++", "html", "css", "sql", "database",
    "matematika", "fisika", "kimia", "biologi", "rumus", "tugas sekolah", "skripsi", "kuliah", "ujian", "pr",
    "motor", "mobil", "bengkel", "otomotif", "oli", "ban", "karburator", "mesin motor",
    "dokter", "obat", "penyakit", "gejala", "resep dokter", "rumah sakit", "klinik", "diagnosis",
    "game", "mobile legends", "mlbb", "free fire", "ff", "pubg", "genshin", "steam", "playstation",
    "hotel", "tiket pesawat", "travel", "wisata", "liburan",
    # English
    "recipe", "cooking", "crypto", "bitcoin", "stocks", "trading", "politics", "president", "election",
    "coding", "programming", "python", "javascript", "homework", "exam", "doctor", "medicine", "disease"
}

def verify_token(hub_mode: str, hub_verify_token: str, hub_challenge: str) -> str:
    """Verify Meta WhatsApp Webhook handshake."""
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        log.info("WhatsApp webhook verified successfully.")
        return hub_challenge
    raise ApiError(403, "Verifikasi token WhatsApp tidak valid")

def parse_webhook_payload(payload: dict) -> list[dict]:
    """Parse incoming webhook from Meta Cloud API or direct simulation payload."""
    messages = []
    
    # Check Meta Cloud API format: entry[].changes[].value.messages[]
    if "entry" in payload and isinstance(payload["entry"], list):
        for entry in payload["entry"]:
            for change in entry.get("changes", []):
                val = change.get("value", {})
                contacts = {c.get("wa_id"): c.get("profile", {}).get("name", "Pelanggan") for c in val.get("contacts", [])}
                for msg in val.get("messages", []):
                    sender = msg.get("from", "")
                    msg_type = msg.get("type", "text")
                    body = ""
                    if msg_type == "text":
                        body = msg.get("text", {}).get("body", "")
                    elif msg_type == "button":
                        body = msg.get("button", {}).get("text", "")
                    elif msg_type == "interactive":
                        interactive = msg.get("interactive", {})
                        body = interactive.get("button_reply", {}).get("title") or interactive.get("list_reply", {}).get("title", "")
                    
                    if sender and body:
                        messages.append({
                            "sender": sender,
                            "customer_name": contacts.get(sender, "Pelanggan"),
                            "message": body.strip(),
                            "message_id": msg.get("id"),
                            "timestamp": msg.get("timestamp"),
                            "raw": msg
                        })
        return messages

    # Check Evolution API format (Baileys WebSocket without browser)
    event_name = str(payload.get("event") or "").strip().lower()
    data_obj = payload.get("data")
    if event_name in ("messages.upsert", "messages.upsert-media") and isinstance(data_obj, dict):
        key = data_obj.get("key", {})
        from_me = key.get("fromMe", False)
        # Process inbound messages from customer only (ignore bot's own outbound messages)
        if not from_me:
            remote_jid = key.get("remoteJid", "")
            # e.g. 62812345678@s.whatsapp.net
            sender = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid
            customer_name = data_obj.get("pushName") or "Pelanggan"
            msg_obj = data_obj.get("message") or {}
            
            body = (
                msg_obj.get("conversation") or
                msg_obj.get("extendedTextMessage", {}).get("text") or
                msg_obj.get("imageMessage", {}).get("caption") or
                msg_obj.get("videoMessage", {}).get("caption") or
                ""
            )
            if sender and body:
                messages.append({
                    "sender": sender,
                    "customer_name": customer_name,
                    "message": str(body).strip(),
                    "message_id": key.get("id") or f"evo_{uuid.uuid4().hex[:12]}",
                    "timestamp": str(data_obj.get("messageTimestamp") or int(datetime.now(timezone.utc).timestamp())),
                    "raw": payload
                })
        return messages

    # Check Direct Simulation / Simple JSON format
    sender = payload.get("sender") or payload.get("from") or payload.get("phone")
    message = payload.get("message") or payload.get("text") or payload.get("body")
    if sender and message:
        messages.append({
            "sender": str(sender).strip(),
            "customer_name": payload.get("customer_name") or payload.get("name") or "Pelanggan",
            "message": str(message).strip(),
            "bot_id": payload.get("bot_id"),
            "message_id": payload.get("message_id") or f"sim_{uuid.uuid4().hex[:12]}",
            "timestamp": payload.get("timestamp") or str(int(datetime.now(timezone.utc).timestamp())),
            "raw": payload
        })
    return messages

def has_order_details(message: str) -> bool:
    """Check if customer provided specific order identifier (invoice, order id, resi)."""
    msg_lower = message.lower()
    return bool(re.search(r'\b(cbx|inv|order|pesanan|resi|tracking|track|no\.?|nomor|number|code|kode)\s*[-:#]?\s*[a-z0-9]{3,}\b|\b\d{5,}\b', msg_lower))

def classify_and_route(message: str, requested_bot: Optional[str] = None) -> Tuple[str, str, str]:
    """Route message to appropriate CS bot: Siti (Frontline) or Hendra (Lead/Escalation).
    Returns (bot_id, intent, priority)."""
    if requested_bot in ("siti", "hendra"):
        bot_id = requested_bot
    else:
        bot_id = "siti"

    msg_lower = message.lower()

    # 0. Check bot resume or human agent takeover requests
    if any(re.search(rf"\b{re.escape(kw)}\b", msg_lower) for kw in BOT_RESUME_KEYWORDS):
        return "siti", "BOT_RESUME", "P2"

    if any(re.search(rf"\b{re.escape(kw)}\b", msg_lower) for kw in HUMAN_TAKEOVER_KEYWORDS):
        return "hendra", "HUMAN_TAKEOVER", "P1"
    
    # 1. Check explicit out-of-scope triggers (cooking, crypto, politics, coding, homework, automotive, health, gaming)
    is_explicit_out_of_scope = any(re.search(rf"\b{kw}\b", msg_lower) for kw in OUT_OF_SCOPE_EXPLICIT_KEYWORDS)
    if is_explicit_out_of_scope:
        return "siti", "OUT_OF_SCOPE", "P3"

    # 2. Check complaints & issues (Hendra - CS Team Lead)
    # 2a. Missing items / incomplete order
    is_missing = any(re.search(rf"\b{kw}\b", msg_lower) for kw in [
        "kurang", "ketinggalan", "hilang", "tidak lengkap", "ga lengkap", "gak lengkap",
        "missing", "incomplete", "left out", "lost"
    ])
    if is_missing and any(w in msg_lower for w in ["barang", "item", "items", "paket", "pesanan", "baju", "celana", "isi", "order", "package", "parcel", "ada", "yang"]):
        return "hendra", "COMPLAINT_MISSING", "P1"

    # 2b. General complaint without specific details
    is_complaint_word = any(re.search(rf"\b{kw}\b", msg_lower) for kw in ["komplain", "complain", "komplen", "keluhan", "complaint"])
    has_specific_detail = any(re.search(rf"\b{kw}\b", msg_lower) for kw in [
        "cacat", "rusak", "robek", "sobek", "kotor", "reject", "kurang", "salah", "retur", "tukar", "refund",
        "damaged", "defective", "torn", "broken", "missing", "wrong"
    ])
    if is_complaint_word and not has_specific_detail:
        return "hendra", "COMPLAINT_GENERAL", "P1"

    # 2c. Wrong item sent
    is_wrong_item = any(re.search(rf"\b{kw}\b", msg_lower) for kw in [
        "salah kirim", "salah barang", "beda barang", "tidak sesuai", "ga sesuai", "gak sesuai", "salah warna", "salah ukuran", "salah size",
        "wrong item", "wrong product", "wrong size", "wrong color", "incorrect item", "different item"
    ])
    if is_wrong_item:
        return "hendra", "COMPLAINT_WRONG_ITEM", "P1"

    # 2d. Damaged / defective product
    is_damaged = any(re.search(rf"\b{kw}\b", msg_lower) for kw in [
        "cacat", "rusak", "robek", "sobek", "kotor", "reject", "noda", "bolong",
        "damaged", "defective", "torn", "broken", "stained", "hole", "flaw", "flawed"
    ])
    if is_damaged:
        return "hendra", "COMPLAINT_DAMAGED", "P1"

    # 2e. Return / refund escalation
    is_refund = any(re.search(rf"\b{kw}\b", msg_lower) for kw in ["refund", "kembalikan uang", "ganti rugi", "money back"])
    if is_refund:
        return "hendra", "RETURN_REFUND", "P1"

    # 2f. Other managerial escalations
    is_escalated = any(re.search(rf"\b{kw}\b", msg_lower) for kw in ESCALATION_KEYWORDS)
    if is_escalated and not requested_bot:
        return "hendra", "COMPLAINT_GENERAL", "P1"

    # 3. Determine general retail intents for Frontline (Siti)
    intent = "PRODUCT_INFO"
    for candidate_intent, keywords in INTENT_KEYWORDS.items():
        if any(re.search(rf"\b{kw}\b", msg_lower) for kw in keywords):
            intent = candidate_intent
            break

    priority = "P2" if intent in ("RETURN_REFUND", "SHIPPING_DELIVERY", "SIZE_FIT") else "P3"
    return bot_id, intent, priority

def generate_cs_reply(bot_id: str, customer_name: str, message: str, intent: str, priority: str, language: Optional[str] = None) -> str:
    """Generate grounded customer support reply following Colorbox CS SOP (concise & to the point).
    Supports bilingual responses (Indonesian & English).
    """
    lang = language or detect_language(message)
    msg_lower = message.lower()

    if lang == "en":
        c_name = customer_name if customer_name and customer_name not in ("Pelanggan", "Kak") else "there"
        if bot_id == "hendra":
            has_order = has_order_details(message)
            if intent == "HUMAN_TAKEOVER":
                return (
                    f"Certainly {c_name}, the bot has been paused and your conversation is transferred to our Customer Service team (human staff) at Colorbox Indonesia. "
                    "Our team will reply directly to this chat shortly 🙏 (Type 'resume bot' or 'start bot' to reactivate the bot)."
                )
            elif intent == "COMPLAINT_GENERAL":
                return (
                    f"Hello {c_name}, I am Hendra, Customer Service Team Lead at Colorbox Indonesia. "
                    "We apologize for the inconvenience. Could you please share the details of your issue? We are ready to help 🙏"
                )
            elif intent == "COMPLAINT_MISSING":
                return (
                    f"Hello {c_name}, I am Hendra, Customer Service Team Lead at Colorbox Indonesia. "
                    "We apologize for the issue with your order. Which item is missing? "
                    "Please share your order number or proof of purchase so we can check it right away 🙏"
                )
            elif intent == "COMPLAINT_WRONG_ITEM":
                return (
                    f"Hello {c_name}, I am Hendra, Customer Service Team Lead at Colorbox Indonesia. "
                    "We apologize for the shipment mix-up. Could you please share your order number and a photo of the received item with its barcode tag? We'll arrange an exchange immediately 🙏"
                )
            elif intent == "COMPLAINT_DAMAGED":
                if not has_order:
                    return (
                        f"Hello {c_name}, I am Hendra, Customer Service Team Lead at Colorbox Indonesia. "
                        "We apologize for the defective item and are ready to assist with an exchange or refund.\n\n"
                        "Could you please provide:\n"
                        "1. 🧾 Order Number / Invoice\n"
                        "2. 👗 Clothing Item Name\n"
                        "3. 📸 Photo of the defect and barcode tag\n\n"
                        "We will process your request within 24 business hours. Thank you 🙏"
                    )
                else:
                    return (
                        f"Hello {c_name}, I am Hendra, Customer Service Team Lead at Colorbox Indonesia. "
                        "Thank you for providing your order number.\n\n"
                        "Our quality assurance & logistics team is currently verifying the issue. "
                        "We will provide an update regarding replacement or refund within 24 business hours 🙏"
                    )
            elif intent == "RETURN_REFUND":
                if not has_order:
                    return (
                        f"Hello {c_name}, I am Hendra, Customer Service Team Lead at Colorbox Indonesia. "
                        "For returns or refunds (max. 7 days, tags intact & unwashed), "
                        "please share your order number and reason for return so we can follow up right away 🙏"
                    )
                else:
                    return (
                        f"Hello {c_name}, I am Hendra, Customer Service Team Lead at Colorbox Indonesia. "
                        "Thank you for the order details. Your return/refund request is being reviewed by our team. "
                        "We will update you within 24 business hours 🙏"
                    )
            else:
                return (
                    f"Hello {c_name}, I am Hendra, Customer Service Team Lead at Colorbox Indonesia. "
                    "Could you please share your invoice number or issue details so I can assist you directly?"
                )
        else:
            # Siti: Warm, friendly, concise frontline support
            if intent == "BOT_RESUME":
                return (
                    f"Hello {c_name}! Colorbox virtual assistant is back active 😊 "
                    "How can Siti help you today with casual outfits, new promos, or order tracking?"
                )
            elif intent == "OUT_OF_SCOPE":
                return (
                    f"Hello {c_name}! Sorry, that question is outside of Siti's scope of assistance at Colorbox 😊\n\n"
                    "Is there anything I can help you with regarding Colorbox casual outfits, new collections, promos, or orders today?"
                )
            elif intent == "RETURN_REFUND":
                return (
                    f"Hello {c_name}! Product exchanges can be requested within 7 days of delivery (tags intact & unwashed) 😊 "
                    "Could you please provide your order number and desired replacement size?"
                )
            elif intent == "SHIPPING_DELIVERY":
                return (
                    f"Hello {c_name}! Regular Colorbox delivery takes 2-4 business days ✨ "
                    "Could you please share your order number or tracking number so Siti can check its latest status?"
                )
            elif intent == "SIZE_FIT":
                return (
                    f"Hello {c_name}! Colorbox sizing ranges from XS to XL (pants 26-32) 💕 "
                    "What item are you looking at, and could you share your approximate height & weight so Siti can recommend your ideal fit?"
                )
            elif intent == "PRODUCT_AVAILABILITY":
                return (
                    f"Hello {c_name}! Our latest Colorbox collection and Colorbox x Liunic drops are available online and in official stores ✨ "
                    "Please share the item name or photo, and Siti will check stock for you right away!"
                )
            else:
                return (
                    f"Hello {c_name}! Welcome to Colorbox Indonesia WhatsApp Support 💕 "
                    "How can Siti assist you today with our casual outfits, latest promos, or your order?"
                )

    # Default Indonesian responses
    c_name = customer_name if customer_name and customer_name != "Pelanggan" else "Kak"

    if bot_id == "hendra":
        has_order = has_order_details(message)
        # Authoritative, calm, highly empathetic managerial resolution
        if intent == "HUMAN_TAKEOVER":
            return (
                f"Baik {c_name}, bot telah dinonaktifkan sementara dan percakapan dialihkan ke Tim Customer Service (staf manusia) Colorbox Indonesia. "
                "CS manusia kami akan segera membalas langsung di chat ini ya Kak 🙏 (Ketik 'resume bot' atau 'aktifkan bot' jika ingin menyalakan bot kembali)."
            )
        elif intent == "COMPLAINT_GENERAL":
            return (
                f"Halo {c_name}, saya Hendra selaku Customer Service Team Lead Colorbox Indonesia. "
                "Mohon maaf atas ketidaknyamanannya ya Kak. Mau komplain terkait kendala apa ya Kak? Kami siap membantu 🙏"
            )
        elif intent == "COMPLAINT_MISSING":
            return (
                f"Halo {c_name}, saya Hendra selaku Customer Service Team Lead Colorbox Indonesia. "
                "Mohon maaf atas kendala pesanannya ya Kak. Untuk barangnya itu apa ya yang kurang? "
                "Boleh dilampirkan bukti pembelian atau nomor pesanannya untuk barang-barang yang kurang tersebut ya Kak, kami siap bantu cek langsung 🙏"
            )
        elif intent == "COMPLAINT_WRONG_ITEM":
            return (
                f"Halo {c_name}, saya Hendra selaku Customer Service Team Lead Colorbox Indonesia. "
                "Mohon maaf atas kekeliruan pengirimannya ya Kak. Boleh dibantu nomor pesanan serta foto produk yang diterima dan barcode tag-nya? Kami bantu proses penukaran barang yang sesuai 🙏"
            )
        elif intent == "COMPLAINT_DAMAGED":
            if not has_order:
                # Proactive human CS follow-up when complaint details are incomplete (concise)
                return (
                    f"Halo {c_name}, saya Hendra selaku Customer Service Team Lead Colorbox Indonesia. "
                    "Mohon maaf atas kendalanya ya Kak, kami siap bantu penukaran atau refund.\n\n"
                    "Boleh dibantu kirimkan:\n"
                    "1. 🧾 Nomor Pesanan / Invoice\n"
                    "2. 👗 Nama Item pakaian\n"
                    "3. 📸 Foto barcode tag produk dan kendala\n\n"
                    "Data akan langsung kami proses dalam 1x24 jam kerja. Terima kasih 🙏"
                )
            else:
                return (
                    f"Halo {c_name}, saya Hendra selaku Customer Service Team Lead Colorbox Indonesia. "
                    "Terima kasih atas nomor pesanannya.\n\n"
                    "Data kendala sedang kami verifikasi bersama tim quality assurance & logistik. "
                    "Solusi penukaran atau refund akan kami infokan dalam 1x24 jam kerja ya Kak. Mohon ditunggu 🙏"
                )
        elif intent == "RETURN_REFUND":
            if not has_order:
                return (
                    f"Halo {c_name}, saya Hendra selaku Customer Service Team Lead Colorbox Indonesia. "
                    "Untuk retur/refund (maks. 7 hari, tag utuh & belum dicuci), "
                    "boleh infokan nomor pesanan dan alasan pengembalian agar langsung kami tindak lanjuti hari ini?"
                )
            else:
                return (
                    f"Halo {c_name}, saya Hendra selaku Customer Service Team Lead Colorbox Indonesia. "
                    "Terima kasih atas nomor pesanannya. Permohonan retur/refund Anda sedang diverifikasi tim logistik & finance. "
                    "Instruksi penukaran/transfer dana akan kami kabari dalam 1x24 jam kerja ya Kak."
                )
        else:
            return (
                f"Halo {c_name}, saya Hendra selaku Customer Service Team Lead Colorbox Indonesia. "
                "Boleh informasikan nomor invoice atau detail kendala pesanan Anda agar segera saya bantu verifikasi langsung?"
            )
    else:
        # Siti: Warm, friendly, helpful frontline assistant (concise & clear)
        if intent == "BOT_RESUME":
            return (
                f"Halo {c_name}! Asisten virtual bot Colorbox telah aktif kembali 😊 "
                "Ada yang bisa Siti bantu seputar outfit santai, promo terbaru, atau informasi pesanan Kakak hari ini?"
            )
        elif intent == "OUT_OF_SCOPE":
            return (
                f"Halo {c_name}! Maaf ya Kak, pertanyaan tersebut di luar ranah dan scope pengetahuan tugas Siti di Colorbox 😊\n\n"
                "Ada yang bisa Siti bantu seputar outfit santai, koleksi pakaian, promo, atau pesanan Anda di Colorbox hari ini?"
            )
        elif intent == "RETURN_REFUND":
            return (
                f"Halo {c_name}! Untuk penukaran produk bisa diajukan maks. 7 hari kerja (tag label utuh & belum dicuci) ya 😊 "
                "Boleh dibantu nomor pesanan dan ukuran pengganti yang diinginkan Kak?"
            )
        elif intent == "SHIPPING_DELIVERY":
            return (
                f"Halo {c_name}! Estimasi pengiriman reguler Colorbox 2-4 hari kerja ✨ "
                "Boleh kirimkan nomor pesanan atau nomor resinya agar langsung Siti bantu lacak status terbarunya sekarang?"
            )
        elif intent == "SIZE_FIT":
            return (
                f"Halo {c_name}! Ukuran Colorbox tersedia dari XS sampai XL (celana 26-32) 💕 "
                "Boleh tahu model pakaian yang Kakak taksir serta perkiraan tinggi & berat badan agar Siti rekomendasikan ukuran yang paling pas?"
            )
        elif intent == "PRODUCT_AVAILABILITY":
            return (
                f"Halo {c_name}! Koleksi terbaru Colorbox dan kolaborasi Colorbox x Liunic tersedia di website & official store ✨ "
                "Boleh sebutkan nama item atau kirim foto produknya? Siti siap cek ketersediaan stoknya sekarang!"
            )
        else:
            return (
                f"Halo {c_name}! Terima kasih sudah menghubungi WhatsApp resmi Colorbox Indonesia 💕 "
                "Ada yang bisa Siti bantu seputar outfit santai, promo terbaru, atau informasi pesanan Kakak hari ini?"
            )

async def send_evolution_whatsapp_message(to: str, text: str, instance: Optional[str] = None) -> bool:
    """Send an outbound WhatsApp message back to the customer via Evolution API (Baileys)."""
    target_instance = instance or EVOLUTION_INSTANCE
    clean_to = "".join(filter(str.isdigit, to))
    url = f"{EVOLUTION_API_URL}/message/sendText/{target_instance}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "number": clean_to,
        "text": text,
        "options": {
            "delay": 1000,
            "presence": "composing"
        }
    }
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code in (200, 201):
                log.info("Successfully sent WhatsApp reply via Evolution API to %s", clean_to)
                return True
            else:
                log.warning("Evolution API failed to send to %s: %s - %s", clean_to, resp.status_code, resp.text)
                return False
    except Exception as e:
        log.warning("Exception sending WhatsApp message via Evolution API: %s", e)
        return False

async def get_evolution_connection_state(instance: Optional[str] = None) -> dict:
    """Get current WhatsApp connection state from Evolution API."""
    target_instance = instance or EVOLUTION_INSTANCE
    url = f"{EVOLUTION_API_URL}/instance/connectionState/{target_instance}"
    headers = {"apikey": EVOLUTION_API_KEY}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            return {"instance": target_instance, "state": "unknown", "status_code": resp.status_code}
    except Exception as e:
        return {"instance": target_instance, "state": "disconnected", "error": str(e)}

async def get_evolution_qr(instance: Optional[str] = None) -> dict:
    """Retrieve live QR code for scanning and connecting WhatsApp."""
    target_instance = instance or EVOLUTION_INSTANCE
    url = f"{EVOLUTION_API_URL}/instance/connect/{target_instance}"
    headers = {"apikey": EVOLUTION_API_KEY}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            # If instance does not exist, try to create it
            if resp.status_code == 404:
                create_url = f"{EVOLUTION_API_URL}/instance/create"
                create_payload = {
                    "instanceName": target_instance,
                    "token": f"token_{target_instance}",
                    "qrcode": True,
                    "integration": "WHATSAPP-BAILEYS"
                }
                c_resp = await client.post(create_url, headers=headers, json=create_payload)
                if c_resp.status_code in (200, 201):
                    # retry connect
                    r2 = await client.get(url, headers=headers)
                    if r2.status_code == 200:
                        return r2.json()
                    return c_resp.json()
            return {"error": f"Evolution API returned status {resp.status_code}", "body": resp.text}
    except Exception as e:
        return {"error": f"Failed to connect to Evolution API: {e}"}

async def send_meta_whatsapp_message(to: str, text: str) -> bool:
    """Send an outbound WhatsApp message back to the customer via Meta Cloud API."""
    token = os.environ.get("WHATSAPP_API_TOKEN") or WHATSAPP_API_TOKEN
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID") or WHATSAPP_PHONE_NUMBER_ID
    if not token or not phone_number_id:
        return False
    
    clean_to = "".join(filter(str.isdigit, to))
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_to,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text
        }
    }
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code in (200, 201):
                log.info("Successfully sent WhatsApp reply to %s", clean_to)
                return True
            else:
                log.warning("Meta API failed to send message to %s: %s - %s", clean_to, resp.status_code, resp.text)
                return False
    except Exception as e:
        log.warning("Exception sending WhatsApp message via Meta API: %s", e)
        return False

async def route_and_process_message(user_id: str, sender: str, customer_name: str, message: str,
                                    requested_bot: Optional[str] = None, metadata: Optional[dict] = None) -> dict:
    """Process incoming WhatsApp message, execute CS routing, log to database, and return response."""
    sender_lang = get_sender_language(sender)
    lang = detect_language(message, fallback_lang=sender_lang)
    set_sender_language(sender, lang)

    # 1. Check if sender is currently in Human Agent Takeover mode (bot paused)
    if is_sender_paused(sender):
        bot_id, intent, priority = classify_and_route(message, requested_bot)
        if intent == "BOT_RESUME":
            resume_sender(sender)
            reply_text = generate_cs_reply(bot_id, customer_name, message, intent, priority, language=lang)
            status = "replied"
            msg_id = uuid.uuid4()
            meta = metadata or {}
            meta.update({
                "intent": intent,
                "priority": priority,
                "routed_bot": bot_id,
                "language": lang,
                "processed_at": datetime.now(timezone.utc).isoformat()
            })
            try:
                await db.ex("""
                    INSERT INTO whatsapp_messages (id, user_id, sender, customer_name, direction, message, bot_id, status, response_text, metadata)
                    VALUES (%s, %s, %s, %s, 'inbound', %s, %s, %s, %s, %s)
                """, msg_id, user_id, sender, customer_name, message, bot_id, status, reply_text, json.dumps(meta))
            except Exception as e:
                log.warning("DB store error: %s", e)
            if EVOLUTION_API_URL and EVOLUTION_API_KEY:
                import asyncio
                asyncio.create_task(send_evolution_whatsapp_message(sender, reply_text))
            return {
                "id": str(msg_id),
                "sender": sender,
                "customer_name": customer_name,
                "routed_bot": bot_id,
                "bot_name": "Siti",
                "bot_role": "Frontline Support Specialist",
                "intent": intent,
                "priority": priority,
                "language": lang,
                "status": status,
                "message": message,
                "reply": reply_text,
                "paused": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            # Human takeover is active: store message with status 'needs_human' and DO NOT send any bot reply
            msg_id = uuid.uuid4()
            meta = metadata or {}
            meta.update({
                "intent": "HUMAN_TAKEOVER_ACTIVE",
                "priority": "P1",
                "routed_bot": "human",
                "language": lang,
                "processed_at": datetime.now(timezone.utc).isoformat()
            })
            try:
                await db.ex("""
                    INSERT INTO whatsapp_messages (id, user_id, sender, customer_name, direction, message, bot_id, status, response_text, metadata)
                    VALUES (%s, %s, %s, %s, 'inbound', %s, 'human', 'needs_human', '', %s)
                """, msg_id, user_id, sender, customer_name, message, json.dumps(meta))
            except Exception as e:
                log.warning("DB store error: %s", e)
            log.info("Human agent takeover active for %s. Message logged as needs_human without bot reply.", sender)
            return {
                "id": str(msg_id),
                "sender": sender,
                "customer_name": customer_name,
                "routed_bot": "human",
                "bot_name": "Human CS" if lang == "en" else "CS Manusia",
                "bot_role": "Human Customer Service Staff" if lang == "en" else "Customer Service Human Staff",
                "intent": "HUMAN_TAKEOVER_ACTIVE",
                "priority": "P1",
                "language": lang,
                "status": "needs_human",
                "message": message,
                "reply": "",
                "paused": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }

    # 2. Normal message routing
    bot_id, intent, priority = classify_and_route(message, requested_bot)
    
    # Generate reply
    reply_text = generate_cs_reply(bot_id, customer_name, message, intent, priority, language=lang)
    
    # Store inbound message and outbound reply
    msg_id = uuid.uuid4()
    meta = metadata or {}
    meta.update({
        "intent": intent,
        "priority": priority,
        "routed_bot": bot_id,
        "language": lang,
        "processed_at": datetime.now(timezone.utc).isoformat()
    })
    
    if intent == "HUMAN_TAKEOVER":
        pause_sender(sender, duration_seconds=7200)  # Pause bot for 2 hours
        status = "needs_human"
    elif bot_id == "hendra":
        status = "escalated"
    else:
        status = "replied"
    
    try:
        await db.ex("""
            INSERT INTO whatsapp_messages (id, user_id, sender, customer_name, direction, message, bot_id, status, response_text, metadata)
            VALUES (%s, %s, %s, %s, 'inbound', %s, %s, %s, %s, %s)
        """, msg_id, user_id, sender, customer_name, message, bot_id, status, reply_text, json.dumps(meta))
    except Exception as e:
        log.warning("Failed to store whatsapp_message into db (will continue): %s", e)

    # Outbound messaging to real WhatsApp:
    # 1. Prefer Evolution API (Baileys) if configured and reachable
    if EVOLUTION_API_URL and EVOLUTION_API_KEY:
        import asyncio
        asyncio.create_task(send_evolution_whatsapp_message(sender, reply_text))
    # 2. Or Meta Cloud API if configured
    else:
        token = os.environ.get("WHATSAPP_API_TOKEN") or WHATSAPP_API_TOKEN
        phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID") or WHATSAPP_PHONE_NUMBER_ID
        if token and phone_id:
            import asyncio
            asyncio.create_task(send_meta_whatsapp_message(sender, reply_text))

    return {
        "id": str(msg_id),
        "sender": sender,
        "customer_name": customer_name,
        "routed_bot": bot_id,
        "bot_name": "Hendra" if bot_id == "hendra" else "Siti",
        "bot_role": "CS Team Lead & Quality Auditor" if bot_id == "hendra" else "Frontline Support Specialist",
        "intent": intent,
        "priority": priority,
        "language": lang,
        "status": status,
        "message": message,
        "reply": reply_text,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

async def list_messages(user_id: str, limit: int = 50, sender: Optional[str] = None) -> list[dict]:
    """Retrieve logged WhatsApp interactions."""
    try:
        if sender:
            rows = await db.q("""
                SELECT id, sender, customer_name, direction, message, bot_id, status, response_text, metadata, created_at
                FROM whatsapp_messages
                WHERE user_id = %s AND sender = %s
                ORDER BY created_at DESC LIMIT %s
            """, user_id, sender, limit)
        else:
            rows = await db.q("""
                SELECT id, sender, customer_name, direction, message, bot_id, status, response_text, metadata, created_at
                FROM whatsapp_messages
                WHERE user_id = %s
                ORDER BY created_at DESC LIMIT %s
            """, user_id, limit)
        return [
            {
                "id": str(r["id"]),
                "sender": r["sender"],
                "customer_name": r["customer_name"],
                "direction": r["direction"],
                "message": r["message"],
                "bot_id": r["bot_id"],
                "status": r["status"],
                "response_text": r["response_text"],
                "metadata": r["metadata"] if isinstance(r["metadata"], dict) else json.loads(r["metadata"] or "{}"),
                "created_at": r["created_at"].isoformat() if r["created_at"] else None
            }
            for r in rows
        ]
    except Exception as e:
        log.warning("list_messages error: %s", e)
        return []

async def get_status() -> dict:
    """Inspect WhatsApp routing health, webhook configuration, and throughput."""
    total_count = 0
    recent_activity = None
    try:
        r = await db.q1("SELECT COUNT(*) as cnt, MAX(created_at) as last_act FROM whatsapp_messages")
        if r:
            total_count = r["cnt"] or 0
            recent_activity = r["last_act"].isoformat() if r["last_act"] else None
    except Exception:
        pass

    return {
        "channel": "WhatsApp Business Cloud API",
        "status": "ready",
        "mode": "live_webhook_and_simulation",
        "webhook_url": f"{config.PUBLIC_BASE_URL}/bff/api/whatsapp/webhook",
        "webhook_verify_token_configured": bool(WHATSAPP_VERIFY_TOKEN),
        "api_token_configured": bool(WHATSAPP_API_TOKEN),
        "primary_agent": {
            "id": "siti",
            "name": "Siti",
            "role": "Frontline Support Specialist"
        },
        "escalation_agent": {
            "id": "hendra",
            "name": "Hendra",
            "role": "CS Team Lead & Quality Auditor"
        },
        "total_messages_processed": total_count,
        "last_activity": recent_activity
    }
