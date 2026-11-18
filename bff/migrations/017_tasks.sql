-- Papan Tugas: a task is one piece of work delegated to an agent or a team. All status changes go through tasks.py (transition).
create table tasks (
    id uuid primary key default gen_random_uuid(),
    user_id text not null,
    title text not null,
    body text not null default '',
    assignee_bot text,
    assignee_group uuid references groups(id),     -- exactly one of the two, except a plan (parent of a content plan) which may have only a group
    status text not null check (status in ('todo', 'scheduled', 'ready', 'running', 'blocked', 'review', 'done', 'archived')),
    outcome text check (outcome in ('ok', 'failed', 'cancelled')),
    kind text not null default 'task' check (kind in ('task', 'plan')),
    priority smallint not null default 0,          -- 0 normal, 1 important
    parent_id uuid references tasks(id) on delete cascade,
    scheduled_at timestamptz,
    source text not null check (source in ('user', 'chat', 'agent', 'plan', 'recurring')),
    source_ref jsonb not null default '{}',        -- {group_id, message_id, session_id, schedule_id}
    result text,
    block_kind text,                               -- needs_input | review | plan_approval | stopped | failed
    block_reason text,
    attempts int not null default 0,
    current_run_id uuid,
    schedule_id uuid references schedules(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    started_at timestamptz,
    completed_at timestamptz,
    check (not (assignee_bot is not null and assignee_group is not null)),
    check (kind = 'plan' or assignee_bot is not null or assignee_group is not null)
);
create index on tasks (user_id, status);
create index on tasks (parent_id);
create index on tasks (status, scheduled_at);
create unique index on tasks ((source_ref->>'message_id')) where kind = 'plan';

create table task_comments (
    id bigserial primary key,
    task_id uuid not null references tasks(id) on delete cascade,
    author text not null check (author in ('user', 'bot', 'system')),
    bot_id text,
    text text not null,
    created_at timestamptz not null default now()
);
create index on task_comments (task_id, id);

create table task_events (
    id bigserial primary key,
    task_id uuid not null references tasks(id) on delete cascade,
    kind text not null,
    payload jsonb not null default '{}',
    created_at timestamptz not null default now()
);
create index on task_events (task_id, id);

alter table runs add column task_id uuid references tasks(id) on delete set null;
create index on runs (task_id) where task_id is not null;
