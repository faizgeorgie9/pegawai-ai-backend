-- What a vision model sees in the official product photo (cut, silhouette, visible fabric, stitching, colour).
alter table product_images
    add column image_description text,
    add column described_at timestamptz,
    add column describer_model text;
