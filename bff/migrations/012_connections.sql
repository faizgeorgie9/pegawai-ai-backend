-- Per-user connections to Google Drive / Gmail / Notion (connections.py). Tokens are stored encrypted (Fernet), never in plain text.
create table connections (
    user_id text not null,
    provider text not null check (provider in ('gdrive', 'gmail', 'notion')),
    access_enc text not null,
    refresh_enc text,
    expires_at timestamptz,
    scopes text[] not null default '{}',
    account text,                    -- email or workspace name shown to the user
    status text not null default 'connected' check (status in ('connected', 'reconnect')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (user_id, provider)
);

-- One row per started consent: random state (stored hashed), bound to the user, short expiry, deleted when used.
create table oauth_states (
    state_hash text primary key,
    user_id text not null,
    provider text not null,
    verifier text,                   -- PKCE code verifier (Google)
    expires_at timestamptz not null
);

-- Items imported through a connection keep the id of the source so they can be re-imported ("Perbarui").
alter table kb_items drop constraint kb_items_kind_check;
alter table kb_items add constraint kb_items_kind_check check (kind in ('file', 'gdrive', 'url', 'notion'));
alter table kb_items add column ext_id text;
create index on kb_items (user_id, ext_id) where ext_id is not null;
