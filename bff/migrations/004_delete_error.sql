-- A bot whose Hermes profile could not be removed in the background comes back with this message.
alter table bots add column if not exists delete_error text;
