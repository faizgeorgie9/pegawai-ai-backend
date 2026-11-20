-- Migration 020: Authentication & User Credentials for Multi-Tenant Support

ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS email text,
    ADD COLUMN IF NOT EXISTS password_hash text,
    ADD COLUMN IF NOT EXISTS salt text,
    ADD COLUMN IF NOT EXISTS role text NOT NULL DEFAULT 'member',
    ADD COLUMN IF NOT EXISTS company text DEFAULT 'Colorbox',
    ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;

-- Ensure email is unique when present
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON users(email) WHERE email IS NOT NULL;

-- Update the default admin user with initial credentials (Password: Admin1234!)
-- Salt: a1b2c3d4e5f607182930415263748596
-- PBKDF2-SHA256 (100,000 iters): 4f9e13cb3321b5dd3c2496f4ed8979cc566876a9467672a0e80aa73de1a5e76e
UPDATE users 
SET email = 'admin@pegawai.ai',
    salt = 'a1b2c3d4e5f607182930415263748596',
    password_hash = '4f9e13cb3321b5dd3c2496f4ed8979cc566876a9467672a0e80aa73de1a5e76e',
    role = 'admin',
    company = 'Colorbox',
    name = 'Super Admin'
WHERE id = 'default';

-- Insert demo team users if not exists (all seeded with initial password Admin1234!)
INSERT INTO users (id, name, email, salt, password_hash, role, company, plan_id)
VALUES 
    ('user_owner', 'Hendrawan (Owner)', 'owner@colorbox.co.id', 'a1b2c3d4e5f607182930415263748596', '4f9e13cb3321b5dd3c2496f4ed8979cc566876a9467672a0e80aa73de1a5e76e', 'owner', 'Colorbox', 'bisnis'),
    ('user_cs', 'Siti Rahma (CS Lead)', 'cs@colorbox.co.id', 'a1b2c3d4e5f607182930415263748596', '4f9e13cb3321b5dd3c2496f4ed8979cc566876a9467672a0e80aa73de1a5e76e', 'cs', 'Colorbox', 'pro'),
    ('user_marketing', 'Bimo Wicaksono (Marketing)', 'marketing@colorbox.co.id', 'a1b2c3d4e5f607182930415263748596', '4f9e13cb3321b5dd3c2496f4ed8979cc566876a9467672a0e80aa73de1a5e76e', 'marketing', 'Colorbox', 'pro'),
    ('user_demo', 'Demo Guest User', 'demo@pegawai.ai', 'a1b2c3d4e5f607182930415263748596', '4f9e13cb3321b5dd3c2496f4ed8979cc566876a9467672a0e80aa73de1a5e76e', 'demo', 'Colorbox Demo', 'pro')
ON CONFLICT (id) DO UPDATE 
SET email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    salt = EXCLUDED.salt,
    role = EXCLUDED.role,
    company = EXCLUDED.company;
