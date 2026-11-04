-- NULL means "no limit" for the monthly token quota and the per-send group budget.
alter table plans alter column monthly_tokens drop not null;
alter table plans alter column group_send_token_budget drop not null;
update plans set group_send_token_budget = null;
update plans set monthly_tokens = null where id = 'bisnis';

alter table runs add column if not exists cache_read_tokens int not null default 0;
