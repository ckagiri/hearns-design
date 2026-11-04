-- A refusal, or a check that cannot run past its free retries: the card waits for a person (ADR-0013). Holds dependents
-- under clause (a), and the reaper does not select it. Close the attempt with end_attempt.sql, the outcome as its class.
UPDATE tasks
   SET state='awaiting_review', outcome=$4, result_summary=$5, check_result=$6,
       lease_holder=NULL, lease_expires_at=NULL, updated_at=now()
 WHERE id=$1 AND lease_holder=$2 AND attempts=$3 AND state='leased';
