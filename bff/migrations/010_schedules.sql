-- Scheduler: schedules (recurring, or a plan = explicit dated list) and their occurrences. Run by the BFF loop (scheduler.py).
-- An occurrence is claimed with a single UPDATE ... planned -> running, so it starts at most once.
create table schedules (
    id uuid primary key default gen_random_uuid(),
    user_id text not null,
    kind text not null check (kind in ('recurring', 'plan')),
    title text not null,
    bot_id text,                     -- target of a recurring schedule on one agent
    group_id uuid references groups(id),  -- target group (recurring: message to the group; plan: writer + visual of the group)
    prompt text,                     -- recurring only
    days int[],                      -- recurring only, 0 = Monday ... 6 = Sunday
    time_of_day text,                -- recurring only, HH:MM in `timezone`
    timezone text not null,
    status text not null default 'active' check (status in ('active', 'paused', 'cancelled')),
    source_message_id bigint,        -- plan only: the group message with the approved plan (approving twice finds this row)
    created_at timestamptz not null default now(),
    check (bot_id is not null or group_id is not null)
);
create index on schedules (user_id, created_at desc);
create unique index on schedules (source_message_id) where source_message_id is not null;

create table schedule_occurrences (
    id uuid primary key default gen_random_uuid(),
    schedule_id uuid not null references schedules(id) on delete cascade,
    user_id text not null,
    planned_at timestamptz not null,
    title text,
    brief text not null,
    targets jsonb,                   -- ordered bot ids for a plan day (writer, visual); null = the schedule's own target
    status text not null default 'planned' check (status in ('planned', 'running', 'done', 'skipped', 'failed', 'cancelled')),
    run_ids jsonb not null default '[]',
    skip_reason text,
    started_at timestamptz,
    finished_at timestamptz,
    unique (schedule_id, planned_at)
);
create index on schedule_occurrences (status, planned_at);
create index on schedule_occurrences (user_id, planned_at);
