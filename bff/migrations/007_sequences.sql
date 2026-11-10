-- Multi-turn runs that continue on the server (Evaluasi cases), one row per sequence.
create table sequences (
    id uuid primary key default gen_random_uuid(),
    user_id text not null default 'default',
    bot_id text not null,
    session_id text not null,
    origin jsonb not null default '{}',
    turns jsonb not null,
    status text not null default 'queued' check (status in ('queued', 'running', 'completed', 'failed', 'stopped')),
    current_turn int not null default 0,
    run_ids jsonb not null default '[]',
    error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create index on sequences (user_id, created_at desc);
