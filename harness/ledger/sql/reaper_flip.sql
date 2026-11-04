-- Core §5.4, verbatim. Runs after the candidate's teardown. Closes its attempt with end_attempt.sql in the
-- same transaction, with escalate_tier.sql when the next delivery is the last and this flip was not free.
UPDATE tasks
   SET state = (CASE WHEN NOT retry_safe AND failure_class IS DISTINCT FROM 'provision_failed'
                          THEN 'awaiting_review'
                     WHEN attempts >= max_attempts THEN 'quarantined'
                     ELSE 'pending' END)::task_state,
       not_before = now() + LEAST(interval '10 seconds' * power(2, attempts - 1),
                                  interval '5 minutes'),
       lease_holder = NULL, lease_expires_at = NULL,
       failure_class = COALESCE(failure_class,
         CASE WHEN lease_expires_at < now() THEN 'lease_expired' ELSE 'stalled' END),
       updated_at = now()
 WHERE id = $1 AND attempts = $2 AND state IN ('leased','failed');
