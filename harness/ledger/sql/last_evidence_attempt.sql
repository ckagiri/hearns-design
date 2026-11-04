-- What layer 7 renders (rule 147). $2 is EVIDENCE: the classes that say something about the work. A dead worker, a stall,
-- a free failure and a parked outcome do not, so a retry after one keeps a byte-identical prompt.
SELECT n, failure_class, check_ref, hidden_check_ref IS NOT NULL AS hidden_failed, diff_ref FROM task_attempts
 WHERE task_id = $1 AND failure_class = ANY($2)
 ORDER BY n DESC LIMIT 1;
