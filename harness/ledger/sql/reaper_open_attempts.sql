-- Rule 141's sweep. List the host's card_* names FIRST, then run this. Anything no row names is removed. The second
-- branch spares a retry_safe=false card's kept workspace until a verb acts (rule 149).
SELECT task_id, n FROM task_attempts WHERE ended_at IS NULL
UNION
SELECT id, attempts FROM tasks WHERE NOT retry_safe AND state = 'awaiting_review';
