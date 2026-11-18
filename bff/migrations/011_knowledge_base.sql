-- Per-user Knowledge Base: items (file / gdrive / url) and their text chunks. Search = Postgres full-text over chunks (kb.py).
create table kb_items (
    id uuid primary key default gen_random_uuid(),
    user_id text not null,
    kind text not null check (kind in ('file', 'gdrive', 'url')),
    name text not null,
    source text,                     -- the URL of a link item
    status text not null default 'processing' check (status in ('processing', 'ready', 'failed')),
    error text,                      -- plain reason when failed
    size_bytes int,
    chars int,
    created_at timestamptz not null default now()
);
create index on kb_items (user_id, created_at desc);

create table kb_chunks (
    id bigserial primary key,
    item_id uuid not null references kb_items(id) on delete cascade,
    user_id text not null,
    pos int not null,
    text text not null,
    -- 'simple' config: no stemming or stop words, so it works the same for Indonesian and English
    tsv tsvector generated always as (to_tsvector('simple', text)) stored
);
create index on kb_chunks (item_id, pos);
create index on kb_chunks using gin (tsv);

-- Items a user attached to a group message (the composer's attachment icon): their text goes to the bots for that message.
alter table group_messages add column kb_items uuid[];
