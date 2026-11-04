-- Core §5.7's second statement. In the commit's transaction.
UPDATE task_attempts SET ended_at=now(), check_ref=$3, diff_ref=$4
 WHERE task_id=$1 AND n=$2;
