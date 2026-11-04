-- What layer 7 renders (ADR-0011). $2 lists the classes that charge nothing: FREE_RETRY and HALTS_RUN.
SELECT n, failure_class, check_ref, diff_ref FROM task_attempts
 WHERE task_id = $1 AND failure_class IS NOT NULL AND NOT (failure_class = ANY($2))
 ORDER BY n DESC LIMIT 1;
