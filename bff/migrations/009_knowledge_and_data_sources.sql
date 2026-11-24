create table if not exists knowledge_sources (
    id uuid primary key default gen_random_uuid(),
    user_id text not null,
    scope text not null default 'cs',
    kind text not null check (kind in ('file', 'website')),
    title text not null,
    url text,
    filename text,
    mime text,
    size_bytes integer,
    sha256 text,
    content text not null,
    created_at timestamptz not null default now()
);

create index if not exists knowledge_sources_owner on knowledge_sources (user_id, scope, created_at desc);

create table if not exists data_connections (
    id uuid primary key default gen_random_uuid(),
    user_id text not null,
    kind text not null check (kind in ('stock', 'orders')),
    url text not null,
    spreadsheet_id text not null,
    gid text,
    tab text,
    header jsonb,
    status text not null default 'unverified',
    detail text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, kind)
);
