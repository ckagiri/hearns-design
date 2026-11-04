-- Closes an attempt that did not commit: failure, reap or drain, each in that path's transaction (core §5.7).
UPDATE task_attempts SET ended_at=now(), failure_class=$3
 WHERE task_id=$1 AND n=$2 AND ended_at IS NULL;
