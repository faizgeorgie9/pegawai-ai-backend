-- Evaluation records for test scenarios (Skenario uji & evaluasi). Prototype log, single user.
create table evaluations (
    id uuid primary key default gen_random_uuid(),
    user_id text not null default 'default',
    case_id text not null,
    bot_id text not null,
    session_id text,
    run_id text,
    prompt text not null default '',
    expected text not null default '',
    actual text not null default '',
    scores jsonb not null default '{}',
    verdict text not null check (verdict in ('pass', 'fail', 'blocked')),
    notes jsonb not null default '{}',
    reviewer text not null default '',
    created_at timestamptz not null default now()
);
create index on evaluations (user_id, created_at desc);
