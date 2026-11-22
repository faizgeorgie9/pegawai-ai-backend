-- Product photos, keyed by product url (not by products.id) because catalog.sync() deletes and reloads `products`.
create table product_images (
    url text primary key,
    image_url text not null,                -- public CDN url, or /api/product-images/<file> for local photos
    image_source text not null,             -- 'colorbox.co.id' or 'local'
    image_fetched_at timestamptz not null default now()
);
