-- Per-agent model choice (null = follow the default) and per-user workspace settings (JSON, merged over code defaults).
alter table bots add column model text, add column provider text, add column reasoning_effort text;
create table settings (
    user_id text primary key references users(id),
    data jsonb not null default '{}',
    updated_at timestamptz not null default now()
);
