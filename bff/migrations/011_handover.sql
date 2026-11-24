alter table data_connections drop constraint if exists data_connections_kind_check;
alter table data_connections add constraint data_connections_kind_check
    check (kind in ('stock', 'orders', 'handover'));

create table if not exists handover_tickets (
    id bigserial primary key,
    user_id text not null,
    ticket_id text not null unique,
    category text not null,
    order_id text,
    contact text,
    summary text not null,
    priority text not null default 'P1',
    owner text,
    status text not null default 'open',
    acknowledgement text not null,
    sheet_mirror text not null default 'not_configured',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists handover_tickets_owner on handover_tickets (user_id, created_at desc);
