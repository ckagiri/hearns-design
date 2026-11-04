-- The project tree (core §9.3). Run with: psql -v p="'project'" -f queries/tree.sql

select id, title, kind, outcome, attempts, tier, caused_by
from tasks
where project = :p
order by string_to_array(id, '.') COLLATE tree_order;   -- NOT lexical: 't-x.2' sorts before 't-x.10'

-- Rolled onto split rows by prefix scan (core §9.3). The outcome names are policy's vocabulary.
select s.id,
       count(d.id)                                         as descendants,
       coalesce(sum(d.cost_usd), 0) + s.cost_usd           as subtree_cost_usd,
       coalesce(max(d.attempts), 0)                        as max_attempts,
       count(*) filter (where d.outcome = 'refused')       as refusals,
       count(*) filter (where d.outcome = 'needs_context') as needs_context,
       coalesce(bool_or(d.state = 'quarantined'), false)   as any_quarantined
from tasks s
left join tasks d on d.id like s.id || '.%'
where s.project = :p and s.kind = 'split'
group by s.id, s.cost_usd
order by string_to_array(s.id, '.') COLLATE tree_order;
