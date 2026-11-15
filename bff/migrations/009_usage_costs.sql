-- USD pricing per model and monthly USD limits per plan.
-- Prices are USD per 1M tokens (input, output, cache read). Source: OpenCode Go price tables (the provider the profiles use),
-- read 2026-11-15. verified = the price comes from an official page AND is one flat rate; anything else is false and every
-- cost computed with it is shown as an estimate ("perkiraan"). off_peak_* = the cheaper rate outside peak hours
-- (Mon-Fri 01:00-04:00 and 06:00-10:00 UTC are peak), only DeepSeek has one.
create table model_prices (
    provider text not null, model text not null,
    input_usd numeric(12,6) not null, output_usd numeric(12,6) not null, cache_read_usd numeric(12,6) not null,
    off_peak_input_usd numeric(12,6), off_peak_output_usd numeric(12,6), off_peak_cache_read_usd numeric(12,6),
    verified boolean not null, source_url text not null, checked_at date not null, note text,
    primary key (provider, model)
);

-- The USD limit replaces the token limit (NULL = no limit). Starting values are product placeholders, change per plan.
alter table plans add column monthly_usd numeric(12,4);
update plans set monthly_usd = 1 where id = 'gratis';
update plans set monthly_usd = 15 where id = 'pro';
alter table plans drop column monthly_tokens;

insert into model_prices (provider, model, input_usd, output_usd, cache_read_usd, off_peak_input_usd, off_peak_output_usd,
                          off_peak_cache_read_usd, verified, source_url, checked_at, note)
select 'opencode-go', v.model, v.i, v.o, v.c, v.oi, v.oo, v.oc, v.verified, v.url, date '2026-11-15', v.note
from (values
    -- flat rate on the Go page: verified
    ('deepseek-v4.1-flash', 0.30, 1.20, 0.006, 0.15, 0.60, 0.003, true, 'https://opencode.ai/docs/go/', 'Tarif puncak; tarif di luar jam puncak lebih murah'),
    ('deepseek-v4-pro', 1.32, 3.96, 0.044, 0.66, 1.98, 0.022, true, 'https://opencode.ai/docs/go/', 'Tarif puncak; tarif di luar jam puncak lebih murah'),
    ('glm-5.3-flash', 0.15, 0.50, 0.03, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('glm-5.3', 1.40, 4.40, 0.26, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('glm-5.2', 1.40, 4.40, 0.26, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('kimi-k3.1-pro', 2.00, 10.00, 0.20, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('kimi-k3', 3.00, 15.00, 0.30, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('kimi-k2.7-code', 0.95, 4.00, 0.19, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('longcat-2.0', 0.30, 1.20, 0.006, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('step-5-preview', 1.00, 2.70, 0.10, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('mimo-v2.6-flash', 0.14, 0.28, 0.0028, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('mimo-v2.6-pro', 0.435, 0.87, 0.003625, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('mimo-v2.5', 0.14, 0.28, 0.0028, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('mimo-v2.5-pro', 0.435, 0.87, 0.003625, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('minimax-m3.1-flash', 0.15, 0.60, 0.015, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('muse-spark-1.3-contributor', 0.10, 0.20, 0.002, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('muse-spark-1.2-contributor', 0.10, 0.20, 0.002, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('qwen3.8-max', 2.00, 6.00, 0.25, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('qwen3.8-flash', 0.15, 0.47, 0.016, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('hy4', 0.834, 2.501, 0.042, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('hy4-preview', 0.834, 2.501, 0.042, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('hy3', 0.14, 0.58, 0.035, null, null, null, true, 'https://opencode.ai/docs/go/', null),
    ('beam-free', 0, 0, 0, null, null, null, true, 'https://opencode.ai/docs/go/', 'Gratis untuk waktu terbatas'),
    ('iceman-contributor-free', 0, 0, 0, null, null, null, true, 'https://opencode.ai/docs/go/', 'Gratis untuk waktu terbatas'),
    ('longcat-2.5-free', 0, 0, 0, null, null, null, true, 'https://opencode.ai/docs/go/', 'Gratis untuk waktu terbatas'),
    -- tiered by request size (the BFF only knows run totals) or a time-limited discount: lowest tier, not verified
    ('minimax-m3', 0.30, 1.20, 0.06, null, null, null, false, 'https://opencode.ai/docs/go/', 'Tarif bertingkat, dipakai tarif terendah (sampai 512K token)'),
    ('qwen3.7-plus', 0.40, 1.60, 0.04, null, null, null, false, 'https://opencode.ai/docs/go/', 'Tarif bertingkat, dipakai tarif terendah (sampai 256K token)'),
    ('grok-4.7', 2.00, 6.00, 0.50, null, null, null, false, 'https://opencode.ai/docs/go/', 'Tarif bertingkat, dipakai tarif terendah (sampai 200K token)'),
    ('gpt-6-luna', 0.10, 0.50, 0.01, null, null, null, false, 'https://opencode.ai/docs/go/', 'Tarif bertingkat, dipakai tarif terendah (sampai 272K token)'),
    ('gpt-5.6-luna', 0.20, 1.20, 0.02, null, null, null, false, 'https://opencode.ai/docs/go/', 'Tarif bertingkat, dipakai tarif terendah (sampai 272K token)'),
    ('claude-haiku-5-5', 0.10, 0.50, 0.01, null, null, null, false, 'https://opencode.ai/docs/go/', 'Tarif bertingkat, dipakai tarif terendah (sampai 100K token)'),
    ('gemini-4-argon', 2.00, 10.00, 0.10, null, null, null, false, 'https://opencode.ai/docs/go/', 'Harga diskon 50% untuk waktu terbatas'),
    -- not on the Go page: price of the same model on OpenCode Zen, not verified for Go
    ('glm-5.1', 1.40, 4.40, 0.26, null, null, null, false, 'https://opencode.ai/docs/zen/', 'Harga dari halaman Zen, belum ada di halaman Go'),
    ('glm-5', 1.00, 3.20, 0.20, null, null, null, false, 'https://opencode.ai/docs/zen/', 'Harga dari halaman Zen, belum ada di halaman Go'),
    ('kimi-k2.6', 0.95, 4.00, 0.16, null, null, null, false, 'https://opencode.ai/docs/zen/', 'Harga dari halaman Zen, belum ada di halaman Go'),
    ('kimi-k2.5', 0.60, 3.00, 0.10, null, null, null, false, 'https://opencode.ai/docs/zen/', 'Harga dari halaman Zen, belum ada di halaman Go'),
    ('minimax-m2.7', 0.30, 1.20, 0.06, null, null, null, false, 'https://opencode.ai/docs/zen/', 'Harga dari halaman Zen, belum ada di halaman Go'),
    ('minimax-m2.5', 0.30, 1.20, 0.06, null, null, null, false, 'https://opencode.ai/docs/zen/', 'Harga dari halaman Zen, belum ada di halaman Go'),
    ('qwen3.6-plus', 0.50, 3.00, 0.05, null, null, null, false, 'https://opencode.ai/docs/zen/', 'Harga dari halaman Zen, belum ada di halaman Go'),
    ('qwen3.5-plus', 0.20, 1.20, 0.02, null, null, null, false, 'https://opencode.ai/docs/zen/', 'Harga dari halaman Zen, belum ada di halaman Go')
) as v(model, i, o, c, oi, oo, oc, verified, url, note);
