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
from pathlib import Path
from typing import Any, Optional, Tuple

from . import config, db
from .errors import ApiError

log = logging.getLogger("bff.whatsapp")

WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "pegawai_ai_wa_verify_secret")
WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")

# Escalation triggers that route directly to Hendra (CS Team Lead)
ESCALATION_KEYWORDS = {
    "cacat", "rusak", "robek", "reject", "kecewa", "tuntut", "kasus", "somasi",
    "refund", "kembalikan uang", "ganti rugi", "tipu", "penipuan",
    "manajer", "manager", "supervisor", "atasan", "lead", "bos", "pimpinan",
    "lapor", "konsumen", "perlindungan konsumen", "bpom", "polisi"
}

# General intents
INTENT_KEYWORDS = {
    "RETURN_REFUND": ["retur", "tukar", "kembali", "pengembalian", "salah ukuran", "kebesaran", "kekecilan"],
    "SHIPPING_DELIVERY": ["ongkir", "resi", "lacak", "ekspedisi", "kapan sampai", "pengiriman", "jne", "sicepat"],
    "SIZE_FIT": ["ukuran", "size", "ld", "lingkar dada", "panjang", "cm", "fitting", "bb", "tb"],
    "PRODUCT_AVAILABILITY": ["ready", "stok", "tersedia", "ada gak", "restok", "habis"],
    "PRODUCT_INFO": ["bahan", "koleksi", "warna", "katalog", "liunic", "denim", "blazer", "dress", "promo", "diskon"],
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

def classify_and_route(message: str, requested_bot: Optional[str] = None) -> Tuple[str, str, str]:
    """Route message to appropriate CS bot: Siti (Frontline) or Hendra (Lead/Escalation).
    Returns (bot_id, intent, priority)."""
    if requested_bot in ("siti", "hendra"):
        bot_id = requested_bot
    else:
        bot_id = "siti"

    msg_lower = message.lower()
    
    # Check escalation keywords
    is_escalated = any(re.search(rf"\b{kw}\b", msg_lower) for kw in ESCALATION_KEYWORDS)
    if is_escalated and not requested_bot:
        bot_id = "hendra"
        priority = "P1"
        intent = "COMPLAINT_DAMAGED" if any(w in msg_lower for w in ["cacat", "rusak", "robek", "reject"]) else "RETURN_REFUND"
        return bot_id, intent, priority

    # Determine intent
    intent = "PRODUCT_INFO"
    for candidate_intent, keywords in INTENT_KEYWORDS.items():
        if any(re.search(rf"\b{kw}\b", msg_lower) for kw in keywords):
            intent = candidate_intent
            break

    priority = "P1" if is_escalated else ("P2" if intent in ("RETURN_REFUND", "SHIPPING_DELIVERY", "SIZE_FIT") else "P3")
    return bot_id, intent, priority

def generate_cs_reply(bot_id: str, customer_name: str, message: str, intent: str, priority: str) -> str:
    """Generate grounded customer support reply following Colorbox CS SOP."""
    c_name = customer_name if customer_name and customer_name != "Pelanggan" else "Kak"
    msg_lower = message.lower()

    if bot_id == "hendra":
        # Authoritative, calm, highly empathetic managerial resolution
        if intent == "COMPLAINT_DAMAGED":
            return (
                f"Halo {c_name}, saya Hendra selaku Customer Service Team Lead Colorbox Indonesia. "
                "Mohon maaf yang sebesar-besarnya atas kendala produk yang kurang berkenan. "
                "Sesuai SOP Penjaminan Kualitas Colorbox, kami akan bertanggung jawab penuh. "
                "Mohon bantuannya untuk melampirkan foto barcode tag produk dan video unboxing singkat, "
                "serta nomor pesanan Anda. Tim kami akan segera memproses penggantian unit baru atau solusi terbaik dalam 1x24 jam kerja."
            )
        elif intent == "RETURN_REFUND":
            return (
                f"Halo {c_name}, saya Hendra dari Manajemen CS Colorbox. "
                "Kami memahami ketidaknyamanan Anda terkait permohonan pengembalian dana/barang. "
                "Kebijakan penukaran resmi Colorbox berlaku hingga 7 hari kalender sejak pesanan diterima dengan kondisi pakaian belum dicuci dan tag harga masih utuh. "
                "Mohon informasikan nomor resi/pesanan Anda agar kami tindak lanjuti langsung dengan tim logistik dan finance kami hari ini."
            )
        else:
            return (
                f"Halo {c_name}, saya Hendra, CS Team Lead Colorbox. "
                "Pesan Anda telah kami prioritaskan untuk penanganan khusus. "
                "Tim kami berkomitmen memberikan kepastian layanan terbaik bagi seluruh #ColorboxBabes. "
                "Boleh informasikan detail kendala atau nomor invoice Anda agar segera saya verifikasi langsung di sistem kami?"
            )
    else:
        # Siti: Warm, friendly, helpful frontline assistant
        if intent == "RETURN_REFUND":
            return (
                f"Halo {c_name}! Terima kasih sudah menghubungi CS Colorbox 😊 "
                "Untuk penukaran produk (misalnya ukuran atau warna), bisa banget dilakukan maksimal 7 hari kerja setelah barang diterima ya Kak, "
                "dengan syarat tag label masih terpasang rapi dan pakaian belum dicuci. "
                "Boleh dibantu sebutkan nomor pesanan dan ukuran yang diinginkan Kak?"
            )
        elif intent == "SHIPPING_DELIVERY":
            return (
                f"Halo {c_name}! Salam hangat dari Colorbox ✨ "
                "Untuk pengecekan pengiriman, pesanan reguler biasanya diproses dalam 1-2 hari kerja dan estimasi sampai 2-4 hari kerja tergantung lokasi Anda. "
                "Boleh dibantu nomor resi atau nomor pesanannya agar Siti bantu lacak status terbarunya sekarang juga?"
            )
        elif intent == "SIZE_FIT":
            return (
                f"Halo {c_name}! Senang bisa bantu rekomendasi gaya Colorbox untuk Kakak 💕 "
                "Ukuran Colorbox umumnya tersedia dari XS sampai XL (serta ukuran celana 26-32). "
                "Untuk siluet Oversized biasanya memiliki lingkar dada lebih longgar (+6 s.d. +10 cm dari reguler). "
                "Boleh tahu produk apa yang sedang Kakak taksir, serta perkiraan tinggi & berat badan agar Siti rekomendasikan ukuran yang paling pas?"
            )
        elif intent == "PRODUCT_AVAILABILITY":
            return (
                f"Halo {c_name}! Terima kasih sudah melirik koleksi Colorbox ✨ "
                "Koleksi terbaru kami dan kolaborasi Colorbox x Liunic tersedia baik di website resmi maupun official store. "
                "Boleh dibantu nama item atau tangkapan layar produk yang Kakak cari? Siti siap cek ketersediaan stoknya sekarang ya!"
            )
        else:
            return (
                f"Halo {c_name}! Terima kasih sudah menghubungi WhatsApp resmi Colorbox Indonesia 💕 "
                "Ada yang bisa Siti bantu seputar outfit santai, promo terbaru, atau informasi pesanan Kakak hari ini? "
                "Siti siap membantu dengan senang hati!"
            )

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
    bot_id, intent, priority = classify_and_route(message, requested_bot)
    
    # Generate reply
    reply_text = generate_cs_reply(bot_id, customer_name, message, intent, priority)
    
    # Store inbound message and outbound reply
    msg_id = uuid.uuid4()
    meta = metadata or {}
    meta.update({
        "intent": intent,
        "priority": priority,
        "routed_bot": bot_id,
        "processed_at": datetime.now(timezone.utc).isoformat()
    })
    
    status = "escalated" if bot_id == "hendra" else "replied"
    
    try:
        await db.ex("""
            INSERT INTO whatsapp_messages (id, user_id, sender, customer_name, direction, message, bot_id, status, response_text, metadata)
            VALUES (%s, %s, %s, %s, 'inbound', %s, %s, %s, %s, %s)
        """, msg_id, user_id, sender, customer_name, message, bot_id, status, reply_text, json.dumps(meta))
    except Exception as e:
        log.warning("Failed to store whatsapp_message into db (will continue): %s", e)

    # If Meta Cloud API credentials are configured, send outbound reply to customer's WhatsApp
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
