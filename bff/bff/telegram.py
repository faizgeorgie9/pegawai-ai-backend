"""Telegram Bot API & webhook routing for Pegawai AI.

Every non-command message becomes a real Hermes run through the same path as web chat (`engine.chat_turn`),
with the bot owner as the run's user, a persisted session, CS/KB handling and normal cost tracking.
The webhook answers Telegram immediately and the turn runs in the background while `typing` is sent.
"""
import asyncio
import logging
import os
import re
import time
import uuid
from contextlib import suppress
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx

from . import auth, bots, config, cs_schema, db, engine
from .errors import ApiError

log = logging.getLogger("bff.telegram")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "mock_telegram_bot_token_sprint5")
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "pegawai_ai_telegram_secret_token_2026")
TELEGRAM_API_BASE = os.environ.get("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")
MAX_TELEGRAM_MESSAGE_CHARS = 4096
# The employee a brand-new chat talks to; its owner (auth.service_user) is the identity of the run.
DEFAULT_BOT = os.environ.get("TELEGRAM_DEFAULT_BOT", "siti").strip().lower() or "siti"
RUN_TIMEOUT_S = 120
TYPING_INTERVAL_S = 4

# Deduplication cache for incoming update_id: {update_id: timestamp}
_seen_update_ids: Dict[int, float] = {}
# One turn at a time per chat, so a fast second message cannot overtake the first one's session.
_chat_locks: Dict[int, asyncio.Lock] = {}
# Outbox log for sent messages (useful for tests and local auditing)
_outbox_log: List[Dict[str, Any]] = []


def is_duplicate_update(update_id: Optional[int]) -> bool:
    """Return True if update_id was already processed recently within 5 minutes."""
    if not update_id:
        return False
    now = time.time()
    # Evict expired entries older than 300 seconds
    expired = [k for k, ts in list(_seen_update_ids.items()) if now - ts > 300]
    for k in expired:
        _seen_update_ids.pop(k, None)

    if update_id in _seen_update_ids:
        return True
    _seen_update_ids[update_id] = now
    return False


def verify_webhook_secret(secret_token: Optional[str]) -> bool:
    """Validate X-Telegram-Bot-Api-Secret-Token against configured secret."""
    return secret_token == TELEGRAM_WEBHOOK_SECRET


def require_webhook_secret(secret_token: Optional[str]) -> None:
    """Reject an unauthenticated webhook before any work starts (the route calls this synchronously)."""
    if not verify_webhook_secret(secret_token):
        log.warning("Telegram webhook unauthorized: invalid secret token")
        raise ApiError(401, "Unauthorized: Invalid Telegram webhook secret token")


def split_telegram_message(text: str, max_chars: int = MAX_TELEGRAM_MESSAGE_CHARS) -> List[str]:
    """Split text into chunks compliant with Telegram 4096 character limit.
    Splits cleanly on paragraph breaks or line breaks when possible.
    """
    if not text:
        return [""]
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current_text = text
    while len(current_text) > max_chars:
        # Try to find paragraph break before max_chars
        split_idx = current_text.rfind("\n\n", 0, max_chars)
        if split_idx == -1:
            # Try single line break
            split_idx = current_text.rfind("\n", 0, max_chars)
        if split_idx == -1:
            # Try space
            split_idx = current_text.rfind(" ", 0, max_chars)
        if split_idx == -1:
            # Hard split
            split_idx = max_chars

        chunk = current_text[:split_idx].strip()
        if chunk:
            chunks.append(chunk)
        current_text = current_text[split_idx:].strip()

    if current_text:
        chunks.append(current_text)

    # If split into multiple, annotate with parts (1/2), (2/2)
    if len(chunks) > 1:
        total = len(chunks)
        chunks = [f"{c}\n\n({i+1}/{total})" for i, c in enumerate(chunks)]

    return chunks


def format_to_telegram_html(text: str) -> str:
    """Format text for native Telegram HTML rendering.
    Converts **bold**, `code`, ```pre```, and bullet points into
    clean, native Telegram formatting tags (<b>, <code>, <pre>).
    """
    if not text:
        return ""

    t = text
    # If the text does not already contain HTML formatting tags, escape HTML special chars
    if not ("<b>" in t or "<code>" in t or "<pre>" in t or "<i>" in t):
        t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Convert code blocks: ```code``` -> <pre>code</pre>
    t = re.sub(r"```(?:[a-zA-Z0-9_-]+)?\n?(.*?)```", r"<pre>\1</pre>", t, flags=re.DOTALL)
    # Convert inline code: `code` -> <code>code</code>
    t = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", t)
    # Convert bold: **text** -> <b>text</b>
    t = re.sub(r"\*\*([^\*\n]+)\*\*", r"<b>\1</b>", t)
    # Convert remaining *text* to <i>text</i>
    t = re.sub(r"(?<!\*)\*([^\*\n]+)\*(?!\*)", r"<i>\1</i>", t)

    return t


def _bot_token() -> str:
    return os.environ.get("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)


def _mocked() -> bool:
    """Mock mode: local tests and any deployment that has not set its own bot token yet."""
    return "mock" in _bot_token() or getattr(config, "TESTING", False)


async def send_chat_action(chat_id: int, action: str = "typing") -> None:
    """Show 'typing…' to the customer while the agent works. Best effort: never fails a turn."""
    if _mocked():
        _outbox_log.append({"chat_id": chat_id, "action": action, "timestamp": time.time()})
        return
    url = f"{TELEGRAM_API_BASE}/bot{_bot_token()}/sendChatAction"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json={"chat_id": chat_id, "action": action})
    except Exception as e:
        log.debug("Telegram chat action failed for chat %s: %s", chat_id, e)


async def send_telegram_message(
    chat_id: int,
    text: str,
    parse_mode: Optional[str] = "HTML",
    mock: bool = False
) -> Dict[str, Any]:
    """Dispatch an outbound message to Telegram chat via Telegram Bot API with native HTML formatting."""
    chunks = split_telegram_message(text)
    results = []

    bot_token = _bot_token()
    for chunk in chunks:
        formatted_chunk = format_to_telegram_html(chunk) if parse_mode == "HTML" else chunk
        payload = {
            "chat_id": chat_id,
            "text": formatted_chunk
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        # If mock mode or test token, record in outbox and return simulated success
        if mock or "mock" in bot_token or getattr(config, "TESTING", False):
            record = {
                "ok": True,
                "result": {
                    "message_id": int(time.time() * 1000) % 1000000,
                    "chat": {"id": chat_id},
                    "text": formatted_chunk,
                    "date": int(time.time())
                },
                "mocked": True
            }
            _outbox_log.append({"chat_id": chat_id, "text": formatted_chunk, "timestamp": time.time()})
            results.append(record)
            continue

        url = f"{TELEGRAM_API_BASE}/bot{bot_token}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                data = resp.json()
                if not data.get("ok") and "parse" in data.get("description", "").lower():
                    # Fallback to plain text with markdown symbols stripped
                    log.warning("Telegram parse error, falling back to plain text for chat %s", chat_id)
                    plain_text = re.sub(r"[*`_]", "", chunk)
                    fallback_payload = {"chat_id": chat_id, "text": plain_text}
                    resp = await client.post(url, fallback_payload)
                    data = resp.json()
                _outbox_log.append({"chat_id": chat_id, "text": formatted_chunk, "response": data, "timestamp": time.time()})
                results.append(data)
        except Exception as e:
            log.error("Failed to send Telegram message to chat %s: %s", chat_id, e)
            results.append({"ok": False, "error": str(e)})

    return {"ok": True, "parts_sent": len(results), "chunks": results}


# ---------- chat state (Postgres, migration 023) ----------

@dataclass
class ChatState:
    """Which employee this Telegram chat talks to, and which conversation it continues."""
    chat_id: int
    owner_id: str
    bot: Dict[str, Any]
    session_id: Optional[str]

    @property
    def bot_id(self) -> str:
        return self.bot["id"]


async def _load_chat(chat_id: int) -> Optional[dict]:
    return await db.q1("select chat_id, user_id, bot_id, session_id from telegram_chats where chat_id = %s", chat_id)


async def _save_chat(chat_id: int, owner_id: str, bot_id: str, session_id: Optional[str]) -> None:
    await db.ex(
        "insert into telegram_chats (chat_id, user_id, bot_id, session_id) values (%s, %s, %s, %s) "
        "on conflict (chat_id) do update set user_id = excluded.user_id, bot_id = excluded.bot_id, "
        "session_id = excluded.session_id, updated_at = now()",
        chat_id, owner_id, bot_id, session_id)


async def _new_session(chat_id: int, owner_id: str, bot_id: str) -> str:
    """Register the conversation the same way web chat does, so it shows up in the web history."""
    session_id = f"tg-{chat_id}-{uuid.uuid4().hex[:8]}"
    await db.ex("insert into chat_sessions (session_id, user_id, bot_id) values (%s, %s, %s)",
                session_id, owner_id, bot_id)
    return session_id


def _chat_lock(chat_id: int) -> asyncio.Lock:
    lock = _chat_locks.get(chat_id)
    if lock is None:
        lock = _chat_locks[chat_id] = asyncio.Lock()
    return lock


async def _default_state(chat_id: int) -> ChatState:
    """First message in a chat: the default employee, owned by their owner (never a hardcoded tenant)."""
    owner_id = await auth.service_user(DEFAULT_BOT)
    available = await bots.list_bots(owner_id)
    chosen = next((b for b in available if b["id"] == DEFAULT_BOT), available[0] if available else None)
    if not chosen:
        raise ApiError(404, "Belum ada pegawai AI yang bisa menjawab.")
    bot = await bots.get_bot(owner_id, chosen["id"])
    await _save_chat(chat_id, owner_id, bot["id"], None)
    return ChatState(chat_id, owner_id, bot, None)


async def _resolve_chat(chat_id: int, forced_bot_id: Optional[str] = None) -> ChatState:
    """The persisted chat state, or the state a new chat starts with. A bot-specific webhook binds the chat to that bot."""
    if forced_bot_id:
        owner_id = await auth.service_user(forced_bot_id)
        try:
            bot = await bots.get_bot(owner_id, forced_bot_id)
        except ApiError:
            raise ApiError(404, "Pegawai AI ini belum tersedia untuk pesan masuk.")
        row = await _load_chat(chat_id)
        same = bool(row and row["bot_id"] == bot["id"] and row["user_id"] == owner_id)
        session_id = row["session_id"] if same else None
        await _save_chat(chat_id, owner_id, bot["id"], session_id)
        return ChatState(chat_id, owner_id, bot, session_id)

    row = await _load_chat(chat_id)
    if row:
        owner_id = row["user_id"]
        bot = None
        try:
            owner_id = await auth.service_user(row["bot_id"])  # current owner, after a bot moved between accounts
            bot = await bots.get_bot(owner_id, row["bot_id"])
        except ApiError:
            bot = None
        if bot:
            session_id = row["session_id"] if owner_id == row["user_id"] else None
            if session_id != row["session_id"] or owner_id != row["user_id"]:
                await _save_chat(chat_id, owner_id, bot["id"], session_id)
            return ChatState(chat_id, owner_id, bot, session_id)
    return await _default_state(chat_id)


async def _ensure_session(state: ChatState) -> str:
    if state.session_id:
        return state.session_id
    state.session_id = await _new_session(state.chat_id, state.owner_id, state.bot_id)
    await _save_chat(state.chat_id, state.owner_id, state.bot_id, state.session_id)
    return state.session_id


async def _available_names(owner_id: str) -> str:
    rows = await bots.list_bots(owner_id)
    return ", ".join(b["name"] for b in rows) if rows else "belum ada"


# ---------- commands ----------

async def switch_chat_bot(state: ChatState, name: str) -> str:
    """Switch to an existing bot of this chat's owner; never create or guess one."""
    target = " ".join(name.lower().split())
    rows = await bots.list_bots(state.owner_id)
    match = next((b for b in rows if b["id"] == target or b["name"].lower() == target), None)
    if not match:
        names = ", ".join(b["name"] for b in rows) if rows else "belum ada"
        return f"Pegawai AI '{name.strip()}' tidak tersedia. Pilihan: {names}."
    bot = await bots.get_bot(state.owner_id, match["id"])
    state.bot, state.session_id = bot, None  # a different employee starts a fresh conversation
    await _save_chat(state.chat_id, state.owner_id, bot["id"], None)
    return f"Siap. Sekarang Anda berbicara dengan {bot['name']}."


async def handle_telegram_command(command: str, args: str, state: ChatState) -> Tuple[bool, str]:
    """Process a Telegram command (/start, /help, /status, /agent, /reset). Returns (is_command, reply)."""
    cmd = command.lower().strip().split("@", 1)[0]  # /help@pegawai_ai_bot
    if cmd == "/start":
        names = await _available_names(state.owner_id)
        return True, (
            "Halo! Selamat datang di Pegawai AI.\n\n"
            f"Saat ini Anda berbicara dengan {state.bot['name']}.\n"
            f"Pegawai AI yang tersedia: {names}.\n\n"
            "Ketik pertanyaan atau tugas Anda langsung di sini.\n"
            "• /agent <nama> — ganti pegawai AI\n"
            "• /reset — mulai topik baru\n"
            "• /status — lihat pegawai AI yang aktif\n"
            "• /help — panduan singkat"
        )

    if cmd == "/help":
        return True, (
            "Panduan singkat:\n"
            "1. Kirim pesan langsung untuk berbicara dengan pegawai AI Anda.\n"
            "2. /agent <nama> untuk berganti pegawai AI.\n"
            "3. /reset untuk memulai topik baru tanpa membawa percakapan lama.\n"
            "4. Balasan panjang akan dipecah otomatis agar tidak terpotong."
        )

    if cmd == "/status":
        return True, (
            f"Pegawai AI aktif: {state.bot['name']}.\n"
            f"Percakapan: {'sedang berjalan' if state.session_id else 'baru'}.\n"
            "Ganti pegawai dengan /agent <nama>."
        )

    if cmd in ("/agent", "/switch"):
        if not args.strip():
            names = await _available_names(state.owner_id)
            return True, f"Pegawai AI aktif: {state.bot['name']}. Pilihan: {names}. Ketik /agent <nama>."
        return True, await switch_chat_bot(state, args)

    if cmd == "/reset":
        state.session_id = None
        await _save_chat(state.chat_id, state.owner_id, state.bot_id, None)
        return True, f"Percakapan baru dimulai. Anda masih berbicara dengan {state.bot['name']}."

    return False, ""


# ---------- agent turn ----------

def customer_reply(output: str) -> Optional[str]:
    """The customer-facing text of a CS answer. Never returns the raw structured JSON."""
    structured, _ = cs_schema.validate_cs(output)
    if structured:
        draft = (structured.get("customer_reply_draft") or "").strip()
        return draft or None
    try:
        data = cs_schema.extract_json(output)
    except ValueError:
        return None
    draft = data.get("customer_reply_draft") if isinstance(data, dict) else None
    return draft.strip() if isinstance(draft, str) and draft.strip() else None


def _looks_like_json(text: str) -> bool:
    s = text.strip()
    return s.startswith("{") or s.startswith("```json") or '"customer_reply_draft"' in s


def _answer_text(output: str) -> Optional[str]:
    draft = customer_reply(output)
    if draft:
        return draft
    if _looks_like_json(output):
        return None  # structured answer without a usable draft: never paste JSON to a customer
    return output.strip() or None


def _unavailable(state: ChatState) -> str:
    return f"Maaf, {state.bot['name']} sedang tidak bisa menjawab. Coba lagi sebentar lagi."


async def _wait_for_run(chat_id: int, run_id: str) -> Optional[dict]:
    """Wait for the final text, showing 'typing' every few seconds. None on timeout."""
    async def typing() -> None:
        while True:
            with suppress(Exception):
                await send_chat_action(chat_id)
            await asyncio.sleep(TYPING_INTERVAL_S)

    task = asyncio.create_task(typing())
    try:
        return await asyncio.wait_for(engine.wait_done(run_id), RUN_TIMEOUT_S)
    except asyncio.TimeoutError:
        return None
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


async def _agent_turn(state: ChatState, text: str) -> str:
    """One real Hermes run for this chat, through the same helper web chat uses."""
    session_id = await _ensure_session(state)
    workflow = "cs" if state.bot.get("team") == "customer_support" else None
    run, _ = await engine.chat_turn(state.owner_id, state.bot, session_id, text, workflow=workflow,
                                    origin={"type": "chat"})
    run_id = str(run["id"])  # the runs row carries a uuid; LIVE is keyed by its string
    row = await _wait_for_run(state.chat_id, run_id)
    if not row:
        log.warning("Telegram run %s for chat %s timed out", run_id, state.chat_id)
        return _unavailable(state)
    if row.get("status") != "completed":
        log.warning("Telegram run %s for chat %s ended %s: %s", run_id, state.chat_id,
                    row.get("status"), row.get("error"))
        return _unavailable(state)
    answer = _answer_text(row.get("output") or "")
    if not answer:
        log.warning("Telegram run %s for chat %s produced no usable answer", run_id, state.chat_id)
        return _unavailable(state)
    return answer


# ---------- webhook ----------

async def process_telegram_update(update_payload: Dict[str, Any], secret_token: Optional[str] = None,
                                  *, forced_bot_id: Optional[str] = None) -> Dict[str, Any]:
    """Parse one Telegram update, then answer a command or run the active AI employee and send its reply."""
    require_webhook_secret(secret_token)

    update_id = update_payload.get("update_id")
    if is_duplicate_update(update_id):
        log.info("Ignored duplicate Telegram update %s", update_id)
        return {"ok": True, "status": "duplicate_ignored", "update_id": update_id}

    message = update_payload.get("message") or update_payload.get("edited_message")
    if not message:
        # Not a standard message update (e.g. callback_query, channel_post)
        return {"ok": True, "status": "no_message_to_process"}

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()

    if not chat_id or not text:
        return {"ok": True, "status": "empty_text_or_chat_id"}

    state: Optional[ChatState] = None
    reply_text = ""
    async with _chat_lock(chat_id):
        try:
            state = await _resolve_chat(chat_id, forced_bot_id)

            if text.startswith("/"):
                parts = text.split(" ", 1)
                is_cmd, reply_text = await handle_telegram_command(parts[0], parts[1] if len(parts) > 1 else "", state)
                if is_cmd:
                    await send_telegram_message(chat_id, reply_text)
                    return {"ok": True, "status": "command_handled", "command": parts[0], "chat_id": chat_id,
                            "bot_id": state.bot_id, "reply": reply_text}

            log.info("Telegram chat %s -> %s", chat_id, state.bot_id)
            reply_text = await _agent_turn(state, text)
        except ApiError as e:
            log.warning("Telegram chat %s could not start a turn: %s", chat_id, e.message)
            if state:
                reply_text = e.message if e.status == 402 else _unavailable(state)
            else:
                reply_text = e.message if e.status in (402, 404) else (
                    "Maaf, layanan sedang sibuk. Coba lagi sebentar lagi.")
        except Exception as e:  # no stack trace ever reaches the customer
            log.warning("Telegram chat %s failed: %s", chat_id, type(e).__name__)
            reply_text = _unavailable(state) if state else "Maaf, layanan sedang sibuk. Coba lagi sebentar lagi."

        await send_telegram_message(chat_id, reply_text)

    return {"ok": True, "status": "message_routed", "chat_id": chat_id,
            "bot_id": state.bot_id if state else None, "user_message": text, "agent_reply": reply_text}


async def process_telegram_update_in_background(update_payload: Dict[str, Any], secret_token: Optional[str] = None,
                                                *, forced_bot_id: Optional[str] = None) -> None:
    """Webhook background task: Telegram already got its 200, so a failure is logged instead of raised."""
    try:
        await process_telegram_update(update_payload, secret_token, forced_bot_id=forced_bot_id)
    except ApiError as e:
        log.warning("Telegram update rejected in background: %s", e.message)
    except Exception as e:
        log.warning("Telegram update failed in background: %s", type(e).__name__)


def get_telegram_status() -> Dict[str, Any]:
    """Return status summary of Telegram bot integration."""
    return {
        "is_configured": bool(TELEGRAM_BOT_TOKEN and "mock" not in TELEGRAM_BOT_TOKEN),
        "bot_token_set": bool(TELEGRAM_BOT_TOKEN),
        "webhook_secret_configured": bool(TELEGRAM_WEBHOOK_SECRET),
        "max_message_chars": MAX_TELEGRAM_MESSAGE_CHARS,
        "default_bot": DEFAULT_BOT,
        "chat_state": "postgres",
        "outbox_messages_logged": len(_outbox_log),
        "supported_commands": ["/start", "/help", "/status", "/agent", "/reset"]
    }
