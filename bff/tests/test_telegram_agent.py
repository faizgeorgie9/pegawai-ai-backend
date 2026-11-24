"""Telegram is a real chat bridge: each message is a Hermes run owned by the bot's owner, with a persisted session."""
import asyncio
import json
from types import SimpleNamespace

import pytest

from bff import telegram
from bff.errors import ApiError

SECRET = telegram.TELEGRAM_WEBHOOK_SECRET
SITI = {"id": "siti", "name": "Siti", "team": "customer_support", "user_id": "user_owner"}
BRAM = {"id": "bram", "name": "Bram", "team": "marketing", "user_id": "user_owner"}
CS_ANSWER = {
    "primary_intent": "PRODUCT_INFO",
    "classification_confidence": 0.9,
    "priority": "P3",
    "customer_reply_draft": "Halo kak, Hoodie terbaru tersedia dalam ukuran S sampai XL.",
    "ticket_summary": {"issue": "tanya produk"},
    "escalation": {"recommended": False, "handoff_status": "recommendation_only"},
    "human_review_required": True,
}


@pytest.fixture
def env(monkeypatch):
    """A chat bridge with the database boundary and the Hermes run stubbed; everything above them is real."""
    sent, typing, turns, sessions = [], [], [], []
    row = {}
    results = []

    async def send(chat_id, text, parse_mode="HTML", mock=False):
        sent.append({"chat_id": chat_id, "text": text})
        return {"ok": True, "parts_sent": 1, "chunks": []}

    async def action(chat_id, action="typing"):
        typing.append({"chat_id": chat_id, "action": action})

    async def load(chat_id):
        return dict(row) if row else None

    async def save(chat_id, owner_id, bot_id, session_id):
        row.update(chat_id=chat_id, user_id=owner_id, bot_id=bot_id, session_id=session_id)

    async def new_session(chat_id, owner_id, bot_id):
        session_id = f"tg-{chat_id}-{len(sessions) + 1}"
        sessions.append({"session_id": session_id, "owner_id": owner_id, "bot_id": bot_id})
        return session_id

    async def owner(_bot_id=None):
        return "user_owner"

    async def get_bot(owner_id, bot_id):
        if owner_id != "user_owner":
            raise ApiError(404, "Bot tidak ditemukan")
        for b in (SITI, BRAM):
            if b["id"] == bot_id:
                return dict(b)
        raise ApiError(404, "Bot tidak ditemukan")

    async def list_bots(_owner_id):
        return [{"id": "siti", "name": "Siti"}, {"id": "bram", "name": "Bram"}]

    async def chat_turn(user_id, bot, session_id, text, **kw):
        turns.append({"user_id": user_id, "bot": bot, "session_id": session_id, "text": text, **kw})
        return {"id": f"run-{len(turns)}"}, []

    async def wait_done(_run_id):
        await asyncio.sleep(0)  # let the typing task run before the fake answer lands
        return dict(results.pop(0))

    monkeypatch.setattr(telegram, "send_telegram_message", send)
    monkeypatch.setattr(telegram, "send_chat_action", action)
    monkeypatch.setattr(telegram, "_load_chat", load)
    monkeypatch.setattr(telegram, "_save_chat", save)
    monkeypatch.setattr(telegram, "_new_session", new_session)
    monkeypatch.setattr(telegram.auth, "service_user", owner)
    monkeypatch.setattr(telegram.bots, "get_bot", get_bot)
    monkeypatch.setattr(telegram.bots, "list_bots", list_bots)
    monkeypatch.setattr(telegram.engine, "chat_turn", chat_turn)
    monkeypatch.setattr(telegram.engine, "wait_done", wait_done)
    return SimpleNamespace(sent=sent, typing=typing, turns=turns, sessions=sessions, row=row, results=results)


def update(text, update_id, chat_id=555001):
    return {"update_id": update_id,
            "message": {"message_id": update_id, "chat": {"id": chat_id},
                        "from": {"id": chat_id, "first_name": "Rina"}, "text": text}}


def complete(env, text):
    env.results.append({"status": "completed", "output": text, "error": None})


@pytest.mark.anyio
async def test_routes_to_hermes_with_owner_and_session(env):
    complete(env, "Halo kak, ini jawaban Siti.")
    res = await telegram.process_telegram_update(update("Berapa harga Hoodie terbaru?", 2001), SECRET)

    assert res["ok"] is True and res["status"] == "message_routed"
    assert res["bot_id"] == "siti"
    assert res["agent_reply"] == "Halo kak, ini jawaban Siti."
    assert env.sent[-1] == {"chat_id": 555001, "text": "Halo kak, ini jawaban Siti."}

    turn = env.turns[0]
    assert turn["user_id"] == "user_owner"  # the bot's owner, never "default"
    assert turn["bot"]["id"] == "siti"
    assert turn["session_id"] == "tg-555001-1"
    assert turn["workflow"] == "cs"  # customer-support employees use the CS instructions
    assert env.sessions == [{"session_id": "tg-555001-1", "owner_id": "user_owner", "bot_id": "siti"}]
    assert env.row == {"chat_id": 555001, "user_id": "user_owner", "bot_id": "siti", "session_id": "tg-555001-1"}


@pytest.mark.anyio
async def test_chat_state_survives_later_messages(env):
    complete(env, "Jawaban pertama.")
    complete(env, "Jawaban kedua.")
    await telegram.process_telegram_update(update("Halo", 2002), SECRET)
    await telegram.process_telegram_update(update("Yang paling murah yang mana?", 2003), SECRET)

    assert len(env.turns) == 2
    assert env.turns[0]["session_id"] == env.turns[1]["session_id"] == "tg-555001-1"
    assert len(env.sessions) == 1  # the stored session is reused, not replaced
    assert env.row["session_id"] == "tg-555001-1"
    assert env.turns[1]["text"] == "Yang paling murah yang mana?"


@pytest.mark.anyio
async def test_chat_state_is_read_from_storage_not_process_memory(env):
    """A reload or another worker writes the row; the next message must honor it, so there is no in-process state."""
    complete(env, "Jawaban pertama.")
    await telegram.process_telegram_update(update("Halo", 2017), SECRET)
    env.row.update(bot_id="bram", session_id="tg-555001-99")  # what a restarted process would find in Postgres

    complete(env, "Jawaban kedua.")
    await telegram.process_telegram_update(update("Lanjut", 2018), SECRET)

    assert env.turns[1]["bot"]["id"] == "bram"
    assert env.turns[1]["session_id"] == "tg-555001-99"


@pytest.mark.anyio
async def test_reset_starts_a_new_session(env):
    complete(env, "Jawaban pertama.")
    complete(env, "Jawaban setelah reset.")
    await telegram.process_telegram_update(update("Halo", 2004), SECRET)

    await telegram.process_telegram_update(update("/reset", 2005), SECRET)
    assert env.row["session_id"] is None
    assert env.row["bot_id"] == "siti"  # reset keeps the employee
    assert "Percakapan baru" in env.sent[-1]["text"]

    await telegram.process_telegram_update(update("Topik baru", 2006), SECRET)
    assert env.turns[1]["session_id"] == "tg-555001-2"
    assert env.turns[1]["session_id"] != env.turns[0]["session_id"]


@pytest.mark.anyio
async def test_agent_switch_only_accepts_existing_bots_of_the_owner(env):
    await telegram.process_telegram_update(update("/agent tukang", 2007), SECRET)
    assert "tidak tersedia" in env.sent[-1]["text"]
    assert env.row["bot_id"] == "siti"
    assert env.turns == []


@pytest.mark.anyio
async def test_agent_switch_to_existing_bot_starts_fresh_conversation(env):
    complete(env, "Jawaban Siti.")
    await telegram.process_telegram_update(update("Halo", 2008), SECRET)

    await telegram.process_telegram_update(update("/agent bram", 2009), SECRET)
    assert "Bram" in env.sent[-1]["text"]
    assert env.row["bot_id"] == "bram" and env.row["session_id"] is None

    complete(env, "Jawaban Bram.")
    await telegram.process_telegram_update(update("Buat caption", 2010), SECRET)
    assert env.turns[1]["bot"]["id"] == "bram"
    assert env.turns[1]["workflow"] is None  # only customer-support employees use the CS workflow
    assert env.turns[1]["session_id"] == "tg-555001-2"


@pytest.mark.anyio
async def test_cs_structured_answer_becomes_customer_text(env):
    complete(env, json.dumps(CS_ANSWER))
    res = await telegram.process_telegram_update(update("Hoodienya ada ukuran apa?", 2011), SECRET)

    assert res["agent_reply"] == CS_ANSWER["customer_reply_draft"]
    reply = env.sent[-1]["text"]
    assert reply == CS_ANSWER["customer_reply_draft"]
    assert "customer_reply_draft" not in reply and "{" not in reply


@pytest.mark.anyio
async def test_failed_run_gets_a_friendly_answer(env):
    env.results.append({"status": "failed", "output": "", "error": "Traceback: internal failure"})
    res = await telegram.process_telegram_update(update("Halo", 2012), SECRET)

    assert res["agent_reply"] == "Maaf, Siti sedang tidak bisa menjawab. Coba lagi sebentar lagi."
    assert "Traceback" not in res["agent_reply"]


@pytest.mark.anyio
async def test_timeout_gets_a_friendly_answer(env, monkeypatch):
    async def slow(_run_id):
        await asyncio.sleep(0.05)
        return {"status": "completed", "output": "terlambat", "error": None}

    monkeypatch.setattr(telegram.engine, "wait_done", slow)
    monkeypatch.setattr(telegram, "RUN_TIMEOUT_S", 0.01)
    res = await telegram.process_telegram_update(update("Halo", 2013), SECRET)

    assert res["agent_reply"] == "Maaf, Siti sedang tidak bisa menjawab. Coba lagi sebentar lagi."


@pytest.mark.anyio
async def test_typing_is_sent_while_waiting(env):
    complete(env, "Jawaban.")
    await telegram.process_telegram_update(update("Halo", 2014), SECRET)

    assert env.typing
    assert env.typing[0] == {"chat_id": 555001, "action": "typing"}


@pytest.mark.anyio
async def test_duplicate_update_is_ignored(env):
    complete(env, "Sekali saja.")
    first = await telegram.process_telegram_update(update("Halo", 2015), SECRET)
    second = await telegram.process_telegram_update(update("Halo", 2015), SECRET)

    assert first["status"] == "message_routed"
    assert second["status"] == "duplicate_ignored"
    assert len(env.turns) == 1


@pytest.mark.anyio
async def test_bot_specific_webhook_binds_the_chat_to_that_bot(env):
    complete(env, "Jawaban Bram.")
    res = await telegram.process_telegram_update(update("Buat caption", 2016), SECRET, forced_bot_id="bram")

    assert res["bot_id"] == "bram"
    assert env.turns[0]["bot"]["id"] == "bram"
    assert env.turns[0]["user_id"] == "user_owner"
    assert env.row["bot_id"] == "bram"


@pytest.mark.anyio
async def test_chat_state_is_persisted_through_postgres(monkeypatch):
    calls = []

    async def ex(sql, *params):
        calls.append(("ex", sql, params))

    monkeypatch.setattr(telegram.db, "ex", ex)
    await telegram._save_chat(777, "user_owner", "siti", "tg-777-1")

    sql, params = calls[0][1], calls[0][2]
    assert "insert into telegram_chats" in sql
    assert "on conflict (chat_id) do update" in sql
    assert params == (777, "user_owner", "siti", "tg-777-1")

    async def q1(_sql, *params):
        assert params == (777,)
        return {"chat_id": 777, "user_id": "user_owner", "bot_id": "siti", "session_id": "tg-777-1"}

    monkeypatch.setattr(telegram.db, "q1", q1)
    assert await telegram._load_chat(777) == {"chat_id": 777, "user_id": "user_owner", "bot_id": "siti",
                                              "session_id": "tg-777-1"}
