-- Original uploaded file of a Knowledge Base item, so the user can open or download it again (uploads from 17 Nov 2026 on).
-- shortcut: bytea in Postgres (max 10 MB per file, the upload limit); move to object storage when volume grows.
create table kb_files (
    item_id uuid primary key references kb_items(id) on delete cascade,
    mime text not null,
    data bytea not null
);
