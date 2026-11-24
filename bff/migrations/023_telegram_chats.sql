-- Migration 023: Telegram chats keep their employee and conversation in Postgres.
-- Additive: one row per Telegram chat. `session_id` is null until the first message (or after /reset),
-- and points at a normal `chat_sessions` row owned by the bot's owner, so web history shows the same conversation.
-- Existing Telegram users simply get a fresh conversation on their next message.

create table if not exists telegram_chats (
    chat_id bigint primary key,
    user_id text not null,
    bot_id text not null,
    session_id text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists telegram_chats_user_bot_idx on telegram_chats (user_id, bot_id);
