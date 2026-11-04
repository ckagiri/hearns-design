-- A misclassified card becomes a split on the same row, so clause (a) holds its dependents (ADR-0013). A split that
-- reports misclassified uses park.sql instead, so no chain can form. Close the attempt with end_attempt.sql.
UPDATE tasks
   SET kind='split', tier=$4, config_hash=$5, state='pending', check_spec=NULL, outcome=NULL, check_result=NULL,
       max_attempts=GREATEST(max_attempts, attempts + 3), not_before=NULL,
       lease_holder=NULL, lease_expires_at=NULL, updated_at=now()
 WHERE id=$1 AND lease_holder=$2 AND attempts=$3 AND state='leased' AND kind <> 'split';
