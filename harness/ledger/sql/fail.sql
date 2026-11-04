-- An explicit failure, fenced. The reaper tears down and flips it (core §5.4). $5: a free class under
-- runs.max_free_retries raises max_attempts by one and never lowers attempts (ADR-0007, ADR-0011).
UPDATE tasks
   SET state='failed', failure_class=$4,
       max_attempts = max_attempts + CASE WHEN $5::boolean THEN 1 ELSE 0 END,
       outcome=$6, check_result=$7, updated_at=now()
 WHERE id=$1 AND lease_holder=$2 AND attempts=$3 AND state='leased';
