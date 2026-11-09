create table plans (
    id text primary key, name text not null, max_bots int not null, max_groups int not null,
    monthly_tokens bigint not null, max_concurrent_runs int not null, group_send_token_budget int not null,
    sort int not null default 0
);
insert into plans values
    ('gratis', 'Gratis', 3, 1, 200000, 1, 30000, 1),
    ('pro', 'Pro', 10, 5, 3000000, 3, 60000, 2),
    ('bisnis', 'Bisnis', 30, 20, 20000000, 8, 120000, 3);

create table users (
    id text primary key, name text not null, plan_id text not null references plans(id),
    created_at timestamptz not null default now()
);
insert into users values ('default', 'Pengguna', 'pro', now());

create table bots (
    id text primary key, user_id text not null references users(id), name text not null, role text not null,
    team text not null, color text not null default 'plain', template text, persona text,
    builtin boolean not null default false, created_at timestamptz not null default clock_timestamp(), deleted_at timestamptz
);
insert into bots (id, user_id, name, role, team, color, template, builtin) values
    ('rian', 'default', 'Rian', 'Copywriting Specialist', 'marketing', 'amber', 'rian', true),
    ('diana', 'default', 'Diana', 'Creative Director & QC Auditor', 'marketing', 'teal', 'diana', true),
    ('budi', 'default', 'Budi', 'Visual Designer & Art Director', 'marketing', 'indigo', 'budi', true),
    ('siti', 'default', 'Siti', 'Frontline Support Specialist', 'customer_support', 'sky', 'siti', true),
    ('hendra', 'default', 'Hendra', 'CS Team Lead & Quality Auditor', 'customer_support', 'teal', 'hendra', true);

create table chat_sessions (
    session_id text primary key, user_id text not null, bot_id text not null,
    created_at timestamptz not null default now()
);
create index on chat_sessions (user_id, bot_id);

create table groups (
    id uuid primary key, user_id text not null, name text not null,
    created_at timestamptz not null default now(), deleted_at timestamptz
);
create table group_members (
    group_id uuid not null references groups(id), bot_id text not null, position int not null,
    primary key (group_id, bot_id)
);

create table runs (
    id uuid primary key, hermes_run_id text, user_id text not null, bot_id text not null, session_id text not null,
    group_id uuid references groups(id), kind text not null, status text not null,
    input text not null default '', output text not null default '', reasoning text, error text,
    input_tokens int not null default 0, output_tokens int not null default 0, total_tokens int not null default 0,
    last_seq int not null default 0,
    created_at timestamptz not null default now(), started_at timestamptz, finished_at timestamptz
);
create index on runs (user_id, status);
create index on runs (group_id);
create index on runs (bot_id, status);

create table run_events (
    id bigserial primary key, run_id uuid not null references runs(id) on delete cascade, seq int not null,
    type text not null, payload jsonb not null default '{}', created_at timestamptz not null default now()
);
create index on run_events (run_id, seq);
create index on run_events (created_at);

create table group_messages (
    id bigserial primary key, group_id uuid not null references groups(id), author text not null, bot_id text,
    text text not null, run_id uuid, send_id uuid, created_at timestamptz not null default now()
);
create index on group_messages (group_id, id);

create table group_cursors (
    group_id uuid not null references groups(id), bot_id text not null, last_message_id bigint not null default 0,
    primary key (group_id, bot_id)
);

create table group_sends (
    id uuid primary key, group_id uuid not null references groups(id), message_id bigint not null,
    status text not null, tokens_used int not null default 0,
    created_at timestamptz not null default now(), finished_at timestamptz
);
create index on group_sends (group_id, status);
