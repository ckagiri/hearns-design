-- An acceptance test for schema fields (core §9.4): a field nobody can write a query against is a field to
-- remove. The first three are core's; the rest are the questions core §8.1.1, §9.2 and the ADRs say the record
-- answers. Run with: psql -v p="'project'" -v d="'digest'" -v h="'hash'" -f queries/lessons.sql

-- which contract shapes produce refusals
select t.contract_completeness, a.failure_class, count(*)
from task_attempts a join tasks t on t.id=a.task_id
where t.kind='execute' and t.project=:p and a.failure_class is not null group by 1,2;

-- what facts were missing, per root intent
select r.intent_digest, a.refusal->'needs'
from task_attempts a join tasks t on t.id=a.task_id join runs r on r.root_id=t.root_id
where a.failure_class='needs_context' and r.project=:p;

-- same intent, different model version
select r.config_pin->>'model_strong' as model,
       sum((select count(*) from task_attempts a
             where a.task_id=t.id and a.failure_class='misclassified')) as misclassified,
       avg(t.attempts)
from runs r join tasks t on t.root_id=r.root_id
where r.intent_digest=:d group by 1;

-- did this card's slice of the system behave the same across runs (core §8.1.1)
select project, root_id, outcome, attempts
from tasks where kind = 'execute' and config_hash = :h;

-- cost and tokens by tier and kind, from what was called (core §9.2)
select t.tier, t.kind, sum(m.cost_usd) as cost_usd, sum(m.tokens_in) as tokens_in,
       sum(m.tokens_out) as tokens_out
from model_calls m join tasks t on t.id = m.task_id
where t.project = :p group by 1,2 order by 3 desc;

-- attempts and outcome distributions (core §9.2)
select kind, attempts, count(*) from tasks where project = :p group by 1,2 order by 1,2;
select kind, outcome, count(*) from tasks where project = :p group by 1,2 order by 1,2;

-- reasoning tokens by kind and effort, against attempts (core §9.2)
select t.kind, m.effort, sum(m.reasoning_tokens) as reasoning_tokens, avg(t.attempts) as avg_attempts
from model_calls m join tasks t on t.id = m.task_id
where t.project = :p group by 1,2;

-- check latency as a fraction of wall clock: where it dominates, workers buy less (core §9.2)
select t.kind,
       sum(t.check_latency_ms) / nullif(sum(extract(epoch from a.ended_at - a.started_at)) * 1000, 0)
         as check_fraction
from tasks t join task_attempts a on a.task_id = t.id
where t.project = :p and a.ended_at is not null group by 1;

-- turns, rung 1 invocations and wall clock per card: R36's "turns x rung latency" (odoo-adaptation)
select t.id, count(distinct (m.attempt, m.seq)) as turns, t.rung1_invocations,
       (select sum(a.ended_at - a.started_at) from task_attempts a where a.task_id = t.id) as wall_clock
from tasks t left join model_calls m on m.task_id = t.id
where t.project = :p group by t.id, t.rung1_invocations;

-- cards waiting because an oracle could not start: climbing across unrelated cards means it is broken (R63)
select t.kind, count(*) from tasks t
where t.project = :p and t.state = 'awaiting_review' and t.outcome = 'check_unavailable' group by 1;

-- reap count, by class (core §9.2)
select a.failure_class, count(*)
from task_attempts a join tasks t on t.id = a.task_id
where t.project = :p and a.failure_class in ('lease_expired', 'stalled') group by 1;

-- stalled attempts that later succeeded with no config change: over a third deletes the clause (ADR-0007)
select count(*) filter (where t.state = 'done') as succeeded_after_stall, count(*) as stalls
from task_attempts a join tasks t on t.id = a.task_id
where t.project = :p and a.failure_class = 'stalled';

-- cards quarantined by free retries, which guards ADR-0011's limit
select t.id, t.failure_class, count(*) as attempts
from tasks t join task_attempts a on a.task_id = t.id
where t.project = :p and t.state = 'quarantined'
  and t.failure_class in ('rate_limited', 'overloaded', 'timeout', 'provision_failed', 'released',
                          'check_unavailable')
group by 1,2;

-- cards committed with no check that ran, by kind (jig-sketch.py, note 3). Rule 145 leaves only not_applicable
select kind, check_result, count(*) from tasks
where project = :p and state = 'done' and check_result is distinct from 'passed' group by 1,2;

-- calls served from cache on attempts after the first (ADR-0012)
select m.attempt, count(*) filter (where m.served_from_cache) as hits, count(*) as calls
from model_calls m join tasks t on t.id = m.task_id
where t.project = :p and m.attempt > 1 group by 1 order by 1;

-- tool denials, and how often a normalizer changed the bytes (ADR-0003, ADR-0012)
select a.tool, count(*) filter (where a.decision = 'denied') as denials,
       count(a.raw_ref) as normalized, avg(a.duration_ms) as avg_ms
from tool_audit a join tasks t on t.id = a.task_id
where t.project = :p group by 1;

-- what people did, and on what (core §7)
select r.verb, count(*) from reviews r join tasks t on t.id = r.task_id
where t.project = :p group by 1;

-- the reaper's inert failure: non-zero and growing means it is not running (core §5.4)
select count(*) from tasks where state='leased' and lease_expires_at < now();
