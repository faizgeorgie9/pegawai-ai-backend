-- Colorbox product catalog (bff/knowledge/colorbox/product-catalog.md) and a small key/value table of knowledge file hashes.
create table if not exists knowledge_meta (
    key text primary key, value text not null, updated_at timestamptz not null default now()
);
create table products (
    id integer generated always as identity primary key,
    category text not null,
    name text not null,
    price integer not null,                 -- rupiah
    price_original integer,                 -- only when the catalog shows a struck-through price
    colors text[] not null default '{}',
    sizes text[] not null default '{}',
    url text not null,
    source text not null default 'SRC-02',
    accessed_date date not null default '2026-11-09',
    search tsvector not null                -- name + category + colors, 'simple' config
);
create index products_search_idx on products using gin (search);
create index products_price_idx on products (price);
