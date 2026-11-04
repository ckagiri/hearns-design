-- Sets the effort rung at claim (policy §2.2, rule 147). $2 is EVIDENCE.
SELECT count(*) FROM task_attempts WHERE task_id = $1 AND failure_class = ANY($2);
