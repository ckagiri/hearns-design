-- Closes an attempt that did not commit: failure, parking, reap or drain, each in that path's transaction (core §5.7).
UPDATE task_attempts
   SET ended_at=now(), failure_class=$3, check_ref=$4, diff_ref=$5, hidden_check_ref=$6, refusal=$7
 WHERE task_id=$1 AND n=$2 AND ended_at IS NULL;
