-- Papan Tugas, stage B: recurring schedules and content plans now run as tasks.
-- A recurring time is created once per schedule: the slot (UTC, same format as scheduler._slot_key) is part of the task's identity.
create unique index tasks_recurring_slot on tasks (schedule_id, (source_ref->>'slot')) where source = 'recurring';

-- Planned occurrences of active recurring schedules become scheduled tasks.
insert into tasks (user_id, title, body, assignee_bot, assignee_group, status, scheduled_at, source, source_ref, schedule_id)
select s.user_id, left(coalesce(o.title, s.title), 120), o.brief, s.bot_id, s.group_id, 'scheduled', o.planned_at, 'recurring',
       jsonb_build_object('schedule_id', s.id, 'slot', to_char(o.planned_at at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')), s.id
from schedule_occurrences o join schedules s on s.id = o.schedule_id
where o.status = 'planned' and s.kind = 'recurring' and s.status = 'active'
on conflict do nothing;

-- Plan schedules (approved content plans) become a plan task (the parent) with one task per day.
-- The parent has the id of the old schedule; its days follow the old occurrences.
insert into tasks (id, user_id, title, assignee_group, status, outcome, kind, source, source_ref, completed_at)
select s.id, s.user_id, left(s.title, 120), s.group_id,
       case when s.status = 'cancelled' then 'archived'
            when exists (select 1 from schedule_occurrences o where o.schedule_id = s.id and o.status = 'planned') then 'todo'
            else 'done' end,
       case when s.status = 'cancelled' then 'cancelled'
            when not exists (select 1 from schedule_occurrences o where o.schedule_id = s.id and o.status = 'planned') then 'ok' end,
       'plan', 'plan', jsonb_build_object('group_id', s.group_id, 'message_id', s.source_message_id),
       case when s.status = 'cancelled' or not exists (select 1 from schedule_occurrences o where o.schedule_id = s.id and o.status = 'planned')
            then now() end
from schedules s
where s.kind = 'plan' and s.source_message_id is not null
on conflict do nothing;

insert into tasks (user_id, title, body, assignee_group, status, outcome, scheduled_at, source, source_ref, parent_id, block_reason, completed_at)
select s.user_id, left(coalesce(o.title, s.title), 120), o.brief, s.group_id,
       case o.status when 'planned' then 'scheduled' when 'done' then 'done' else 'archived' end,
       case o.status when 'planned' then null when 'done' then 'ok' when 'cancelled' then 'cancelled' else 'failed' end,
       o.planned_at, 'plan',
       jsonb_build_object('group_id', s.group_id, 'message_id', s.source_message_id, 'targets', o.targets),
       s.id, o.skip_reason, o.finished_at
from schedule_occurrences o join schedules s on s.id = o.schedule_id
where s.kind = 'plan' and s.source_message_id is not null
  and exists (select 1 from tasks p where p.id = s.id);

-- shortcut: schedule_occurrences stays in the database but nothing reads or writes it any more; drop it when nobody needs the history.
