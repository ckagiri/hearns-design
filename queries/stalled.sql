-- ADR-0006's transitive-stall query: pending cards behind a card that will not reach `done` without a person. Follows
-- both predicate clauses: a dep itself, and a dep's descendant unless that descendant is quarantined, which clause (b)
-- accepts. `failed` is excluded because the reaper retries it. Run with: psql -v p="'project'" -f queries/stalled.sql

with recursive stuck as (
  select id as task_id, state::text as own_state, id as held_by, state::text as held_state
    from tasks
   where project = :p and state in ('quarantined', 'awaiting_review')
  union
  select t.id, 'pending', s.held_by, s.held_state
    from tasks t
   cross join lateral unnest(t.deps) as dep(id)
    join stuck s on s.task_id = dep.id
                 or (s.own_state <> 'quarantined' and s.task_id like dep.id || '.%')
   where t.state = 'pending'
)
select s.task_id, t.title, s.held_by, s.held_state
from stuck s join tasks t on t.id = s.task_id
where s.task_id <> s.held_by
order by s.held_by, string_to_array(s.task_id, '.') COLLATE tree_order;
