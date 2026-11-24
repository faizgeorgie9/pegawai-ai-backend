-- Migration 022: per-user token version, so logout can invalidate tokens already issued.
-- Additive and safe for the previous release: the old code ignores the column, existing tokens have no
-- `tv` claim and therefore count as version 0, which is the default for every existing row.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS token_version integer NOT NULL DEFAULT 0;
