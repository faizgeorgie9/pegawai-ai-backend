-- Sprint 5 Day 2: Per-Agent KB Isolation and Document Classification
-- Adds category and allowed_roles to kb_items to enforce agent-level boundaries

ALTER TABLE kb_items 
    ADD COLUMN IF NOT EXISTS category text NOT NULL DEFAULT 'general',
    ADD COLUMN IF NOT EXISTS classification text NOT NULL DEFAULT 'internal';

-- Add index on category for fast filtered queries
CREATE INDEX IF NOT EXISTS idx_kb_items_category ON kb_items (user_id, category);

-- Constraint on supported categories
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'kb_items_category_check'
    ) THEN
        ALTER TABLE kb_items ADD CONSTRAINT kb_items_category_check 
        CHECK (category IN ('general', 'finance', 'cs', 'marketing', 'catalog', 'hr', 'legal'));
    END IF;
END $$;
