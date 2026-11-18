-- 019_whatsapp_messages.sql: WhatsApp routing and customer support message logging
create table if not exists whatsapp_messages (
    id uuid primary key default gen_random_uuid(),
    user_id text not null default 'default',
    sender text not null,
    customer_name text,
    direction text not null default 'inbound', -- inbound, outbound
    message text not null,
    bot_id text not null default 'siti',
    status text not null default 'received', -- received, processing, replied, escalated, failed
    response_text text,
    metadata jsonb default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_wa_sender_created on whatsapp_messages (sender, created_at desc);
create index if not exists idx_wa_status on whatsapp_messages (status);
