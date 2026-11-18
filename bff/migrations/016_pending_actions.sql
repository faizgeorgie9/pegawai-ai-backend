-- Risky agent actions (delete a file, send an email) wait here until the user approves or rejects them (actions.py).
create table pending_actions (
    id uuid primary key default gen_random_uuid(),
    user_id text not null,
    kind text not null,                  -- which executor runs it: drive_trash, later gmail_send
    summary text not null,               -- one plain sentence for the card
    payload jsonb not null default '{}', -- what the executor needs (and the card shows, e.g. an email preview)
    status text not null default 'pending' check (status in ('pending', 'approved', 'rejected', 'done', 'failed', 'expired')),
    result text,
    source jsonb,                        -- where the agent asked: {bot_id, run_id, session_id, group_id}, when known
    created_at timestamptz not null default now(),
    decided_at timestamptz
);
create index on pending_actions (user_id, status, created_at desc);
