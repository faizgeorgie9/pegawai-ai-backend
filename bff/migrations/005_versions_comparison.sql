-- Version snapshot per run, and comparison / version snapshot on evaluation records.
alter table runs add column if not exists meta jsonb not null default '{}';
alter table evaluations add column if not exists meta jsonb not null default '{}';
alter table evaluations add column if not exists comparison jsonb;
