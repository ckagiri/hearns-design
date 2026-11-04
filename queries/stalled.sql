-- ADR-0006's transitive-stall query: pending cards behind a card that will not reach `done` without a person.
-- `failed` is excluded because the reaper retries it. Clause (b) accepts a quarantined descendant, so only
-- deps are followed. Run with: psql -v p="'project'" -f queries/stalled.sql

with recursive stuck as (
  select id as task_id, id as held_by, state::text as held_state
    from tasks
   where project = :p and state in ('quarantined', 'awaiting_review')
  union
  select t.id, s.held_by, s.held_state
    from tasks t join stuck s on s.task_id = any(t.deps)
   where t.state = 'pending'
)
select s.task_id, t.title, s.held_by, s.held_state
from stuck s join tasks t on t.id = s.task_id
where s.task_id <> s.held_by
order by s.held_by, string_to_array(s.task_id, '.') COLLATE tree_order;
